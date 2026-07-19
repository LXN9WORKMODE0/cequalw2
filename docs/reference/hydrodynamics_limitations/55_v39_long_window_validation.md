# V39 Untuned 54-Day Validation

Updated: 2026-07-19

## Validation contract

The V38 candidate `NEFF=0.0725` was selected using JDAY 44430.0–44436.5. V39 freezes that value and runs both the default baseline and candidate over the original JDAY 44430.0–44484.0 case. No further calibration is performed.

The input-package audit found no flagged processed points for XLD, YMT, SJ or BHT in this window. Both runs use the same executable, forcing, observations and multi-station analysis. The candidate differs only by `tail_domain.opt = 1 26` and `tail_macro_active.opt = 1 28 0.0725`.

## Full-window evidence

| Metric | Baseline | V38 candidate | Change |
|---|---:|---:|---:|
| BHT RMSE (m) | 3.244 | 0.979 | -69.80% |
| SJ RMSE (m) | 1.415 | 1.245 | -11.98% |
| XLD→BHT head RMSE (m) | 2.614 | 0.542 | -79.25% |
| YMT→SJ head RMSE (m) | 0.541 | 0.295 | -45.57% |
| XLD RMSE (m) | 0.733 | 0.757 | +3.27% |
| YMT RMSE (m) | 0.969 | 1.000 | +3.17% |
| BHT stage–Q slope ratio | 0.381 | 0.798 | closer to 1 |

The candidate BHT bias is `-0.637 m` rather than the baseline `-2.660 m`. Total XLD→BHT head bias is `-0.055 m` rather than `-2.112 m`.

## Window robustness and conservation

The 54 days were also divided into seven-day windows plus the final five days. Candidate BHT and SJ RMSE improve in all eight windows. The worst baseline BHT window, JDAY 44444–44451, changes from `5.772 m` to `1.678 m`; the final window changes from `1.551 m` to `0.574 m`. XLD and YMT changes are small and mixed, consistent with the intended upstream reach-scale influence.

Both runs finish with zero computational warnings. The candidate has:

- maximum V24/V31 mass residual `9.3169e-9 m3/s`;
- maximum V27 profile-storage gap `9.8705e-5 m3`;
- maximum V32 segment-volume gap `9.9987e-5 m3`.

The default-off 6.5-day rerun remains byte-identical to the pre-V38 baseline:

- `wl.csv`: `4BF244290DFB8AC38965F4E2A69FA06CE6A2D4EE339250B55494F7280AD3D9FE`
- `flowbal.csv`: `020705597433EDBA2F228DEB6E051177DD05D31D7998FC829E9C4E0CDE614FBE`

## Decision

The active macro closure is retained as an optional experimental capability and `NEFF=0.0725` as the current BHT–SJ validation candidate. The result is strong enough to continue from this implementation; it does not justify writing `0.0725` into the reservoir's physical Manning input or enabling it by default.

The next useful exploration is out-of-sample forcing or another year with compatible BHT endpoint data. A second SJ–YMT state should only be introduced if evidence shows a remaining error that the one-state boundary-preserving closure cannot represent.
