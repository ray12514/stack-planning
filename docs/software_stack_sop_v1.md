# Standard Operating Procedure: Software Stack Lifecycle

| Document control | |
|---|---|
| Version | Draft 3 |
| Date | 2026-07-13 |
| Owner | CSE stack team |
| Status | For management review |
| Review cycle | To be set at adoption |

This document describes how computing systems are onboarded, how software
stacks are designed, built, and published, and how app managers and users
work with the results. Every step produces a plain, reviewable file that a
person can author, inspect, or correct by hand.

## 1. The process at a glance

| # | Step | What exists afterward | Who owns it |
|---|---|---|---|
| 1 | Record the system's facts | the **fact sheet**: compilers, MPIs and their compiler pairings, GPU toolkits, network fabric, filesystems, module system | app manager for that system |
| 2 | Choose the site paths | the **deployment overlay**: install tree, cache locations, module and view roots plus the owning collaboration group and access audience. Always chosen, never derived. | installer |
| 3 | Declare the software | the **stack file** and reusable **package sets**: what to build, at which versions | app manager (curated stack) |
| 4 | Derive the work tree | the **work tree**: complete build configuration, config scopes plus one build environment per lane | derived from steps 1 to 3 |
| 5 | Build | installed software, one **lockfile** per lane, build-cache entries | app manager |
| 6 | Publish | the **modules and views** users see, and the **release manifest** | app manager and release approver |
| 7 | Verify | validation evidence attached to the release | app manager |

The continuous loop: when the system changes, step 1 is redone and the new
facts are compared with the approved release's platform runtime fingerprint.
When the software list changes, only step 3 is redone. When site paths change,
only step 2 is redone. Whatever changed, the work tree is re-derived. The
runtime-transition gate in section 7 determines whether each lane can be
revalidated, must remain pinned to an older supported runtime set, or must be
rebuilt. Nothing downstream is edited in place.

## 2. Vocabulary

- **Fact sheet**: the per-system record of what the machine provides. It
  contains platform reality only, never software intent.
- **Deployment overlay**: the per-system record of where things go. Access to
  those locations is an installer-owned deployment policy, never a discovered
  system fact.
- **Stack file / package set**: the record of what software is wanted. It
  contains intent only, never system facts.
- **Lane**: one independently built target. A compiler, optionally paired
  with an MPI, optionally targeting a GPU architecture. Each lane has its
  own build environment, lockfile, view, and modules. Lanes never mix
  compilers.
- **Scope**: a directory of build configuration a lane pulls in by
  reference (common policy, OS externals, CPU target, MPI pairing, GPU
  toolkit). Scopes are shared; lanes include only what they need.
- **Work tree**: the derived directory holding all scopes and one build
  environment per lane. It can be regenerated at any time, it is never
  patched by hand, and every value in it can be traced to the fact sheet,
  overlay, or stack file that set it.
- **Release**: one built, verified, tagged copy of the stack. A `current`
  pointer names the active release; promotion moves the pointer.
- **Platform catalog**: a published, per-system, per-release set of
  ready-to-include build configuration (the system's compilers, MPIs, and
  GPU toolkits as pinned externals) with a manifest naming the recommended
  choices. Any app manager can use it without joining the curated stack
  process.
- **Platform runtime set**: the coherent vendor and site runtime selected for a
  lane: compiler and programming-environment release, MPI provider and flavor,
  fabric runtime, launcher/PMI components, accelerator toolkit and integration
  libraries, and other platform-coupled libraries such as Cray LibSci.
- **Platform runtime transition**: evaluation of a candidate runtime set after
  a system or vendor update against the set recorded for a published release.
  A transition is approved only with documented support evidence and tests;
  module coexistence or a new system default is not compatibility evidence.

## 3. Onboarding a new system

1. The app manager records the fact sheet: which compilers exist and where,
   which MPI builds pair with which compilers, GPU toolkits and
   architectures, fabric, filesystems, and the module system. It is a plain
   YAML file checked against a published schema.
2. The installer records the deployment overlay: install tree, cache paths,
   module and view roots. These are decisions, not discoveries. The fact
   sheet lists candidates; a person chooses. The selected roots must be on a
   shared filesystem visible from the required login, build, and compute node
   types. During the alpha deployment, the overlay names the CSE collaboration
   group that owns the roots; access is group-only.
3. Review and sign-off: both files enter the repo of record through a
   reviewed change (pull request). A second app manager, or the stack lead
   where there is only one, confirms the facts against the machine and
   approves. No downstream step consumes an unreviewed fact sheet.
4. The platform catalog for the system is generated from the approved fact
   sheet and published alongside it, versioned by release.

If a fact later proves wrong, the correction goes into the fact sheet and
everything downstream is re-derived. Generated files are never patched to
work around a wrong fact. This rule keeps every file in the process
trustworthy.

## 4. How the curated stack (CSE) is built

