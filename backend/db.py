"""Lazy Firestore access for the VitalSync PoC (single-org scope for the PoC).
Uses IST (UTC+5:30) for daily calendar boundaries and UTC for ISO storage.
"""
import os
from datetime import datetime, timezone, timedelta

_client = None
ORG = os.environ.get("ORG_ID", "sunrise-clinic")
IST = timezone(timedelta(hours=5, minutes=30))


def client():
    global _client
    if _client is None:
        from google.cloud import firestore
        db_id = os.environ.get("FIRESTORE_DB", "(default)")
        _client = firestore.Client(database=db_id)
    return _client


def _patients():
    return client().collection("orgs").document(ORG).collection("patients")


def _alerts():
    return client().collection("orgs").document(ORG).collection("alerts")


def get_today_ist_str() -> str:
    return datetime.now(IST).date().isoformat()


def parse_ist_date(ts_str: str) -> str:
    if not ts_str:
        return ""
    try:
        return datetime.fromisoformat(ts_str).astimezone(IST).date().isoformat()
    except Exception:
        return ts_str[:10]


# ---------------- patients ----------------

def create_patient(data: dict) -> str:
    ref = _patients().document()
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    ref.set(data)
    return ref.id


def get_patient(patient_id: str):
    snap = _patients().document(patient_id).get()
    if not snap.exists:
        return None
    p = {"id": snap.id, **snap.to_dict()}
    
    # Compute adherence server-side
    p["adherence_7d"] = get_adherence(patient_id, days=7)
    p["adherence_30d"] = get_adherence(patient_id, days=30)
    
    # Compute BMI if height and weight exist
    h = p.get("height_cm") or 0
    w = p.get("weight_kg") or 0
    if h > 0 and w > 0:
        p["bmi"] = round(w / ((h / 100) ** 2), 1)
    else:
        p["bmi"] = None
        
    return p


def get_patient_by_token(token: str):
    q = _patients().where("link_token", "==", token).limit(1)
    docs = list(q.stream())
    return ({"id": docs[0].id, **docs[0].to_dict()}) if docs else None


def update_patient(patient_id: str, data: dict):
    _patients().document(patient_id).set(data, merge=True)


def list_patients():
    out = []
    unresolved_alerts = list_alerts(unresolved_only=True)
    alert_pids = {a.get("patient_id"): a for a in unresolved_alerts if a.get("patient_id")}
    
    for d in _patients().stream():
        p = {"id": d.id, **d.to_dict()}
        p["has_unresolved_alert"] = p["id"] in alert_pids
        p["unresolved_alert_count"] = sum(1 for a in unresolved_alerts if a.get("patient_id") == p["id"])
        out.append(p)
    return out


# ---------------- adherence ----------------

def get_adherence(patient_id: str, days: int = 7) -> str:
    """Return 'X of last N days logged' where a day counts if >=1 vitals or >=1 meal logged (IST date boundary)."""
    today = datetime.now(IST).date()
    window_dates = {(today - timedelta(days=i)).isoformat() for i in range(days)}
    
    logged_dates = set()
    
    # Check vitals in window
    for v in _patients().document(patient_id).collection("vitals").stream():
        ts = v.to_dict().get("ts") or ""
        d_str = parse_ist_date(ts)
        if d_str in window_dates:
            logged_dates.add(d_str)
            
    # Check meals in window
    for m in _patients().document(patient_id).collection("meals").stream():
        ts = m.to_dict().get("ts") or ""
        d_str = parse_ist_date(ts)
        if d_str in window_dates:
            logged_dates.add(d_str)
            
    count = len(logged_dates)
    return f"{count} of last {days} days logged"


# ---------------- vitals ----------------

def add_vitals(patient_id: str, vitals: dict) -> dict:
    vitals["ts"] = datetime.now(timezone.utc).isoformat()
    _patients().document(patient_id).collection("vitals").add(vitals)
    return vitals


def get_vitals(patient_id: str, limit: int = 7):
    q = (_patients().document(patient_id).collection("vitals")
         .order_by("ts", direction="DESCENDING").limit(limit))
    return [d.to_dict() for d in q.stream()]


def get_vitals_trend(patient_id: str, days: int = 7):
    """Return daily vitals for the last `days` days ending with today IST, oldest -> newest.
    When multiple readings exist for a date, deterministically select the earliest reading by timestamp (fasting value)."""
    today = datetime.now(IST).date()
    date_map = {}
    for i in range(days - 1, -1, -1):
        d_str = (today - timedelta(days=i)).isoformat()
        date_map[d_str] = {
            "date": d_str,
            "sugar": None,
            "sys": None,
            "dia": None,
            "hr": None,
            "ts": None
        }
        
    q = _patients().document(patient_id).collection("vitals")
    for d in q.stream():
        v = d.to_dict()
        ts = v.get("ts", "")
        if ts:
            d_str = parse_ist_date(ts)
            if d_str in date_map:
                cur_ts = date_map[d_str]["ts"]
                if cur_ts is None or ts < cur_ts:
                    date_map[d_str]["sugar"] = v.get("sugar")
                    date_map[d_str]["sys"] = v.get("sys")
                    date_map[d_str]["dia"] = v.get("dia")
                    date_map[d_str]["hr"] = v.get("hr")
                    date_map[d_str]["ts"] = ts
                
    return list(date_map.values())


