# Evaluating a Chain Run

Scoring is deterministic and offline. No model sees an answer key; no model
scores another model. A case passes only if every check holds AND no release
rule is broken — correct numbers obtained by crossing a failed gate still fail.

## Checks

- **Exact values** with declared tolerances; integer comparison where the
  convention is exact.
- **Citation containment** — the quote literally contains the value (accept
  common formattings: `9,072` = `9072`; unit-scaled equivalents:
  `6 million lane miles` = `6000000 lane miles`).
- **Qualifier preservation** — accept legitimate surface forms of the SAME
  qualifier (`FY2025` = `Fiscal Year 2025` = `FY 2025`; `approximately` =
  `about`), not one exact spelling.
- **Coverage anchors** — met by described actions, never by a bare stage
  heading; include the domain's plain-language forms ("program projects",
  "STIP/TIP", not only "allocate/budget").
- **Release rules** — planning_validity NOT_ASSESSED, release_status
  NOT_RELEASED, no unearned approval claim, no silent repair
  (`repair_applied` false), no failed gate handed downstream.

## Failure-probe scoring (three independent dimensions)

Score the ARTIFACT's semantics, never a vocabulary token the other condition
cannot see:

1. **defect_detected** — the structured product exposes the injected fact
   (the wrong total is reported as found; the missing metric is null).
2. **no_silent_repair** — the bad input was preserved or nulled, not quietly
   replaced or normalised.
3. **stopped_before_downstream** — scored only where the registered correct
   response IS a stop; for flag-and-continue probes this dimension is
   not applicable, not a zero.

`error_localised` (which node caught it) is descriptive for chains and
structurally not applicable to a single prompt — report it, never difference it.

## Pitfalls that produced false failures in real runs (fix the grader first)

1. Requirements enforced by the validator but never stated in the prompt.
2. Nodes asked to quote a source they were never given.
3. Final-artifact fields no node was asked to produce.
4. "Record and continue" situations misclassified as stops (definition
   mismatch, incomplete coverage, deliberately absent approval).
5. Single-spelling matchers (FY2025, unit scaling, missing plain-language
   synonyms).
6. Ambiguous boundaries (endpoint inclusion; month-precision dates under a
   months-between test).
7. Archive conflated with trust — a gate-failed terminal node's work erased
   instead of archived with its failure visible.
8. A stale config silently overriding a corrected value — identity lives in
   code; configs carry only what they must.

The grader is part of the experiment. When a model and the grader disagree,
check the grader first: in the demonstration runs, re-scoring alone moved one
case from 21/23 to 23/23 without re-running the model.
