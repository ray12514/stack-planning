> **Superseded (pre-provider-refactor).** This document predates the move to a
> single `defaults.yaml` (no contract/toolchain/build-class) and generic
> `compiler_providers`/`mpi_providers` (Cray PE is one `provider_family`). It is
> kept for design history. The current model lives in
> `stack_generation_structure_v1.md`, `stack_workspace_lifecycle_v1.md`, and the
> JSON Schemas under `../schemas/`. Names below (`vendor_cray`, `contract`,
> `toolchain`, `build_classes`, `compilers_external`) are historical.

# Stack Composer Declarative Render Alignment v1

This note records the pre-v1 correction needed for `stack-composer`: keep the
renderer thin and move site/vendor/package policy back into declarative
contracts, template scopes, profile facts, and normal Spack configuration.

No v1 stack release has been deployed. If the current implementation shape is
wrong, change it directly before v1.

**Status update (pre-v1):** the user-facing `stack.yaml` has been simplified to
be spec-native — a build is `name` + Spack `specs` (or a `package_set`), with
`kind` and the `class`/`toolchain`/`nodes`/`expand` fields optional and inferred.
See `schemas/stack-v1.json` and v6 § stack.yaml. The resolver machinery stays in
the template contract; this note's render-internals guidance still applies.

## Decision

`stack-composer` should not become a second package manager, a second Spack
concretizer, or a large Python policy engine.

The target model is:

```text
cluster-inspector
  -> profile.yaml                 # observed system facts

package manager / stack owner
  -> stack.yaml                   # stack intent, package sets/specs, policy
  -> package-sets/*.yaml          # curated or inline Spack specs

template-set owner
  -> contract.yaml                # resolver names, scope mappings, policy maps
  -> stack-defaults.yaml          # default stack policy
  -> configs/**                   # Spack config fragments / Jinja templates
  -> environments/**/spack.yaml   # environment templates

stack-composer
  -> validates and resolves facts + intent + contract
  -> renders normal Spack environments/configs
```

Python owns validation, merging, generic resolution, deterministic rendering,
and clear failure messages. YAML/templates own package, provider, module,
target, external, GPU, MPI, and site-specific policy wherever possible.

## Why this note exists

The repository already has the right broad shape: a `profile.yaml`, a
`stack.yaml`, package sets, and a template set with `contract.yaml`,
`stack-defaults.yaml`, `configs/**`, and `environments/**`.

The drift is that some decisions that should be declarative have moved into
Python while implementing early phases. That makes the renderer harder to
generalize across Cray, Penguin, IBM, generic Linux, future modular Cray PE,
Open MPI on Slingshot, CUDA, ROCm, and site-built providers.

## Current drift inventory

This is the current implementation smell to remove before v1 where practical.

| Current location | Current behavior | Target owner |
|---|---|---|
| `render/plan.py::compiler_candidates` | Interprets names such as `gnu_host_default` and `each_science_*` directly in Python. | `contract.yaml` compiler resolver definitions plus generic resolver code. |
| `render/plan.py::mpi_provider_for` | Picks `cray-mpich` whenever `profile.vendor_cray.cray_mpich` exists unless policy is `none`. | Contract-driven MPI policy: `auto`, `require_external`, `prefer_compatible_external`, fallback-to-Spack rules. |
| `render/scopes.py::gpu_scope` | Maps `gfx*` to `gpu/amd-rocm` and `sm_*` to `gpu/nvidia-cuda` in Python. | `contract.yaml` GPU selector/scope mapping. |
| `model/package_set.py::expand_gpu_variant` | Expands custom `+gpu` placeholder to `+rocm` or `+cuda` in Python. | Contract-declared package-spec alias/variant expansion, or remove shorthand and require normal Spack specs. |
| `render/plan.py::make_lane` | Hardcodes foundation target as `x86_64_v3`; otherwise uses `node.cpu.preferred`. | `contract.target_policies` and profile baseline/target facts. |
| `render/plan.py::make_lane` | Hardcodes release root as `/shared/stack/releases/...`. | Stack/site/deployment input rendered through `config.yaml`, module roots, view roots, and manifest fields. |
| `render/environments.py::toolchain_for_lane` | Uses Cray string checks and `gfx`/`sm_` checks to build toolchain context. | Generic provider facts resolved into lane context. |
| `render/platform_modules.py` | Looks in `vendor_cray`, `compilers_external`, `mpi`, and GPU toolkit fields with provider-specific branches. | Generic provider/module-chain facts, with Cray as one provider family. |
| Templates | Missing or incomplete scopes for `config.yaml`, `concretizer.yaml`, `modules.yaml`, `mirrors.yaml`, system externals, fabric externals, and selected install tree. | Template-set scopes fed by validated context. |

The goal is not to eliminate all Python. The goal is to keep Python generic.
For example, a generic resolver can evaluate declarative compiler/MPI/GPU
resolver rules. It should not know that every Cray-hosted MPI lane means
`cray-mpich`, or that every AMD GPU package uses exactly one hardcoded variant
expansion.

## Target template-set layout

A v1-ready template set should look closer to this:

