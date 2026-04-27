from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from run_v21_bht_redistribution_scan import (
    parse_boundary_flux_stats,
    redistribute_bht_series,
    redistribute_bht_with_sources,
    tail_flow_stats,
    write_npt_with_header,
)


class RedistributeBhtSeriesTests(unittest.TestCase):
    def test_moves_only_positive_distributed_flow_and_preserves_total(self) -> None:
        bht = [(1.0, 100.0), (2.0, 200.0), (3.0, 300.0)]
        distributed = [(1.0, 40.0), (2.0, -20.0), (3.0, 0.0)]

        moved_bht, moved_distributed = redistribute_bht_series(bht, distributed, 0.25)

        self.assertEqual(moved_bht, [(1.0, 110.0), (2.0, 200.0), (3.0, 300.0)])
        self.assertEqual(moved_distributed, [(1.0, 30.0), (2.0, -20.0), (3.0, 0.0)])
        for (_, original_bht), (_, original_dt), (_, new_bht), (_, new_dt) in zip(
            bht, distributed, moved_bht, moved_distributed
        ):
            self.assertAlmostEqual(original_bht + original_dt, new_bht + new_dt)

    def test_tail_flow_stats_filters_to_requested_branch(self) -> None:
        text = "\n".join(
            [
                "[V10_TAIL_REACH] JB=1 QPHYS=100.000 QOUT=90.000 VOL=1 WSE_HYD=1 WSE_STOR=1",
                "[V10_TAIL_REACH] JB=2 QPHYS=1000.000 QOUT=800.000 VOL=1 WSE_HYD=1 WSE_STOR=1",
            ]
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w2.wrn"
            path.write_text(text, encoding="utf-8")

            stats = tail_flow_stats(path, branch=1)

        self.assertEqual(stats["v10_count"], 1)
        self.assertEqual(stats["v10_qphys_mean"], 100.0)
        self.assertEqual(stats["v10_qout_mean"], 90.0)

    def test_aggregate_redistribution_moves_positive_sources_to_bht(self) -> None:
        bht = [(1.0, 100.0), (2.0, 200.0)]
        source_a = [(1.0, 40.0), (2.0, -20.0)]
        source_b = [(1.0, 10.0), (2.0, 30.0)]

        moved_bht, moved_sources = redistribute_bht_with_sources(bht, [source_a, source_b], 0.5)

        self.assertEqual(moved_bht, [(1.0, 125.0), (2.0, 215.0)])
        self.assertEqual(moved_sources[0], [(1.0, 20.0), (2.0, -20.0)])
        self.assertEqual(moved_sources[1], [(1.0, 5.0), (2.0, 15.0)])

    def test_boundary_flux_stats_parse_jb1_marker(self) -> None:
        text = "\n".join(
            [
                "[V22_BOUNDARY_FLUX] JB=1 QIN=100.000 QEFF=90.000 QDT_SUM=12.000 QSS_SUM=10.000 TAIL_Q=80.000",
                "[V22_BOUNDARY_FLUX] JB=2 QIN=1000.000 QEFF=900.000 QDT_SUM=120.000 QSS_SUM=100.000 TAIL_Q=800.000",
            ]
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w2.wrn"
            path.write_text(text, encoding="utf-8")

            stats = parse_boundary_flux_stats(path, branch=1)

        self.assertEqual(stats["v22_count"], 1)
        self.assertEqual(stats["v22_qin_mean"], 100.0)
        self.assertEqual(stats["v22_qeff_mean"], 90.0)
        self.assertEqual(stats["v22_qdt_sum_mean"], 12.0)
        self.assertEqual(stats["v22_qss_sum_mean"], 10.0)

    def test_write_npt_preserves_decimal_points_for_integer_values(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "BHTOUTFLOW.npt"

            write_npt_with_header(path, ["BHT", "flow", "jday flow"], [(44430.0, 5360.0)])

            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(lines[-1].split(), ["44430.", "5360."])


if __name__ == "__main__":
    unittest.main()
