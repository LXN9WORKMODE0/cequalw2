# Four-Stage Boundary Reconvergence

Updated: 2026-04-12

## Purpose

This note is the authoritative interpretation of the four-stage reduction boundary after the Stage 4 implementation work completed in the current tree.

It supersedes the earlier reading that treated Stage 4 as still pending.

## 1. Final Boundary

The final reduced deliverable keeps:

- `withdrawal.f90`
- `gate-spill-pipe.f90`
- structure-flow behavior
- structural withdrawal behavior
- selective-withdrawal temperature control

The final reduced deliverable removes:

- TDG control logic
- TDG source files
- TDG package inputs
- TDG output files from the supported baseline

## 2. Non-Negotiable Facts

### Fact 1: hydro + temperature core files remain required

- `az.f90`
- `shading.f90`
- `heat-exchange.f90`

These remain part of the hydro + temperature solver path and are not Stage 4 removal candidates.

### Fact 2: structure-flow support remains inside the supported boundary

- `gate-spill-pipe.f90` remains part of the supported reduced deliverable
- the current Bonneville baseline still depends on structure-flow behavior

### Fact 3: selective withdrawal remains inside the supported boundary

- `withdrawal.f90` remains part of the supported reduced deliverable
- `SELECTC = ON` and `SELECTC = USGS` remain supported

### Fact 4: TDG is now outside the supported boundary

The reduced deliverable no longer supports:

- `w2_systdg.npt`
- `w2_TDGtarget.csv`
- `TDGdyntarget.csv`
- `TDG_output.csv`
- `TDGTarget_output.csv`
- `TDGTarget_warning.opt`
- `%DO` / `TDG` output requests
- `GASSPC = ON` / `GASGTC = ON`

## 3. Stage Status

### Stage 1

Name:

- runtime water-quality shutdown

Status:

- completed

Meaning:

- the reduced build forces `CONSTITUENTS = .FALSE.`
- the reduced GUI and console main flows do not enter `wqconstituents`

### Stage 2

Name:

- source dependency isolation

Status:

- completed

Meaning:

- the reduced path no longer needs `water-quality.f90` entry points during initial output setup
- reduced-path placeholders are used for `REAER`, `KF`, and `CD`
- dormant optional reduced-path calls were isolated before file removal

### Stage 3

Name:

- build-chain and water-quality file removal

Status:

- completed

Meaning:

- the reduced build no longer compiles:
  - `wqconstituents.F90`
  - `water-quality.f90`
  - `gas-transfer.f90`
  - `ReduceReaerAlgae.f90`
  - `aerate.f90`
  - `Plunge_Point.f90`

### Stage 4

Name:

- contract narrowing and final deliverable definition

Status:

- completed

Meaning:

- the final boundary keeps structure flow and selective withdrawal
- the source tree no longer contains:
  - `systdg.f90`
  - `tdg.f90`
  - `TDGtarget.f90`
  - `tdg - Copy.f90`
- the reduced build scripts no longer depend on TDG source files
- supported cases and packaged cases no longer ship TDG files or TDG outputs
- `input.F90` now rejects TDG files and TDG output requests explicitly

## 4. Stage 4 Acceptance Result

The Stage 4 acceptance criteria are now met:

- the final reduced model boundary is explicit and documented
- supported cases use the intended no-TDG contract
- package contents, build scripts, and documentation match the final boundary
- a clean supported case still runs and produces the expected reduced outputs
- reintroduced TDG files are rejected early

## 5. What Remains Outside The Four Stages

The main remaining engineering risk is no longer Stage 4.

What remains is:

- broader historical-case compatibility outside the supported Bonneville baseline
- any future expansion beyond the current reduced deliverable boundary

## 6. Practical Summary

For the current tree, the correct reading is now:

- Stage 1 is done
- Stage 2 is done
- Stage 3 is done
- Stage 4 is done

The reduced deliverable boundary is now: structure flow plus selective withdrawal retained, TDG fully removed from the supported contract.
