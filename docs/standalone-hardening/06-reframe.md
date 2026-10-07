# 06 — Drive the hardening trial with ReFrame

ReFrame drives the tests against the already-built package variants. It runs the paired timing harness from [01](01-common.md), checks that the measurements completed correctly, extracts runtimes and changes, and prints a performance table. Raw paired CSV, driver logs, loaded-library records, and JSON summaries are preserved. It does not need Spack.

The configuration below runs locally **inside an existing scheduler allocation**. Serial checks constrain the caller to `CPUSET`; parallel checks use the fixed Open MPI + UCX launcher and mapping. This keeps paired runs on the same allocation instead of submitting a different allocation for each hardening arm. Use ReFrame's serial execution policy so workloads do not compete for CPUs or the test filesystem.

## 1. Install a pinned ReFrame in a private environment

Python 3.10 or later is required. ReFrame is independent of GCC's bootstrap. On a connected staging host, prepare wheels for this Python/platform, then transfer them if the target cannot reach PyPI. No Python libraries are installed into the system environment.

```bash
source "$TRIAL_ROOT/env.sh"
python3 -m venv "$TRIAL_ROOT/tools/reframe-venv"
"$TRIAL_ROOT/tools/reframe-venv/bin/python" -m pip install 'reframe-hpc==4.10.4'
export REFRAME="$TRIAL_ROOT/tools/reframe-venv/bin/reframe"
"$REFRAME" --version
```

