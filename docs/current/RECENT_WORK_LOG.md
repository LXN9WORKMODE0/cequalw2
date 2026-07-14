# Recent Work Log

Updated: 2026-04-14

## Summary

This log records the recent reduction, packaging, case-validation, workspace-cleanup, and final Stage 4 boundary work for the CE-QUAL-W2 v4.5.5 workspace.

## 2026-04-14 Actual Case Migration Note

- Reviewed the current reduction documents before touching the user-provided `实际案例` directory.
- Confirmed the active reduced boundary remains:
  - hydrodynamics
  - temperature
  - gate / spill / pipe structure-flow behavior
  - structural withdrawal and selective withdrawal
  - no runtime water quality
  - no TDG support
- Inspected `C:\Users\NING\Desktop\v455\实际案例\w2_con.csv` and confirmed it was still a v4.5-era full-shape control file carrying the legacy water-quality block and TDG-related output requests.
- Verified that the reduced executable initially failed during `INPUT` on that legacy control file shape.
- Preserved the original control file as:
  - `C:\Users\NING\Desktop\v455\实际案例\w2_con_v45_original.csv`
- Converted the working control file in:
  - `C:\Users\NING\Desktop\v455\实际案例\w2_con.csv`
- The conversion strategy was:
  - keep the existing hydrodynamic / geometry / structure configuration already present in the case
  - remove the legacy water-quality / TDG section from the active working copy
  - rewrite the trailing `FILE NAMES` section to the reduced CSV contract currently accepted by `input.F90`
- Added explicit placeholder files required by the reduced CSV file-name contract for unused inputs:
  - `ext_unused.npt`
  - `qot_unused.npt`
  - `pre_unused.npt`
  - `tpr_unused.npt`
  - `euh_unused.npt`
  - `tuh_unused.npt`
  - `edh_unused.npt`
  - `tdh_unused.npt`
- Rebuilt the console executable from the canonical reduced source tree:
  - `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe`
- Verified that the rebuilt reduced executable now accepts the migrated `实际案例` inputs and enters runtime instead of failing in `INPUT`.
- Representative outputs observed in `C:\Users\NING\Desktop\v455\实际案例` after the migrated run started:
  - `XLD.w2l`
  - `XLD_snp.opt`
  - `XLD_spr.csv`
  - `XLD_cpl.opt`
  - `flowbal.csv`
  - `wl.csv`
  - `XLD_tsr_*.csv`
- Runtime side observations:
  - `w2.err` remained empty during the checked run window
  - `w2.wrn` contained layer add/subtract runtime messages rather than an input-contract failure
  - `reduced_run.log` advanced through repeated screen checkpoints up to approximately `JDAY=44442.49` before the desktop session timeout interrupted the unattended verification run
- Engineering interpretation:
  - the user-provided `实际案例` has now been adapted into a reduced-build runnable form for in-workspace use
  - this work demonstrates practical compatibility of that case with the current reduced parser/runtime path
  - this case has not yet been promoted into the formal supported baseline or packaged acceptance set, because a full uninterrupted end-to-end completion was not captured in this session

## Completed Engineering Work

- Established `w2source_v455_2_11_2026` as the canonical source tree.
- Fixed the `GTNAME` conflict in `hydroinout.F90`.
- Restored `SED_DIAG` compatibility in `input.F90`.
- Implemented stage 1 of hydrodynamics-only reduction:
  - the reduced build now forces water quality off at runtime
  - GUI and console main flows no longer enter `wqconstituents` in the reduced build path
- Implemented stage 2 reduced-path source isolation for initial outputs:
  - `temperature.F90` no longer needs water-quality `ENTRY` points in the reduced path
  - reduced-path placeholders are initialized for `REAER`, `KF`, and `CD`
  - `AERATEC` is now parser-compatible but ignored in the reduced path
  - `Plunge_Point` remains outside the active reduced-path call graph
- Implemented stage 3 reduced-build file removal:
  - removed `water-quality.f90`
  - removed `wqconstituents.F90`
  - removed `gas-transfer.f90`
  - removed `ReduceReaerAlgae.f90`
  - removed `aerate.f90`
  - removed `Plunge_Point.f90`
  - updated GUI and console build scripts so they no longer compile those files
  - removed residual live reduced-path references from `temperature.F90`, `layeraddsub.F90`, `w2_4_win.f90`, `w2_main.f90`, and `endsimulation.F90`
