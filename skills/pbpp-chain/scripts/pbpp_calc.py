#!/usr/bin/env python3
"""Deterministic calculators for the pbpp-chain calculation nodes.

Arithmetic belongs in a tool (TM4 Section 2.2). Requires Python 3.10+.
Pure standard library; no dependencies.

Every function returns three separated verdicts (see node-protocol.md):
  validator_status  did the tool run to spec on LEGAL inputs (PASS/FAIL)
  business_finding  what the result says about the world (feasible, gaps, ...)
  chain_action      continue | stop  (a legitimate finding continues)

Fail-closed policy: illegal or ambiguous input is a FAIL with a named
failure_class and NO computed numbers — this tool never produces a
plausible-looking result from bad input.

CLI:
  python pbpp_calc.py logit  '{"modes": {...}, "coefficients": {...}}'
  python pbpp_calc.py trips  '{"total": 46000, "shares_pct": {...}}'
  python pbpp_calc.py audit  '{"baseline": {...}, "candidate": {...},
                               "constraint_total": 220, "constraint": "equality|ceiling"}'
  python pbpp_calc.py gaps   '{"rows": [...]}'
  python pbpp_calc.py --version
"""
import json
import math
import sys

__version__ = "0.2.0"

_COEF_ATTR = {"time": "time_min", "cost": "cost_usd", "frequency": "services_per_hour"}
_EXP_LIMIT = 700.0  # beyond this math.exp overflows


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _fail(tool: str, reason: str, failure_class: str = "data_blocking", **extra) -> dict:
    out = {"tool": tool, "tool_version": __version__,
           "validator_status": "FAIL", "failure_class": failure_class,
           "reason": reason, "business_finding": None, "chain_action": "stop"}
    out.update(extra)
    return out


def logit(modes: dict, coefficients: dict) -> dict:
    """Multinomial logit. Refuses silent defaults: every supplied coefficient
    must have its attribute present and numeric in EVERY mode."""
    tool = "pbpp_calc.logit"
    if not isinstance(coefficients, dict) or not coefficients:
        return _fail(tool, "coefficients missing or empty; a zero coefficient "
                           "must be written explicitly, never assumed")
    unknown = sorted(set(coefficients) - set(_COEF_ATTR))
    if unknown:
        return _fail(tool, f"unknown coefficient keys {unknown}; known: "
                           f"{sorted(_COEF_ATTR)}", "tool_blocking")
    if not isinstance(modes, dict) or len(modes) < 2:
        return _fail(tool, "need at least two modes")
    for c, v in coefficients.items():
        if not _num(v):
            return _fail(tool, f"coefficient {c!r} is not a finite number: {v!r}")
    for name, a in modes.items():
        if not isinstance(a, dict):
            return _fail(tool, f"mode {name!r} is not an attribute object")
        for c in coefficients:
            attr = _COEF_ATTR[c]
            if attr not in a:
                return _fail(tool, f"mode {name!r} lacks {attr!r} required by "
                                   f"coefficient {c!r}; write an explicit value")
            if not _num(a[attr]):
                return _fail(tool, f"mode {name!r}.{attr} is not a finite number")
        if "asc" in a and not _num(a["asc"]):
            return _fail(tool, f"mode {name!r}.asc is not a finite number")

    utilities, exps = {}, {}
    for name, a in modes.items():
        u = sum(coefficients[c] * a[_COEF_ATTR[c]] for c in coefficients) + a.get("asc", 0.0)
        if abs(u) > _EXP_LIMIT:
            return _fail(tool, f"utility for {name!r} is {u:.3g}; |u| > {_EXP_LIMIT:g} "
                               "would overflow exp() — check units", "tool_blocking")
        utilities[name] = round(u, 10)
        exps[name] = math.exp(u)
    denom = sum(exps.values())
    unrounded = {k: v / denom for k, v in exps.items()}
    return {
        "tool": tool, "tool_version": __version__,
        "validator_status": "PASS", "failure_class": None, "chain_action": "continue",
        "inputs": {"modes": modes, "coefficients": coefficients},
        "utilities": utilities,
        "exponentials": {k: round(v, 6) for k, v in exps.items()},
        "denominator": round(denom, 6),
        "unrounded_shares": {k: round(v, 10) for k, v in unrounded.items()},
        "displayed_shares_pct": {k: round(v * 100, 1) for k, v in unrounded.items()},
        "unrounded_share_sum": round(sum(unrounded.values()), 10),
        "business_finding": {"shares": {k: round(v, 4) for k, v in unrounded.items()}},
    }


