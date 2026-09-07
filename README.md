# Computer-Use Automation System

A focused end-to-end implementation for interface.ai's computer-use take-home. The system uses an LLM during **discovery** to operate a real browser surface, records the successful flow into a typed/versioned capability artifact, and then **replays deterministically without an LLM**. It also enforces guardrails, classifies runtime outcomes, captures evidence, and contains a real pause/control/resume seam for human intervention.

## Verified local replay

A genuine local replay completed on September 7, 2026. Its [recorded events](evidence/live/replay_20260907_165253/events.jsonl) show successful fill, click, and read steps, ending with `savings_balance=$12,430.18`. The [success screenshot](evidence/live/replay_20260907_165253/success.png) shows the demo account balance.

See the [run notes](evidence/live/replay_20260907_165253/README.md). This verifies deterministic replay using the example capability. Genuine LLM discovery and a real not-found/error replay are not yet included. Files under `evidence/sample/` remain illustrative.

## What is implemented

- Goal-driven observe → decide → act loop against a live Playwright browser.
- Accessibility-tree-first observation (`aria_snapshot(mode="ai")`) rather than depending on clean DOM/test IDs.
- Typed Pydantic capability artifact with parameters, outputs, locator strategies, checkpoints, risks, and error rules.
- Deterministic replay with no model decisions.
- Explicit taxonomy: business outcome / recoverable / hard failure.
- Allowlisted hosts/actions and conservative risky-action policy.
- Redacted structured JSONL logs, screenshots, and Playwright trace evidence.
- Human handoff: automation pauses, retains the same headed browser session, exposes a minimal operator page, and resumes only after the operator signals control back.
- Local intentionally old-fashioned banking proxy UI with lookup, balance read, validation error, permission denial, session-expired state, and sub-account review flow.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
playwright install chromium
cp .env.example .env
export OPENAI_API_KEY='...'
```

Use Python 3.11+. Do not commit `.env` or credentials.

## Run without live model services

Terminal 1:
```bash
source .venv/bin/activate
python -m demo_app.app
```

Terminal 2 — deterministic replay using the checked-in example artifact:
```bash
source .venv/bin/activate
computer-use replay \
  --artifact artifacts/member_balance.example.json \
  --params '{"member_id":"12345"}' \
  --headless
```

Expected result: `status=success` and output `savings_balance=$12,430.18`.

Known business outcome:
```bash
computer-use replay \
  --artifact artifacts/member_balance.example.json \
  --params '{"member_id":"99999"}' \
  --headless
```

Expected result: `status=business_outcome`, `outcome_code=NOT_FOUND`. This is intentionally not reported as a crash.

## Genuine LLM discovery run (required before submission)

With the demo app running and `OPENAI_API_KEY` set:

```bash
computer-use discover \
  --goal 'Look up member {{member_id}} and return the current savings balance as savings_balance' \
  --url http://127.0.0.1:8000 \
  --artifact artifacts/member_balance.json
```

Then replay the newly discovered capability:

```bash
computer-use replay \
  --artifact artifacts/member_balance.json \
  --params '{"member_id":"12345"}'
```

The live run produces timestamped evidence under `evidence/live/`: JSONL decision/action logs, accessibility snapshots, screenshots, and a Playwright `trace.zip`.

**Evidence status:** A genuine successful replay log and screenshot are included under `evidence/live/`. `evidence/sample/` contains illustrative examples only. A genuine LLM discovery run and its replay validation still need to be recorded before completing the submission checklist below.

## Human-in-the-loop demo

Replay blocks risky steps unless `--allow-risky` is given. When a risky step is encountered in a headed run, the browser remains open on the exact live session, `intervention.json` is persisted, and a minimal operator page starts at `http://127.0.0.1:9010`. The operator can manipulate the already-open browser window, then click **Resume automation** to cede control back. The same evidence directory spans pre-handoff and post-handoff events.

The minimal UI is intentional: the important piece is the control-transfer model and preservation of the live browser/session. A production operator console would stream the session and enforce operator identity/leases.

## Tests

```bash
pytest -q
```

## Repository map

```text
src/interface_automation/
  discovery.py       LLM-driven discovery loop
  llm.py             model adapter
  recorder.py        decision transcript -> capability artifact
  models.py          typed/versioned contracts
  replay.py          deterministic production execution path
  surface.py         browser surface abstraction
  policy.py          allowlists + risk policy
  handoff.py         pause / same-session human control / resume
  logging_utils.py   evidence
  redaction.py       log redaction

demo_app/app.py      legacy-style target surface
artifacts/            reusable capability examples
/tests/               contract/policy/redaction tests
/evidence/sample/     illustrative evidence, clearly non-live
/evidence/live/       generated genuine run evidence (gitignored by default)
REPORT.md             design write-up
```

## Before submitting

1. Run one genuine discovery with your model API key.
2. Commit a sanitized genuine discovery evidence directory and at least one replay success plus one not-found/error replay. Remove secrets/PII first.
3. Inspect the Playwright trace and screenshots for accidental sensitive data.
4. Push this directory to a **public GitHub repository**.
5. Email the repo URL on its own line to `assignments@interface.ai` from the address used to apply.
