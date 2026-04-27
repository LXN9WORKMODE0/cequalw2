# Hybrid Tailreach V15-V18 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current single-segment `tailreach prototype` into a multi-segment hybrid tailreach that owns a fixed tail domain, segmentwise reach state, segmentwise transition closure, and stronger same-step reservoir coupling.

**Architecture:** Keep the main W2 reservoir solver intact. Replace the current branch-level tail sidecar with a fixed contiguous tail domain that stores per-segment `stage / depth / area / storage / discharge / transition-state`. Use a predictor/corrector loop so the reservoir solver consumes predicted tail interface conditions, then commit corrected tail state after the reservoir solve. Preserve rollback semantics for every tail state array.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Responsibility: declare new multi-segment tail-domain arrays and scalar controls.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Responsibility: initialize new controls and default fixed-tail settings.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Responsibility: zero and prepare new multi-segment tail arrays.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
  Responsibility: define a true fixed tail domain and derive `TAIL_COUPLE_SEG`.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
  Responsibility: implement segmentwise tail-state evolution, transition closure, predictor/corrector coupling, and rollback-safe state handling.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`
  Responsibility: demote front-state to semantic/minimum-wetness support and sync from segmentwise tail state.
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90`
  Responsibility: export multi-segment tail-domain outputs instead of only `TAIL_UPSEG`.
- `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Responsibility: add structural checks for multi-segment tail domain and richer transition coverage.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`
  Responsibility: index the new implementation notes.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\30_v15_multisegment_tail_domain_implementation.md`
  Responsibility: record V15 results.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\31_v16_segmentwise_reach_state_implementation.md`
  Responsibility: record V16 results.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\32_v17_segmentwise_transition_closure_implementation.md`
  Responsibility: record V17 results.
- `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\33_v18_multisegment_hybrid_coupling_implementation.md`
  Responsibility: record V18 results.

## Task 1: V15 Fixed Multi-Segment Tail Domain

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\30_v15_multisegment_tail_domain_implementation.md`

- [ ] **Step 1: Write the failing smoke expectation**

Add these checks to `run_w2_v0_v1_smoke.py`:

```python
required_markers = [
    "[V11_TAIL_DOMAIN]",
    "[V15_TAIL_DOMAIN_MULTI]",
]
```

and parse two new summary fields:

```python
has_v15_tail_domain_multi: bool
tail_domain_nseg_min: int
```

The harness should fail if `tail_domain_nseg_min < 2`.

- [ ] **Step 2: Run smoke to verify it fails**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL because `[V15_TAIL_DOMAIN_MULTI]` is missing and/or `tail_domain_nseg_min` is still `1`.

- [ ] **Step 3: Add fixed-domain metadata and controls**

In `w2modules.F90`, add:

```fortran
INTEGER, ALLOCATABLE, DIMENSION(:) :: TAIL_COUPLE_SEG
INTEGER, ALLOCATABLE, DIMENSION(:) :: TAIL_FIXED_MIN_NSEG
LOGICAL, ALLOCATABLE, DIMENSION(:) :: TAIL_MULTI_SEGMENT
```

In `input.F90`, initialize:

```fortran
TAIL_FIXED_MIN_NSEG = 4
TAIL_MULTI_SEGMENT  = .TRUE.
```

In `init.F90`, zero:

```fortran
TAIL_COUPLE_SEG = 0
```

- [ ] **Step 4: Replace the current NSEG=1 domain derivation**

In `init-geom.F90`, replace the current:

```fortran
TAIL_DOMAIN_DS(JB) = MAX(FRONT_SEG(JB), IUPHYS(JB))
TAIL_DOMAIN_NSEG(JB) = TAIL_DOMAIN_DS(JB)-TAIL_DOMAIN_US(JB)+1
```

with fixed-length logic:

```fortran
TAIL_DOMAIN_US(JB) = IUPHYS(JB)
TAIL_DOMAIN_DS(JB) = MIN(IUPHYS(JB) + TAIL_FIXED_MIN_NSEG(JB) - 1, DS(JB) - 1)
TAIL_DOMAIN_NSEG(JB) = MAX(0, TAIL_DOMAIN_DS(JB) - TAIL_DOMAIN_US(JB) + 1)
TAIL_COUPLE_SEG(JB) = MIN(TAIL_DOMAIN_DS(JB) + 1, DS(JB))
```

and emit:

```fortran
[V15_TAIL_DOMAIN_MULTI] JB=... US=... DS=... NSEG=... COUPLE=...
```

- [ ] **Step 5: Make outputs reflect the domain, not only `TAIL_UPSEG`**

