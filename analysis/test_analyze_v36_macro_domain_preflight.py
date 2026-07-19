from __future__ import annotations

import unittest

from analyze_v36_macro_domain_preflight import (
    DomainCandidate,
    candidate_row,
    center_distance_m,
    parse_branch_connections,
    parse_dlx_rows,
)


class V36MacroDomainPreflightTests(unittest.TestCase):
    def test_parses_dlx_and_center_spacing(self) -> None:
        rows = [["DLX", *[str(100 * segment) for segment in range(1, 223)]]]

        dlx = parse_dlx_rows(rows)

        self.assertEqual(dlx[2], 200.0)
        self.assertAlmostEqual(center_distance_m(dlx, 1, 4), 750.0)

    def test_parses_branch_grid_definition(self) -> None:
        rows = [
            ["BR1", "BR2"],
            ["2", "225"],
            ["222", "226"],
            ["0", "0"],
            ["0", "28"],
        ]

        connections = parse_branch_connections(rows, branch_count=2)

        self.assertEqual(connections[1].first_segment, 225)
        self.assertEqual(connections[1].downstream_host_segment, 28)

    def test_candidate_crossing_junction_requires_branch_source(self) -> None:
        rows = [
            ["BR1", "BR2"],
            ["2", "225"],
            ["222", "226"],
            ["0", "0"],
            ["0", "28"],
        ]
        connections = parse_branch_connections(rows, branch_count=2)
        dlx = {segment: 1000.0 for segment in range(1, 223)}
        candidate = DomainCandidate("test", 2, 56, 57, 2, "two_intervals", "review")

        row = candidate_row(candidate, dlx, connections)

        self.assertEqual(row["owned_branch_junctions"], "BR2@SEG28")
        self.assertIn("BR2_Q_T_C", row["required_source_contract"])
        self.assertEqual(row["required_state_zones"], 2)


if __name__ == "__main__":
    unittest.main()
