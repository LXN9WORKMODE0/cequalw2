# W2 V2 Continuous Front Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative continuous-front layer on top of the verified V0+V1 foundation so the protected tailreach no longer exists only as a suppressed add-segment request, but as an explicit front state with hysteresis and minimum wetness protection.

**Architecture:** Keep the current W2 hydrodynamic solver intact and do not yet move the protected physical head into the active hydrodynamic span. Instead, introduce a front-buffer state machine for the locked main-branch head segment, track proxy wetness continuously, and use hysteresis to control when add/subtract intent is interpreted as front wetting or drying. This is a transitional solver layer, not the final full wetting/drying implementation.

**Tech Stack:** Intel Fortran reduced console build, Python smoke regression harness, CE-QUAL-W2 v4.55 source tree.

---

## File Map

- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Purpose: add front-state arrays/constants shared across init and runtime.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Purpose: allocate new front-state arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Purpose: initialize new front-state arrays and defaults.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
  Purpose: define protected front-buffer segment(s) from `IUPHYS/CUSMIN`.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`
  Purpose: update front-state machine, hysteresis counters, and proxy wetness; write V2 diagnostics; keep segment addition suppressed for the protected front buffer.
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Purpose: extend smoke regression to assert V2 markers and preserve V0/V1 pass conditions.
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\17_v2_continuous_front_implementation.md`
  Purpose: record actual V2 implementation and validation findings.

## Task 1: Add the failing V2 regression

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Write the failing V2 checks**

Add a new required marker list entry for a V2 front-state log line, for example:

```python
REQUIRED_MARKERS = [
    "[V0_BOUNDARY_INIT]",
    "[V0_BOUNDARY_SHIFT]",
    "[V0_SOURCE_PLACE]",
    "[V2_FRONT_STATE]",
]
```

Also add a V2-specific failure if the smoke case never logs a front-state line for the protected main branch.

- [ ] **Step 2: Run the smoke test against the current V0+V1 executable and verify RED**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: fail because `[V2_FRONT_STATE]` does not exist yet.

- [ ] **Step 3: Keep existing pass conditions**

Do not remove existing assertions for:

- missing V0 markers
- late `Add segments 2 through 2`
- `w2.err` / runtime error detection

- [ ] **Step 4: Re-run the Python syntax check**

Run:

```powershell
python -m py_compile C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py
```

Expected: no output.

## Task 2: Add front-state data structures

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`

- [ ] **Step 1: Add minimal front-state arrays**

Introduce shared arrays for one conservative front-buffer segment per branch:

```fortran
INTEGER, ALLOCATABLE, DIMENSION(:) :: FRONT_SEG, FRONT_STATE, FRONT_WET_COUNT, FRONT_DRY_COUNT
REAL(R8), ALLOCATABLE, DIMENSION(:) :: FRONT_WSE, FRONT_DEPTH
```

Also add integer state constants, for example:

```fortran
INTEGER, PARAMETER :: FRONT_STATE_DRY = 0, FRONT_STATE_WETTING = 1, FRONT_STATE_BUFFER_WET = 2
```

- [ ] **Step 2: Add conservative thresholds**

Add shared thresholds as parameters or module scalars:

```fortran
REAL(R8), PARAMETER :: FRONT_H_ON = 0.50D0
REAL(R8), PARAMETER :: FRONT_H_OFF = 0.10D0
REAL(R8), PARAMETER :: FRONT_H_MIN = 0.05D0
INTEGER, PARAMETER :: FRONT_WET_STEPS = 3
INTEGER, PARAMETER :: FRONT_DRY_STEPS = 6
```

- [ ] **Step 3: Allocate arrays**

Allocate the arrays in `input.F90` next to the existing V0/V1 branch-state arrays.

- [ ] **Step 4: Initialize arrays**

Initialize all front-state arrays in `init.F90`:

```fortran
FRONT_SEG = 0
FRONT_STATE = FRONT_STATE_DRY
FRONT_WET_COUNT = 0
FRONT_DRY_COUNT = 0
FRONT_WSE = 0.0D0
FRONT_DEPTH = 0.0D0
```

## Task 3: Define the protected front buffer

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`

- [ ] **Step 1: Define the front-buffer segment from V1 semantics**

For protected branches only, compute:

```fortran
IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. CUSMIN(JB) > IUPHYS(JB)) THEN
  FRONT_SEG(JB) = CUSMIN(JB) - 1
ELSE
  FRONT_SEG(JB) = 0
END IF
```

