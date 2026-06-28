# End-To-End Map v1

The single point-A-to-point-B map: every input, who produces it, every output,
who consumes it, the tools that do the work, the synchronization step, and what
is hand-done the first time versus continuously updated.

This is the consolidated overview. For depth, follow the cross-references:

- commands for a first run → `runbook.md`;
- the multi-system loop and re-render cadence → `stack_generation_orchestration_note_v1.md`;
- the rendered tree → build-path handoff → `stack_build_handoff_note_v1.md`;
- repository hosting and the `stack-content` layout → `pre_v1_hosting_and_external_inventory_note_v1.md`;
- the render model (defaults, providers, resolution) → `stack_generation_structure_v1.md`;
- per-stack workspaces and the shared install tree → `stack_workspace_lifecycle_v1.md`.

No v1 stack release has been deployed yet. This map is changeable pre-v1.

## Actors and tools

| Actor / tool | Role |
|---|---|
| `cluster-inspector` (Go binary) | Probes one system; produces `profile.yaml`. Read-only facts; never decides policy. |
| Template maintainer | Curates the supported vocabulary: `templates/<set>/` (defaults, configs, environments). |
| Package manager | Authors stack intent: `stacks/<stack>/stack.yaml`, optional `package-sets/`. |
| Installer | Chooses the site paths in `systems/<system>/deployment.yaml`: install tree, caches, view/module roots, `publish_root`. Often the same person as the package manager. |
| `stack-content` (GitLab repo) | The hosted source of truth render consumes; synced to each target's shared filesystem. |
| Driver (Make / CI / Ansible / shell) | Thin, external. Loops render over targets and hands trees to a build path. Owns no policy. See orchestration note. |
| `stack-composer` (Python `.pyz`) | Validates inputs, resolves intent, renders the workspace tree. Never calls Spack. |
| Build path | One of: `spacktools`, `spack-build`, Ansible, bare Spack. Concretizes + installs the rendered tree. |
| Spack | The concretizer/installer the build path drives. |

## The flow (master table)

`P` = produced once and re-touched only on change; `C` = continuous / on every change.

| # | Stage | Input(s) | Producer / owner | Tool | Output | Consumed by | Cadence |
|---|---|---|---|---|---|---|---|
| 0 | Set up the stack directory | layout decision | Maintainer | git / GitLab | empty `stack-content` repo skeleton | render, driver | **first-time, hand-done** · P |
| 1 | Probe each system | the live system | System owner | `cluster-inspector` | `systems/<system>/profile.yaml` | render | hand-reviewed first time; re-run on system change · P |
| 2 | Curate template set | observed patterns | Template maintainer | hand-authored, checked with `validate-template-set` | `templates/<set>/{defaults,configs,environments}` | render | hand-done; rare (new OS/MPI/GPU/compiler) · P |
| 3 | Author stack intent | package needs | Package manager | editor | `stacks/<stack>/stack.yaml` (+ `package-sets/`) | render | hand-done; **most frequent** · C |
| 4 | Sync source to shared FS | `stack-content` (GitLab) | Driver / CI | `git clone`/`pull` (or GitLab-direct, no sync) | `stack-content` on shared FS (or remote URLs) | render | automatable from day one · C |
| 5 | Render | profile + stack + templates + package-sets + **`deployment.yaml`** | Driver invokes | `stack-composer render` | rendered workspace tree: `configs/**`, `environments/**/spack.yaml`, `release-manifest.yaml` | build path | automatable; re-render on any input change · C |
| 6 | Build + concretize | rendered workspace tree | Site | a build path (`spacktools` / `spack-build` / Ansible / bare Spack) | install tree, `spack.lock` per lane, buildcache | Spack, users | first run validated by hand; then automatable · C |
| 7 | Expose | installed lanes + manifest | Site / publish | `stack-composer publish-manifest` + module/view emission | modules, views, final manifest, `current` symlink | users | per release · C |
| 8 | Validate | installed lanes | Operator | smoke tests | pass/fail evidence | release record | per release · C |

The `spack.yaml` you asked about is the **stage-5 output** (`environments/<compiler>/<lane>/spack.yaml`). It is generated, not hand-written — produced by render from stages 1–3, then consumed by the build path at stage 6.

The install tree, caches, view/module roots, and module `publish_root` are **not** auto-derived. The installer chooses them in `systems/<system>/deployment.yaml` (the profile offers only candidates); build-time flags can override. See `deployment_inputs_and_ownership_v1.md`.

## Worked example: `example-cray` / ScienceStack `2026.06`

