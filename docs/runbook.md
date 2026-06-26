# First Full-Iteration Runbook

Alpha end-to-end sequence for the first real-hardware runs on Cray and
Penguin systems. This is not a production deployment runbook yet. The goal is
to exercise `cluster-inspector`, `stack-composer`, the chosen build path
(`spack-build` or `stack tools`), and Spack on real systems, identify missing
model fields or rendering gaps, and bring those findings back to the source
repositories.

Keep one notes file per system and bring reviewed findings back after each
stage.

## Current readiness

The workflow is ready for controlled full-iteration testing, not for a tagged
v1 release.

| Area | Current status | First-test handling |
|---|---|---|
| System facts | `cluster-inspector` can generate and verify `profile.yaml`; operator hints are expected. | Review the generated profile before render. Hand-edit only with notes that become inspector bugs or schema/design updates. |
| Stack render | `stack-composer` renders lane workspaces and Spack scopes from the stack/profile/template inputs. | Use `validate` and inspect the rendered `configs/` and `environments/` before invoking Spack. |
| Vendor scope selection | The template contract must include `vendor_scope_selectors`; there is no fallback. | Add the selector block to the template contract before render. |
| Install tree / `config.yaml` | Phase 7 is still open. The profile reports filesystem candidates, but the installer chooses the final install tree in `deployment.yaml` (never auto-derived). | For the first test, render or hand-add a temporary `configs/common/config.yaml` with the selected install tree, build stage, source cache, and misc cache. Record the exact shape needed for Phase 7. |
| Module exposure | Phase 9 is still open. Front-door/lane modulefiles are not generated yet. | Use temporary shell/view exposure only. Record required prereqs and MODULEPATH behavior for the module design. |
| MPI provider policy | Phase 6f.2 is still open. Cray MPICH works as the current Cray default, but general `mpi.mode: auto` provider resolution is not complete. | Start with a simple lane whose external MPI/provider behavior is already represented in the profile/template. Record any cross-compiler MPI or non-Cray-provider gaps. |
| Build/cache orchestration | A co-equal build path drives lanes — `stack tools`, `spack-build`, Ansible, or bare Spack; production cache policy may be owned by other site tools. | Pick one build path. With `spack-build`, use `--skip-push` unless this test is explicitly exercising cache publication. |

Because no v1 deployment exists yet, do not preserve compatibility with
previous alpha contract shapes. If a field or layout is wrong, change the
current design/schema/tooling and document the decision.

## Pre-flight

| Item | Target-system expectation |
|---|---|
| `cluster-inspector` | Copy a release binary, or build with Go 1.22 or newer. |
| `stack-composer.pyz` | Build with `scripts/build-pyz.sh`; target Python must be 3.9 or newer. |
| `spack-build` | Use the script shipped in the stack-composer release tarball. |
| Spack | Pin an exact supported release. The current tested floor is 1.1.1; treat 1.2 as an explicit adoption test until its smoke matrix passes. |
| Stack source | Keep `stack.yaml`, `profile.yaml`, templates, package sets, and package repositories in a writable checkout. |

Confirm that `cluster-inspector --help`,
`python3 stack-composer.pyz --help`, and `spack --version` all run before
continuing. Record the Spack version and intended install, view, build-stage,
and buildcache paths in the deployment notes.

Before render, also decide the deployment-owned paths that are not facts:

- selected install tree;
- source cache;
- misc/user cache if used;
- build stage per node type;
- buildcache destination, if this run will push binaries;
- temporary module/view exposure path for the test.

These roots are the installer's choice — recorded in
`systems/<system>/deployment.yaml` and rendered into
`configs/common/config.yaml`, or supplied/overridden at build time. They are
never auto-derived; the profile only offers install-tree candidates. See
`deployment_inputs_and_ownership_v1.md`.

## Stage 0 — Establish the stack directory

Set up the `stack-content` directory before probing. It is the hosted source of
truth render consumes, synced onto the target's shared filesystem.

