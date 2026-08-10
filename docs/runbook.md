# CSE Static Pilot Runbook

## Purpose

This is the single operator procedure for Blueback, Raider, Wheat, and Fran.
Run it once per system to produce a complete Spack 1.2 pilot workspace and
reach the build handoff.

```text
cluster-inspector
  -> reviewed systems/<system>/profile.yaml
  -> stack-composer render-static
  -> versioned platform catalog
  -> reviewed systems/<system>/cse-pilot-values.yaml
  -> stack-composer init-workspace
  -> Core/Common/Serial/MPI/GPU environments
  -> concretize all environments
  -> build Core, Common, Serial, MPI, GPU
```

This is the current pre-v1 workflow. There is no parallel legacy procedure.
`render-static` creates reusable platform configuration scopes; it does not
create a complete environment. `init-workspace` combines an exact catalog
selection with the CSE pilot blueprint to create the buildable environments.

## Pilot order

| Order | System | Known family | Current local record |
|---:|---|---|---|
| 1 | Blueback | Cray PE, Slurm, ROCm | Detailed system notes and deployment example |
| 2 | Raider | Generic Linux, Slurm, CUDA | Detailed system notes |
| 3 | Wheat | Generic Linux, PBS | Create from the system-note template |
| 4 | Fran | Cray PE; scheduled later | Create from the system-note template |

The table selects the platform checklist, not provider versions. Every
compiler, MPI, GPU, prefix, and module value must come from the live system's
reviewed profile and generated catalog.

## Pilot storage and control policy

During the pilot, keep the tools and editable source under the pilot operator's
control in the operator's home directory. Put reviewed generated outputs and
the state needed to build or run packages in the CAC-group shared area.

```text
$HOME/STACK_TESTING/                         # operator-controlled
  cluster-inspector/                         # source + built binary
  stack-composer/                            # source + built pyz/spack-build
  stack-content/                             # editable pilot inputs
  stack-planning/                            # current runbook/design
  spack/<version>/                           # optional operator-controlled Spack clone
  probe-work/<system>/<catalog-release>/     # raw fragments/transcripts

<cac-pilot-root>/                            # CAC-group shared filesystem
  catalogs/<system>/static/<catalog-release>/
  workspaces/<system>/cse-pilot/<pilot-release>/
    inputs/                                  # reviewed input snapshot
    environments/                            # includes durable spack.lock files
    configs/
    modulefiles/
  spack/opt/                                 # shared Spack install tree
  cache/source/                              # reusable source cache
  cache/misc/                                # reusable Spack metadata cache
  views/                                     # generated views
  modules/                                   # generated package module trees
  buildcache/                                # only when publication is approved
  evidence/<system>/<pilot-release>/         # logs and acceptance evidence

<node-local-or-site-scratch>/
  <user>/<system>/<pilot-release>/spack-stage/  # disposable build stage
```

The repository clones, executables, raw probe transcripts, and unreviewed
inputs are not shared pilot products. Cluster Inspector and Stack Composer run
from the operator's home checkout. A Cluster Inspector binary may be copied
temporarily into an allocation when the home filesystem is not visible there;
that does not make it a group-installed tool.

The shared catalog and workspace are generated directly at their final paths.
Do not generate them in `$HOME` and move them afterward: catalog manifests and
initialized environments contain absolute catalog/workspace paths. Moving a
tree makes those paths wrong.

The static catalog becomes read-only after review. The initialized workspace
stays operator-writable through concretization because Spack writes
`spack.lock` into each environment, then becomes read-only after the release
record is complete. For the operator-controlled pilot, the CAC group can read
and execute shared outputs but only the operator writes them. Use
`permissions.group: <CAC Unix group>`, `permissions.read: group`, and
`permissions.write: user` in the values file. Change to group-write only when
another approved builder actually needs it.

The exact Unix group name and shared root are site decisions. The examples use
`CAC_GROUP` and `CAC_PILOT_ROOT`; replace them with approved values rather than
assuming that the display name `CAC` is the Unix group name.

## Build-readiness gates