In `outputa2w2tools.F90`, replace the current special-case write:

```fortran
IF (I == TAIL_UPSEG(JB)) THEN
```

with a tail-domain check:

```fortran
IF (TAIL_DOMAIN_DEFINED(JB) .AND. I >= TAIL_DOMAIN_US(JB) .AND. I <= TAIL_DOMAIN_DS(JB)) THEN
```

For `V15`, write the domain-wide stage placeholder:

```fortran
ELKT(I) = TAIL_WSE_UP(JB)
```

so every tail-domain segment stops writing `-999` and becomes visible to verification.

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
- `has_v15_tail_domain_multi = 1`
- `tail_domain_nseg_min >= 2`

- [ ] **Step 8: Record V15**

Write `30_v15_multisegment_tail_domain_implementation.md` with:

- what changed
- exact `US/DS/NSEG/COUPLE` behavior
- smoke evidence
- whether `SEG 2`/`SEG 222`/difference changed

- [ ] **Step 9: Commit**

```bash
git add C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90 C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\30_v15_multisegment_tail_domain_implementation.md
git commit -m "feat: define fixed multi-segment tail domain"
```

## Task 2: V16 Segmentwise Reach State Evolution

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\31_v16_segmentwise_reach_state_implementation.md`

- [ ] **Step 1: Write the failing smoke expectation**

Require a new marker:

```python
"[V16_SEGMENT_Q_STATE]",
```

and parse:

```python
has_v16_segment_q_state: bool
tail_segment_state_count: int
```

Fail if `tail_segment_state_count < 2`.

- [ ] **Step 2: Run smoke to verify it fails**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL because segmentwise state does not exist yet.

- [ ] **Step 3: Add segmentwise state arrays**

In `w2modules.F90`, add:

```fortran
INTEGER, PARAMETER :: MAX_TAIL_SEG = 16
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_STAGE_SEG, TAIL_DEPTH_SEG, TAIL_AREA_SEG
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_HRAD_SEG, TAIL_VOL_SEG
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_Q_SEG, TAIL_Q_TARGET_SEG
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRAVEL_TIME_SEG, TAIL_CELERITY_SEG
LOGICAL, ALLOCATABLE, DIMENSION(:,:) :: TAIL_SEG_VALID
```

In `init.F90`, zero them all.

- [ ] **Step 4: Add per-segment geometry initialization**

In `w2_main.f90`, add a helper:

```fortran
SUBROUTINE INITIALIZE_TAIL_SEGMENT_STATE(JB_IN)
```

that loops:

```fortran
DO IS=1,TAIL_DOMAIN_NSEG(JB_IN)
  ISEG = TAIL_DOMAIN_US(JB_IN) + IS - 1
```

and fills `TAIL_STAGE_SEG`, `TAIL_DEPTH_SEG`, `TAIL_AREA_SEG`, `TAIL_VOL_SEG`.

- [ ] **Step 5: Replace single `TAIL_Q_STATE` evolution with per-segment routing**

Add:

```fortran
SUBROUTINE ADVANCE_TAIL_SEGMENT_STATES(JB_IN, JW_IN)
```

with a loop skeleton:

```fortran
QUP = QIN(JB_IN)
DO IS=1,TAIL_DOMAIN_NSEG(JB_IN)
  CALL UPDATE_ONE_TAIL_SEGMENT(JB_IN, JW_IN, IS, QUP, QDN)
  QUP = QDN
END DO
TAIL_Q_LINK(JB_IN) = QUP
TAIL_WSE_UP(JB_IN) = TAIL_STAGE_SEG(1,JB_IN)
TAIL_WSE_DN(JB_IN) = TAIL_STAGE_SEG(TAIL_DOMAIN_NSEG(JB_IN),JB_IN)
```

Keep `UPDATE_TAIL_STAGE` as the branch-level wrapper, but make it call `ADVANCE_TAIL_SEGMENT_STATES`.

- [ ] **Step 6: Emit per-segment diagnostics**

Write:

```fortran
[V16_SEGMENT_Q_STATE] JB=... IS=... ISEG=... Q=... STAGE=...
```

- [ ] **Step 7: Rebuild and rerun all smoke windows**

Run the same three smoke commands as Task 1.

Expected:

- PASS on all windows
- `has_v16_segment_q_state = 1`
- `tail_segment_state_count >= 2`

- [ ] **Step 8: Record V16**

Write `31_v16_segmentwise_reach_state_implementation.md` with:

- the new per-segment state arrays
- how branch-level `TAIL_Q_LINK / TAIL_WSE_*` now derive from segmentwise state
- metric deltas for `SEG 2`, `SEG 222`, and difference

- [ ] **Step 9: Commit**

```bash
git add C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90 C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\31_v16_segmentwise_reach_state_implementation.md
git commit -m "feat: add segmentwise tail reach state evolution"
```

## Task 3: V17 Segmentwise Transition Closure

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\32_v17_segmentwise_transition_closure_implementation.md`