Offline alternative on the staging host: `python3 -m pip download 'reframe-hpc==4.10.4' -d /path/to/wheels`, using a host with the same Python ABI, OS and architecture as the test system. Transfer the wheels, then use `pip install --no-index --find-links=/path/to/wheels 'reframe-hpc==4.10.4'` inside the private environment. Retain the package/version list with the results. See [ReFrame 4.10.4](https://pypi.org/project/reframe-hpc/4.10.4/) and the [official tutorial](https://reframe-hpc.readthedocs.io/en/stable/tutorial.html).

## 2. Create the allocation-local configuration

```bash
mkdir -p "$TRIAL_ROOT/reframe" "$TRIAL_ROOT/results/reframe"
cat > "$TRIAL_ROOT/reframe/settings.py" <<'PY'
import os
root = os.environ['TRIAL_ROOT']
site_configuration = {
    'systems': [{
        'name': 'hardening', 'descr': 'Standalone GCC 12.5 trial allocation',
        'hostnames': ['.*'],
        'partitions': [{
            'name': 'allocation', 'scheduler': 'local', 'launcher': 'local',
            'environs': ['gcc125']
        }]
    }],
    'general': [{'topology_prefix': root + '/reframe/topology'}],
    'environments': [{
        'name': 'gcc125',
        'cc': root + '/toolchains/gcc-12.5.0/bin/gcc',
        'cxx': root + '/toolchains/gcc-12.5.0/bin/g++',
        'ftn': root + '/toolchains/gcc-12.5.0/bin/gfortran'
    }]
}
PY
```

The environment names the compiler for provenance. These are run-only checks; the configuration does not build GCC or replace the compiler selected by the build runbooks.

## 3. Create the test definition

Initially `COMPARATORS=reference`. After installing selected removal variants, use e.g. `COMPARATORS=reference,minus-stack,stack-strong`. ReFrame expands the workload/comparator combinations. `minus-fortify` and `minus-init` are skipped for Fortran LAPACK because they do not create a meaningful Fortran contrast.

The primary HDF5 metric shown in the table is write/create/close. Read timing is retained in each summary and raw CSV. FFTW's primary metric is execution; planning is retained separately. One full/comparator check includes the warmups and all `PAIRS` independent timing pairs.

```bash
cat > "$TRIAL_ROOT/reframe/hardening.py" <<'PY'
import json
import os
import pathlib
import shlex
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import parameter, run_after, run_before
from reframe.core.builtins import sanity_function, performance_function

ROOT = pathlib.Path(os.environ['TRIAL_ROOT'])
WORKLOADS = {
    'fft-small': ('fftw', 'fftw-fixed', 'execution', ['1','1024','50000','1','estimate'], False),
    'fft-large': ('fftw', 'fftw-fixed', 'execution', ['1','1048576','30','1','estimate'], False),
    'fft-3d': ('fftw', 'fftw-fixed', 'execution', ['3','64','100','1','estimate'], False),
    'hdf5-contiguous': ('hdf5', 'hdf5-fixed', 'write_create_close', ['@FILE@','16777216','0','0'], False),
    'hdf5-chunked': ('hdf5', 'hdf5-fixed', 'write_create_close', ['@FILE@','16777216','65536','0'], False),
    'lapack-small': ('lapack', 'lapack-fixed', 'lu_solve', ['128','50'], False),
    'lapack-large': ('lapack', 'lapack-fixed', 'lu_solve', ['1024','3'], False),
    'fft-mpi': ('fftw-mpi', 'fftw-mpi-fixed', 'execution_maxrank', ['64','100','estimate'], True),
    'hdf5-collective': ('hdf5-mpi', 'hdf5-mpi-fixed', 'write_collective_maxrank', ['@FILE@','8388608','collective'], True),
    'hdf5-independent': ('hdf5-mpi', 'hdf5-mpi-fixed', 'write_independent_maxrank', ['@FILE@','8388608','independent'], True)
}
SELECTED = os.environ.get('WORKLOADS', 'fft-small,hdf5-contiguous,lapack-small').split(',')
COMPARATORS = os.environ.get('COMPARATORS', 'reference').split(',')
if any(w not in WORKLOADS for w in SELECTED):
    raise ValueError('Unknown WORKLOADS entry')

@sn.deferrable
def metric(stdout, phase, key, index=None):
    value = json.loads(pathlib.Path(stdout).read_text())['phases'][phase][key]
    return value if index is None else value[index]

@rfm.simple_test
class HardeningTrial(rfm.RunOnlyRegressionTest):
    workload = parameter(SELECTED)
    comparator = parameter(COMPARATORS)
    valid_systems = ['hardening:allocation']
    valid_prog_environs = ['gcc125']
    sourcesdir = None
    time_limit = '30m'

    @run_after('init')
    def describe(self):
        self.tags = {'hardening', 'mpi' if WORKLOADS[self.workload][4] else 'serial'}
        self.descr = f'{self.workload}: full vs {self.comparator}, paired measurements'

    @run_before('run')
    def prepare(self):
        package, driver, phase, arguments, mpi = WORKLOADS[self.workload]
        self.skip_if(package == 'lapack' and self.comparator in ('minus-fortify','minus-init'),
                     'Control does not apply to Fortran LAPACK')
        session = os.environ['RUN_ID']
        io_dir = pathlib.Path(os.environ['IO_DIR'])
        if not io_dir.is_dir():
            raise ValueError('IO_DIR must be a dedicated existing trial directory')
        filename = io_dir / f'reframe-{self.workload}-{self.comparator}-{session}.h5'
        arguments = [str(filename) if a == '@FILE@' else a for a in arguments]
        self._phase = phase
        command = [str(ROOT/'bench'/'paired.py'), package,
                   str(ROOT/'bench'/driver), self.workload, *arguments]
        self.env_vars = {
            'TRIAL_ROOT': str(ROOT), 'GCC_LIB_DIRS': os.environ['GCC_LIB_DIRS'],
            'RESULT_ROOT': str(ROOT/'results'/'reframe'/session/'paired'),
            'COMPARE': self.comparator, 'PAIRS': os.environ.get('PAIRS','10'),
            'MPI_NP': os.environ.get('MPI_NP','2') if mpi else '0',
            'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'
        }
        if mpi:
            for name in ('MPI_PREFIX','MPI_LIB_DIRS','MPI_MAP','OMPI_MCA_io'):
                self.env_vars[name] = os.environ[name]
            for name in ('MPI_EXTRA_ARGS','UCX_TLS','UCX_NET_DEVICES'):
                if name in os.environ:
                    self.env_vars[name] = os.environ[name]
            self.executable = 'python3'
            self.executable_opts = [shlex.quote(arg) for arg in command]
        else:
            self.executable = 'taskset'
            self.executable_opts = [shlex.quote(arg) for arg in
                                    ['-c', os.environ['CPUSET'], 'python3', *command]]

    @sanity_function
    def measurements_completed(self):
        checks = [sn.assert_eq(self.job.exitcode, 0),
                  sn.assert_found(r'"runtime_ratio_full_over_comparator"', self.stdout)]
        limit = os.environ.get('MAX_SLOWDOWN_PERCENT')
        if limit is not None:
            checks.append(sn.assert_le(metric(self.stdout, self._phase,
                'bootstrap_95_percent_interval', 1), float(limit)))
        return sn.all(checks)

    @performance_function('s')
    def full_seconds(self):
        return metric(self.stdout, self._phase, 'full_runtime_seconds_geomean')

    @performance_function('s')
    def comparator_seconds(self):
        return metric(self.stdout, self._phase, 'comparator_runtime_seconds_geomean')

    @performance_function('%')
    def full_runtime_increase(self):
        return metric(self.stdout, self._phase, 'full_runtime_increase_percent')

    @performance_function('%')
    def interval_low(self):
        return metric(self.stdout, self._phase, 'bootstrap_95_percent_interval', 0)

    @performance_function('%')
    def interval_high(self):
        return metric(self.stdout, self._phase, 'bootstrap_95_percent_interval', 1)
PY
```

Without `MAX_SLOWDOWN_PERCENT`, PASS means the drivers' correctness checks and paired measurement procedure completed; it does not mean the overhead is acceptable. If an agreed limit is set, the sanity check also requires the upper interval bound of the primary metric to be below it. Do not use that same gate automatically for removal comparators: those show the incremental cost of a control, not total overhead versus reference.

## 4. List and run the serial pilot

Use a compute allocation and replace `CPUSET` with an allocated CPU. Set `IO_DIR` to a dedicated directory on the filesystem to measure. Use a new `RUN_ID` per ReFrame session; existing raw results are never overwritten.

```bash
source "$TRIAL_ROOT/env.sh"
export REFRAME="$TRIAL_ROOT/tools/reframe-venv/bin/reframe"
export CPUSET=0
export IO_DIR=/absolute/path/to/test-filesystem/hdf5-hardening-trial
mkdir -p "$IO_DIR"
export WORKLOADS=fft-small,hdf5-contiguous,lapack-small
export COMPARATORS=reference PAIRS=10
export RUN_ID
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$TRIAL_ROOT/results/reframe/$RUN_ID"
"$REFRAME" -C "$TRIAL_ROOT/reframe/settings.py" \
  -c "$TRIAL_ROOT/reframe/hardening.py" -l
"$REFRAME" -C "$TRIAL_ROOT/reframe/settings.py" \
  -c "$TRIAL_ROOT/reframe/hardening.py" -r --exec-policy=serial \
  --performance-report \
  --prefix="$TRIAL_ROOT/results/reframe/$RUN_ID/rfm" \
  --report-file="$TRIAL_ROOT/results/reframe/$RUN_ID/report.json" \
  2>&1 | tee "$TRIAL_ROOT/results/reframe/$RUN_ID/console.log"
```

The terminal shows each workload's PASS/FAIL and five metrics: full seconds, comparator seconds, full runtime increase %, and the interval endpoints. The actual values come from the run; this runbook contains no claimed benchmark results. ReFrame's JSON report retains its version/data-version and per-test performance values. The `paired/` subtree contains the CSV and summary JSON used to produce those numbers. See [ReFrame CLI/reporting](https://reframe-hpc.readthedocs.io/en/stable/manpage.html).

## 5. Drive parallel tests and the removal matrix

First build/qualify [Open MPI + UCX](00b-openmpi-ucx.md) and install the [parallel FFTW/HDF5 variants and fixed callers](05-parallel.md). Then, in the same two-node allocation:

```bash
source "$TRIAL_ROOT/mpi-env.sh"
export MPI_NP=2 MPI_MAP=ppr:1:node
export WORKLOADS=fft-mpi,hdf5-collective,hdf5-independent
export COMPARATORS=reference
export RUN_ID
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$TRIAL_ROOT/results/reframe/$RUN_ID"
"$REFRAME" -C "$TRIAL_ROOT/reframe/settings.py" \
  -c "$TRIAL_ROOT/reframe/hardening.py" -r --exec-policy=serial \
  --performance-report --prefix="$TRIAL_ROOT/results/reframe/$RUN_ID/rfm" \
  --report-file="$TRIAL_ROOT/results/reframe/$RUN_ID/report.json" \
  2>&1 | tee "$TRIAL_ROOT/results/reframe/$RUN_ID/console.log"
```

`IO_DIR` must be shared between those nodes. Rank binding is handled by Open MPI. Timed UCX logging stays off. To examine removals, install the selected variants first and change `COMPARATORS`, then run a new session with identical workloads and placement. A missing variant is a failed prerequisite, not a zero measurement.

This starter uses allocation-local execution deliberately. A later site configuration can use ReFrame's Slurm scheduler and MPI launcher directly, but paired arms must still share a controlled allocation/placement. Do not submit independent full/reference jobs to unrelated node types and treat their difference as compiler overhead.
