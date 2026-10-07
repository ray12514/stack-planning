# 01 — Common GCC 12.5.0 profiles and measurements

Prerequisite: [00 — GCC bootstrap](00-gcc-bootstrap.md). Execute these setup blocks once in Bash after sourcing `env.sh`. All package runbooks source the resulting `profiles.sh`.

## 1. Create explicit profiles

GCC 12.5.0 does not have `-fhardened`. Spell out the controls. The full profile deliberately starts with `-fstack-protector-all`; `stack-strong` tests the narrower alternative. FORTIFY and local automatic initialization apply to C/C++, not to LAPACK's Fortran array operations. `_GLIBCXX_ASSERTIONS` applies only to C++ code using libstdc++; it is recorded here but the initial C-only payloads do not exercise it.

| Profile | Change relative to full |
|---|---|
| `full` | All applicable controls in this runbook |
| `reference` | All variable controls disabled; optimization, PIC, warnings, and non-executable stack retained |
| `stack-strong` | Replace stack protection for every function with strong stack protection |
| `minus-stack` | Disable stack protector |
| `minus-fortify` | Disable C/C++ FORTIFY |
| `minus-clash` | Disable stack-clash protection |
| `minus-init` | Disable C/C++ automatic local initialization |
| `minus-cf` | Disable x86 compiler control-flow protection |
| `minus-relro` | Disable RELRO, retain eager binding |
| `minus-now` | Disable eager binding, retain RELRO |
| `minus-pie` | Consumer executable only: disable PIE, retain the full library and other controls |

PIC remains on for shared libraries. A non-executable stack remains on throughout; there is no executable-stack timing arm. `-fcf-protection=full` is compiler-generated x86 CET support, not proof that hardware shadow-stack enforcement is active. Record processor, kernel, loader, and ELF properties; do not label its delta as isolated hardware SHSTK overhead.

```bash
source "$TRIAL_ROOT/env.sh"
cat > "$TRIAL_ROOT/profiles.sh" <<'SH'
profile_flags() {
    local p=${1:?profile required}
    local stack=-fstack-protector-all clash=-fstack-clash-protection
    local cf="-fcf-protection=$CF_MODE" init=-ftrivial-auto-var-init=zero
    local fortify="-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=$FORTIFY_LEVEL"
    local assertions=-D_GLIBCXX_ASSERTIONS
    local relro=-Wl,-z,relro now=-Wl,-z,now pie=-fPIE pielink=-pie
    case "$p" in
      full) ;;
      reference)
        stack=-fno-stack-protector; clash=-fno-stack-clash-protection
        cf=-fcf-protection=none; init=-ftrivial-auto-var-init=uninitialized
        fortify=-U_FORTIFY_SOURCE; assertions=-U_GLIBCXX_ASSERTIONS
        relro=-Wl,-z,norelro; now=-Wl,-z,lazy; pie=-fno-pie; pielink=-no-pie ;;
      stack-strong) stack=-fstack-protector-strong ;;
      minus-stack) stack=-fno-stack-protector ;;
      minus-fortify) fortify=-U_FORTIFY_SOURCE ;;
      minus-clash) clash=-fno-stack-clash-protection ;;
      minus-init) init=-ftrivial-auto-var-init=uninitialized ;;
      minus-cf) cf=-fcf-protection=none ;;
      minus-relro) relro=-Wl,-z,norelro ;;
      minus-now) now=-Wl,-z,lazy ;;
      minus-pie) pie=-fno-pie; pielink=-no-pie ;;
      *) printf 'Unknown profile: %s\n' "$p" >&2; return 1 ;;
    esac
    BASE_OPT="-O3 -g -march=$CPU_TARGET -mtune=generic -fno-lto"
    C_CONTROL="$stack $clash $cf $init $fortify -Wformat -Werror=format-security"
    F_CONTROL="$stack $clash $cf"
    CFLAGS="$BASE_OPT $C_CONTROL -fPIC"
    CXXFLAGS="$CFLAGS $assertions"
    FFLAGS="$BASE_OPT $F_CONTROL -fPIC"
    FCFLAGS="$FFLAGS"
    CPPFLAGS=''
    SHARED_LDFLAGS="$relro $now -Wl,-z,noexecstack"
    EXE_CFLAGS="$BASE_OPT $C_CONTROL $pie"
    EXE_FFLAGS="$BASE_OPT $F_CONTROL $pie"
    EXE_LDFLAGS="$SHARED_LDFLAGS $pielink"
    export CFLAGS CXXFLAGS FFLAGS FCFLAGS CPPFLAGS
}
LIB_PROFILES=(full reference stack-strong minus-stack minus-fortify minus-clash
              minus-init minus-cf minus-relro minus-now)
LAPACK_PROFILES=(full reference stack-strong minus-stack minus-clash minus-cf
                 minus-relro minus-now)
SH
source "$TRIAL_ROOT/profiles.sh"
```

