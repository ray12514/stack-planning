# Robust testing roadmap (v1)

Recorded 2026-07-07 (Ravon, during the Raider bring-up). Once the Raider
smoke passes, testing moves from "does the pipeline run" to "does the model
hold up for real users on unfamiliar systems."

## 1. Bare-specs stack (the minimal user)

A user who knows roughly what is on the system writes a `stack.yaml` that is
nothing but a name and Spack specs (or a matrix) — no kind, no compilers, no
mpi block, no externals posture:

```yaml
schema_version: 1
name: my-stack
profile_contract: { schema_version: 1 }
templates: { set: v6 }
builds:
  - name: apps
    specs: [hdf5+mpi, kokkos]
```

Everything else must come from the template-set defaults: kind inference from
the specs, `compilers: baseline` (gcc-or-first), MPI provider preference +
`version_policy: newest`, GPU archs from the profile. Acceptance: this stack
renders and concretizes on both a Cray profile (cray-mpich + PrgEnv-gnu) and
a generic Linux profile (site MPI or Spack-built openmpi) **unchanged**.
Add fixture tests for both before testing on real systems.

## 2. Vendor-generic GPU intent (design first, then implement)

A user who does not know the system's GPUs should be able to express "GPU
build of this package" without naming rocm/cuda or an arch. Today the stack
author writes the vendor variant (`kokkos+rocm amdgpu_target=gfx942` /
`kokkos+cuda cuda_arch=80`); the profile already knows vendor and
`arch_target` per node type. The renderer should be able to expand a
vendor-neutral GPU request into the vendor-specific variant + arch per GPU
lane, making stacks portable across AMD/NVIDIA systems.

Open design questions (write the design before implementing):
- Surface: keep `stack.yaml` spec-native. Candidates: a `kind: gpu` build
  whose spec omits the vendor variant (renderer appends `+rocm
  amdgpu_target=X` / `+cuda cuda_arch=Y`), or a documented placeholder.
  No new user-facing policy vocabulary.
- Not every package spells GPU support the same way (`+rocm` vs `+hip` vs
  `+cuda`); the mapping may need to live in package-set metadata, not the
  renderer.
- arch formats must normalize (profile `arch_target` gfx942/sm_80 ↔ spec
  `amdgpu_target=gfx942`/`cuda_arch=80`).

## 3. Multi-system matrix

After Raider: run the same stacks (bare-specs, *-smoke) across every system
profile we hold (blueback, raider, linux-smoke container, smoke fixtures) as
a routine regression, not a one-off. The orchestration loop lives outside
stack-composer (see stack_generation_orchestration_note_v1.md); the render
side just needs the fixtures checked in.

## 4. Lane-less modulefile render into user space (design first)

Asked 2026-07-07: a mode that considers no lanes at all — just renders a
modulefile into a user-chosen location (e.g. `~/privatemodules`), pointing at
an existing built stack. Does not exist today: modulefiles are entirely
lane-driven (`build_front_door_module_plan` derives init/lane modules from
rendered lanes), module roots are installer-owned via `deployment.yaml`, and
zero renderable builds is a hard `no-rendered-lanes` error. Design questions:
what the input is (a rendered workspace? a release manifest? bare
prefix+name), whether it is a new `stack-composer` subcommand or a template
mode, and how it respects the deployment-ownership rule when the target is
explicitly user space.

## Known blockers being worked in parallel

- Raider CUDA externals: gpu lane rendered without cuda toolkit externals
  (Spack tried to fetch cuda itself). Render now warns
  (`gpu_toolkit_unavailable` / `gpu_arch_unrecognized`); root cause in the
  profile's `gpu_toolkit_modules.cudatoolkit` / `arch_target` is under
  diagnosis.
- Inspector probe-system speed (cluster-inspector
  `docs/probe-performance-note-v1.md`).
