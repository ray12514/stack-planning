# Static Platform Catalog Overview v1

| Document control | Value |
|---|---|
| Status | Pre-v1 consumer overview |
| Intended readers | CSE stack maintainers and other Spack package managers |
| Scope | Catalog contents, ownership, consumption, and manual availability |

## Purpose

The static platform catalog is a versioned, system-specific bundle of reviewed
Spack configuration. It gives every package manager the same approved
description of the system's compilers, MPI providers, GPU toolkits, targets,
externals, and path-independent site policy without requiring that package
manager to rediscover or retype those facts.

The catalog is configuration, not a software stack. It does not contain root
package selections, a complete build environment, installed packages, or
deployment paths.

## What the catalog contains

One catalog release contains:

| Content | Purpose |
|---|---|
| `README.md` | Identifies the release and explains scope selection. |
| `manifest.yaml` | Records the system, catalog release, supported Spack identity or floor, available scopes, supported compiler and MPI pairings, source revisions, and file identities. |
| `profile.yaml` | Retains the exact reviewed system-fact snapshot for provenance and human review. Spack does not include this file as configuration. |
| `reports/static-plan.yaml` | Records what platform choices were admitted, rejected, or left unresolved. |
| `scopes/common/` | Contains path-independent common Spack policy approved for consumers. |
| `scopes/compilers/` | Contains one include-ready compiler configuration per supported compiler identity. |
| `scopes/mpi/` | Contains MPI provider configuration and compiler pairings that have sufficient evidence. |
| `scopes/gpu/` | Contains approved CUDA or ROCm toolkit configuration when applicable. |
| `scopes/platform/` | Contains platform runtime, fabric, launcher, and system-external configuration when policy permits publication. |
| `examples/` | Shows small `spack.yaml` files that include valid combinations of catalog scopes. |
| `publication.yaml` and `SHA256SUMS` | Record approval and file checksums in the published copy. |

Every file below `scopes/` must be valid Spack configuration YAML. Catalog
consumers do not need Stack Composer to interpret those files.

The catalog must not publish a compiler and MPI pairing that has not been
established by module, wrapper, prefix, or platform evidence. Unsupported or
unresolved observations remain in the retained profile and report; they do not
become selectable scopes.

## What remains outside the catalog

The package manager or managed CSE stack still supplies:

- root package specs, versions, variants, and dependency constraints;
- the stack or application release identity;
- the install tree, build stages, source and miscellaneous caches;
- build-cache destinations and trust policy;
- views, module roots, and module presentation policy;
- filesystem ownership and permissions; and
- the resulting `spack.lock`, build evidence, and release approval.

For a managed CSE stack, these choices come from `stack.yaml`, package sets,
`deployment.yaml`, and the release process. For an independently managed Spack
environment, the package manager records them in the environment and its
deployment record.

## How CSE consumes it

CSE retains a restricted, versioned catalog release as the approved platform
configuration record. Workspace preparation selects the required compiler,
MPI, GPU, platform, and common scopes for each CSE environment, then combines
them with CSE package intent and restricted deployment configuration.

During the Initial Conversion Trials, the workspace initializer snapshots the
restricted catalog under the generated workspace and writes relative includes
to the selected scopes. The source catalog release remains in the workspace
manifest as provenance, but the completed workspace handoff does not depend on
the original catalog path remaining mounted.

A workspace tool may reference the restricted scopes or copy their exact
configuration into the generated workspace. A full renderer may also
materialize the same selections from the reviewed profile and policy plan.
These are delivery differences, not separate platform policies. The workspace
release manifest must identify the catalog release or the equivalent source
inputs and must record the selected scope identities so the result can be
reviewed.

CSE does not use the public copy to authorize a restricted build. It uses the
restricted catalog of record, or the same reviewed platform plan when the
catalog has been assembled through another controlled path. The public copy
exists for consumers outside the CSE management group.

## How another package manager consumes it

An external package manager chooses a versioned published catalog release,
selects one supported compiler and its compatible MPI or GPU scopes, and
includes those directories from a package-manager-owned `spack.yaml`:

```yaml
spack:
  include::
    - <published-catalog-release>/scopes/common
    - <published-catalog-release>/scopes/compilers/<compiler>/<version>
    - <published-catalog-release>/scopes/mpi/<provider>/<version>/<compiler-flavor>
    - <published-catalog-release>/scopes/platform/<platform>
  specs:
    - hdf5+mpi
    - netcdf-c+mpi
```

The package manager owns the `specs` list and deployment configuration. Spack
merges the selected catalog scopes with that environment, concretizes the
result, and records the exact graph in `spack.lock`.

Use a versioned catalog path for every reproducible environment. A `current`
pointer may help users discover the latest approved release, but it is not a
release input.

## Restricted and published copies

The restricted and published copies represent the same reviewed platform
configuration release:

| Copy | Audience | Use |
|---|---|---|
| Restricted | CSE package managers and reviewers | Review, CSE workspace preparation, and catalog publication source. |
| Published | All authenticated system users | Package-manager scope selection and inclusion. |

Publication copies the reviewed catalog without rerendering it, adds the
publication record and checksum inventory, and grants read and directory
traverse access to other users. Consumers outside CSE receive no write access.
An accepted version is not edited in place. A correction produces a complete
new catalog release.

## Manual availability when the generator is unavailable

The catalog contract does not depend on the catalog generator being installed
where a package manager consumes the release. CSE can use `render-static` in
its controlled environment, generate the catalog elsewhere and transfer the
complete release, or create a release manually by:

1. selecting one reviewed `profile.yaml` and site-policy revision;
2. writing complete Spack YAML files for each supported scope;
3. recording the supported combinations and provenance in `manifest.yaml`;
4. retaining unresolved facts in the profile and static plan instead of
   publishing unsafe scope choices;
5. creating at least one small example environment for each supported
   compiler and MPI pairing;
6. validating the selected scopes with the approved Spack runtime; and
7. retaining the reviewed release in the restricted catalog area before
   publishing an exact approved copy.

`stack-composer render-static` automates this producer-side contract. The
production method does not change what the catalog means or which decisions
remain with the package manager.

## Consumer boundary

| Artifact | Answers |
|---|---|
| Static platform catalog | What platform configuration is supported on this system? |
| `stack.yaml` or package-manager `spack.yaml` | What packages and variants should be built? |
| `deployment.yaml` or equivalent deployment record | Where is the environment installed and who can access it? |
| `spack.lock` | What exact concrete dependency graph was approved and built? |

The detailed catalog tree and future automation contract are recorded in
[Static Platform Catalog Design Note v1](manual_config_catalog_note_v1.md).
