# Stack Generation Orchestration Note v1

This note records how rendered workspaces are generated **across multiple
systems**, the lifecycle and cadence of each input, and the **driver contract**
that keeps `stack-composer render` a pure per-system seam.

It answers four questions that were previously only implied:

1. What is generated, and how?
2. How does it stay consistent across systems while each system uses only its
   own slice?
3. What changes, how often, and what does a change force to re-render/rebuild?
4. What orchestrates the loop, and what must stay *out* of `stack-composer`?

No v1 stack release has been deployed yet. This model is changeable pre-v1.

See also: `end_to_end_map_v1.md` (the consolidated A→B map),
`stack_build_handoff_note_v1.md` (rendered tree → build path),
`pre_v1_hosting_and_external_inventory_note_v1.md` (stack-content hosting), and
v6 §"Render Step — Specification" (the seam this note orchestrates).

## Generation is a pure, per-system seam

`stack-composer render` is invoked **once per `(system, stack, release)`**:

```text
render(profile, stack, package_sets, package_repos, templates, release_vars, output)
  → output/<system>/<stack>/<release>/   { configs/**, environments/**, release-manifest.yaml }
```

Render invariants (v6 §Render Step — Specification): file-in / file-out,
deterministic (same inputs → byte-identical tree), never calls Spack, never reads
`$HOME` / `$PATH` / host state, never writes outside `output`. **One profile in,
one system's tree out.** N systems = N render calls = N sibling trees under
`output/`.

This purity is the load-bearing constraint. Everything below keeps the *loop*
and the *cadence* outside this function.

## One shared source, per-system slices (the intersection model)

`stack-content` is the single consistent source. Each system's render selects
only its slice:

```text
profile (what this system has)
  ∩ defaults (what the template set supports)
  ∩ stack.yaml (what is requested)
  [∩ per_system (optional narrowing for this system name)]
  → the concrete lanes rendered for this system
```

The source is consistent; the **output differs per system** because each profile
intersects differently. `per_system:` (v6 §Durable Inputs) is the only place a
system name may appear, and it may **only narrow** — it never widens the
contract, invents a compiler/MPI/GPU arch, or changes package roots. That
guardrail is what lets one `stack.yaml` stay portable across every system.

| Input | Shared or per-system |
|---|---|
| `templates/<set>/` (defaults, configs, environments) | Shared |
| `stacks/<stack>/stack.yaml` | Per-stack (shared across systems) |
| `package-sets/*`, `package-repos/*` | Shared |
| `systems/<system>/profile.yaml` | Per-system |
| rendered `output/<system>/<stack>/<release>/` | Per-system (one tree per render) |

## Input lifecycle and cadence

| Input | Produced by | Cadence | A change re-renders |
|---|---|---|---|
| `templates/<set>/` | Template maintainer (gated by scaffold + review) | Rare — new OS / compiler / MPI / GPU support | every system+stack using that set |
| `stacks/<stack>/stack.yaml` | Package manager | **Most frequent** — package adds, version bumps, new lanes | every system that deploys that stack |
| `package-sets/*` | Curator | Occasional | stacks referencing the set |
| `package-repos/*` | Maintainer | Occasional | stacks referencing the repo |
| `systems/<system>/profile.yaml` | `cluster-inspector` | One-time per system, then on a system change (CPE / OS / compiler upgrade) | only that system |

The rendered workspace is **never committed**. It is a build artifact,
regenerated on demand from the inputs above (v6 §End-to-End Mental Model).

## Re-render / rebuild trigger matrix

The driver uses this to decide scope after a change:

| Changed input | Re-render scope | Rebuild scope |
|---|---|---|
| `profile.yaml` for system S | S only | S's affected lanes |
| `stack.yaml` for stack T | every system deploying T | changed lanes of T on those systems |
| `package-set` P | every stack referencing P (on its systems) | lanes whose specs changed |
| `template set` V (defaults / configs / environments) | every system+stack on V | lanes whose rendered scopes changed |
| new `release` id | the targeted `(system, stack)` | full release build |

Determinism makes this safe: re-rendering unchanged inputs yields the identical
tree, so the driver may re-render freely and let the build path rebuild only what
changed (Spack's own `reuse` / buildcache handles incremental builds).

## The driver contract (tool-agnostic)

A **driver** orchestrates render across systems. It is thin and external — a
`Makefile`, a CI pipeline, an Ansible play, or a shell loop. The model does not
mandate one; each site picks the mechanism. The driver MUST:

1. **Enumerate targets** — the `(system, stack, release)` set to render (see
   Target enumeration).
2. **Resolve inputs** — locate the synced `stack-content` and each system's
   `profile.yaml`.
3. **Invoke `render` per target** — one system at a time; never batch profiles
   into a single call.
4. **Hand each rendered tree to a build path** — `spacktools`, `spack-build`,
   Ansible, or bare Spack; see `stack_build_handoff_note_v1.md`.
5. **Record outcomes** — keep each `release-manifest.yaml`; optionally record
   what changed for incremental runs.

The driver MUST NOT:

- probe hosts, read `/etc`, or run `module avail` (that is `cluster-inspector`);
- embed package / provider / target policy (that is profile facts + contract +
  templates);
- mutate or hand-edit a rendered tree (fix the inputs and re-render);
- concretize, install, or push buildcaches (that is the build path);
- become a second renderer, or carry state that belongs in the inputs.

These boundaries are the guardrail. Orchestration lives in the driver, not in
`stack-composer`. Letting the loop, change-detection, or policy creep into the
Python tool is exactly the drift this project is correcting.

## Target enumeration

The driver must know which `(system, stack, release)` targets to render.
Provisional options, to confirm during first-system testing:

| Option | How targets are chosen | Trade-off |
|---|---|---|
| Explicit run args | Operator / CI passes system + stack + release per run | Simplest; always available; no extra schema |
| Derived | Render every `(profile, stack)` whose contract+profile intersect non-empty | Convenient but implicit; easy to render more than intended |
| Deployment matrix | A small reviewed file in `stack-content` listing which stacks deploy to which systems at which release | Explicit and reviewable; best once the matrix grows |

No deployment-matrix schema is committed yet. Start with explicit run args for
first-system tests; design a matrix file from real usage if the target set grows
beyond a few entries.

## Open questions

1. **Change detection** — content-hash of inputs, git-diff, or always-render?
   Determinism allows always-render; incremental needs a hash/diff rule owned by
   the driver, not by `stack-composer`.
2. **Release id source and retention** — who allocates `release`, and how does
   `stack.release.retain_previous` interact with the driver's cleanup?
3. **Deployment matrix** — adopt an explicit `stack-content` targets file, or
   keep targets as run args? Decide from first-system scale.
4. **Build hand-off ownership** — does the same driver invoke the build path, or
   stop at render and let a separate build orchestrator pick up the trees?
