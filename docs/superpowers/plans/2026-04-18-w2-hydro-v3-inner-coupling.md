# W2 V3 Inner Coupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative inner-coupling scaffold so each hydrodynamic timestep can perform a second source/surface/velocity pass, with explicit V3 diagnostics, while preserving the verified V0/V1/V2 behavior.

**Architecture:** Keep the current W2 timestep structure and autostep recovery path intact. Instead of a full nonlinear refactor, wrap the existing hydrodynamic solve in a small Picard-style inner loop: rerun `HYDROINOUT`, recompute free-surface and velocity fields, and log pass-to-pass deltas. The first V3 slice uses a fixed two-pass scaffold with convergence diagnostics rather than a fully configurable iterative solver.

**Tech Stack:** Intel Fortran reduced console build, Python smoke regression harness, CE-QUAL-W2 v4.55 source tree.

---

## File Map

- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
  Purpose: add the conservative inner-coupling scaffold, local iteration arrays, and V3 diagnostics.
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Purpose: require V3-specific coupling diagnostics in the smoke harness while preserving all previous checks.
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\18_v3_inner_coupling_implementation.md`
  Purpose: record what V3 actually changed and what it still does not solve.

## Task 1: Add the failing V3 regression

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add V3 marker requirements**

Extend the required marker list with one V3 marker that proves the inner-coupling pass executed, for example:

```python
REQUIRED_MARKERS = [
    "[V0_BOUNDARY_INIT]",
    "[V0_BOUNDARY_SHIFT]",
    "[V0_SOURCE_PLACE]",
    "[V0_SEGMENT_ADD_CHECK]",
    "[V2_FRONT_STATE]",
    "[V3_INNER_ITER]",
]
```

- [ ] **Step 2: Run the current V2 executable and verify RED**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: fail because `[V3_INNER_ITER]` does not exist yet.

- [ ] **Step 3: Preserve all prior smoke gates**

Do not remove these checks:

- missing V0/V2 markers
- `Add segments 2 through 2`
- runtime error / `w2.err`
- required outputs

## Task 2: Add conservative V3 inner-coupling state in `w2_main`

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Add local V3 iteration variables**

Add local variables near the top of `PROGRAM W2_MAIN`:

```fortran
INTEGER :: HYDRO_ITER, HYDRO_ITER_MAX
REAL(R8) :: HYDRO_MAX_DZ, HYDRO_MAX_DQ
REAL(R8), ALLOCATABLE :: ELWS_INNER_PREV(:), QC_INNER_PREV(:)
```

Use a conservative fixed maximum:

```fortran
HYDRO_ITER_MAX = 2
```

- [ ] **Step 2: Allocate the local arrays once**

Allocate the arrays after initialization is complete and before the timestep loop starts:

```fortran
ALLOCATE(ELWS_INNER_PREV(IMX), QC_INNER_PREV(IMX))
ELWS_INNER_PREV = 0.0D0
QC_INNER_PREV = 0.0D0
```

## Task 3: Wrap the hydrodynamic solve in a small inner loop

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Insert an inner-iteration entry label just before the hydrodynamic solve**

Place a label between the selective-withdrawal calls and the hydrodynamic section so the existing source update and Tasks 2.2.1-2.2.5 can be rerun cleanly:

```fortran
HYDRO_ITER = 1
211 CONTINUE
CALL HYDROINOUT
```

Keep label `210` and label `220` intact so the current timestep restart path still works.

- [ ] **Step 2: Snapshot the previous pass at the end of pass 1**

After Task 2.2.5 and before autostepping, add:

```fortran
IF (HYDRO_ITER == 1) THEN
  ELWS_INNER_PREV = ELWS
  QC_INNER_PREV = QC
  HYDRO_ITER = HYDRO_ITER + 1
  WARNING_OPEN = .TRUE.
  WRITE(WRN,'(A,1X,A,I0)') '[V3_INNER_ITER]', 'PASS=',1
  GO TO 211
END IF
```

- [ ] **Step 3: Compute pass-to-pass deltas on pass 2**

Still before autostepping, add:

```fortran
HYDRO_MAX_DZ = MAXVAL(ABS(ELWS(CUS(BS(1)):DS(BE(NWB))) - ELWS_INNER_PREV(CUS(BS(1)):DS(BE(NWB)))))
HYDRO_MAX_DQ = MAXVAL(ABS(QC(CUS(BS(1)):DS(BE(NWB))) - QC_INNER_PREV(CUS(BS(1)):DS(BE(NWB)))))
WARNING_OPEN = .TRUE.
WRITE(WRN,'(A,1X,A,I0,1X,A,F0.4,1X,A,F0.4)') '[V3_INNER_ITER]', 'PASS=',HYDRO_ITER, 'MAX_DZ=',HYDRO_MAX_DZ, 'MAX_DQ=',HYDRO_MAX_DQ
```

Use exact branch-wide slices only if they are safe in this source layout; otherwise compute the max across nested `JW/JB/I` loops.

- [ ] **Step 4: Do not add new solver decisions yet**

For this first V3 slice:

- do not add dynamic stopping based on tolerance
- do not change autostep decisions
- do not move `temperature` or later modules inside the inner loop

The goal is a conservative second hydrodynamic pass with diagnostics, not a complete nonlinear control framework.

## Task 4: Build and validate

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
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected:

- `[V3_INNER_ITER]` exists
- prior V0/V1/V2 checks still pass

- [ ] **Step 3: Run the extended smoke**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected:

- same pass conditions
- at least two `V3_INNER_ITER` lines across the hydrodynamic solve

## Task 5: Document the outcome

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\18_v3_inner_coupling_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record what V3 actually changed**

Document that this slice adds:

- a second hydrodynamic pass inside the timestep
- repeated `HYDROINOUT`
- repeated free-surface and velocity solve
- coupling diagnostics (`MAX_DZ`, `MAX_DQ`)

- [ ] **Step 2: Record what V3 still does not do**

Explicitly state that it still does not:

- iterate structures to convergence
- perform fully tolerance-driven stopping
- turn the front buffer into a fully active hydrodynamic cell

- [ ] **Step 3: Record the next likely slice**

State clearly that the next step after this is stronger feedback between front-buffer state and the inner-coupled solve, or a larger V4/V5 geometry/physics upgrade, not another round of diagnostics alone.