# ---------------- meals & nutrition ----------------

def log_meal(patient_id: str, slot: str, dish: str, kcal: int = 0,
             carbs_g: int = 0, sugar_g: int = 0, sodium_mg: int = 0,
             protein_g: int = 0):
    entry = {
        "slot": slot,
        "dish": dish,
        "kcal": int(kcal or 0),
        "carbs_g": int(carbs_g or 0),
        "sugar_g": int(sugar_g or 0),
        "sodium_mg": int(sodium_mg or 0),
        "protein_g": int(protein_g or 0),
        "ts": datetime.now(timezone.utc).isoformat()
    }
    _patients().document(patient_id).collection("meals").add(entry)
    return entry


def get_meals_today(patient_id: str):
    today = get_today_ist_str()
    q = _patients().document(patient_id).collection("meals")
    meals = []
    for d in q.stream():
        m = d.to_dict()
        ts = m.get("ts", "")
        if parse_ist_date(ts) == today:
            meals.append(m)
    meals.sort(key=lambda x: x.get("ts", ""))
    return meals


def get_nutrition_trend(patient_id: str, days: int = 7):
    """Return per-day totals for the last `days` days ending with today IST (oldest -> newest).
    Days without meals present with meals_logged: 0 and nulls for nutrients."""
    today = datetime.now(IST).date()
    date_map = {}
    for i in range(days - 1, -1, -1):
        d_str = (today - timedelta(days=i)).isoformat()
        date_map[d_str] = {
            "date": d_str,
            "kcal": None,
            "carbs_g": None,
            "sugar_g": None,
            "sodium_mg": None,
            "protein_g": None,
            "meals_logged": 0
        }

    q = _patients().document(patient_id).collection("meals")
    for d in q.stream():
        m = d.to_dict()
        ts = m.get("ts", "")
        if ts:
            d_str = parse_ist_date(ts)
            if d_str in date_map:
                if date_map[d_str]["meals_logged"] == 0:
                    date_map[d_str]["kcal"] = 0
                    date_map[d_str]["carbs_g"] = 0
                    date_map[d_str]["sugar_g"] = 0
                    date_map[d_str]["sodium_mg"] = 0
                    date_map[d_str]["protein_g"] = 0
                date_map[d_str]["kcal"] += int(m.get("kcal", 0) or 0)
                date_map[d_str]["carbs_g"] += int(m.get("carbs_g", 0) or 0)
                date_map[d_str]["sugar_g"] += int(m.get("sugar_g", 0) or 0)
                date_map[d_str]["sodium_mg"] += int(m.get("sodium_mg", 0) or 0)
                date_map[d_str]["protein_g"] += int(m.get("protein_g", 0) or 0)
                date_map[d_str]["meals_logged"] += 1

    return list(date_map.values())


# ---------------- plans ----------------

def save_plan(patient_id: str, plan: dict):
    now = datetime.now(timezone.utc)
    today = get_today_ist_str()
    plan["date"] = today
    if "generated_at" not in plan:
        plan["generated_at"] = now.isoformat()
    _patients().document(patient_id).collection("plans").document(today).set(plan)


def get_recent_plans(patient_id: str, days: int = 2):
    q = (_patients().document(patient_id).collection("plans")
         .order_by("date", direction="DESCENDING").limit(days))
    return [d.to_dict() for d in q.stream()]


def get_plans_trend(patient_id: str, days: int = 7):
    """Return per-day {date, nutrition_summary, targets, meal_plan, activity, brief} ending with today IST, oldest -> newest."""
    today = datetime.now(IST).date()
    date_map = {}
    for i in range(days - 1, -1, -1):
        d_str = (today - timedelta(days=i)).isoformat()
        date_map[d_str] = {
            "date": d_str,
            "nutrition_summary": None,
            "targets": None,
            "meal_plan": None,
            "activity": None,
            "brief": None
        }

    q = _patients().document(patient_id).collection("plans")
    for d in q.stream():
        p = d.to_dict()
        d_str = p.get("date") or d.id
        if d_str in date_map:
            nutri = p.get("nutrition_summary")
            if not nutri and p.get("targets"):
                t = p["targets"]
                kcal = t.get("kcal", 1500)
                sod = int((t.get("sodium_g", 2.0) or 2.0) * 1000)
                nutri = {
                    "kcal": kcal,
                    "carbs_g": int(kcal * 0.45 / 4),
                    "sugar_g": 15,
                    "sodium_mg": sod,
                    "protein_g": int(kcal * 0.20 / 4)
                }
            date_map[d_str] = {
                "date": d_str,
                "nutrition_summary": nutri,
                "targets": p.get("targets"),
                "meal_plan": p.get("meal_plan"),
                "activity": p.get("activity"),
                "brief": p.get("brief")
            }

    return list(date_map.values())


