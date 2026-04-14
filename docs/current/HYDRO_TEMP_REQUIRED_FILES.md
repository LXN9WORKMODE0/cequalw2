# Hydro + Temperature Required Files

Updated: 2026-04-11

This note records the current file-level understanding for the reduced CE-QUAL-W2 v4.5.5 workspace.

Its purpose is to prevent accidental deletion of files that are still required for hydrodynamics + meteorology + temperature.

## 1. Important Correction

The earlier idea that `shading.f90` could be removed together with water-quality files was incorrect.

At the current code state:

- `w2_main.f90` and `w2_4_win.f90` call `CALCULATE_AZ`, which is defined in `az.f90`
- `temperature.F90` calls `SHADING`
- `temperature.F90` also calls `SURFACE_TERMS` and `EQUILIBRIUM_TEMPERATURE`
- `SURFACE_TERMS` and `EQUILIBRIUM_TEMPERATURE` are `ENTRY` points in `heat-exchange.f90`

Therefore:

- `az.f90` is part of the core hydro/turbulence path
- `shading.f90` is part of the temperature / solar-radiation path
- `heat-exchange.f90` is part of the temperature / surface heat-budget path

These files are not water-quality-only files.

## 2. Two Different Scopes

There are two different questions that must not be mixed together:

1. what is required for the bare hydro + temperature engine
2. what is required to keep the current supported Bonneville baseline runnable

Some files are core to both.
Some files are not part of the bare hydro-temp kernel, but are still required by the current supported case family.

## 3. Core Files That Must Be Kept For Hydro + Temperature

These files are part of the current hydro + meteorology + temperature execution path and should not be treated as deletion candidates.

### Program entry and shared declarations

- `w2_main.f90`
- `w2_4_win.f90`
- `w2modules.F90`
- `preprocessor_definitions.fpp`

### Input, setup, geometry, time-varying forcing

- `input.F90`
- `waterbody.f90`
- `init.F90`
- `init-geom.F90`
- `init-cond.F90`
- `init-u-elws.f90`
- `time-varying-data.f90`
- `MetFileRegion.f90`

### Core hydro / temperature solver path

- `hydroinout.F90`
- `transport.f90`
- `density.f90`
- `az.f90`
- `temperature.F90`
- `heat-exchange.f90`
- `shading.f90`
- `layeraddsub.F90`
- `balances.F90`
- `update.F90`

### Runtime support, restart, output, termination

- `output.f90`
- `outputinitw2tools.F90`
- `outputa2w2tools.F90`
- `restart.f90`
- `date.f90`
- `endsimulation.F90`

## 4. Why These Files Are Core

Representative code-level evidence:

- `w2_main.f90` / `w2_4_win.f90`
  - call `INPUT`
  - call `INIT`
  - call `INTERPOLATE_INPUTS`
  - call `HYDROINOUT`
  - call `CALCULATE_AZ`
  - call `temperature`
  - call `LAYERADDSUB`
  - call `BALANCES`
  - call `UPDATE`
  - call `OUTPUTA`
  - call `ENDSIMULATION`

- `input.F90`
  - calls `WATERBODY`

- `init.F90`
  - calls `INITGEOM`
  - calls `INTERPOLATION_MULTIPLIERS`
  - calls `INITCOND`
  - calls `TIME_VARYING_DATA`
  - calls `READ_INPUT_DATA`
  - calls `GREGORIAN_DATE`

- `transport.f90`
  - provides `INTERPOLATION_MULTIPLIERS`
  - provides `HORIZONTAL_MULTIPLIERS*`
  - provides `VERTICAL_MULTIPLIERS*`
  - provides `TRIDIAG`

- `az.f90`
  - defines `CALCULATE_AZ`
  - defines turbulence / eddy-viscosity calculations

- `temperature.F90`
  - calls `SHADING`
  - calls `SURFACE_TERMS`
  - calls `EQUILIBRIUM_TEMPERATURE`

- `heat-exchange.f90`
  - contains the heat-budget routine and the `ENTRY` points used by `temperature.F90`

- `density.f90`
  - provides `DENSITY`
  - density is used in the hydro solver and in `hydroinout.F90`

## 5. Files Required By The Current Bonneville Baseline But Not Necessarily By A Future Bare Hydro-Temp Kernel

These files are not the first place to delete, because the current supported case still depends on them.

- `withdrawal.f90`
- `gate-spill-pipe.f90`
- `systdg.f90`
- `tdg.f90`
- `TDGtarget.f90`

Reason:

- the packaged Bonneville baseline still uses gates / spill structures
- the packaged control file still shows gate-gas / TDG-related behavior
- `hydroinout.F90` calls structure-flow and TDG-related routines

This means:

- these files are not in the same category as `water-quality.f90`
- they may become removable later only if the supported case contract is changed accordingly

## 6. Current Case Facts That Matter

From `packaging\cases\minimal_case_inputs\w2_con.csv`:

- `NGT = 20`
- `SELECTC = OFF`
- `AERATEC = OFF`
- the file list includes `BON_SHD_1.npt`
- the file comments mention gate gas / `SYSTDG`

Interpretation:

- selective withdrawal is not currently active in the packaged clean-input case
- aeration is not currently active in the packaged clean-input case
- shading input is still part of the supported case
- gate / spill / TDG logic is still part of the supported case family

## 7. Clear Water-Quality-Only Candidates For A Later Removal Pass

These are the files that most clearly belong to the water-quality side rather than the core hydro + temperature side:

- `water-quality.f90`
- `wqconstituents.F90`
- `gas-transfer.f90`
- `ReduceReaerAlgae.f90`

However, even these should only be removed after:

1. runtime water-quality paths are fully severed
2. no remaining caller or module dependency points to them
3. the supported case contract no longer relies on any attached water-quality compatibility behavior

## 8. Conditional / Non-Core Files

These are not part of the always-on core path for the current packaged baseline, but they are still compiled in the current build scripts:

- `aerate.f90`
  - only used when `AERATEC == ON`

- `Plunge_Point.f90`
  - current call site is commented out

They are not the same as the core hydro-temp files listed above.
They can be evaluated separately after the core boundary is kept intact.

## 9. Practical Rule For Future Reduction Work

Before deleting any file, classify it into one of these buckets:

1. core hydro-temp solver file
2. current-case support file
3. conditional feature file
4. water-quality-only file

Do not delete files from bucket 1.
Do not delete files from bucket 2 until the supported case contract changes.
Only bucket 4 should be considered early removal candidates.