- [ ] **Step 1: Write the failing smoke expectation**

Require:

```python
"[V17_SEGMENT_TRANSITION]",
```

and parse:

```python
has_v17_segment_transition: bool
tail_mode_set: str
```

Fail if the long-window mode set does not include `0,1,2`.

- [ ] **Step 2: Run long-window smoke to verify it fails**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44458
```

Expected: FAIL because current mode coverage is still only `[1,2]`.

- [ ] **Step 3: Add segmentwise transition arrays**

In `w2modules.F90`, add:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRANSITION_SEG
REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_SUBMERGENCE_SEG, TAIL_LOCAL_SLOPE_SEG, TAIL_FROUDE_SEG
INTEGER,  ALLOCATABLE, DIMENSION(:,:) :: TAIL_MODE_SEG
```

- [ ] **Step 4: Compute transition state per segment**

In `w2_main.f90`, add:

```fortran
SUBROUTINE UPDATE_TAIL_SEGMENT_TRANSITION(JB_IN, JW_IN, IS)
```

and compute:

```fortran
SUB_SCORE    = MIN(MAX(TAIL_SUBMERGENCE_SEG(IS,JB_IN), 0.0D0), 1.0D0)
SLOPE_SCORE  = 1.0D0 - MIN(TAIL_LOCAL_SLOPE_SEG(IS,JB_IN)/MAX(SLOPEC(JB_IN),1.0D-6), 1.0D0)
FROUDE_SCORE = 1.0D0 - MIN(TAIL_FROUDE_SEG(IS,JB_IN), 1.0D0)
TAIL_TRANSITION_SEG(IS,JB_IN) = MIN(MAX(0.25D0*SUB_SCORE + 0.40D0*SLOPE_SCORE + 0.35D0*FROUDE_SCORE, 0.0D0), 1.0D0)
```

Use thresholds:

```fortran
IF (TAIL_TRANSITION_SEG(IS,JB_IN) < 0.33D0) THEN
  TAIL_MODE_SEG(IS,JB_IN) = 0
ELSEIF (TAIL_TRANSITION_SEG(IS,JB_IN) < 0.66D0) THEN
  TAIL_MODE_SEG(IS,JB_IN) = 1
ELSE
  TAIL_MODE_SEG(IS,JB_IN) = 2
END IF
```

- [ ] **Step 5: Make transition state control local closure**

Still in `w2_main.f90`, apply `TAIL_TRANSITION_SEG` to per-segment closure:

```fortran
TAIL_AREA_SEG(IS,JB_IN) = TAIL_AREA_SEG(IS,JB_IN) * (1.0D0 - 0.15D0*TAIL_TRANSITION_SEG(IS,JB_IN))
TAIL_HRAD_SEG(IS,JB_IN) = TAIL_HRAD_SEG(IS,JB_IN) * (1.0D0 - 0.10D0*TAIL_TRANSITION_SEG(IS,JB_IN))
```

and to propagation:

```fortran
TAIL_CELERITY_SEG(IS,JB_IN) = TAIL_CELERITY_SEG(IS,JB_IN) * (1.0D0 - 0.20D0*TAIL_TRANSITION_SEG(IS,JB_IN))
```

- [ ] **Step 6: Demote `FRONT_STATE` to semantic sync**

In `layeraddsub.F90`, replace the current single-value sync:

```fortran
FRONT_TRANSITION(JB) = TAIL_TRANSITION_STATE(JB)
```

with downstream-most segment sync:

```fortran
FRONT_TRANSITION(JB) = TAIL_TRANSITION_SEG(TAIL_DOMAIN_NSEG(JB), JB)
TAIL_CONTROL_MODE(JB) = TAIL_MODE_SEG(TAIL_DOMAIN_NSEG(JB), JB)
```

Keep wet/dry counters and minimum wetness logic, but stop using `FRONT_STATE` as the primary source of transition physics.

- [ ] **Step 7: Emit segmentwise diagnostics**

Write:

```fortran
[V17_SEGMENT_TRANSITION] JB=... IS=... MODE=... TRANS=... SUB=... SLOPE=... FR=...
```

- [ ] **Step 8: Rebuild and rerun all smoke windows**

Run the same three smoke commands as Task 1.

Expected:

