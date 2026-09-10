# VitalSync PoC — Build Brief for Antigravity

You are the application-development agent for VitalSync. This file is your
contract: follow it exactly. Requirements, prompts, and validation are owned by
the product owner; do not redesign scope — build what each Task
specifies, to its acceptance criteria.

## Project context

VitalSync: HCP-prescribed nutrition & vitals tracking for diabetes care (India).
A doctor enrolls a patient; the patient logs morning vitals; a Pub/Sub event
triggers the Meal-Plan Agent (Google ADK + Gemini) which writes a personalized
daily plan to Firestore; meal photos go to Gemini Flash for dish recognition;
everything is visible live on a doctor portal. **Proof of concept** — synthetic
data only, no real patients.

## Hard constraints (never violate)

1. **Google-only stack.** Cloud Run, Firestore, Pub/Sub, Gemini (AI Studio key),
   ADK, Firebase. No non-Google cloud services, no other model providers.
2. Region **asia-south1** for everything deployable.
3. Do not modify `backend/agent.py` prompt text (`AGENT_INSTRUCTION`) — the
   prompt is owned by the product owner and iterated in Google AI Studio.
   (The vision prompt in `main.py` `/api/meal-photo` MAY be extended per Task 2.)
4. Never hardcode API keys or secrets in code or commit them. `GOOGLE_API_KEY`,
   `FIRESTORE_DB`, `PUBSUB_TOPIC` come from Cloud Run environment variables.
5. Wellness positioning: UI copy must never give medical advice. Keep the
   existing disclaimer lines.
6. Keep the existing REST contract stable; extend it, don't break it.
7. Deploy target is the existing service `vitalsync-api` in asia-south1.

## Current state

- **Task 1 — DONE and validated (Sep 1).** UI at `/` wired to live APIs; state
  selector + food-exclusion chips + edit-profile; vitals → Pub/Sub → agent →
  plan polling; meal-photo → Gemini Flash suggestions → confirm; doctor portal
  with patients, alerts, guidance.
- Infra fix applied outside code: Pub/Sub subscription ack deadline raised to
  120 s (was causing duplicate agent runs).
- `seed/reset_demo.py` resets demo data (Ramesh = Telangana, 5-day vitals).

---

## TASK 2 — Doctor portal v2 (final spec, Sep 1)

The doctor's portal is a clinical decision surface. Build exactly this.

### 2A. Portal structure
1. **Left nav / patient list** — all patients with status pill (invited /
   active), an **alert badge** on any patient with an unresolved alert, and an
   **Enroll patient** action (existing form; captures state as a plain field
   but never displays it afterwards — the doctor does not need cuisine).
2. **Patient header (slim bar)** — name · age · gender · height/weight (BMI
   computed) · food exclusions · allergens · status pill ·
   **adherence: "X of last 7 days logged"** (a day counts if ≥1 vitals or
   ≥1 meal logged). No avatar circles, no state/cuisine text.
3. **Alerts panel** — unresolved alerts for this patient (severity pill,
   reading, time) with a "Mark reviewed" action (`POST /api/alerts/{id}/resolve`
   sets `resolved: true`). The nav badge reflects unresolved count.
4. **Guidance to patient** — existing textarea + send (unchanged behavior),
   showing the last sent note and time.

### 2B. Trends (primary content)
5. **Range selector: Weekly (7 d) · Monthly (30 d) · Quarterly (90 d)** —
   applies to every chart on the page.
6. **Vitals trends** — three line charts: fasting glucose (mg/dL, with a
   faint reference band 80–130), blood pressure (systolic and diastolic as two
   lines), heart rate. Daily points; the range selector aggregates nothing —
   it only changes the window.
7. **Nutrition trends — planned vs eaten** — four line charts: carbohydrates
   (g), **"Sugar intake (g)"** (never just "sugar" — avoids confusion with
   blood glucose), sodium (mg), protein (g). Each chart has two series:
   **planned** (from that day's plan `nutrition_summary`) and **eaten** (sum of
   confirmed meals). Above the charts, a **today** row: eaten vs planned for
   the four nutrients + kcal, difference highlighted with semantic colors only
   when eaten exceeds planned by >20%. Days with no data show gaps, not
   zero-lines.
8. **Drill-down panel** — clicking any data point (on any chart) opens a
   right-side panel for **that day**: the planned menu (8 slots, dish, kcal,
   targets, activity, brief) on top, and the **eaten meals** below — a table
   of time · slot · confirmed dish · kcal · carbs · sugar · sodium · protein.
   **No photos anywhere in the portal** (photos are analyzed live by Gemini
   in the patient app and are not retained in the PoC).

### 2C. Backend
9. `/api/meal-photo`: extend the vision prompt so each suggestion returns
   `{"dish","kcal","carbs_g","sugar_g","sodium_mg","protein_g"}` (integers,
   typical Indian single serving).
10. Photos are NOT stored in the PoC. `POST /api/meal-confirm` carries only
    slot, dish, and the five nutrition fields (no image). Do not create a
    Cloud Storage bucket or any photo-serving endpoint.
11. `MealConfirm` + `db.log_meal` persist the five nutrition fields.
12. `GET /api/patient/{id}/nutrition?days=N` → per-day
    `{date, kcal, carbs_g, sugar_g, sodium_mg, protein_g, meals_logged}`,
    oldest → newest, days without meals present with `meals_logged: 0` and
    nulls (not zeros) for nutrients.
13. `GET /api/patient/{id}/plans?days=N` → per-day
    `{date, nutrition_summary, targets, meal_plan, activity, brief}`.
