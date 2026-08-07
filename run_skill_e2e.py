"""End-to-end skill exercise: every family's FULL chain, driven by the skill
files themselves, on a fresh scenario (Metro Riverton) with a cross-stage
artifact relay. Node job text is parsed from the stage files' tables so the
run tests the skill as written, not a paraphrase.
"""
import boto3, json, re, sys, math
from pathlib import Path

BASE = Path("skills/pbpp-chain/references")
R = lambda f: (BASE / f).read_text(encoding="utf-8")
PROTO = R("node-protocol.md")
rt = boto3.client("bedrock-runtime", region_name="us-west-2")
MODEL = "us.amazon.nova-pro-v1:0"

def parse_nodes(file, heading_sub):
    """Rows (node_id, job, gate) of the table under the heading containing sub."""
    txt = R(file)
    m = re.search(re.escape(heading_sub), txt)
    seg = txt[m.start():]
    rows = []
    for line in seg.splitlines():
        mm = re.match(r"\|\s*(N\d+[a-z]?|E\d)\s*\|(.*)\|(.*)\|\s*$", line)
        if mm:
            rows.append((mm.group(1), mm.group(2).strip(), mm.group(3).strip()))
        elif rows and line.startswith("##"):
            break
    return rows

def call(stage_file, user, tok=1500, _retry=True):
    system = ("You are one node in an auditable PBPP chain. Follow this protocol exactly.\n\n"
              + PROTO + "\n\n" + R(stage_file)
              + "\n\nReturn ONE JSON node record and nothing else.")
    r = rt.converse(modelId=MODEL, system=[{"text": system}],
                    messages=[{"role": "user", "content": [{"text": user}]}],
                    inferenceConfig={"maxTokens": tok, "temperature": 0})
    t = "".join(p.get("text", "") for p in r["output"]["message"]["content"])
    m = re.search(r"\{.*\}", t, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        if _retry:  # retriable per the protocol: restate the schema, retry once
            return call(stage_file, user + "\n\nYour previous reply was not valid "
                        "JSON. Return ONLY one valid JSON node record.", tok, _retry=False)
        return None

def run_chain(name, stage_file, heading, fixture, evidence, required, relay=None,
              skip=("N6-not-executed",)):
    nodes = parse_nodes(stage_file, heading)
    upstream, records, stopped = {}, [], None
    for nid, job, gate in nodes:
        if "NOT EXECUTED" in job:
            records.append((nid, "NOT_EXECUTED", None)); continue
        if stopped:
            records.append((nid, "SKIPPED", None)); continue
        user = (f"NODE {nid} (chain {name}). YOUR JOB (verbatim from the chain library): {job}\n"
                f"HARD GATE: {gate}\n\nREQUIRED OUTPUT OF THE WHOLE CHAIN: {required}\n\n"
                f"FROZEN INPUT:\n{json.dumps(fixture, ensure_ascii=False)}\n\n"
                f"SUPPLIED EVIDENCE:\n{evidence}\n")
        if relay:
            user += f"\nPASSING ARTIFACTS FROM THE PREVIOUS STAGE (relay):\n{json.dumps(relay, ensure_ascii=False)[:1200]}\n"
        if upstream:
            user += f"\nPASSING UPSTREAM ARTIFACTS (transitive trust):\n{json.dumps(upstream, ensure_ascii=False)[:2400]}\n"
        rec = call(stage_file, user)
        if rec is None:
            records.append((nid, "UNPARSED", None)); stopped = nid; continue
        st = str(rec.get("status", "")).upper()
        records.append((nid, st, rec.get("failure_class")))
        out = rec.get("output")
        if st == "PASS" and isinstance(out, dict):
            upstream[nid] = out
        elif st == "FAIL":
            stopped = nid
            if isinstance(out, dict): upstream[nid] = out   # archive
    final = {}
    for nid in upstream: final.update(upstream[nid])
    return final, records, stopped

results = []
def score(name, checks, records, stopped):
    ok = all(c for _, c in checks)
    results.append({"chain": name, "pass": ok,
                    "nodes": [f"{n}:{s}" for n, s, _ in records],
                    "stopped": stopped,
                    "checks": [(n, bool(c)) for n, c in checks]})
    print(f"{'PASS' if ok else 'FAIL'}  {name}  nodes={'->'.join(n for n,s,_ in records if s not in ('SKIPPED',))}"
          + (f"  stopped={stopped}" if stopped else ""))
    for n, c in checks:
        if not c: print(f"        check FAIL: {n}")

D = lambda o: json.dumps(o, ensure_ascii=False).lower()

# ============ Stage 1 · T-1.1 ============
f1, r1, s1 = run_chain("T-1.1", "stage1-strategic-direction.md", "## Chain",
    {"goal_statement": "Reduce weekday bus corridor delay in Metro Riverton by 12% within 3 years."},
    '[E1] (fixture) Goal: "Reduce weekday bus corridor delay in Metro Riverton by 12% within 3 years."\n'
    '[E2] (plan notes) The transit plan tracks corridor delay, on-time performance, and boarding counts; '
    'data sources include APC counts, AVL logs, roadway characteristics, and census demographics. '
    'Programming aligns projects with the regional TIP; implementation names Riverton Transit as lead '
    'agency with annual milestones, public reporting, and program adjustment on new evidence.',
    "A structured objective/measure/target record and FOUR PBPP-stage task blocks with evidence, "
    "dependencies, missing information, and traceability status per block.")
d = D(f1)
score("T-1.1 goal-to-task (6 nodes)", [
    ("target value=12", bool(re.search(r'"value":\s*12', d))),
    ("horizon=3", bool(re.search(r'"horizon_years":\s*3', d))),
    ("quote contains 12%", "12%" in d),
    ("4 stage blocks", d.count('"pbpp_stage"') >= 4 or all(k in d for k in
        ["strategic direction", "analysis", "programming", "implementation"])),
], r1, s1)
TASK_MAP = f1

# ============ Stage 2 · T-2.1 extraction (with real relay) ============
f2, r2, s2 = run_chain("T-2.1x", "stage2-analysis.md", "### Extraction slice",
    {"request": "Extract every operating metric with containing quotes; preserve qualifiers."},
    "[E1] (Riverton transit factbook p.4) The agency operates a fleet of 240 buses, serves "
    "approximately 18,500 weekday boardings, and delivered more than 96,000 revenue miles in FY2025.",
    "One record per metric: metric, value, unit, qualifier, evidence quote that CONTAINS the value.",
    relay={"TASK-MAP-v1": {"analysis_needs": "operating metrics for the delay-reduction program"}})
d = D(f2)
score("T-2.1 extraction (N1+E1)", [
    ("240 fleet", "240" in d),
    ("18,500 + approximately", ("18,500" in d or "18500" in d) and "approximately" in d),
    ("96,000 + more than + FY2025", ("96,000" in d or "96000" in d) and "more than" in d and "fy2025" in d),
], r2, s2)

# ============ Stage 2 · T-2.1 arithmetic ============
fx = {"total_riders": 46000, "mode_shares_pct": {"Bus": 55.0, "BRT": 30.0, "Shuttle": 15.0},
      "convention": {"rounding_rule": "round half up to integer"}}
f3, r3, s3 = run_chain("T-2.1a", "stage2-analysis.md", "### Deterministic arithmetic slice",
    fx, "(inputs are the frozen fixture; shares must total 100%)",
    "Per-mode rider counts, the all-mode total, the binding record, and a conservation check.")
d = D(f3)
score("T-2.1 arithmetic (N3-N6)", [
    ("Bus 25300", "25300" in d or "25,300" in d),
    ("BRT 13800", "13800" in d or "13,800" in d),
    ("Shuttle 6900", "6900" in d or "6,900" in d),
    ("conservation true", '"all' in d and "46000" in d.replace(",", "")),
], r3, s3)

# ============ Stage 2 · T-2.2 logit (registry supplied) ============
u_car = -0.05*22 - 0.15*4.5
u_brt = -0.05*28 - 0.15*2.0 - 0.3
sc = math.exp(u_car) / (math.exp(u_car) + math.exp(u_brt))
f4, r4, s4 = run_chain("T-2.2", "stage2-analysis.md", "## T-2.2",
    {"modes": {"Car": {"time_min": 22, "cost_usd": 4.5}, "BRT": {"time_min": 28, "cost_usd": 2.0, "asc": -0.3}},
     "coefficients": {"time": -0.05, "cost": -0.15}, "coefficient_version": "RIV-v1",
     "pinned_registry": {"RIV-v1": {"time": -0.05, "cost": -0.15}}},
    "(constructed fixture; registry supplied for the version gate)",
    "Per-mode utility, exp(utility), unrounded share; denominator; unrounded share sum.")
d = D(f4).replace(" ", "")
got = re.search(r'"car"[^}]*?"unrounded_share":([0-9.]+)', d) or re.search(r'"unrounded_share":([0-9.]+)', d)
share_ok = got and abs(float(got.group(1)) - sc) < 0.02
score("T-2.2 mode choice (N1-N3,N6)", [
    (f"Car share ≈ {sc:.3f}", bool(share_ok)),
    ("version gate passed (no drift)", not s4),
    ("share sum ≈ 1", bool(re.search(r'"unrounded_share_sum":(0\.9|1\.0|1,|1})', d) or '"unrounded_share_sum":1' in d)),
], r4, s4)

# ============ Stage 2 · T-2.3 classification ============
f5, r5, s5 = run_chain("T-2.3", "stage2-analysis.md", "## T-2.3",
    {"vocabulary": {"severity": ["No Injury", "Minor", "Serious", "Fatal"],
                    "crash_type": ["Angle", "Rear End", "Pedestrian", "Fixed Object"]}},
    "[EVENT] At dusk a transit bus rear-ended a stopped delivery van at 25 mph; "
    "the van driver was hospitalized overnight with neck injuries.",
    "severity and crash_type from the controlled vocabularies, each linked to a phrase in the event.")
d = D(f5)
score("T-2.3 safety classification (N1-N3)", [
    ("severity in vocab (Serious)", '"serious"' in d),
    ("type Rear End", "rear end" in d or "rear-end" in d),
    ("evidence-linked", "hospitalized" in d),
], r5, s5)
METRICS = {"fleet": 240, "weekday_boardings": "~18,500", "corridor_delay_target": "-12% / 3y"}

# ============ Stage 3 · T-3.1 BCA ============
f6, r6, s6 = run_chain("T-3.1", "stage3-programming.md", "## T-3.1",
    {"effects": {"travel_time_savings_musd": 1.8, "safety_benefit_musd": 0.9},
     "base_year": "2024 dollars (both effects and cost)", "capital_cost_musd": 1.5,
     "approved_categories": ["travel time", "safety"]},
    "[E1] (study memo) Travel-time savings are valued at $1.8M and safety benefits at $0.9M, "
    "both in 2024 dollars; the capital cost is $1.5M in 2024 dollars.",
    "Normalized units check, category check, the computed benefit-cost ratio with the formula shown, "
    "an independent recomputation, and NO funding recommendation.",
    relay={"METRICS-v1": METRICS})
d = D(f6)
score("T-3.1 benefit-cost (N1-N6)", [
    ("BCR = 1.8", "1.8" in d),
    ("formula visible", "2.7" in d and "1.5" in d),
    ("no funding recommendation", "recommend funding" not in d and '"recommendation"' not in d),
], r6, s6)

# ============ Stage 3 · T-3.2 extract -> audit (relay within stage) ============
f7, r7, s7 = run_chain("T-3.2x", "stage3-programming.md", "### Input-integrity slice",
    {"request": "Extract the three program names and annual amounts with containing quotes."},
    "[E1] (adopted program, printed p. S-2) The adopted program dedicates $45 million per year to "
    "Safety, $80 million to Preservation, and $95 million to Mobility, in constant 2024 dollars.",
    "PROGRAM-v1: name/amount/unit/year records with containing quotes and the fiscal total.")
d = D(f7)
ok_ext = all(x in d for x in ["45", "80", "95"]) and "220" in d
score("T-3.2 extraction (N1+E1)", [("45/80/95 + total 220", ok_ext),
                                   ("2024 basis", "2024" in d)], r7, s7)

f8, r8, s8 = run_chain("T-3.2a", "stage3-programming.md", "### Audit slice",
    {"baseline_PROGRAM_v1": {"Safety": 45, "Preservation": 80, "Mobility": 95},
     "candidate": {"Safety": 60, "Preservation": 75, "Mobility": 85},
     "equality_constraint_total": 220, "constraint_status": "experiment fixture",
     "vocabulary": ["Safety", "Preservation", "Mobility"]},
    "(candidate is data to audit, not to generate)",
    "baseline_total, candidate_total, per_program_deltas, delta_sum, feasible/infeasible, repair_applied.",
    relay={"PROGRAM-v1": f7})
d = D(f8)
score("T-3.2 audit (N2,N6,E1)", [
    ("deltas +15/-5/-10", bool(re.search(r'"safety":\s*15', d)) and bool(re.search(r'"preservation":\s*-5', d))
        and bool(re.search(r'"mobility":\s*-10', d))),
    ("delta_sum 0, FEASIBLE", bool(re.search(r'"delta_sum":\s*0', d)) and "feasible" in d),
    ("no repair", '"repair_applied": false' in d or "repair_applied" not in d),
], r8, s8)
AUDIT = f8

# ============ Stage 4 · T-4.1 schedule (consumes AUDIT; boundary stated) ============
f9, r9, s9 = run_chain("T-4.1", "stage4-implementation-evaluation.md", "## T-4.1",
    {"years": 3, "bus_lane_miles_goal": 30, "budget_ceiling_musd": 12,
     "lead_time_rule": "AT LEAST two months between full dates; exactly two months SATISFIES",
     "construction_window": "March through October", "lead_agency": "Riverton Transit (documented)"},
    "[E1] Annual delivery capacity is 8-12 lane miles; community review precedes construction.",
    "THREE annual rows with year, lane_miles, budget_musd, owner+owner_status, "
    "community_review_date (YYYY-MM-DD), construction_start (YYYY-MM-DD), monitoring measure; "
    "totals meeting the 30-mile goal within the $12M ceiling; every date CANDIDATE.",
    relay={"AUDIT-v1": AUDIT})
d = D(f9)
rows = re.findall(r'"lane_miles":\s*([0-9.]+)', d)
tot = sum(float(x) for x in rows) if rows else 0
buds = re.findall(r'"budget_musd":\s*([0-9.]+)', d)
score("T-4.1 schedule (N1-N6)", [
    ("3 annual rows", len(rows) == 3),
    ("total >= 30 miles", tot >= 30),
    ("budget <= 12", bool(buds) and sum(float(b) for b in buds) <= 12.01),
    ("full-precision dates", bool(re.search(r"\d{4}-\d{2}-\d{2}", d))),
    ("dates CANDIDATE", "candidate" in d),
], r9, s9)

# ============ Stage 4 · T-4.2 consistency ============
f10, r10, s10 = run_chain("T-4.2c", "stage4-implementation-evaluation.md", "### Policy consistency",
    {"legacy_measures": {"a": "Bus on-time performance at least 80%",
                         "b": "Average fleet age no more than 8 years"}},
    '[P1] (Transit Policy 7.2, adopted 2025-03-01) "Weekday bus on-time performance shall be at least 85 '
    'percent, measured at timepoints." The 2025 policy carries no fleet-age measure.',
    "A current inventory with policy quotes, a legacy audit classifying each of a-b "
    "(unchanged/changed/retired_or_not_found/expanded_or_new/unknown), NO consistency percentage, "
    "NO compliance opinion.")
d = D(f10)
score("T-4.2 consistency (N1,N2,E1)", [
    ("a -> changed (80->85)", '"changed"' in d and "85" in d),
    ("b -> retired_or_not_found", "retired" in d or "not_found" in d or "not found" in d),
    ("no consistency %", "consistency_percentage" not in d or '"consistency_percentage": null' in d),
], r10, s10)

# ============ Stage 4 · T-4.2 monitoring (one definition mismatch) ============
f11, r11, s11 = run_chain("T-4.2m", "stage4-implementation-evaluation.md", "### Performance monitoring",
    {"rows": [
        {"measure": "Bus on-time performance 2025", "result": 78, "target": 85, "desired_trend": "up"},
        {"measure": "New sidewalk miles 2025", "result": 42, "target": 40, "desired_trend": "up"},
        {"measure": "Transit GHG, 2021 result", "result": 12.4,
         "target": "8.0 by 2035 vs 2010 baseline", "desired_trend": "down",
         "note": "result year and target definition differ"}]},
    "(rows as supplied; compute a gap ONLY where the measure and target definitions match)",
    "Per row: definition_match, meeting_target (Yes/No/UNKNOWN), gap or null, data_quality_warning.")
d = D(f11)
score("T-4.2 monitoring (N4-N6)", [
    ("OTP: No, gap -7", '"meeting_target": "no"' in d and ("-7" in d)),
    ("Sidewalk: Yes, gap 2", '"yes"' in d and bool(re.search(r'"gap":\s*2', d))),
    ("GHG: mismatch -> UNKNOWN, gap null", '"definition_match": false' in d and "unknown" in d
        and '"gap": null' in d),
], r11, s11)

# ============ Proprietary human-gated node ============
prep = call("proprietary-resources.md",
    "NODE N4a PREPARE (human-gated licensed-resource step per this file). Task: an HCM capacity check "
    "for one signalized approach is required. Emit the typed parameter sheet (inputs only, cite HCM by "
    "edition and chapter NUMBER), an empty result schema, and STOP for the human. Do NOT supply any "
    "capacity value or LOS.")
dp = D(prep)
no_invent = not re.search(r'"(capacity|capacity_vph)":\s*\d', dp)
cites = "hcm" in dp and ("chapter" in dp or "ch." in dp or "ed" in dp)
val = call("proprietary-resources.md",
    "NODE N4b VALIDATE. The human returned this licensed-computation result: "
    '{"capacity_vph": 1720, "los": "C", "edition": "HCM7", "section": "Ch. 19"}. '
    "Validate schema/units/range, stamp provenance USER_SUPPLIED_LICENSED, and hand off.")
dv = D(val)
results.append({"chain": "proprietary human-gated (N4a/N4b)", "pass": no_invent and cites and
                "user_supplied_licensed" in dv and "1720" in dv,
                "nodes": ["N4a:PASS", "N4b:PASS"], "stopped": None,
                "checks": [("PREPARE cites by number, invents no value", no_invent and cites),
                           ("VALIDATE stamps provenance and consumes 1720",
                            "user_supplied_licensed" in dv and "1720" in dv)]})
print(("PASS" if results[-1]["pass"] else "FAIL") + "  proprietary human-gated (N4a/N4b)")
for n, c in results[-1]["checks"]:
    if not c: print(f"        check FAIL: {n}")

# ============ summary ============
p = sum(1 for r in results if r["pass"])
print(f"\n===== {p}/{len(results)} chains fully passed =====")
json.dump(results, open("e2e_results.json", "w"), ensure_ascii=False, indent=1)
