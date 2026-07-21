from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_v42_multiyear_macro_closure import TailGeometry, isolated_spike_mask


ROOT = Path(__file__).resolve().parents[1]
BATHYMETRY = ROOT / "cases/xld_2021_base/InputFiles/BTH/DIXING20250226.csv"


class TailGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.geometry = TailGeometry.from_bathymetry(BATHYMETRY)

    def test_reach_length_matches_fortran_run(self) -> None:
        self.assertAlmostEqual(self.geometry.reach_length(), 23830.0, places=6)

    def test_fortran_first_logged_point(self) -> None:
        # The W2 warning log rounds both stages to 0.01 m, so a few m3/s of
        # difference is expected when the exact geometry formula is replayed.
        flow = self.geometry.aggregate_flow_array(
            np.array([588.87]), np.array([576.57]), 0.0725
        )[0]
        self.assertAlmostEqual(flow, 5360.0, delta=5.0)

    def test_lower_effective_manning_increases_flow(self) -> None:
        q070 = self.geometry.aggregate_flow_array(
            np.array([588.87]), np.array([576.57]), 0.070
        )[0]
        q075 = self.geometry.aggregate_flow_array(
            np.array([588.87]), np.array([576.57]), 0.075
        )[0]
        self.assertGreater(q070, q075)

    def test_complete_equation_recovers_effective_manning(self) -> None:
        wup = np.array([588.87])
        wdn = np.array([576.57])
        q070 = self.geometry.aggregate_flow_array(wup, wdn, 0.070)[0]
        _, rfric, rvel, valid = self.geometry.aggregate_components_array(
            wup, wdn, 0.0725
        )
        recovered = np.sqrt(
            ((wup[0] - wdn[0]) / q070**2 - rvel[0])
            / (rfric[0] / 0.0725**2)
        )
        self.assertTrue(valid[0])
        self.assertAlmostEqual(recovered, 0.070, places=12)

    def test_stage_inversion_round_trip(self) -> None:
        expected = np.array([588.87, 590.0])
        downstream = np.array([576.57, 580.0])
        target = self.geometry.aggregate_flow_array(expected, downstream, 0.0725)
        solved, representable = self.geometry.solve_upstream_stage_array(
            target, downstream, 0.0725
        )
        self.assertTrue(representable.all())
        reconstructed = self.geometry.aggregate_flow_array(
            solved, downstream, 0.0725
        )
        np.testing.assert_allclose(reconstructed, target, atol=1.0e-3, rtol=0.0)

    def test_profile_volume_increases_with_upstream_stage(self) -> None:
        volume = self.geometry.profile_volume_array(
            np.array([585.0, 586.0]), np.array([580.0, 580.0])
        )
        self.assertGreater(volume[1], volume[0])


class QualityControlTest(unittest.TestCase):
    def test_isolated_spike_only(self) -> None:
        values = pd.Series([580.0, 580.1, 600.0, 580.2, 580.3])
        mask = isolated_spike_mask(values)
        self.assertEqual(mask.tolist(), [False, False, True, False, False])

    def test_sustained_change_is_not_called_spike(self) -> None:
        values = pd.Series([580.0, 580.1, 590.0, 590.1, 590.2])
        self.assertFalse(isolated_spike_mask(values).any())


if __name__ == "__main__":
    unittest.main()
