from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "w2source_v455_2_11_2026" / "w2_main.f90"


class V41RoundoffAwareConservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8", errors="ignore")

    def test_residual_removes_only_provable_storage_roundoff_bound(self) -> None:
        self.assertIn("FUNCTION TAIL_CONTINUITY_RESIDUAL", self.source)
        self.assertIn("0.5D0*MAX(SPACING(VOLUME_OLD),SPACING(VOLUME_NEW))", self.source)
        self.assertIn("MAX(ABS(RAW_RESIDUAL)-ROUND_BOUND,0.0D0)", self.source)

    def test_local_and_full_step_contract_use_same_adjustment(self) -> None:
        self.assertGreaterEqual(self.source.count("TAIL_CONTINUITY_RESIDUAL("), 3)
        self.assertIn("'RRAW=',TAIL_FULL_STORAGE_RAW", self.source)
        self.assertIn("'RBOUND=',TAIL_FULL_STORAGE_ROUNDOFF", self.source)


if __name__ == "__main__":
    unittest.main()