Do not install packages until every gate is green.

- [ ] All four repositories are synchronized on
  `codex/simplified-render-plan`.
- [ ] Freshly built Cluster Inspector and Stack Composer artifacts run.
- [ ] The selected Spack is version 1.2 or newer.
- [ ] `profile.yaml` verifies and matches the live system.
- [ ] The static catalog contains one compatible compiler/MPI/GPU tuple.
- [ ] `cse-pilot-values.yaml` names only real catalog scopes and approved
  deployment paths.
- [ ] `init-workspace` generates five environments and five native
  `modules.yaml` files.
- [ ] All five environments concretize and their lockfiles pass review.

The final gate is the handoff into the build process.

## 1. Set the system values

Start a clean Bash login shell on the target system. Use a lowercase system
name: `blueback`, `raider`, `wheat`, or `fran`.

```bash
export WORK_ROOT="$HOME/STACK_TESTING"
export SYSTEM_NAME="<system>"
export STACK_BRANCH="codex/simplified-render-plan"
export CATALOG_RELEASE="<system>-catalog-001"
export PILOT_RELEASE="<system>-pilot-001"
export CAC_GROUP="<approved-cac-unix-group>"
export CAC_PILOT_ROOT="<approved-shared-path>/cse-pilot"

export INSPECTOR="$WORK_ROOT/cluster-inspector"
export COMPOSER="$WORK_ROOT/stack-composer"
export CONTENT="$WORK_ROOT/stack-content"
export PLANNING="$WORK_ROOT/stack-planning"
export SYSTEM_DIR="$CONTENT/systems/$SYSTEM_NAME"
export PROBE_DIR="$WORK_ROOT/probe-work/$SYSTEM_NAME/$CATALOG_RELEASE"
export STATIC_ROOT="$CAC_PILOT_ROOT/catalogs"
export WORKSPACE_ROOT="$CAC_PILOT_ROOT/workspaces"
export EVIDENCE_ROOT="$CAC_PILOT_ROOT/evidence/$SYSTEM_NAME/$PILOT_RELEASE"
export STACK_COMPOSER="$COMPOSER/dist/stack-composer.pyz"
export CATALOG="$STATIC_ROOT/$SYSTEM_NAME/static/$CATALOG_RELEASE"
export WORKSPACE="$WORKSPACE_ROOT/$SYSTEM_NAME/cse-pilot/$PILOT_RELEASE"

mkdir -p "$WORK_ROOT" "$PROBE_DIR"
```

Do not create files below a repository path until that repository has been
cloned. Step 6 creates the shared roots with the approved group and modes.

## 2. Acquire and synchronize the repositories

Clone missing repositories as siblings. HTTPS is the default on HPC login
nodes because SSH keys may not be installed there.

```bash
if [ ! -d "$INSPECTOR/.git" ]; then
  git clone https://github.com/ray12514/cluster-inspector.git "$INSPECTOR"
fi
if [ ! -d "$COMPOSER/.git" ]; then
  git clone https://github.com/ray12514/stack-composer.git "$COMPOSER"
fi
if [ ! -d "$CONTENT/.git" ]; then
  git clone https://github.com/ray12514/stack-content.git "$CONTENT"
fi
if [ ! -d "$PLANNING/.git" ]; then
  git clone https://github.com/ray12514/stack-planning.git "$PLANNING"
fi
```

Review local state before switching branches:

```bash
for repo in cluster-inspector stack-composer stack-content stack-planning; do
  git -C "$WORK_ROOT/$repo" status --short --branch
done
```

Stop if a repository contains local work you have not reviewed. When the state
is understood, synchronize all four repositories:

```bash
for repo in cluster-inspector stack-composer stack-content stack-planning; do
  git -C "$WORK_ROOT/$repo" fetch origin
  git -C "$WORK_ROOT/$repo" switch "$STACK_BRANCH"
  git -C "$WORK_ROOT/$repo" pull --ff-only
done
```

Create the system record after Stack Content exists:

