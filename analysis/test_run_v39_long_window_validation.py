from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_v39_long_window_validation import candidate_label, prepare_case, window_ranges


class V39LongWindowValidationTests(unittest.TestCase):
    def test_candidate_label_tracks_requested_effective_resistance(self) -> None:
        self.assertEqual(candidate_label(0.0725), "v38_neff_0725")

    def test_window_ranges_cover_interval_without_overlap(self) -> None:
        self.assertEqual(
            window_ranges(44430.0, 44448.0, 7.0),
            [(44430.0, 44437.0), (44437.0, 44444.0), (44444.0, 44448.0)],
        )

    def test_prepare_candidate_writes_fixed_macro_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "w2_con.csv").write_text("TMEND,1\n", encoding="ascii")
            exe = root / "model.exe"
            exe.write_bytes(b"model")
            work = root / "work"
            with (
                patch("run_v39_long_window_validation.SOURCE_CASE", source),
                patch("run_v39_long_window_validation.WORK_ROOT", work),
                patch("run_v39_long_window_validation.smoke.update_tmend"),
                patch("run_v39_long_window_validation.smoke.stage_exe"),
            ):
                case = prepare_case("candidate", 2.0, exe, True, 0.0725, False)
            self.assertEqual((case / "tail_domain.opt").read_text(encoding="ascii"), "1 26\n")
            self.assertEqual(
                (case / "tail_macro_active.opt").read_text(encoding="ascii"),
                "1 28 0.07250000\n",
            )


if __name__ == "__main__":
    unittest.main()
