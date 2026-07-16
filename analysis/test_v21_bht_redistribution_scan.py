from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from run_v21_bht_redistribution_scan import (
    parse_boundary_flux_stats,
    parse_interface_commit_stats,
    parse_interface_mass_stats,
    parse_q_update_mode,
    redistribute_bht_series,
    redistribute_bht_with_sources,
    tail_flow_stats,
    write_npt_with_header,
)
from run_w2_v0_v1_smoke import (
    assert_v33_local_targets,
    count_computational_warnings,
    parse_v26_contract,
    parse_v27_profile_contract,
    parse_v31_single_step_contract,
    parse_v32_segment_volume_contract,
)


class RedistributeBhtSeriesTests(unittest.TestCase):
    def test_computational_warning_counter_detects_volume_balance_warning(self) -> None:
        text = "\n".join(
            [
                "COMPUTATIONAL WARNING AT JULIAN DAY = 44430.0034",
                "VOLUME ERROR = -0.10642802E+07 M^3",
                "COMPUTATIONAL WARNING AT JULIAN DAY = 44431.0000",
            ]
        )

        self.assertEqual(count_computational_warnings(text), 2)

    def test_v26_contract_parser_requires_exclusive_domain_and_single_consumer_flux(self) -> None:
        text = "\n".join(
            [
                "[V26_DOMAIN_OWNER] JB=1 CUS=6 TAIL_US=2 TAIL_DS=5 COUPLE=6 EXCLUSIVE=T",
                "[V26_BOUNDARY_CONSUMER] JB=1 QPHYS=100 QRES=80 QTHERM=80 QVOL=80",
                "[V26_BOUNDARY_CONSUMER] JB=2 QPHYS=1000 QRES=700 QTHERM=600 QVOL=500",
            ]
        )

        contract = parse_v26_contract(text, branch=1)

        self.assertTrue(contract["exclusive"])
        self.assertEqual(contract["active_cus"], 6)
        self.assertEqual(contract["couple"], 6)
        self.assertEqual(contract["consumer_count"], 1)
        self.assertEqual(contract["consumer_gap_max"], 0.0)

    def test_v27_profile_parser_checks_storage_identity_and_center_distance(self) -> None:
        text = "\n".join(
            [
                "[V12_Q_STATE] JB=1 QSTATE=80 QTARGET=90 TAU=1 CEL=2 LENGTH=3855 ALPHA=.25",
                "[V27_PROFILE_STORAGE] JB=1 VSTATE=1000 VPROFILE=999.9995 VGAP=0.0005 WUP=590 WDN=580",
                "[V27_PROFILE_STORAGE] JB=2 VSTATE=100 VPROFILE=90 VGAP=10 WUP=590 WDN=580",
            ]
        )

        contract = parse_v27_profile_contract(text, branch=1)

        self.assertEqual(contract["profile_count"], 1)
        self.assertAlmostEqual(contract["profile_gap_max"], 0.0005)
        self.assertEqual(contract["reach_length_min"], 3855.0)
        self.assertEqual(contract["reach_length_max"], 3855.0)

    def test_v31_parser_checks_full_timestep_storage_identity(self) -> None:
        text = "\n".join(
            [
                "[V31_SINGLE_STEP] JB=1 VPRE=1000 VFINAL=1010 RATE=10 RTAIL=1E-10 RATEGAP=-2E-10",
                "[V31_SINGLE_STEP] JB=2 VPRE=100 VFINAL=200 RATE=100 RTAIL=50 RATEGAP=50",
            ]
        )

        contract = parse_v31_single_step_contract(text, branch=1)

        self.assertEqual(contract["count"], 1)
        self.assertAlmostEqual(contract["full_storage_resid_max"], 1.0e-10)
        self.assertAlmostEqual(contract["storage_rate_gap_max"], 2.0e-10)

    def test_v32_parser_checks_segment_volume_sum(self) -> None:
        text = "\n".join(
            [
                "[V32_SEGMENT_VOLUME] JB=1 VTOTAL=1000 VSEG=999.999 VGAP=0.001",
                "[V32_SEGMENT_VOLUME] JB=2 VTOTAL=100 VSEG=90 VGAP=10",
            ]
        )

        contract = parse_v32_segment_volume_contract(text, branch=1)

        self.assertEqual(contract["count"], 1)
        self.assertAlmostEqual(contract["segment_volume_gap_max"], 0.001)

    def test_v33_gate_requires_every_segment_at_every_accepted_step(self) -> None:
        result = SimpleNamespace(
            tail_local_target_count=7,
            tail_segment_volume_count=2,
            tail_domain_nseg_min=4,
        )

        with self.assertRaisesRegex(AssertionError, "actual=7, expected_min=8"):
            assert_v33_local_targets(result)

        result.tail_local_target_count = 8
        assert_v33_local_targets(result)

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

    def test_q_update_mode_parser_reads_v23_marker(self) -> None:
        text = "[V23_Q_UPDATE_MODE] MODE=RELAX\n"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w2.wrn"
            path.write_text(text, encoding="utf-8")

            mode = parse_q_update_mode(path)

        self.assertEqual(mode, "RELAX")

    def test_interface_mass_parser_reads_v24_marker(self) -> None:
        text = "\n".join(
            [
                "[V24_INTERFACE_MASS] JB=1 QPHYS=100 QIFACE=80 QRES=90 DSTORAGE=15 RTAIL=-5 RFLUX=10 RCOMB=5 SEGLOSS=3",
                "[V24_INTERFACE_MASS] JB=2 QPHYS=1000 QIFACE=800 QRES=900 DSTORAGE=150 RTAIL=-50 RFLUX=100 RCOMB=50 SEGLOSS=30",
            ]
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w2.wrn"
            path.write_text(text, encoding="utf-8")

            stats = parse_interface_mass_stats(path, branch=1)

        self.assertEqual(stats["v24_count"], 1)
        self.assertEqual(stats["v24_tail_mass_resid_max"], 5.0)
        self.assertEqual(stats["v24_flux_gap_max"], 10.0)
        self.assertEqual(stats["v24_combined_mass_resid_max"], 5.0)
        self.assertEqual(stats["v24_segment_q_loss_max"], 3.0)

    def test_interface_commit_parser_requires_evaluated_single_flux(self) -> None:
        text = "\n".join(
            [
                "[V24_INTERFACE_COMMIT] JB=1 QRES=80 QCOMMIT=80 ETA_PREV=588 ETA_COMMIT=589 DETA_APPLIED=1 EVALUATED=T",
                "[V24_INTERFACE_COMMIT] JB=2 QRES=800 QCOMMIT=700 ETA_PREV=580 ETA_COMMIT=590 DETA_APPLIED=10 EVALUATED=F",
            ]
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "w2.wrn"
            path.write_text(text, encoding="utf-8")

            stats = parse_interface_commit_stats(path, branch=1)

        self.assertEqual(stats["v24_commit_count"], 1)
        self.assertEqual(stats["v24_commit_q_gap_max"], 0.0)
        self.assertEqual(stats["v24_commit_eta_applied_max"], 1.0)
        self.assertEqual(stats["v24_commit_all_evaluated"], 1)


if __name__ == "__main__":
    unittest.main()
