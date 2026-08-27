# Portable Tools And GitLab Transition Plan v1

| Document control | |
|---|---|
| Date | 2026-08-25 |
| Status | Proposed pre-v1 transition plan |
| Scope | Cluster Inspector, Stack Composer, the four-repository GitLab home, and target-host distribution |
| Trial impact | None. The active trial commands remain supported while the release artifacts and simpler interfaces are developed. |

## 1. Outcome

The stack-generation tools should be installable commands, not development
checkouts. A target system should not need Go, a Python virtual environment,
pip, GitHub access, or the tool's source tree to run either command.

The intended operator experience is:

```text
cluster-inspector ...   -> reviewed profile.yaml
stack-composer ...      -> deterministic rendered workspace
spack-build ...         -> downstream build execution
```

GitLab becomes the authoritative source, CI, release, package, and provenance
home. If private GitHub copies are retained, they are downstream mirrors or
deliberate exports; they are not an authority and target systems never depend
on them.

## 2. Separate four concerns

The transition must not treat repository hosting and executable portability as
one problem.

| Concern | Required result |
|---|---|
| Source authority | Project-owned repositories and reviews are authoritative in GitLab. |
| Build isolation | Release pipelines can build from pinned, mirrored or vendored inputs without live GitHub access. |
| Runtime isolation | Target systems run released artifacts without source checkouts, language toolchains, package installation, or network access. |
| User interface | Each tool presents a small command interface that hides repository layout and packaging details. |

## 3. Current-state assessment

### Cluster Inspector

Cluster Inspector is already close to the desired product shape:

- it is a Go command;
- schemas and discovery resources are embedded;
- its design already requires no source checkout, Spack installation, or
  network access at runtime; and
- its dependencies do not need to exist separately on the target.

The remaining gap is a repeatable release pipeline and artifact matrix. The
currently built local executable proves compilation, not portability to all
target Linux systems. The module path and several project-owned documentation
links also still use the temporary personal GitHub namespace.

### Stack Composer

Stack Composer already has a normal `stack-composer` console entry point and a
release builder that creates `stack-composer.pyz`. The `.pyz` contains the
application and its Python dependencies and needs no target-side pip install,
but it still requires Python 3.9 or newer on the target. It is therefore an
offline Python application bundle, not a standalone executable.

The current `render` command also exposes many internal inputs independently.
That is precise for development, but it makes the operator understand too much
of the repository layout and provenance plumbing. Packaging and interface
simplification should be handled together as a product pass, while preserving
the deterministic render seam.

## 4. Distribution recommendation

### 4.1 Cluster Inspector: static Go release artifacts

Publish one self-contained binary per supported operating-system/architecture
pair. For the current systems, Linux x86-64 is the first required artifact;
additional architectures are added only when the supported-system inventory
requires them.

Release builds should:

- use `CGO_ENABLED=0` unless a future probe dependency demonstrates a real need
  for CGO;
- embed version, commit, schema/content version, and clean/dirty release state;
- use reproducible path trimming and deterministic build inputs;
- include checksums, license inventory, SBOM, and signature/attestation;
- run on the oldest supported Linux ABI/kernel baseline and every representative
  target family; and
- prove that `cluster-inspector --version`, `--help`, profile generation, and
  embedded-schema validation work with no network or adjacent repositories.

"Any machine" means every machine in the declared support matrix, not one
universal executable across Linux, macOS, CPU architectures, or incompatible
kernel/ABI floors.

### 4.2 Stack Composer: standalone command bundle

Retain the `.pyz` as a useful developer and near-term fallback, but do not make
it the final target-host contract if CSE wants no system Python dependency.

Run a short packaging spike comparing:

1. a PyInstaller or Nuitka standalone build;
2. a relocatable bundle containing a controlled CPython runtime and all pinned
   wheels; and
3. the existing Shiv `.pyz` as the control.

The recommended production shape is a versioned tarball with one public
`bin/stack-composer` command and its private runtime beside it. This can still
feel like a normal binary to an operator while avoiding reliance on target
Python. A true one-file executable may be offered only if target testing proves
its runtime extraction works on shared HPC filesystems, restricted temporary
directories, and `noexec` environments. A one-directory bundle is usually the
more predictable HPC deployment artifact.

