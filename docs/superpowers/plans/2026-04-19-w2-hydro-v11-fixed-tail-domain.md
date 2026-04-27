# V11 Fixed Tail Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an explicit fixed tail-domain metadata layer so the tailreach is no longer hidden inside single-link variables, while preserving current V10 behavior and validations.

**Architecture:** This slice is intentionally structural, not physical. We add explicit tail-domain bounds and diagnostics, thread them through initialization, output, and verification, and keep the current one-link coupling logic intact. This creates a stable domain scaffold for V12 reach-state evolution without changing the underlying tail discharge equations yet.

**Tech Stack:** Intel Fortran reduced W2 build, PowerShell smoke harness, Markdown reference docs

---

## File Structure

- `w2source_v455_2_11_2026/w2modules.F90`
  Responsibility: declare explicit tail-domain metadata arrays and any helper constants needed by V11.
- `w2source_v455_2_11_2026/input.F90`
  Responsibility: allocate the new tail-domain arrays.
- `w2source_v455_2_11_2026/init.F90`
  Responsibility: initialize the new tail-domain arrays to safe defaults.
- `w2source_v455_2_11_2026/init-geom.F90`
  Responsibility: define fixed tail-domain bounds from physical geometry semantics and emit a new V11 diagnostic marker.
- `w2source_v455_2_11_2026/outputa2w2tools.F90`
  Responsibility: use explicit tail-domain metadata when deciding whether an upstream protected segment can emit a tailreach stage.
- `analysis/run_w2_v0_v1_smoke.py`
  Responsibility: require the new V11 diagnostic marker and record a pass/fail field for it.
- `docs/reference/hydrodynamics_limitations/26_v11_fixed_tail_domain_implementation.md`
  Responsibility: record what V11 changed and what it deliberately did not change.
- `docs/reference/hydrodynamics_limitations/README.md`
  Responsibility: index the new V11 implementation note.

## Task 1: Make V11 Measurable First

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- Test: `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-*.csv`

- [ ] **Step 1: Write the failing smoke expectation**

Add a required marker and result field for `V11`:

```python
REQUIRED_MARKERS = [
    ...
    "[V10_TAIL_REACH]",
    "[V11_TAIL_DOMAIN]",
]
```

Add:

```python
has_v11_tail_domain: bool
```

and fail if it is missing.

- [ ] **Step 2: Run smoke to verify it fails**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected: FAIL mentioning missing `[V11_TAIL_DOMAIN]`.

## Task 2: Add Explicit Tail-Domain Metadata

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init.F90`

- [ ] **Step 1: Declare explicit tail-domain arrays**

In `GLOBAL`, add:

```fortran
INTEGER, ALLOCATABLE, DIMENSION(:) :: TAIL_DOMAIN_US, TAIL_DOMAIN_DS, TAIL_DOMAIN_NSEG
LOGICAL, ALLOCATABLE, DIMENSION(:) :: TAIL_DOMAIN_DEFINED
```

Keep existing `TAIL_UPSEG/TAIL_DNSEG` unchanged for now.

- [ ] **Step 2: Allocate and initialize**

Allocate in `input.F90` and initialize in `init.F90`:

```fortran
TAIL_DOMAIN_US = 0
TAIL_DOMAIN_DS = 0
TAIL_DOMAIN_NSEG = 0
TAIL_DOMAIN_DEFINED = .FALSE.
```

- [ ] **Step 3: Rebuild immediately**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

## Task 3: Define the Fixed Tail Domain in Geometry Setup

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`

- [ ] **Step 1: Define domain bounds from physical semantics**

Add logic so that for protected upstream branches:

```fortran
TAIL_DOMAIN_US(JB) = IUPHYS(JB)
TAIL_DOMAIN_DS(JB) = MAX(FRONT_SEG(JB), IUPHYS(JB))
TAIL_DOMAIN_NSEG(JB) = TAIL_DOMAIN_DS(JB) - TAIL_DOMAIN_US(JB) + 1
TAIL_DOMAIN_DEFINED(JB) = TAIL_DOMAIN_NSEG(JB) > 0
```

For unprotected branches, zero them out.

- [ ] **Step 2: Emit a dedicated diagnostic**

Write:

```fortran
[V11_TAIL_DOMAIN] JB=... US=... DS=... NSEG=... LINK_US=... LINK_DN=... DEFINED=...
```

from `init-geom.F90`.

- [ ] **Step 3: Keep current V10 behavior unchanged**

Do **not** change the actual V10 coupling equations in this task. This is a structural step only.

## Task 4: Thread V11 Metadata Through Output Semantics

**Files:**
- Modify: `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\outputa2w2tools.F90`

- [ ] **Step 1: Replace single-link output check with explicit domain-aware check**

Keep the current behavior of only overriding the protected upstream segment output, but gate it through:

```fortran
TAIL_DOMAIN_DEFINED(JB)
TAIL_DOMAIN_US(JB) <= I .AND. I <= TAIL_DOMAIN_DS(JB)
I == TAIL_UPSEG(JB)
```

This keeps behavior stable while moving semantics away from “single variable means domain”.

- [ ] **Step 2: Rebuild**

Run:

```powershell
cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"
```

Expected: `BUILD SUCCESSFUL`

## Task 5: Verify V11 End-to-End

**Files:**
- Test: `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`

- [ ] **Step 1: Run short-window smoke**

Run:

```powershell
python C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py --exe C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe --tmend 44435.4
```

Expected:
- PASS
- `has_v11_tail_domain=1`
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
- no `Add segments 2 through 2`
- `SEG 2` and `SEG 222` still have valid counts

## Task 6: Document What V11 Does and Does Not Do

**Files:**
- Create: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\26_v11_fixed_tail_domain_implementation.md`
- Modify: `C:\Users\NING\Desktop\v455\docs\reference\hydrodynamics_limitations\README.md`

- [ ] **Step 1: Write implementation note**

Document:
- new explicit domain metadata
- how it differs from the old hidden single-link semantics
- that V11 is structural groundwork, not yet a new 1D reach equation set

- [ ] **Step 2: Update index**

Add the V11 implementation note to the hydrodynamics limitations README reading order.

## Self-Review

- Spec coverage: this plan covers the V11 goals from the second-stage blueprint: fixed tail-domain bounds, explicit metadata, output/path semantics, and verification gates.
- Placeholder scan: no `TODO/TBD` placeholders remain; every task names exact files and commands.
- Type consistency: all new metadata names are consistently `TAIL_DOMAIN_*` and intentionally do not replace `TAIL_UPSEG/TAIL_DNSEG` yet.
