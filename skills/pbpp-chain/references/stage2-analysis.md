# Stage 2 — Analysis (T-2.1, T-2.2, T-2.3)

## T-2.1 Data preparation and trip generation

### Extraction slice — pattern: direct structured generation

| Node | Job | Hard gate |
|---|---|---|
| N1 | Extract every metric from the evidence block IN ONE NODE (shared evidence, gate, and failure class = one node, not N handoffs). Preserve qualifiers verbatim: approximately, more than, fiscal-year stamps. A metric absent from the evidence goes to `missing_information` with value null — never inferred. | citation_containment |
| E1 | Independent evaluator (did not produce the artifact, has no answer key): per record, does the quote literally contain the value; unit right; qualifier preserved. Reports, never fixes. | — |

### Deterministic arithmetic slice — pattern: tool-mediated linear

| Node | Job | Hard gate |
|---|---|---|
| N3 | Bind inputs, category vocabulary, inclusion rule, rounding convention. Verify control totals (shares sum to 100%). On failure STOP `data_blocking` — never normalise, rescale, or redistribute. | share_total_equals_100 |
| N4 | Deterministic calculator (shown formula or versioned tool), all counts and declared subtotals in one run. | — |
| N5 | Independent conservation check: totals vs control, exactly the declared exclusions applied. Reports, never repairs. | conservation |
| N6 | Archive simplifications and limitations (e.g. "workforce × mode share is not an observed trip table"). | — |

## T-2.2 Travel demand forecasting — pattern: tool-mediated, branch for scenarios

| Node | Job | Hard gate |
|---|---|---|
| N1 | Validate the mode/zone table, coefficient set, units, frequency conversion. Compare the ACTUAL coefficients against the registered set for the declared version — the version string alone proves nothing. Mismatch: STOP `tool_blocking` BEFORE any arithmetic. | input_version |
| N2 | Calculation node. Arithmetic belongs in a TOOL (TM4 Section 2.2): if the agent has a code-execution runtime (Claude Code and most agent frameworks do), RUN the bundled calculator (`scripts/pbpp_calc.py logit`, path from the skill root) and paste its JSON — never compute floats in prose when a runtime exists. Only when no runtime exists at all, the model IS the calculator and must show every step as structured arithmetic — per mode: each coefficient×attribute term on its own line, their sum as the utility, then exp(utility); then the denominator as the sum of ALL exponentials; then each share as exp(U)÷denominator. Emit the worked terms alongside the results. Shares are the DIVIDED values — emitting exponentials as shares is the known failure. In-text float arithmetic remains unreliable even with worked terms (observed: correct utilities, wrong exponential sum); the N3 gate is the safety net, not a formality. | shares_are_divided |
| N3 | Independent check: RECOMPUTE every utility and share from the RAW inputs — never from N2's intermediates. An unrounded share sum differing from 1 by more than 1e-6 FAILS this gate and stops the chain (`tool_blocking`, back to N2); it is never explained away. A displayed-share sum of 100.1% after rounding is reported as a rounding artifact — never forced to 100.0. | share_conservation |
| N4–N5 | Scenario branches (only when the task asks): one branch per scenario, same calculator, deltas reported against the base. | — |
| N6 | Archive assumptions and rounding diagnostics. | — |

## T-2.3 Safety impact prediction — pattern: linear classification

| Node | Job | Hard gate |
|---|---|---|
| N1 | Bind the controlled vocabularies (severity levels, crash types, contributing factors — e.g. FARS/CRSS definitions). An out-of-vocabulary label is invalid output, not a new category. | vocabulary |

Production use of T-2.3 additionally requires, before any real prediction: an approved model and its documented domain of applicability, a stated confidence threshold below which the output is UNKNOWN, and the privacy thresholds of `node-protocol.md` applied to individual-level records. Without these, this chain is a structural demonstration only.
| N2 | Classify from the event description. Every predicted factor links to a phrase in the description. | evidence_linked |
| N3 | Independent check: classes valid, links present, no factor introduced from model memory. | — |

Individual-level crash records are sensitive (Memo 3A): no fine-tuning on raw
records, k-anonymity on small zones, suppress geocoded identifiers below the
spatial threshold.
