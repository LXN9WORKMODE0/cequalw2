## Goal

Implement the first coherent upgrade slice of the CE-QUAL-W2 hydrodynamic blueprint:

- `V0`: diagnostics and regression hooks
- `V1`: domain-foundation semantics for a fixed physical upstream boundary

This slice must remain logically consistent across:

- physical upstream boundary meaning
- active-domain meaning
- inflow/source placement meaning
- warning-log diagnostics
- runnable regression validation

## Scope

In scope:

1. Add explicit runtime diagnostics that distinguish physical upstream position from active upstream position.
2. Add a fixed physical-upstream concept for each branch, starting with conservative protection of the branch head.
3. Prevent the active upstream boundary from numerically retreating past the protected physical head in this first version.
4. Keep source-placement semantics consistent with the new boundary meaning.
5. Build a reduced console executable and validate behavior on a short-window XLD case.

Out of scope for this slice:

- continuous wetting/drying (`V2`)
- hydro inner iterations (`V3`)
- partial-cell/subgrid geometry (`V4`)
- transition-state physics and GRAV weakening (`V5`)
- hybrid tailreach solver (`V6`)

## Files Expected To Change

Primary source files:

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\input.F90`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-geom.F90`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-u-elws.f90`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\hydroinout.F90`
- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90`

Test and support files:

- `C:\Users\NING\Desktop\v455\analysis\run_w2_v0_v1_smoke.py`
- optional result folders under `C:\Users\NING\Desktop\v455\analysis\verification\`

## Implementation Steps

### Step 1: Baseline regression harness

Create a short-window smoke/regression harness that:

- clones the XLD actual case into an isolated test directory
- shortens the control window to end just after the known `SEG 2` late-activation event
- swaps in a chosen executable
- runs the model
- parses `w2.wrn`
- asserts on diagnostics and segment-activation behavior

The first run must fail because the new diagnostics do not exist yet.

### Step 2: V0 diagnostics

Add warning-log traces for:

- branch physical upstream segment
- branch active upstream segment
- any change to `CUS(JB)`
- source-placement remapping where active-domain rules differ from physical placement

The diagnostics should be readable and stable enough for automated parsing.

### Step 3: V1 domain-foundation semantics

Introduce a fixed physical-upstream branch concept, tentatively `IUPHYS(JB)`, and keep it distinct from `CUS(JB)`.

For this first conservative implementation:

- initialize the physical head from the branch geometry/head segment
- keep the branch-head segment in the active domain for protected branches
- ensure source placement and initialization know both physical and active positions

This version should be intentionally conservative: preserve existing solver structure while stopping the obvious “physical head disappears” behavior.

### Step 4: Build and rerun

Use the reduced console build script to produce a new executable, then rerun the smoke harness.

Expected outcome for this slice:

- the warning log contains the new diagnostics
- the branch-head segment no longer disappears in the same way as baseline
- the short-window run remains executable

### Step 5: Post-run review

Record:

- whether the run completed
- whether `SEG 2` still gets added late
- whether diagnostics stayed internally consistent
- whether any new numerical instability appeared

## Regression Criteria

Required for this slice to count as complete:

1. The modified executable builds successfully.
2. The smoke case runs successfully.
3. The smoke log contains explicit physical/active upstream diagnostics.
4. The protected upstream head is no longer removed and then re-added in the same baseline pattern.
5. No obvious new fatal instability appears in the smoke window.

## Risks

- The existing code may rely on `CUS(JB)` carrying both physical and active meaning in more places than expected.
- A naive clamp on `CUS(JB)` could break geometry assumptions if not paired with minimal active-layer handling.
- Build products are tracked in this repository; verification may recreate generated files in dirty areas of the worktree.

## Working Notes

- Do not revert unrelated case, docs, or build-output changes already present in the worktree.
- Prefer conservative semantic changes over broad refactors in this first slice.
- Keep all new logging behind existing warning-log patterns so validation stays lightweight.
