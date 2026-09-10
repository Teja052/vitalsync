"""VitalSync Meal-Plan Agent — built with Google's Agent Development Kit (ADK).

The agent receives a patient's morning vitals, uses tools to read the
patient profile, recent vitals history, and the recipe library from
Firestore, and returns a JSON daily plan (brief + meal plan + targets).
Powered by Gemini via the AI Studio API key (GOOGLE_API_KEY env var).
"""
import asyncio
import json
import os

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

import db  # local module: lazy Firestore access

MODEL = os.environ.get("AGENT_MODEL", "gemini-3.7-flash")

# ---------------- Tools (the agent decides when to call these) ----------------

def get_patient_profile(patient_id: str) -> dict:
    """Return the patient's profile: name, age, gender, height, weight,
    food_exclusions (foods the patient does NOT eat, e.g. egg, chicken,
    mutton, pork, beef, seafood, all meat, dairy), allergen list, and state
    (Indian state whose cuisine the meal plan must follow, e.g. Telangana,
    Tamil Nadu, Punjab)."""
    return db.get_patient(patient_id) or {"error": "patient not found"}


def get_vitals_history(patient_id: str) -> list:
    """Return the patient's last 7 vitals entries (fasting blood sugar mg/dL,
    systolic/diastolic BP mmHg, heart rate bpm), newest first."""
    return db.get_vitals(patient_id, limit=7)


def get_recent_plans(patient_id: str) -> list:
    """Return the patient's meal plans from the last 2 days (newest first),
    each with its meal_plan slots — used to avoid repeating yesterday's menu."""
    return db.get_recent_plans(patient_id, days=2)


def get_recipes(exclusions: list) -> list:
    """Return diabetic-friendly Indian recipes containing NONE of the given
    excluded foods (e.g. ['egg', 'all meat', 'dairy']). Each recipe has name,
    kcal, sodium_mg, and a 'contains' list of notable ingredients."""
    return db.get_recipes(exclusions)


AGENT_INSTRUCTION = """You are VitalSync's Meal-Plan Agent for diabetic patients in India.

Given a patient id and today's morning vitals, you MUST:
1. Call get_patient_profile and get_vitals_history to understand the patient.
2. Call get_recipes with the patient's food_exclusions list.
3. Call get_recent_plans to see the last 2 days' menus.
4. Compose the day's plan.

Rules:
- Be supportive and plain-spoken. You give wellness suggestions, NEVER medical
  advice, diagnosis, or medication guidance. If fasting sugar >= 250 or
  systolic >= 180, say the care team has been notified and keep the tone calm.
- EXCLUSIONS AND ALLERGENS ARE ABSOLUTE: the profile's food_exclusions are
  foods the patient does not eat ('all meat' covers chicken, mutton, pork,
  beef, and seafood). Never include an excluded food or an allergen in any
  dish, garnish, or side — no exceptions.
- STATE CUISINE IS A MUST: the profile includes the patient's Indian state
  (e.g. Telangana, Tamil Nadu, Punjab, West Bengal, Gujarat, Kerala). Meal
  suggestions must reflect that state's everyday cuisine (e.g. Telangana →
  jonna roti, sajja roti, pesarattu; Tamil Nadu → idli, dosai, kambu koozh;
  Punjab → phulka, dal, sarson ka saag). Pan-Indian/generic dishes (sprouts
  salad, buttermilk, roasted chana) are allowed as a minority of slots. Never
  suggest a dish alien to the patient's state as a main meal.
- VARIETY IS REQUIRED: compare against the previous day's menu (from
  get_recent_plans). At most 2 of the 8 slots (~30%) may repeat a dish from
  the previous day; the rest must be different dishes, still matching the
  patient's state cuisine, preference, and allergen rules.
- Meal slots: wake-up drink, breakfast, mid-day snack, lunch, evening tea,
  evening snack, dinner, bedtime.
- Targets: pick a sensible calorie target (1400-1800 kcal by gender/weight),
  sodium cap in grams, and a step goal (4000-8000 by age).

Respond with ONLY valid JSON, no markdown fences, in this exact shape:
{"brief": "<3-4 sentence plain-language summary of today's readings and trend>",
 "alert": <true if readings are concerning enough to flag the care team, else false>,
 "targets": {"kcal": <int>, "sodium_g": <float>, "steps": <int>},
 "meal_plan": [{"slot": "<slot name>", "suggestion": "<dish>", "kcal": <int>}, ...one per slot...],
 "activity": "<one line: walk + specific no-equipment yoga asanas appropriate to age e.g. Vajrasana, Bhujangasana, Pawanmuktasana, Ardha Matsyendrasana>"}
"""

_agent = Agent(
    name="meal_plan_agent",
    model=MODEL,
    description="Turns a diabetic patient's morning vitals into a personalized daily meal plan.",
    instruction=AGENT_INSTRUCTION,
    tools=[get_patient_profile, get_vitals_history, get_recipes, get_recent_plans],
)

_runner = InMemoryRunner(agent=_agent, app_name="vitalsync")


async def _run_async(prompt: str) -> str:
    session = await _runner.session_service.create_session(
        app_name="vitalsync", user_id="system")
    message = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])
    final = ""
    async for event in _runner.run_async(
            user_id="system", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text or "" for p in event.content.parts)
    return final


def generate_plan(patient_id: str, vitals: dict) -> dict:
    """Run the Meal-Plan Agent for one patient's morning vitals. Returns the plan dict."""
    prompt = (
        f"Patient id: {patient_id}. Today's morning readings: "
        f"fasting blood sugar {vitals.get('sugar')} mg/dL, "
        f"BP {vitals.get('sys')}/{vitals.get('dia')} mmHg, "
        f"heart rate {vitals.get('hr')} bpm. Build today's plan."
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            raw = pool.submit(asyncio.run, _run_async(prompt)).result()
    else:
        raw = asyncio.run(_run_async(prompt))

    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):text.rfind("}") + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"brief": text[:600], "alert": False, "targets": {},
                "meal_plan": [], "activity": "", "parse_error": True}
