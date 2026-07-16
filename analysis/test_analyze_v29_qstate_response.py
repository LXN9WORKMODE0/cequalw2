from __future__ import annotations

import math
import unittest

from analyze_v29_qstate_response import (
    AcceptedTailState,
    best_response_lag_days,
    hold_statistics,
    parse_accepted_tail,
)


class AcceptedTailResponseTests(unittest.TestCase):
    def test_parser_keeps_only_requested_branch(self) -> None:
        text = "\n".join(
            [
                "[V29_ACCEPTED_TAIL] JB=1 JDAY=1 DT=10 QPHYS=100 QSTATE=90 QTARGET=95 QMAX=120 STORAGE=1000 WUP=590 WDN=580 DVUP=10 DVDN=20 CAP=F",
                "[V29_ACCEPTED_TAIL] JB=2 JDAY=1 DT=10 QPHYS=1000 QSTATE=900 QTARGET=950 QMAX=1200 STORAGE=10000 WUP=590 WDN=580 DVUP=100 DVDN=200 CAP=T",
            ]
        )

        rows = parse_accepted_tail(text, branch=1)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].qstate, 90.0)
        self.assertFalse(rows[0].cap)

    def test_hold_statistics_measure_repeated_state_duration(self) -> None:
        rows = [
            AcceptedTailState(jday=0.0, dt=86400.0, qphys=float(index), qstate=value, qtarget=value, qmax=10.0, storage=1.0, wup=1.0, wdn=0.0, dvup=1.0, dvdn=1.0, cap=False)
            for index, value in enumerate([1.0, 1.0, 1.0, 2.0])
        ]

        count, fraction, duration = hold_statistics(rows)

        self.assertEqual(count, 2)
        self.assertAlmostEqual(fraction, 2.0 / 3.0)
        self.assertEqual(duration, 2.0)

    def test_lag_scan_finds_delayed_state(self) -> None:
        qphys = [0.0, 1.0, 4.0, 2.0, 5.0, 3.0, 6.0]
        rows = [
            AcceptedTailState(
                jday=float(index),
                dt=86400.0,
                qphys=qphys[index],
                qstate=qphys[max(index - 1, 0)],
                qtarget=qphys[index],
                qmax=10.0,
                storage=1.0,
                wup=1.0,
                wdn=0.0,
                dvup=1.0,
                dvdn=1.0,
                cap=False,
            )
            for index in range(len(qphys))
        ]

        lag, corr = best_response_lag_days(rows, max_lag=2.0, step=1.0)

        self.assertEqual(lag, 1.0)
        self.assertTrue(math.isclose(corr, 1.0))


if __name__ == "__main__":
    unittest.main()
