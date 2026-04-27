# V13 Transition-State Reach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Internalize the river-transition-reservoir control state into the fixed tailreach so existing transition closures are driven by tailreach hydraulics rather than by the standalone front-state patch.

**Architecture:** Keep V12 discharge-state evolution intact, but add a continuous tail control state computed from tail stage, local slope, submergence, and Froude-like behavior. Then synchronize the legacy `FRONT_TRANSITION/DRAG/GRAV` closure inputs from this internal tailreach state instead of letting the front-state machine remain the primary physical driver.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `w2source_v455_2_11_2026/w2modules.F90`
  Responsibility: declare V13 transition-state variables and constants.
- `w2source_v455_2_11_2026/input.F90`
  Responsibility: allocate the V13 variables.
- `w2source_v455_2_11_2026/init.F90`
  Responsibility: initialize V13 state safely.
- `w2source_v455_2_11_2026/init-geom.F90`
  Responsibility: clear V13 state when the fixed tail domain is reset.
- `w2source_v455_2_11_2026/w2_main.f90`
  Responsibility: compute internal tail transition metrics and emit V13 diagnostics.
- `w2source_v455_2_11_2026/layeraddsub.F90`
  Responsibility: consume V13 tail transition state when synchronizing front-state geometry and closures.
- `analysis/run_w2_v0_v1_smoke.py`
  Responsibility: require a V13 diagnostic marker.
- `docs/reference/hydrodynamics_limitations/28_v13_transition_state_reach_implementation.md`
  Responsibility: record what V13 changed and whether it materially changed results.
- `docs/reference/hydrodynamics_limitations/README.md`
  Responsibility: index the new V13 note.

## Task 1: Make V13 Measurable First

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add the required marker**

Require:

```python
"[V13_TRANSITION_REACH]",
```

and add:

```python
has_v13_transition_reach: bool
```

- [ ] **Step 2: Run short-window smoke to confirm red**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL mentioning missing `[V13_TRANSITION_REACH]`.

## Task 2: Add Tailreach Transition-State Variables

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`

- [ ] **Step 1: Declare transition-state arrays**

Add:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_TRANSITION_STATE
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_SUBMERGENCE, TAIL_LOCAL_SLOPE, TAIL_FROUDE
INTEGER,  ALLOCATABLE, DIMENSION(:) :: TAIL_CONTROL_MODE
```

Use `TAIL_CONTROL_MODE` only as a reporting summary; keep the true control variable continuous.

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90`, initialize to zero in `init.F90`, and reset them in `init-geom.F90`.

- [ ] **Step 3: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

## Task 3: Compute Internal Tail Transition State

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Add a helper to compute tail transition metrics**

Add a helper such as:

```fortran
SUBROUTINE UPDATE_TAIL_TRANSITION_STATE(...)
```

that computes:
- `TAIL_LOCAL_SLOPE = max((WSE_UP - WSE_DN) / LENGTH, 0)`
- `TAIL_SUBMERGENCE` from downstream stage relative to upstream depth
- `TAIL_FROUDE` from `QSTATE`, area, depth, and gravity

- [ ] **Step 2: Blend those metrics into one continuous control state**

Construct:

```fortran
TAIL_TRANSITION_STATE(JB)
```

as a bounded `0..1` control where:
- values near `0` mean river control
- values near `1` mean reservoir/submerged control

Use a weighted combination of:
- low local slope relative to branch slope
- high submergence
- low Froude

- [ ] **Step 3: Derive a reporting mode from the continuous value**

Set:

```fortran
TAIL_CONTROL_MODE = 0/1/2
```

for:
- `0 = river`
- `1 = transition`
- `2 = reservoir`

but do **not** let this discrete mode replace the continuous state in closures.

- [ ] **Step 4: Emit a V13 diagnostic marker**

Write:

```fortran
[V13_TRANSITION_REACH] JB=... TRANS=... SUB=... SLOPE=... FR=... MODE=...
```

from the tail update path.

## Task 4: Make Front Closures Consume Internal Tail State

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`

- [ ] **Step 1: Synchronize front transition from tail state**

Where `TAIL_STAGE_VALID` already syncs front geometry, replace the old “derive transition from `FRONT_STATE`” behavior with:

```fortran
FRONT_TRANSITION(JB) = TAIL_TRANSITION_STATE(JB)
```

when the tailreach state is valid.

- [ ] **Step 2: Keep legacy `FRONT_STATE` as secondary**

Do **not** delete the current front-state machine yet. Instead:
- keep it for add/subtract semantics
- stop treating it as the primary physical source of `FRONT_TRANSITION`

- [ ] **Step 3: Preserve existing closure outputs**

Continue to compute:

```fortran
FRONT_DRAG_FACTOR
FRONT_GRAV_FACTOR
```

from `FRONT_TRANSITION`, but now `FRONT_TRANSITION` should come from the tailreach when available.

## Task 5: Verify V13 Stability First

**Files:**
- Test: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Run short-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected:
- PASS
- `has_v13_transition_reach = 1`

- [ ] **Step 2: Run extended smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: PASS.

- [ ] **Step 3: Run long-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44458
```

Expected:
- PASS
- no runaway
- both stations still valid

## Task 6: Document What V13 Did

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\28_v13_transition_state_reach_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record the implementation note**

Document:
- the new internal transition-state variables
- how V13 differs from the old `FRONT_STATE -> FRONT_TRANSITION` path
- whether V13 mainly changed architecture or also changed metrics

- [ ] **Step 2: Update the reading index**

Add the V13 note to the hydrodynamics limitations README.

## Self-Review

- Spec coverage: this plan covers the V13 blueprint requirement to move transition-state logic into the reach interior and demote the standalone front-state patch.
- Placeholder scan: all tasks name exact files, commands, and the specific logic shape.
- Type consistency: `TAIL_TRANSITION_STATE`, `TAIL_SUBMERGENCE`, `TAIL_LOCAL_SLOPE`, `TAIL_FROUDE`, and `TAIL_CONTROL_MODE` form one consistent family and feed `FRONT_TRANSITION` rather than replacing all front-state machinery at once.
