# Standalone hardening build and test runbooks

Date: 2026-10-06. Target: Linux x86-64 with glibc. Build method: upstream source, outside Spack. These procedures have been checked against source/build documentation and locally checked for shell syntax; the target Linux builds and performance trial have not been executed.

Profile update 2026-10-07: the default now matches the supplied list: **strong stack protection, FORTIFY level 2, RELRO/NOW, and executable PIE**. The exact settings and injection points are in [01](01-common.md) and each package's build section. The earlier broader set is an explicit `extended` experiment. Use a new trial root if you already built the earlier full profile; changing the environment does not rebuild old binaries.

Environment update 2026-10-08: begin with [build environment and system dependencies](00-build-environment.md). Required site master modules and the existing Slurm/fabric installation are retained; explicit executable/runtime paths prevent inherited AOCC and MPI selections from contaminating the private builds. UCX and Open MPI are private source builds, not the site's installed UCX/MPI.

Download update 2026-10-09: FFTW source staging now tries independent HTTPS mirrors after the upstream URL and verifies the pinned SHA-256 before accepting a download. For an existing trial, follow the [FFTW-only retry procedure](00-gcc-bootstrap.md#retry-fftw-after-a-certificate-error).

If GCC's prerequisite download is blocked, use the [direct HTTPS downloads and offline transfer procedure](00-gcc-bootstrap.md#stage-gcc-prerequisites-for-a-machine-without-download-access). Stage all four pinned source archives inside the GCC source root; the bundled helper verifies and unpacks them without a download request.

The [Slurm campaign plan](08-slurm-campaign.md) defines hypotheses and the actual ReFrame matrix, including serial/threaded cases, small-dataset HDF5, startup/PIE comparisons, and 1/2/4/8-node MPI runs. It generates sequential batch submission and collects all phase results into a CSV. The bootstrap seed defaults to the installed `/usr/bin/gcc` and `/usr/bin/g++`; payloads use private GCC 12.5. Regenerate/recompile the updated callers and ReFrame files before running this campaign.

The [results presentation plan](09-results-presentation.md) includes a five-page PDF draft, illustrative plots, native ReFrame history options and a possible Grafana route. All example chart values are invented; use the collected campaign outputs for actual performance conclusions.

The [repeatability plan](08-slurm-campaign.md#repeatability-and-a-manageable-first-assessment) starts with a 10-pair qualification pilot, then 20 pairs per case across three allocations on the initial 1/2-node coverage. Seek different homogeneous hosts and record actual placement. `ALLOCATION_REPEATS` controls batch repetitions; summaries and CSV retain arithmetic means/sample standard deviations alongside the paired effect and interval. Regenerate `paired.py`, ReFrame definitions, batch scripts and the collector from 01/06/08 to use these additions; this update does not require rebuilding unchanged library/caller binaries. Keep allocation estimates separate in the report.

[10 — Single allocation campaign](10-single-allocation.md) adds a second mode: reserve 8/4/2 nodes once, run serial cases on each host and MPI on selected subsets, and repeat predetermined rounds. CPU cases can run concurrently on different hosts; HDF5/MPI cases are sequential. Smaller reservations explicitly record unavailable scales. The separate-job campaign in 08 remains the fallback. Regenerate the paired harness, ReFrame definitions and collector from 01/06/08 for selected-host verification/metadata, then generate the new scripts in 10. Qualified unchanged libraries/callers need no recompilation.

## Download onto the test machine

The current alpha host is [ray12514/stack-planning on GitHub](https://github.com/ray12514/stack-planning/tree/codex/node-build-resources/docs/standalone-hardening), branch **`codex/node-build-resources`**. The runbooks live in `docs/standalone-hardening/`. This repository is public; HTTPS cloning and archive downloads require no GitHub sign-in. `stack-content` is a separate, private repository and does not contain these standalone runbooks.

### Clone with Git

Clone over HTTPS:

```bash
git clone --branch codex/node-build-resources --single-branch \
  https://github.com/ray12514/stack-planning.git stack-planning-hardening
cd stack-planning-hardening/docs/standalone-hardening
less README.md
```

In an existing checkout, fetch and switch to `codex/node-build-resources` before reading the runbooks. Record `git rev-parse HEAD` with the trial results so the procedure version is reproducible.

### Download an archive

Download the branch snapshot with curl:

```bash
curl -fL --retry 3 -o stack-planning-hardening.tar.gz \
  https://codeload.github.com/ray12514/stack-planning/tar.gz/refs/heads/codex/node-build-resources
sha256sum stack-planning-hardening.tar.gz > stack-planning-hardening.tar.gz.sha256
mkdir stack-planning-hardening
tar -xzf stack-planning-hardening.tar.gz --strip-components=1 \
  -C stack-planning-hardening
cd stack-planning-hardening/docs/standalone-hardening
less README.md
```

The GitHub branch page also offers **Code → Download ZIP**. Extract the archive and open `docs/standalone-hardening/README.md`. Retain the archive and its checksum with the results. For a fixed snapshot, use `https://codeload.github.com/ray12514/stack-planning/tar.gz/FULL_COMMIT_SHA` with the recorded commit SHA in place of `FULL_COMMIT_SHA`.

### Transfer to an offline machine

Download on a connected staging machine first. Transfer the archive and checksum through the site's transfer route, verify with `sha256sum --check stack-planning-hardening.tar.gz.sha256`, and extract as above. The runbook archive contains instructions and embedded source code; stage the GCC/package sources, GCC prerequisites, MPI/UCX sources, and Python wheels separately using 00, 00b, and 06. Build Linux toolchains on compatible Linux systems.

If the folder is already on your Mac, copy it directly, replacing `USER` and `TEST_HOST`:

```bash
rsync -av \
  /Users/ravonventers/Development/stack-planning/docs/standalone-hardening/ \
  USER@TEST_HOST:~/hardening-runbooks/
```

## Prepare and run

Use a Bash shell on the Linux build/test system. Follow the command blocks in the runbooks below in order; the Markdown files are procedures, with heredocs that create the actual benchmark sources and ReFrame configuration under `TRIAL_ROOT`.

1. Choose a writable absolute `TRIAL_ROOT` visible at the same path on execution nodes, with no whitespace in the path. Keep the downloaded documentation in its own folder.
2. Follow the environment procedure to establish required master modules and explicit search paths, then 00 to bootstrap GCC 12.5.0 or install a compatible transferred toolchain. GCC 12.5 is assumed absent. A source bootstrap needs a working seed C/C++ compiler and OS development files; 00 covers the route when no compiler exists.
3. Follow 01 to create and qualify the explicit flags before package builds.
4. Build the serial package variants and fixed callers with 02–04. Build and qualify Open MPI + UCX with 00b, then follow 05 for parallel FFTW/HDF5.
5. Follow 06 sections 1–3 to install ReFrame and create its configuration and checks. Use its serial or parallel launch procedure inside a compute allocation.
6. Follow 07 to build PIE comparators, then 08 for the hypotheses, expanded matrix, Slurm sequence and data collection. Supply the site's master-module setup, account, partition/node constraint, I/O directory and resource limits.
7. Optionally use 10 to run selected nodes/rounds inside one allocation; retain 08 for separate jobs and checks across independent allocations.

After the serial builds and ReFrame setup, this runs the three-package pilot. Replace the root, CPU, and I/O directory with the trial's chosen values:

```bash
export TRIAL_ROOT=/absolute/path/to/hardening-trial
source "$TRIAL_ROOT/env.sh"
export CPUSET=0  # replace with an allocated CPU
export IO_DIR=/absolute/path/to/test-filesystem/hdf5-hardening-trial
mkdir -p "$IO_DIR"
export WORKLOADS=fft-small,hdf5-contiguous,lapack-small
export COMPARATORS=reference PAIRS=10
export RUN_ID
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$TRIAL_ROOT/results/reframe/$RUN_ID"
REFRAME="$TRIAL_ROOT/tools/reframe-venv/bin/reframe"
"$REFRAME" -C "$TRIAL_ROOT/reframe/settings.py" \
  -c "$TRIAL_ROOT/reframe/hardening.py" -l
"$REFRAME" -C "$TRIAL_ROOT/reframe/settings.py" \
  -c "$TRIAL_ROOT/reframe/hardening.py" -r --exec-policy=serial \
  --performance-report --prefix="$TRIAL_ROOT/results/reframe/$RUN_ID/rfm" \
  --report-file="$TRIAL_ROOT/results/reframe/$RUN_ID/report.json" \
  2>&1 | tee "$TRIAL_ROOT/results/reframe/$RUN_ID/console.log"
```

The terminal and `console.log` show correctness status, full/reference seconds, runtime change %, and confidence interval endpoints. `report.json` stores ReFrame results; `paired/` stores raw CSV, caller logs, loaded-library records, and summaries. PASS establishes successful correctness and measurement checks; apply an agreed slowdown limit as described in 06 when judging overhead. Use a new `RUN_ID` for every session.

## Run order

| Runbook | Outcome |
|---|---|
| [Build environment and system dependencies](00-build-environment.md) | Required master modules, explicit search paths, removal of inherited compiler/MPI overrides, and existing Slurm/fabric provenance |
| [00 — Bootstrap GCC 12.5.0](00-gcc-bootstrap.md) | A private GCC C/C++/Fortran installation, binutils, CMake, verified package sources, and a reusable environment file |
| [01 — Common hardening profiles and measurement](01-common.md) | Full profile, optimized reference, individual control removal, compiler qualification, and paired timing procedure |
| [00b — Open MPI 4.1.8 + UCX 1.16.0](00b-openmpi-ucx.md) | One fixed GNU-built MPI/UCX installation, wrapper checks, and a two-node transport qualification |
| [02 — FFTW 3.3.11](02-fftw.md) | Shared serial/threaded FFTW variants, correctness tests, and separate planning/execution measurements |
| [03 — HDF5 2.1.0](03-hdf5.md) | Shared serial HDF5 variants, correctness tests, and contiguous/chunked read/write measurements |
| [04 — LAPACK 3.12.1](04-lapack.md) | Shared LAPACK variants, one fixed reference BLAS, correctness tests, and LU solve measurements |
| [05 — Parallel FFTW and HDF5](05-parallel.md) | MPI-enabled variants, distributed FFTs, and collective/independent parallel HDF5 I/O |
| [06 — ReFrame driver and reports](06-reframe.md) | Paired comparisons, correctness gates, terminal performance tables, raw CSV, and JSON reports |
| [07 — Executable PIE comparison](07-consumer-pie.md) | PIE versus non-PIE callers with full libraries fixed, reporting whole-process elapsed time |
| [08 — Slurm campaign and hypotheses](08-slurm-campaign.md) | Predeclared comparisons, serial/threaded and 1/2/4/8-node matrix, Slurm submission, placement verification, and all-phase CSV collection |
| [09 — Results presentation](09-results-presentation.md) | Illustrative PDF and plots, audience narrative, result-to-figure mapping, history options and Grafana design |
| [10 — Single allocation campaign](10-single-allocation.md) | Optional 8/4/2-node reservation, host/subset rotation, repeated rounds, CPU concurrency, serial I/O/MPI steps and capacity/failure records |

Run 00 and 01 once, then 02–04 for serial packages. Run 00b after qualifying the profiles in 01, then 05 for parallel packages. Use 06 to drive and report either suite after its variants and fixed callers are installed, and 07 for executable PIE. Start with `full` and `reference`; each removal starts from `full`. `stack-all` is an optional stronger-stack comparison. Extended-set controls require a separate, explicitly labelled trial root.

Versions match the current trial roster. Binutils 2.44 is a runbook pin; it is not claimed to be the binutils version used by every existing trial. CMake 3.31.12 matches the roster's build-tool pin. HDF5 2.1.0 is the selected trial input, not a recommendation to replace it with the current upstream release.

The initial workloads cover serial CPU and I/O costs. FFTW threads are built and can be measured separately. The parallel phase uses **Open MPI 4.1.8 with UCX 1.16.0**, matching the trial pins; build and qualify it once with GCC 12.5 and hold it fixed. Select and record the UCX transport for the actual fabric, and use a compute allocation. Serial results do not establish parallel-I/O or MPI-FFT performance.

## What the trial answers

The listed full profile uses `-fstack-protector-strong`, C/C++ `-D_FORTIFY_SOURCE=2`, `-Wl,-z,relro`, and `-Wl,-z,now`. Benchmark executables use `-fPIE -pie`; shared libraries retain `-fPIC`. PIC, a non-executable stack, optimization, and warnings stay fixed across library arms.

The optional extended set adds controls described in 01. Sanitizers and Fortran bounds diagnostics are separate experiments. The [HPCMP policy alignment note](../hpcmp_compiler_hardening_policy_alignment_v1.md) explains the public program model and why central flag configuration alone does not establish STIG compliance. A measured removal may support a package-specific decision; it does not establish a universal performance exemption.

The primary package comparisons use one fixed benchmark executable while switching its loaded library. That isolates package changes. A separate consumer comparison changes executable hardening too; those results must be labelled separately. For LAPACK the fixed BLAS rule is particularly important.

## Inputs the operator selects

* A writable absolute `TRIAL_ROOT`, visible on the compute node, with no whitespace in its path.
* A bootstrap C/C++ compiler or a compatible approved GCC binary installation when no compiler exists.
* Required master modules, the existing Slurm client directory, and explicit approved utility/runtime directories. Do not inherit an AOCC/MPI environment wholesale.
* A compute allocation, build parallelism, and one recorded CPU target. The default is `x86-64`, portable across x86-64 nodes; select `x86-64-v3` only when every execution node supports it. Do not use `-march=native` on a different login-node CPU.
* A test filesystem directory, CPU affinity list within the allocation, and an acceptable regression threshold chosen before results.
* `HARDENING_SET=listed` and `FORTIFY_LEVEL=2` for the supplied list. Qualify compiler acceptance and actual artifacts before measurements; select the extended set only for a separate experiment.

No system compiler or system library is replaced by these procedures. Installed trial prefixes and logs remain available for reruns. Use a new build directory/prefix when changing flags or prerequisites; these commands refuse to reuse a package build directory.