Build Linux bundles against the oldest supported glibc/OS baseline and publish
separate artifacts when architectures or ABI floors require them. Do not claim
that a Python executable built on one arbitrary machine is portable everywhere.

### 4.3 Shared release contract

Both tools should expose:

```text
<tool> --version
```

The output should identify the tool version, source commit, embedded contract
version, target OS/architecture, and release status. A release directory should
contain the executable/bundle, checksums, signature, SBOM, license inventory,
and a concise installation/readme file.

## 5. Stack Composer interface redesign

The public seam should accept product concepts rather than every internal file
path separately. A candidate operator interface is:

```bash
export STACK_CONTENT_ROOT="<site-selected Stack Content checkout>"

stack-composer show \
  --content "$STACK_CONTENT_ROOT" \
  --system wheat \
  --stack cse

stack-composer render \
  --content "$STACK_CONTENT_ROOT" \
  --system wheat \
  --stack cse \
  --release 2026.09
```

From the explicit content root and names, Stack Composer can locate the
profile, deployment, defaults, stack, templates, package sets, and package
repositories through the documented Stack Content layout. It can read source
identity from a release metadata file or Git when available, but a target run
must not require Git or a network checkout. The output root remains an
installer-owned value recorded in deployment content rather than an implicit
home-directory default.

This interface is intentionally proposed, not committed. Before changing the
CLI, walk through the remaining trial commands and record which arguments are:

- actual operator choices;
- derivable from the Stack Content layout;
- release-pipeline provenance;
- temporary trial-only inputs; or
- maintainer-only diagnostics.

The final public command should keep only the first category. Validation should
be automatic before render. Lower-level commands may remain as maintainer
interfaces, but trial-only `init-workspace` must not define the production user
experience. Stack Composer continues to render; it does not absorb
concretization or package builds.

## 6. GitLab authority and optional GitHub mirror

Use one GitLab group with the existing four-repository ownership split:

```text
<gitlab-group>/cluster-inspector
<gitlab-group>/stack-composer
<gitlab-group>/stack-planning
<gitlab-group>/stack-content
```

GitLab should own:

- protected authoritative branches and tags;
- merge requests and review history;
- CI runners and release jobs;
- the generic package/release registry for binaries and bundles;
- versioned schema/content artifacts;
- internal dependency mirrors, package registries, or vendored archives; and
- release signatures, checksums, SBOMs, and attestations.

If GitHub remains:

- make the project repositories private as intended;
- update them only from an accepted GitLab commit/tag through a one-way mirror
  or an explicit export procedure;
- do not accept independent changes on both hosts; and
- do not put GitHub credentials, URLs, or availability into a target-host
  runtime path.

Manual copying in both directions should not become the normal workflow. It
creates two possible authorities and makes commit identity and release
provenance harder to prove.

## 7. What “remove GitHub dependencies” means

Track the cleanup in four classes so important distinctions are not lost.

### 7.1 Project-owned identities

Remove all personal/project-owned GitHub module paths, documentation links,
badges, clone instructions, source-repository defaults, and examples. Once the
final GitLab namespace is known, change Cluster Inspector's Go module path and
all internal imports directly before v1; no compatibility bridge is required.

### 7.2 Build-time dependency access

Target release builders should not need live GitHub access. Use one or more of:

- committed Go vendoring plus checksum verification;
- a GitLab Go proxy/dependency proxy or approved internal mirror;
- a pinned Python wheelhouse published in GitLab;
- mirrored source archives and license material; and
- an internal mirror of the approved Spack and `spack-packages` generations.

The release pipeline should run once in a network-denied mode to prove the
complete input set is present.

### 7.3 Target runtime access

Neither executable may fetch code, schemas, templates, Python packages, Go
modules, or project metadata while running on a target. Stack Content and any
approved Spack/source mirrors are deployed explicitly through the release
process.

### 7.4 Third-party provenance URLs

