# Proprietary and Copyright-Protected Resources

Planning work routinely depends on resources the model must not ingest:
AASHTO Green Book, Highway Capacity Manual (HCM), licensed datasets (INRIX,
HERE, Replica, StreetLight), and paywalled publications. Memo 3A sets the
governing rule: RAG over external publications is permitted only when the
source is licensed for that use or falls under fair-use guidelines, and the
licence of every text source is recorded in the dataset metadata package.

This file turns that rule into a chain pattern.

## The human-gated tool node

A licensed-resource step occupies the same slot as a deterministic tool node:
the chain prepares its input, a step outside the model produces the result,
and the chain validates and consumes it. The difference is that the "tool" is
a person with a licensed copy.

```
N(k)   PREPARE   model emits a typed parameter sheet: exactly the inputs the
                 licensed procedure needs (units stated), the edition/section
                 to apply (cite by NUMBER, e.g. "HCM 7th ed., Ch. 12"), and
                 an empty result schema. No licensed text is quoted.

HUMAN  EXECUTE   the user performs the lookup/computation offline in the
                 licensed resource and fills the result schema.

N(k+1) VALIDATE  model checks the returned artifact: schema, units, plausible
                 ranges, edition recorded. Provenance is set to
                 USER_SUPPLIED_LICENSED with resource name, edition, and
                 section number. gate: schema+units. On failure: tool_blocking
                 back to the user, never a guessed value.

N(k+2) CONSUME   downstream nodes use the validated artifact; summaries and
                 presentation of the RESULT are permitted (results and facts
                 are not the licensed expression).
```

## Rules

1. **Never paste licensed text into a prompt.** Cite edition and section
   number; the human applies the content offline.
2. **Never ask the model to reproduce a licensed table or method from
   memory.** The retrieval guardrail "do not use model memory to supply a
   missing policy, value, or citation" covers exactly this case. If the value
   only exists in the licensed source and no human result is supplied, the
   node returns null with `data_blocking`.
3. **Record the licence.** The returned artifact carries resource, edition,
   section, licence-holder (the agency seat), and date, mirroring the Memo 3A
   Section 2.7 metadata package.
4. **Prefer the open surrogate when one exists** and the task allows it:
   NPMRDS in place of INRIX/HERE speeds, LEHD LODES in place of licensed OD
   products. Name the substitution in `assumptions` so reviewers see the
   trade.
5. **AI before and after, human in the middle.** The model may structure
   inputs, check units, assemble, summarize, and present. The licensed
   analytical act itself is the human's.

## Worked shape (HCM capacity check inside a T-4.1 chain)

- N4a PREPARE: emits `{facility_type, segment_geometry, demand_vph, peak_hour_factor, units}` plus "apply HCM 7th ed., Chapter 12 motorized-vehicle method" and an empty `{capacity_vph, los, edition}` schema.
- Human runs the HCM procedure, returns `{capacity_vph: 1850, los: "D", edition: "HCM7"}`.
- N4b VALIDATE: units check, range check (capacity within published bounds for the facility class), provenance stamp; PASS hands off.
- N5 uses the validated capacity in the schedule feasibility gate. The memo may state "LOS D per HCM 7th ed., Ch. 12 (user-supplied computation)" — a fact citation, not licensed expression.
