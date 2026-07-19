# V40 Strict Holdout and Regime Validation

Updated: 2026-07-19

## Contract

V38 selected `NEFF=0.0725` using JDAY 44430.0–44436.5. V40 excludes that interval completely and evaluates only the 1140 hourly samples after `44436.5` through `44484.0`. XLD, YMT, SJ and BHT have zero flagged processed points in the holdout.

Acceptance thresholds were fixed before reading the result:

- BHT RMSE reduction at least 50%;
- XLD→BHT total-head RMSE reduction at least 50%;
- XLD, YMT or SJ RMSE worsening no greater than 10%;
- zero computational warnings and all existing conservation gates;
- BHT and total-head RMSE improve in every flow and trend regime.

Flow thirds are defined from holdout physical discharge only: low `Q <= 5733.33 m3/s`, middle `5733.33 < Q <= 6830 m3/s`, and high above `6830 m3/s`. Rising, steady and falling classes use centered hourly physical-discharge change. Flow is interpolated to observation times because the two hourly files use slightly different decimal-day rounding phases.

## Strict holdout result

| Metric | Baseline | `NEFF=0.0725` | Change |
|---|---:|---:|---:|
| BHT RMSE (m) | 3.428 | 1.016 | -70.37% |
| XLD→BHT head RMSE (m) | 2.745 | 0.529 | -80.74% |
| SJ RMSE (m) | 1.474 | 1.317 | -10.67% |
| XLD RMSE (m) | 0.777 | 0.805 | +3.61% |
| YMT RMSE (m) | 1.031 | 1.064 | +3.16% |
| BHT stage–Q slope ratio | 0.210 | 0.744 | closer to 1 |

All predeclared full-holdout gates pass.

## Regime result

| Regime | Samples | BHT RMSE baseline→candidate (m) | Reduction | Total-head reduction |
|---|---:|---:|---:|---:|
| Low flow | 380 | 1.601→0.565 | 64.71% | 59.00% |
| Middle flow | 382 | 2.770→0.775 | 72.04% | 84.90% |
| High flow | 378 | 5.011→1.478 | 70.51% | 82.90% |
| Rising | 565 | 2.895→0.837 | 71.09% | 81.26% |
| Steady | 218 | 5.466→1.641 | 69.98% | 87.36% |
| Falling | 357 | 2.453→0.736 | 70.00% | 67.62% |

The gain is not produced by one flow range or hydrograph direction. The weakest regime still improves BHT by 64.7% and total head by 59.0%.

## Review

V40 converts the earlier 54-day comparison into a true temporal holdout test relative to the parameter-selection window. It supports the macro-closure mechanism without supplying new evidence that `NEFF` is a physical roughness. The next test is parameter-interval robustness, not point retuning.
