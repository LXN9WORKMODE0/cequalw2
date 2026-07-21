from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from audit_v42_full_model_forcing_coverage import forcing_role, summarize_declared_window


class FullModelForcingAuditTest(unittest.TestCase):
    def test_forcing_roles(self) -> None:
        self.assertEqual(forcing_role(Path("metinput_34.csv")), "meteorology")
        self.assertEqual(forcing_role(Path("DT_QIN_BHT.csv")), "inflow_or_distributed_flow")
        self.assertEqual(forcing_role(Path("DT_TIN_BHT.npt")), "temperature")

    def test_declared_window_requires_every_file(self) -> None:
        files = pd.DataFrame(
            [
                {"role": "meteorology", "exists": True, "first_jday": 44400.0, "last_jday": 44500.0},
                {"role": "temperature", "exists": True, "first_jday": 44430.0, "last_jday": 44484.0},
                {"role": "inflow_or_distributed_flow", "exists": True, "first_jday": 44431.0, "last_jday": 44484.0},
            ]
        )
        result = summarize_declared_window(files)
        inflow = result[result["role"] == "inflow_or_distributed_flow"].iloc[0]
        self.assertFalse(inflow["role_ready"])
        self.assertFalse(result["all_required_roles_ready"].iloc[0])


if __name__ == "__main__":
    unittest.main()
