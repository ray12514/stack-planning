# Manual Config Catalog Note v1

This note records a follow-up product for manual/package-manager users. It is
not part of the current Blueback managed-stack validation path.

No v1 stack release has been deployed yet. This note is changeable pre-v1.

## Decision

Keep the **manual config catalog** separate from the existing managed workspace
render.

The current managed render remains:

```text
profile.yaml + deployment.yaml + stack.yaml + templates
  -> rendered workspace
  -> generated lane spack.yaml files
  -> build path
```

The manual config catalog is a separate flow:

```text
profile.yaml + deployment.yaml/site policy + templates
  -> complete reusable Spack config YAML files for the system
  -> manual users/package managers include those files from their own spack.yaml
```

The two flows may reuse implementation helpers, especially normalized external
rendering for compilers, MPI, GPU toolkits, and system externals. They must not
share one user-facing interface or one output contract.

## Purpose

The manual config catalog gives package managers and advanced users a supported
way to consume maintainer-vetted platform facts without asking Stack Composer to
own their package intent.

A manual user still owns:

- their `spack.yaml`;
- their root specs;
- their views, if any;
- their environment naming and lifecycle;
- whether to use bare Spack, `spacktools`, scripts, or another build path.

The catalog owns:

- reusable compiler external config;
- reusable MPI external config;
- reusable GPU toolkit external config;
- curated system externals such as OpenSSL, curl, fabric libraries, and
  platform math/runtime libraries when policy selects them;
- common config such as install tree/cache/mirror/concretizer defaults if the
  site chooses to publish those.

## Non-goals

- Do not change the existing `stack-composer render` managed workspace contract
  while Blueback is still being proven.
- Do not make manual users use Stack Composer to author their application specs.
- Do not conflate the catalog with generated lane environments.
- Do not publish every discovered fact blindly. The catalog should publish only
  facts that pass site policy and render-safety validation.

## Expected shape

The exact layout can change, but the output should be a versioned system-local
tree with one copy also committed or published through the source repository:

```text
stack-config-catalog/
  <system>/
    releases/
      2026.09/
        common/
          config.yaml
          packages.yaml
          repos.yaml
        compilers/
          packages.yaml
        mpi/
          packages.yaml
        gpu/
          rocm/packages.yaml
          cuda/packages.yaml
        os/
          packages.yaml
        targets/
          packages.yaml
        examples/
          gnu-cray-mpich-spack.yaml
    current -> releases/2026.09
```

The important property is that each file is a complete valid Spack config YAML,
not a snippet that requires Stack Composer-specific interpretation.

Example manual environment:

```yaml
spack:
  include:
  - /apps/cse/spack-config-catalog/blueback/current/common
  - /apps/cse/spack-config-catalog/blueback/current/compilers
  - /apps/cse/spack-config-catalog/blueback/current/mpi
  - /apps/cse/spack-config-catalog/blueback/current/gpu/rocm
  specs:
  - hdf5+mpi
  - netcdf-c+mpi
```

Spack, not Stack Composer, decides whether each included package config is used
during concretization.

## Relationship to managed workspace render

The existing managed render can continue to emit only the config scopes needed
by the resolved stack lanes. That is correct for curated stack builds.

The manual config catalog should emit the full maintainer-supported config set
for the system, independent of one `stack.yaml`.

| Product | Primary user | User owns specs? | Stack Composer writes environment `spack.yaml`? | Output |
|---|---|---:|---:|---|
| Managed workspace render | Curated stack maintainers | mostly no | yes | lane environments + selected config scopes + manifest |
| Manual config catalog | Package managers / advanced users | yes | no | complete reusable Spack config YAML files |

## Open policy questions

These should be resolved after Blueback managed render is green:

1. Should catalog externals be strict (`buildable: false`) or advisory
   (`externals` available but user can still build alternatives)?
2. Should there be both strict and advisory catalog variants?
3. Should compiler, MPI, and GPU config be rendered as one full file per class
   or split further into one file per provider?
4. Which deployment fields are safe to publish to manual users by default
   (install tree, cache, mirrors, build stage, modules)?
5. How should provenance be recorded for catalog files published to the shared
   filesystem and source repository?

## Recommended timing

Do not implement this until the Blueback managed-stack path has passed:

```text
cluster-inspector -> profile.yaml -> stack-composer render -> build/concretize
```

After that, implement the catalog as a separate command and output contract,
using the proven Blueback profile as the first fixture.