- Added and verified a console build path.
- Preserved the original GUI entry chain and added a verified `ReducedGUI` build path.
- Added packaging for `ReducedGUI.zip`.
- Promoted the Bonneville-shaped reduced case family to the current supported runtime baseline.
- Implemented stage 4 final-boundary narrowing:
  - kept structure-flow support in `gate-spill-pipe.f90`
  - kept structural-withdrawal and selective-withdrawal support in `withdrawal.f90`
  - removed TDG source files from the source tree:
    - `systdg.f90`
    - `tdg.f90`
    - `TDGtarget.f90`
    - `tdg - Copy.f90`
  - removed dead TDG global state from `w2modules.F90`, `input.F90`, and `endsimulation.F90`
  - isolated `time-varying-data.f90` from `modSYSTDG` so the reduced build no longer depends on TDG modules
  - tightened `input.F90` so TDG files and TDG output requests now fail early
  - cleaned supported cases and packaged cases so they no longer ship TDG files or TDG outputs
  - rebuilt and repackaged `ReducedGUI.zip` after the TDG cleanup

## Supported Runtime Baseline

Supported:

- `temp_case_work`
- `绀轰緥鏂囦欢2`
- `w2source_v455_2_11_2026\packaging\cases\minimal_case_inputs`
- `w2source_v455_2_11_2026\packaging\cases\minimal_case_verified`

Unsupported legacy case:

- `_workspace_archive\unsupported_cases\绀轰緥鏂囦欢`

Reason:

- it uses a materially different and larger control-file shape
- prior testing indicated it did not run reliably even with the original v455 executable

## Final Reduced Contract

Supported:

- gate / spill / pipe structure-flow behavior
- structural withdrawal behavior
- selective-withdrawal temperature control

Not supported:

- `w2_systdg.npt`
- `w2_TDGtarget.csv`
- `TDGdyntarget.csv`
- `TDG_output.csv`
- `TDGTarget_output.csv`
- `TDGTarget_warning.opt`
- `%DO` / `TDG` output requests
- `GASSPC = ON` / `GASGTC = ON`

## Packaging Outcome

Package path:

- `w2source_v455_2_11_2026\dist\ReducedGUI.zip`

Package structure:

