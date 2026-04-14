# Reduced Model Baseline

Updated: 2026-04-12

This document defines the current reduced baseline for CE-QUAL-W2 v4.5.5 in this workspace.

## 1. Source Of Truth

Canonical source tree:

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026`

Archived historical debug trees:

- `C:\Users\NING\Desktop\v455\_workspace_archive\historical_debug\temp_compile`
- `C:\Users\NING\Desktop\v455\_workspace_archive\historical_debug\temp_w2_build`

## 2. Supported Case Policy

Supported runtime baseline:

- `temp_case_work`
- `绀轰緥鏂囦欢2`
- `packaging\cases\minimal_case_inputs`
- `packaging\cases\minimal_case_verified`

Unsupported legacy case:

- `_workspace_archive\unsupported_cases\绀轰緥鏂囦欢`

## 3. Final Deliverable Boundary

The current reduced baseline keeps:

- hydrodynamics
- temperature
- gate / spill / pipe structure-flow logic
- structural withdrawal logic
- selective-withdrawal temperature control

The current reduced baseline removes:

- live water-quality runtime behavior
- dormant stage-3 water-quality source files
- TDG source files and TDG package support

## 4. Current Build Targets

Console executable:

- `build_console\w2_v455_console.exe`

GUI executable:

- `build_gui\w2_v455_reduced_gui.exe`

Package:

- `dist\ReducedGUI.zip`

## 5. Packaged Cases

### `minimal_case_inputs`

Purpose:

- clean-input baseline intended for a fresh run

Source:

- derived from `绀轰緥鏂囦欢2`
- cleaned so the supported baseline no longer ships TDG control files

Verified behavior:

- a clean clone starts and produces runtime outputs
- no TDG-only outputs are generated in the reduced baseline
- the packaged `w2_con.csv` now uses the slim reduced contract and no longer ships the removed WQ/TDG input block

### `minimal_case_verified`

Purpose:

- verification snapshot containing representative outputs from a successful baseline run

Source:

- derived from `temp_case_work`

Verified behavior:

- contains representative runtime outputs from a successful no-TDG reduced run

## 6. Current Compatibility Strategy

The current parser strategy is:

1. accept the slim reduced CSV contract used by the packaged baseline
2. fall back to the older Bonneville-shaped full CSV layout for legacy compatibility
3. consume retained structure / withdrawal sections needed by the supported baseline
4. reject TDG files and TDG output requests explicitly instead of silently tolerating them

This baseline is now sufficient for the supported Bonneville case family.

## 7. Practical Contract Rules

Supported:

- slim `w2_con.csv` cases that stop after retained output controls and continue at `FILE NAMES`
- legacy full-shape `w2_con.csv` cases that still carry the old WQ block
- structure-flow sections required by the Bonneville baseline
- `SELECTC = ON` and `SELECTC = USGS`

Removed from the slim packaged input contract:

- constituent control and naming blocks
- WQ kinetics / algae / zooplankton / macrophyte / BOD / gas chemistry blocks
- constituent and derived-constituent output request blocks
- gate gas rows (`GASGTC / EQGT / AGASGT / BGASGT / CGASGT`)
- WQ-only `FILE NAMES` rows:
  - `ATMDEPFN`
  - `CINFN`
  - `CDTFN`
  - `CPRFN`
  - `CUHFN`
  - `CDHFN`

Not supported:

- `w2_systdg.npt`
- `w2_TDGtarget.csv`
- `TDGdyntarget.csv`
- `%DO` / `TDG` output requests
- `GASSPC = ON` / `GASGTC = ON`

If any of those TDG artifacts are present, the reduced executable now stops early with a TDG-not-supported message.

## 8. What Is Out Of Scope

Not part of the current baseline:

- broader historical-case compatibility
- the archived `绀轰緥鏂囦欢` legacy case
- a re-versioned or more aggressively redesigned reduced CSV schema beyond the current slim contract
- GUI redesign

## 9. Practical Meaning

The baseline is no longer just "it compiles."

It now means:

- the console build succeeds
- the GUI shell build succeeds
- the package builds
- the clean packaged case runs from the slim reduced `w2_con.csv` without TDG artifacts
- the verified packaged case captures a successful no-TDG reduced run snapshot
