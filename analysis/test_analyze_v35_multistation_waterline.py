from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analyze_v35_multistation_waterline import (
    Station,
    build_station_samples,
    flagged_points_in_window,
    summarize_interval,
    summarize_linear_profile_preflight,
    summarize_station,
    validate_npt,
    validate_processing_audit,
)


class V35MultistationWaterlineTests(unittest.TestCase):
    def test_station_summary_uses_simulation_minus_observation(self) -> None:
        station = Station("T", "test", 10.0, 7)
        samples = build_station_samples(
            station,
            [(1.0, 10.0), (2.0, 20.0)],
            [(1.0, 11.0), (2.0, 23.0)],
            [(1.0, 100.0), (2.0, 200.0)],
            1.0,
            2.0,
        )

        row = summarize_station(samples, flagged_points=0)

        self.assertEqual(row["count"], 2)
        self.assertAlmostEqual(row["bias_m"], 2.0)
        self.assertAlmostEqual(row["rmse_m"], 5.0**0.5)
        self.assertAlmostEqual(row["observed_stage_q_slope_m_per_m3s"], 0.1)
        self.assertAlmostEqual(row["stage_q_slope_ratio"], 1.2)

    def test_interval_summary_uses_upstream_minus_downstream_head(self) -> None:
        downstream = Station("D", "down", 0.0, 20)
        upstream = Station("U", "up", 10.0, 10)
        down_samples = build_station_samples(
            downstream,
            [(1.0, 10.0), (2.0, 11.0)],
            [(1.0, 10.5), (2.0, 11.5)],
            [(1.0, 100.0), (2.0, 200.0)],
            1.0,
            2.0,
        )
        up_samples = build_station_samples(
            upstream,
            [(1.0, 13.0), (2.0, 15.0)],
            [(1.0, 12.0), (2.0, 14.0)],
            [(1.0, 100.0), (2.0, 200.0)],
            1.0,
            2.0,
        )

        row = summarize_interval(down_samples, up_samples)

        self.assertEqual(row["interval"], "D->U")
        self.assertAlmostEqual(row["observed_head_mean_m"], 3.5)
        self.assertAlmostEqual(row["simulated_head_mean_m"], 2.0)
        self.assertAlmostEqual(row["head_bias_m"], -1.5)
        self.assertAlmostEqual(row["head_q_slope_ratio"], 1.0)

    def test_gap_overlap_counts_inclusive_hourly_points(self) -> None:
        rows = [
            {
                "year": "2021",
                "station_code": "SS",
                "start_time": "2021-01-02 00:00",
                "end_time": "2021-01-02 02:00",
            }
        ]

        self.assertEqual(flagged_points_in_window(rows, "SS", 44198.0, 44198.1), 3)
        self.assertEqual(flagged_points_in_window(rows, "HH", 44198.0, 44198.1), 0)

    def test_linear_profile_preflight_uses_chainage_fraction(self) -> None:
        downstream = Station("D", "down", 0.0, 20)
        interior = Station("I", "inside", 25.0, 15)
        upstream = Station("U", "up", 100.0, 10)
        flow = [(1.0, 100.0), (2.0, 200.0)]
        down_samples = build_station_samples(downstream, [(1.0, 10.0), (2.0, 20.0)], [(1.0, 10.0), (2.0, 20.0)], flow, 1.0, 2.0)
        inside_samples = build_station_samples(interior, [(1.0, 11.0), (2.0, 22.0)], [(1.0, 11.0), (2.0, 22.0)], flow, 1.0, 2.0)
        up_samples = build_station_samples(upstream, [(1.0, 20.0), (2.0, 40.0)], [(1.0, 20.0), (2.0, 40.0)], flow, 1.0, 2.0)

        row = summarize_linear_profile_preflight(down_samples, inside_samples, up_samples)

        self.assertAlmostEqual(row["interior_fraction_from_downstream"], 0.25)
        self.assertAlmostEqual(row["prediction_minus_observation_bias_m"], 2.25)

    def test_validate_npt_rejects_wrong_record_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "short.npt"
            path.write_text("eleobs\nbal\nJDAY  el_obs\n44197.00 580.00\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Expected 8760 records"):
                validate_npt(path)

    def test_processing_audit_must_reconcile_with_gap_hours(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "2021").mkdir()
            (root / "2021" / "ss.npt").touch()
            audit = root / "audit.csv"
            audit.write_text(
                "year,station_code,raw_missing,raw_out_of_range,raw_temporal_inconsistent,"
                "raw_spatial_inconsistent,interpolated_total,gap_count,max_gap_hours,output_file\n"
                "2021,SS,0,0,2,0,2,1,2,2021/ss.npt\n",
                encoding="utf-8",
            )
            gaps = root / "gaps.csv"
            gaps.write_text(
                "year,station_code,start_time,end_time,hours\n"
                "2021,SS,2021-01-02 00:00,2021-01-02 01:00,2\n",
                encoding="utf-8",
            )

            rows = validate_processing_audit(audit, gaps, root)

            self.assertEqual(rows[0]["gap_hours"], 2)
            self.assertTrue(rows[0]["reconciled"])


if __name__ == "__main__":
    unittest.main()
