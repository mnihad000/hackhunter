# PiggyBank Backend Tasks (Hackathon First, Roadmap After)

This is the backend execution checklist from start to finish.
Use this order unless a dependency says otherwise.

## Current Progress
- Completed: `A1` through `A6`, `B1` through `B14`, `C1`, `C2`, and `C5`.
- In place locally: `.env` created and `.gitignore` updated to exclude secrets.
- Environment update: `pip` bootstrapped, backend requirements installed, and backend test suite now passes locally.
- Verification status: `python -m pytest -q backend/tests -p no:cacheprovider --basetemp=C:\Users\nihad\AppData\Local\Temp\piggybank-pytest` → `44 passed`.
- Remaining warning-only cleanup: FastAPI `on_event` deprecation warnings and a few `datetime.utcnow()` deprecation warnings.

## Priority Guide
- `P0`: Must ship for hackathon MVP.
- `P1`: Strongly recommended for demo stability.
- `P2`: Future improvements (if time).

## Definition of Done (applies to every task)
- Code merged and runnable locally.
- Basic tests added or updated.
- Logs and error paths handled for the task scope.
- Short notes added to README/docs when behavior changes.

---

## Section A - Foundation

- [x] `A1 (P0)` Create backend project skeleton.
  - Deliverables: `backend/main.py`, `backend/routes/`, `backend/services/`, `backend/models/`, `backend/db/`, `backend/tests/`.
  - Acceptance: `uvicorn` starts and returns `200` on health endpoint.

- [x] `A2 (P0)` Add dependency and environment management.
  - Deliverables: `requirements.txt` (or `pyproject.toml`), `.env.example`, config loader.
  - Acceptance: app boot fails fast with clear errors when required env vars are missing.

- [x] `A3 (P0)` Add app settings for Twilio, Gemini, DB, scheduler, thresholds.
  - Deliverables: typed settings model and centralized config access.
  - Acceptance: no hardcoded secrets in source code.

- [x] `A4 (P0)` Set up database layer with SQLAlchemy session management.
  - Deliverables: engine/session helpers, dependency injection for DB sessions.
  - Acceptance: app can connect to local Postgres and run a simple query.

- [x] `A5 (P0)` Set up Alembic migrations.
  - Deliverables: migration config + initial migration workflow.
  - Acceptance: `upgrade head` creates schema on empty DB.

- [x] `A6 (P0)` Create base schema: `users`, `transactions`, `goals`, `feedback`, `nudge_events`.
  - Deliverables: ORM models + migration files.
  - Acceptance: foreign keys and indexes exist for common query paths.

- [ ] `A7 (P1)` Add structured logging and request IDs.
  - Deliverables: JSON or consistent log format, middleware for request context.
  - Acceptance: inbound `/sms` and outbound provider calls are traceable in logs.

- [ ] `A8 (P1)` Add baseline error handling framework.
  - Deliverables: exception handlers for validation errors and provider failures.
  - Acceptance: API returns consistent error payloads without stack trace leaks.

---

## Section B - Core MVP Flow (Hackathon Must Ship)

- [x] `B1 (P0)` Implement `POST /sms` Twilio webhook endpoint.
  - Deliverables: route + form parsing (`From`, `Body`) + quick response path.
  - Acceptance: Twilio can POST and receive valid TwiML response.

- [x] `B2 (P0)` Add inbound webhook validation.
  - Deliverables: Twilio signature validation (toggleable in local dev).
  - Acceptance: invalid signatures rejected in non-dev environments.

- [x] `B3 (P0)` Implement message classification (`transaction`, `feedback`, `command`, `unknown`).
  - Deliverables: classifier module with deterministic rules.
  - Acceptance: covered by unit tests for representative message samples.

- [x] `B4 (P0)` Implement transaction parser for `"<category> <amount>"`.
  - Deliverables: parser service returning normalized category + decimal amount.
  - Acceptance: invalid formats return user-friendly correction prompt.

- [x] `B5 (P0)` Implement user lookup/auto-create by phone number.
  - Deliverables: idempotent get-or-create flow.
  - Acceptance: repeated SMS from same number never creates duplicate users.

- [x] `B6 (P0)` Persist transactions from valid transaction messages.
  - Deliverables: transaction write path + timestamps + category normalization.
  - Acceptance: transaction appears in DB and is linked to correct user.

- [x] `B7 (P0)` Return fast acknowledgments via TwiML for each message type.
  - Deliverables: response templates for transaction saved, invalid format, feedback, unknown.
  - Acceptance: webhook consistently returns quickly and does not block on heavy work.

- [x] `B8 (P0)` Implement prediction engine v1 (rule-based, recency-weighted intervals).
  - Deliverables: `predict_for_user(user_id) -> Prediction[]`.
  - Acceptance: produces category, probability, time window, confidence for users with enough history.

- [x] `B9 (P0)` Implement nudge eligibility policy.
  - Deliverables: threshold + in-window + no-recent-duplicate gating.
  - Acceptance: policy blocks duplicate/fatiguing nudges in configured cooldown.

- [x] `B10 (P0)` Implement Gemini agent decision/message adapter.
  - Deliverables: `decide_and_generate_nudge(prediction, user_context) -> NudgeDecision`.
  - Acceptance: Gemini only decides action/tone, never overwrites numeric prediction fields.

