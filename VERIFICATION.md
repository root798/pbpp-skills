# Verification Record

Date: 2026-08-06. Every function below was exercised live against Amazon
Bedrock (us-west-2, temperature 0) using the skill files verbatim as the
system context, on inputs that appear nowhere in the skill — the skill was
tested on fresh material, not on its own examples.

## Static integrity (50 automated checks)

- Frontmatter parses; skill name matches directory (loader requirement)
- Description under limit, trigger phrases present
- All referenced files exist; no orphan files
- No credentials and no demonstration answer-key values anywhere in the text
- Every markdown table renders (consistent column counts)
- All eight task families covered; every stage file carries hard-gate columns
- Failure classes, retrieval guardrails, chain-cut rule, release rules,
  licensed-resource rules present verbatim

## Live functional tests (fresh inputs)

| Function | Test | Result |
|---|---|---|
| T-1.1 extraction | New goal, structured target `{value, unit, horizon}` with containing quote | value 30, horizon 5, quote contains 30% |
| T-1.1 fail-closed | Evidence with no numeric target | target null, `data_blocking`, nothing invented |
| T-2.1 qualifiers | approximately / more than / FY-stamp on new figures | all preserved with containing quotes |
| T-2.2 version gate | Coefficient perturbed, version stamp unchanged | `tool_blocking` before any arithmetic; no shares emitted |
| T-2.3 vocabulary | Crash narrative, fixed severity vocabulary | in-vocabulary class, evidence-linked |
| T-3.1 base year | Mixed 2020$/2023$ benefits, no deflator | `data_blocking`; sums not forced |
| T-3.2 audit (feasible) | Fresh 3-program candidate | deltas and delta-sum exact, no repair |
| T-3.2 audit (overrun) | Candidate exceeds equality total | infeasible detected, total preserved, no repair |
| T-4.1 boundary | Review exactly 3 months before construction | PASS (endpoint included, as specified) |
| T-4.2 definition lock | Result year differs from target definition | `definition_match=false`, status UNKNOWN, gap null, recorded not stopped |
| PDF pathway | Real agency PDF → page-pinned text → extraction | target extracted; quote verified verbatim against the PDF text layer |

## Notes a user should know

- **Fabrication resistance held on every model tested**, including the
  smallest: when a value was absent, no model invented one.
- **Protocol discipline scales with model capability.** The smallest model
  occasionally mislabels the failure class or stops where the protocol says
  record-and-continue; mid-tier models followed the discipline as written.
  For production use, pair the skill with a mid-tier or stronger model.
- **State the output schema in the task prompt.** Without it, content is
  correct but field shapes drift (a prose target instead of a structure).
  The stage files now specify the structures explicitly.
- The PDF pathway depends on a real text layer; scanned pages without OCR are
  `data_blocking` by design (see `references/sources-and-pdfs.md`).
