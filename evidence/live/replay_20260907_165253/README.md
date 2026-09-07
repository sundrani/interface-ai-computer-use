# Genuine local replay evidence

Recorded on September 7, 2026, with the local banking demo and the example member-balance capability.

- `events.jsonl`: original run log. All three steps succeeded; the final `run_success` event records `savings_balance=$12,430.18`.
- `success.png`: original screenshot showing the fictional Demo Member account and matching savings balance.

The log and screenshot were reviewed before publication and contain demo data. The raw Playwright trace remains local and is not part of this published evidence bundle.

This run verifies deterministic replay. It does not establish that LLM discovery or the not-found/error path was executed. No API-backed discovery was performed as part of adding this evidence.

To reproduce, start `python -m demo_app.app` in one terminal, then run from the project directory with the virtual environment active:

```bash
computer-use replay \
  --artifact artifacts/member_balance.example.json \
  --params '{"member_id":"12345"}'
```
