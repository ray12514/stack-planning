# First-Deployment Runbook

End-to-end sequence for the first real-hardware runs on Cray and Penguin
systems. Keep one notes file per system and bring reviewed findings back to the
source repositories after each stage.

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
  writable and large enough.

Commit the reviewed profile to the stack source. Preserve probe output for any
fact that required manual correction.

Design references:
`cluster_inspector_stack_profile_design_v1.md` and
`cluster_inspector_profile_extraction_map_v1.md`.

## Stage 2 — Compose

Validate the inputs, then render a deterministic workspace.

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

## Stage 3 — Build

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
generation and `prefix_inspections` policy.

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
