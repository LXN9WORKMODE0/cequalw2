from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_v41_long_window_robustness import all_candidates_pass, case_label, prepare_case


class V41LongWindowRobustnessTests(unittest.TestCase):
    def test_case_label_preserves_four_decimal_resistance(self) -> None:
        self.assertEqual(case_label(0.070), "v38_neff_0700")
        self.assertEqual(case_label(0.075), "v38_neff_0750")

    def test_prepare_case_writes_boundary_preserving_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "w2_con.csv").write_text("TMEND,1\n", encoding="ascii")
            exe = root / "model.exe"
            exe.write_bytes(b"model")
            work = root / "work"
            with (
                patch("run_v41_long_window_robustness.SOURCE_CASE", source),
                patch("run_v41_long_window_robustness.WORK_ROOT", work),
                patch("run_v41_long_window_robustness.smoke.update_tmend"),
                patch("run_v41_long_window_robustness.smoke.stage_exe"),
            ):
                case = prepare_case(0.070, 2.0, exe, False)
            self.assertEqual((case / "tail_domain.opt").read_text(encoding="ascii"), "1 26\n")
            self.assertEqual(
                (case / "tail_macro_active.opt").read_text(encoding="ascii"),
                "1 28 0.07000000\n",
            )

    def test_every_boundary_candidate_must_pass(self) -> None:
        rows = [
            {"candidate": "v38_neff_0700", "passed": True},
            {"candidate": "v38_neff_0725", "passed": True},
            {"candidate": "v38_neff_0750", "passed": True},
        ]
        self.assertTrue(all_candidates_pass(rows))
        rows[-1]["passed"] = False
        self.assertFalse(all_candidates_pass(rows))


if __name__ == "__main__":
    unittest.main()