1. Create (or clone) the `stack-content` repo in the project GitLab group and lay
   out the source tree:

   ```text
   stack-content/
     systems/<system>/profile.yaml      # added in Stage 1
     stacks/<stack>/stack.yaml
     package-sets/*.yaml
     package-repos/<name>/
     templates/<set>/{contract.yaml,stack-defaults.yaml,configs/,environments/}
   ```

2. Decide the config delivery mode for this run:
   - **synced tree** (default): sync `stack-content` to the shared filesystem;
     render emits relative `include::`; the build path roots the rendered tree there.
   - **GitLab-direct**: render emits remote GitLab-URL `include::`; Spack reads
     config yaml directly from GitLab with no sync. Validate the remote-include
     syntax against the pinned Spack version first.

3. Confirm the shared-filesystem path is writable and visible from the build and
   compute node types.

Design references: `pre_v1_hosting_and_external_inventory_note_v1.md` and
`stack_build_handoff_note_v1.md`.

## Stage 1 — Probe

Produce a reviewed `profile.yaml` from the login node. Select a runner and role
for every node type used by the stack.

```bash
./cluster-inspector profile \
  --system <system-name> \
  --node-type login=this:role=both \
  --node-type compute=srun:role=runtime \
  --node-type build=srun:role=build_host \
  --hints ./inspector-hints.yaml \
  --output profile.yaml
```

To inspect fragments before merging them:

```bash
./cluster-inspector probe-system \
  --system <system-name> \
  --hints ./inspector-hints.yaml \
  --output system.frag.yaml
./cluster-inspector probe-node \
  --node-type login --role both --runner this --output login.frag.yaml
./cluster-inspector probe-node \
  --node-type compute --role runtime --runner srun --output compute.frag.yaml
./cluster-inspector probe-node \
  --node-type build --role build_host --runner srun --output build.frag.yaml
./cluster-inspector merge \
  --system-fragment system.frag.yaml \
  --node login.frag.yaml \
  --node compute.frag.yaml \
  --node build.frag.yaml \
  --output profile.yaml
./cluster-inspector verify profile.yaml
```

Manual review checklist:

- `vendor_cray` and CPE family fields match the live module tree.
- `gpu_toolkit_modules` names the exact ROCm or CUDA modules intended as
  externals.
- `compilers_external` contains only the compilers intended for lanes, with
  correct versions, executable paths, and module prerequisites.
- MPI externals contain the expected providers, prefixes, and module
  prerequisites.
- Module patterns in the hints and discovery evidence match the live system.
- `filesystem.install_tree_candidates` and node build-stage candidates are
  writable and large enough. These are candidates/facts, not the final install
  policy.

Commit the reviewed profile to the stack source. Preserve probe output for any
fact that required manual correction.

Design references:
`cluster_inspector_stack_profile_design_v1.md` and
`cluster_inspector_profile_extraction_map_v1.md`.

## Stage 2 — Compose

Validate the inputs, then render a deterministic workspace. Confirm the selected
template contract contains `vendor_scope_selectors`; missing selectors are a
contract error.

```bash
python3 stack-composer.pyz validate \
  --profile ./profile.yaml \
  --stack ./stack.yaml \
  --templates ./templates \
  --package-sets ./package-sets \
  --package-repos ./package-repos \
  --report validation-report.yaml

python3 stack-composer.pyz render \
  --profile ./profile.yaml \
  --stack ./stack.yaml \
  --templates ./templates \
  --package-sets ./package-sets \
  --package-repos ./package-repos \
  --output-root ./rendered \
  --release <release-id> \
  --rendered-at <UTC-timestamp> \
  --source-repo <source-repository> \
  --source-commit <source-commit>
```

The workspace is
`rendered/<system>/<stack>/<release>/`. Inspect:

- `release-manifest.yaml` for version pins and the complete lane plan.
- `environments/<compiler>/<lane>/spack.yaml` for every planned lane.
- `configs/` for the common, compiler, MPI, GPU, and vendor scopes referenced
  by those environments.
