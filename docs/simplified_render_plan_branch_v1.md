# Simplified Render Plan Branch v1

Recorded 2026-07-02. Branch: `codex/simplified-render-plan`.

This branch uses the current Blueback render path as the control while
introducing a cleaner internal seam for the next renderer shape. The first goal
is not a user workflow change. The first goal is to make render decisions
explicit, testable, and comparable before removing template logic.

## Control and experiment

| Path | Purpose |
|---|---|
| `main` | Current Blueback path and baseline behavior. |
| `codex/simplified-render-plan` | Add explicit `RenderPlan`, `NetworkPlan`, and `ModulePlan` seams, then migrate one lane at a time. |

The experiment must prove that it can reproduce the current useful behavior
before replacing it. A successful branch makes debugging easier even if it does
not immediately remove much code.

## Target seam

Current render flow:

```text
profile + stack + deployment + defaults
  -> lane dictionaries
  -> Jinja templates + modulefile renderer
  -> workspace files
```

Target render flow:

```text
profile + stack + deployment + policy
  -> RenderPlan
       lanes
       network plan
       module plan
       ignored candidates
       emitted scopes
  -> mechanical emitters
  -> workspace files
```

The `RenderPlan` is the interface between decision-making and file emission. A
template or emitter may print a value from the plan, but it should not decide
which compiler, MPI, GPU toolkit, network runtime, module path, or package
visibility rule applies.

## Template rule

Templates are allowed as dumb printers. They are not allowed to own policy.

Allowed in a template:

- iterate over already resolved providers;
- print YAML/Lua/Tcl syntax;
- apply formatting defaults that do not affect selection.

Not allowed in a template:

- vendor branching such as "if Cray";
- choosing an MPI provider;
- choosing compiler/MPI compatibility;
- classifying externals;
- deciding lane/module visibility;
- hardcoding Blueback or CSE paths.

Over time, Spack YAML templates should either become tiny emitters or be replaced
by structured YAML writers. This is an implementation choice after the plan seam
is stable.

## Module exposure is part of render

Module exposure is not deferred. A lane is not complete unless render can show
how users reach it.

The plan must include a `module_plan` with:

- exposure model: `front_door` or `direct`;
- generated compiler init module names;
- generated lane module names;
- module paths exposed by each init module;
- package module roots exposed by each lane module;
- conflicts between mutually exclusive lanes;
- core/foundation view exposure.

The current front-door behavior remains the baseline:

```text
<stack>_init_<compiler>
  -> exposes compiler/core view
  -> prepends lane module root

<stack>/<lane>
  -> prepends that lane's package module root
```

## Network plan

MPI/fabric/GPU transport policy should move toward a first-class network plan.
The plan should be able to explain:

- selected MPI provider and version;
- selected compiler-compatible MPI flavor;
- whether the MPI is platform external or Spack-built;
- selected fabric/runtime dependencies such as libfabric, UCX, CXI, PMI/PALS,
  and GTL;
- GPU runtime additions for ROCm/CUDA lanes;
- ignored MPI candidates, such as application-local OpenFOAM providers.

Stackinator's `network.yaml` model is useful prior art, but the emitted Spack
mechanism should use Spack-native toolchains where supported.

Current branch rule:

- `cluster-inspector` may report Cray PMI, PALS, and GTL as
  `fabric.userspace` facts when it observes concrete evidence.
- `stack-composer` reports those facts in `reports/render-plan.yaml` under the
  network plan.
- `stack-composer` does not render `cray-gtl`, `cray-pmi`, or `cray-pals` as
  Spack package externals by default. Those package names require an explicit
  package-repo policy, likely modeled after CSCS `alps-cluster-config`.
- The default common Spack scope remains conservative: `libfabric` and `ucx`
  can be rendered as fabric userspace externals; Cray runtime packages remain
  observed-but-not-rendered until the stack owns the package definitions.

## Platform release plan

Cluster Inspector should report broad platform inventory. On a Cray system this
means it may emit multiple `cray-mpich` provider versions, multiple LibSci
generations, and multiple GTL generations when the module tree exposes them.
That is intentional: discovery records facts, not stack intent.

Stack Composer owns the render-time selection. The simplified branch starts
with one conservative default:

- platform-owned system externals such as `cray-libsci` render only the latest
  observed package generation;
- older observed generations are recorded in `reports/render-plan.yaml` under
  `platform_plan.ignored_system_externals`;
- the selected generation is recorded under
  `platform_plan.selected_system_externals`;
- future production policy may replace the default `latest` selector with an
  explicit CPE/platform release table in content policy, without changing the
  profile schema.

The public profile interface remains generic. Do not add a Cray-only top-level
`cpe_versions` contract unless testing proves package version alone is
insufficient to select a coherent platform release. Multiple Cray MPICH versions
should be represented as multiple `mpi_providers` entries, each with its own
per-compiler `flavors` map.

## External classification

Discovered facts are not automatically consumed. The resolver should classify
externals before rendering:

| Class | Default action |
|---|---|
| OS build basics (`openssl`, `curl`, `git`, `perl`) | allow as controlled externals |
| vendor runtimes and compilers | allow when module-backed/profile-backed |
| network runtimes (`cray-mpich`, `libfabric`, `ucx`, `libcxi`, PMI/PALS/GTL) | allow only through network policy |
| GPU SDKs (`rocm`, `cuda`, NVHPC) | allow when version/module policy matches |
| application-local providers such as OpenFOAM MPI/compiler modules | discover but ignore by default |

## Comparison criteria

The branch should report old-vs-new impact with concrete data:

1. Does the current Blueback smoke render still work?
2. Does the simplified path render the same intended lanes?
3. Does `reports/render-plan.yaml` explain the selected compiler/MPI/GPU/module
   decisions clearly?
4. Does Blueback concretization get at least as far as the baseline?
5. How many template files/conditionals are removed or simplified?
6. How many lines of code/templates are removed, added, or moved?
7. Are there fewer places to update for a new MPI provider or new system family?

Code reduction is desirable but secondary to a cleaner seam. A branch that adds
a small amount of code to expose the plan may still be correct if it enables
later template deletion and better debugging.

Suggested measurement commands:

```bash
# From each changed repo.
git diff --stat main...HEAD

# In stack-composer or stack-content, track template surface area.
find . -path '*/templates/*' -name '*.j2' | sort | wc -l
find . -path '*/templates/*' -name '*.j2' -print0 | xargs -0 wc -l

# Track policy-bearing template conditionals. The count should trend down as
# policy moves to RenderPlan/NetworkPlan/ModulePlan.
rg -n '\{[%#]|if |elif |for ' templates tests/fixtures/template-sets || true
```

For branch notes, record:

| Metric | Baseline (main, 2026-07-03) | Branch (2026-07-03) | Notes |
|---|---:|---:|---|
| Python LOC touched | 0 | +1000/−88 (18 files) | `git diff --stat main...HEAD`, stack-composer |
| Jinja template files | 24 (274 lines) | 24 (274 lines) | unchanged so far — slice 1 is additive by design |
| Jinja conditional/loop sites | 45 | 45 | `grep -rEn '\{%-? *(if|elif|for) '` over fixture templates; should decrease in later slices |
| Render reports emitted | 0 | 1 (`reports/render-plan.yaml`) | |
| Blueback render/concretize status | pending run | real-system smoke path passed | Blueback reached the managed-stack blueprint path on 2026-07-05; Cray MPICH library verify warning recorded as external-runtime follow-up |

## Blueback smoke result (2026-07-05)

The branch produced a working first real-system Blueback smoke path:

```text
cluster-inspector -> profile.yaml -> stack-composer validate/render -> spack-build
```

The run proved the current seam is useful enough to continue the simplification
work:

- Stack Composer selected one coherent Blueback platform runtime set for render:
  latest `PrgEnv-gnu`, `cray-mpich` 9.1.0, ROCm 7.0.0, `gfx942`.
- Cray MPICH rendering stopped emitting every discovered Cray MPICH flavor into
  the active lane. The active package external is a plain provider spec, and
  the compiler/MPI binding is represented in `toolchains.yaml`.
- ROCm HIP external rendering uses the ROCm toolkit root proven by `bin/hipcc`;
  it no longer invents `$ROCM_ROOT/hip` as a package prefix.
- Cray GTL, PMI, and PALS are visible as observed runtime facts in the render
  plan but are not written as package externals without an explicit site
  package-repo policy.