The stack file lists the software. The work tree derived from it contains
one build environment per lane. For example, a Cray system with two
compiler surfaces has a Serial, an MPI, and a GPU lane under each of GCC
and CCE. Each lane is ordinary Spack input, built with ordinary Spack
commands:

```
spack -e environments/gcc/mpi concretize
spack -e environments/gcc/mpi install
```

Checkpoint at concretize: the system's own compilers, MPI, and GPU toolkits
must appear as pinned externals being used. If the build tool starts
downloading something the machine already provides, the inputs were wrong.
Stop and fix the fact sheet; do not fix the derived files.

Publishing regenerates views and modules, pushes build caches, and records
the release manifest and per-lane lockfiles. Those three artifacts (manifest,
lockfiles, caches) are what make a release reproducible.

Access has two enforcement points. Spack applies ownership and read/write
permissions to package installation prefixes from the rendered
`packages.yaml`. The build/publish path applies group ownership and setgid or
default-ACL policy to the shared roots Spack does not own: caches, views,
module trees, buildcache destinations, release metadata, and `current`.
Discovery never changes permissions. Working roots are group-writable while a
release is assembled. A promoted release is group-readable/executable and is
not modified in place. The module front door and `current` pointer must resolve
from both login and compute nodes. World access is disabled for the initial
deployment; expanding the publication audience is a deliberate release-policy
change.

Promotion gate: a release becomes `current` only after (a) the validation
report is clean, (b) a user-level smoke test passes (load a compiler
surface, load one lane, compile and run a small MPI program), (c) a clean
session from another member of the collaboration group can read the release
and load its modules from both login and compute nodes, and (d) the stack lead
approves. The approval and evidence are recorded in the release manifest.
Rollback is moving the pointer back.

Build policy boundaries:

- The fact sheet records what exists. It does not decide what to build.
- The stack file records package intent. It does not duplicate platform
  discovery.
- The renderer selects a coherent compiler/MPI/GPU/platform-runtime set from
  the fact sheet and policy, then renders only that set for the managed stack.
- Platform-coupled runtimes such as Cray MPICH, Cray LibSci, libfabric, CUDA,
  and ROCm are consumed only through explicit policy. Observing a runtime on a
  machine is not enough to expose it to a managed stack.
- Every lane has a lockfile and manifest record. If a lane is rebuilt, the
  release evidence changes with it.

## 5. How an independent app manager builds

App managers outside the curated stack keep their own environments and
their own module conventions. The process supports them without requiring
any coordination:

1. Pull the system's platform catalog. Its manifest names the recommended
   compiler, MPI, and GPU configuration; the README shows the include block.
2. Write an ordinary Spack environment by hand, including the catalog's
   scopes so the build links the system's supported compilers and MPI:

   ```yaml
   spack:
     include:
       - <catalog>/scopes/common
       - <catalog>/scopes/compilers/gcc/14.3.0
       - <catalog>/scopes/mpi/cray-mpich/9.1.0/gcc-14.3.0
     specs:
       - mytool@2.1
       - mytool@2.0
   ```

3. Build, then write a modulefile per version and place it in their own
   shared directory that is already on the system's module path. The
   package is immediately available to users through the path they already
   had. Nothing about the curated stack changes.

An app manager can operate fully by hand indefinitely, or adopt parts of
the curated process later. The catalog exists so that software built
outside the stack still matches the machine.

## 6. What users experience

Three commands, no build-system knowledge:

```
module load cse/GCC        # compiler surface: core tools appear, and
                           # foundation libraries are available to link
module load MPI            # exactly one lane: Serial, MPI, or GPU
module load hdf5/1.14.6    # the package, at the version they choose
```

Loading a second, conflicting lane fails with an explicit error rather than
silently mixing environments. `module whatis` on any package reports where
it came from: built by the stack, provided by the platform, or provided by
the site.

Package modules also protect version-sensitive dependency relationships. If
`netcdf-c` was built against a specific compatible `hdf5` in the selected lane,
the `netcdf-c` module loads, requires, or conflicts accordingly. Users see clean
package names; the module layer prevents incompatible mixes where compatibility
matters.

User exposure policies:

- A user loads one compiler surface, then one lane under that compiler. The lane
  exposes only its package module root.
- Serial, MPI, and GPU lanes conflict as public entry points. Users do not load
  MPI and GPU lanes together.
- A GPU lane is a complete MPI-capable GPU surface when the stack selected a
  compatible compiler/MPI/GPU combination. In that case GPU is a superset of the
  matching MPI lane's runtime surface, not a separate add-on lane.
- Package module names stay clean. Compatibility rules live in module metadata,
  not in long public names.
- Foundation libraries are ambient in the compiler/lane view and single-version
  by release policy. Core tools are loadable. MPI-dependent, GPU-dependent, and
  performance-sensitive packages remain payload packages in Serial, MPI, or GPU
  lanes.

