from __future__ import annotations

import math
import unittest

from analyze_v24_residual_structure import ResidualSample, linear_slope, pearson, summarize_samples


class ResidualStructureTests(unittest.TestCase):
    def test_basic_statistics_and_correlations(self) -> None:
        samples = [
            ResidualSample(1.0, 10.0, 5.0, 6.0, 3.0, 3.5),
            ResidualSample(2.0, 20.0, 5.0, 7.0, 3.0, 4.0),
            ResidualSample(3.0, 30.0, 5.0, 8.0, 3.0, 4.5),
        ]

        summary = summarize_samples(samples)

        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["seg2_bias"], 2.0)
        self.assertEqual(summary["seg222_bias"], 1.0)
        self.assertEqual(summary["head_bias"], 1.0)
        self.assertEqual(summary["corr_seg2_error_qphys"], 1.0)
        self.assertAlmostEqual(summary["seg2_error_trend_m_per_day"], 1.0)

    def test_degenerate_correlation_and_slope_are_nan(self) -> None:
        self.assertTrue(math.isnan(pearson([1.0, 1.0], [2.0, 3.0])))
        self.assertTrue(math.isnan(linear_slope([1.0, 1.0], [2.0, 3.0])))


if __name__ == "__main__":
    unittest.main()