```bash
mkdir -p "$SYSTEM_DIR"
if [ ! -f "$SYSTEM_DIR/runbook-notes.md" ]; then
  cp "$CONTENT/systems/_template/runbook-notes.md" "$SYSTEM_DIR/runbook-notes.md"
fi
```

Record the system, releases, branch, and work paths in the system notes.

## 3. Build and verify the tools

Build Cluster Inspector with Go 1.22 or newer:

```bash
cd "$INSPECTOR"
make build
./cluster-inspector --help >/dev/null
```

Build Stack Composer in its repository-local Python environment:

```bash
cd "$COMPOSER"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
PYTHON=.venv/bin/python bash scripts/build-pyz.sh
python "$STACK_COMPOSER" --help >/dev/null
deactivate
```

Activate the exact Spack checkout selected for the pilot:

```bash
source /path/to/spack/share/spack/setup-env.sh
: "${SPACK_ROOT:?SPACK_ROOT is not set}"
spack --version
```

The pilot workspace uses Spack 1.2 `group` and `needs`; stop if the selected
Spack is older than 1.2. Record the Go, Python, Stack Composer, Spack, and
module-tool versions in the system notes.

For this operator-controlled pilot, a pinned Spack checkout may live under
`$WORK_ROOT/spack/<version>`. A site-provided Spack module is also acceptable.
The Spack tool location is distinct from the CAC-shared `spack/opt` install
tree where built packages land.

## 4. Generate and review `profile.yaml`

Use the fragment workflow for the first run on a system. It makes the node that
produced each fact explicit.

On the login node:

```bash
cd "$PROBE_DIR"
HINTS_OPTION=()
if [ -f "$SYSTEM_DIR/inspector-hints.yaml" ]; then
  HINTS_OPTION=(--hints "$SYSTEM_DIR/inspector-hints.yaml")
fi

"$INSPECTOR/cluster-inspector" probe-system \
  --system "$SYSTEM_NAME" \
  "${HINTS_OPTION[@]}" \
  --record "$PROBE_DIR/system-probe-transcript.yaml" \
  --output "$PROBE_DIR/system.frag.yaml"

"$INSPECTOR/cluster-inspector" probe-node \
  --node-type login \
  --role both \
  --runner this \
  --output "$PROBE_DIR/login.frag.yaml"
```

Allocate or log into each distinct compute, GPU, and build node type. Run this
on the allocated node, changing the name and role to match reality:

```bash
"$INSPECTOR/cluster-inspector" probe-node \
  --node-type <node-type-name> \
  --role <runtime|build_host|both> \
  --runner this \
  --output <node-type-name>.frag.yaml
```

Copy every node fragment back to `$PROBE_DIR`. Wheat uses PBS rather than
Slurm, but `--runner this` is unchanged after entering the allocation.

Merge the system fragment and every unique node fragment. Adjust the example
to the node types that actually exist:

```bash
"$INSPECTOR/cluster-inspector" merge \
  --system-fragment "$PROBE_DIR/system.frag.yaml" \
  --node "$PROBE_DIR/login.frag.yaml" \
  --node "$PROBE_DIR/compute.frag.yaml" \
  --node "$PROBE_DIR/gpu.frag.yaml" \
  --output "$PROBE_DIR/profile.yaml"

"$INSPECTOR/cluster-inspector" verify "$PROBE_DIR/profile.yaml"
```

Omit nonexistent node types and add every additional real node type.

Review the profile against the live machine:

- compiler names, versions, prefixes, modules, languages, and provider family;
- MPI names, versions, prefixes/flavors, modules, and compiler compatibility;
- CUDA or ROCm versions, prefixes, modules, and GPU architecture;
- fabric and platform runtime externals;
- login, build, CPU-runtime, and GPU-runtime node roles;
- every missing, unknown, or ambiguous fact required by the pilot.

On Cray systems, select one coherent CPE/compiler/Cray MPICH/GPU runtime set.
On generic Linux systems, prove that the selected MPI was built with the
selected compiler. Preserve the transcript when discovery is wrong, fix the
inspector or hints, and regenerate the profile. Do not hand-enter a guess as a
durable fact.

