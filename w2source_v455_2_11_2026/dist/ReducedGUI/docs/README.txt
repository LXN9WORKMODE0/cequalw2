ReducedGUI Package

Contents
- app\w2_v455_reduced_gui.exe
- cases\minimal_case_inputs\
- cases\minimal_case_verified\
- docs\PREREQUISITES.txt
- docs\SUPPORTED_CASES.txt

How to run
1. Extract the zip to a writable local directory.
2. Open app\w2_v455_reduced_gui.exe.
3. For a clean first run, set the model run directory to cases\minimal_case_inputs.
4. Use cases\minimal_case_verified as a reference snapshot of a successful reduced baseline run.
5. Click Run.

Current package intent
- This package keeps the original CE-QUAL-W2 GUI entry path.
- The reduced build keeps the original WinMain/Dialog/CE_QUAL_W2 structure.
- The package includes both a clean-input case and a verified-output reference case.
- The reduced deliverable keeps structure flow and selective withdrawal support.
- TDG is not part of the packaged reduced deliverable.

Output behavior
- Runtime logs and generated outputs are written into the selected case directory.
- Supported reduced runs generate hydro/temperature/structure-flow outputs only.
- TDG-only outputs are not part of the supported package baseline.
- If the model stops with an input/runtime problem, inspect w2.err in the case directory first.

Unsupported case artifacts
- Do not place `w2_systdg.npt` in the run directory.
- Do not place `w2_TDGtarget.csv` in the run directory.
- Do not place `TDGdyntarget.csv` in the run directory.
- Do not request `%DO` or `TDG` outputs in `w2_con.csv`.
- Do not enable `GASSPC` or `GASGTC` in `w2_con.csv`.

Notes
- `minimal_case_inputs` is the supported clean-start case for demonstration and rerun.
- `minimal_case_verified` retains representative outputs generated during baseline verification.
- `绀轰緥鏂囦欢` is not part of the supported package baseline.