## 7. Platform upgrades and runtime transitions

Every release manifest records the platform runtime fingerprint used by each
lane. At minimum it records the approved fact-sheet revision, programming
environment, compiler identity and module chain, MPI provider/version/flavor
and module chain, fabric provider/version/prefix, launcher and PMI components,
GPU toolkit and integration runtime where applicable, and platform-coupled
libraries such as GTL and LibSci. A release never relies on whichever runtime
the host happens to load by default.

When the operating system, programming environment, compiler set, MPI, fabric,
launcher, or accelerator stack changes, the app manager performs this gate on
the pre-production or test system before the update reaches production:

1. Generate a new fact sheet and retain the approved old fact sheet. Produce a
   structured diff of their platform runtime fingerprints.
2. Review the vendor release notes, product dependency matrix, and site module
   changes for every changed platform-coupled component. Do not infer
   compatibility solely from a package's major version, a path still existing,
   or two modules being loadable side by side.
3. Capture the old and candidate module chains in clean shells. Confirm the
   actual compiler, MPI, fabric, PMI/launcher, and GPU libraries selected with
   module inspection plus executable/library evidence such as `readelf`,
   `ldd`, wrapper output, and provider diagnostics.
4. Re-render and concretize against the candidate fact sheet. Classify and
   record the outcome for every affected lane using the decision table below.
5. Run the transition acceptance tests before promotion: C, C++, and Fortran
   compile/link checks; scheduler-launched multi-node MPI; fabric-provider
   checks; GPU-aware MPI where applicable; representative package/application
   tests; module-chain tests; and library-resolution verification.
6. Publish the decision with the release: supported runtime set, required
   prerequisite modules, revalidated or rebuilt lanes, known restrictions,
   deprecation date for an older runtime set, and user action if any.

| Evidence | Required action |
|---|---|
| Runtime identity, explicit module chain, and linked providers are unchanged; transition tests pass | Revalidate the lane. No rebuild is required. |
| The old runtime remains installed, explicitly selectable, and vendor/site-supported; the old module chain recreates the recorded fingerprint and tests pass | Keep the release pinned to the old runtime set. Do not let the new default leak into it. |
| A required runtime, prefix, ABI, provider, or supported MPI/fabric/GPU pairing changed or disappeared | Rebuild the affected lane against the candidate runtime set, then run the full release gate. |
| Compatibility or support status is unknown, or tests do not prove the recorded pairing | Hold promotion. Obtain vendor/site evidence or rebuild; never assume compatibility. |

For Cray systems, Cray MPICH, libfabric/CXI, PMI/PALS, GTL, LibSci, the selected
PrgEnv/compiler, and the GPU runtime are evaluated as one platform runtime set.
The Cray MPICH external must load the exact supported module chain for that set;
it must not inherit an ambient libfabric default. Older Cray PE releases may
remain usable side by side only when the site and HPE support that pairing and
the acceptance tests reproduce the recorded runtime fingerprint. A change to
the system default alone neither proves that a rebuild is necessary nor proves
that the old stack remains safe.

The rebuild unit is the affected lane, not automatically the whole stack. A
shared foundation or compiler-layer component rebuild expands the impact to
every lane that consumes it. The app manager records that dependency impact in
the transition report before any `current` pointer moves.

## 8. Requests and issues

- A user reporting a broken module or requesting a package or version
  raises it through the site's normal support channel. The system's app
  manager owns triage.
- A problem traced to a wrong system fact is fixed in the fact sheet and
  re-derived (section 3). One traced to the software list is fixed in the
  stack file (section 4). An independent app manager's package is handled
  by its owner (section 5).

## 9. What good looks like

- The fact sheet and overlay are reviewed and approved before anything
  consumes them.
- Every value in the work tree can be traced to one of the three input
  files.
- Concretization uses the machine's externals; nothing the machine already
  provides is downloaded.
- The serial lane's lockfile contains no MPI node: lane purity is checked
  in the concretized lock, never assumed from the render.
- A release promotes only with clean validation, a passing user-level smoke
  test, and recorded approval.
- A fresh user shell reaches any published package in three module commands.
- Shared release roots, module roots, and the `current` pointer are visible
  from login and compute nodes and have the approved group-only access policy.
- Version-sensitive package module chains are tested: compatible chains load
  cleanly, and incompatible dependency mixes fail or are prevented.
- Every release records its platform runtime fingerprint and can recreate its
  runtime through explicit modules without relying on the current system
  default.
- A system upgrade has a reviewed transition report with a per-lane
  revalidate/pin/rebuild/hold decision before production promotion.

## 10. Open items for later revisions

Not yet defined and deliberately out of scope for this draft: system and
release decommissioning; security re-validation cadence after CVEs in
system-provided libraries; cross-system version-consistency audits; the
package deprecation and removal flow; the onboarding checklist for a new
app manager (the person, not the system).
