"""Adversarial regression set for scripts/pbpp_calc.py (see evaluation.md:
re-run whenever the tool changes; passing happy paths alone does not detect a
weakened guardrail).

Run:  python -m unittest discover tests
"""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "skills" / "pbpp-chain" / "scripts"))
import pbpp_calc as C  # noqa: E402

MODES = {"Car": {"time_min": 22, "cost_usd": 4.5},
         "BRT": {"time_min": 28, "cost_usd": 2.0, "asc": -0.3}}
COEFS = {"time": -0.05, "cost": -0.15}


class TestLogit(unittest.TestCase):
    def test_happy_path_matches_hand_computation(self):
        r = C.logit(MODES, COEFS)
        self.assertEqual(r["validator_status"], "PASS")
        uc = -0.05 * 22 - 0.15 * 4.5
        ub = -0.05 * 28 - 0.15 * 2.0 - 0.3
        self.assertAlmostEqual(r["utilities"]["Car"], uc, places=9)
        self.assertAlmostEqual(r["utilities"]["BRT"], ub, places=9)
        sc = math.exp(uc) / (math.exp(uc) + math.exp(ub))
        self.assertAlmostEqual(r["unrounded_shares"]["Car"], sc, places=9)
        self.assertAlmostEqual(r["unrounded_share_sum"], 1.0, places=9)

    def test_empty_coefficients_fail_not_fifty_fifty(self):
        r = C.logit(MODES, {})
        self.assertEqual(r["validator_status"], "FAIL")
        self.assertNotIn("unrounded_shares", r)

    def test_unknown_coefficient_key_fails(self):
        self.assertEqual(C.logit(MODES, {"tim": -0.05})["validator_status"], "FAIL")

    def test_missing_attribute_fails_instead_of_silent_zero(self):
        modes = {"Car": {"time_min": 22}, "BRT": {"time_min": 28}}
        r = C.logit(modes, {"time": -0.05, "cost": -0.15})
        self.assertEqual(r["validator_status"], "FAIL")
        self.assertIn("cost_usd", r["reason"])

    def test_extreme_utility_fails_before_exp_overflow(self):
        modes = {"A": {"time_min": 1e6}, "B": {"time_min": 1.0}}
        r = C.logit(modes, {"time": -0.05})
        self.assertEqual(r["validator_status"], "FAIL")

    def test_nan_fails(self):
        modes = {"A": {"time_min": float("nan")}, "B": {"time_min": 1.0}}
        self.assertEqual(C.logit(modes, {"time": -0.05})["validator_status"], "FAIL")

    def test_single_mode_fails(self):
        self.assertEqual(C.logit({"Car": {"time_min": 1}}, {"time": -1})
                         ["validator_status"], "FAIL")


class TestTrips(unittest.TestCase):
    def test_happy_path_exact(self):
        r = C.trips(46000, {"Bus": 55.0, "BRT": 30.0, "Shuttle": 15.0})
        self.assertEqual(r["validator_status"], "PASS")
        self.assertEqual(r["counts"], {"Bus": 25300, "BRT": 13800, "Shuttle": 6900})
        self.assertEqual(r["all_category_total"], 46000)

    def test_float_friendly_hundred(self):
        shares = {"A": 78.1, "B": 9.1, "C": 7.0, "D": 1.6, "E": 1.6, "F": 0.6, "G": 2.0}
        self.assertEqual(C.trips(9100000, shares)["validator_status"], "PASS")

    def test_rounding_residual_is_a_fail_not_a_pass(self):
        r = C.trips(1, {"A": 50.0, "B": 50.0})   # counts would sum to 2 != 1
        self.assertEqual(r["validator_status"], "FAIL")
        self.assertIn("residual", r["reason"])

    def test_negative_share_fails_even_when_sum_is_100(self):
        r = C.trips(1000, {"A": -10.0, "B": 110.0})
        self.assertEqual(r["validator_status"], "FAIL")
        self.assertNotIn("network_subtotal", r)

    def test_sum_not_100_fails(self):
        self.assertEqual(C.trips(1000, {"A": 55.0, "B": 45.5})["validator_status"], "FAIL")

    def test_bad_total_fails(self):
        self.assertEqual(C.trips(0, {"A": 100.0})["validator_status"], "FAIL")
        self.assertEqual(C.trips(float("inf"), {"A": 100.0})["validator_status"], "FAIL")

    def test_unknown_excluded_category_fails(self):
        r = C.trips(100, {"A": 60.0, "B": 40.0}, excluded=["C"])
        self.assertEqual(r["validator_status"], "FAIL")


