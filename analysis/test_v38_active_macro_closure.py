from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "w2source_v455_2_11_2026"


class V38ActiveMacroClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.modules = (SOURCE / "w2modules.F90").read_text(encoding="utf-8", errors="ignore")
        cls.input_source = (SOURCE / "input.F90").read_text(encoding="utf-8", errors="ignore")
        cls.init_source = (SOURCE / "init.F90").read_text(encoding="utf-8", errors="ignore")
        cls.geometry = (SOURCE / "init-geom.F90").read_text(encoding="utf-8", errors="ignore")
        cls.main = (SOURCE / "w2_main.f90").read_text(encoding="utf-8", errors="ignore")

    def test_active_configuration_is_per_branch_and_default_off(self) -> None:
        self.assertIn("TAIL_MACRO_ACTIVE_SEG", self.modules)
        self.assertIn("TAIL_MACRO_ACTIVE_MANNING", self.modules)
        self.assertIn("TAIL_MACRO_ACTIVE_SEG(NBR)", self.input_source)
        self.assertIn("TAIL_MACRO_ACTIVE_MANNING(NBR)", self.input_source)
        self.assertIn("TAIL_MACRO_ACTIVE_SEG = 0", self.init_source)
        self.assertIn("TAIL_MACRO_ACTIVE_MANNING = 0.0D0", self.init_source)

    def test_active_configuration_must_match_coupling_boundary(self) -> None:
        self.assertIn("tail_macro_active.opt", self.geometry)
        self.assertIn("TAIL_MACRO_ACTIVE_SEG(JB) /= TAIL_COUPLE_SEG(JB)", self.geometry)
        self.assertIn("[V38_ACTIVE_MACRO_CONFIG]", self.geometry)

    def test_one_profile_closure_serves_stage_and_flow_consumers(self) -> None:
        self.assertIn("SUBROUTINE COMPUTE_TAIL_PROFILE_LINK_FLOW", self.main)
        self.assertIn("SUBROUTINE SOLVE_TAIL_PROFILE_STAGE", self.main)
        self.assertGreaterEqual(self.main.count("CALL COMPUTE_TAIL_PROFILE_LINK_FLOW"), 3)
        self.assertIn("WSE_STORAGE, ACTIVE_MACRO", self.main)
        self.assertIn(".NOT. TAIL_Q_STATE_INITIALIZED(JB_IN)) QABS = QPHYS", self.main)
        self.assertIn("[V38_ACTIVE_MACRO]", self.main)


if __name__ == "__main__":
    unittest.main()
