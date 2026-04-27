# V14 Stronger Coupled Hybrid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade tailreach/reservoir interaction from a weak post-step sidecar into a same-step predictor/corrector hybrid with rollback-safe tail state.

**Architecture:** Keep the current V13 tailreach physics intact, but add orchestration around them: save committed tail state at timestep entry, run a tail predictor before the main W2 hydrodynamic solve, use the predicted tail stage/discharge during the reservoir solve, then run a post-solve tail corrector to commit the updated state. If autostepping rejects the timestep, restore the saved tail state before retrying.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `w2source_v455_2_11_2026/w2_main.f90`
  Responsibility: implement V14 predictor/corrector orchestration, tail-state save/restore, and diagnostics.
- `analysis/run_w2_v0_v1_smoke.py`
  Responsibility: require the V14 diagnostic marker.
- `docs/reference/hydrodynamics_limitations/29_v14_stronger_coupled_hybrid_implementation.md`
  Responsibility: record what V14 changed and how it affected coupling behavior.
- `docs/reference/hydrodynamics_limitations/README.md`
  Responsibility: index the new V14 note.

## Task 1: Make V14 Measurable First

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add required marker**

Require:

```python
"[V14_COUPLED_HYBRID]",
```

and add:

```python
has_v14_coupled_hybrid: bool
```

- [ ] **Step 2: Run short-window smoke to confirm red**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL mentioning missing `[V14_COUPLED_HYBRID]`.

## Task 2: Add Tail-State Save/Restore

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Add local backup arrays**

Add local allocatables for the dynamic tail state that can change within a timestep, including:
- `TAIL_WSE_UP/DN`
- `TAIL_Q_LINK`
- `TAIL_DEPTH_UP`
- `TAIL_STORAGE_VOL`
- `TAIL_Q_INFLOW/OUTFLOW`
- `TAIL_Q_STATE`
- `TAIL_Q_TARGET`
- `TAIL_TRAVEL_TIME`
- `TAIL_WAVE_CELERITY`
- `TAIL_REACH_LENGTH`
- `TAIL_TRANSITION_STATE`
- `TAIL_SUBMERGENCE`
- `TAIL_LOCAL_SLOPE`
- `TAIL_FROUDE`
- `TAIL_STAGE_MODE`
- `TAIL_CONTROL_MODE`
- `TAIL_STAGE_VALID`
- `TAIL_REACH_INITIALIZED`
- `TAIL_Q_STATE_INITIALIZED`

- [ ] **Step 2: Allocate backup arrays**

Allocate them next to the existing local allocatables near `QIN_INNER_PREV`.

- [ ] **Step 3: Add helper routines**

Add:

```fortran
SUBROUTINE SAVE_TAIL_DYNAMIC_STATE()
SUBROUTINE RESTORE_TAIL_DYNAMIC_STATE()
```

## Task 3: Add a Pre-Solve Tail Predictor

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Save committed tail state at timestep entry**

At label `210`, after `CALL HYDROINOUT` and before Task 2.2 hydrodynamics, call:

```fortran
CALL SAVE_TAIL_DYNAMIC_STATE()
```

- [ ] **Step 2: Add predictor-facing temporary arrays**

Add small local arrays for the boundary-facing predicted tail values:
- `TAIL_WSE_UP_PRED`
- `TAIL_Q_LINK_PRED`
- `TAIL_DEPTH_UP_PRED`
- `TAIL_STAGE_VALID_PRED`

- [ ] **Step 3: Run a predictor loop**

Before Task 2.2 hydrodynamics, loop through coupled branches, call the existing `UPDATE_TAIL_STAGE`, capture the predicted boundary-facing values, restore the committed state, then reapply only the predictor-facing values.

The goal is:
- main W2 sees predicted `TAIL_WSE_UP`
- main W2 sees predicted `TAIL_Q_LINK`
- committed tail storage/Q-state are not advanced yet

- [ ] **Step 4: Emit predictor diagnostics**

Write:

```fortran
[V14_COUPLED_HYBRID] JB=... PASS=1 COMMIT=F QLINK=... WSE_UP=...
```

## Task 4: Add a Post-Solve Corrector

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Replace the single tail update with a corrector call**

After the main hydrodynamic solve, keep the current `UPDATE_TAIL_STAGE` call, but now treat it explicitly as the corrector/commit pass.

- [ ] **Step 2: Emit corrector diagnostics**

Write:

```fortran
[V14_COUPLED_HYBRID] JB=... PASS=2 COMMIT=T QLINK=... WSE_UP=...
```

## Task 5: Restore Tail State on Timestep Rejection

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Hook restore into the rollback branch**

In the `220` timestep-reduction path, before `GO TO 210`, call:

```fortran
CALL RESTORE_TAIL_DYNAMIC_STATE()
```

This keeps tail dynamic state consistent with the already-restored reservoir state.

## Task 6: Verify V14 Stability First

**Files:**
- Test: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 2: Run short-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: PASS with `has_v14_coupled_hybrid = 1`.

- [ ] **Step 3: Run extended smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: PASS.

- [ ] **Step 4: Run long-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44458
```

Expected:
- PASS
- no runaway
- both stations still valid

## Task 7: Record the V14 Result

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\29_v14_stronger_coupled_hybrid_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Write the implementation note**

Document:
- the predictor/corrector order
- the rollback behavior
- whether V14 changed metrics or mainly strengthened numerical coherence

- [ ] **Step 2: Update the index**

Add the V14 note to the hydrodynamics limitations README.

## Self-Review

- Spec coverage: this plan covers the V14 blueprint requirement for a stronger same-step hybrid coupling sequence with rollback safety.
- Placeholder scan: all tasks include explicit files, commands, and expected behavior.
- Type consistency: predictor, corrector, and rollback are all framed around the same dynamic tail-state data.
