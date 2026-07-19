# V41 Long-Window Parameter-Interval Robustness

Updated: 2026-07-19

## Contract

V41 freezes the V38 structure and the V40 acceptance rules, then runs the two previously declared interval boundaries `NEFF=0.070` and `0.075` over the full JDAY 44430–44484 case. The existing `0.0725` run is the interval center. No result is used to select a new point.

## Roundoff-aware conservation diagnosis

The first boundary run exposed a diagnostic limit rather than a state-equation error. At one `0.070` step:

- storage was about `1.6721e8 m3` and `DT=1.195897 s`;
- raw continuity residual was `-1.1095e-8 m3/s`;
- the double-precision half-ULP storage projection bound was `1.2460e-8 m3/s`;
- the independent full/local storage-rate gap remained exactly zero.

At a `0.075` step, raw residual `1.0731e-8` was likewise below its `1.2768e-8` bound. Because the machine representation floor can exceed the established `1e-8` gate at `O(1e8 m3)` storage, the diagnostic now records `RRAW` and `RBOUND` and tests only `max(abs(RRAW)-RBOUND, 0)` against the unchanged physical tolerance. Storage, stage, discharge, interface consumption and the threshold itself are not changed.

## Strict holdout interval result

| Effective n | BHT RMSE reduction | Total-head RMSE reduction | Maximum other-station worsening | All six regimes improve |
|---:|---:|---:|---:|:---:|
| 0.0700 | 65.96% | 78.53% | 3.69% | yes |
| 0.0725 | 70.37% | 80.74% | 3.61% | yes |
| 0.0750 | 74.20% | 80.57% | 3.65% | yes |

The minimum BHT reduction across any individual regime is `60.95%`, `64.71%` and `66.64%` respectively. The minimum total-head reduction is `62.13%`, `59.00%` and `53.79%`. Every candidate passes every predeclared gate.

Holdout BHT RMSE changes from baseline `3.428 m` to `1.167/1.016/0.884 m`; BHT stage–Q slope ratio changes from `0.210` to `0.722/0.744/0.764`. Total-head RMSE becomes `0.589/0.529/0.533 m`.

## Decision

The supported object is an interval near `0.070–0.075`, not an identifiable exact coefficient. `0.0725` remains the validation candidate because it is the preselected interval center, has near-zero total-head bias, and avoids retuning on validation evidence. It remains optional and default-off.

The reduced build, full test suite and fresh default-off smoke must remain required release checks. Independent-year acceptance still requires compatible BHT endpoint and forcing data.