```text
template-set/
  contract.yaml
  stack-defaults.yaml

  configs/
    common/
      config.yaml.j2
      concretizer.yaml.j2
      packages.yaml.j2
      repos.yaml.j2
      mirrors.yaml.j2
      modules.yaml.j2

    os/
      rhel8/
      rhel9/
      sles15/

    provider/
      generic-linux/
      cray-pe/
      penguin/
      ibm/

    compiler/
      gcc/
      cce/
      aocc/
      oneapi/
      nvhpc/

    mpi/
      cray-mpich/
      openmpi/
      mpich/
      intel-mpi/
      mvapich2/

    gpu/
      amd-rocm/
      nvidia-cuda/

    externals/
      system/
      fabric/
      vendor-math/

    target/
      x86_64_v3/
      zen3/
      zen4/

  environments/
    core/spack.yaml.j2
    serial/spack.yaml.j2
    mpi/spack.yaml.j2
    gpu/spack.yaml.j2
```

The exact names can change. The important part is that the template tree owns
rendered Spack config shape, while `contract.yaml` tells the resolver which
scope names satisfy which profile facts and stack policies.

## Package-manager authoring model

Package managers should not need to learn a large new stack-composer language.

They should mostly author:

- normal Spack root specs;
- package-set references when a curated set is useful;
- stack policy such as whether to prefer platform externals;
- optional per-system narrowing when a system needs fewer lanes.

Normal Spack specs must always be accepted:

```yaml
builds:
  - name: mpi
    kind: mpi
    specs:
      mpi:
        - hdf5@1.14.5+mpi+fortran
        - netcdf-c@4.9.2+mpi
```

If shorthand such as `+gpu` remains, it must be documented as a
stack-composer alias and declared by the template contract. The package manager
must be able to run an explain/preflight command that shows the expanded Spack
specs before render.

Do not invent a full matrix language. Spack already has environment
definitions, spec matrices, includes, package preferences, externals, and
package repositories. Stack Composer should generate these Spack-native files,
not replace them.

## Provider and external policy

The durable provider model is:

```text
profile facts say what exists
stack/default policy says whether facts may be used
contract rules say how facts map to scopes and lanes
templates render selected facts into Spack config
```

Cray PE is one provider family, not the universal model. Current Cray PE probes
are useful, but new renderer policy should prefer generic provider facts:

- compiler providers;
- MPI providers and compiler compatibility;
- GPU toolkit providers;
- fabric/runtime providers;
- system external candidates;
- vendor external candidates when Spack can represent them cleanly.

See `pre_v1_hosting_and_external_inventory_note_v1.md` for the external
inventory boundary and external focus hints.

## Refactor sequence

Use this order so the work stays systematic.

### Sweep 1 — Freeze the target boundary

1. Update design docs and `AGENTS.md` so future agents know the renderer must
   stay declarative-first.
2. Mark current Python hardcoding as drift, not as the intended v1 design.
3. Decide whether `+gpu` remains as a contract-declared alias or is removed in
   favor of normal Spack specs.

### Sweep 2 — Move resolver semantics into `contract.yaml`

Move these from Python branches into declarative resolver maps:

- compiler resolver names;
- MPI provider policy and fallback behavior;
- GPU architecture-to-scope and architecture-to-variant mapping;
- target policy;
- provider-family-to-scope mapping;
- module exposure mode mapping.

Python should evaluate resolver rules and produce lane context. It should not
encode site/vendor policy names.

### Sweep 3 — Generalize profile provider facts

Before v1, decide whether to keep current profile fields through the first
system test or migrate directly to generic provider inventories.

At minimum, add enough profile facts for:

- selected install-tree candidates versus chosen install tree;
- system external candidates such as OpenSSL/curl when policy can choose them;
- fabric userspace externals;
- provider module chains;
- compiler/MPI compatibility evidence.

### Sweep 4 — Complete missing Spack config scopes

Render these as normal Spack config fragments:

- `config.yaml` for install tree, source cache, build stage;
- `concretizer.yaml`;
- `modules.yaml`;
- `mirrors.yaml`;
- system/fabric/vendor external `packages.yaml` scopes;
- module-front-door artifacts if `stack.modules.exposure` requires them.

### Sweep 5 — First-system evidence loop

Run one Cray and one Penguin/generic Linux system through:

```text
cluster-inspector -> profile.yaml -> stack-composer validate/explain/render
-> spack concretize -> spack install smoke package
```

Bring back every missing fact or hardcoded assumption to this note and update
the schema/design before adding more implementation branches.

## Definition of done for the alignment

The alignment is complete enough for v1 when:

- adding a new MPI provider does not require editing `render/plan.py`;
- adding a new GPU toolkit/provider scope does not require editing
  `render/scopes.py` or `model/package_set.py`;
- Cray-specific behavior is represented as profile facts plus provider-family
  policy, not as a universal branch;
- install tree, build stage, modules, mirrors, and externals are rendered from
  explicit stack/profile/template inputs;
- `stack-composer explain` can show available compilers, MPI providers, GPU
  selectors, external candidates, selected scopes, expanded specs, and skipped
  lanes before render;
- package managers can author normal Spack specs without learning a separate
  stack-specific package language.

## Open questions

Answer these before or during Sweep 1:

1. Should `+gpu` remain as contract-declared shorthand, or should stack owners
   write explicit Spack GPU variants?
2. Should generic provider inventory replace `vendor_cray` before v1, or should
   first-system Cray testing use `vendor_cray` while the generic model is
   designed from evidence?
3. What is the smallest initial external focus set for Cray and Penguin tests?
4. Where should the selected install tree live: `stack.yaml`, a deployment
   overlay, or a separate site/deployment input consumed by Stack Composer?
5. How much of module front-door generation belongs in Stack Composer versus a
   downstream deployment/build helper?