- PASS on all windows
- `has_v17_segment_transition = 1`
- long-window `tail_mode_set` includes `0,1,2`

- [ ] **Step 9: Record V17**

Write `32_v17_segmentwise_transition_closure_implementation.md` with:

- how transition-state moved from branch-level to segmentwise
- how `FRONT_STATE` was demoted
- whether long-window mode coverage now includes river control

- [ ] **Step 10: Commit**

```bash
git add C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90 C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\32_v17_segmentwise_transition_closure_implementation.md
git commit -m "feat: add segmentwise transition closure for tail reach"
```

## Task 4: V18 Multi-Segment Stronger Hybrid Coupling

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90`
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\33_v18_multisegment_hybrid_coupling_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Write the failing smoke expectation**

Require:

```python
"[V18_MULTI_HYBRID]",
```

and add summary checks:

```python
has_v18_multi_hybrid: bool
tail_predictor_pass_count: int
tail_corrector_pass_count: int
```

Fail if either count is zero.

- [ ] **Step 2: Run smoke to verify it fails**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL because `[V18_MULTI_HYBRID]` does not exist yet.

- [ ] **Step 3: Extend predictor/corrector to segmentwise state**

In `w2_main.f90`, extend:

```fortran
SUBROUTINE SAVE_TAIL_DYNAMIC_STATE()
SUBROUTINE RESTORE_TAIL_DYNAMIC_STATE()
SUBROUTINE RUN_TAIL_PREDICTOR()
```

so they also save/restore and predict:

```fortran
TAIL_STAGE_SEG
TAIL_DEPTH_SEG
TAIL_AREA_SEG
TAIL_HRAD_SEG
TAIL_VOL_SEG
TAIL_Q_SEG
TAIL_TRANSITION_SEG
TAIL_MODE_SEG
```

The predictor should call the segmentwise solver and leave the reservoir-facing values committed for the main W2 solve:

```fortran
TAIL_WSE_DN(JBP)
TAIL_Q_LINK(JBP)
```

- [ ] **Step 4: Use the fixed coupling segment at the reservoir boundary**

Replace the current implicit branch-level coupling with:

```fortran
IU = MAX(CUS(JB), TAIL_COUPLE_SEG(JB))
```

where appropriate in the upstream-boundary path so the reservoir solve consistently uses the fixed downstream edge of the tail domain.

- [ ] **Step 5: Export tail-domain water-surface results**

In `outputa2w2tools.F90`, write per-segment stage:

```fortran
IS = I - TAIL_DOMAIN_US(JB) + 1
ELKT(I) = TAIL_STAGE_SEG(IS,JB)
```

for any `I` inside the fixed tail domain.

- [ ] **Step 6: Emit multi-segment hybrid diagnostics**

Write:

```fortran
[V18_MULTI_HYBRID] JB=... PASS=1 COMMIT=F QLINK=... WSE_DN=...
[V18_MULTI_HYBRID] JB=... PASS=2 COMMIT=T QLINK=... WSE_DN=...
```

- [ ] **Step 7: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 8: Run short, extended, and long smoke**

Run the same three smoke commands as Task 1.

Expected:

- PASS on all windows
- `has_v18_multi_hybrid = 1`
- both predictor and corrector counts > 0
- `SEG 2`, `SEG 222`, and `SEG 2-SEG 222` all remain measurable

- [ ] **Step 9: Record V18 and update the hydrodynamics index**

Write `33_v18_multisegment_hybrid_coupling_implementation.md` and add it to:

```markdown
C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md
```

Document:

- the final multi-segment coupling path
- segmentwise output behavior
- current best metrics
- remaining residual gap to a full local 1D solver

- [ ] **Step 10: Commit**

```bash
git add C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90 C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90 C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\33_v18_multisegment_hybrid_coupling_implementation.md C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md
git commit -m "feat: couple multi-segment tail reach to reservoir solver"
```

## Self-Review

- Spec coverage:
  - fixed multi-segment tail domain -> Task 1
  - segmentwise reach state -> Task 2
  - segmentwise transition-state -> Task 3
  - stronger multi-segment hybrid coupling -> Task 4
- Placeholder scan:
  - No `TODO`/`TBD`
  - Every task has files, code targets, verification commands, and expected outcomes
- Type consistency:
  - `TAIL_DOMAIN_*`, `TAIL_COUPLE_SEG`, `TAIL_*_SEG`, and `TAIL_MODE_SEG` names are consistent across tasks

Plan complete and saved to `C:\Users\NING\Desktop\v455\docs\superpowers\plans\2026-04-20-hybrid-tailreach-v15-v18-implementation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints
