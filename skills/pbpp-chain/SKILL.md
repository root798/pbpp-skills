---
name: pbpp-chain
description: >
  Execute a transportation-planning task as an auditable TM4 node chain,
  organized by PBPP stage. Use this skill whenever the user asks for planning
  work of any kind — goal or objective decomposition, extracting metrics or
  targets from a plan or policy PDF, trip generation or travel-demand and
  mode-choice calculation, crash or safety outcome prediction, benefit-cost
  analysis, project prioritization, budget or investment allocation and
  audits, implementation schedules, or checking a plan against policy and
  monitoring performance — even if they do not say "chain", "PBPP", or name a
  task family. Also use it when planning work must be traceable, reviewable,
  or defensible to an agency reviewer. Produces inspectable node records with
  evidence quotes, gates, and failure classes instead of free-text reasoning.
  Routine one-off lookups or pure text editing do not need the chain.
  NCHRP 08-187 Task 5 deliverable.
---

# PBPP Prompt-Chain Skill

This skill runs a planning task as a chain of small, checkable nodes rather
than one large prompt. Each node does one job, carries one hard gate, and hands
off only what the next node may trust. The design follows NCHRP 08-187
Technical Memorandum No. 4 (Chain-of-Thought Workflows and Prompt Design for
GenAI-Enabled Transportation Planning).

## The seven-step outer workflow (TM4 Section 3.2 — governs every run)

(1) state the decision and its acceptance criteria — including the decision
owner; (2) identify required modalities and data-quality gates; (3) serialize
and align inputs (`references/sources-and-pdfs.md`; artifacts carry the
serialization contract in `references/node-protocol.md`); (4) define nodes,
schemas, gates, and failure actions (the stage references below); (5) execute
one passing node at a time; (6) correct, retrieve, rerun, revert, escalate,
or stop according to the failure class; (7) synthesize and archive — sources,
assumptions, tool calls, unresolved issues, approvals, prompt and model
versions — as the acceptance record in `references/evaluation.md`.

Steps 1–3 happen BEFORE any node runs. A chain started without stated
acceptance criteria and serialized inputs is not a TM4 run.

## Step 1 — Identify the task family

| PBPP stage | Family | The task looks like | Reference |
|---|---|---|---|
| 1 Strategic Direction | T-1.1 | "Turn this goal into the tasks it requires" | `references/stage1-strategic-direction.md` |
| 2 Analysis | T-2.1 | "Extract the metrics / prepare data / estimate trips" | `references/stage2-analysis.md` |
| 2 Analysis | T-2.2 | "Forecast demand / mode shares / assignment" | `references/stage2-analysis.md` |
| 2 Analysis | T-2.3 | "Predict crash outcome from this description" | `references/stage2-analysis.md` |
| 3 Programming | T-3.1 | "Is this investment worth it (benefit-cost)" | `references/stage3-programming.md` |
| 3 Programming | T-3.2 | "Prioritize / allocate / audit this portfolio" | `references/stage3-programming.md` |
| 4 Implementation & Evaluation | T-4.1 | "Build the phased implementation plan" | `references/stage4-implementation-evaluation.md` |
| 4 Implementation & Evaluation | T-4.2 | "Check the plan against policy / monitor performance" | `references/stage4-implementation-evaluation.md` |

Preparing inputs: source documents (PDFs) become pinned, hashed evidence
passages per `references/sources-and-pdfs.md` BEFORE any node runs. To run all
four stages as one connected cycle, follow `references/full-pbpp-cycle.md`.

Load `references/node-protocol.md` first in every run — it defines the node
record, the failure classes, and the handoff contract that all chains share.
If any input is a licensed or copyright-protected resource (AASHTO Green Book,
Highway Capacity Manual, INRIX, Replica, StreetLight, paywalled publications),
also load `references/proprietary-resources.md` before writing any prompt.

## Step 2 — Execute the chain node by node

One node per response turn. For each node:

1. State the node id, its single job, and its hard gate.
2. Do only that node's work. Do not perform a later node's job early.
3. Emit the node record (the envelope in `node-protocol.md`) — evidence quotes
   that CONTAIN every number used, assumptions, the gate result, a failure
   class if the gate failed, and the handoff statement.
4. If the gate fails: stop the chain, name the failure class, report what is
   missing. Never repair an input silently. Never invent a plausible value.
   A gate-failed terminal node still archives its work — a failed gate must be
   visible in the record, not erase the record.

Deterministic arithmetic (trip totals, logit shares, budget sums, performance
gaps) goes to a calculation the reader can re-run. The bundled
`scripts/pbpp_calc.py` covers the four recurring calculations (logit, trips,
audit, gaps) — run it and paste its JSON into the node record instead of
computing floats in prose. Where the calculation needs a
licensed resource, use the human-gated tool node from
`references/proprietary-resources.md`.

## What this skill can and cannot guarantee

This is a protocol the agent follows, not a hosted runner. Gate stops,
pass-only handoff, and evaluator independence are procedures; they are
mechanically guaranteed only when an external runner parses the node records
and controls what enters each context. When running inside a single session,
apply two mitigations: run evaluator nodes in a FRESH context (a subagent or a
new conversation) given only the artifact and its inputs — never the producing
transcript — and route every calculation through `scripts/pbpp_calc.py`, whose
verdicts cannot be talked into passing. The project's reference runner, which
enforces these mechanically, lives in the research harness, not in this skill.

## Step 3 — Assemble and report

Assembly copies fields from passing node outputs into the final artifact. It
introduces no new values. The final artifact always carries:

```
planning_validity: NOT_ASSESSED
release_status:    NOT_RELEASED
```

Matching a benchmark is verification, not planning approval. This skill never
claims approval, never emits an overall consistency percentage for a policy
crosswalk, and never asserts a benefit-cost ratio that its inputs cannot
support. Scoring guidance for whoever evaluates the output is in
`references/evaluation.md`.
