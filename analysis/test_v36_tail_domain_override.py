from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "w2source_v455_2_11_2026"


class V36TailDomainOverrideTests(unittest.TestCase):
    def test_override_is_per_branch_and_default_preserving(self) -> None:
        modules = (SOURCE / "w2modules.F90").read_text(encoding="utf-8", errors="ignore")
        input_source = (SOURCE / "input.F90").read_text(encoding="utf-8", errors="ignore")
        init_source = (SOURCE / "init.F90").read_text(encoding="utf-8", errors="ignore")
        geometry = (SOURCE / "init-geom.F90").read_text(encoding="utf-8", errors="ignore")

        self.assertIn("ALLOCATABLE, DIMENSION(:)       :: TAIL_FIXED_MIN_NSEG", modules)
        self.assertIn("TAIL_FIXED_MIN_NSEG(NBR)", input_source)
        self.assertIn("TAIL_MACRO_INTERFACE_SEG(NBR)", input_source)
        self.assertIn("TAIL_FIXED_MIN_NSEG = 4", init_source)
        self.assertIn("TAIL_FIXED_MIN_NSEG(JB)", geometry)

    def test_override_is_explicit_bounded_and_observable(self) -> None:
        init_source = (SOURCE / "init.F90").read_text(encoding="utf-8", errors="ignore")
        geometry = (SOURCE / "init-geom.F90").read_text(encoding="utf-8", errors="ignore")

        self.assertIn("CALL LOAD_TAIL_DOMAIN_OPTIONS", init_source)
        self.assertIn("tail_domain.opt", geometry)
        self.assertIn("tail_macro.opt", geometry)
        self.assertIn("NSEG_CONFIG > MAX_TAIL_SEG", geometry)
        self.assertIn("[V36_TAIL_DOMAIN_CONFIG]", geometry)

    def test_macro_interface_is_shadow_only(self) -> None:
        init_source = (SOURCE / "init.F90").read_text(encoding="utf-8", errors="ignore")
        main_source = (SOURCE / "w2_main.f90").read_text(encoding="utf-8", errors="ignore")

        self.assertIn("TAIL_MACRO_INTERFACE_SEG = 0", init_source)
        self.assertIn("[V37_MACRO_TARGET]", main_source)
        self.assertIn("SUBROUTINE COMPUTE_TAIL_MACRO_LINK_FLOW", main_source)
        self.assertNotIn("TAIL_Q_LINK(JB) = TAIL_MACRO", main_source)


if __name__ == "__main__":
    unittest.main()