A Cray-class system (RHEL8, Slingshot/CXI, AMD MI250X `gfx90a` + MI300A `gfx942`).

**Stage 0 — stack directory (once).** Create `stack-content` in the project
GitLab group with the source skeleton (`systems/`, `stacks/`, `package-sets/`,
`templates/v6/`). Sync target: a shared filesystem path visible to build +
compute nodes.

**Stage 1 — profile (per system).** On the login node:

```bash
cluster-inspector profile --system example-cray \
  --hints systems/example-cray/inspector-hints.yaml \
  --node-type login=this:role=build_host \
  --node-type gpu_compute_mi250x=srun:partition=gpu,constraint=mi250x:role=runtime \
  --output systems/example-cray/profile.yaml
```

Output: `profile.yaml` listing `cce@17.0.1`, `gcc-native@13`, `rocmcc@6.0.0`,
`cray-mpich@8.1.29`, `rocm@6.0.0`, fabric, filesystem candidates. **Hand-reviewed
the first time**, committed to `stack-content`. Producer: `cluster-inspector`.
Consumer: render.

**Stage 2 — template set (rare).** `templates/v6/defaults.yaml` is the site
policy (selection + conventions); `configs/*.j2` are the Spack component
templates. Maintained by the template owner; changes only when
adding new support. Consumer: render.

**Stage 3 — stack intent (frequent).** `stacks/science-stack/stack.yaml` names
`templates.set: v6`, the builds (core/serial/mpi/gpu), and the specs (or a
`package_set`). This is the file that actually churns — package adds and version
bumps. Producer: package manager. Consumer: render.

**Stage 4 — sync.** The driver makes the reviewed `stack-content` available where
render runs:

- *synced tree (default):* `git pull` onto the shared filesystem; render emits
  relative `include::`.
- *GitLab-direct:* render emits remote GitLab-URL `include::`; Spack reads config
  yaml from GitLab with no local sync (validate the syntax against the pinned
  Spack floor first).

**Stage 5 — render (the `spack.yaml` appears).** The driver invokes:

```bash
stack-composer render \
  --profile systems/example-cray/profile.yaml \
  --deployment systems/example-cray/deployment.yaml \
  --stack   stacks/science-stack/stack.yaml \
  --templates templates --package-sets package-sets \
  --output-root <shared-fs>/rendered --release 2026.06
```

Output tree `<shared-fs>/rendered/example-cray/science-stack/2026.06/`:
`environments/cce/mpi-craympich/spack.yaml` (and the other lanes) +
`configs/**` + `release-manifest.yaml`. Only the lanes in
`profile ∩ deployment ∩ defaults ∩ stack` are emitted. This tree is a
**regeneratable build artifact** — it persists on the shared FS but is rebuilt
from inputs, not committed. Producer: `stack-composer`. Consumer: the build path.

**Stage 6 — build (co-equal choice).** Hand the tree to one build path:

```bash
# in-house local path
spack-build --workspace <shared-fs>/rendered/example-cray/science-stack/2026.06 \
  --spack-root "$SPACK_ROOT"
# or hand the same tree (or its GitLab-direct URLs) to `spacktools`,
# or drive it from Ansible, or run bare `spack -e <env> install`.
```

Output: install tree, `spack.lock` per lane, buildcache. **First run validated by
hand; then automatable.** Consumer: Spack, then users.

**Stages 7–8 — expose + validate.** `publish-manifest` finalizes the manifest;
modules/views expose the lanes; smoke tests confirm `mpicc`, `srun`, GPU runtime,
and a representative app. Per release.

## First time vs. continuous

| Hand-done the first time | Continuously updated (automatable) |
|---|---|
| Create `stack-content` (stage 0) | Sync source → shared FS (stage 4) |
| Review the first `profile.yaml` per system (stage 1) | Render on any input change (stage 5) |
| Curate the template set (stage 2) | Build changed lanes (stage 6) |
| Validate the first build by hand (stage 6) | Expose + validate per release (stages 7–8) |
| | Re-probe only when a system changes (stage 1) |

After the first proven run, the steady state is: edit `stack.yaml` → driver syncs
+ re-renders the affected systems → build path rebuilds changed lanes. Profiles
and templates sit until a system or support change forces a touch.

## Where the boundaries hold

- Facts come from `cluster-inspector`; policy from defaults + stack + templates;
  rendering from `stack-composer`; building from a build path. No stage reaches
  into another's job (see the orchestration note's driver MUST-NOT list).
- The rendered tree is regeneratable, not source. Back up the `stack-content`
  inputs (GitLab) and the reproducibility artifacts (lockfiles, manifest,
  buildcache) — not the workspace.