- `app\w2_v455_reduced_gui.exe`
- `cases\minimal_case_inputs\`
- `cases\minimal_case_verified\`
- `docs\README.txt`
- `docs\PREREQUISITES.txt`
- `docs\SUPPORTED_CASES.txt`

Meaning of the two packaged cases:

- `minimal_case_inputs`
  - clean-input baseline intended for a fresh run
  - contains no TDG control files
- `minimal_case_verified`
  - verification snapshot containing representative outputs from a successful no-TDG baseline run

## Workspace Cleanup

The root workspace was cleaned so that only the active source tree, active supported cases, archive root, and top-level project documentation remain in place.

Archived locations:

- `_workspace_archive\historical_debug\temp_compile`
- `_workspace_archive\historical_debug\temp_w2_build`
- `_workspace_archive\historical_debug\VS鎵嬪姩缂栬瘧log`
- `_workspace_archive\unsupported_cases\绀轰緥鏂囦欢`

Deleted scratch directories:

- `temp_zero_read_test`
- `temp_package_inputs_test`
- `temp_package_inputs_test2`

## Current State

- The console build works.
- The GUI build works.
- The reduced GUI executable still launches successfully.
- The packaged clean-input baseline runs successfully without TDG files.
- A clean-input copy with `AERATEC = ON` and no aeration input file still enters the reduced runtime path.
- Validation runs still show stable `ReaerationCoeff(day-1)` output values of `0.000` in the reduced path.
- Stage 1 behavior is in place: the reduced build behaves as hydrodynamics + temperature at runtime.
- Stage 2 behavior is in place: reduced-path initial outputs are no longer initialized through water-quality entry points.
- Stage 3 behavior is in place: the reduced build no longer compiles or ships the removed dormant water-quality source files.
- Stage 4 behavior is now in place: the reduced deliverable keeps structure flow and selective withdrawal while explicitly rejecting TDG-related files and output requests.

## 2026-04-27 V22 Hydrodynamic Interface Diagnosis

- Added `V22_BOUNDARY_FLUX` diagnostics for branch 1 to separate physical BHT inflow, effective reservoir inflow, distributed source contribution, total source/sink contribution, and tailreach feedback flow.
- Fixed the redistribution scan writer so `.npt` integer values keep a decimal point; without this, W2 can misread rewritten BHT outflow values by roughly one order of magnitude.
- Re-ran full-window redistribution diagnostics with `TMEND=44436.5`:
  - `bht_a00`: baseline, `QDT_SUM mean = 154.24`, `tail_q_max = 10255`
  - `bht_a100`: BHT active distributed moved to BHT outflow, `QDT_SUM mean = 0`, `tail_q_max = 10255`
  - `all_a100`: all positive active distributed moved to BHT outflow, `QDT_SUM mean = 0`, `tail_q_max = 10255`
- Current conclusion: moving distributed flow to the BHT tail changes the mass-entry path and water-level bias, but does not remove the V21 interface Q residual peak. Next work should focus on the interface Q update and the `TAIL_Q_LINK -> QEFF` coupling path.
- Additional localization: all three full-window cases hit `tail_q_max = 10255` at the same early warning-log event, with `Q_P = 7315.457` and `Q_C = 15936.757`; this makes the peak look like a shared initial tailreach/interface transient rather than a distributed-flow placement effect.

## 2026-04-28 V23 Q Update Mode Diagnosis

- Added diagnostic environment switch `W2_TAIL_Q_UPDATE_MODE`:
  - `SECANT`: current V21 behavior
  - `RELAX`: Q uses residual relaxation only
  - `HOLD`: Q guess is held fixed inside the interface iteration
- Added `[V23_Q_UPDATE_MODE]` marker and parser coverage so each scan row records the active Q update mode.
- Short-window `TMEND=44431.0`, `bht alpha=0` result:
  - `SECANT`: `tail_q_max = 10255`
  - `RELAX`: `tail_q_max = 1985.8`
  - `HOLD`: `tail_q_max = 3002.6`
- Full-window `TMEND=44436.5`, `bht alpha=0` confirmation:
  - `SECANT`: `tail_eta_max = 0.45645`, `tail_q_max = 10255`, `head_bias = 0.971229`
  - `RELAX`: `tail_eta_max = 0.45858`, `tail_q_max = 1985.8`, `head_bias = 0.967227`
- Current conclusion: the V21 Q secant update is the immediate amplifier of the `10255` Q residual peak. Q should use conservative relaxation or a gated secant strategy, not unconditional secant during startup.

## 2026-07-15 V24 Interface Conservation Refactor

- Reorganized the workspace around one tracked baseline case and ignored `analysis/.runs/` outputs; started V24 from clean commit `1859ee8`.
- Quantified the V23 conservation gaps with `[V24_INTERFACE_MASS]`: `max|RTAIL|=10309`, `max|RFLUX|=9619.6`, `max|RCOMB|=2732.4`, and unaccounted segment flow loss `171.45 m3/s`.
- Replaced the tail-only four-step pseudo-implicit SECANT loop with a single evaluated partitioned commit: predictor, reservoir, and tail storage now use one interface flux.
- Removed segment flow attenuation without a storage/source term and added the physical available-water cap `QIFACE <= QPHYS + max(Vold-Vmin,0)/DT`, including predictor-cache validation.
- Added strict commit/mass parsers and `assert_v24_conservation`; 8 Python tests and the reduced Fortran console build pass.
- Fresh `TMEND=44436.5`, `bht alpha=0` validation passed with 1129 evaluated commits, `max|RTAIL|=1.1642e-10`, and all other interface/segment mass gaps equal to zero.
- Relative to the same-window V23 RELAX result, SEG 2 bias improved by `0.128771 m`, head bias improved by `0.137818 m`, and SEG 222 bias increased by `0.009046 m`.
- Current conclusion: V24 is the first conservation-closed baseline for further tailreach optimization. Next work should diagnose the remaining upstream water-level bias before implementing true segmentwise continuity/momentum.
