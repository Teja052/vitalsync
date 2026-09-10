# VitalSync — HCP-prescribed nutrition & vitals tracking for diabetes care.

VitalSync is an HCP-prescribed digital health platform for diabetes care. A clinician enrolls a patient from a clean clinical dashboard; the patient verifies by phone OTP, then logs morning vitals (fasting glucose, blood pressure, heart rate) and photographs their meals — Gemini vision identifies each dish and estimates its calories, carbohydrates, sugar, sodium, and protein. A Meal-Plan Agent built on Google's ADK and Gemini responds to every morning reading with a personalized, nutritionally balanced 8-slot daily plan — protein at every main meal, vegetables, low-GI choices — honoring the patient's regional cuisine, dietary exclusions, allergens, and daily targets for calories, carbs, sugar, sodium, and protein. The clinician's portal closes the loop with planned-versus-eaten trends for each of those nutrients, weekly-to-quarterly vitals telemetry, per-day drill-downs comparing the planned menu against what was actually eaten, and automatic alerts on dangerous readings.


## Architecture

VitalSync is built entirely on a Google Cloud-native architecture deployed in region `asia-south1` (Mumbai):

```
+-----------------------------------------------------------------------------------+
|                                     VitalSync                                     |
+-----------------------------------------------------------------------------------+
|  [ Patient App (Web / PWA) ]              [ Doctor Clinical Portal ]              |
|   - Firebase Phone Auth                    - Clinical Decision Dashboard          |
|   - Vitals Telemetry Entry                 - 7d / 30d / 90d Trend Analytics       |
|   - Gemini Vision Meal Photo Recognition   - Vitals & Planned vs Eaten Nutrition  |
|   - Daily Brief & 8-Slot Menu              - Day-level Telemetry Drill-Down       |
|                                            - Actionable Alert Management          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       Google Cloud Run (FastAPI Backend)                          |
|   - REST API & Idempotency Guards                                                 |
|   - AI Food Recognition — Gemini Flash Vision (dish + nutrient estimation)        |
|   - Pub/Sub Push Handler & Telemetry Ingestion                                    |
+-----------------------------------------------------------------------------------+
         |                                                 |
         v                                                 v
+-----------------------------+               +-------------------------------------+
|   Google Cloud Pub/Sub      |               |      Google Cloud Firestore         |
|   - Event-driven Ingestion  |               |      - Patients & Profiles          |
|   - Vitals Telemetry Queue  |               |      - Telemetry Readings & Alerts  |
+-----------------------------+               |      - Daily Plans & Meal Logs      |
         |                                    +-------------------------------------+
         v                                                 ^
+--------------------------------------------------+       |
|  Meal-Plan Agent (Google ADK + Gemini 3.7 Flash) |-------+
|  - Reads Patient Profile & Vitals History        |
|  - Selects Regional Dishes & Calculates Targets  |
|  - Writes Personalized Daily Plan to Firestore   |
+--------------------------------------------------+
```

- **Compute & APIs:** Google Cloud Run running FastAPI (`asia-south1`).
- **Data Store:** Google Cloud Firestore in Native mode (`asia-south1`).
- **Messaging:** Google Cloud Pub/Sub for asynchronous event-driven telemetry ingestion.
- **AI / LLM:** Google ADK with Gemini 3.7 Flash for agentic meal planning, and Gemini Flash for meal vision recognition.
- **Authentication:** Firebase Authentication with phone sign-in.

## Repository Map

- `backend/agent.py` — the ADK Meal-Plan Agent and its instruction (the AI's behavioral rules)
- `backend/main.py` — FastAPI backend: enrollment, vitals, Pub/Sub handler, Gemini vision meal recognition, portal APIs
- `backend/db.py` — Firestore data layer
- `backend/static/` — the two live UIs: `doctor.html` (clinical portal), `patient.html` (patient app)
- `seed/` — synthetic demo data seeding and reset scripts
- `frontend/prototype.html` — early planning-phase design mock (not the live UI)
- `AGENTS.md` — the build contract used to direct AI coding agents during development

## Telemetry & Vitals Flow

1. **Patient Ingestion:** The patient inputs their morning fasting readings (glucose, blood pressure, resting heart rate) in the patient application.
2. **Alert Evaluation & Pub/Sub:** The backend ingests the reading, evaluates clinical safety thresholds (generating alerts for abnormal spikes), and publishes an event to Google Cloud Pub/Sub.
3. **Agentic Plan Generation:** The Pub/Sub subscription triggers the Google ADK Meal-Plan Agent, which inspects the patient's vitals, medical history, regional state cuisine (e.g. Telangana, Tamil Nadu), and dietary exclusions.
4. **Plan Persistence:** Gemini generates a personalized clinical brief, nutrient targets, 8-slot regional meal menu, and physical activity recommendation, saving it directly to Firestore with idempotency protection.
5. **Real-Time Visibility:** The patient application immediately renders the daily clinical brief and meal suggestions, while the Doctor Clinical Portal provides live adherence tracking, glycemic trends, and planned vs. eaten nutritional analytics.

## Synthetic Data Notice

> **Note:** All patient profiles (e.g., Ramesh, Lakshmi), clinical readings, and telemetry records in this demo are strictly synthetic and generated for demonstration purposes. No real patient data is used or stored.