- The remaining library verify warning around external runtime libraries
  such as XPM/hugepages is not a render-selection failure. It is a package
  modeling decision for a later runtime-policy slice.

This result changes the branch status: Blueback is no longer blocking the
policy-driven renderer work. The next work should simplify the implementation
that produced the successful run.

## First vertical slice

The first vertical slice is complete:

1. Emit `reports/render-plan.yaml` for the current render.
2. Include lane decisions and current front-door module exposure in the plan.
3. Add tests that assert the module plan matches generated modulefiles.
4. Add a simple code-size/template-count comparison command to the runbook or
   branch notes.

The next slices should reduce policy-bearing template logic:

1. Define a small internal interface for resolved platform runtime selection:
   selected MPI provider, selected compiler flavor, selected GPU toolkit, and
   selected network/runtime facts.
   **Status (2026-07-05): done for the render side.** All four selection axes
   are resolved once into the render context and templates only print:
   `mpi_plan` (render/network.py), `gpu_plan` (render/gpu.py), `common_plan`
   (render/common.py), `compiler_plan` (render/compilers.py), alongside the
   existing `platform_plan` and `module_plan`. The only remaining template
   globals are formatting helpers (`to_yaml`, `path_join`, `spack_spec`);
   templates can no longer compute selection policy. Each plan has a guard test
   asserting it equals the global it replaced, so rendered output is unchanged.
2. Move Cray MPICH, ROCm, LibSci, fabric, and runtime selection into that plan
   layer. The templates should only print plan fields. **Done** (see slice 1
   status).
3. Add a fixture that represents a generic Linux system with multiple compiler
   and MPI providers. The same plan layer must select or reject providers
   without Cray-specific assumptions leaking into generic logic.
   **Checked (2026-07-05): the Cray-only `selected_mpi_providers` version filter
   is correct, not a leak.** Cray PE flavors of one cray-mpich version share a
   single product-tree prefix, so multiple flavors must collapse to the
   lane-selected version or Spack sees duplicate externals. Non-Cray providers
   at *different* versions (openmpi@4.1.6 vs @4.1.7) are distinguishable by Spack
   and render as a version-qualified catalog with version-qualified toolchain
   names (`aocc420_openmpi416` vs `aocc420_openmpi503`) — no ambiguity, covered
   by `test_rendered_generic_linux_workspace_contains_site_mpi_without_cray` and
   `test_mpi_version_pin_disambiguates_and_versions_toolchain_names`. The
   "multiple externals" ambiguity only affects duplicate *same* name@version
   (the softlinked-compiler case, fixed by inspector dedup). A dedicated generic
   multi-provider render fixture is still worth adding for confidence, but there
   is no filter change to make.
4. After managed render stays green, implement the manual config catalog as a
   separate command/output contract that reuses the same resolved plan data.
5. Run the next real-system test on a generic Linux cluster after the
   policy/template seam has at least one generic fixture.

## Repository boundary recommendation

Do not merge repositories during this branch. The branch is testing the renderer
seam, not repository packaging.

Current recommendation:

| Repo | Keep separate? | Reason |
|---|---|---|
| `cluster-inspector` | yes | Generic fact-gathering tool with value outside stack generation. |
| `stack-composer` | yes for now | Renderer/validator/reporter implementation. Its interface should stabilize before any packaging move. |
| `stack-content` | yes for now | Site content, policies, stacks, templates, and system records should be consumable and reviewable without changing renderer code. |
| `stack-planning` | yes | Design history, ADR-style notes, and runbooks. Eventually docs may be published separately. |

Revisit merging `stack-composer` and `stack-content` only after v1 behavior is
stable. Merge pressure is valid if most changes require synchronized edits in
both repos and CI/release tagging becomes error-prone. Until then, separation is
useful: content can evolve under site review while composer remains a versioned
tool.

If these move to GitLab, a good layout is one GitLab group/project namespace
with sibling repos:

```text
stack/
  cluster-inspector
  stack-composer
  stack-content
  stack-planning
```

This keeps cross-repo references local to one GitLab group without forcing an
early monorepo. A monorepo is still possible later if synchronized release
management becomes more important than independent tool/content ownership.