Third-party license and provenance records may name an upstream project whose
canonical source happens to be GitHub. Removing those strings does not improve
runtime isolation and may weaken traceability. If policy requires literally no
GitHub URL anywhere in released source or documentation, mirror those sources
and record both the internal source location and original upstream identity in
the legal inventory. Decide this separately from eliminating GitHub as an
operational dependency.

## 8. Spack and package-source isolation

Moving the four project repositories is not sufficient if rendered content
still points directly to GitHub for Spack, `spack-packages`, overlays, or source
archives.

The production release should pin and publish:

- the approved Spack runtime source/commit in GitLab or an internal source
  artifact;
- the approved `spack-packages` generation in GitLab or an internal mirror;
- CSE package overlays from Stack Content;
- a populated Spack source mirror for restricted builds;
- build-cache artifacts segmented by compatibility domain; and
- checksums/signatures connecting every artifact to the CSE release manifest.

Rendered configuration must use the internal locations. An upstream URL may be
retained as provenance metadata, but target operation and cache-only rebuilds
must not depend on it.

## 9. Transition phases

### Phase 0 - Record the support and authority decisions

Before changing paths, record the final GitLab group, supported Linux
OS/glibc/kernel floors, architectures, GitHub mirror policy, release signing
method, and whether third-party provenance URLs are allowed.

### Phase 1 - Inventory references and dependencies

Produce a machine-readable inventory across all four repositories:

- project-owned GitHub references;
- third-party GitHub references;
- Go module/import paths;
- Python and Go dependency download sources;
- Spack/package-repository URLs;
- CI badges/workflows and release metadata; and
- commands that assume a source checkout, sibling repository, Git, Go, Python,
  pip, or network access.

Classify each entry as rename, mirror/vendor, preserve for provenance, or
remove.

### Phase 2 - Release Cluster Inspector

Add the GitLab release pipeline, cross-build matrix, offline dependency input,
checksums/SBOM/signing, and target smoke tests. Change the project-owned Go
module path only after the final GitLab namespace exists.

### Phase 3 - Simplify and package Stack Composer

First record the desired operator workflow from the completed trials. Then
implement the smaller content-root-based public interface and the standalone
packaging spike. Select the bundle only after it passes the supported target
matrix without system Python, pip, Git, or network access.

### Phase 4 - Cut GitLab over as authority

Import complete repository history, protect branches/tags, establish CI and
release permissions, publish the schema/content artifacts, change project-owned
links and module paths, and verify release provenance end to end.

### Phase 5 - Establish the optional private GitHub mirror

If retained, configure or document a one-way GitLab-to-GitHub flow. Prove that
turning GitHub access off does not affect development release builds from the
internal dependency inputs or any target-host operation.

### Phase 6 - Target-host acceptance

Install only the released artifacts and Stack Content on representative clean
systems. Verify profile generation, rendering, schema validation, deterministic
output, and downstream build handoff without developer tooling or source
checkouts.

## 10. Acceptance gates

The transition is complete when:

- GitLab is the single authoritative host for all four project repositories;
- project-owned source/import/documentation identities no longer use the
  personal GitHub namespace;
- Cluster Inspector runs as a self-contained binary on every supported target;
- Stack Composer runs through one installed command with no target system
  Python or pip requirement;
- both tools run with no source checkout, Git, or network access;
- release builds succeed using only approved mirrored, vendored, or registry
  inputs;
- target rendering contains no operational GitHub URL;
- checksums, signatures, SBOMs, license records, embedded contract versions,
  and source commits are published with every release;
- the simpler Stack Composer interface reproduces byte-identical output from
  the same declared inputs; and
- private GitHub unavailability cannot block a build, render, deployment, or
  recovery operation.

## 11. Related documents

- [Pre-v1 hosting and external inventory](pre_v1_hosting_and_external_inventory_note_v1.md)
- [Stack generation structure](stack_generation_structure_v1.md)
- [Stack build handoff](stack_build_handoff_note_v1.md)
- [Cluster Inspector design](cluster_inspector_stack_profile_design_v1.md)
- [Deployment inputs and ownership](deployment_inputs_and_ownership_v1.md)
