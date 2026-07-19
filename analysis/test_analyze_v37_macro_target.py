from __future__ import annotations

import unittest

from analyze_v37_macro_target import parse_macro_targets, summarize


class V37MacroTargetTests(unittest.TestCase):
    def test_parser_filters_branch(self) -> None:
        text = "\n".join(
            [
                "[V37_MACRO_TARGET] JB=1 ISEG=26 JDAY=1 QPHYS=100 QCOMMIT=90 QTARGET=99 QAGG=95 WUP=590 WIFACE=589 DX=20000 RCOEFF=1E-7 RFRIC=9E-8 RVEL=1E-8 VALID=T",
                "[V37_MACRO_TARGET] JB=2 ISEG=30 JDAY=1 QPHYS=200 QCOMMIT=180 QTARGET=198 QAGG=190 WUP=591 WIFACE=590 DX=30000 RCOEFF=2E-7 RFRIC=19E-8 RVEL=1E-8 VALID=T",
            ]
        )
        rows = parse_macro_targets(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].interface_segment, 26)
        self.assertEqual(rows[0].qtarget, 99.0)

    def test_summary_measures_flow_closure(self) -> None:
        rows = parse_macro_targets(
            "\n".join(
                [
                    "[V37_MACRO_TARGET] JB=1 ISEG=26 JDAY=1 QPHYS=100 QCOMMIT=100 QTARGET=90 QAGG=90 WUP=590 WIFACE=589 DX=20000 RCOEFF=1E-4 RFRIC=9E-5 RVEL=1E-5 VALID=T",
                    "[V37_MACRO_TARGET] JB=1 ISEG=26 JDAY=2 QPHYS=200 QCOMMIT=200 QTARGET=220 QAGG=220 WUP=591 WIFACE=589 DX=20000 RCOEFF=5E-5 RFRIC=4E-5 RVEL=1E-5 VALID=T",
                ]
            )
        )
        summary = summarize(rows)
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["interface_segment"], 26)
        self.assertAlmostEqual(summary["qtarget_qcommit_ratio_median"], 1.0)
        self.assertEqual(summary["qtarget_qcommit_ratio_within_20pct_fraction"], 1.0)


if __name__ == "__main__":
    unittest.main()
