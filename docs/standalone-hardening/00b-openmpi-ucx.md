# 00b — Open MPI 4.1.8 with UCX 1.16.0 and GCC 12.5.0

Run after [00 — GCC bootstrap](00-gcc-bootstrap.md) and [01 — profile qualification](01-common.md), before the MPI FFTW/HDF5 builds. These versions match `cse-pilot/site-values.example.yaml`. Build this dependency stack once and keep it unchanged across all package variants. This isolates FFTW/HDF5 hardening; measuring MPI/UCX hardening itself would require a separate matrix.

## 1. Stage exact MPI sources

Use Open MPI's official release archive, not GitHub's automatically generated source snapshot. Stage/transfer these like the other sources when the test system is offline.

```bash
source "$TRIAL_ROOT/env.sh"
source "$TRIAL_ROOT/profiles.sh"
cd "$TRIAL_ROOT/downloads"
curl -fL --retry 3 -o openmpi-4.1.8.tar.bz2 \
  https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.8.tar.bz2
curl -fL --retry 3 -o ucx-1.16.0.tar.gz \
  https://github.com/openucx/ucx/releases/download/v1.16.0/ucx-1.16.0.tar.gz
cat > MPI-SHA256SUMS <<'SUMS'
466f68e3132a1dc02710cc2011fafced8336d98359fa2dae4dddcfd5719f12a9  openmpi-4.1.8.tar.bz2
f73770d3b583c91aba5fb07557e655ead0786e057018bfe42f0ebe8716e9d28c  ucx-1.16.0.tar.gz
SUMS
sha256sum --check MPI-SHA256SUMS | tee "$TRIAL_ROOT/logs/mpi-sources.log"
tar -xf ucx-1.16.0.tar.gz -C "$TRIAL_ROOT/src"
tar -xf openmpi-4.1.8.tar.bz2 -C "$TRIAL_ROOT/src"
export UCX_PREFIX="$TRIAL_ROOT/install/ucx-1.16.0-fixed"
export MPI_PREFIX="$TRIAL_ROOT/install/openmpi-4.1.8-ucx-fixed"
```

