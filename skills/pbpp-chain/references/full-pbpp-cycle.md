# Running a Full PBPP Cycle

A complete run is four stages connected by an artifact relay: each stage
consumes the PASSING artifacts of the one before it and hands a versioned,
typed artifact to the next. This file is the operating procedure.

## The artifact relay

```
Stage 1  T-1.1   goal + policy evidence          →  TASK-MAP-v1
Stage 2  T-2.1   plan PDFs (pinned pages)        →  METRICS-v1
         T-2.2   model params + version registry →  FORECAST-v1
Stage 3  T-3.2   adopted program table (PDF)     →  PROGRAM-v1
         T-3.2   PROGRAM-v1 + candidate          →  AUDIT-v1
Stage 4  T-4.1   AUDIT-v1 + constraints          →  SCHEDULE-v1
         T-4.2   policy clauses (pinned)         →  INVENTORY-v1  (consistency chain)
         T-4.2   INVENTORY-v1 + results table    →  MONITORING-v1 (closes the loop
                                                    against the Stage-1 measures)
```

Rules of the relay:

- Only a PASSING artifact crosses a stage boundary. A failed artifact stays
  archived with its failure visible; the receiving stage never consumes it.
- Every artifact is named and versioned (`PROGRAM-v1`). A revision is a new
  version, never an in-place edit.
- The full audit trail = every node record + every artifact + the source
  manifest. Keep all three; the artifact alone is not the record.

## Session mechanics

Run ONE stage (often one chain) per working session, then carry forward:

1. Start: "Use the pbpp-chain skill. Stage N, family T-x.y. Here is the frozen
   input, the evidence passages (prepared per `sources-and-pdfs.md`), and the
   PASSING artifacts from the previous stage: [paste JSON]."
2. The chain executes node by node; you receive node records.
3. End: save the final artifact JSON and the node records. Paste the artifact
   into the next stage's opening prompt.

Do not run two stages in one chain "to save time" — the stage boundary is
where a human reviews the artifact before it becomes someone else's input.

## Worked sequence (prompts to type, condensed)

1. **Stage 1** — "T-1.1: decompose this adopted goal into the four PBPP stage
   task blocks. Goal: [text]. Evidence: [E1..E3]." → TASK-MAP-v1. The map's
   Analysis block tells you which Stage-2 extractions and forecasts to run.
2. **Stage 2** — "T-2.1: extract the operating metrics TASK-MAP-v1 requires.
   Evidence: [pinned pages]." → METRICS-v1. Then "T-2.2: compute mode shares
   with this coefficient set (version, registry attached)." → FORECAST-v1.
3. **Stage 3** — "T-3.2 input integrity: extract the adopted program amounts.
   Evidence: [pinned ES page]." → PROGRAM-v1. Then "T-3.2 audit: audit this
   candidate against PROGRAM-v1 under the declared constraint (status:
   experiment fixture unless the agency adopted it)." → AUDIT-v1.
4. **Stage 4** — "T-4.1: build the five-year schedule consuming AUDIT-v1
   under these constraints (state boundary inclusiveness and date
   precision)." → SCHEDULE-v1. Then the two T-4.2 chains SEPARATELY:
   consistency preflight → INVENTORY-v1; monitoring against the official
   results → MONITORING-v1.
5. **Close the loop** — MONITORING-v1's gaps land back on the Stage-1
   measures: the next cycle's T-1.1 run receives them as evidence.

## Failure routing across stages

| Failure surfaces in… | Route back to |
|---|---|
| Stage 2 extraction (`data_blocking`, value not in evidence) | the source preparer — re-pin pages (`sources-and-pdfs.md`) |
| Stage 3 audit (INFEASIBLE) | that is a FINDING, not an error — it goes in AUDIT-v1 and to the decision owner |
| Stage 4 schedule gate (lead time, totals) | N3 of the same chain; if the constraint itself is ambiguous, fix the specification and note the change |
| Any `policy_escalation` | the named human role; the chain waits |

## What a complete run archive contains

- source manifest (sha256, pinned pages, licences)
- every prompt version used
- every node record, including failed and archived-despite-failure nodes
- every versioned artifact
- the acceptance record per released artifact (`evaluation.md`) — versions,
  hard/soft outcomes, escalations, approver
- `planning_validity: NOT_ASSESSED`, `release_status: NOT_RELEASED` throughout —
  a full cycle produces decision-ready material, not decisions.
