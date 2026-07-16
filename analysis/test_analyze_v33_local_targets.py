from __future__ import annotations

import unittest

from analyze_v33_local_targets import parse_local_targets, summarize


class LocalTargetAnalysisTests(unittest.TestCase):
    def test_parser_filters_branch_and_preserves_interface(self) -> None:
        text = "\n".join(
            [
                "[V33_LOCAL_TARGET] JB=1 IS=1 ISEG=2 QCOMMIT=100 QTARGET=120 WUP=590 WDN=589 DX=700 STORAGE=1000",
                "[V33_LOCAL_TARGET] JB=2 IS=1 ISEG=20 QCOMMIT=1000 QTARGET=1200 WUP=590 WDN=589 DX=700 STORAGE=10000",
            ]
        )

        samples = parse_local_targets(text, branch=1)

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].upstream_segment, 2)
        self.assertEqual(samples[0].qtarget, 120.0)

    def test_summary_groups_interfaces_and_computes_ratio(self) -> None:
        text = "\n".join(
            [
                "[V33_LOCAL_TARGET] JB=1 IS=1 ISEG=2 QCOMMIT=100 QTARGET=100 WUP=590 WDN=589 DX=700 STORAGE=1000",
                "[V33_LOCAL_TARGET] JB=1 IS=1 ISEG=2 QCOMMIT=200 QTARGET=240 WUP=591 WDN=589 DX=700 STORAGE=1100",
                "[V33_LOCAL_TARGET] JB=1 IS=2 ISEG=3 QCOMMIT=100 QTARGET=200 WUP=589 WDN=588 DX=800 STORAGE=900",
            ]
        )

        rows = summarize(parse_local_targets(text))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["count"], 2)
        self.assertAlmostEqual(rows[0]["target_commit_ratio_mean"], 1.1)
        self.assertEqual(rows[1]["target_commit_ratio_median"], 2.0)


if __name__ == "__main__":
    unittest.main()
