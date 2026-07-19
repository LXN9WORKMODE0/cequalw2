from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_v37_macro_target import prepare_case


class V37MacroTargetRunnerTests(unittest.TestCase):
    def test_prepare_writes_only_shadow_interface_option(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "w2_con.csv").write_text("TMEND,1\n", encoding="ascii")
            exe = root / "model.exe"
            exe.write_bytes(b"model")
            work = root / "work"
            with (
                patch("run_v37_macro_target.SOURCE_CASE", source),
                patch("run_v37_macro_target.WORK_ROOT", work),
                patch("run_v37_macro_target.smoke.update_tmend"),
                patch("run_v37_macro_target.smoke.stage_exe"),
            ):
                case = prepare_case(exe, 2.0, 26, False)
            self.assertEqual((case / "tail_macro.opt").read_text(encoding="ascii"), "1 26\n")
            self.assertFalse((case / "tail_domain.opt").exists())


if __name__ == "__main__":
    unittest.main()
