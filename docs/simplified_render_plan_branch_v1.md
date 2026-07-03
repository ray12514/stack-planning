# Simplified Render Plan Branch v1

Recorded 2026-07-02. Branch: `codex/simplified-render-plan`.

This branch preserves the current Blueback render path as the control while
introducing a cleaner internal seam for the next renderer shape. The goal is not
to change user workflow first. The goal is to make render decisions explicit,
testable, and comparable before removing template logic.

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

| Metric | Baseline | Branch | Notes |
|---|---:|---:|---|
| Python LOC touched | | | `git diff --stat` |
| Jinja template files | | | should decrease or become dumb printers |
| Jinja conditional/loop sites | | | policy-bearing sites should decrease |
| Render reports emitted | | | should increase: `render-plan.yaml` first |
| Blueback render/concretize status | | | compare to `main` |

## First vertical slice

The first vertical slice is additive:

1. Emit `reports/render-plan.yaml` for the current render.
2. Include lane decisions and current front-door module exposure in the plan.
3. Add tests that assert the module plan matches generated modulefiles.
4. Add a simple code-size/template-count comparison command to the runbook or
   branch notes.

Only after this should the branch migrate one Blueback lane to reduced template
logic.

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
