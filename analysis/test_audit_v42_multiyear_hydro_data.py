from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from audit_v42_multiyear_hydro_data import (
    audit_time_axis,
    build_quality_masks,
    longest_true_run,
)


class MultiyearHydroAuditTest(unittest.TestCase):
    def test_longest_true_run(self) -> None:
        mask = pd.Series([False, True, True, False, True, True, True, False])
        self.assertEqual(longest_true_run(mask), 3)

    def test_quality_bounds_and_zero_flow_flag(self) -> None:
        index = pd.date_range("2021-01-01", periods=3, freq="h")
        data = pd.DataFrame(
            {
                "BHT_WL": [580.0, -100000.0, np.nan],
                "BHT_Q_TD": [1000.0, 0.0, 60000.0],
            },
            index=index,
        )
        valid, reasons = build_quality_masks(data)
        self.assertEqual(valid["BHT_WL"].tolist(), [True, False, False])
        self.assertEqual(valid["BHT_Q_TD"].tolist(), [True, True, False])
        self.assertEqual(reasons.loc[index[1], "BHT_Q_TD"], "zero_flow_review")

    def test_time_axis_finds_missing_hour(self) -> None:
        index = pd.DatetimeIndex(
            [pd.Timestamp("2021-01-01 00:00"), pd.Timestamp("2021-01-01 02:00")]
        )
        audit = audit_time_axis(pd.DataFrame({"x": [1, 2]}, index=index), "test")
        self.assertEqual(audit["missing_timestamp_count"], 1)
        self.assertEqual(audit["nonhourly_step_count"], 1)


if __name__ == "__main__":
    unittest.main()