14. `GET /api/patient/{id}/vitals?days=N` → daily vitals oldest → newest.
15. `GET /api/patient/{id}/day/{date}` → everything for the drill-down
    (plan + meals with nutrition).
16. `POST /api/alerts/{id}/resolve`; `GET /api/org/alerts?unresolved=1`.
17. Adherence computed server-side, returned on `GET /api/patient/{id}` as
    `adherence_7d` and `adherence_30d`.

### 2D. Seed data (extend `seed/reset_demo.py`; keep it idempotent)
18. **demo-ramesh** (Telangana; no egg, no meat; nuts allergy): **30 days** of
    daily vitals with a gently improving trend (sugar 165 → 135, two spike
    days ≥ 250 to exercise alerts), daily plans with `nutrition_summary`,
    and 3–6 confirmed meals/day with nutrition (Telangana dishes), with ~5
    unlogged days scattered in for realistic adherence (≈83%).
19. **Second patient `demo-lakshmi`** — Lakshmi Devi (synthetic), 52 F,
    158 cm / 66 kg, Tamil Nadu, doesn't eat beef & pork, no allergies, status
    active: **30 days**, well-controlled (sugar 105–125), high adherence
    (≈95%), Tamil dishes incl. fish/chicken. She is the "doing well" contrast
    to Ramesh in demos.
20. Keep Ananya (invited, no data) as the enrollment-state example. Seed a
    couple of unresolved alerts for Ramesh's spike days.

### 2E. Visual design (portal only — patient app unchanged)
Restrained clinical dashboard. Follow these rules; do not reinterpret:
- **No emoji anywhere in the portal.** Text labels or simple inline SVG line
  icons (16–20 px, single color).
- **Type:** Google Fonts `Inter` (or `Roboto`); body 14 px, secondary
  12–13 px, page title 20–22 px semibold, section headers 11 px uppercase
  with 0.06em letter-spacing. `font-variant-numeric: tabular-nums` on numbers.
- **Palette tokens:** background `#F6F8F9`; surface `#FFFFFF`; border
  `#E3E8EA`; text `#1B2426`; secondary text `#5B6B70`; single accent
  `#0F766E`; planned series `#0F766E`, eaten series `#5B6B70` (dashed);
  semantic only for state — success `#1B7F4B`, warning `#B7791F`, critical
  `#B42318`. No gradients, no colored card backgrounds, shadows ≤
  `0 1px 2px rgba(0,0,0,.06)`, radius ≤ 6 px.
- **Layout:** 8 px grid; nav 240 px; content max 1280 px; drill-down panel
  420 px, slides in from the right, closes with Esc.
- **Data density over decoration:** text-first stat tiles (value 22 px, label
  12 px); 1 px row dividers; right-aligned numbers; 1.5 px chart lines, light
  gridlines, faint area fill only under the eaten series.

### Acceptance criteria (validated against the deployed URL)
- [ ] No state/cuisine text anywhere in the portal markup.
- [ ] Header shows name, age, gender, BMI, exclusions, allergens, status,
      adherence "X of last 7 days".
- [ ] Nav shows alert badges; alerts panel lists and resolves alerts;
      resolving updates the badge without reload.
- [ ] Range selector switches all charts between 7 / 30 / 90 days.
- [ ] Glucose/BP/HR charts render 30 days for both demo patients.
- [ ] Four nutrition charts show planned AND eaten series; sugar chart is
      labelled "Sugar intake (g)"; today row highlights >20% overage.
- [ ] Clicking a data point opens the day drill-down with planned menu +
      eaten meals table; Esc closes it.
- [ ] Confirming a meal in the patient app (after live photo recognition)
      persists dish + nutrition and appears in that day's drill-down and in
      today's eaten totals; no images are stored or shown anywhere.
- [ ] `GET .../nutrition?days=30`, `.../plans?days=30`, `.../vitals?days=30`,
      `.../day/{date}` all return correct shapes for demo-ramesh and
      demo-lakshmi.
- [ ] Zero emoji in served portal markup; Inter/Roboto loads; only the palette
      tokens above are used in the portal stylesheet.
- [ ] Patient app visually unchanged (regression); no console errors through
      the full doctor flow; usable at tablet width.

## TASK 3 — Idempotency guard for the agent (small)

Pub/Sub delivers at-least-once. In `main.py` `_run_agent`: before running the
agent, if a plan for the patient exists with `generated_at` within the last
90 seconds for the same `vitals` values, skip and return the existing plan.
Add `generated_at` (ISO UTC) to saved plans. Acceptance: re-posting identical
vitals twice within 10 s yields one plan and one alert (for a ≥250 reading).

## TASK 4 — Firebase Auth (test-mode OTP) — only after Task 2 & 3 pass
1. Add Firebase to the project, enable Phone auth, configure **test phone
   numbers** (e.g. +91 5555550001 / code 123456) — no real SMS in the PoC.
2. Replace the simulated OTP screen with real `signInWithPhoneNumber` using a
   test number; store the Firebase UID on the patient doc at first login.
3. Keep a `?demo=1` query-param bypass so the demo video can skip auth.
Acceptance: patient logs in with the test number; refresh keeps the session;
`?demo=1` still allows the full flow.

## Working agreement

- After each task: deploy (`gcloud run deploy vitalsync-api --source backend
  --region asia-south1`) and report the service URL + what changed, with the
  acceptance checklist filled in. Validation happens with the product owner;
  fix-lists coming back from validation take priority over new work.
- Small commits per feature. If something in this brief is impossible as
  written, stop and report why instead of silently deviating.
- Never leave demo data in a test state: after any test that changes
  demo-ramesh, run `python3 seed/reset_demo.py`.
