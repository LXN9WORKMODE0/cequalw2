from __future__ import annotations

import unittest

from analyze_v40_holdout_regimes import (
    build_regime_index,
    evaluate_acceptance,
    quantile,
)


class V40HoldoutRegimeTests(unittest.TestCase):
    def test_quantile_uses_linear_order_statistic(self) -> None:
        values = [0.0, 10.0, 20.0, 30.0]
        self.assertEqual(quantile(values, 1.0 / 3.0), 10.0)
        self.assertEqual(quantile(values, 2.0 / 3.0), 20.0)

    def test_regime_index_uses_strict_holdout_and_central_trend(self) -> None:
        rows = [
            (1.0, 0.0),
            (2.0, 10.0),
            (3.0, 10.0),
            (4.0, 0.0),
        ]
        index, thresholds = build_regime_index(rows, 1.0, 4.0)
        self.assertNotIn(1.0, index)
        self.assertEqual(index[2.0], ("middle", "rising"))
        self.assertEqual(index[3.0], ("middle", "falling"))
        self.assertEqual(index[4.0], ("low", "falling"))
        self.assertAlmostEqual(thresholds[0], 20.0 / 3.0)
        self.assertEqual(thresholds[1], 10.0)

    def test_acceptance_requires_large_target_gain_and_bounded_side_effects(self) -> None:
        baseline = {
            "bht_rmse_m": 4.0,
            "xld_bht_head_rmse_m": 3.0,
            "xld_rmse_m": 1.0,
            "ymt_rmse_m": 2.0,
            "sj_rmse_m": 2.0,
            "computational_warning_count": 0,
            "v24_mass_residual_max": 1.0e-9,
            "v27_profile_gap_max": 1.0e-3,
            "v32_segment_volume_gap_max": 1.0e-3,
        }
        candidate = dict(baseline)
        candidate.update(
            bht_rmse_m=1.5,
            xld_bht_head_rmse_m=1.2,
            xld_rmse_m=1.05,
            ymt_rmse_m=2.1,
            sj_rmse_m=1.8,
        )
        rows, passed = evaluate_acceptance(baseline, candidate)
        self.assertTrue(passed)
        self.assertTrue(all(row["passed"] for row in rows))
        candidate["ymt_rmse_m"] = 2.3
        _, passed = evaluate_acceptance(baseline, candidate)
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main()
