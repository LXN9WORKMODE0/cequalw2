from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from run_v36_tail_domain_scan import parse_v36_config, select_primary_station_rows


class V36TailDomainScanTests(unittest.TestCase):
    def test_parses_branch_config_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "w2.wrn"
            path.write_text(
                "[V36_TAIL_DOMAIN_CONFIG] JB=1 MIN_NSEG=26 MAX_SUPPORTED=64\n",
                encoding="utf-8",
            )

            self.assertEqual(parse_v36_config(path), (26, 64))

    def test_primary_station_selection_drops_ss_alternative(self) -> None:
        rows = [
            {"station_code": "SS", "mapping_variant": "downstream_boundary_origin", "bias_m": 1.0},
            {"station_code": "SS", "mapping_variant": "segment222_center_origin", "bias_m": 2.0},
            {"station_code": "SJ", "mapping_variant": "source_mapping", "bias_m": 3.0},
        ]

        selected = select_primary_station_rows(rows)

        self.assertEqual(selected["SS"]["bias_m"], 1.0)
        self.assertEqual(selected["SJ"]["bias_m"], 3.0)


if __name__ == "__main__":
    unittest.main()
