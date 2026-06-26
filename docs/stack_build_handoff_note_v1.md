# Stack Build Handoff Note v1

This note records the pre-v1 decision for where `stack-composer` stops and how
the build half is handed off:

1. `stack-composer` renders a Spack workspace **tree**; the per-lane `spack.yaml`
   environments plus the `configs/**` scopes they include are the handoff.
2. Build and concretize are a **co-equal downstream choice** — `stack tools`
   (a separate build/concretize tool), the in-house `spack-build` script,
   Ansible, or bare Spack — not `stack-composer`'s job.
3. The source content render consumes lives in a hosted **stack-content**
   directory; see `pre_v1_hosting_and_external_inventory_note_v1.md`.

No v1 stack release has been deployed yet. If the current shape is wrong, change
it directly before v1 rather than preserving unused alpha behavior.

## Decision: Stack Composer is a spec/workspace generator

`stack-composer` validates inputs, resolves stack intent against profile facts
and the template contract, and renders normal Spack input. It is **not** a
package manager, a concretizer, or a build orchestrator. It must stay
adoptable: a site should be able to take its rendered output and build with
whatever tool it already trusts.

This complements `stack_composer_declarative_render_alignment_v1.md`, which keeps
the *render internals* declarative. This note governs the *downstream* build seam
and the *upstream* source directory.

The framing in older docs — "the non-helper," "the central tool," "everything
goes through `stack-composer`" — overstates the tool. Render is one mechanical
seam between source-of-truth inputs and a runnable Spack workspace. The build is
a separate, swappable step.

## The handoff is a workspace tree, not a single file

`stack-composer render` writes a tree and **places files, it does not flatten**:

```text
<shared-fs-or-render-dir>/<system>/<stack>/<release>/
  configs/
    common/            # config.yaml, concretizer.yaml, packages.yaml, mirrors.yaml, modules.yaml, ...
    os/<os>/
    target/<target>/
    vendor/<vendor>/
    mpi/<provider>/
    gpu/<toolkit>/
  environments/
    <compiler>/<lane>/spack.yaml   # the "spec" Spack builds
  release-manifest.yaml
```

Each lane `spack.yaml` references its Spack component yamls through one
`include::` list. In the default delivery mode those are **relative** paths:

```yaml
spack:
  include::
    - ../../../configs/common
    - ../../../configs/mpi/cray-mpich
    - ../../../configs/target/zen3
  specs:
    - hdf5@1.14.5+mpi+fortran %cce_craympich
```

Contract consequence: a lone `spack.yaml` is **not** self-contained. The build
consumer must root the **whole tree** where Spack can read the included scopes.
The `include::` list — not ambient `~/.spack`, site, or system scopes — is the
production isolation boundary, so the tree must travel intact.

## Co-equal build paths

The render step ends at the workspace. The build half — concretize, fetch,
install, smoke/verify, and (optionally) buildcache push — has four supported
paths. None is "the default"; a site picks one.

| Path | Use when | Owns |
|---|---|---|
| `stack tools` | A site already runs the coworker's build/concretize tool. | Concretize, install, cache, verify, from the rendered tree. |
| `spack-build` | Local / single-machine builds; the in-house reference script shipped with `stack-composer`. | Per-lane Spack invocation, reports, version-floor check. |
| Ansible | Multi-host production clusters. | Per-host orchestration; may call `spack-build` or replicate its loop. |
| Bare Spack | Manual fallback, debugging; always available with no helper installed. | The operator runs `spack concretize`/`install` by hand. |

`stack-composer` itself never calls Spack and never reads host state during
render. Each build path owns *how* Spack is invoked. Do not rename `spack-build`;
it is the descriptive name for the Spack-driving helper.

## Build-time locations

A build cannot run until Spack knows the install tree, caches, build stage, and
view/module roots. These are **deployment-owned**, not facts. The handoff
supports **both** mechanisms, and they compose:

- **From the deployment overlay** — the installer's chosen roots in
  `systems/<system>/deployment.yaml` are rendered into
  `configs/common/config.yaml`. They are *chosen*, never auto-derived from the
  profile (which only offers install-tree candidates). See
  `deployment_inputs_and_ownership_v1.md`. (Rendering `config.yaml` is the open
  Phase 7 item in `design_implementation_coverage.md`.)
