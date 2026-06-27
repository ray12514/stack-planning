# Pre-v1 Hosting And External Inventory Note v1

This note records two pre-v1 project policies:

1. project-owned source paths must be able to move from GitHub to GitLab before
   v1 without carrying compatibility code; and
2. external discovery must remain a facts-versus-policy boundary between
   `cluster-inspector` and `stack-composer`.

No v1 stack release has been deployed yet. If the current model is wrong,
change it directly before v1 rather than preserving unused alpha behavior.

## Hosting and import paths

The implementation repositories may temporarily live on GitHub during alpha
development, but GitHub is not the intended long-term import authority for
project-owned code.

Policy:

- Do not add new project-owned imports or source references under a personal
  GitHub namespace.
- Before the v1 tag, move project-owned import/module paths to the final GitLab
  namespace, or to a neutral vanity import path if that route is chosen.
- Third-party open-source URLs may still point at GitHub when GitHub is the
  upstream source for that dependency.
- Documentation examples should avoid personal GitHub URLs for project-owned
  repos. Use neutral names, GitLab placeholders, or relative repo references
  unless the line is explicitly describing the temporary alpha host.

For `cluster-inspector`, this specifically means replacing the Go module path:

```go
module github.com/ray12514/cluster-inspector
```

with the final path before v1, for example:

```go
module gitlab.example.com/<group>/cluster-inspector
```

and rewriting the repository's internal imports to match. Because
`cluster-inspector` is a command-oriented Go binary and no v1 consumers exist
yet, this should be a direct rename, not a compatibility bridge.

`stack-composer` is a Python application package and does not currently use a
project-owned GitHub import path. Moving it to GitLab should mainly affect git
remotes and CI/release publishing.

`stack-planning` is documentation/schema source. It should avoid
project-owned GitHub links in docs once the final GitLab namespace is known.

## Repository layout recommendation

Use one GitLab group for the stack-generation project and keep a four-repo
split underneath it — three tool repos plus a stack-content repo:

```text
<gitlab-group>/cluster-inspector
<gitlab-group>/stack-composer
<gitlab-group>/stack-planning
<gitlab-group>/stack-content
```

This keeps ownership boundaries clear:

- `cluster-inspector`: read-only system facts and profile production;
- `stack-composer`: stack/profile/template validation and render tooling;
- `stack-planning`: schemas, design docs, and operating model;
- `stack-content`: the human-authored source render consumes — per-system
  `profile.yaml`, `stack.yaml`, package sets, package repos, and the template
  set (`defaults.yaml`, `configs/`, `environments/`).

`stack-content` is data, not a tool. It is the "stack directory" a deployment
sets up first, and it is **synced onto each target's shared filesystem** where
`stack-composer render` and the chosen build path run. A site may keep more than
one `stack-content` repo (per team or per stack family); the pattern is the same.
See `stack_build_handoff_note_v1.md` for how the rendered workspace is handed off
to a build path.

A monorepo can be reconsidered before v1 if CI, release, or review overhead
becomes the bigger problem. The current split matches the component boundaries
better and lets `cluster-inspector` remain useful even if the render path
changes substantially.

## External inventory boundary

`cluster-inspector` should report observed system facts. `stack-composer`
should decide how those facts are used for a particular stack.

That means:

- `cluster-inspector` may discover external candidates: compilers, MPI
  providers, GPU toolkits, fabric userspace libraries, system libraries, module
  prerequisites, prefixes, versions, and confidence/evidence.
- `cluster-inspector` should not decide stack policy such as "use OpenSSL from
  the OS" versus "build OpenSSL with Spack." That belongs to
  `stack.externals`, `defaults.yaml` policy, and render-time validation.
- `stack-composer` should not probe the host. It consumes `profile.yaml`,
  `deployment.yaml`, stack/default policy, package sets, package repos, and
  templates.

Current profile v1 already has first-class fields for:

- `compiler_providers`;
- `mpi_providers`;
- `gpu_toolkit_modules`;
- `fabric.drivers`;
- `fabric.userspace`;
- filesystem candidates.

This is the intended direction: if Stack Composer needs an external at render
time, the candidate should come from `profile.yaml`, not from a host probe in
Stack Composer and not from an untracked side file.

Current profile v1 does not have a general-purpose inventory for ordinary
system package externals such as OpenSSL and curl. Today those are policy fields
in `stack.externals.openssl` and `stack.externals.curl`, but the renderer lacks
a profile fact block that says exactly which system OpenSSL/curl version,
prefix, and variants were observed.

That is a real pre-v1 gap. If the stack policy can say "use system OpenSSL" or
"use system curl", the system profile needs enough observed facts for the
renderer to either emit a correct Spack external or fail with a useful error.

## Pre-v1 direction for Cray and provider generalization

> **Status — realized.** Provider inventory now uses generic
> `compiler_providers` + `mpi_providers`. The generic provider axis is
> `provider_family: platform|site|system`; platform-specific detail such as
> Cray PE/CPE is `platform_family: cray-pe`.

Treat Cray PE/CPE as platform-family detail layered on normal Linux/provider
facts, not as the primary model for the whole system.

The durable direction is:

- `cluster-inspector` detects provider candidates, versions, prefixes, modules,
  compatibility relationships, and provenance;
- `profile.yaml` records those facts in a renderable form;
- `stack-composer` resolves stack intent against profile facts and stack
  policy;
- templates render the selected providers into Spack config.

Cray-specific logic belongs at the evidence/probing boundary: recognizing
`PrgEnv-*`, `cray-mpich`, `craype-*`, CPE version, Slingshot/fabric
requirements, and module prerequisites. Render-time policy should consume the
resulting facts and compatibility relationships instead of hardcoding
`/opt/cray/pe` or assuming every Cray-hosted MPI lane is `cray-mpich`.

