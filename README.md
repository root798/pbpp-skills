# PBPP Prompt-Chain Skills

Auditable chain-of-thought prompt skills for transportation planning, built
for **NCHRP Project 08-187 — Generative AI for Transportation Planning** as a
Task 5 companion deliverable to Technical Memorandum No. 4 (*Guide to
Chain-of-Thought Workflows and Prompt Design for GenAI-Enabled Transportation
Planning*).

The repository contains one skill, **`pbpp-chain`**, which runs a planning
task as a chain of small, checkable nodes instead of one large prompt. Every
node does a single job behind a hard gate, records the evidence that contains
each value it used, and hands downstream only what the next node may trust.
The output of a run is not just an answer — it is a record a reviewer can
re-read node by node.

## Why chains instead of one prompt

Public-sector planning work must be traceable: a number in a memo has to point
back to the page that contains it, a constraint check has to be visible, and a
failed input has to stop the work rather than silently propagate into it. A
single prompt can produce a correct answer, but it cannot show which check it
ran or which one it skipped. The chain design makes that record the primary
product:

- **One decision per node.** A node that both extracts and judges cannot be
  gated, because one gate cannot test two different claims.
- **Evidence-quote gates.** A value is accepted only with a verbatim quote
  that contains it. A quote that names the item but omits the number fails
  that number — even when the number happens to be right.
- **Typed failure classes.** `retriable`, `data_blocking`, `tool_blocking`,
  `policy_escalation`, `terminal` — each names its correction, so a failure
  routes to the right fix instead of a generic retry.
- **Fail closed, never repair silently.** Shares that sum to 100.5% stop the
  chain; they are never quietly normalised. A missing value is null, never a
  plausible guess.
- **Verification is not approval.** Every artifact carries
  `planning_validity: NOT_ASSESSED` and `release_status: NOT_RELEASED`.
  Matching a benchmark is verification; planning approval belongs to a human
  who is accountable for it.

In demonstration runs across seven commercial models (ten cases per model,
with a single-prompt control arm on identical inputs), the chain's advantage
concentrated where a value must clear a machine-checkable constraint before
acceptance — the fiscal-audit case passed under the chain on every model
tested, while the single prompt failed it outright on four. On open-ended
decomposition the chain adds traceability rather than accuracy. The skill
documents both behaviours; see `skills/pbpp-chain/references/evaluation.md`.

## Repository layout

```
skills/pbpp-chain/
  SKILL.md                                  entry point: task-family selector and the 3-step procedure
  references/
    node-protocol.md                        the node record, failure classes, chain-cut rule,
                                            retrieval guardrails, recurring gates, specifier duties
    stage1-strategic-direction.md           T-1.1  goal-to-task decomposition
    stage2-analysis.md                      T-2.1  data preparation / trip generation
                                            T-2.2  travel-demand forecasting
                                            T-2.3  safety impact prediction
    stage3-programming.md                   T-3.1  benefit-cost analysis
                                            T-3.2  prioritization and investment allocation
    stage4-implementation-evaluation.md     T-4.1  implementation plan
                                            T-4.2  plan evaluation (two chains: policy
                                            consistency and performance monitoring)
    sources-and-pdfs.md                     turning source PDFs into pinned, hashed evidence
                                            passages; page pinning as a leakage control
    full-pbpp-cycle.md                      running all four stages as one connected cycle
                                            (the artifact relay, session mechanics, failure routing)
    proprietary-resources.md                copyright-protected inputs: the human-gated tool
                                            node for HCM / AASHTO Green Book / licensed data
    evaluation.md                           deterministic scoring, probe dimensions, and the
                                            grader pitfalls that produce false failures
```

## Quick start (Claude Code)

```bash
git clone https://github.com/root798/pbpp-skills.git
mkdir -p .claude/skills
cp -r pbpp-skills/skills/pbpp-chain .claude/skills/
```

Then ask for planning work in plain language. The skill triggers on the task,
selects the family, and runs the chain:

> Use the pbpp-chain skill. Stage 3, T-3.2 audit: audit this candidate
> allocation against the adopted program table (attached) under the declared
> equality constraint.

For any other agent framework, paste `SKILL.md` plus `node-protocol.md` and
the relevant stage file into the system context.

## Running a single task

1. **Prepare evidence first.** If the source is a PDF, follow
   `references/sources-and-pdfs.md`: record the sha256, pin the physical
   pages the task needs, verify the text layer, and keep answer-key pages
   (published crosswalks, results tables) out of the pin.
2. **State the required output and its schema in the task prompt.** A schema
   shows field shapes; requirements ("four task blocks, one per PBPP stage")
   must be stated or they will not be enforced. Structured fields (a target
   as `{value, unit, horizon_years}`) prevent shape drift.
3. **Run the chain node by node** — one node per turn. Each node returns the
   node record defined in `node-protocol.md`; a failed gate stops the chain
   with a named failure class and archives the work done so far.
4. **Keep everything.** The audit trail is the node records plus the
   versioned artifacts plus the source manifest — not the final answer alone.

## Running the full PBPP cycle

`references/full-pbpp-cycle.md` is the operating procedure for connecting all
four stages on one program of work: Stage 1 produces the task map, Stage 2
the validated metrics and forecasts, Stage 3 the source-grounded program and
its audit, Stage 4 the schedule and the two evaluation chains — whose gaps
land back on the Stage-1 measures for the next cycle. One stage per session;
only PASSING artifacts cross a stage boundary; every artifact is named and
versioned.

## Copyright-protected and licensed resources

Some inputs must never enter a prompt: the AASHTO Green Book, the Highway
Capacity Manual, licensed datasets (INRIX, HERE, Replica, StreetLight),
paywalled publications. `references/proprietary-resources.md` handles these
with a **human-gated tool node**: the model prepares a typed parameter sheet
citing the resource by edition and section number only, the licensed
computation is performed by a person offline, and the result returns to the
chain as a validated artifact with provenance `USER_SUPPLIED_LICENSED`. The
model never quotes licensed text and never supplies a licensed value from
memory — if no human result is provided, the node returns null with
`data_blocking`. Licence metadata follows the Memo 3A governance rule
(recorded per source; retrieval only where licensed or fair use). Open
surrogates (NPMRDS, LEHD LODES) are preferred where the task allows.


## Provenance and scope

The chains implement TM4 Section 6 (task-specific prompt-chain library) and
Appendix B as executed and hardened in the August 2026 demonstration runs.
The skill contains prompts and protocols only: no credentials, no gold
answers, no licensed text. Nothing in this repository renders a planning
judgment; every run ends `NOT_RELEASED`.

NCHRP Project 08-187, Johns Hopkins University.
