# Stage 3 — Programming (T-3.1, T-3.2)

## T-3.1 Benefit-cost analysis — pattern: tool-mediated linear

The failure-aware cut (from the TM4 worked derivation), NOT the
memo-shaped cut (gather → compute → recommend):

| Node | Job | Hard gate | Fails as |
|---|---|---|---|
| N1 | Retrieve evidence for each effect; every effect documented or absent | citation_containment | `data_blocking` |
| N2 | Normalize units, base year, discounting basis | units_and_base_year | `data_blocking` |
| N3 | Category check: each benefit in an approved category, no double counting | category | `policy_escalation` |
| N4 | Benefit-cost tool computes; inputs validated against the tool schema first | tool_schema | `tool_blocking` |
| N5 | Independent recomputation / sensitivity check | — | — |
| N6 | Archive; NO funding recommendation — that is the approver's step, NOT EXECUTED | — | — |

Never assert a BCR the inputs cannot support. If benefit derivations or
eligible-network baselines are absent, the honest output is the list of what
is missing (`data_blocking`), not an illustrative ratio.

## T-3.2 Prioritization and investment allocation

### Input-integrity slice — pattern: direct extraction with deterministic gate

| Node | Job | Hard gate |
|---|---|---|
| N1 | Extract program names and amounts from the adopted table, with currency basis and year. Each amount's quote must CONTAIN the amount — a quote naming the program without the number fails that amount even if the number is right. | citation_containment |
| E1 | Independent evaluator: controlled vocabulary, containing quotes, units/year basis, fiscal total. | — |

### Audit slice — pattern: constraint evaluation

| Node | Job | Hard gate |
|---|---|---|
| N2 | Bind the PASSING baseline artifact; validate candidate fields against the controlled vocabulary. | controlled_vocabulary |
| N6 | Deterministic fiscal validator (`scripts/pbpp_calc.py audit`, path from the skill root, when a runtime exists; supports equality and ceiling constraints): totals, per-program deltas, delta sum, constraint status. An overrun is INFEASIBLE — the chain never rebalances another line to force a pass (`repair_applied` stays false). | equality/ceiling as declared |
| E1 | Independent evaluator: no benefit-cost ratio asserted, no optimality claim, no silent repair. | — |
| N8 | NOT EXECUTED — human selection/approval. | — |

State the constraint's status in the fixture: an experiment equality total
derived from a published average is not an officially adopted ceiling, and the
run records the difference. "Feasible" never becomes "best" or "adopted": no
weight set exists unless the agency published one.

Cross-model note from the demonstration runs: this audit slice was the most
reproducible case in the whole set — the deterministic gate carries models
that fail the same task as a single prompt.