- **Build-time override** — the build path may supply or override
  install/view/module/cache roots when it invokes Spack, without re-rendering.

Inline environment config and the include order still apply: a build-time
override wins over a rendered scope when both set the same key.

## Config delivery modes

How the build consumer reads the config scopes is a **user choice**:

| Mode | `include::` targets | Sync needed | Notes |
|---|---|---|---|
| A — synced tree | Relative local paths (`../../../configs/...`) | Yes — tree on the shared filesystem | Default. Tree must stay intact. |
| B — GitLab-direct | Remote GitLab URLs | No local sync | Spack reads the config yaml directly from GitLab. |

Mode B requires a Spack release that supports URL/remote config includes.
**Validate the exact remote-include syntax against the pinned Spack floor**
(current tested floor 1.1.1; 1.2 is an explicit adoption test) before committing
it to a template set. Do not assume the syntax from this note; prove it with the
deployed Spack first.

Both modes deliver the same logical workspace; only the include targets and the
sync requirement differ. The chosen mode is a render option / template-contract
setting, not a fork in the model.

## Stack-content directory (the upstream source)

Render consumes a hosted **stack-content** directory — the human-authored source
of truth, distinct from the three tool repos:

```text
stack-content/
  systems/<system>/profile.yaml                 # per-system observed facts
  stacks/<stack>/stack.yaml                       # package intent
  package-sets/*.yaml                             # curated Spack spec sets
  package-repos/<name>/                           # optional package repositories
  templates/<set>/
    contract.yaml
    stack-defaults.yaml
    configs/                                       # Spack component yamls (.j2)
    environments/
```

It is a new (4th) GitLab repo in the same group as `cluster-inspector`,
`stack-composer`, and `stack-planning`, **synced onto each target's shared
filesystem** where render and build run. See
`pre_v1_hosting_and_external_inventory_note_v1.md` for the repository-layout
recommendation. There may be more than one stack-content repo (per team or
per stack family); the pattern is the same. For how render is driven across
systems and when to re-render, see `stack_generation_orchestration_note_v1.md`.

## stack tools integration boundary

| Concern | Owner |
|---|---|
| Validate inputs, resolve intent, render the workspace tree | `stack-composer` |
| Choose install tree / caches / view & module roots | **Installer** via `deployment.yaml` (or build-time flags); profile offers candidates only, never auto |
| Concretize, fetch, install, smoke/verify | `stack tools` (or `spack-build` / Ansible / bare Spack) |
| Buildcache push | The build path, per stack policy |

`stack tools` is an external peer. `stack-planning` owns the rendered-workspace
contract it consumes; it does not own `stack tools`' internals.

## Provisional status and open questions

The handoff contract is provisional until first-system testing. Confirm with the
coworker / `stack tools` and bring evidence back here:

1. Does `stack tools` consume the **whole tree** intact (relative `include::`),
   or want absolute include paths, a flattened single `spack.yaml`, or a
   different root?
2. Does it honor the rendered `config.yaml` roots, or supply its own
   install/view/module/cache roots at build time?
3. Does it fetch stack-content by **cloning GitLab** or by reading the
   **shared-FS** synced copy?
4. Who owns **concretizer policy** (`unify`/`reuse`) and **Spack version-floor**
   enforcement — `stack tools` or us?
5. Does `stack tools` also cover **multi-host** orchestration (overlap with
   Ansible), or single-host build only?
6. Who owns **buildcache push** destinations?
7. Does `stack tools` run a Spack that supports remote/URL `include::` (config
   delivery mode B), or only local workspace trees?

## Definition of done for the handoff

The handoff is v1-ready when:

- the rendered workspace tree builds under at least `stack tools` and
  `spack-build` from the same inputs;
- the install tree, caches, and view/module roots are resolvable either from a
  rendered `config.yaml` or a build-time override, with a clear error when
  neither supplies them;
- both config delivery modes (synced tree and GitLab-direct) are validated
  against the pinned Spack release;
- a package manager can render and hand off without learning a `stack-composer`
  build language — they author normal Spack specs and pick a build path.