def trips(total, shares_pct: dict, excluded: list | None = None) -> dict:
    """total x share, round half up. Fails closed on illegal shares AND on a
    conservation residual — a total too small to survive rounding is reported,
    never papered over."""
    tool = "pbpp_calc.trips"
    if not _num(total) or total <= 0:
        return _fail(tool, f"total must be a positive finite number, got {total!r}")
    if not isinstance(shares_pct, dict) or not shares_pct:
        return _fail(tool, "shares_pct missing or empty")
    for k, v in shares_pct.items():
        if not _num(v) or v < 0 or v > 100:
            return _fail(tool, f"share {k!r}={v!r} outside [0, 100]; negative or "
                               ">100% shares are illegal, not normalisable")
    s = round(sum(shares_pct.values()), 10)
    if abs(s - 100.0) > 1e-9:
        return _fail(tool, "shares do not total 100%; normalisation is forbidden",
                     share_total_pct=s)
    counts = {k: int(math.floor(total * v / 100 + 0.5)) for k, v in shares_pct.items()}
    all_total = sum(counts.values())
    residual = all_total - int(math.floor(total + 0.5))
    if residual != 0:
        return _fail(tool, f"rounding residual {residual:+d}: category counts sum to "
                           f"{all_total}, control total is {int(total)}. Adjust the "
                           "rounding convention or the fixture; never reallocate "
                           "the residual silently",
                     counts=counts, all_category_total=all_total)
    excl = set(excluded or [])
    bad_excl = sorted(excl - set(shares_pct))
    if bad_excl:
        return _fail(tool, f"excluded categories not in shares: {bad_excl}")
    return {
        "tool": tool, "tool_version": __version__,
        "validator_status": "PASS", "failure_class": None, "chain_action": "continue",
        "inputs": {"total": total, "shares_pct": shares_pct, "excluded": sorted(excl)},
        "counts": counts,
        "all_category_total": all_total,
        "network_subtotal": sum(v for k, v in counts.items() if k not in excl),
        "conservation_ok": True,
        "business_finding": {"counts": counts},
    }


def audit(baseline: dict, candidate: dict, constraint_total,
          vocabulary: list | None = None, constraint: str = "equality") -> dict:
    """Fiscal audit. INFEASIBLE is a BUSINESS FINDING that continues downstream;
    illegal input is a validator FAIL that stops. Never repairs."""
    tool = "pbpp_calc.audit"
    if constraint not in ("equality", "ceiling"):
        return _fail(tool, f"constraint must be 'equality' or 'ceiling', got "
                           f"{constraint!r}", "tool_blocking")
    if not _num(constraint_total) or constraint_total <= 0:
        return _fail(tool, f"constraint_total must be positive finite, got "
                           f"{constraint_total!r}")
    for label, d in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(d, dict) or not d:
            return _fail(tool, f"{label} missing or empty")
        for k, v in d.items():
            if not _num(v) or v < 0:
                return _fail(tool, f"{label}[{k!r}]={v!r} is not a non-negative "
                                   "finite number")
    if vocabulary is not None:
        vocab = list(vocabulary)
        bad_c = sorted(set(candidate) - set(vocab))
        bad_b = sorted(set(baseline) - set(vocab))
        missing = sorted(set(vocab) - set(candidate))
        if bad_c or bad_b or missing:
            return _fail(tool, "controlled-vocabulary violation",
                         unknown_candidate=bad_c, unknown_baseline=bad_b,
                         missing_from_candidate=missing)
    else:
        vocab = sorted(set(baseline) | set(candidate))

    deltas = {k: round(candidate.get(k, 0) - baseline.get(k, 0), 6) for k in vocab}
    ct = round(sum(candidate.values()), 6)
    if constraint == "equality":
        feasible = abs(ct - constraint_total) < 1e-9
    else:
        feasible = ct <= constraint_total + 1e-9
    return {
        "tool": tool, "tool_version": __version__,
        "validator_status": "PASS", "failure_class": None,
        "chain_action": "continue",   # INFEASIBLE is a finding, not a chain failure
        "inputs": {"baseline": baseline, "candidate": candidate,
                   "constraint": constraint, "constraint_total": constraint_total},
        "baseline_total": round(sum(baseline.values()), 6),
        "candidate_total": ct,
        "per_program_deltas": deltas,
        "delta_sum": round(sum(deltas.values()), 6),
        "business_finding": {"feasible": "FEASIBLE" if feasible else "INFEASIBLE",
                             "constraint": constraint},
        "repair_applied": False,
    }


def gaps(rows: list) -> dict:
    """Performance gaps. Gap only where definition_match is true; an unknown
    desired_trend yields UNKNOWN — it is never guessed as a direction."""
    tool = "pbpp_calc.gaps"
    if not isinstance(rows, list) or not rows:
        return _fail(tool, "rows missing or empty")
    out = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or "measure" not in r:
            return _fail(tool, f"row {i} lacks a measure")
        if not isinstance(r.get("definition_match"), bool):
            return _fail(tool, f"row {i} ({r.get('measure')!r}): definition_match "
                               "must be an explicit JSON boolean")
        rec = dict(r)
        if not r["definition_match"]:
            rec.update(gap=None, meeting_target="UNKNOWN",
                       data_quality_warning="definition mismatch: gap not computable")
        else:
            if not _num(r.get("result")) or not _num(r.get("target")):
                return _fail(tool, f"row {i} ({r['measure']!r}): result/target must "
                                   "be finite numbers when definitions match")
            trend = str(r.get("desired_trend", "")).lower()
            if trend not in ("up", "down"):
                rec.update(gap=None, meeting_target="UNKNOWN",
                           data_quality_warning=f"desired_trend {r.get('desired_trend')!r} "
                                                "is not 'up' or 'down'; direction is "
                                                "never assumed")
            else:
                gap = round(r["result"] - r["target"], 6)
                meets = ("Yes" if (r["result"] >= r["target"] if trend == "up"
                                   else r["result"] <= r["target"]) else "No")
                rec.update(gap=gap, meeting_target=meets, data_quality_warning=None)
        out.append(rec)
    return {"tool": tool, "tool_version": __version__,
            "validator_status": "PASS", "failure_class": None,
            "chain_action": "continue",
            "rows": out, "business_finding": {"rows": out}}


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in ("--version", "-V"):
        print(__version__)
        sys.exit(0)
    if len(sys.argv) < 3:
        print("usage: python pbpp_calc.py {logit|trips|audit|gaps} '<json>'  "
              "| --version   (payload shapes in the docstring)")
        sys.exit(1)
    cmd, payload = sys.argv[1], json.loads(sys.argv[2])
    fn = {"logit": lambda p: logit(p["modes"], p["coefficients"]),
          "trips": lambda p: trips(p["total"], p["shares_pct"], p.get("excluded")),
          "audit": lambda p: audit(p["baseline"], p["candidate"],
                                   p.get("constraint_total", p.get("equality_total")),
                                   p.get("vocabulary"),
                                   p.get("constraint", "equality")),
          "gaps": lambda p: gaps(p["rows"])}
    if cmd not in fn:
        print(f"unknown command {cmd!r}; expected logit|trips|audit|gaps")
        sys.exit(1)
    print(json.dumps(fn[cmd](payload), ensure_ascii=False, indent=1))