After review, copy only the verified fact sheet into the editable Stack Content
checkout. Keep raw fragments and transcripts in the personal probe directory:

```bash
cp "$PROBE_DIR/profile.yaml" "$SYSTEM_DIR/profile.yaml"
```

Gate: `profile.yaml` verifies and the system notes identify the reviewed
compiler/MPI/GPU tuple.

## 5. Generate and inspect the static catalog

Before rendering, confirm `CAC_GROUP` and `CAC_PILOT_ROOT` with the filesystem
owner. Use an operator-write/group-read umask and setgid directories so every
artifact inherits the CAC group without granting group write:

```bash
umask 0027

install -d -m 2750 -g "$CAC_GROUP" \
  "$CAC_PILOT_ROOT" \
  "$STATIC_ROOT" \
  "$WORKSPACE_ROOT" \
  "$CAC_PILOT_ROOT/spack/opt" \
  "$CAC_PILOT_ROOT/cache/source" \
  "$CAC_PILOT_ROOT/cache/misc" \
  "$CAC_PILOT_ROOT/views" \
  "$CAC_PILOT_ROOT/modules" \
  "$CAC_PILOT_ROOT/evidence" \
  "$EVIDENCE_ROOT"
```

Do not recursively change ownership or permissions on a pre-existing shared
tree without approval from its owner. If a later phase authorizes multiple CAC
builders, change the dedicated working roots to the site's approved group-write
mode/default ACL as a deliberate policy update.

```bash
python "$STACK_COMPOSER" render-static \
  --profile "$SYSTEM_DIR/profile.yaml" \
  --templates "$CONTENT/templates" \
  --template-set v6 \
  --output-root "$STATIC_ROOT" \
  --release "$CATALOG_RELEASE" \
  --rendered-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --source-repo "stack-content" \
  --source-commit "$(git -C "$CONTENT" rev-parse HEAD)"
```

Add `--source-dirty` when reviewed system inputs are not yet committed. Use
`--overwrite` only when deliberately regenerating the same catalog release.

Expected output:

```text
<static-root>/<system>/static/<catalog-release>/
  README.md
  manifest.yaml
  reports/static-plan.yaml
  scopes/common/
  scopes/compilers/<compiler>/<version>/
  scopes/mpi/<provider>/<version>/<compiler-version>/
  scopes/gpu/<provider>/<version>/
  scopes/platform/<provider-family>/       # when present
```

Inspect it:

```bash
cat "$CATALOG/README.md"
sed -n '1,260p' "$CATALOG/manifest.yaml"
sed -n '1,320p' "$CATALOG/reports/static-plan.yaml"
find "$CATALOG/scopes" -type f | sort
```

For the intended tuple, inspect every `packages.yaml` and `toolchains.yaml`.
Confirm external specs, prefixes, modules, compiler stamps, MPI requirements,
and GPU packages against the reviewed profile.

Gate: the catalog contains one exact compiler scope, one compatible MPI scope,
and the required common, GPU, and platform scopes. If a required scope is
missing, fix the profile or catalog logic; do not type a nonexistent path into
the next input.

## 6. Choose the disposable build stage

Choose a node-local or site scratch build stage, for example:

```text
<site-scratch>/<user>/<system>/<pilot-release>/spack-stage
```

Create it in the build allocation or through the site's normal scratch
procedure. It is disposable and should not be placed in the durable CAC release
tree unless the site requires a shared build stage.

## 7. Create `cse-pilot-values.yaml`

```bash
cp "$CONTENT/pilots/cse-pilot/site-values.example.yaml" \
  "$SYSTEM_DIR/cse-pilot-values.yaml"
```

Edit the copy. Use only facts and scope paths from the current catalog.

