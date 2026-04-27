# V19-V21 Implicit Interface Coupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current one-pass `V18` interface coupling with a more mature interface treatment: first make interface residuals explicit, then add strong interface iteration, then promote the interface update toward a low-dimensional implicit correction.

**Architecture:** Keep the current W2 reservoir solver and tailreach subdomain, but stop relying on many tiny time steps to resolve interface mismatch. Introduce explicit interface residual diagnostics, then same-step interface iteration with convergence criteria, and finally a reduced implicit/semi-implicit interface update around the coupled `(ETA_INT, Q_INT)` state.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Responsibility: expose interface-residual and interface-iteration diagnostics to smoke verification.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Responsibility: declare new interface residual, interface iterate, and convergence control fields.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Responsibility: initialize interface-iteration tolerances and limits.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Responsibility: zero new interface diagnostic and convergence arrays.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
  Responsibility: implement interface residual diagnostics, interface iteration, and reduced implicit interface update.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\35_v19_interface_residual_implementation.md`
  Responsibility: record the V19 result.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\36_v20_interface_iteration_implementation.md`
  Responsibility: record the V20 result.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\37_v21_reduced_implicit_interface_implementation.md`
  Responsibility: record the V21 result.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`
  Responsibility: index the new implementation notes.

## Task 1: V19 Interface Residual Diagnostics

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\35_v19_interface_residual_implementation.md`

- [ ] **Step 1: Add a failing smoke gate for interface residuals**

In `run_w2_v0_v1_smoke.py`, add:

```python
"[V19_INTERFACE_RESIDUAL]",
```

and summary fields:

```python
has_v19_interface_residual: bool
tail_iface_resid_max_eta: float
tail_iface_resid_max_q: float
```

The harness should fail if the marker is missing.

- [ ] **Step 2: Verify the gate fails before implementation**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL because `[V19_INTERFACE_RESIDUAL]` does not exist yet.

- [ ] **Step 3: Add interface residual state**

In `w2modules.F90`, add branch-level interface residual arrays:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_ETA_PRED, TAIL_IFACE_ETA_CORR
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_Q_PRED, TAIL_IFACE_Q_CORR
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_DETA, TAIL_IFACE_DQ
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_MAX_DETA, TAIL_IFACE_MAX_DQ
```

- [ ] **Step 4: Initialize and zero the new fields**

In `input.F90` and `init.F90`, allocate and zero all new residual arrays.

- [ ] **Step 5: Emit predictor/corrector interface residual diagnostics**

In `w2_main.f90`, after:

- predictor stage
- corrector stage

record:

```fortran
TAIL_IFACE_ETA_PRED(JB) = TAIL_WSE_DN(JB)
TAIL_IFACE_Q_PRED(JB)   = TAIL_Q_LINK(JB)
```

and after the corrector:

```fortran
TAIL_IFACE_ETA_CORR(JB) = TAIL_WSE_DN(JB)
TAIL_IFACE_Q_CORR(JB)   = TAIL_Q_LINK(JB)
TAIL_IFACE_DETA(JB)     = TAIL_IFACE_ETA_CORR(JB) - TAIL_IFACE_ETA_PRED(JB)
TAIL_IFACE_DQ(JB)       = TAIL_IFACE_Q_CORR(JB) - TAIL_IFACE_Q_PRED(JB)
TAIL_IFACE_MAX_DETA(JB) = MAX(TAIL_IFACE_MAX_DETA(JB), ABS(TAIL_IFACE_DETA(JB)))
TAIL_IFACE_MAX_DQ(JB)   = MAX(TAIL_IFACE_MAX_DQ(JB), ABS(TAIL_IFACE_DQ(JB)))
```

Write:

```fortran
[V19_INTERFACE_RESIDUAL] JB=... DETA=... DQ=... ETA_P=... ETA_C=... Q_P=... Q_C=...
```

- [ ] **Step 6: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 7: Run short, extended, and long smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44458
```

Expected:

- PASS on all three windows
- `has_v19_interface_residual = 1`
- residual maxima are measurable and nonzero

- [ ] **Step 8: Record V19**

Write `35_v19_interface_residual_implementation.md` with:

- what interface residuals are now exposed
- what the initial residual magnitudes look like
- whether they oscillate or decay

## Task 2: V20 Strong Interface Iteration

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\36_v20_interface_iteration_implementation.md`

- [ ] **Step 1: Add a failing smoke gate for interface iteration**

In `run_w2_v0_v1_smoke.py`, add:

```python
"[V20_INTERFACE_ITER]",
```

and summary fields:

```python
has_v20_interface_iter: bool
tail_iface_iter_max: int
tail_iface_iter_converged_count: int
```

The harness should fail if the marker is missing.

