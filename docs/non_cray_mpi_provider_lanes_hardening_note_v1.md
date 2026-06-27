> **Superseded (pre-provider-refactor).** This document predates the move to a
> single `defaults.yaml` (no contract/toolchain/build-class) and generic
> `compiler_providers`/`mpi_providers` (Cray PE is one `provider_family`). It is
> kept for design history. The current model lives in
> `stack_generation_structure_v1.md`, `stack_workspace_lifecycle_v1.md`, and the
> JSON Schemas under `../schemas/`. Names below (`vendor_cray`, `contract`,
> `toolchain`, `build_classes`, `compilers_external`) are historical.

# Non-Cray MPI Provider Lane Hardening Note v1

## Status

Design note / hardening target. This is not assumed to be fully supported by the current implementation.

## Context

The stack generation system must support Cray systems well, because many target machines are Cray systems and Cray PE is a major operational reality. However, Cray PE should not become the hidden default assumption behind every compiler, MPI, GPU, module, and build-cache decision.

Cray-specific logic is valid where Cray is genuinely special, especially for `PrgEnv-*`, Cray compiler wrappers, Cray MPICH flavors, LibSci, and Slingshot/libfabric behavior. But the broader stack model should remain provider-oriented and vendor-neutral wherever possible.

## Motivation

Some supported applications or delivered binaries may require a non-default compiler/MPI pairing. One example is an Intel compatibility lane on a Cray system:

```text
PrgEnv-intel / Intel compiler runtime
+
Intel MPI
```

This is different from the normal Cray-native pairing:

```text
PrgEnv-intel
+
Cray MPICH
```

The Intel MPI case may not be the preferred default for source builds on AMD-heavy Cray systems, but it can still be required for compatibility with vendor-delivered binaries, precompiled applications, or codes whose support contract assumes Intel runtimes and Intel MPI.

## Design principle

Cray MPICH should be the normal Cray MPI provider, not a hard-coded universal assumption.

The stack model should represent MPI providers as explicit lane/provider choices. A Cray-hosted stack should be able to express both:

```text
compiler = intel
mpi      = cray-mpich
```

and:

```text
compiler = intel
mpi      = intel-mpi
```

without forcing the second case through Cray MPICH-specific logic.

## Desired profile representation

A future `profile.yaml` should be able to capture non-Cray MPI providers with their full required module stack, including compiler or programming-environment preconditions when needed.

Example target shape:

```yaml
vendor_cray:
  intel:
    version: "2024.2"
    prefix: /opt/intel/oneapi/compiler/2024.2
    modules:
      - PrgEnv-intel
      - intel/2024.2

mpi:
  - name: intel-mpi
    provenance: site
    version: "2021.13"
    prefix: /opt/intel/oneapi/mpi/2021.13
    compiler: intel@2024.2
    modules:
      - PrgEnv-intel
      - intel/2024.2
      - intel-mpi/2021.13
```

The important part is that the MPI provider records the actual environment contract needed to use it, not merely the final MPI module name.

## Desired lane representation

The template/contract layer should be able to define a compatibility lane such as:

```yaml
toolchains:
  intel-intelmpi:
    compiler: intel
    mpi: intel-mpi
    gpu_toolkit: none
    purpose: compatibility
```

The lane should render separately from the Cray-native Intel lane:

```yaml
toolchains:
  intel-craympich:
    compiler: intel
    mpi: cray-mpich
    gpu_toolkit: none
    purpose: cray-native
```

## Desired provider policy

MPI provider selection is a render-time policy decision, not a
`cluster-inspector` decision. `cluster-inspector` reports observed
facts: available compilers, MPI providers, prefixes, modules, and the
provider's compiler or programming-environment preconditions when
known. Stack Composer resolves those facts against the selected stack
contract and lane compiler.

The contract-facing MPI shape should allow a package manager to omit
the mode in the common case:

```yaml
toolchains:
  science-mpi:
    compiler: each_science_mpi_compiler
    mpi:
      provider: openmpi
```

Omitting `mode` is equivalent to:

```yaml
mpi:
  provider: openmpi
  mode: auto
```

`auto` means: use a compatible external MPI if the profile and
contract prove one exists for the lane's compiler; otherwise let Spack
build that MPI for the lane. It must never silently reuse an external
MPI built with a different compiler. Power users and compatibility
lanes may override the default with stricter modes such as:

- `external` — require a compatible external and fail render if none
  exists;
- `spack` — always build the named MPI provider with Spack for that
  lane;
- `platform` — require a platform-backed provider such as Cray MPICH;
- `bespoke` — use an explicitly named site/provider resolver from the
  template contract.

Cray MPICH remains the default production Cray MPI provider today, and
Spack-built MPI remains forbidden for production Cray MPICH lanes. The
model still needs to support alternate, contract-approved providers on
Cray-hosted systems — for example Intel MPI compatibility lanes today,
or future OpenMPI/MPICH-style providers that officially support the
site's Slingshot/CPE environment. Those providers should be added as
profile facts plus contract policy, not as new hardcoded Python
branches.

## Desired Spack external rendering

For the Intel MPI case, rendered Spack configuration should preserve the full platform module chain:

```yaml
packages:
  mpi:
    buildable: false
    require:
      - intel-mpi

  intel-mpi:
    buildable: false
    externals:
      - spec: intel-mpi@2021.13 %intel@2024.2
        prefix: /opt/intel/oneapi/mpi/2021.13
        modules:
          - PrgEnv-intel
          - intel/2024.2
          - intel-mpi/2021.13
```

This avoids relying on an implicit loaded environment and makes the lane reproducible.

## Current limitation to harden

The current implementation is expected to handle Cray MPICH more naturally than Cray-hosted non-Cray MPI providers. The hardening target is to avoid assumptions such as:

- every Cray MPI lane means Cray MPICH;
- generic MPI verification only needs to load the MPI module itself;
- MPI providers do not need compiler or programming-environment preconditions;
- lane planning can choose the MPI provider from system family alone.
- an MPI provider named in the contract is always usable as an
  external for every compiler lane.

Instead, MPI provider selection should be explicit and contract-driven.

## Acceptance criteria

A future hardening pass should make the following possible:

1. A Cray profile can contain both `cray-mpich` and `intel-mpi` providers.
2. A generic MPI provider can declare required modules that include compiler and `PrgEnv-*` preconditions.
3. Stack Composer can select `intel-mpi` on a Cray system for an explicitly requested compatibility lane.
4. The default Cray lanes continue to prefer Cray MPICH unless policy says otherwise.
5. Rendered `packages.yaml`, lane metadata, and final manifests show which MPI provider was selected.
6. Module emission preserves the full provider module chain for user-facing front-door modules.
7. A generic Linux MPI toolchain can omit `mode` and get `auto`
   semantics: compatible external if proven, otherwise Spack-built MPI.
8. If no compatible external MPI exists for a lane compiler, Stack
   Composer does not borrow another compiler's MPI external.

## Non-goal

This note does not imply that Intel MPI should become a default MPI provider on Cray systems. The intended default remains Cray-native unless a system contract, stack policy, or application compatibility lane explicitly chooses otherwise.