- `configs/**/packages.yaml` for correct external prefixes, module
  prerequisites, and `buildable: false` policy where required.
- Core lanes for each compiler. In the committed v1 model, payload lanes do
  not include another environment's lockfile; foundation reuse is supplied by
  the buildcache and `concretizer:reuse: true`.

Front-door and lane module emission is Phase 9 work. No generated modulefiles
are expected from the current renderer.

Until Phase 7 renders `configs/common/config.yaml`, verify whether the rendered
workspace contains the selected deployment paths. If it does not, add the
temporary `config.yaml` scope for this test and record it as Phase 7 evidence.
The temporary file should include only deployment-owned path policy and should
not be committed as generated output.

Alternatively, pass the install/view/module/cache roots to the build path at
build time instead of rendering them; the handoff supports both. Record which
mode this run used as Phase 7 evidence.

## Stage 3 — Build

Build is a **co-equal choice** of build path — `stack tools`, `spack-build`,
Ansible, or bare Spack. Pick the one this site will operate. The example below
uses the in-house `spack-build`; to hand off to `stack tools` instead, give it
the rendered workspace tree (or the GitLab-direct config URLs) and let it run
concretize + install. See `stack_build_handoff_note_v1.md`.

Run one Core lane end to end before queueing the remaining lanes. Build all
Core lanes before serial, MPI, and GPU payload lanes so their artifacts can be
reused from the configured buildcache.

```bash
./spack-build \
  --workspace rendered/<system>/<stack>/<release> \
  --spack-root "$SPACK_ROOT" \
  --lanes '<compiler>/<lane>' \
  --reports reports/ \
  --fail-fast
```

Use repeatable `--buildcache NAME=URL` options when this run is responsible for
pushing artifacts. Use `--skip-push` when another approved build/cache tool
owns publication.

Monitor concretizer diagnostics, buildcache hits, source builds, install
prefixes, and lane reports. An unsatisfiable lane is usually an input,
template, or profile mismatch; preserve the complete solver output before
changing inputs or attributing the failure to Spack.

## Stage 4 — Temporary exposure

Until Phase 9 implements front-door and lane modules, use the view paths
recorded in `release-manifest.yaml` through a local, non-published shell helper:

```bash
export VIEW_ROOT=<lane-view-from-release-manifest>
export PATH="$VIEW_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$VIEW_ROOT/lib:$VIEW_ROOT/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export MANPATH="$VIEW_ROOT/share/man${MANPATH:+:$MANPATH}"
```

Do not treat this helper as the final user interface. Record any additional
paths needed by real applications; they are evidence for Phase 9 module
generation, platform-module prerequisite handling, and `prefix_inspections`
policy.

## Stage 5 — Validate end to end

Run at least these checks for every applicable lane:

| Check | Example |
|---|---|
| Compiler or wrapper resolves from the intended lane | `which mpicc && mpicc --version` |
| MPI launcher works on compute nodes | `srun -n 2 hostname` |
| GPU runtime is visible on a GPU node | `srun rocm-smi` or `srun nvidia-smi` |
| Representative application runs | Use the stack's existing smoke workload. |

Capture failures before applying temporary environment changes. Correct
discovery errors in the profile and rendering errors in the templates or stack
input.

## Bring findings back

| Artifact | Destination |
|---|---|
| Reviewed `profile.yaml` | Stack source under `profiles/<system>.yaml`. |
| Probe defects and regression fixtures | `cluster-inspector`. |
| Known-good rendered fixtures and renderer defects | `stack-composer`. |
| Design gaps and accepted policy changes | `stack-planning/docs/`. |
| Build, solver, cache, and temporary exposure notes | Deployment record plus the relevant implementation issue. |

Use one merge or pull request per repository and concern. Include the system,
date, exact tool versions, and evidence paths in its description. Do not edit
generated release assets directly.