Use the explicit flags in the [GCC 12.5 instrumentation manual](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Instrumentation-Options.html), [automatic initialization documentation](https://gcc.gnu.org/onlinedocs/gcc-12.5.0/gcc/Optimize-Options.html), and [glibc FORTIFY documentation](https://sourceware.org/glibc/manual/latest/html_node/Source-Fortification.html). The full set is a candidate for this experiment, not a claim that every option is mandatory under your organizational profile.

## 2. Qualify flags before expensive builds

Run on the execution CPU, not only the login node. This checks compiler acceptance, FORTIFY implementation level, and smoke execution. It does not establish that every package function receives a check.

```bash
mkdir -p "$TRIAL_ROOT/bench/probes" "$TRIAL_ROOT/logs/profiles"
cat > "$TRIAL_ROOT/bench/probes/probe.c" <<'C'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#if defined(_FORTIFY_SOURCE) && __USE_FORTIFY_LEVEL != _FORTIFY_SOURCE
#error Requested FORTIFY level is not implemented by these headers/compiler
#endif
int main(int argc, char **argv) {
    char b[64];
    snprintf(b, sizeof b, "%s", argc > 1 ? argv[1] : "probe");
    puts(b);
    return 0;
}
C
cp "$TRIAL_ROOT/bench/probes/probe.c" "$TRIAL_ROOT/bench/probes/probe.cc"
for p in "${LIB_PROFILES[@]}" minus-pie; do
    profile_flags "$p"
    read -r -a cargs <<< "$EXE_CFLAGS"
    read -r -a largs <<< "$EXE_LDFLAGS"
    read -r -a fargs <<< "$EXE_FFLAGS"
    {
      declare -p CFLAGS CXXFLAGS FFLAGS SHARED_LDFLAGS EXE_CFLAGS EXE_FFLAGS EXE_LDFLAGS
      "$CC" -Werror "${cargs[@]}" "$TRIAL_ROOT/bench/probes/probe.c" \
        "${largs[@]}" -o "$TRIAL_ROOT/bench/probes/c-$p"
      "$CXX" -Werror "${cargs[@]}" "$TRIAL_ROOT/bench/probes/probe.cc" \
        "${largs[@]}" -o "$TRIAL_ROOT/bench/probes/cxx-$p"
      "$FC" -Werror "${fargs[@]}" "$TRIAL_ROOT/bench/gcc-fortran-smoke.f90" \
        "${largs[@]}" -o "$TRIAL_ROOT/bench/probes/f-$p"
      "$TRIAL_ROOT/bench/probes/c-$p"
      "$TRIAL_ROOT/bench/probes/cxx-$p"
      "$TRIAL_ROOT/bench/probes/f-$p"
      readelf -hW "$TRIAL_ROOT/bench/probes/c-$p"
      readelf -lW "$TRIAL_ROOT/bench/probes/c-$p"
      readelf -dW "$TRIAL_ROOT/bench/probes/c-$p"
      readelf -nW "$TRIAL_ROOT/bench/probes/c-$p"
    } > "$TRIAL_ROOT/logs/profiles/$p.log" 2>&1
done
```

If FORTIFY 3 is rejected or downgraded, set `FORTIFY_LEVEL=2` in `env.sh`, re-source it, and rerun qualification. Name results with the selected level. GCC's acceptance of a macro alone is insufficient. If another control is unsupported, stop and define a reduced profile explicitly before starting the matrix; do not silently change only one package. For x86 control-flow protection, `CF_MODE=none` means the full profile omits that protection and `minus-cf` has no meaningful contrast.

Expected artifact distinctions: full probe executable is ELF `DYN`/PIE; reference and minus-PIE are `EXEC`. Full has a `GNU_RELRO` segment and a `BIND_NOW`/`NOW` dynamic flag; minus-RELRO lacks the former, minus-NOW lacks the latter. `GNU_STACK` should not have execute permission in any arm. GNU properties and `endbr64` disassembly help inspect CET code generation, but object property merging and runtime enablement also matter. Stack-protector and `_chk` symbols may occur only when the package actually needs them; their absence alone is not proof the flags were lost.

## 3. Inspect each installed variant

Run this with the actual shared library path from its package runbook. Keep its output alongside compile commands and CMake cache/configure output.

```bash
LIBRARY=/absolute/path/to/installed/lib/library.so
test -f "$LIBRARY"
readelf -lW "$LIBRARY"
readelf -dW "$LIBRARY"
readelf -nW "$LIBRARY"
nm -D "$LIBRARY" | awk '/__stack_chk_fail|_chk/ {print}'
objdump -d "$LIBRARY" | awk '/endbr64/ {n++} END {print "endbr64 instructions:", n+0}'
```

Do not use shell success as the only flag audit: look at actual compile/link commands and ELF properties. If a build system overrides flags, correct it before benchmarking.

## 4. Create the paired timing harness

The package runbooks create one fixed driver each. Drivers print CSV rows `phase,seconds,error` and fail on a correctness error. The harness switches the library path, warms each variant once, alternates the order within each independent pair, retains raw results, and computes a bootstrap interval for the geometric mean of paired runtime ratios. It uses Python's standard library only. Ten pairs are a pilot; increase `PAIRS` when variability leaves the chosen regression threshold unresolved.

```bash
cat > "$TRIAL_ROOT/bench/paired.py" <<'PY'
import csv, json, math, os, pathlib, random, shlex, statistics, subprocess, sys
package, executable, case, *args = sys.argv[1:]
root = pathlib.Path(os.environ['TRIAL_ROOT'])
comparator = os.environ.get('COMPARE', 'reference')
pairs = int(os.environ.get('PAIRS', '10'))
if pairs < 2:
    raise SystemExit('PAIRS must be at least 2')
profiles = ('full', comparator)
if comparator == 'full':
    raise SystemExit('COMPARE must differ from full')
envs = {}
mpi_np = int(os.environ.get('MPI_NP', '0'))
launcher = []
if mpi_np:
    launcher = [str(pathlib.Path(os.environ['MPI_PREFIX']) / 'bin/mpirun'),
                '-np', str(mpi_np), '--map-by', os.environ.get('MPI_MAP', 'ppr:1:node'),
                '--bind-to', 'core', '--mca', 'pml', 'ucx', '--mca', 'btl', '^uct',
                '-x', 'PATH', '-x', 'LD_LIBRARY_PATH', '-x', 'OMPI_MCA_io']
    for name in ('UCX_TLS', 'UCX_NET_DEVICES'):
        if name in os.environ:
            launcher += ['-x', name]
    launcher += shlex.split(os.environ.get('MPI_EXTRA_ARGS', ''))
for profile in profiles:
    prefix = root / 'install' / package / profile / 'lib'
    if not prefix.is_dir():
        raise SystemExit(f'Missing installed variant: {prefix}')
    env = os.environ.copy()
    runtime = os.environ.get('MPI_LIB_DIRS', '')
    env['LD_LIBRARY_PATH'] = ':'.join(x for x in
        (str(prefix), runtime, os.environ['GCC_LIB_DIRS']) if x)
    envs[profile] = env
result_root = pathlib.Path(os.environ.get('RESULT_ROOT', str(root / 'results')))
outdir = result_root / package / case / comparator
outdir.mkdir(parents=True, exist_ok=True)
raw = outdir / 'raw.csv'
if raw.exists():
    raise SystemExit(f'Results already exist: {raw}; select a new case label')
for profile in profiles:
    proc = subprocess.run(['ldd', executable], env=envs[profile], text=True,
                          capture_output=True, check=True)
    (outdir / f'loaded-{profile}.txt').write_text(proc.stdout + proc.stderr)
    if 'not found' in proc.stdout:
        raise SystemExit(f'Missing runtime dependency for {profile}')
    if str(root / 'install' / package / profile) not in proc.stdout:
        raise SystemExit(f'ldd did not select the requested {package}/{profile} library')
def run(profile):
    proc = subprocess.run([*launcher, executable, *args], env=envs[profile], text=True,
                          capture_output=True)
    with (outdir / 'driver.log').open('a') as f:
        f.write(f'profile={profile} args={args!r}\n{proc.stdout}{proc.stderr}\n')
    proc.check_returncode()
    rows = []
    for phase, seconds, error in csv.reader(proc.stdout.splitlines()):
        seconds, error = float(seconds), float(error)
        if not math.isfinite(seconds) or seconds <= 0 or not math.isfinite(error):
            raise RuntimeError('Invalid measurement')
        rows.append((phase, seconds, error))
    if not rows or len({r[0] for r in rows}) != len(rows):
        raise RuntimeError('Missing or duplicate measurement phase')
    return rows
for profile in profiles:
    run(profile)
data = {}
with raw.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['pair', 'order', 'package', 'case', 'profile', 'phase', 'seconds', 'error'])
    for pair in range(pairs):
        order = profiles if pair % 2 == 0 else profiles[::-1]
        data[pair] = {}
        for position, profile in enumerate(order):
            rows = run(profile)
            data[pair][profile] = {phase: seconds for phase, seconds, _ in rows}
            for phase, seconds, error in rows:
                writer.writerow([pair, position, package, case, profile, phase, seconds, error])
            f.flush()
phases = set(data[0]['full'])
if any(set(values[p]) != phases for values in data.values() for p in profiles):
    raise RuntimeError('Phases differ across runs')
rng = random.Random(20261006)
summary = {}
for phase in sorted(phases):
    logs = [math.log(v['full'][phase] / v[comparator][phase]) for v in data.values()]
    ratio = math.exp(statistics.mean(logs))
    samples = sorted(math.exp(statistics.mean(rng.choices(logs, k=pairs)))
                     for _ in range(10000))
    summary[phase] = {'pairs': pairs, 'runtime_ratio_full_over_comparator': ratio,
                      'full_runtime_seconds_geomean': math.exp(statistics.mean(
                          math.log(v['full'][phase]) for v in data.values())),
                      'comparator_runtime_seconds_geomean': math.exp(statistics.mean(
                          math.log(v[comparator][phase]) for v in data.values())),
                      'full_runtime_increase_percent': 100*(ratio-1),
                      'bootstrap_95_percent_interval': [100*(samples[250]-1),
                                                        100*(samples[9749]-1)]}
record = {'package': package, 'case': case, 'comparator': comparator,
          'driver': executable, 'args': args, 'launcher': launcher, 'phases': summary}
(outdir / 'summary.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
PY
```

The interval is a pilot statistical summary, not a guarantee against scheduler/filesystem drift. Inspect pair order, outliers, and raw results. Choose more repetitions or better controlled workloads when needed; do not declare zero cost merely because an interval includes zero.

## 5. Run inside one compute allocation

Set a CPU list actually assigned to the job. `taskset` constrains execution; it does not allocate CPUs. Keep jobs sequential and avoid build jobs while timing. For the serial pilot select one allocated CPU; for threaded FFTW use a recorded set large enough for its thread count.

```bash
export CPUSET=0   # replace with a CPU assigned to this allocation
export PAIRS=10
export COMPARE=reference
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export BLIS_NUM_THREADS=1
lscpu > "$TRIAL_ROOT/logs/execution-cpu.txt"
taskset -pc $$ >> "$TRIAL_ROOT/logs/execution-cpu.txt"
```

Run each package's timing commands first for `COMPARE=reference`. Then select an installed removal variant and a new case label or comparator directory. A positive `full_runtime_increase_percent` means full was slower than that comparator; a negative value means it was faster. All numbers are elapsed runtime changes, not throughput-loss percentages.

For an executable/consumer comparison, compile the same driver source once per profile with `EXE_CFLAGS` or `EXE_FFLAGS` and `EXE_LDFLAGS`, linking the same full library for the PIE-only experiment. Measure whole-process elapsed time separately from driver kernel phases. PIE removal does not change a shared library's PIC requirement. Do not feed those differently built executables to the fixed-driver comparison and call the result a library-only cost.
