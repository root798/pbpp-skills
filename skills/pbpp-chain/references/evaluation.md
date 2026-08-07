# Evaluating a Chain Run

Deterministic offline checks are primary: no model sees an answer key, and a
case passes only if every check holds AND no release rule is broken — correct
numbers obtained by crossing a failed gate still fail. A model MAY serve as a
FIRST READER under a written rubric (TM4 Section 5.5), but it never replaces a
deterministic check or human approval, and it is subject to the bias controls
below.

## Three kinds of criteria (TM4 Section 5.4)

- **Hard gates** — automated checks that BLOCK on failure (budget, currency
  year, recomputation, containment, conservation).
- **Soft criteria** — scored by a reviewer against a rubric; they inform a
  judgment, they do not block.
- **Escalation triggers** — conditions a professional must decide (policy
  conflict, stakeholder trade-off). Routed via `policy_escalation`, never
  resolved by the chain.

## The acceptance record (archive with every released result)

```
chain_id | case_id | prompt_version | model_id_and_version |
retrieval_corpus_version | tool_versions | assumption_set_id
hard_gates      every gate id, PASS/FAIL, observed value
soft_criteria   reviewer score per rubric criterion, rubric id
escalations     failure_class, node_id, who decided, decision, date
unresolved      open issues the reviewer accepted the result despite
approver        name and role of the person who owns the judgment
```

A result without a complete acceptance record is not releasable, whatever its
scores.

## Evaluator bias controls (when a model is the first reader)

- Score criterion by criterion against the rubric; return PASS/FAIL plus the
  evidence ids used — never a rewritten output.
- Run every pairwise comparison twice, AB and BA; an order-dependent verdict
  is a tie.
- A model never evaluates its own output in the same workflow.
- Any criterion the evaluator cannot verify goes to the named human reviewer.

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

## Regression testing and change control (TM4 Section 5.6)

Version the prompt, model, retrieval corpus, and tool in every acceptance
record. Whenever ANY of them changes, re-run a fixed adversarial set with
known expected outcomes — ordinary passing cases do not detect a weakened
guardrail. The regression set includes, at minimum: a fail-closed case (value
absent from evidence), a silent-repair bait (inputs that do not reconcile), a
version-drift case (perturbed value under an unchanged stamp), an injection
attempt inside a source passage, an out-of-vocabulary label, and one case
whose correct outcome is an escalation.
