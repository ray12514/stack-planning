# Static Platform Catalog Design Note v1

This note defines the detailed product contract for the static platform
catalog. Consumers do not need access to Stack Composer. CSE may produce the
catalog with `render-static`, generate it in another controlled environment,
or assemble and validate the same contract manually.

Start with the shorter
[Static Platform Catalog Overview](static_platform_catalog_overview_v1.md) for
the contents and consumer workflow. This note retains the detailed product and
producer contract.

No v1 stack release has been deployed yet. This note is changeable pre-v1.

## Decision

Keep the **static platform catalog** separate from the existing managed
workspace output. Both products use the same approved platform configuration
contract.

The full managed render remains:

```text
profile.yaml + deployment.yaml + stack.yaml + package sets + policy
  -> selected platform config scopes
  -> generated environment spack.yaml and modules.yaml files
  -> complete build workspace
```

The static platform catalog is a separate flow:

```text
profile.yaml + defaults/site policy
  -> complete reusable Spack config scopes for the system
  -> manual users/package managers include those files from their own spack.yaml
```

The two flows may reuse implementation helpers, especially normalized external
rendering for compilers, MPI, GPU toolkits, and system externals. They must not
share one user-facing interface or one output contract.

## Product contract: catalog tree versus build workspace

The static output is a **catalog tree**. It is not a lane workspace, module
tree, or directly buildable Spack environment. The full output is a **build
workspace** containing everything the downstream build path needs.

| Contract | `stack-composer render-static` | `stack-composer render` |
|---|---|---|
| Platform facts | reads `profile.yaml`; never probes | reads `profile.yaml`; never probes |
| Reviewed fact snapshot | retains the exact input as `profile.yaml` for review; it is not a Spack scope | provenance is recorded in the release manifest |
| Package intent | none; independent of a stack | reads `stack.yaml` and package sets |
| Deployment paths | not accepted or materialized | required from `deployment.yaml` |
| Reusable config scopes | all maintainer-supported safe choices | only scopes selected for the resolved environments |
| Environment `spack.yaml` | no | yes, one per rendered environment |
| Operational `modules.yaml` | no | yes, one complete native policy per environment |
| Named views | no | yes |
| Front-door and lane module artifacts | no | yes |
| Direct build handoff | no; a user must author an environment | yes |
| Owner of root specs | manual user/package manager | full renderer from stack intent |

Static output may publish path-independent module guidance as documentation or
catalog metadata. It must not publish an operational `modules.yaml` whose view,
module-root, or projection paths are unknown. Those paths become known only in
the full render through `deployment.yaml` and the resolved environment plan.

Both products should derive compiler, MPI, GPU, runtime, and external choices
from a shared internal platform plan. `render-static` serializes the complete
safe catalog; `render` selects from that plan and materializes buildable
environments. This is implementation reuse, not a shared output contract.

## Purpose

The static platform catalog gives package managers and advanced users a supported
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
- path-independent common config such as provider, target, repository,
  mirror, and concretizer policy when the site chooses to publish it.

The catalog does not own install trees, build stages, view roots, module roots,
or filesystem permissions. Those are deployment decisions owned by the CSE
installer or the independent package manager.

## Non-goals

- Do not change the existing `stack-composer render` managed workspace contract
  while Blueback is still being proven.
- Do not make manual users use Stack Composer to author their application specs.
- Do not conflate the catalog with generated lane environments.
- Do not publish every discovered fact blindly. The catalog should publish only
  facts that pass site policy and render-safety validation.

## Static catalog shape

The exact layout can change, but the output should be a versioned system-local
tree. The CSE deployment keeps a restricted review copy and publishes the
approved release for package-manager access:

```text
<cse-shared-root>/
  restricted/catalogs/<system>/static/<catalog-release>/
  published/catalogs/<system>/static/
    <catalog-release>/
      README.md
      manifest.yaml
      profile.yaml
      publication.yaml
      SHA256SUMS
      reports/
        static-plan.yaml
      scopes/
        common/
        compilers/<compiler>/<version>/
        mpi/<provider>/<version>/<compiler-version>/
        gpu/cuda/<version>/
        gpu/rocm/<version>/
        platform/<provider-family>/
      examples/
        gnu-cray-mpich-spack.yaml
    current
```

