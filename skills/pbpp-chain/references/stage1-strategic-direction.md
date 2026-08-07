# Stage 1 — Strategic Direction (T-1.1 Goal-to-Task Identification)

Pattern: **linear decomposition**. Convert an adopted goal into the PBPP tasks
it requires, without inventing a target and without merging source extraction
with task design.

## Chain

| Node | Job | Hard gate |
|---|---|---|
| N1 | Retrieve the goal statement and every controlling passage. No task mapping yet. | source_present — a missing source is `data_blocking` |
| N2 | Extract objective, measure(s), target — target as a STRUCTURE a structure with `value` (number or null), `unit` (string or null), and `horizon_years` (number or null), never a prose string. Every numeric target carries the evidence ref and the verbatim quote that CONTAINS it. The supplied passages are the authority for this node; a frozen fixture passage is an acceptable containing quote (record provenance MEMO_FIXTURE). Only if NO supplied passage contains a target: target=null, `data_blocking` after one retrieval retry. Never substitute a plausible number. | every_number_has_containing_quote |
| N3 | Map ONLY the extracted objective onto task candidates for all four PBPP stages. No re-extraction, no new numbers. | no_new_numbers |
| N4 | Record dependencies, conflicts, unresolved items. Policy choices are escalated (`policy_escalation`), not resolved. | — |
| N5 | Traceability gate: every task block carries evidence or is marked PARTIAL/UNSUPPORTED with a per-stage FAIL — and the complete record is still EMITTED. All four stage blocks appear regardless. Stop only if the upstream artifact is missing entirely. | traceability |
| N6 | NOT EXECUTED — approval. Emit ready_for_approval, `release_status: NOT_RELEASED`. | — |

## Required output (state it; the schema alone does not)

A structured objective/measure/target record and FOUR PBPP-stage task blocks
(Strategic Direction, Analysis, Programming, Implementation and Evaluation),
each with source evidence, dependencies, missing-information fields, and a
traceability status. Across the blocks the map must address: performance
measures, data needed, corridor-level analysis, countermeasure analysis,
programming actions, milestones, named owners, monitoring, public reporting,
and adjustment on new evidence.

For an ordered protocol variant (e.g. corridor congestion decomposition):
SIX numbered task records — data collection, bottleneck diagnosis, forecast,
redistribution or mode shift, performance estimation,
prioritization/phasing/monitoring — and name the anchors the protocol must
cover (signal timing, volumes, delay, V/C, LOS, growth rate, benchmark,
phasing, monitoring). Every numeric input carries a source status: SOURCED,
MEMO_FIXTURE, or UNSUPPORTED.

## DO / AVOID

- DO keep extraction (N2) and mapping (N3) in separate nodes.
- DO fail closed when evidence is absent; DO return unresolved when a figure
  is only a fixture.
- AVOID one prompt that reads, proposes, and approves.
- AVOID a paraphrase presented as a quote.
- AVOID reordering steps for report-writing convenience.
- AVOID letting the generation node score itself.
