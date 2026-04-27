# V12 Reach State Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a true tail discharge state with time memory on the fixed tail domain so the tailreach is no longer just storage plus algebraic outflow.

**Architecture:** Keep the V11 fixed-tail-domain metadata and V10 storage/inflow/outflow architecture, but add an explicit discharge state that evolves toward a hydraulic target with a travel-time-based response. Use that state in storage continuity and coupling, and verify it with a dedicated V12 diagnostic marker.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `w2source_v455_2_11_2026/w2modules.F90`
  Responsibility: declare V12 tail discharge-state arrays and tuning constants.
- `w2source_v455_2_11_2026/input.F90`
  Responsibility: allocate the new V12 arrays.
- `w2source_v455_2_11_2026/init.F90`
  Responsibility: initialize the new V12 arrays safely.
- `w2source_v455_2_11_2026/init-geom.F90`
  Responsibility: zero/reset V12 state when the tail domain is initialized.
- `w2source_v455_2_11_2026/w2_main.f90`
  Responsibility: implement discharge-state evolution, compute response times from the fixed tail domain, and emit V12 diagnostics.
- `analysis/run_w2_v0_v1_smoke.py`
  Responsibility: require a V12 diagnostic marker in smoke verification.
- `docs/reference/hydrodynamics_limitations/27_v12_reach_state_evolution_implementation.md`
  Responsibility: record what V12 changed, what improved, and what remains for V13.
- `docs/reference/hydrodynamics_limitations/README.md`
  Responsibility: index the new V12 note.

## Task 1: Make V12 Measurable First

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add a required V12 marker**

Extend the smoke harness to require:

```python
"[V12_Q_STATE]",
```

Add:

```python
has_v12_q_state: bool
```

and fail if it is missing.

- [ ] **Step 2: Run short-window smoke to confirm red**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL mentioning missing `[V12_Q_STATE]`.

## Task 2: Add Explicit Tail Discharge-State Storage

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`

- [ ] **Step 1: Declare V12 state arrays**

Add arrays:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_Q_STATE, TAIL_Q_TARGET
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_TRAVEL_TIME, TAIL_WAVE_CELERITY, TAIL_REACH_LENGTH
LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_Q_STATE_INITIALIZED
```

Add constants such as:

```fortran
REAL(R8), PARAMETER :: TAIL_Q_STATE_RELAX_MIN = 0.05D0
REAL(R8), PARAMETER :: TAIL_Q_STATE_RELAX_MAX = 1.00D0
```

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90` and initialize in both `init.F90` and the V11 tail reset section in `init-geom.F90`.

- [ ] **Step 3: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

## Task 3: Implement Minimal Reach-State Evolution

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Compute fixed tail-domain length from explicit V11 metadata**

In the tail helper code, add a function or subroutine that computes:

```fortran
TAIL_REACH_LENGTH(JB) = SUM(DLX(TAIL_DOMAIN_US(JB):TAIL_DOMAIN_DS(JB)))
```

with safe guards when the domain is undefined.

- [ ] **Step 2: Compute a hydraulic target discharge**

Keep the existing hydraulic target logic, but store it separately as:

```fortran
TAIL_Q_TARGET(JB)
```

Do not let it immediately become the new discharge state.

- [ ] **Step 3: Advance a true discharge state with time memory**

Add a helper such as:

```fortran
SUBROUTINE ADVANCE_TAIL_Q_STATE(...)
```

that uses:
- current `TAIL_Q_STATE`
- current `TAIL_Q_TARGET`
- current domain length
- current upstream depth / area
- a simple wave-speed estimate like `sqrt(g * depth)`

to compute:

```fortran
TAIL_TRAVEL_TIME(JB)
TAIL_WAVE_CELERITY(JB)
TAIL_Q_STATE(JB)
```

The update should be first-order and bounded:

```fortran
alpha = min(max(DLT / tau, TAIL_Q_STATE_RELAX_MIN), TAIL_Q_STATE_RELAX_MAX)
Q_new = Q_old + alpha * (Q_target - Q_old)
```

- [ ] **Step 4: Use discharge state in continuity**

Update storage with the evolved state:

```fortran
TAIL_Q_OUTFLOW(JB) = TAIL_Q_STATE(JB)
TAIL_Q_LINK(JB)    = TAIL_Q_STATE(JB)
```

and then advance storage / stage as before.

- [ ] **Step 5: Emit a V12 diagnostic marker**

Write:

```fortran
[V12_Q_STATE] JB=... QSTATE=... QTARGET=... TAU=... CEL=... LENGTH=... ALPHA=...
```

from the tail-stage update block.

## Task 4: Preserve Existing Coupling Semantics

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Keep V10 coupling shape, only swap in the evolved state**

Do not redesign:
- fixed tail-domain semantics
- V11 output routing
- V9 head feedback shape

Only replace the “algebraic outflow” piece with the new discharge state.

- [ ] **Step 2: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

## Task 5: Verify V12 Stability First

**Files:**
- Test: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Run short smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected:
- PASS
- `has_v12_q_state = 1`
- `seg2_valid_count > 0`

- [ ] **Step 2: Run extended smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: PASS with no runtime errors.

- [ ] **Step 3: Run long-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44458
```

Expected:
- PASS
- no long-window runaway
- `SEG 2` and `SEG 222` still valid

## Task 6: Record V12 Behavior

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\27_v12_reach_state_evolution_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Document what V12 changed**

Record:
- the new discharge-state variables
- how V12 differs from V10 algebraic outflow
- whether metrics improved or only stability/physics interpretation improved

- [ ] **Step 2: Update the hydrodynamics index**

Add the V12 note to the reading order in the README.

## Self-Review

- Spec coverage: this plan covers the V12 requirements from the second-stage blueprint: explicit discharge state, time memory, use of the fixed tail domain, and dedicated diagnostics.
- Placeholder scan: all tasks include exact files, commands, and the intended code shape.
- Type consistency: the new V12 naming stays consistent around `TAIL_Q_STATE`, `TAIL_Q_TARGET`, `TAIL_TRAVEL_TIME`, `TAIL_WAVE_CELERITY`, and `TAIL_REACH_LENGTH`.