The generic provider shape is:

```yaml
compiler_providers:
  - name: gcc
    version: "13"
    provider_family: platform
    platform_family: cray-pe
    modules: [PrgEnv-gnu, gcc-native/13]
    prefix: /opt/cray/pe/gcc-native/13

mpi_providers:
  - name: cray-mpich
    version: "8.1.29"
    provider_family: platform
    platform_family: cray-pe
    modules: [cray-mpich/8.1.29]
    compatibility:
      compilers: [gcc]
    prefix: /opt/cray/pe/mpich/8.1.29
```

This example is not a committed schema. It records the direction: Cray is a
tagged provider family with special evidence and policy constraints, while the
renderer operates on provider facts and relationships that can also represent
Penguin, IBM, generic Linux, future modular Cray PE, Open MPI on Slingshot, or
site-built MPI/toolkit providers.

Do not add more Cray-only render branches without checking whether the same
information is really a compiler, MPI, GPU toolkit, fabric, or system external
provider fact.

## Current ROCm/GPU toolkit behavior

ROCm is already modeled closer to the desired shape than OpenSSL/curl:

```yaml
gpu_toolkit_modules:
  rocm:
    version: "6.0.0"
    module: rocm/6.0.0
    prefix: /opt/rocm-6.0.0
    spack_components:
      - { package: hip,          prefix: /opt/rocm-6.0.0/hip }
      - { package: hsa-rocr-dev, prefix: /opt/rocm-6.0.0 }
      - { package: comgr,        prefix: /opt/rocm-6.0.0 }
      - { package: rocblas,      prefix: /opt/rocm-6.0.0 }
      - { package: hipblas,      prefix: /opt/rocm-6.0.0 }
      - { package: hipsparse,    prefix: /opt/rocm-6.0.0 }
      - { package: rocprim,      prefix: /opt/rocm-6.0.0/rocprim }
      - { package: llvm-amdgpu,  prefix: /opt/rocm-6.0.0 }
```

Stack Composer currently renders every `spack_components` entry as a
`buildable: false` Spack external in the ROCm GPU scope. Therefore, the render
path already depends on the profile to say which ROCm component externals are
available and where they live.

The current `cluster-inspector` implementation derives a fixed ROCm component
list from the ROCm prefix. That is adequate for the first smoke path, but it is
not the same as dynamically discovering every ROCm package Spack could
externalize. Before v1, first-system testing should answer whether the fixed
component list is sufficient or whether profile v1 needs one of these changes:

- more default ROCm components in `gpu_toolkit_modules.rocm.spack_components`;
- hint-controlled inclusion/exclusion of ROCm components;
- probe-backed component detection from the ROCm install tree;
- a more generic external-candidate inventory shared with other system
  packages.

## Proposed pre-v1 direction for system package externals

Do not create a separate long-lived `externals.yaml` unless the profile becomes
too large or the evidence payload becomes operationally noisy. Prefer one
reviewed `profile.yaml` as the render input so Stack Composer has one system
fact contract.

For OpenSSL, curl, and similar system packages, use the generic
`system_externals` profile field. Current pre-v1 shape:

```yaml
system_externals:
  - name: openssl
    version: "3.0.7"
    prefix: /usr
    provider_family: system
    variants: "+shared"
    detection:
      confidence: probed
      source: rpm
  - name: curl
    version: "7.76.1"
    prefix: /usr
    provider_family: system
    variants: "+ssl"
    detection:
      confidence: probed
      source: rpm
```

The field remains pre-v1 and can change from first-system evidence. The
important contract is stable:

- profile facts say what exists;
- stack/default policy says whether those facts may be used;
- templates render `packages.yaml` from the intersection of facts and policy.

Operator hints should be able to narrow or add candidates when automatic
detection is incomplete. Those hints should feed the profile facts, not bypass
the profile and go directly into rendered Spack config.

### External focus hints

`cluster-inspector` already uses module hints to focus discovery on the module
families the site cares about. External discovery should have the same shape
before it becomes broad or expensive.

A future hints file may include an external focus list such as:

```yaml
externals:
  focus:
    - spack: openssl
      sources: [system, module]
    - spack: curl
      sources: [system, module]
    - spack: cray-libsci
      sources: [module]
      module_patterns: [cray-libsci]
```

This example is not a committed schema. It records the rule:

- hints tell `cluster-inspector` what to look for;
- the profile records what was actually found, with evidence;
- Stack Composer renders only profile facts allowed by stack policy;
- absence of a focused external should produce a clear warning or render-time
  failure when policy requires it.

Do not make `cluster-inspector` discover and emit every vendor library it can
see. For vendor packages such as Cray LibSci or future Cray components, first
verify that Spack has a package name that can represent the external cleanly.
If the site-facing module name and Spack package name differ, record that
mapping explicitly in the hint/profile path instead of baking it into renderer
special cases.

The first-system tests should refine the initial external focus set. The
starting list is OpenSSL, curl, fabric/runtime libraries needed for MPI/GPU
stacks, and only those vendor math/runtime libraries that Spack can consume as
externals.

## What this means for the first full-iteration run

For the first Cray and Penguin-system tests:

1. Use `cluster-inspector` to gather compiler/MPI/GPU/fabric/filesystem facts.
2. Record whether OpenSSL, curl, libfabric, UCX, PMIx, hwloc, ncurses,
   libpciaccess, rdma-core, or other system externals must be represented for
   the stack to concretize cleanly.
3. If a system package external is needed but absent from `profile.yaml`, do
   not patch Stack Composer with host-specific probing. Add or fix the
   `cluster-inspector` fact path so the external appears under
   `system_externals`.
4. Keep Stack Composer's role policy-driven: it should render or reject based
   on explicit profile facts and stack policy.
