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

Instead, MPI provider selection should be explicit and contract-driven.

## Acceptance criteria

A future hardening pass should make the following possible:

1. A Cray profile can contain both `cray-mpich` and `intel-mpi` providers.
2. A generic MPI provider can declare required modules that include compiler and `PrgEnv-*` preconditions.
3. Stack Composer can select `intel-mpi` on a Cray system for an explicitly requested compatibility lane.
4. The default Cray lanes continue to prefer Cray MPICH unless policy says otherwise.
5. Rendered `packages.yaml`, lane metadata, and final manifests show which MPI provider was selected.
6. Module emission preserves the full provider module chain for user-facing front-door modules.

## Non-goal

This note does not imply that Intel MPI should become a default MPI provider on Cray systems. The intended default remains Cray-native unless a system contract, stack policy, or application compatibility lane explicitly chooses otherwise.
