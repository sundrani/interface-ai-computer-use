# 1. Architecture

The system has five deliberately small boundaries: **surface adapter**, **LLM discovery planner**, **artifact recorder**, **deterministic replay executor**, and **policy/evidence/handoff services** shared by both paths.

```text
                 DISCOVERY (model in loop)
Goal + target ──> Surface.observe() ──> LLM planner ──> policy ──> Surface.act()
      │                                                        │
      └──────────────── successful typed decisions ────────────┘
                               │
                               v
                    CapabilityArtifact v1
                               │
                               v
                 PRODUCTION REPLAY (no model)
Inputs ──> validator ──> replay executor ──> policy ──> Surface.act/read
                              │    │
                       outcomes    ├── evidence
                              │    └── human handoff
                              v
                   structured RunResult
```

The load-bearing decision is to keep **intent** out of replay. The model is useful when discovering a new flow, but every production invocation executes a reviewed artifact with fixed steps and explicit targeting/checkpoints. This makes behavior cheaper, debuggable, auditable, and policy-enforceable.

I chose Playwright for the concrete implementation, but the artifact does not encode Playwright APIs. `BrowserSurface` is the seam. Discovery observes an accessibility-oriented snapshot and acts through abstract locator strategies; replay consumes the same abstract strategies. A desktop implementation could satisfy the same interface with UI Automation/AX APIs or a screenshot+coordinate adapter.

I intentionally did not build queues, distributed schedulers, or tenant infrastructure. The assignment's key risk is correctness of the capability/replay contract, not horizontal scaling plumbing.

# 2. Artifact schema

`CapabilityArtifact` is a typed, versioned contract rather than a transcript. It contains:

- capability identity/version and target app compatibility metadata;
- typed runtime inputs, including a `sensitive` flag;
- typed outputs mapped to extraction steps;
- ordered steps with action type, locator strategy, parameter template, timeout, risk, checkpoint, and error rules;
- a final success checkpoint;
- an evidence pointer for provenance.

A locator is represented as a strategy (`role_name`, `label`, `text`, or `css`) instead of a raw selector. The preferred strategy is accessible role + name because it survives markup rearrangement better than deep CSS/XPath and generalizes conceptually to desktop accessibility trees. CSS is a last-resort escape hatch for hostile legacy surfaces.

Parameter values are never baked into the reusable artifact. `{{member_id}}` is bound at invocation time. This prevents a discovery transcript from accidentally becoming a PII-bearing executable script and makes the capability agent-invocable.

The schema includes `tenant_scope` and `app_version_range` so the same base artifact can later be specialized without cloning everything. In production I would add signed approval state (`draft -> reviewed -> approved`), schema migration tooling, and immutable artifact hashes.

# 3. Determinism & error handling

Replay performs no LLM call. For each step it resolves the declared locator, binds typed parameters, executes one fixed action, applies explicit waits/checkpoints, scans for known runtime conditions, and records a structured event.

The error taxonomy is intentionally part of the contract:

- **Business outcome** — e.g. `NOT_FOUND`. The run returns `status=business_outcome`; the caller can branch normally.
- **Recoverable condition** — e.g. session/transient load. A rule can allow a bounded retry. Retries are finite and recorded.
- **Hard failure / escalation** — e.g. permission denial, missing target, or unmet checkpoint. The executor stops with `failed_step_id`, observed state, screenshot, and trace.

This distinction avoids the common failure mode where a legitimate negative result is reported as infrastructure failure. It also prevents blind continuation after a click: checkpoints establish that the expected state was actually reached.

UI drift is secondary here because the brief describes stable enterprise UIs. Still, target strategies are layered so a future locator resolver can try approved fallbacks and record which one matched. I would never silently let an LLM rewrite a production capability. A bounded assisted-recovery mode could propose a one-step repair, but it should create a new draft artifact/version for review.

# 4. Heterogeneity & multi-tenant

The key abstraction is `Surface`: observe, navigate, find/control a target, act, read, capture evidence. The artifact stores **what control means** rather than browser-specific calls. Implementations can therefore include:

- modern/legacy web: accessibility roles first, labels/text second, CSS/XPath only when unavoidable; frame context can be added to a locator strategy;
- native desktop: Windows UI Automation, macOS Accessibility, or equivalent role/name/value paths;
- visual-only surfaces: screenshot region + anchor/template/coordinate strategy, ideally with a stable visual anchor and screen geometry constraints.

For multi-tenant reuse, I would model a three-layer capability:

1. **vendor base artifact** — canonical workflow and semantic target names;
2. **version profile** — locator/checkpoint overrides for vendor versions;
3. **tenant overlay** — smallest possible set of branding/configuration-specific overrides.

At invocation, `(vendor, app_version, tenant)` resolves to a base artifact plus overlays. Replay telemetry produces a compatibility signal by locator/checkpoint. A rising failure rate or a new app fingerprint (title/version markers/accessibility anchors) marks the capability `needs_validation` for that profile instead of immediately re-recording every tenant.

# 5. Escalation & handoff

Escalation can be raised by discovery (stuck/max steps), replay (unhandled state/permission issue), or policy (risky action). The intervention record includes capability/goal, current step, reason, screenshot/evidence path, and session context.

The implementation keeps the **same headed browser and browser context alive** while automation is paused. A tiny local operator HTTP page exposes the intervention context and a Resume control. The human operates that already-open browser window; pressing Resume transfers control back to automation. This is intentionally minimal but makes the seam real: automation does not destroy the session or restart the task.

Production would formalize this with a control lease: `AUTOMATION`, `HUMAN(operator_id)`, `PAUSED`, each transition compare-and-set with an expiry. A remote-browser gateway would stream the same session into the operator console. Every operator action/identity would be appended to the audit stream. Automation could only resume after the human explicitly relinquishes the lease.

# 6. Safety

Safety is enforced before action rather than added only to prompts. The policy layer checks an explicit host allowlist and action allowlist. Steps carry risk classification. Risky/irreversible actions are blocked by default and routed to human approval; the demo stops at a review screen rather than actually creating an account.

Artifacts contain parameter placeholders, not real secrets. Logs run through redaction and should never intentionally capture credentials/tokens/full PII. Screenshots/traces are richer evidence and therefore more sensitive; in production they would have short retention, tenant-scoped encryption, strict RBAC, and capture suppression around credential fields. The current regex redactor is intentionally small and is not sufficient for production DLP.

The model is also not trusted as a security boundary. Discovery can only request actions that the policy layer permits, and production replay does not grant the model an opportunity to choose arbitrary navigation or actions.

# 7. Cuts

I deliberately cut breadth rather than core capabilities. I did not build distributed execution, a real remote co-browsing console, desktop automation, tenant databases, artifact approval UI, or automatic drift repair. The operator UI is minimal and the demo app is local so the submission is safe and reproducible.

With more time, my priorities would be: (1) approval/signing and immutable artifact versions; (2) a stronger locator resolver with frame/accessibility/visual fallbacks and per-strategy telemetry; (3) control leases and authenticated remote session streaming for human handoff; (4) vendor/version/tenant overlays with compatibility scoring; and (5) multi-run stability reports that gate unattended execution on demonstrated replay success.
