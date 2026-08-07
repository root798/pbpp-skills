#!/usr/bin/env python3
"""Deterministic calculators for the pbpp-chain calculation nodes.

Arithmetic belongs in a tool (TM4 Section 2.2). When a chain reaches a
calculation node, run the matching function here instead of computing floats
in prose. Pure standard library; no dependencies.

CLI:
  python pbpp_calc.py logit  '{"modes": {...}, "coefficients": {...}}'
  python pbpp_calc.py trips  '{"total": 46000, "shares_pct": {...}}'
  python pbpp_calc.py audit  '{"baseline": {...}, "candidate": {...}, "equality_total": 220}'
  python pbpp_calc.py gaps   '{"rows": [{"measure": "...", "result": 78, "target": 85,
                               "desired_trend": "up", "definition_match": true}]}'

Every function returns a dict ready to paste into the node record's `output`.
Each result carries `tool: pbpp_calc` and the input echo so the N-check node
can recompute from the same inputs.
"""
import json
import math
import sys


def logit(modes: dict, coefficients: dict) -> dict:
    """Multinomial logit. Mode attrs: time_min, cost_usd, services_per_hour, asc.

    Shares are the DIVIDED values (exp(U)/denominator); the share sum is exact
    by construction, which is the property in-text arithmetic loses.
    """
    utilities, exps = {}, {}
    for name, a in modes.items():
        u = (coefficients.get("time", 0.0) * a.get("time_min", 0.0)
             + coefficients.get("cost", 0.0) * a.get("cost_usd", 0.0)
             + coefficients.get("frequency", 0.0) * a.get("services_per_hour", 0.0)
             + a.get("asc", 0.0))
        utilities[name] = round(u, 10)
        exps[name] = math.exp(u)
    denom = sum(exps.values())
    unrounded = {k: v / denom for k, v in exps.items()}
    return {
        "tool": "pbpp_calc.logit",
        "inputs": {"modes": modes, "coefficients": coefficients},
        "utilities": utilities,
        "exponentials": {k: round(v, 6) for k, v in exps.items()},
        "denominator": round(denom, 6),
        "unrounded_shares": {k: round(v, 10) for k, v in unrounded.items()},
        "displayed_shares_pct": {k: round(v * 100, 1) for k, v in unrounded.items()},
        "unrounded_share_sum": round(sum(unrounded.values()), 10),
    }


def trips(total: float, shares_pct: dict, excluded: list | None = None) -> dict:
    """total x share, round half up. Fails closed if shares do not total 100."""
    s = round(sum(shares_pct.values()), 10)
    if abs(s - 100.0) > 1e-9:
        return {"tool": "pbpp_calc.trips", "status": "FAIL",
                "failure_class": "data_blocking",
                "share_total_pct": s,
                "reason": "shares do not total 100%; normalisation is forbidden"}
    counts = {k: int(math.floor(total * v / 100 + 0.5)) for k, v in shares_pct.items()}
    excl = set(excluded or [])
    return {
        "tool": "pbpp_calc.trips", "status": "PASS",
        "inputs": {"total": total, "shares_pct": shares_pct,
                   "excluded": sorted(excl)},
        "counts": counts,
        "all_category_total": sum(counts.values()),
        "network_subtotal": sum(v for k, v in counts.items() if k not in excl),
    }


def audit(baseline: dict, candidate: dict, equality_total: float,
          vocabulary: list | None = None) -> dict:
    """Fiscal audit. Reports INFEASIBLE; never repairs."""
    vocab = vocabulary or sorted(baseline)
    unknown = sorted(set(candidate) - set(vocab))
    missing = sorted(set(vocab) - set(candidate))
    deltas = {k: round(candidate.get(k, 0) - baseline.get(k, 0), 6) for k in vocab}
    ct = round(sum(candidate.values()), 6)
    return {
        "tool": "pbpp_calc.audit",
        "inputs": {"baseline": baseline, "candidate": candidate,
                   "equality_total": equality_total},
        "baseline_total": round(sum(baseline.values()), 6),
        "candidate_total": ct,
        "per_program_deltas": deltas,
        "delta_sum": round(sum(deltas.values()), 6),
        "vocabulary_ok": not unknown and not missing,
        "unknown_programs": unknown, "missing_programs": missing,
        "feasible": "FEASIBLE" if (not unknown and not missing
                                   and abs(ct - equality_total) < 1e-9) else "INFEASIBLE",
        "repair_applied": False,
    }


def gaps(rows: list) -> dict:
    """Performance gaps. A gap is computed ONLY where definition_match is true."""
    out = []
    for r in rows:
        rec = dict(r)
        if not r.get("definition_match"):
            rec.update(gap=None, meeting_target="UNKNOWN",
                       data_quality_warning="definition mismatch: gap not computable")
        else:
            gap = round(r["result"] - r["target"], 6)
            trend = str(r.get("desired_trend", "")).lower()
            meets = ("Yes" if (r["result"] >= r["target"] if trend == "up"
                               else r["result"] <= r["target"]) else "No")
            rec.update(gap=gap, meeting_target=meets, data_quality_warning=None)
        out.append(rec)
    return {"tool": "pbpp_calc.gaps", "rows": out}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python pbpp_calc.py {logit|trips|audit|gaps} '<json>'  "
              "(see the docstring for each payload shape)")
        sys.exit(1)
    cmd, payload = sys.argv[1], json.loads(sys.argv[2])
    fn = {"logit": lambda p: logit(p["modes"], p["coefficients"]),
          "trips": lambda p: trips(p["total"], p["shares_pct"], p.get("excluded")),
          "audit": lambda p: audit(p["baseline"], p["candidate"],
                                   p["equality_total"], p.get("vocabulary")),
          "gaps": lambda p: gaps(p["rows"])}[cmd]
    print(json.dumps(fn(payload), ensure_ascii=False, indent=1))
