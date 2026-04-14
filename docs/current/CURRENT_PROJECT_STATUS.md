# CE-QUAL-W2 v4.5.5 Current Project Status

Updated: 2026-04-12

This file is the authoritative status summary for the workspace at `C:\Users\NING\Desktop\v455`.
If it conflicts with older notes, build logs, or architecture writeups, trust this file first.

## 1. Project Goal

The project remains in a reduction-and-rebuild phase:

- understand the original CE-QUAL-W2 v4.5.5 structure
- keep a reduced Windows build using Intel `ifx`
- preserve runnable hydrodynamics + temperature behavior while trimming optional model pieces

The final reduced deliverable boundary is now:

- keep structure-flow support (`gate-spill-pipe.f90`)
- keep structural withdrawal and selective-withdrawal temperature control (`withdrawal.f90`)
- remove TDG support from the source tree, package, and supported case contract

Broader historical-case compatibility is still intentionally out of scope.

## 2. Source Of Truth

The source of truth is:

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026`

This tree now contains:

- the promoted `GTNAME` fix in `hydroinout.F90`
- `SED_DIAG` compatibility restored in `input.F90`
- a stage-1 runtime rule that forces water quality off in the reduced build
- a stage-2 reduced-path placeholder initialization in `temperature.F90`
- reduced-path aeration compatibility guards in `w2_4_win.f90`, `w2_main.f90`, and `endsimulation.F90`
- a stage-3 source-tree removal of:
  - `water-quality.f90`
  - `wqconstituents.F90`
  - `gas-transfer.f90`
  - `ReduceReaerAlgae.f90`
  - `aerate.f90`
  - `Plunge_Point.f90`
- a stage-4 source-tree removal of:
  - `systdg.f90`
  - `tdg.f90`
  - `TDGtarget.f90`
  - `tdg - Copy.f90`
- reduced build scripts that no longer compile the removed stage-3 or stage-4 files
- a stage-4 input-contract rule that rejects:
  - `w2_systdg.npt`
  - `w2_TDGtarget.csv`
  - `TDGdyntarget.csv`
  - `%DO` / `TDG` output requests in `w2_con.csv`
  - `GASSPC = ON` / `GASGTC = ON` in `w2_con.csv`
- a compatibility-first CSV slimming pass in `input.F90` and `packaging\cases\minimal_case_inputs\w2_con.csv` that:
  - accepts a new slim reduced CSV contract
  - keeps legacy full-shape CSV fallback
  - removes WQ-only `FILE NAMES` rows tied to already removed code from the packaged baseline
- the current console and GUI build scripts
- the current packaged case assets

Historical debug material is archived at:

- `C:\Users\NING\Desktop\v455\_workspace_archive\historical_debug\temp_compile`
- `C:\Users\NING\Desktop\v455\_workspace_archive\historical_debug\temp_w2_build`
- `C:\Users\NING\Desktop\v455\_workspace_archive\historical_debug\VS鎵嬪姩缂栬瘧log`

## 3. Supported Case Boundary

Current supported Bonneville/ReducedGUI baseline:

- `C:\Users\NING\Desktop\v455\temp_case_work`
- `C:\Users\NING\Desktop\v455\绀轰緥鏂囦欢2`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\packaging\cases\minimal_case_inputs`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\packaging\cases\minimal_case_verified`

Current unsupported legacy case:

- `C:\Users\NING\Desktop\v455\_workspace_archive\unsupported_cases\绀轰緥鏂囦欢`

That unsupported case should be treated as a separate future compatibility project.

## 4. Final Reduced Contract

Supported:

- gate / spill / pipe structure-flow behavior
- structural withdrawal behavior
- `SELECTC = ON` and `SELECTC = USGS` selective-withdrawal temperature control
- the slim reduced `w2_con.csv` packaged baseline
- the existing Bonneville-shaped full CSV layout, as long as the reduced contract below is respected

Not supported:

- `w2_systdg.npt`
- `w2_TDGtarget.csv`
- `TDGdyntarget.csv`
- `TDG_output.csv`
- `TDGTarget_output.csv`
- `TDGTarget_warning.opt`
- `%DO` or `TDG` output requests in `w2_con.csv`
- `GASSPC = ON` or `GASGTC = ON` in `w2_con.csv`
- any case that still relies on TDG control behavior

Behavioral rule:

- if a case directory still contains TDG files or TDG output requests, the reduced executable now stops early with a clear TDG-not-supported message

## 5. What Is Verified

### 5.1 Build baseline

Verified build outputs:

- `build_console\w2_v455_console.exe`
- `build_gui\w2_v455_reduced_gui.exe`

Verified package output:

- `dist\ReducedGUI.zip`

The package contains:

- `app\w2_v455_reduced_gui.exe`
- `cases\minimal_case_inputs\`
- `cases\minimal_case_verified\`
- `docs\README.txt`
- `docs\PREREQUISITES.txt`
- `docs\SUPPORTED_CASES.txt`

### 5.2 GUI baseline

Verified facts:

- the reduced GUI executable launches successfully
- the original `WinMain/W2_DIALOG/CE_QUAL_W2` shell remains intact

### 5.3 Parser and runtime baseline

Verified facts:

- the canonical `INPUT` accepts the `SED_DIAG` field again
- the reduced build forces `CONSTITUENTS = .FALSE.` at runtime
- the reduced GUI/console main flows no longer contain a live `wqconstituents` runtime call
- the reduced path no longer needs `temperature.F90` to call water-quality `ENTRY` points during initial output setup
- the reduced path initializes deterministic placeholders before initial output:
  - `REAER = 0`
  - `KF = 0`
  - `CD = -99`
- `AERATEC = ON` is accepted by the parser but ignored in the reduced path
- the reduced GUI/console builds now succeed without compiling the removed stage-3 and stage-4 files
- the supported slim reduced baseline now passes `INPUT` without the legacy WQ block
- the legacy Bonneville-shaped full CSV baseline still passes `INPUT`
- a clean clone of `packaging\cases\minimal_case_inputs` runs successfully with no TDG files present
- representative reduced outputs such as `flowbal.csv`, `BON_spr.csv`, `BON_snp.opt`, and `Bonneville.w2l` are produced
- TDG-only outputs are no longer generated in the supported reduced baseline

### 5.4 Contract enforcement baseline

Verified facts:

- if `w2_systdg.npt` is added back into an otherwise supported case, the executable stops early with a TDG-not-supported message
- supported clean cases no longer ship TDG control files or TDG output snapshots
- representative TSR outputs still retain a stable `ReaerationCoeff(day-1)` value of `0.000` in the reduced path

Conclusion:

- the supported reduced boundary is now implemented both in source code and in shipped case assets

## 6. What Is Not Supported

The current deliverable does not promise compatibility for every historical case shape.

In particular:

- `绀轰緥鏂囦欢` is not part of the current support boundary
- older archived `temp_compile` cases are historical references, not current package acceptance criteria
- TDG-enabled Bonneville variants are no longer inside the reduced deliverable boundary

## 7. Current Engineering Interpretation

The project has now resolved:

- source-tree choice
- console build path
- GUI build path
- package assembly
- stage-1 runtime water-quality shutdown
- stage-2 reduced-path source dependency isolation for initial output setup
- stage-3 removal of dormant water-quality runtime source files from the reduced build
- stage-4 boundary decision to keep structure flow and selective withdrawal while removing TDG support
- stage-4 source-tree TDG file removal
- stage-4 package and supported-case contract narrowing
- compatibility-first input-contract realignment between `input.F90` and the packaged slim `w2_con.csv`
- Bonneville baseline case validation
- root workspace cleanup and archive layout

The main remaining risk is now:

- broader historical-case compatibility outside the supported Bonneville baseline

## 8. Related Documents

Use these next:

1. `CURRENT_PROJECT_STATUS.md`
2. `REDUCED_MODEL_BASELINE.md`
3. `RECENT_WORK_LOG.md`
4. `FOUR_STAGE_BOUNDARY_RECONVERGED.md`
5. `HYDRO_TEMP_REQUIRED_FILES.md`
6. `ORIGINAL_SOURCE_DELETE_PRIORITY.md`
7. `../reference/CEQUALW2_Architecture_Brief.md`
8. `../reference/CEQUALW2_Architecture_Full.md`
9. `../../_workspace_archive/historical_debug/temp_compile/debug_status.md`

## 9. One-Sentence Summary

The canonical source tree now builds, packages, and runs the supported ReducedGUI baseline with a slim reduced `w2_con.csv`, legacy full-shape CSV fallback, preserved structure flow/selective withdrawal support, and explicit TDG rejection.