Source references: [Open MPI 4.1 downloads](https://www.open-mpi.org/software/ompi/v4.1/), [UCX build and Open MPI integration](https://openucx.readthedocs.io/en/master/running.html).

## 2. Select the UCX transport prerequisites

UCX can run over TCP/shared memory without RDMA development libraries. For an InfiniBand/RoCE trial, the site must supply compatible verbs/rdmacm headers and libraries, kernel drivers, and access to the relevant devices. Building UCX alone does not install network drivers. Record `ucx_info -d` on the compute nodes; do not describe a TCP fallback as RDMA performance.

Choose exactly one array below. The default is a portable TCP/shared-memory bring-up. If the trial is intended to exercise RDMA, select the RDMA array before building and fail if its prerequisites cannot be found.

```bash
UCX_TRANSPORT_ARGS=(--without-verbs --without-rdmacm)
# For an IB/RoCE system with development libraries installed, use instead:
# UCX_TRANSPORT_ARGS=(--with-verbs --with-rdmacm)
# For libraries in a nonstandard site prefix, use --with-verbs=/prefix and
# --with-rdmacm=/prefix, and preserve their runtime paths on every node.
```

Leave UCX's runtime transport selection at its normal defaults initially. Record any later `UCX_TLS`/`UCX_NET_DEVICES` choices and apply them identically to both arms. A non-IB fabric requires its own supported UCX configuration; verify available transports rather than guessing from the machine's vendor name.

## 3. Build UCX once

Use the full qualified hardening profile, fixed for every package arm. UCX's release configuration disables diagnostic instrumentation unrelated to this production experiment. If that fixed profile causes an MPI/UCX compatibility failure, resolve and record the chosen dependency profile before building any payloads.

```bash
profile_flags full
build="$TRIAL_ROOT/build/ucx-fixed"
test ! -e "$build" && test ! -e "$UCX_PREFIX"
mkdir -p "$build" "$TRIAL_ROOT/logs/ucx-fixed"
(
  cd "$build"
  CC="$CC" CXX="$CXX" CFLAGS="$CFLAGS" CXXFLAGS="$CXXFLAGS" \
    CPPFLAGS='' LDFLAGS="$SHARED_LDFLAGS" \
    "$TRIAL_ROOT/src/ucx-1.16.0/contrib/configure-release" \
    --prefix="$UCX_PREFIX" --libdir="$UCX_PREFIX/lib" \
    --enable-shared --disable-static --enable-mt \
    --without-cuda --without-rocm --without-java --without-knem --without-xpmem \
    "${UCX_TRANSPORT_ARGS[@]}" \
    2>&1 | tee "$TRIAL_ROOT/logs/ucx-fixed/configure.log"
  make -j "$JOBS" V=1 2>&1 | tee "$TRIAL_ROOT/logs/ucx-fixed/build.log"
  make check 2>&1 | tee "$TRIAL_ROOT/logs/ucx-fixed/check.log"
  make install 2>&1 | tee "$TRIAL_ROOT/logs/ucx-fixed/install.log"
  cp config.log "$TRIAL_ROOT/logs/ucx-fixed/config.log"
)
export LD_LIBRARY_PATH="$UCX_PREFIX/lib:$GCC_LIB_DIRS"
"$UCX_PREFIX/bin/ucx_info" -v > "$TRIAL_ROOT/logs/ucx-fixed/version.txt"
"$UCX_PREFIX/bin/ucx_info" -d > "$TRIAL_ROOT/logs/ucx-fixed/devices.txt"
```

Review configure warnings for unrecognized options and confirm threading support and the selected network transports in the built configuration. Testing requirements may vary by installed optional transport; retain failures and resolve them rather than ignoring the test result.

## 4. Build Open MPI once against UCX

The example assumes Slurm, as in the existing trial examples. For another scheduler, replace `--with-slurm` with its supported configuration before building. Open MPI supplies bundled hwloc, libevent, and PMIx, so their development packages are not assumed present. ROMIO is enabled and selected consistently for the HDF5 MPI-IO phase.

```bash
profile_flags full
build="$TRIAL_ROOT/build/openmpi-fixed"
test ! -e "$build" && test ! -e "$MPI_PREFIX"
mkdir -p "$build" "$TRIAL_ROOT/logs/openmpi-fixed"
(
  cd "$build"
  CC="$CC" CXX="$CXX" FC="$FC" CFLAGS="$CFLAGS" CXXFLAGS="$CXXFLAGS" \
    FCFLAGS="$FFLAGS" FFLAGS="$FFLAGS" CPPFLAGS='' \
    LDFLAGS="$SHARED_LDFLAGS -Wl,-rpath,$UCX_PREFIX/lib" \
    "$TRIAL_ROOT/src/openmpi-4.1.8/configure" \
    --prefix="$MPI_PREFIX" --libdir="$MPI_PREFIX/lib" \
    --with-ucx="$UCX_PREFIX" --with-hwloc=internal --with-libevent=internal \
    --with-pmix=internal --with-slurm --enable-io-romio \
    --enable-mpi-fortran=all --disable-mpi-cxx --disable-oshmem \
    --enable-shared --disable-static --without-cuda \
    --enable-mca-no-build=btl-uct \
    2>&1 | tee "$TRIAL_ROOT/logs/openmpi-fixed/configure.log"
  make -j "$JOBS" V=1 2>&1 | tee "$TRIAL_ROOT/logs/openmpi-fixed/build.log"
  make check 2>&1 | tee "$TRIAL_ROOT/logs/openmpi-fixed/check.log"
  make install 2>&1 | tee "$TRIAL_ROOT/logs/openmpi-fixed/install.log"
  cp config.log "$TRIAL_ROOT/logs/openmpi-fixed/config.log"
)
export MPI_LIB_DIRS="$MPI_PREFIX/lib:$UCX_PREFIX/lib"
{
  for name in MPI_PREFIX UCX_PREFIX MPI_LIB_DIRS; do
    printf 'export %s=%q\n' "$name" "${!name}"
  done
  cat <<'ENV'
export PATH="$MPI_PREFIX/bin:$UCX_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$MPI_LIB_DIRS:$GCC_LIB_DIRS"
export OMPI_MCA_pml=ucx
export OMPI_MCA_btl='^uct'
export OMPI_MCA_io=romio321
ENV
} > "$TRIAL_ROOT/mpi-env.sh"
source "$TRIAL_ROOT/mpi-env.sh"
"$MPI_PREFIX/bin/ompi_info" --all > "$TRIAL_ROOT/logs/openmpi-fixed/info.txt"
"$MPI_PREFIX/bin/ompi_info" --param pml ucx
"$MPI_PREFIX/bin/ompi_info" --param io all
"$MPI_PREFIX/bin/mpicc" --showme:command
"$MPI_PREFIX/bin/mpicc" --showme:compile
"$MPI_PREFIX/bin/mpicc" --showme:link
"$MPI_PREFIX/bin/mpifort" --showme:command
```

The wrapper commands must name the private GCC 12.5.0 drivers. Wrapper compile flags must not force an experiment control into every consuming package: hardening Open MPI itself should not silently inject its hardening flags into callers. Inspect the wrapper-data files and `--showme:*` output. If flags are injected, correct the wrapper configuration and requalify before the package matrix. Verify the `ucx` PML and `romio321` I/O components are present; `ompi_info` success alone is not a data-transfer test.

## 5. Verify two-node execution before benchmarking

Use a two-node scheduler allocation; for Slurm, obtain it with the site's account/partition options, for example `salloc -N 2 -n 2 -t 00:30:00`. Use `mpirun` within that allocation. Do not bypass the scheduler with an unapproved host list. The prefix/source/result paths must exist at the same absolute paths on both nodes.

```bash
cat > "$TRIAL_ROOT/bench/mpi-smoke.c" <<'C'
#include <mpi.h>
#include <stdio.h>
int main(int argc,char **argv) {
    int rank,size,sum,provided;
    MPI_Init_thread(&argc,&argv,MPI_THREAD_FUNNELED,&provided);
    MPI_Comm_rank(MPI_COMM_WORLD,&rank); MPI_Comm_size(MPI_COMM_WORLD,&size);
    MPI_Allreduce(&rank,&sum,1,MPI_INT,MPI_SUM,MPI_COMM_WORLD);
    if(provided<MPI_THREAD_FUNNELED || sum!=size*(size-1)/2) MPI_Abort(MPI_COMM_WORLD,1);
    char host[MPI_MAX_PROCESSOR_NAME]; int len;
    MPI_Get_processor_name(host,&len);
    printf("rank=%d size=%d host=%s sum=%d\n",rank,size,host,sum);
    MPI_Finalize(); return 0;
}
C
"$MPI_PREFIX/bin/mpicc" "$TRIAL_ROOT/bench/mpi-smoke.c" \
  -o "$TRIAL_ROOT/bench/mpi-smoke"
"$MPI_PREFIX/bin/mpirun" -np 2 --map-by ppr:1:node --bind-to core \
  --report-bindings --mca pml ucx --mca btl '^uct' \
  -x PATH -x LD_LIBRARY_PATH -x UCX_LOG_LEVEL=info \
  "$TRIAL_ROOT/bench/mpi-smoke" \
  2>&1 | tee "$TRIAL_ROOT/logs/openmpi-fixed/two-node-smoke.log"
```

Confirm distinct hostnames, the correct sum, and the selected UCX transport. UCX's informational logging is for qualification; remove it from timed runs. On each rank/node record `ucx_info -d`, `ldd` for the benchmark and the installed UCX PML component, and `ulimit -l`. Verify no system MPI/UCX is substituted. Keep runtime environment, transport/device selection, rank count, binding, and the MPI/UCX libraries fixed in all package comparisons. Do not add oversubscription to conceal an allocation mismatch.

Continue with [05 — Parallel FFTW and HDF5](05-parallel.md).
