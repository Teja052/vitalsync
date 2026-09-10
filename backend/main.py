"""VitalSync PoC — Cloud Run backend.

Flow: doctor enrolls patient → patient logs vitals → event goes to Pub/Sub
(or runs inline if Pub/Sub isn't configured yet) → Meal-Plan Agent (ADK +
Gemini) writes today's plan → doctor view shows everything live.
Meal photos → Gemini Flash vision → dish suggestions with nutrition macros.
"""
import base64
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db

app = FastAPI(title="VitalSync PoC")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "")  # e.g. projects/<id>/topics/vitals-events
VISION_MODEL = os.environ.get("VISION_MODEL", "gemini-3.7-flash")

MEAL_SLOTS = ["wake-up drink", "breakfast", "mid-day snack", "lunch",
              "evening tea", "evening snack", "dinner", "bedtime"]

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------- models ----------------

class Enroll(BaseModel):
    name: str
    dob: str
    gender: str
    height_cm: float
    weight_kg: float
    food_exclusions: list[str] = []
    allergens: list[str] = []
    state: str = "Telangana"  # Indian state (cuisine); doctor inputs, patient can change
    phone: str | None = None


class ProfileUpdate(BaseModel):
    patient_id: str
    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    state: str | None = None
    food_exclusions: list[str] | None = None
    allergens: list[str] | None = None
    guide: str | None = None
    status: str | None = None
    firebase_uid: str | None = None


class Vitals(BaseModel):
    patient_id: str
    sugar: float
    sys: float
    dia: float
    hr: float


class MealPhoto(BaseModel):
    patient_id: str
    slot: str
    image_b64: str  # jpeg/png bytes, base64


class MealConfirm(BaseModel):
    patient_id: str
    slot: str
    dish: str
    kcal: int = 0
    carbs_g: int = 0
    sugar_g: int = 0
    sodium_mg: int = 0
    protein_g: int = 0


@app.on_event("startup")
def on_startup():
    db.cleanup_stale_patients()
    try:
        import seed_demo
        seed_demo.run_reset()
    except Exception as e:
        print(f"Startup seed warning: {e}")


@app.post("/api/admin/reset")
def admin_reset():
    import seed_demo
    return seed_demo.run_reset()


# ---------------- doctor side ----------------

@app.post("/api/enroll")
def enroll(p: Enroll):
    if not p.name or not p.name.strip() or p.name.strip().lower() in ("undefined", "null"):
        raise HTTPException(400, "Valid patient name is required")
    token = uuid.uuid4().hex[:8].upper()
    pid = db.create_patient({**p.model_dump(), "link_token": token, "status": "invited"})
    return {"patient_id": pid, "secure_link": f"/patient?token={token}", "token": token, "demo_otp": "4821"}


@app.post("/api/profile")
def update_profile(u: ProfileUpdate):
    """Patient-editable profile fields: state (cuisine), food exclusions, allergens, doctor guide."""
    changes = {k: v for k, v in u.model_dump(exclude={"patient_id"}).items()
               if v is not None}
    if "name" in changes and (not str(changes["name"]).strip() or str(changes["name"]).strip().lower() in ("undefined", "null")):
        del changes["name"]
    if not changes:
        raise HTTPException(400, "nothing to update")
    if "guide" in changes:
        changes["guide_updated_at"] = datetime.now(timezone.utc).isoformat()
    db.update_patient(u.patient_id, changes)
    return {"updated": list(changes.keys())}


@app.get("/api/org/patients")
def org_patients():
    return db.list_patients()


@app.get("/api/org/alerts")
def org_alerts(unresolved: int = 0):
    return db.list_alerts(unresolved_only=(unresolved == 1))


@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    return db.resolve_alert(alert_id)


# ---------------- patient side & trends ----------------

