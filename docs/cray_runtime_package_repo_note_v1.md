# Cray Runtime Package Repo Note v1

Recorded 2026-07-02. This note scopes the Cray runtime package work that is
separate from the current Blueback smoke run. The immediate Blueback workaround
may still be `LD_PRELOAD` for the GTL library; this note records the preferred
pre-v1 direction so the workaround does not become the design.

## Reference

CSCS ALPS cluster config, Balfrin snapshot:

https://github.com/eth-cscs/alps-cluster-config/blob/b33dcc9639fe8acb0e3e80b9ead3f95d38ab4444/balfrin/packages.yaml

Relevant observed pattern from that config:

- `cray-gtl`, `cray-mpich`, `cray-pals`, and `cray-pmi` are explicitly
  `buildable: true`;
- `patchelf` is constrained to `@:0.17`;
- `slurm` and `xpmem` are registered as non-buildable system/vendor externals;
- GCC is registered with explicit compiler executables under
  `extra_attributes.compilers`.

## Problem

GPU-aware Cray MPICH needs the GPU transport layer (GTL) to be correctly linked
or loaded. For the first Blueback Kokkos smoke test, `LD_PRELOAD` is an
acceptable operator workaround, but it is not the desired managed-stack model.

Longer term, the stack should be able to represent Cray runtime integration as
ordinary Spack package/config data:

- Cray MPICH and its GPU transport layer;
- Cray PMI/PALS runtime integration where packages need scheduler/runtime
  interfaces;
- fabric-adjacent packages such as libfabric, CXI, XPMEM, Slurm, and possibly
  Open MPI over Slingshot when the site supports that path;
- version constraints required by the Cray platform, such as the observed
  `patchelf` cap in the reference config.

## Proposed direction

Create a project-owned Spack package repository overlay for site/platform
runtime packages that Spack upstream either does not model fully enough for the
target systems or cannot model with site-specific policy.

The package repo should be consumed as a normal Spack repo by Stack Composer's
rendered workspaces. It should not be embedded as Python logic in Stack
Composer templates.

Initial candidate package/recipe surface:

| Package | Purpose |
|---|---|
| `cray-gtl` | Model GTL so GPU-aware Cray MPICH can link/load it without ad hoc `LD_PRELOAD`. |
| `cray-pmi` | Model Cray PMI runtime where MPI/runtime packages need it. |
| `cray-pals` | Model PALS runtime integration for Cray launcher/scheduler paths. |
| `cray-mpich` overlay, if needed | Add missing Cray MPICH package logic only if upstream Spack cannot express the required GTL/runtime coupling. |
| `libfabric` / CXI-related overlay, if needed | Handle Slingshot/CXI-specific libfabric variants or externals when upstream/default Spack behavior is insufficient. |

Do not create recipes merely to mirror every Cray package. Add a package only
when one of these is true:

- Spack needs a package identity to model dependency/linkage correctly;
- the package is a runtime precondition for a supported lane;
- the package must be constrained or patched for the target Cray environment;
- the package is needed to remove an operational workaround such as GTL
  `LD_PRELOAD`.

## Ownership boundary

- `cluster-inspector` discovers facts: installed package prefixes, modules,
  versions, evidence, and runtime relationships where they can be probed.
- `stack-composer` consumes facts and policy: it may include the package repo,
  select external/buildable posture, and render `packages.yaml` / `repos.yaml`.
- The package repo owns package recipes and any Cray-runtime-specific Spack
  package logic.
- `stack-content` owns the policy choice for a given system/stack: which package
  repos to include, which packages are buildable, and which externals are
  accepted.

This keeps Stack Composer generic. The renderer should not learn the internals
of GTL/PALS/PMI. It should learn only enough to include a repo and render
policy-backed Spack config.

## Upstream Spack status (checked 2026-07-03)

Upstream `spack-packages` `cray_mpich` (builtin, external-only,
`has_code = False`) already models GTL *location*: the external spec can carry
`+cuda cuda_arch=NN` / `+rocm amdgpu_target=gfxNNN`, and a `gtl_lib` property
resolves `libmpi_gtl_{cuda,hsa}` under the PE product tree and returns the
needed `ldflags`/`ldlibs`.

**It does not attach GTL automatically, by design.** Nothing in the package or
in Spack core consumes `gtl_lib`; a dependent package must call
`spec["cray-mpich"].package.gtl_lib` in its own `flag_handler`. A repo-wide
search (2026-07-03) found exactly one consumer: LAMMPS. Kokkos, OSU, and HDF5
do not opt in, so no spec spelling makes GTL link for them via upstream alone.
Externals are opaque to Spack — no post-install patchelf is possible on
`/opt/cray` binaries — which is why universal attachment needs the
CSCS-style *buildable* repackaging (patchelf `--add-needed` at install time)
this note proposes.

Consequences:

- Rendered GPU-lane `cray-mpich` externals should carry the GPU variant and
  arch (`+rocm amdgpu_target=gfx942`) so upstream's `gtl_lib` machinery and any
  opt-in consumer work correctly. Cheap, upstream-aligned, fits the network
  plan; the lane already knows its arch.
- The package-repo direction stands: upstream answers "where is GTL", not
  "link it into everything".

## Minimum viable path

1. Keep the Blueback smoke path moving with an explicit documented GTL
   `LD_PRELOAD` step if needed.
2. Add a stack-content policy note identifying which Cray runtime packages are
   currently workaround-backed.
3. Prototype a package repo with the smallest package needed to remove the
   workaround, likely `cray-gtl`.
4. Render that repo through `repos.yaml` and validate that Kokkos can
   concretize/build without manual GTL preload hacks.

## Production-ready path

1. Package repo lives in the final GitLab group with review, tags, CI, and
   release notes.
2. CI validates the package repo against supported Spack floors, starting with
   Spack 1.1.1 and the active Spack 1.2 line.
3. Blueback/Cray template validation checks that GPU-aware Cray MPICH lanes have
   a coherent CPE/ROCm/GTL package story.
4. Manual config catalog and managed stack render both include the repo through
   standard Spack `repos.yaml`.
5. The runbook states whether the lane is still workaround-backed or package
   repo-backed.

## Open questions

- Does upstream Spack already have enough package support for `cray-gtl`,
  `cray-pmi`, `cray-pals`, and newer Slingshot/Open MPI paths, or do we need
  overlay recipes?
- For Blueback's installed Cray MPICH, can GTL be represented as a dependency
  that Spack links normally, or is runtime module/preload behavior still needed?
- Which libfabric should Cray lanes use when both Cray-provided and
  admin/site-installed libfabric are present?
- Should Open MPI over Slingshot be supported as a first v1 lane or tracked as
  a post-v1 provider path?
