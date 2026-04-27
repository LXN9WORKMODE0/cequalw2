# W2 V4 Front Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative front-buffer geometry layer so the protected tailreach front is no longer described only by depth/state, but also by continuous proxy area, volume, and hydraulic-radius geometry.

**Architecture:** Do not yet replace the main W2 branch geometry with partial-cell equations. Instead, extend the existing front-buffer object (`FRONT_SEG`, `FRONT_DEPTH`, `FRONT_STATE`) with proxy geometry computed directly from the protected front segment and current proxy depth. This keeps V4 stable and gives later versions a continuous geometry object to couple into stronger physics.

**Tech Stack:** Intel Fortran reduced console build, Python smoke regression harness, CE-QUAL-W2 v4.55 source tree.

---

## File Map

- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Purpose: add front-geometry arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Purpose: allocate front-geometry arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Purpose: initialize front-geometry arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
  Purpose: seed front-geometry arrays at setup time.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`
  Purpose: update front-buffer area/volume/hydraulic-radius proxies whenever front depth/state is updated.
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Purpose: require a V4 geometry marker while preserving all previous smoke gates.
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\19_v4_front_geometry_implementation.md`
  Purpose: record the actual V4 implementation and limits.

## Task 1: Add the failing V4 regression

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add a V4 marker requirement**

Extend the required marker list with:

```python
"[V4_FRONT_GEOM]"
```

- [ ] **Step 2: Run the current executable and verify RED**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: fail because `[V4_FRONT_GEOM]` does not exist yet.

## Task 2: Add front-geometry state

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`

- [ ] **Step 1: Add geometry arrays**

Add:

```fortran
REAL(R8), ALLOCATABLE, DIMENSION(:) :: FRONT_AREA, FRONT_VOLUME, FRONT_HRAD
```

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90` and initialize to `0.0D0` in `init.F90`.

## Task 3: Seed and update front geometry

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`

- [ ] **Step 1: Seed setup geometry**

At front setup time, initialize:

```fortran
FRONT_AREA(JB) = 0.0D0
FRONT_VOLUME(JB) = 0.0D0
FRONT_HRAD(JB) = 0.0D0
```

- [ ] **Step 2: Update proxy geometry when front depth is updated**

In the existing V2 front-state update path, compute conservative proxy geometry:

```fortran
FRONT_AREA(JB) = BI(KTWB(JW), FRONT_SEG(JB)) * FRONT_DEPTH(JB)
FRONT_VOLUME(JB) = FRONT_AREA(JB) * DLX(FRONT_SEG(JB))
FRONT_HRAD(JB) = FRONT_AREA(JB) / MAX(BI(KTWB(JW), FRONT_SEG(JB)) + 2.0D0 * FRONT_DEPTH(JB), 1.0D-6)
```

Clamp negative values to zero.

- [ ] **Step 3: Add a V4 geometry log marker**

Write a stable line such as:

```fortran
[V4_FRONT_GEOM] JB=<...> SEG=<...> AREA=<...> VOLUME=<...> HRAD=<...>
```

Log on the same protected add-candidate events already used for `V2_FRONT_STATE`.

## Task 4: Build and validate

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

Expected: all previous gates still pass, plus `[V4_FRONT_GEOM]`.

- [ ] **Step 3: Extended smoke**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: same pass conditions.

## Task 5: Document the outcome

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\19_v4_front_geometry_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record what V4 actually means**

Document clearly that V4 adds continuous proxy geometry for the front buffer, not full branch-wide partial-cell dynamics.

- [ ] **Step 2: Record what remains for later**

State that a later version would need to couple `FRONT_AREA / FRONT_VOLUME / FRONT_HRAD` back into the main hydrodynamic equations if we want true front-geometry feedback, rather than geometry diagnostics alone.