@app.get("/api/patient/{patient_id}")
def patient_home(patient_id: str):
    p = db.get_patient(patient_id)
    if not p:
        raise HTTPException(404, "patient not found")
    return {
        "profile": p,
        "vitals": db.get_vitals(patient_id, limit=7),
        "meals_today": db.get_meals_today(patient_id),
        "plan_today": db.get_plan_today(patient_id),
        "slots": MEAL_SLOTS,
        "adherence_7d": p.get("adherence_7d"),
        "adherence_30d": p.get("adherence_30d"),
        "bmi": p.get("bmi")
    }


@app.get("/api/patient/{patient_id}/vitals")
def patient_vitals_trend(patient_id: str, days: int = 7):
    return db.get_vitals_trend(patient_id, days=days)


@app.get("/api/patient/{patient_id}/nutrition")
def patient_nutrition_trend(patient_id: str, days: int = 7):
    return db.get_nutrition_trend(patient_id, days=days)


@app.get("/api/patient/{patient_id}/plans")
def patient_plans_trend(patient_id: str, days: int = 7):
    return db.get_plans_trend(patient_id, days=days)


@app.get("/api/patient/{patient_id}/day/{date}")
def patient_day_drilldown(patient_id: str, date: str):
    return db.get_day_detail(patient_id, date)


@app.post("/api/vitals")
def record_vitals(v: Vitals):
    if not (30 <= v.sugar <= 600 and 60 <= v.sys <= 260 and
            30 <= v.dia <= 160 and 30 <= v.hr <= 220):
        raise HTTPException(400, "reading out of accepted range — please re-check")
    db.add_vitals(v.patient_id, v.model_dump(exclude={"patient_id"}))
    event = v.model_dump()
    if PUBSUB_TOPIC:
        _publish(event)
        return {"status": "queued", "via": "pubsub"}
    result = _run_agent(v.patient_id, event)
    return {"status": "done", "via": "inline", "plan": result}


def _publish(event: dict):
    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient()
    publisher.publish(PUBSUB_TOPIC, json.dumps(event).encode()).result()


@app.post("/api/agent/handle")
async def pubsub_push(request: Request):
    """Pub/Sub push subscription endpoint."""
    import asyncio
    body = await request.json()
    payload = json.loads(base64.b64decode(body["message"]["data"]))
    plan = await asyncio.to_thread(_run_agent, payload)
    return {"plan": plan}


def _run_agent(event: dict) -> dict:
    import agent
    patient_id = event["patient_id"]

    # Task 3: Idempotency check (skip if generated within last 90s for identical vitals)
    existing_plan = db.get_plan_today(patient_id)
    if existing_plan and "generated_at" in existing_plan:
        try:
            gen_time = datetime.fromisoformat(existing_plan["generated_at"])
            now_time = datetime.now(timezone.utc)
            age_seconds = (now_time - gen_time).total_seconds()

            saved_vitals = existing_plan.get("vitals", {})
            vitals_match = (
                float(saved_vitals.get("sugar", -999)) == float(event.get("sugar", -998)) and
                float(saved_vitals.get("sys", -999)) == float(event.get("sys", -998)) and
                float(saved_vitals.get("dia", -999)) == float(event.get("dia", -998)) and
                float(saved_vitals.get("hr", -999)) == float(event.get("hr", -998))
            )
            if 0 <= age_seconds <= 90 and vitals_match:
                return existing_plan
        except Exception:
            pass

    plan = agent.generate_plan(patient_id, event)
    now_iso = datetime.now(timezone.utc).isoformat()
    plan["generated_at"] = now_iso
    plan["vitals"] = {
        "sugar": event.get("sugar"),
        "sys": event.get("sys"),
        "dia": event.get("dia"),
        "hr": event.get("hr")
    }
    
    # Ensure nutrition_summary is present in plan
    if "nutrition_summary" not in plan and plan.get("targets"):
        t = plan["targets"]
        kcal = t.get("kcal", 1500)
        sod = int((t.get("sodium_g", 2.0) or 2.0) * 1000)
        plan["nutrition_summary"] = {
            "kcal": kcal,
            "carbs_g": int(kcal * 0.45 / 4),
            "sugar_g": 15,
            "sodium_mg": sod,
            "protein_g": int(kcal * 0.20 / 4)
        }

    # Ensure yoga recommendations always specify asana names
    act = plan.get("activity", "")
    if act and "yoga" in act.lower():
        if "(" not in act and ":" not in act and not any(a in act.lower() for a in ["vajrasana", "bhujangasana", "asana"]):
            act = re.sub(r"(?i)(gentle |simple )?yoga", "yoga (Vajrasana, Bhujangasana & Ardha Matsyendrasana)", act)
            plan["activity"] = act

    db.save_plan(patient_id, plan)
    
    if plan.get("alert") or event.get("sugar", 0) >= 250 or event.get("sys", 0) >= 180:
        p = db.get_patient(patient_id) or {}
        severity = "critical" if (event.get("sugar", 0) >= 250 or event.get("sys", 0) >= 180) else "warning"
        db.add_alert(
            patient_id,
            f"{p.get('name', 'Patient')}: sugar {event.get('sugar')} mg/dL, "
            f"BP {event.get('sys')}/{event.get('dia')} — review advised",
            severity=severity
        )
    return plan


