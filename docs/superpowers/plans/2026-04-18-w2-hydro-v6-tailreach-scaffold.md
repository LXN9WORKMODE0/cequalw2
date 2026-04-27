# W2 V6 Tailreach Coupling Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real V6 scaffold by making the tailreach-to-reservoir hydraulic coupling surface explicit in code, with stable exchange variables and diagnostics.

**Architecture:** Do not build a full 1D Saint-Venant tailreach solver yet. Instead, formalize the coupling interface that a future tailreach solver would need: protected tailreach upstream segment, protected reservoir-side active segment, proxy upstream water surface, downstream active water surface, and exchanged discharge. This turns V6 from a pure idea into a concrete, testable coupling object.

**Tech Stack:** Intel Fortran reduced console build, Python smoke regression harness, CE-QUAL-W2 v4.55 source tree.

---

## File Map

- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
  Purpose: add tailreach-coupling scaffold arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
  Purpose: allocate tailreach-coupling arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`
  Purpose: initialize tailreach-coupling arrays.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
  Purpose: define coupling surfaces from the protected front/buffer semantics.
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`
  Purpose: update and log the coupling interface variables each timestep.
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
  Purpose: require the V6 coupling marker while preserving V0-V5 checks.
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\21_v6_tailreach_scaffold_implementation.md`
  Purpose: record the scaffold implementation and its limits.

## Task 1: Add the failing V6 regression

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Add a V6 marker requirement**

Extend the required marker list with:

```python
"[V6_COUPLING]"
```

- [ ] **Step 2: Run the current executable and verify RED**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: fail because `[V6_COUPLING]` does not exist yet.

## Task 2: Add tailreach coupling scaffold state

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`

- [ ] **Step 1: Add coupling-interface arrays**

Add:

```fortran
LOGICAL, ALLOCATABLE, DIMENSION(:) :: TAIL_COUPLED
INTEGER, ALLOCATABLE, DIMENSION(:) :: TAIL_UPSEG, TAIL_DNSEG
REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_WSE_UP, TAIL_WSE_DN, TAIL_Q_LINK
```

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90` and initialize in `init.F90`:

```fortran
TAIL_COUPLED = .FALSE.
TAIL_UPSEG = 0
TAIL_DNSEG = 0
TAIL_WSE_UP = 0.0D0
TAIL_WSE_DN = 0.0D0
TAIL_Q_LINK = 0.0D0
```

## Task 3: Define the coupling surface

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`

- [ ] **Step 1: Seed the hydraulic-only coupling interface**

For protected branches with a front buffer:

```fortran
IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. FRONT_SEG(JB) > 0) THEN
  TAIL_COUPLED(JB) = .TRUE.
  TAIL_UPSEG(JB) = FRONT_SEG(JB)
  TAIL_DNSEG(JB) = CUSMIN(JB)
END IF
```

Do not yet create a separate solver domain. This is interface definition only.

## Task 4: Update and log the coupling surface in `w2_main`

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90`

- [ ] **Step 1: Update interface variables after hydrodynamic solve**

After the main hydrodynamic solve and before autostep:

```fortran
IF (TAIL_COUPLED(JB)) THEN
  TAIL_WSE_UP(JB) = FRONT_WSE(JB)
  TAIL_WSE_DN(JB) = ELWS(CUS(JB))
  TAIL_Q_LINK(JB) = QC(CUS(JB))
END IF
```

- [ ] **Step 2: Add a V6 marker**

Log:

```fortran
[V6_COUPLING] JB=<...> UPSEG=<...> DNSEG=<...> WSE_UP=<...> WSE_DN=<...> QLINK=<...>
```

Log only for protected coupled branches and only when the front event path is active, to keep noise bounded.

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

- [ ] **Step 3: Extended smoke**

Run:

```powershell
if (Test-Path 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case') { Remove-Item -LiteralPath 'C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\case' -Recurse -Force }
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44436.5
```

Expected: all prior gates still pass, plus `[V6_COUPLING]`.

## Task 6: Document the outcome

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\21_v6_tailreach_scaffold_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Record what V6 scaffold actually means**

Document clearly that this is a hydraulic coupling-interface scaffold, not a full 1D tailreach solver.

- [ ] **Step 2: Record the next true V6 step**

State that the next step after this would be to replace the proxy front evolution with a real local 1D dynamic solver operating on `TAIL_UPSEG <-> TAIL_DNSEG`.
