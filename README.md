# PBPP Prompt-Chain Skills

NCHRP Project 08-187 — Generative AI for Transportation Planning.
Task 5 companion deliverable: the TM4 chain-of-thought workflow packaged as a
reusable agent skill, organized by PBPP stage.

## What this is

One skill, `pbpp-chain`, that runs a transportation-planning task as an
auditable node chain per Technical Memorandum No. 4: one decision per node,
hard gates, typed failure classes, evidence quotes that contain every value,
pass-only handoff, and `NOT_RELEASED` on everything — verification never
substitutes for planning approval.

```
skills/pbpp-chain/
  SKILL.md                                  entry point and family selector
  references/
    node-protocol.md                        node record, failure classes, chain-cut, guardrails
    stage1-strategic-direction.md           T-1.1 goal-to-task
    stage2-analysis.md                      T-2.1 data/trips, T-2.2 forecasting, T-2.3 safety
    stage3-programming.md                   T-3.1 benefit-cost, T-3.2 prioritization
    stage4-implementation-evaluation.md     T-4.1 implementation, T-4.2 evaluation
    proprietary-resources.md                copyright-protected inputs (Green Book, HCM, licensed data)
    evaluation.md                           deterministic scoring and grader pitfalls
```

## Use with Claude

- **Claude Code**: copy `skills/pbpp-chain/` into your project's
  `.claude/skills/` directory (or `~/.claude/skills/` for all projects), then
  ask for a planning task — e.g. "run a T-3.2 audit of this candidate
  allocation" or "decompose this safety goal into PBPP tasks".
- **Any agent**: paste `SKILL.md` plus the relevant stage reference into the
  system context.

The skill contains prompts and protocols only: no credentials, no gold
answers, no licensed text.

## Provenance

Chains follow TM4 (CoT Prompt Guide, Section 6 library and Appendix B) as
executed and hardened in the August 2026 demonstration runs (ten cases, seven
models, single-prompt control arm). The proprietary-resources protocol
implements the Memo 3A data-governance rule (licence recorded per source; RAG
only where licensed or fair use) at the workflow level.
