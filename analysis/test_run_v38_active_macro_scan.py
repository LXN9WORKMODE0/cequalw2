from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_v38_active_macro_scan import case_name, parse_active_config, prepare_case


class V38ActiveMacroRunnerTests(unittest.TestCase):
    def test_case_name_is_stable(self) -> None:
        self.assertEqual(
            case_name(0.0458, 44431.0),
            "nseg_26_i028_neff_0p0458_tmend_44431p00_case",
        )

    def test_parser_reads_requested_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "w2.wrn"
            path.write_text(
                "[V38_ACTIVE_MACRO_CONFIG] JB=1 ISEG=26 NEFF=4.5800E-02\n",
                encoding="utf-8",
            )
            self.assertEqual(parse_active_config(path), (26, 0.0458))

    def test_prepare_writes_consistent_domain_and_active_options(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "w2_con.csv").write_text("TMEND,1\n", encoding="ascii")
            exe = root / "model.exe"
            exe.write_bytes(b"model")
            work = root / "work"
            with (
                patch("run_v38_active_macro_scan.SOURCE_CASE", source),
                patch("run_v38_active_macro_scan.WORK_ROOT", work),
                patch("run_v38_active_macro_scan.smoke.update_tmend"),
                patch("run_v38_active_macro_scan.smoke.stage_exe"),
            ):
                case = prepare_case(0.0458, 2.0, exe, False)
            self.assertEqual((case / "tail_domain.opt").read_text(encoding="ascii"), "1 26\n")
            self.assertEqual(
                (case / "tail_macro_active.opt").read_text(encoding="ascii"),
                "1 28 0.04580000\n",
            )


if __name__ == "__main__":
    unittest.main()
