# Standard Operating Procedure: Software Stack Lifecycle

| Document control | |
|---|---|
| Version | Draft 2 |
| Date | 2026-07-09 |
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
| 2 | Choose the site paths | the **deployment overlay**: install tree, cache locations, module and view roots. Always chosen, never derived. | installer |
| 3 | Declare the software | the **stack file** and reusable **package sets**: what to build, at which versions | app manager (curated stack) |
| 4 | Derive the work tree | the **work tree**: complete build configuration, config scopes plus one build environment per lane | derived from steps 1 to 3 |
| 5 | Build | installed software, one **lockfile** per lane, build-cache entries | app manager |
| 6 | Publish | the **modules and views** users see, and the **release manifest** | app manager and release approver |
| 7 | Verify | validation evidence attached to the release | app manager |

The continuous loop: when the system changes, only step 1 is redone. When
the software list changes, only step 3. When site paths change, only step 2.
Whatever changed, the work tree is re-derived and only the affected lanes
rebuild. Nothing downstream is edited in place.

## 2. Vocabulary

- **Fact sheet**: the per-system record of what the machine provides. It
  contains platform reality only, never software intent.
- **Deployment overlay**: the per-system record of where things go.
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

## 3. Onboarding a new system

1. The app manager records the fact sheet: which compilers exist and where,
   which MPI builds pair with which compilers, GPU toolkits and
   architectures, fabric, filesystems, and the module system. It is a plain
   YAML file checked against a published schema.
2. The installer records the deployment overlay: install tree, cache paths,
   module and view roots. These are decisions, not discoveries. The fact
   sheet lists candidates; a person chooses.
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

Promotion gate: a release becomes `current` only after (a) the validation
report is clean, (b) a user-level smoke test passes (load a compiler
surface, load one lane, compile and run a small MPI program), and (c) the
stack lead approves. The approval and evidence are recorded in the release
manifest. Rollback is moving the pointer back.

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
module load CSE/GCC        # compiler surface: core tools appear, and
                           # foundation libraries are available to link
module load MPI            # exactly one lane: Serial, MPI, or GPU
module load hdf5/1.14.6    # the package, at the version they choose
```

Loading a second, conflicting lane fails with an explicit error rather than
silently mixing environments. `module whatis` on any package reports where
it came from: built by the stack, provided by the platform, or provided by
the site.

## 7. Requests and issues

- A user reporting a broken module or requesting a package or version
  raises it through the site's normal support channel. The system's app
  manager owns triage.
- A problem traced to a wrong system fact is fixed in the fact sheet and
  re-derived (section 3). One traced to the software list is fixed in the
  stack file (section 4). An independent app manager's package is handled
  by its owner (section 5).

## 8. What good looks like

- The fact sheet and overlay are reviewed and approved before anything
  consumes them.
- Every value in the work tree can be traced to one of the three input
  files.
- Concretization uses the machine's externals; nothing the machine already
  provides is downloaded.
- A release promotes only with clean validation, a passing user-level smoke
  test, and recorded approval.
- A fresh user shell reaches any published package in three module commands.

## 9. Open items for later revisions

Not yet defined and deliberately out of scope for this draft: system and
release decommissioning; security re-validation cadence after CVEs in
system-provided libraries; cross-system version-consistency audits; the
package deprecation and removal flow; the onboarding checklist for a new
app manager (the person, not the system).