| Values | Source |
|---|---|
| system and release | profile/catalog plus `PILOT_RELEASE` |
| compiler name, version, modules | selected compiler scope and static plan |
| compiler toolchain | local spec-safe name, for example `cse_gcc1430` |
| MPI name, version, modules | compatible MPI scope and static plan |
| MPI toolchain | local spec-safe name, for example `cse_gcc1430_craympich910` |
| GPU provider, version, modules, architecture | selected GPU scope and live node |
| `catalog_scopes.*` | exact relative paths under `$CATALOG` |
| install tree | `$CAC_PILOT_ROOT/spack/opt` |
| source/misc caches | `$CAC_PILOT_ROOT/cache/{source,misc}` |
| views/modules roots | `$CAC_PILOT_ROOT/{views,modules}` |
| build stage | selected node-local or site scratch path |
| permissions | `group: CAC_GROUP`, `read: group`, `write: user` for this operator-controlled pilot |
| package-repository generation | reviewed pilot recipe pin |

Toolchain names may contain only letters, digits, and underscores. Their
versions must match the selected catalog tuple.

Use `source: external` for the recommended first platform surface. A deliberate
`source: build` experiment still needs real reference catalog paths under the
current pilot values contract; never enter dummy paths. If no supported GPU
tuple exists, stop—the current blueprint always creates a GPU environment and
must not be filled with a fake scope.

Record the selected tuple and paths in the system notes.

## 8. Initialize and inspect the complete workspace

```bash
python "$STACK_COMPOSER" init-workspace \
  --blueprint "$CONTENT/pilots/cse-pilot" \
  --catalog "$CATALOG" \
  --values "$SYSTEM_DIR/cse-pilot-values.yaml" \
  --output "$WORKSPACE"
```

Use `--overwrite` only after reviewing and deliberately replacing the existing
workspace.

Expected output:

```text
<workspace>/
  README.md
  workspace-manifest.yaml
  configs/common/
  configs/providers/
  configs/environments/<compiler>/{core,common,serial,mpi-*,gpu-*}/modules.yaml
  environments/<compiler>/{core,common,serial,mpi-*,gpu-*}/spack.yaml
  modulefiles/cse/<Compiler>
  modulefiles/<compiler>/lanes/{Serial,MPI,GPU}
```

Inspect it:

```bash
cat "$WORKSPACE/README.md"
sed -n '1,260p' "$WORKSPACE/workspace-manifest.yaml"
find "$WORKSPACE/environments" -name spack.yaml -print | sort
find "$WORKSPACE/configs/environments" -name modules.yaml -print | sort
find "$WORKSPACE/modulefiles" -type f -print | sort
```

Verify that every `include::` path exists, every environment selects the
reviewed providers, Serial has no MPI scope, MPI and GPU share the compatible
MPI tuple, and `config.yaml` contains the approved roots.

The values file and pilot blueprint are source. Regenerate after changing them;
do not patch the generated workspace as a second source of truth.

Gate: five `spack.yaml` files and five matching `modules.yaml` files exist and
all selected paths/providers are correct.

Snapshot the reviewed inputs and tool/source identities beside the generated
workspace so the CAC-shared release can be audited without access to mutable
files in the operator's home directory:

```bash
mkdir -p "$WORKSPACE/inputs"
cp "$SYSTEM_DIR/profile.yaml" "$WORKSPACE/inputs/profile.yaml"
cp "$SYSTEM_DIR/cse-pilot-values.yaml" "$WORKSPACE/inputs/cse-pilot-values.yaml"
cp "$CATALOG/manifest.yaml" "$WORKSPACE/inputs/catalog-manifest.yaml"
cp "$CATALOG/reports/static-plan.yaml" "$WORKSPACE/inputs/static-plan.yaml"
git -C "$INSPECTOR" rev-parse HEAD > "$WORKSPACE/inputs/cluster-inspector.commit"
git -C "$COMPOSER" rev-parse HEAD > "$WORKSPACE/inputs/stack-composer.commit"
git -C "$CONTENT" rev-parse HEAD > "$WORKSPACE/inputs/stack-content.commit"
spack --version > "$WORKSPACE/inputs/spack.version"
```

These copies are evidence, not another editable source tree. Correct the home
checkout and regenerate when an input changes.

## 9. Concretize all environments before installing

Set the exact names from `cse-pilot-values.yaml`:

```bash
export COMPILER_NAME="<compiler-name>"
export MPI_NAME="<mpi-name>"
export GPU_LANE_SUFFIX="<gpu-lane-suffix>"

ENVIRONMENTS=(
  "$COMPILER_NAME/core"
  "$COMPILER_NAME/common"
  "$COMPILER_NAME/serial"
  "$COMPILER_NAME/mpi-$MPI_NAME"
  "$COMPILER_NAME/gpu-$MPI_NAME-$GPU_LANE_SUFFIX"
)
```

Concretize every environment without installing:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  echo "Concretizing $environment"
  spack -e "$WORKSPACE/environments/$environment" concretize --force -j 1 || break
done
```

Review every lock:

```bash
for environment in "${ENVIRONMENTS[@]}"; do
  test -f "$WORKSPACE/environments/$environment/spack.lock" || break
  spack -e "$WORKSPACE/environments/$environment" find -lv
done
```

Required checks:

- Serial contains no MPI implementation.
- Selected external compiler, MPI, GPU, and runtime packages use their intended
  prefixes and are not proposed for download/build.
- Producer groups appear only for providers intentionally set to `build`.
- MPI and GPU roots use the selected compatible toolchain.
- Version-paired HDF5/NetCDF roots preserve their intended pairings.
- No environment selects an unexpected compiler or provider.

Save solver output for any failure and fix the owning profile, catalog, values,
roster, or blueprint. Do not repair a lock by editing generated files.

Gate: all five lockfiles exist and pass review. The system is ready to build.

## 10. Build in dependency order

Build Core, Common, Serial, MPI, then GPU:

```bash
export BUILD_JOBS="<approved-job-count>"

for environment in "${ENVIRONMENTS[@]}"; do
  echo "Building $environment"
  spack -e "$WORKSPACE/environments/$environment" fetch -D || break
  spack -e "$WORKSPACE/environments/$environment" install -j "$BUILD_JOBS" || break
  spack -e "$WORKSPACE/environments/$environment" env view regenerate || break
  spack -e "$WORKSPACE/environments/$environment" \
    module tcl refresh --delete-tree -y || break
done
```

Do not push a build cache during the first pass unless publication is an
explicit objective and its ownership has been approved.

After installation, exercise the generated module hierarchy from clean shells:

```bash
module use "$WORKSPACE/modulefiles"
module load "cse/<Compiler-public-name>"
module avail
module load Serial
```

Repeat separately for `MPI` and `GPU`. Loading a second conflicting lane must
fail. Apply `cray_pe_acceptance_checklist_v1.md` on Cray PE systems and
`generic_linux_acceptance_checklist_v1.md` on generic Linux systems. Record
build logs, package-module visibility, single-node and multi-node runtime
results, and GPU-aware MPI behavior in the system notes.

## Artifact ownership

| Artifact | Treatment |
|---|---|
| Tool/source checkouts and built executables | Operator home; mutable and operator-controlled |
| Raw probe fragments/transcripts | Operator home under `probe-work`; review before sharing |
| `profile.yaml`, values, system notes | Editable operator checkout; snapshot reviewed inputs into the shared workspace |
| static catalog | CAC-shared, versioned, generated directly at its final absolute path |
| initialized workspace | CAC-shared build input; writable through lock generation, then frozen |
| `spack.lock` and workspace `inputs/` | CAC-shared durable release evidence |
| install tree, caches, views, modules, buildcache | CAC-shared runtime/build state; never commit |
| build stage | Node-local or site scratch; disposable |
| logs and acceptance evidence | CAC-shared `evidence/<system>/<pilot-release>` |

The intentionally untracked planning email draft is unrelated to this workflow
and must not be published during a system run.

## System and platform details

Use the following only for a system-specific delta after following this
runbook:

- `stack-content/systems/blueback/runbook-notes.md`
- `stack-content/systems/raider/runbook-notes.md`
- `stack-content/systems/_template/runbook-notes.md`
- `cray_pe_acceptance_checklist_v1.md`
- `generic_linux_acceptance_checklist_v1.md`
- `deployment_inputs_and_ownership_v1.md`
