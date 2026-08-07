# Stage 4 — Implementation and Evaluation (T-4.1, T-4.2)

## T-4.1 Implementation plan — pattern: linear with iterative checks

| Node | Job | Hard gate |
|---|---|---|
| N1 | Form work packages; keep extracted official facts strictly separate from proposed values. | facts_vs_proposals |
| N2 | Dependencies, approvals, owners. Every owner is DOCUMENTED (named in evidence) or PROPOSED — never invented. | owner_status |
| N3 | Candidate phases and dates. Every date stays CANDIDATE until checked. | — |
| N4 | Dependency, schedule, lead-time, resource checks. A failed check returns the schedule to N3 — never silently rewrite a date. | lead_time_and_dependencies |
| N5 | Annual funding and multi-year totals against the declared constraints. Never move funds across years to force a pass. | totals |
| N6 | Record risks and every failed gate, then EMIT the archived artifact. The absent approval (N7) is expected, not `terminal`. | — |

Boundary duties for the specifier (both bit real runs):
- State whether a bound includes its endpoint ("at least 3 months: exactly
  3 months PASSES").
- Give dates the precision the check needs — a `YYYY-MM` date cannot support a
  months-between test; require `YYYY-MM-DD` and name the reference date the
  lead is measured to.

## T-4.2 Plan evaluation — TWO chains, never merged

### Policy consistency (preflight) — pattern: evidence comparison

| Node | Job | Hard gate |
|---|---|---|
| N1 | Retrieve and version-pin the legacy fixture and every current policy clause. An undated threshold cannot be called current. | vintage |
| N2 | Compare like measures by definition and vintage; classify each legacy item: unchanged, changed, retired_or_not_found, expanded_or_new, unknown. Topic similarity is NOT equivalence. Check the legacy mapping's own arithmetic; a self-contradictory claim is flagged, not carried forward. | definition_equivalence |
| E1 | Independent evaluator: every current target has a containing policy quote; no consistency percentage or compliance opinion emitted (both stay null). | — |

Leakage control when building such a case: if the agency publishes its own
legacy-to-current crosswalk, that crosswalk is the answer key — pin the
supplied pages so it stays OUT of the evidence.

### Performance monitoring — pattern: tool-mediated monitoring

| Node | Job | Hard gate |
|---|---|---|
| N4 | Load and version-pin each measure, target, desired trend, result, official status. A result whose year/scope differs from the target's definition gets `definition_match=false` — RECORDED on the row, never a `data_blocking` stop. | definition_lock |
| N5 | Deterministic gap calculator: gap only where `definition_match=true`; mismatches return gap=null, status UNKNOWN, with a data_quality_warning. | — |
| N6 | Reproduce the official status; keep status fields separate (meeting_target vs trend) — never collapse a multi-state field into yes/no. | status_reproduction |

- DO keep policy consistency and performance monitoring as separate chains.
- AVOID a single consistency score; AVOID computing across mismatched
  definitions; AVOID scoring recommendation reasonableness.
