# W2 V5 Transition Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative state-dependent transition closure so the protected tailreach front buffer can weakly influence local momentum closure through drag and gravity scaling.

**Architecture:** Keep the feedback local and minimal. Derive transition factors from the existing front state/geometry object, then apply them only around the first active segment of the protected main branch. Do not alter the whole branch closure, and do not yet feed the transition factors into ADMX/ADMZ or full turbulence closure.

**Tech Stack:** Intel Fortran reduced console build, Python smoke regression harness, CE-QUAL-W2 v4.55 source tree.

---

## File Map

- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Purpose: add transition-factor arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Purpose: allocate transition-factor arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Purpose: initialize transition-factor arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`
  Purpose: derive transition-state factors from front state/geometry and log them.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
  Purpose: apply the local drag/gravity scaling in a conservative way near the protected active front.
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Purpose: require the V5 transition marker while preserving all prior gates.
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\20_v5_transition_closure_implementation.md`
  Purpose: record the real V5 implementation and limits.

## Task 1: Add the failing V5 regression

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add a V5 marker requirement**

Extend the required marker list with:

```python
"[V5_TRANSITION]"
```

- [ ] **Step 2: Run the current V4 executable and verify RED**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: fail because `[V5_TRANSITION]` does not exist yet.

## Task 2: Add transition-factor state

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`

- [ ] **Step 1: Add arrays**

Add:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: FRONT_TRANSITION, FRONT_DRAG_FACTOR, FRONT_GRAV_FACTOR
```

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90` and initialize in `init.F90`:

```fortran
FRONT_TRANSITION = 0.0D0
FRONT_DRAG_FACTOR = 1.0D0
FRONT_GRAV_FACTOR = 1.0D0
```

## Task 3: Derive transition closure from front state

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`

- [ ] **Step 1: Map front state to transition factor**

In the existing front-buffer update path, derive:

```fortran
SELECT CASE (FRONT_STATE(JB))
  CASE (FRONT_STATE_DRY)
    FRONT_TRANSITION(JB) = 0.0D0
  CASE (FRONT_STATE_WETTING)
    FRONT_TRANSITION(JB) = 0.5D0
  CASE (FRONT_STATE_BUFFER_WET)
    FRONT_TRANSITION(JB) = 1.0D0
END SELECT
```

- [ ] **Step 2: Derive local closure factors**

Use conservative mappings:

```fortran
FRONT_DRAG_FACTOR(JB) = 1.0D0 + 0.20D0 * FRONT_TRANSITION(JB)
FRONT_GRAV_FACTOR(JB) = 1.0D0 - 0.40D0 * FRONT_TRANSITION(JB)
```

Clamp to reasonable bounds if needed:

```fortran
FRONT_DRAG_FACTOR(JB) = MIN(MAX(FRONT_DRAG_FACTOR(JB), 1.0D0), 1.20D0)
FRONT_GRAV_FACTOR(JB) = MIN(MAX(FRONT_GRAV_FACTOR(JB), 0.60D0), 1.00D0)
```

- [ ] **Step 3: Add a V5 marker**

Write:

```fortran
[V5_TRANSITION] JB=<...> SEG=<...> TRANS=<...> DRAG=<...> GRAV=<...>
```

Log on the same protected add-candidate events that already emit `V2_FRONT_STATE` and `V4_FRONT_GEOM`.

## Task 4: Apply local feedback in `w2_main`

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Apply drag scaling only at the first active segment**

In the bottom-shear section, after `SB` has been assembled for a segment, add a guarded local scaling:

```fortran
IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. I == IU) THEN
  SB(KT:KBMIN(I),I) = SB(KT:KBMIN(I),I) * FRONT_DRAG_FACTOR(JB)
END IF
```

- [ ] **Step 2: Apply gravity scaling only at the active-front neighborhood**

In the gravity-force section, add a guarded scaling near the active upstream edge:

```fortran
IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. (I == IU-1 .OR. I == IU)) THEN
  GRAV(KT:KB(I),I) = GRAV(KT:KB(I),I) * FRONT_GRAV_FACTOR(JB)
END IF
```

- [ ] **Step 3: Do not touch these terms yet**

Do not scale yet:

- `ADMX`
- `ADMZ`
- `DM`
- `AZ`
- the tridiagonal water-surface coefficients

This first V5 is local closure feedback only.

## Task 5: Build and validate

**Files:**
- Use the modified source files and smoke harness

- [ ] **Step 1: Build**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

- [ ] **Step 2: Short-window smoke**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: all previous gates still pass, plus `[V5_TRANSITION]`.

- [ ] **Step 3: Extended smoke**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: same pass conditions.

## Task 6: Document the outcome

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\20_v5_transition_closure_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record what V5 actually changes**

Document clearly that V5 adds local state-dependent drag/gravity scaling near the protected active front.

- [ ] **Step 2: Record what V5 still does not do**

State that it still does not provide branch-wide state-dependent closure or full transition feedback into all momentum terms.