class TestAudit(unittest.TestCase):
    B = {"Safety": 45, "Preservation": 80, "Mobility": 95}

    def test_equality_feasible_with_exact_deltas(self):
        r = C.audit(self.B, {"Safety": 60, "Preservation": 75, "Mobility": 85}, 220)
        self.assertEqual(r["validator_status"], "PASS")
        self.assertEqual(r["business_finding"]["feasible"], "FEASIBLE")
        self.assertEqual(r["per_program_deltas"],
                         {"Mobility": -10, "Preservation": -5, "Safety": 15})
        self.assertEqual(r["delta_sum"], 0)

    def test_infeasible_is_a_finding_that_continues(self):
        r = C.audit(self.B, {"Safety": 61, "Preservation": 75, "Mobility": 85}, 220)
        self.assertEqual(r["validator_status"], "PASS")
        self.assertEqual(r["business_finding"]["feasible"], "INFEASIBLE")
        self.assertEqual(r["chain_action"], "continue")
        self.assertFalse(r["repair_applied"])

    def test_ceiling_constraint_both_directions(self):
        under = C.audit(self.B, {"Safety": 40, "Preservation": 80, "Mobility": 95},
                        230, constraint="ceiling")
        over = C.audit(self.B, {"Safety": 80, "Preservation": 80, "Mobility": 95},
                       230, constraint="ceiling")
        self.assertEqual(under["business_finding"]["feasible"], "FEASIBLE")
        self.assertEqual(over["business_finding"]["feasible"], "INFEASIBLE")

    def test_unknown_baseline_category_fails_with_vocabulary(self):
        r = C.audit({"Safety": 45, "Slush": 10}, {"Safety": 55}, 55,
                    vocabulary=["Safety"])
        self.assertEqual(r["validator_status"], "FAIL")
        self.assertEqual(r["unknown_baseline"], ["Slush"])

    def test_negative_amount_fails(self):
        self.assertEqual(C.audit(self.B, {"Safety": -1, "Preservation": 80,
                                          "Mobility": 141}, 220)["validator_status"],
                         "FAIL")

    def test_bad_constraint_type_fails(self):
        self.assertEqual(C.audit(self.B, self.B, 220, constraint="target")
                         ["validator_status"], "FAIL")


class TestGaps(unittest.TestCase):
    def test_matched_rows_up_and_down(self):
        r = C.gaps([{"measure": "OTP", "result": 78, "target": 85,
                     "desired_trend": "up", "definition_match": True},
                    {"measure": "Delay", "result": 4, "target": 5,
                     "desired_trend": "down", "definition_match": True}])
        self.assertEqual(r["rows"][0]["gap"], -7)
        self.assertEqual(r["rows"][0]["meeting_target"], "No")
        self.assertEqual(r["rows"][1]["meeting_target"], "Yes")

    def test_definition_mismatch_is_unknown_null(self):
        r = C.gaps([{"measure": "GHG", "result": 12.4, "target": 8.0,
                     "desired_trend": "down", "definition_match": False}])
        self.assertIsNone(r["rows"][0]["gap"])
        self.assertEqual(r["rows"][0]["meeting_target"], "UNKNOWN")

    def test_trend_typo_is_unknown_never_assumed_down(self):
        r = C.gaps([{"measure": "X", "result": 4, "target": 5,
                     "desired_trend": "dwon", "definition_match": True}])
        self.assertEqual(r["rows"][0]["meeting_target"], "UNKNOWN")
        self.assertIsNone(r["rows"][0]["gap"])
        self.assertIn("desired_trend", r["rows"][0]["data_quality_warning"])

    def test_string_boolean_fails(self):
        r = C.gaps([{"measure": "X", "result": 1, "target": 1,
                     "desired_trend": "up", "definition_match": "true"}])
        self.assertEqual(r["validator_status"], "FAIL")

    def test_nonnumeric_result_fails(self):
        r = C.gaps([{"measure": "X", "result": "78", "target": 85,
                     "desired_trend": "up", "definition_match": True}])
        self.assertEqual(r["validator_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
