# V38 BHT–SJ Active Macro Closure

Updated: 2026-07-19

## Purpose and boundary

V38 tests the smallest active implementation supported by the V35–V37 evidence: one conservative BHT–SJ macro control volume, without crossing the BR2 junction and without interpreting the fitted resistance as the physical Manning coefficient of the whole reservoir.

The trial contract is explicit and reversible:

- `tail_domain.opt`: `1 26`; branch 1 owns segments 2:27.
- `tail_macro_active.opt`: `1 28 NEFF`; segment 28 is the coupling section immediately before the BR2 junction.
- `NEFF` is an engineering-effective resistance for this macro reach only. It combines unresolved local loss, profile, bathymetry and roughness effects.
- With either option absent, the established V24–V37 path remains active. An active interface that does not equal the coupling section is rejected at startup.

## Processing and state chain

For a trial upstream and downstream stage, V38 constructs the same distance-weighted linear water-surface profile used by the conservative storage calculation. At every section it evaluates the real cross-section area and hydraulic radius, integrates Manning resistance by the trapezoidal rule, adds the endpoint velocity-head coefficient, and obtains

`Q = sqrt((WUP - WDN) / (Rfriction + Rvelocity))`.

The identical closure is used in both directions:

1. invert discharge to establish the hydraulic upstream stage;
2. evaluate the old and new discharge targets during the continuity update;
3. retain the existing single-control-volume balance `dV/dt = Qin - Qinterface`;
4. invert the same profile-storage relation back to stage;
5. commit the existing sole interface discharge to the reservoir consumer.

No second flux, hidden storage correction or side-branch source is introduced. The first active state initializes its committed discharge from physical inflow; subsequent states use the existing dynamic discharge state. Active storage inversion uses a stricter numerical tolerance so that the existing V27/V32 conservation gates are met without relaxing their thresholds.

## Short-window scan

The final scan uses JDAY 44430.0–44436.5, segments 2:27 and coupling section 28.

| Effective n | BHT bias (m) | BHT RMSE (m) | BHT slope ratio | SJ RMSE (m) | XLD→BHT head RMSE (m) |
|---:|---:|---:|---:|---:|---:|
| 0.0650 | -0.702 | 1.024 | 0.612 | 0.489 | 1.038 |
| 0.0700 | -0.285 | 0.732 | 0.669 | 0.471 | 0.724 |
| 0.0725 | -0.052 | 0.659 | 0.686 | 0.462 | 0.633 |
| 0.0750 | +0.182 | 0.675 | 0.699 | 0.450 | 0.625 |

The useful region is a flat interval near 0.070–0.075 rather than a sharply identifiable point. `0.0725` is retained as the validation candidate because it nearly removes BHT and total-head bias while avoiding the positive BHT bias at `0.075`.

All final scan cases have zero computational warnings. Maximum V24/V31 residuals remain below `7e-9 m3/s`; V27 profile and V32 segment-volume gaps remain below `1e-4 m3`.

## Review

V38 succeeds where V36 failed because it changes the reach-scale momentum representation while keeping a single, conservative control volume. It does not merely enlarge ownership under the old local closure. It also avoids the premature two-state design: the new downstream boundary is already a physical junction boundary, so no side branch is crossed.

This is still an optional engineering closure, not a new default physical parameter set. The short-window result alone is insufficient for acceptance; V39 performs the untuned 54-day check.