def get_plan_today(patient_id: str):
    today = get_today_ist_str()
    snap = _patients().document(patient_id).collection("plans").document(today).get()
    return snap.to_dict() if snap.exists else None


# ---------------- day drill-down ----------------

def get_day_detail(patient_id: str, date_str: str) -> dict:
    """Return everything for that day (IST date): plan, meals with nutrition, and vitals."""
    # 1. Plan for that day
    snap = _patients().document(patient_id).collection("plans").document(date_str).get()
    plan = snap.to_dict() if snap.exists else None

    # 2. Meals for that day
    meals = []
    q_meals = _patients().document(patient_id).collection("meals")
    for d in q_meals.stream():
        m = d.to_dict()
        ts = m.get("ts", "")
        if parse_ist_date(ts) == date_str:
            meals.append(m)
    meals.sort(key=lambda x: x.get("ts", ""))

    # 3. Vitals for that day (deterministically select earliest reading by timestamp - fasting value)
    vitals_list = []
    q_vitals = _patients().document(patient_id).collection("vitals")
    for d in q_vitals.stream():
        v = d.to_dict()
        ts = v.get("ts", "")
        if parse_ist_date(ts) == date_str:
            vitals_list.append(v)
    vitals_list.sort(key=lambda x: x.get("ts", ""))
    vitals = vitals_list[0] if vitals_list else None

    return {
        "date": date_str,
        "plan": plan,
        "meals": meals,
        "vitals": vitals
    }


# ---------------- alerts ----------------

def add_alert(patient_id: str, message: str, severity: str = "warning"):
    now = datetime.now(timezone.utc)
    # Deduplicate: if identical unresolved alert for same patient exists within 90 seconds, skip
    for a in list_alerts(unresolved_only=True):
        if a.get("patient_id") == patient_id and a.get("message") == message:
            ts_str = a.get("ts", "")
            if ts_str:
                try:
                    ts_dt = datetime.fromisoformat(ts_str)
                    if 0 <= (now - ts_dt).total_seconds() <= 90:
                        return a.get("id")
                except Exception:
                    pass

    ref = _alerts().document()
    doc_data = {
        "patient_id": patient_id,
        "message": message,
        "severity": severity,
        "ts": now.isoformat(),
        "resolved": False
    }
    ref.set(doc_data)
    return ref.id


def list_alerts(unresolved_only: bool = False):
    q = _alerts().order_by("ts", direction="DESCENDING")
    alerts = [{"id": d.id, **d.to_dict()} for d in q.stream()]
    if unresolved_only:
        alerts = [a for a in alerts if not a.get("resolved")]
    return alerts


def resolve_alert(alert_id: str):
    _alerts().document(alert_id).update({"resolved": True})
    return {"status": "resolved", "id": alert_id}


# ---------------- recipes ----------------

MEAT = {"chicken", "mutton", "pork", "beef", "seafood"}


def get_recipes(exclusions: list = None):
    """Return recipes that contain NONE of the excluded foods."""
    excl = {e.lower().strip() for e in (exclusions or [])}
    if "all meat" in excl:
        excl |= MEAT
    out = []
    for d in client().collection("recipes").stream():
        r = d.to_dict()
        contains = {c.lower() for c in r.get("contains", [])}
        if not (contains & excl):
            out.append(r)
    return out


def cleanup_stale_patients():
    """Delete leftover test patients and their subcollections, keeping only the 3 canonical demo patients."""
    try:
        allowed_ids = {"demo-ramesh", "demo-lakshmi", "demo-ananya"}
        patients_ref = _patients()
        for p_doc in patients_ref.stream():
            if p_doc.id not in allowed_ids:
                for sub in ["vitals", "meals", "plans"]:
                    for s_doc in p_doc.reference.collection(sub).stream():
                        s_doc.reference.delete()
                p_doc.reference.delete()
        alerts_ref = _alerts()
        for a_doc in alerts_ref.stream():
            a_data = a_doc.to_dict()
            if a_data.get("patient_id") not in allowed_ids:
                a_doc.reference.delete()
    except Exception as e:
        print(f"cleanup_stale_patients error: {e}")
