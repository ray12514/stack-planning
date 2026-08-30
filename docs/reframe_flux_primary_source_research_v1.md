# ReFrame and Flux primary-source research (v1)

Recorded 2026-08-28. This note evaluates [ReFrame](https://reframe-hpc.readthedocs.io/en/stable/)
and [Flux Framework](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/)
against the CSE Spack stack build, validation, and orchestration model. Sources are
first-party ReFrame documentation/source and Flux Framework documentation/source.

## Executive recommendation

Adopt ReFrame as an optional, downstream acceptance and regression-test harness for
the rendered CSE release. Keep Stack Composer's render/build boundary and the
locked-Spack build path authoritative. ReFrame can compile and run small test
programs, but its native `build_system = 'Spack'` mode creates or modifies a Spack
environment in the ReFrame test stage; that is a different lifecycle from the
project's reviewed eight environments, global lock verification, shared install
tree, and cache-only publication. Use ReFrame to exercise the already installed
release through the selected module/toolchain/launcher chain, or to build a small
independent probe when that is explicitly the test's purpose.

Use Flux only as an optional execution accelerator inside a site-approved Slurm (or
other foreign-manager) allocation. It is a good fit for scheduling many independent
locked environment-install wrappers and ReFrame test jobs within one allocation,
but it should not become a required dependency of the renderer or a replacement for
the site's allocation manager. Slurm/Cray/PBS bootstrap, PMI, binding, network,
accounting, and policy integration require real-system evidence. Start with the
existing direct Slurm/PBS/Cray launch paths, then add a Flux lane behind an explicit
driver capability and acceptance check.

This recommendation follows the project's existing boundaries:

* [Stack build handoff note](stack_build_handoff_note_v1.md) makes the rendered
  workspace the handoff and leaves concretize, install, smoke/verify, and cache
  operations to `spacktools`, `spack-build`, Ansible, or bare Spack.
* [Initial Conversion Trials build execution model](initial_conversion_trials_build_execution_model_v1.md)
  requires all eight lockfiles to pass global verification before parallel
  installation, permits distinct environments to run concurrently, and assigns one
  owner to each environment's view/module refresh.
* [Initial Conversion Trials dependency risk audit](initial_conversion_trials_dependency_risk_audit_v1.md)
  states that recipes and generic concretization cannot prove scheduler launch,
  Cray wrapper/module ABI, runtime visibility, or shared-filesystem behavior.
* [Initial Conversion Trials build findings](initial_conversion_trials_build_findings_v1.md)
  records that MPI wrapper/library identity and launcher selection are independent;
  an unrelated ambient `mpiexec` must never be accepted.
* [Stack generation orchestration note](stack_generation_orchestration_note_v1.md)
  keeps multi-system orchestration outside Stack Composer.

## 1. ReFrame capabilities and exact configuration patterns

### 1.1 Test model and compile/run pipeline

ReFrame tests are Python classes, usually decorated with `@rfm.simple_test`, and
derive from `RegressionTest`, `CompileOnlyRegressionTest`, or
`RunOnlyRegressionTest`. A normal `RegressionTest` goes through setup, compile,
run, sanity, performance, and cleanup stages; hooks can run before or after these
stages. A `RunOnlyRegressionTest` intentionally skips compilation. See the
[tutorial's compiled-test and pipeline description](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#compiling-the-test-code)
and the [ReFrame source repository](https://github.com/reframe-hpc/reframe).

Minimal compile-and-run shape:

```python
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import sanity_function

@rfm.simple_test
class cse_probe(rfm.RegressionTest):
    valid_systems = ['cse:*']
    valid_prog_environs = ['cse-gcc-mpi']
    build_system = 'SingleSource'
    sourcepath = 'probe.c'
    executable = './probe.x'
    num_tasks = 2
    num_cpus_per_task = 1

    @sanity_function
    def validate(self):
        return sn.assert_found(r'PASS', self.stdout)
```

The current tutorial demonstrates `build_system = 'SingleSource'` and
`sourcepath`, while the how-to documents the supported `Make`, `CMake`,
`Autotools`, `EasyBuild`, `Spack`, and `CustomBuild` backends. Build-system
properties are configured in a hook after the string has been converted to a
build-system object. `CustomBuild` accepts exact command lists, but ReFrame warns
that environment management, reproducibility, and side effects are then the
test's responsibility. See [Working with build systems](https://reframe-hpc.readthedocs.io/en/stable/howto.html#working-with-build-systems).

Relevant patterns are:

* `build_system = 'Make'`, `CMake`, or `Autotools`, with backend-specific options
  such as `config_opts`, `make_opts`, compiler flags, and `max_concurrency`.
* `build_system = 'CustomBuild'` plus `self.build_system.commands = [...]` in a
  pre-compile hook for a deliberately bespoke probe.
* `build_system = 'Spack'` plus `self.build_system.specs = [...]`. ReFrame creates
  a new environment under the test stage by default, adds the specs, installs
  them, and loads the result for the test. An existing environment may instead be
  supplied with the `environment` attribute. The documented example and generated
  scripts are in [Integrating with Spack](https://reframe-hpc.readthedocs.io/en/stable/howto.html#integrating-with-spack).
* `RunOnlyRegressionTest` plus `executable` and optional `executable_opts` for
  exercising a release already installed by the CSE build path.
* `CompileOnlyRegressionTest` when compilation itself is the assertion and no run
  job is needed.

ReFrame normally compiles locally on the host where it runs. Set
`build_locally = False` (or `-S build_locally=0`) to make it generate and submit a
separate compilation job to the selected scheduler. This is useful for cross-
compile or compute-only environments, but it introduces another scheduler job
and another stage/output lifecycle. See [Compiling remotely](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#compiling-remotely).

For CSE, use the compile/run stages for small compiler, MPI, module, and ABI probes.
Do not use ReFrame's Spack backend to reconcretize the eight release environments.
If a probe must compile against CSE's installed artifacts, use the release's
explicit module chain and launcher as its `valid_prog_environs` and run it with
`RunOnlyRegressionTest` or a tiny `RegressionTest` whose build does not mutate the
release environment.

### 1.2 Systems, partitions, environments, modules, and launchers

ReFrame's system is an abstraction over an HPC system; a system contains named
partitions. A partition maps to a scheduler backend and a parallel launcher. An
environment is a named collection of compiler definitions, modules, environment
variables, features, and extras. Tests select combinations through
`valid_systems` and `valid_prog_environs`. The tutorial gives a complete baseline:

```python
site_configuration = {
    'systems': [{
        'name': 'cse',
        'hostnames': ['login[0-9]+'],
        'modules_system': 'lmod',
        'partitions': [{
            'name': 'compute',
            'scheduler': 'slurm',
            'launcher': 'srun',
            'access': ['-A', 'cse', '-p', 'compute'],
            'environs': ['cse-gcc-mpi'],
            'max_jobs': 4,
        }],
    }],
    'environments': [{
        'name': 'cse-gcc-mpi',
        'cc': 'cse-mpicc',
        'cxx': 'cse-mpicxx',
        'ftn': 'cse-mpifort',
        'modules': ['cse/init-GCC', 'MPI'],
        'env_vars': [['CSE_VALIDATION_MODE', 'acceptance']],
        'features': ['mpi'],
        'extras': {'mpi_provider': 'cray-mpich'},
    }],
}
```

The module and command names above illustrate an accepted CSE GCC MPI SDK; the
release builder chooses the actual front-door name. Do not substitute an
ambient `PrgEnv-gnu` for the CSE-built GCC surface. Before the SDK gate passes,
the ReFrame environment should use the exact candidate commands from the trial
acceptance record and remain non-publishable.

The exact configuration keys and supported values are in the [ReFrame
configuration reference](https://reframe-hpc.readthedocs.io/en/stable/config_reference.html):

* `systems.partitions.scheduler` supports `flux`, `local`, `lsf`, `oar`, `pbs`,
  `pbspro`, `sge`, `slurm`, `squeue`, `ssh`, and `torque` in the current stable
  documentation. `slurm` uses accounting; `squeue` is the Slurm backend for sites
  where accounting is unavailable or unsuitable. `pbspro` was added in ReFrame
  4.10.
* `systems.partitions.launcher` includes `local`, `srun`, `mpirun`,
  `mpirun-openmpi`, `mpirun-intelmpi`, `mpiexec`, `aprun`, `lrun`, `ibrun`,
  `ssh`, `pdsh`, and others. The launcher emits the parallel program command,
  while the scheduler emits the batch/allocation preamble. ReFrame does not treat
  MPI library selection and launcher selection as the same thing.
* `access` carries partition/account/queue options for the scheduler. Test-level
  `job.options` or `-J` can add options. `sched_options.sched_access_in_submit`
  controls whether access options are passed on the submit command rather than
  only in the generated script.
* `systems.partitions.modules` are loaded for every test on a partition;
  `environments.modules` are loaded for a named programming environment;
  `systems.modules` are loaded for every test on the system. Module objects can be
  strings or objects with `name`, `collection`, and optional `path`. The module
  system is configured with `modules_system` (for example `lmod` or `envmod`).
* `env_vars`, `prepare_cmds`, `prerun_cmds`, and `postrun_cmds` make the module and
  runtime setup explicit. Test-level `modules` and `env_vars` can be changed in
  hooks when a fixture or built artifact determines them.
* `features` and `extras` are metadata and selection controls. Features are
  requested with `+feature` or excluded with `-feature`; extras are requested with
  `%key=value`. This is a useful mapping for CSE's compiler/MPI/GPU lane metadata,
  but the values should be generated from the reviewed profile/release manifest,
  not inferred from an ambient module environment.
* `systems.partitions.max_jobs` defaults to 8 and limits concurrently active test
  cases when ReFrame uses asynchronous execution. It is a ReFrame concurrency
  limit, not a CPU budget; test resource requests and the outer allocation still
  determine whether concurrent jobs fit.

For additional scheduler-specific resource shapes, define partition resources and
request them from a test:

```python
# partition configuration
'resources': [{'name': 'gpu',
               'options': ['--gres=gpu:{num_gpus_per_node}']}]

# test
extra_resources = {'gpu': {'num_gpus_per_node': '4'}}
```

The [custom scheduler resources documentation](https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#custom-job-scheduler-resources)
states that placeholders are filled from `extra_resources`; PBS/Torque resources
can be qsub options or `-l` resource specifications. This is the right seam for a
site's GPU, memory, placement, or Cray-specific resource request without putting
Slurm/PBS syntax into the test logic.

For explicit launcher changes, a pre-run hook can set `self.job.launcher` using
`getlauncher('local')()`, or wrap the current launcher with a debugger/profiler
modifier. The [launcher guidance](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#modifying-the-launch-command)
also documents `self.job.launcher.options`, `modifier`, and
`modifier_options`. For CSE, the selected MPI provider and launcher command should
be recorded as one reviewed runtime tuple, then rendered into the ReFrame config
and checked in the generated script/log.

### 1.3 Parameterization, fixtures, and dependencies

ReFrame's `parameter()` creates variants across one or more dimensions. Existing
test variables can be parameterized on the command line with `-P`, for example
`-P num_tasks=1,2,4,8`. Fixtures can also be parameterized, implicitly creating
matching variants of dependent tests. The tutorial covers [multi-dimensional test
parameterization](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#test-parameterization).

Typical CSE dimensions are compiler surface, MPI provider, serial/MPI mode, node
type, task count, and module-chain variant. Keep the cross-product bounded with
parameter packs or a pruning hook; use explicit selection (`--system`, `-p`, `-n`,
tags) for a release's acceptance matrix rather than running every possible
combination by default.

Fixtures are normal tests with a scope. A fixture runs before its consumer and the
consumer can access the fixture's attributes and produced resources. Scope controls
reuse, such as one compiler probe per environment or one built microbenchmark per
system partition. This is a direct fit for “compile once, run several checks” and
for a small shared compiler/MPI probe suite. See [Test fixtures](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#test-fixtures).

Low-level dependencies use `depends_on()` and `getdep()`. The documentation says
the higher-level fixture API is generally preferable because it is more intuitive,
less error-prone, and more flexible. For parameterized dependencies, use
`get_variant_nums()` and `variant_name()` rather than assuming variant numbering.
See [Resolving dependencies](https://reframe-hpc.readthedocs.io/en/stable/howto.html#resolving-dependencies)
and [depending on parameterized tests](https://reframe-hpc.readthedocs.io/en/stable/howto.html#depending-on-parameterized-tests).

Important boundary: ReFrame's test DAG orders test preparation and checks; it does
not replace the global CSE lock verifier. All eight concrete locks still need to
pass before source installation or any Flux/ReFrame parallel work begins.

### 1.4 Sanity and performance checks

Every test must define a sanity result, either with a `@sanity_function` method or
the older `sanity_patterns` attribute. Sanity functions commonly use
`assert_found`, `assert_eq`, `assert_true`, `extractsingle`, and composition helpers
from `reframe.utility.sanity`. They are evaluated after the run from the test stage
directory and may return deferred expressions. A sanity function returns a boolean
or raises `SanityError`.

Performance functions use `@performance_function(unit)` and extract a figure of
merit from output. The `reference` dictionary can provide per-system and
per-partition target values with lower/upper fractional thresholds; missing
references are logged without being validated. The tutorial's [sanity and
performance section](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#mastering-sanity-and-performance-checking)
and [performance references](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#adding-performance-references)
show the exact forms.

For CSE acceptance, sanity checks should cover at least:

* compiler identity and language probes (C, C++, Fortran, `mpif.h`, `mpi`, and
  `mpi_f08` where applicable);
* loaded module chain and key wrapper/library paths;
* a two-rank MPI launch through the reviewed site launcher, not an ambient
  `mpiexec` discovered by CMake;
* package runtime probes (HDF5, NetCDF, FFTW, Boost, Dakota, or the system-specific
  acceptance set); and
* clean-session module visibility and executable/library resolution.

Performance functions are appropriate for bandwidth, MPI latency, scaling, and
other benchmark figures, but CSE should not turn a noisy performance baseline into
an installation gate until per-system references and tolerances are reviewed.

### 1.5 Reports, artifacts, logging, and retries

ReFrame keeps successful test artifacts in the output directory and failed test
artifacts in the stage directory. Generated job scripts, stdout, and stderr are
the default artifacts. The stage/output roots can be set by `--stage`, `--output`,
or `--prefix`; use deployment-owned or node-local paths appropriate to the CSE
release rather than a user's default home directory.

The tutorial documents three result forms:

* detailed session information in the ReFrame results database under
  `$HOME/.reframe/reports` by default;
* a JSON run report under the same report root, with `latest.json` unless
  `--report-file` is supplied; and
* performance CSV logs under `perflogs/<system>/<partition>/<testname>.log`, plus
  the `--performance-report` summary/comparison option.

Use `--report-file` and explicit stage/output/performance roots in CSE so the
release evidence is durable, attributable to `(system, stack, release, lane)`,
and not hidden in a builder's home directory. Preserve generated scripts and
scheduler output for launcher-debugging evidence. See [run reports and
performance logging](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#run-reports-and-performance-logging)
and [test artifacts/failures](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#inspecting-test-artifacts).

`--max-retries=N` retries failing tests at the end of the session, not immediately.
Each retry receives a separate stage directory; a test that later passes is marked
successful with an indication that it passed on retry. This is useful for
transient scheduler/node/network failures, but it must not hide deterministic ABI,
module, launcher, or package failures. The [retry documentation](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#retrying-tests)
also notes that `--keep-stage-files` and `--dont-restage` help debug or avoid
rebuilding expensive test dependencies. Separately, the configuration reference
has Slurm-only `resubmit_on_errors` for selected scheduler submission errors; that
is not a general test retry policy.

## 2. Flux inside an existing allocation

### 2.1 What Flux is and how it nests

Flux Core describes a Flux instance as a self-contained workload manager that can
run standalone, as a job in another resource manager, or recursively as a job in
Flux. An instance is a set of broker processes on a distributed overlay. A batch
job or interactive allocation is an independent Flux instance on a subset of its
parent's resources. See [Starting a Flux Instance](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/guide/start.html)
and [Working with Flux Job Hierarchies](https://flux-framework.readthedocs.io/en/latest/jobs/hierarchies.html).

The important nesting model is:

```text
site scheduler allocation (Slurm/PBS/Cray)
  -> external parallel launcher starts one Flux broker per selected node
    -> Flux instance owns the allocation's discovered cores/GPUs
      -> flux run / flux submit / flux batch schedule build and test jobs
        -> optional deeper Flux subinstances, only when isolation is needed
```

Flux's `flux start` normal mode does not itself launch all brokers. An external
launcher starts `flux start` in parallel, and the brokers use the launcher's PMI
bootstrap (or an explicit/static method). Flux documentation gives Slurm's
canonical form:

```bash
srun -N2 --pty --mpi=pmi2 flux start
```

For noninteractive batch use, the official example launches one broker per node
with `srun ... --mpi=none --mpibind=off flux start flux_batch.sh`, then the script
submits work inside Flux. The `--mpi=none`/`--mpibind=off` choices are not cosmetic:
they avoid having Slurm treat Flux's broker launch as an application MPI job and
avoid parent binding that can hide resources from Flux. See [Flux batch jobs,
including Slurm mode](https://flux-framework.readthedocs.io/en/latest/jobs/batch.html)
and the [Flux start command reference](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/man1/flux-start.html).

When started under a foreign resource manager, Flux discovers resources with
HWLOC. The official `flux-start` reference says that, if successful, `flux resource
info` should show all nodes, cores, and GPUs allocated by Slurm. The Flux FAQ warns
that parent binding can make resources appear missing and recommends checking
Slurm's `--mpibind=off` (and the analogous binding control for other managers).
The version of HWLOC must have the relevant GPU plugins enabled for GPU discovery.

Flux can therefore use an existing allocation without requesting a second outer
allocation. The enclosing manager owns the allocation lifetime and accounting;
Flux schedules only within the resource set visible to its instance.

### 2.2 Scheduling build jobs and ReFrame jobs

Inside the instance, `flux run` is blocking, while `flux submit` and `flux batch`
submit asynchronously. `flux queue drain` stops new submissions and waits for all
submitted jobs to complete. A Flux batch job creates a nested single-user Flux
instance allocated to that job's requested resources. Flux batch requests are
described using resource slots and shape options:

```bash
# Two independent locked build wrappers
flux submit --output=logs/build-gcc-{{id}}.out \
  --nodes=1 --cores-per-slot=32 ./build-one-environment.sh gcc-core
flux submit --output=logs/build-mpi-{{id}}.out \
  --nodes=2 --cores-per-slot=32 ./build-one-environment.sh gcc-mpi
flux queue drain

# Then run acceptance jobs, or submit them and drain once at the end
flux submit --nodes=2 --cores-per-slot=4 ./reframe-lane.sh gcc-mpi
flux queue drain
```

The exact option vocabulary is `--nslots`, `--cores-per-slot`, `--gpus-per-slot`,
`--nodes`, and `--exclusive` for `flux batch`/`flux alloc`; `flux run` and
`flux submit` also support task-oriented options such as `--ntasks`. See the
[Flux batch job reference](https://flux-framework.readthedocs.io/en/latest/jobs/batch.html)
and [flux-batch(1)](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/man1/flux-batch.html).

For CSE, the outer driver should implement explicit phases:

1. validate the rendered workspace, all eight lockfiles, and the cross-node
   prefix/database-lock smoke test;
2. submit one Flux job per distinct locked environment (never submit the same
   environment twice), with a resource shape and `BUILD_JOBS` budget that fit the
   outer allocation;
3. wait for all build jobs and verify their logs, concrete hashes, and shared-store
   state;
4. submit ReFrame acceptance jobs that consume the resulting release module
   chains; and
5. drain, collect reports, and promote only artifacts satisfying the existing
   release gates.

This preserves the local execution model's rule that identical Spack hashes may
wait on shared locks and reuse a completed prefix, while distinct environments can
run concurrently. Flux does not replace Spack's prefix/database locking or the
project's global lock verifier.

### 2.3 Resource and broker layout

The minimal production layout is one Flux broker per outer-allocation node. Rank 0
hosts the leader and initial program; the other broker ranks provide the distributed
instance. The Flux FAQ notes that the rank-0 broker can need significant CPU and
memory for large fast-cycling workloads and suggests draining rank 0 from scheduling
when appropriate. For the relatively small CSE environment matrix, reserve a
small broker budget and measure before adding complexity.

Flux resources are represented internally as a hierarchical resource graph. The
instance can subdivide the allocation using nested jobs. A nested `flux batch`
instance is useful when a build/test group needs its own queue or lifecycle, but
unnecessary nesting increases observability and failure complexity. The hierarchy
guide explicitly warns that even small hierarchies can be challenging to understand;
record parent job IDs, child job IDs, resource shape, and instance depth in CSE
evidence.

Flux's initial-program environment intentionally unsets several enclosing-manager
variables, including `SLURM_*`, `PMI_*`, `PMIX_*`, and `PALS_*`, to prevent accidental
interpretation of foreign-manager state. It provides `FLUX_URI`; scripts should use
Flux queries such as `flux resource list -n -o {nnodes}`,
`{ncores}`, `{ngpus}`, and `flux getattr hostlist` instead of assuming Slurm/PBS
variables are available. See [flux-environment(7)](https://flux-framework.readthedocs.io/projects/flux-core/en/latest/man7/flux-environment.html).

The Flux KVS/state directory defaults can matter on clusters where `/tmp` is a
small RAM-backed filesystem. The official FAQ documents using `--broker-opts` or
`-Sstatedir=...` to place persistent broker state on a suitable path; set this in
the site wrapper and retain it as operational evidence.

### 2.4 ReFrame and Flux integration

ReFrame's current configuration reference lists `flux` as a supported scheduler
backend, and the official ReFrame how-to includes a Flux configuration and run
example. The integration is therefore a supported ReFrame execution mode, not a
home-grown adapter. See [Using the Flux framework scheduler](https://reframe-hpc.readthedocs.io/en/stable/howto.html#using-the-flux-framework-scheduler)
and the [scheduler configuration reference](https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#system-partition-configuration).

Run ReFrame from within the active Flux instance and configure a partition whose
`scheduler` is `flux`; select a launcher appropriate to the test program and site
(`local` for a one-task probe or a reviewed MPI launcher for multi-rank tests).
Use ReFrame's test resource fields and `extra_resources` to express shape. If
ReFrame itself is launched outside Flux with `scheduler='slurm'` or `pbs`, it will
submit independent jobs to the outer scheduler rather than use the existing Flux
instance; that is a different execution mode and can accidentally request nested
allocations.

For a CSE nested-Flux path, the driver should:

* launch and validate the Flux instance first (`flux uptime`, `flux resource info`,
  `flux getattr hostlist`);
* set the ReFrame partition scheduler to `flux` and configure its stage/output/
  report roots explicitly;
* generate/list the concrete test cases before running them;
* bound ReFrame `max_jobs` to the free resources after broker reservation;
* run the two-rank MPI sanity test through the selected provider launcher; and
* archive the ReFrame report together with Flux job IDs and the parent allocation.

Do not infer a launcher from `PATH` or from CMake's `MPIEXEC` discovery. The CSE
finding about an unrelated MVAPICH2 `mpiexec` is exactly the failure mode to guard
against.

### 2.5 Slurm, PBS, and Cray constraints

The official Flux examples provide strong evidence for Slurm-in-allocation
operation. Flux Core also states that it can be started as a parallel job under
most HPC resource managers and launchers, and its `flux start` interface uses a
placeholder `[launcher]`. However, the primary examples and troubleshooting
guidance are not a promise that every site's PBS, Cray ALPS/PALS, PMI, security,
or network setup works without adaptation.

For PBS/PBS Professional, the safe interpretation is: obtain a PBS allocation,
then use the site's verified multi-node launcher (or a static broker bootstrap)
to start one Flux broker per node. ReFrame has native `pbs`/`pbspro` backends for
direct submission, but Flux-in-PBS still needs an integration wrapper and a real
allocation test. Do not claim PBS support merely because the ReFrame scheduler
list contains `pbs`.

For Cray systems, validate the exact CPE/Cray launcher, PMI implementation, CPU/GPU
binding, network reachability among brokers, and interaction with the platform MPI
provider. A Cray MPICH environment may be able to launch Flux, but this must be
proved with the reviewed site launcher and module chain; do not substitute a
source-built scheduler or MPI stack for the platform runtime. The project's own
runbook already requires retaining inspected Cray MPICH/PMI/fabric records and
running a two-rank acceptance launch.

## 3. Risks and limitations

### ReFrame risks

1. **Spack authority split.** ReFrame's Spack backend creates a stage-local Spack
   environment and invokes concretize/install. This conflicts with the CSE rule
   that reviewed `spack.lock` files and the selected build path own concretization
   and publication. Keep ReFrame's Spack mode out of the release build path.
2. **Scheduler/launcher ambiguity.** ReFrame deliberately models the batch
   scheduler and parallel launcher separately. A correct compiler/MPI wrapper does
   not prove that the launch command is correct. Render and verify both.
3. **Concurrent-job oversubscription.** `max_jobs` limits active test cases, not
   aggregate CPU, memory, GPU, or network usage. Combine ReFrame's limit with Flux
   resource requests and the per-process Spack `BUILD_JOBS` budget.
4. **Parameterized explosion.** Compiler × MPI × GPU × node type × task-count
   matrices can become large. Use explicit release acceptance sets, parameter
   pruning, and test listing as a gate.
5. **Retry masking.** `--max-retries` is useful for transient failures but can turn
   a flaky launcher or underspecified resource request into an apparent pass. Keep
   first-failure logs, retry directories, and the reason for allowing a retry.
6. **Module-shell portability.** Generated scripts depend on the configured module
   backend and shell. Validate clean sessions on each system; do not rely on the
   ReFrame process's already-loaded module state.
7. **Report location and retention.** Defaults under a user's home directory are
   not a durable release record. Set explicit roots and include the report in the
   release evidence tree.

### Flux risks

1. **Bootstrap/PMI failure.** A missing or mismatched PMI client can cause multiple
   singletons instead of one multi-node instance. The Flux docs recommend reducing
   the allocation, tracing PMI, and checking `FLUX_PMI_CLIENT_METHODS` when this
   happens. Treat `flux resource info` node count as a mandatory gate.
2. **Binding hides resources.** Parent Slurm/Cray/PBS binding can cause HWLOC to
   report fewer cores/GPUs than allocated. Start broker ranks with the site's
   documented binding controls and compare Flux's inventory to the allocation.
3. **Network overlay.** Brokers must reach one another over the cluster network.
   Firewall, interface selection, IPv4/IPv6, random-port policy, or Cray fabric
   isolation can prevent quorum even when PMI succeeds.
4. **Foreign-manager state is intentionally removed.** Flux unsets `SLURM_*`,
   `PMI_*`, `PMIX_*`, and related variables in initial programs. Build/test wrappers
   that depend on those variables must query Flux or receive explicit values.
5. **Nested accounting and policy.** The outer scheduler accounts for one
   allocation while Flux schedules many jobs inside it. Site policy may prohibit
   user-level nested schedulers, and node-local scratch, walltime, or fair-share
   policy may not match the inner queue's assumptions.
6. **Broker overhead and failure domain.** A lost critical broker can terminate the
   instance; rank-0 resource use can reduce effective capacity. Flux's hierarchy
   and failure behavior need site-specific runbook entries.
7. **PBS/Cray evidence gap.** Official primary material gives concrete Slurm
   examples and general foreign-launch guidance, not a universal PBS or Cray
   recipe. A CSE recommendation must remain conditional until those systems pass
   broker, resource, MPI, and recovery tests.
8. **State/KVS pressure.** Long or high-throughput workflows can fill `/tmp` via
   Flux's SQLite-backed KVS. Configure a suitable `rundir`/`statedir` and output
   redirection, especially when many build logs are produced.
9. **Observability complexity.** A site job contains a Flux instance, which contains
   Flux jobs, which may run ReFrame jobs and fixtures. Preserve parent/child IDs,
   generated scripts, and reports or diagnosis becomes difficult.

## 4. Evidence-backed CSE adoption plan

### Phase 1: ReFrame without Flux

1. Build and publish using the current CSE path: render, fresh-concretize, verify
   all eight locks, install, exercise lanes, push cache, and cache-only publish.
2. Add a small ReFrame test library that consumes published modules and explicit
   launcher metadata. Start with compiler identity, serial C/C++/Fortran, MPI
   wrappers, two-rank launch, HDF5/NetCDF/FFTW/Boost/Dakota smoke checks, and clean
   module-session checks.
3. Configure one ReFrame partition per execution context (login/local,
   Slurm-compute, PBS-compute, and any Cray-specific context), with explicit
   scheduler, launcher, access, modules, env vars, and report roots.
4. Use fixture scope to compile a probe once per compiler/MPI environment and reuse
   it across runtime checks. Keep acceptance parameterization bounded and list the
   concrete test cases before execution.
5. Preserve generated scripts, stdout/stderr, JSON report, performance logs, and
   scheduler job IDs as lane evidence. Exercise `--max-retries` only for named
   operational failure classes.

### Phase 2: optional Flux accelerator

1. In one approved Slurm allocation, start one Flux broker per node with the site's
   verified PMI/binding/network options. Confirm node/core/GPU inventory exactly
   matches the outer allocation.
2. Submit two harmless multi-node probes with `flux run`; verify hostlist, rank
   count, CPU/GPU visibility, module loading, and MPI launcher behavior.
3. Submit two independent locked build wrappers with different resource shapes;
   verify that the shared store/database locks, cache partitions, and CSE group
   permissions behave as required. Never run one environment twice.
4. Run ReFrame with its `flux` scheduler backend inside the instance, first with
   one test and `max_jobs=1`, then increase concurrency while measuring broker and
   filesystem behavior. Keep ReFrame's compile/build tests separate from the
   release's authoritative Spack build unless they are explicitly independent
   probes.
5. Add Flux job IDs, instance depth, `flux resource list`, `flux jobs`, and queue
   drain status to the release evidence. Test cancellation, timeout, node loss, and
   outer-allocation expiry before making Flux a supported operational path.
6. Repeat the bootstrap and acceptance procedure on PBS and Cray only after each
   system's launcher/PMI/network/site policy owner approves the exact wrapper.

### Final decision rule

ReFrame is recommended for CSE acceptance and regression evidence now, with the
explicit configuration and lifecycle boundaries above. Flux is recommended as a
conditional, driver-owned optimization for many independent jobs inside a single
allocation. It should remain optional until Slurm, PBS, and Cray acceptance proves
that Flux's broker bootstrap, resource discovery, MPI launch, node binding, state
paths, failure handling, and site policy all hold. Neither tool should be placed in
Stack Composer's pure render seam.

## Primary sources

* [ReFrame Tutorial (stable)](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html)
* [ReFrame How Tos (stable)](https://reframe-hpc.readthedocs.io/en/stable/howto.html)
* [ReFrame Configuration Reference (stable)](https://reframe-hpc.readthedocs.io/en/stable/config_reference.html)
* [ReFrame regression-test API](https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html)
* [ReFrame source repository](https://github.com/reframe-hpc/reframe)
* [Flux Core: Starting a Flux Instance](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/guide/start.html)
* [Flux Core: `flux-start(1)`](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/man1/flux-start.html)
* [Flux Core: `flux-batch(1)`](https://flux-framework.readthedocs.io/projects/flux-core/en/stable/man1/flux-batch.html)
* [Flux Framework: Batch Jobs](https://flux-framework.readthedocs.io/en/latest/jobs/batch.html)
* [Flux Framework: Job Hierarchies](https://flux-framework.readthedocs.io/en/latest/jobs/hierarchies.html)
* [Flux Core: `flux-environment(7)`](https://flux-framework.readthedocs.io/projects/flux-core/en/latest/man7/flux-environment.html)
* [Flux Core FAQ (official source repository)](https://github.com/flux-framework/flux-docs/blob/master/faqs.rst)
* [Flux Core source repository](https://github.com/flux-framework/flux-core)
* [Fluxion scheduler source repository](https://github.com/flux-framework/flux-sched)