- [x] `B11 (P0)` Implement outbound Twilio sender adapter.
  - Deliverables: `send_sms(to, body) -> ProviderResult`.
  - Acceptance: send success/failure is logged and persisted to `nudge_events`.

- [x] `B12 (P0)` Implement background scheduler for periodic prediction checks.
  - Deliverables: async loop or scheduler job runner.
  - Acceptance: scheduler scans users, evaluates nudges, and dispatches eligible messages.

- [x] `B13 (P1)` Implement feedback ingestion and lightweight behavior updates.
  - Deliverables: feedback parser + persistence + simple adaptation signals.
  - Acceptance: feedback rows are stored and can influence nudge cooldown/tone selection.

- [x] `B14 (P0)` Add dashboard-support endpoints.
  - Deliverables:
    - `GET /transactions`
    - `GET /predict`
    - `GET /goals`
    - `PATCH /goals`
  - Acceptance: endpoints return stable JSON contracts and support frontend teammate integration.

---

## Section C - Quality and Shipping

- [x] `C1 (P0)` Unit tests for parser, classifier, prediction engine, and nudge policy.
  - Acceptance: key decision logic has deterministic tests and edge-case coverage.

- [x] `C2 (P0)` Integration tests for `/sms` flow and DB persistence.
  - Acceptance: test covers valid transaction, invalid format, feedback, unknown input.

- [ ] `C3 (P1)` Mock-based tests for Gemini and Twilio adapters.
  - Acceptance: provider outages/errors produce graceful fallback behavior.

- [ ] `C4 (P1)` Add idempotency tests for repeated webhook deliveries.
  - Acceptance: repeated delivery does not duplicate transaction/nudge records unexpectedly.

- [x] `C5 (P1)` Add health/readiness endpoints and startup checks.
  - Deliverables: `/healthz` and `/readyz`.
  - Acceptance: readiness confirms DB and required integrations are configured.

- [ ] `C6 (P1)` Add Dockerfile for backend service.
  - Acceptance: image builds and runs with env-driven configuration.

- [ ] `C7 (P1)` Add `docker-compose` for local backend + Postgres.
  - Acceptance: one command starts local stack and migrations can run against it.

- [ ] `C8 (P1)` Create deploy checklist document.
  - Deliverables: env vars, migration step, Twilio webhook setup, scheduler run mode, smoke tests.
  - Acceptance: another teammate can deploy by following checklist only.

- [ ] `C9 (P1)` Run end-to-end smoke test.
  - Acceptance: inbound SMS -> transaction saved -> prediction eligible -> nudge sent/logged.

---

## Public APIs and Interfaces to Lock

- [ ] `I1 (P0)` Lock webhook contract for `POST /sms` (Twilio form payload + response format).
- [x] `I2 (P0)` Lock dashboard API response shapes for `GET /transactions`, `GET /predict`, `GET /goals`, `PATCH /goals`.
- [x] `I3 (P0)` Lock service interfaces:
  - `parse_message(text) -> ParsedMessage`
  - `predict_for_user(user_id) -> Prediction[]`
  - `decide_and_generate_nudge(prediction, user_context) -> NudgeDecision`
  - `send_sms(to, body) -> ProviderResult`

---

## Test Scenarios Checklist

- [x] Valid transaction SMS is parsed and stored.
- [x] Invalid transaction format returns guidance message.
- [ ] Feedback reply is stored and affects adaptation signal.
- [x] Unknown command returns safe help response.
- [ ] Duplicate/replayed webhook behavior is safe.
- [x] Prediction behavior with sparse, regular, and irregular histories.
- [x] Nudge gating inside vs outside predicted window.
- [x] Gemini unavailable fallback behavior.
- [ ] Twilio send failure retry/error behavior.
- [ ] End-to-end path from inbound SMS to logged nudge event.

---

## Section D - Future Improvements (If Time)

- [ ] `D1 (P2)` Queue-based async processing (Celery/Redis or equivalent).
- [ ] `D2 (P2)` More flexible NLP parsing for free-text transaction messages.
- [ ] `D3 (P2)` OCR receipt ingestion pipeline.
- [ ] `D4 (P2)` Plaid integration for automatic bank transaction import.
- [ ] `D5 (P2)` Prediction model upgrades (GBM/survival/sequence models).
- [ ] `D6 (P2)` Nudge fatigue controls and policy optimization (RL-style tuning).
- [ ] `D7 (P2)` Observability stack: metrics, traces, alerts, dashboards.

---

## Recommended Execution Order (Hackathon)

1. `A1 -> A6` (foundation + schema)
2. `B1 -> B7` (inbound SMS vertical slice)
3. `B8 -> B12` (prediction + nudge engine)
4. `B14` (frontend-support API contracts)
5. `C1 -> C3` (minimum reliability)
6. `C5 -> C9` (ship readiness)
7. `D*` only if MVP is stable

## Recommended Next Steps

1. Finish `C3` and `C4` by adding explicit Twilio failure-path tests and replay/idempotency coverage for repeated webhook deliveries.
2. Finish `C8` and `C9` by writing the deploy checklist and running a real manual smoke test with Twilio + Gemini configured.
3. Configure the public `POST /sms` Twilio webhook and verify a real inbound message hits the backend.
4. Optional cleanup after MVP is stable: replace deprecated FastAPI startup/shutdown hooks with lifespan handlers and switch internal UTC calls to timezone-aware `datetime.now(dt.UTC)`.