# ---------------- UI & Static routes ----------------

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}


@app.get("/")
def serve_root():
    doctor_file = os.path.join(STATIC_DIR, "doctor.html")
    if os.path.exists(doctor_file):
        return FileResponse(doctor_file, headers=NO_CACHE_HEADERS)
    raise HTTPException(404, "Doctor portal page not found")


@app.get("/patient")
def serve_patient():
    patient_file = os.path.join(STATIC_DIR, "patient.html")
    if os.path.exists(patient_file):
        return FileResponse(patient_file, headers=NO_CACHE_HEADERS)
    raise HTTPException(404, "Patient app page not found")


@app.get("/join/{token}")
def join_invite(token: str):
    patient_file = os.path.join(STATIC_DIR, "patient.html")
    if os.path.exists(patient_file):
        return FileResponse(patient_file, headers=NO_CACHE_HEADERS)
    raise HTTPException(404, "Invite page not found")


@app.get("/api/invite/{token}")
def get_by_invite(token: str):
    p = db.get_patient_by_token(token)
    if not p:
        raise HTTPException(404, "Invalid or expired invite link")
    return p


@app.get("/api/recipes")
def get_recipes_list(exclusions: str = ""):
    excl = [e.strip() for e in exclusions.split(",") if e.strip()] if exclusions else []
    return db.get_recipes(excl)


# ---------------- meal photos (Gemini Flash vision) ----------------

@app.post("/api/meal-photo")
def meal_photo(m: MealPhoto):
    from google import genai
    from google.genai import types
    client = genai.Client()  # uses GOOGLE_API_KEY
    b64_str = m.image_b64
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    image = types.Part.from_bytes(data=base64.b64decode(b64_str),
                                  mime_type="image/jpeg")
    prompt = (f"This is a photo of an Indian '{m.slot}' meal of a diabetic patient. "
              "Identify the 3 most likely dishes. Respond ONLY with JSON: "
              '[{"dish": "<name>", "kcal": <estimated int>, "carbs_g": <estimated int>, '
              '"sugar_g": <estimated int>, "sodium_mg": <estimated int>, "protein_g": <estimated int>}, ...] '
              "— no markdown.")
    resp = client.models.generate_content(model=VISION_MODEL, contents=[image, prompt])
    text = resp.text.strip()
    if text.startswith("```"):
        text = text[text.find("["):text.rfind("]") + 1]
    try:
        return {"suggestions": json.loads(text)}
    except json.JSONDecodeError:
        return {"suggestions": [], "raw": text[:300]}


@app.post("/api/meal-confirm")
def meal_confirm(m: MealConfirm):
    return db.log_meal(
        m.patient_id, m.slot, m.dish, m.kcal,
        m.carbs_g, m.sugar_g, m.sodium_mg, m.protein_g
    )


@app.get("/healthz")
def health():
    return {"ok": True}
