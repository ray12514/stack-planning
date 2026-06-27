# Stack Workspace Lifecycle v1

How a system, its stacks, the rendered workspaces, and the durable artifacts
relate — and what `stack-content` holds. This closes the "one workspace per
system" misconception: a workspace is per *stack*, and one system runs many.

No v1 release has deployed yet. If the shape is wrong, change it directly before
v1 rather than preserving unused alpha behavior.

## Per system vs per stack

A system has exactly one of three things: one `profile.yaml` (its blueprint of
what is available), one shared install tree, one module root. Everything else is
per stack. `stack-composer render` runs once **per stack**, not once per system.
A single package is just a one-spec stack — same machinery, no special path.

## Many stacks, one shared install tree

Stacks do not share a workspace; they share the install tree. Spack
content-addresses every install by hash, so if one stack already built
`openmpi@5.0.8/abc123…`, another stack that resolves to the same hash reuses it —
no rebuild, no copy. Separate recipes converge into one deduplicated tree.

![Many stacks per system feed one shared install tree](diagrams/stack_system_view.svg)

## Three lifetimes

| Layer | Lifetime | Lives where |
|---|---|---|
| `profile.yaml`, `stack.yaml` | kept (source) | `stack-content`, tracked |
| workspace (`configs/` + `environments/`) | regenerable recipe; keep the `spack.lock` as the build record | render dir / shared FS |
| install tree + views/modules | durable; what users point at | deployment-chosen roots |

The environment is throwaway scaffolding. The **view** (a merged directory /
`module load`) is the stable front-door, backed by the install tree, surviving
re-renders. You can delete and re-render a workspace without touching an
installed package.

## What stack-content holds

`stack-content` is data, not a tool: templates (rendering policy), per-system
files, and a reusable catalog. **Templates live here — not in `stack-composer`**
— because changing the layout (add an OS scope, tweak compiler externals, add an
MPI provider) is a content edit, not a code change. The test: if changing it does
not require editing Python, it is content. `stack-composer` keeps only a minimal
reference/fixture template set; `stack-planning` owns the template API (the
variables/globals render guarantees) — the contract that keeps templates
decoupled from the engine.

![What the stack-content repo holds](diagrams/stack_content_contents.svg)

## Shared vs per-user

Same machinery; only the roots differ. An admin publishes blessed stacks to
shared roots (most users just `module load`). A power user renders their own
stack into their own space, installing into the shared tree via buildcache
(reusing everything) or into a private tree. Set by `deployment.yaml` or
build-time overrides.

## Related

- `stack_build_handoff_note_v1.md` — where render stops and the build seam.
- `deployment_inputs_and_ownership_v1.md` — the chosen roots (`deployment.yaml`).
- `pre_v1_hosting_and_external_inventory_note_v1.md` — the four-repo layout.