- [ ] **Step 2: Seed proxy front depth**

Initialize `FRONT_WSE` and `FRONT_DEPTH` conservatively to zero at startup. Do not yet try to modify active hydrodynamic geometry here.

- [ ] **Step 3: Add a one-time setup log**

Write a setup marker such as:

```fortran
[V2_FRONT_SETUP] JB=<...> FRONT_SEG=<...> IUPHYS=<...> CUSMIN=<...>
```

This is diagnostic only and must not replace the V0 markers.

## Task 4: Implement the V2 front-state machine

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`

- [ ] **Step 1: Compute proxy front wetness before segment-add execution**

For a protected branch with `FRONT_SEG(JB) > 0`, compute a proxy front water-surface elevation and depth from the current active upstream segment:

```fortran
FRONT_WSE(JB) = ELWS(CUS(JB))
FRONT_DEPTH(JB) = MAX(0.0D0, (FRONT_WSE(JB) - EL(KBI(FRONT_SEG(JB))+1, FRONT_SEG(JB))) / COSA(JB))
```

Clamp negative or pathological values to zero.

- [ ] **Step 2: Update hysteresis counters**

Use the candidate-add signal plus proxy depth to update counters:

```fortran
IF (IUCAND < IU .OR. FRONT_DEPTH(JB) >= FRONT_H_ON) THEN
  FRONT_WET_COUNT(JB) = FRONT_WET_COUNT(JB) + 1
  FRONT_DRY_COUNT(JB) = 0
ELSE IF (FRONT_DEPTH(JB) <= FRONT_H_OFF) THEN
  FRONT_DRY_COUNT(JB) = FRONT_DRY_COUNT(JB) + 1
  FRONT_WET_COUNT(JB) = 0
END IF
```

- [ ] **Step 3: Update the discrete front state**

Apply the state transitions:

```fortran
IF (FRONT_WET_COUNT(JB) >= FRONT_WET_STEPS) FRONT_STATE(JB) = FRONT_STATE_BUFFER_WET
IF (FRONT_STATE(JB) == FRONT_STATE_DRY .AND. FRONT_WET_COUNT(JB) > 0) FRONT_STATE(JB) = FRONT_STATE_WETTING
IF (FRONT_DRY_COUNT(JB) >= FRONT_DRY_STEPS) FRONT_STATE(JB) = FRONT_STATE_DRY
```

- [ ] **Step 4: Add V2 log lines**

Emit a stable line for the regression harness, for example:

```fortran
[V2_FRONT_STATE] JB=<...> SEG=<...> STATE=<...> DEPTH=<...> WET_COUNT=<...> DRY_COUNT=<...> IUCAND=<...> IU=<...>
```

Log on state change and also on protected add-candidate events so the smoke window always records at least one line.

- [ ] **Step 5: Keep actual segment addition suppressed in V2**

Do not change the current V1 protection that prevents `SEG 2` from being re-added into the active hydrodynamic span during the smoke window. V2 is still a conservative front-buffer representation, not full activation.

- [ ] **Step 6: Do not yet modify these areas**

Leave untouched in this slice:

- `w2_main.f90`
- `hydroinout.F90` source-placement logic
- `init-u-elws.f90`
- actual `ADD_LAYER/SUB_LAYER` numerical geometry rules beyond logging/state tracking

## Task 5: Build and validate

**Files:**
- Use the modified source files and smoke harness

- [ ] **Step 1: Build the reduced console executable**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 2: Run the short-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected:

- `[V2_FRONT_STATE]` exists
- no late `Add segments 2 through 2`
- no runtime error

- [ ] **Step 3: Run the extended smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected:

- same pass conditions
- at least one protected-front state log for `JB=1`

## Task 6: Document the outcome

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\17_v2_continuous_front_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record what V2 actually means**

Document that this slice adds:

- front state machine
- hysteresis
- proxy wetness
- minimum-wetness semantics in diagnostics

and explicitly document that it still does not make the physical tailreach segment fully active in the hydrodynamic solve.

- [ ] **Step 2: Record validation outputs**

Link the passing smoke summaries and describe:

- whether `SEG 2` late-add stayed suppressed
- whether `[V2_FRONT_STATE]` appeared
- whether any new numerical instability appeared

- [ ] **Step 3: Record the next boundary**

State clearly that the next meaningful slice after this is stronger solver participation for the front buffer or a more explicit continuous wetting geometry path, not another round of pure logging.