- [ ] **Step 2: Verify the gate fails before implementation**

Run the short-window smoke and confirm failure due to missing `V20` diagnostics.

- [ ] **Step 3: Add interface iteration controls**

In `w2modules.F90`, add:

```fortran
INTEGER,  ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_ITER_COUNT
LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_CONVERGED
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_RELAX
INTEGER,  PARAMETER :: TAIL_IFACE_MAX_ITERS = 4
REAL(R8), PARAMETER :: TAIL_IFACE_ETA_TOL = 0.01D0
REAL(R8), PARAMETER :: TAIL_IFACE_Q_TOL = 10.0D0
REAL(R8), PARAMETER :: TAIL_IFACE_RELAX_MIN = 0.20D0
REAL(R8), PARAMETER :: TAIL_IFACE_RELAX_MAX = 0.80D0
```

- [ ] **Step 4: Initialize all interface-iteration fields**

Allocate and zero them in `input.F90` and `init.F90`.

- [ ] **Step 5: Implement same-step interface iteration**

In `w2_main.f90`, replace the one-pass interface handoff with an inner loop:

```fortran
DO ITER=1,TAIL_IFACE_MAX_ITERS
  CALL RUN_TAIL_PREDICTOR()
  ! reservoir solve with current interface guess
  ! tail corrector/update
  ! compute residual
  IF (ABS(TAIL_IFACE_DETA(JB)) < TAIL_IFACE_ETA_TOL .AND. ABS(TAIL_IFACE_DQ(JB)) < TAIL_IFACE_Q_TOL) EXIT
  CALL UPDATE_INTERFACE_GUESS_AITKEN(...)
END DO
```

The first version can use under-relaxation, with optional Aitken update if the residual history is available.

- [ ] **Step 6: Emit iteration diagnostics**

Write:

```fortran
[V20_INTERFACE_ITER] JB=... ITER=... DETA=... DQ=... RELAX=... CONV=...
```

- [ ] **Step 7: Rebuild and rerun smoke**

Run build and all three smoke windows again.

Expected:

- PASS on all windows
- `has_v20_interface_iter = 1`
- `tail_iface_iter_max >= 1`
- at least some steps show convergence before max iterations

- [ ] **Step 8: Record V20**

Write `36_v20_interface_iteration_implementation.md` with:

- how many iterations are needed
- whether residuals decay
- whether runtime improves vs. V18

## Task 3: V21 Reduced Implicit Interface Update

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\37_v21_reduced_implicit_interface_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Add a failing smoke gate for the reduced implicit solve**

In `run_w2_v0_v1_smoke.py`, add:

```python
"[V21_INTERFACE_SOLVE]",
```

and summary fields:

```python
has_v21_interface_solve: bool
tail_iface_linear_updates: int
```

The harness should fail if the marker is missing.

- [ ] **Step 2: Verify the gate fails before implementation**

Run short-window smoke and confirm it fails because `V21` is missing.

- [ ] **Step 3: Add reduced interface linearization state**

In `w2modules.F90`, add fields to store:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_ETA_GUESS, TAIL_IFACE_Q_GUESS
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_ETA_PREV, TAIL_IFACE_Q_PREV
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_IFACE_DETA_STEP, TAIL_IFACE_DQ_STEP
```

- [ ] **Step 4: Implement a reduced implicit interface correction**

In `w2_main.f90`, after computing interface residuals, add a low-dimensional correction step:

```fortran
CALL UPDATE_INTERFACE_GUESS_REDUCED_IMPLICIT(JB, ...)
```

The first version can be a secant/quasi-Newton style correction on `(ETA_INT, Q_INT)`, using current and previous iterate information, rather than a full global matrix solve.

- [ ] **Step 5: Emit solve diagnostics**

Write:

```fortran
[V21_INTERFACE_SOLVE] JB=... ITER=... DETA_STEP=... DQ_STEP=... ETA=... Q=...
```

- [ ] **Step 6: Rebuild and rerun all smoke windows**

Expected:

- PASS on all windows
- `has_v21_interface_solve = 1`
- runtime should be materially better than current V18 baseline

- [ ] **Step 7: Record V21 and update the hydrodynamics index**

Write `37_v21_reduced_implicit_interface_implementation.md` and add the new note to:

```markdown
C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md
```

Document:

- how the reduced implicit update works
- whether runtime and stability improved
- what still remains before a fully mature interface solver

## Self-Review

- Spec coverage:
  - explicit interface residuals -> Task 1
  - strong interface iteration -> Task 2
  - reduced implicit interface update -> Task 3
- Placeholder scan:
  - No `TODO`/`TBD`
  - Every task includes files, required markers, verification commands, and expected outcomes
- Type consistency:
  - `TAIL_IFACE_*` naming is consistent across V19-V21
