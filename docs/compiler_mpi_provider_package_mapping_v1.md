# Compiler and MPI Provider Package Mapping v1

## Decision

`profile.yaml` records the provider identity observed on the system. Spack
configuration records the package identity used by the pinned Spack package
repository. Those names are often the same, but they are not required to be.

For the Initial Conversion Trials, the renderer applies these mappings:

| Observed profile provider | Spack package |
|---|---|
| `intel` | `intel-oneapi-compilers-classic` |
| `oneapi` | `intel-oneapi-compilers` |
| `intel-mpi` | `intel-oneapi-mpi` |

Other provider names remain unchanged unless a reviewed Spack package mapping
is added later.

Classic Intel remains `intel` in the profile because that is the compiler
family exposed by `icc`, `icpc`, and `ifort`. The newer LLVM-based Intel
compiler remains `oneapi` and is identified by `icx`, `icpx`, and `ifx`.
Cluster Inspector reports those observed facts; it does not choose which
provider the stack uses.

When `intel-mpi` is paired with Classic Intel, the rendered
`intel-oneapi-mpi` external requires `+classic-names`. This preserves the
classic Intel MPI wrapper surface rather than silently selecting only the
LLVM-based wrapper names.

## Pre-change assessment

1. **Requested change.** Support a Classic Intel compiler plus Intel MPI
   platform lane and the current CCE releases without maintaining separate
   renderer paths for individual systems.
2. **Design source.** `stack_generation_structure_v1.md` assigns observed
   providers to `profile.yaml`, stack selection to defaults/stack intent, and
   Spack scope generation to Stack Composer. `AGENTS.md` in Cluster Inspector
   requires discovery vocabulary to remain in the embedded policy.
3. **Ownership.** Compiler commands and module evidence are observed facts.
   The corresponding Spack package name and required package variants are
   renderer/build-tool behavior.
4. **Scope classification.** Required by the current design. The static catalog
   cannot be valid when an observed provider name is not a package in the
   pinned Spack repository.
5. **Seam.** Cluster Inspector's discovery policy distinguishes Classic Intel
   from LLVM-based oneAPI. A small Stack Composer provider-package adapter owns
   the name translation and package-specific variants. Static and managed
   rendering both use that adapter.
6. **Risks.** Mapping at probe time would make Cluster Inspector package-manager
   aware. Mapping independently at template call sites would create drift.
   The selected seam avoids both. Explicit compiler paths in the profile remain
   authoritative when a site's installation layout differs.
7. **Decision.** Update this design note first, then change the discovery policy,
   the shared renderer adapter, tests, and representative trial content.

## CCE package versions

The pinned `spack-packages` release contains an external-only CCE stub with only
`16.0.0`. The CSE package repository defines the same external compiler package
behavior with only the three CCE releases used by current CPE generations:
`19.0.0`, `20.0.0`, and `21.0.0`. No download metadata is required because CCE
is platform-provided and remains non-buildable.