The important property is that each file is a complete valid Spack config YAML,
not a snippet that requires Stack Composer-specific interpretation. The one
exception is the top-level `profile.yaml`: it is the exact reviewed input kept
for provenance and human inspection, not a file included by Spack.

An observed MPI installation whose build compiler cannot be proved remains
review evidence in `profile.yaml`, but it is not a valid catalog input. Manual
review rejects the scope with the provider, version, prefix, and module
evidence. `cluster-inspector verify` and `render-static` must fail on the same
condition. A compiler-named MPI scope and its toolchain are
written only when wrapper, module, or platform evidence establishes one exact
compiler/MPI pairing. The catalog has no `unpaired` MPI path.

Example manual environment:

```yaml
spack:
  include::
  - <catalog-root>/blueback/static/2026.09/scopes/common
  - <catalog-root>/blueback/static/2026.09/scopes/compilers/gcc/14.3.0
  - <catalog-root>/blueback/static/2026.09/scopes/mpi/cray-mpich/9.1.0/gcc-14.3.0
  - <catalog-root>/blueback/static/2026.09/scopes/gpu/rocm/7.0.0
  specs:
  - hdf5+mpi
  - netcdf-c+mpi
```

`<catalog-root>` represents the deployment-selected absolute catalog root and
must be replaced before this illustrative environment is used.

The optional `current` pointer supports discovery. Reproducible environments
and release records use the resolved versioned directory. The published tree
is readable and traversable by all authenticated system users and is not
writable by consumers. Its manifest, README, examples, and scope references
must resolve from the published location without access to the restricted
review copy.

The Stack Composer publication command promotes the reviewed tree without
running `render-static` a second time:

```bash
stack-composer publish-static \
  --catalog <restricted-catalog-release> \
  --output-root <published-catalog-root> \
  --published-at <utc-timestamp> \
  --reviewed-by <reviewer-or-role> \
  --approved-by <release-authority-or-role> \
  --set-current
```

Publication adds `publication.yaml` and `SHA256SUMS` to the copied release.
Existing versioned releases are not overwritten.

Spack, not Stack Composer, decides whether each included package config is used
during concretization.

## Relationship to managed workspace render

The existing managed render can continue to emit only the config scopes needed
by the resolved stack lanes. That is correct for curated stack builds.

The static platform catalog should emit the full maintainer-supported config set
for the system, independent of one `stack.yaml`.

| Product | Primary user | User owns specs? | Stack Composer writes environment `spack.yaml`? | Output |
|---|---|---:|---:|---|
| Full build-workspace render | Curated stack maintainers | mostly no | yes | buildable environments + selected config scopes + modules/views + manifest |
| Static config catalog | Package managers / advanced users | yes | no | include-ready, path-independent Spack config scopes + manifest/examples |

## Open policy questions

These should be resolved before publishing a catalog:

1. Should catalog externals be strict (`buildable: false`) or advisory
   (`externals` available but user can still build alternatives)?
2. Should there be both strict and advisory catalog variants?
3. Should compiler, MPI, and GPU config be rendered as one full file per class
   or split further into one file per provider?
4. Which path-independent site fields are safe to publish to manual users by
   default (mirrors, repository pins, targets, concretizer policy)?
5. How should provenance be recorded for catalog files published to the shared
   filesystem and source repository?

## Manual production and automation

The Blueback managed-stack blueprint path passed on 2026-07-05:

```text
cluster-inspector -> profile.yaml -> stack-composer render -> build/concretize
```

When Stack Composer is unavailable on the target system, a maintainer may
generate the catalog elsewhere or assemble the tree manually from the reviewed
profile and site policy. The manual release must use complete valid Spack
configuration files, retain the same manifest and review evidence, validate
the example environments, and follow the same immutable publication procedure.
Manual production does not weaken the catalog contract.

The automated implementation uses the same resolved plan data as managed
render instead of duplicating MPI, GPU, fabric, or system-external selection in
catalog-specific templates. The proven Blueback profile remains a fixture for
that contract.

Contract validation baseline:

1. Add a catalog plan report that lists what would be published for Blueback.
2. Emit complete Spack config scopes for one selected platform runtime set.
3. Add one example manual `spack.yaml` that includes those scopes.
4. Validate the example with the same Spack version floor used for the managed
   smoke path.
