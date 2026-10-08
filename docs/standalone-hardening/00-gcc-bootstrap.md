# 00 — Bootstrap GCC 12.5.0 and stage sources

Prerequisite: [build environment and system dependencies](00-build-environment.md). Keep the required site master modules and create its explicit `site-env.sh` baseline before this bootstrap.

## 1. Establish a bootstrap route

GCC 12.5.0 is assumed absent. Building it from source still needs a working native C/C++ compiler supporting C++11, libc development headers/startup objects, and an assembler/linker. An existing Fortran compiler is not required for the normal three-stage bootstrap. See [GCC prerequisites](https://gcc.gnu.org/install/prerequisites.html) and [out-of-tree configuration](https://gcc.gnu.org/install/configure.html).

| Available on the test system | Route |
|---|---|
| Older working GCC/G++ or suitable Clang/Clang++ | Load its site module and set the two absolute seed paths below. It builds GCC, not the three payload packages. |
| No compiler, but administrators can provision OS development packages | Have the site provision its supported C/C++ compiler, libc headers, make, and binutils. On RHEL/Rocky-like systems the usual package names include `gcc gcc-c++ glibc-devel make binutils`; on Debian-like systems, `build-essential`. This is a prerequisite for the operator, not a command this runbook runs automatically. |
| No compiler and no package provisioning | Build GCC 12.5.0 and binutils on a compatible Linux builder, install at the exact intended absolute prefixes, and transfer those trees through the site's normal transfer route. Use the same architecture, compatible CPU baseline, and the same or older glibc than the execution system. Preserve the prefix path and run all qualification steps here after transfer. Alternatively transfer a compatible seed compiler and perform the bootstrap locally. |

A macOS compiler, a bare source archive, or a compiler binary requiring newer glibc cannot fill the no-compiler route. Headers and linker startup files are still needed to compile payloads even with a transferred compiler.

## 2. Start a Bash shell on the build allocation

Run in a site-approved build allocation. Set jobs to fit its CPU and memory limits; four is a conservative starting point, not a scheduler request. Reserve substantial scratch space for GCC's three-stage build. Inspect `df -h` before building. Use the same filesystem paths on login/build/execution nodes.

```bash
bash
set -euo pipefail
export TRIAL_ROOT=/absolute/path/to/hardening-trial
export JOBS=4
: "${SEED_CC:?Set the absolute seed C path in the environment procedure}"
: "${SEED_CXX:?Set the absolute seed C++ path in the environment procedure}"
case "$TRIAL_ROOT" in /*) ;; *) exit 1 ;; esac
case "$TRIAL_ROOT" in *[[:space:]]*) exit 1 ;; esac
mkdir -p "$TRIAL_ROOT"/{downloads,src,build,toolchains,tools,install,logs,bench,results}
export GCC_PREFIX="$TRIAL_ROOT/toolchains/gcc-12.5.0"
export BINUTILS_PREFIX="$TRIAL_ROOT/toolchains/binutils-2.44"
source "$TRIAL_ROOT/site-env.sh"
# The seed is needed only for the bootstrap, not for the payload builds.
export PATH="$(dirname "$SEED_CC"):$(dirname "$SEED_CXX"):$TRIAL_BASE_PATH"
export LD_LIBRARY_PATH="$TRIAL_SITE_LIB_DIRS"
if test -n "${TRIAL_SEED_LIB_DIRS:-}"; then
    export LD_LIBRARY_PATH="$TRIAL_SEED_LIB_DIRS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if test -z "$LD_LIBRARY_PATH"; then unset LD_LIBRARY_PATH; fi
hash -r
for tool in make tar xz bzip2 bash awk sed diff sha256sum; do
    command -v "$tool"
done
uname -a > "$TRIAL_ROOT/logs/host.txt"
cat /etc/os-release >> "$TRIAL_ROOT/logs/host.txt"
getconf GNU_LIBC_VERSION >> "$TRIAL_ROOT/logs/host.txt"
df -h "$TRIAL_ROOT" >> "$TRIAL_ROOT/logs/host.txt"
cat > "$TRIAL_ROOT/bench/seed.cc" <<'CPP'
#include <vector>
int main() { auto v = std::vector<int>{1,2,3}; return v[1] != 2; }
CPP
if test -x "$SEED_CC" && test -x "$SEED_CXX"; then
    "$SEED_CC" --version
    "$SEED_CXX" --version
    "$SEED_CXX" -std=c++11 "$TRIAL_ROOT/bench/seed.cc" -o "$TRIAL_ROOT/bench/seed"
    "$TRIAL_ROOT/bench/seed"
else
    printf '%s\n' 'No usable seed: use the compatible transferred-toolchain route.'
fi
```

Record loaded modules (`module list` when available). Avoid inheriting a Cray compiler-family marker for the direct GNU build: start a fresh shell/module environment appropriate to the site and inspect `PE_ENV`/`CRAYPE_*`; the payload commands explicitly use the installed GNU drivers.

## 3. Stage source archives

On a connected staging machine, download these exact archives. On an offline test machine, transfer this directory instead and begin at the checksum command. No package build invokes Spack. The expected SHA256 values below come from the existing trial recipe inventory; using those recorded source identities does not use the Spack build machinery.

```bash
cd "$TRIAL_ROOT/downloads"
curl -fL --retry 3 -o gcc-12.5.0.tar.xz \
  https://ftp.gnu.org/gnu/gcc/gcc-12.5.0/gcc-12.5.0.tar.xz
curl -fL --retry 3 -o binutils-2.44.tar.bz2 \
  https://ftp.gnu.org/gnu/binutils/binutils-2.44.tar.bz2
curl -fL --retry 3 -o cmake-3.31.12.tar.gz \
  https://github.com/Kitware/CMake/releases/download/v3.31.12/cmake-3.31.12.tar.gz
curl -fL --retry 3 -o fftw-3.3.11.tar.gz \
  https://www.fftw.org/fftw-3.3.11.tar.gz
curl -fL --retry 3 -o hdf5-2.1.0.tar.gz \
  https://github.com/HDFGroup/hdf5/releases/download/2.1.0/hdf5-2.1.0.tar.gz
curl -fL --retry 3 -o lapack-3.12.1.tar.gz \
  https://github.com/Reference-LAPACK/lapack/archive/refs/tags/v3.12.1.tar.gz
cat > SHA256SUMS <<'SUMS'
71cd373d0f04615e66c5b5b14d49c1a4c1a08efa7b30625cd240b11bab4062b3  gcc-12.5.0.tar.xz
f66390a661faa117d00fab2e79cf2dc9d097b42cc296bf3f8677d1e7b452dc3a  binutils-2.44.tar.bz2
5f3fd5a54dfa65602bdbed64f981a72673cc19f2d304cc2955cf0dfa0cfd8272  cmake-3.31.12.tar.gz
5630c24cdeb33b131612f7eb4b1a9934234754f9f388ff8617458d0be6f239a1  fftw-3.3.11.tar.gz
ce7f5515a95d588b8606c3fb50643f8b88ac52ffbbde9c63bb1edca6a256e964  hdf5-2.1.0.tar.gz
2ca6407a001a474d4d4d35f3a61550156050c48016d949f0da0529c0aa052422  lapack-3.12.1.tar.gz
SUMS
sha256sum --check SHA256SUMS | tee "$TRIAL_ROOT/logs/sources.log"
for archive in gcc-12.5.0.tar.xz binutils-2.44.tar.bz2 cmake-3.31.12.tar.gz \
               fftw-3.3.11.tar.gz hdf5-2.1.0.tar.gz lapack-3.12.1.tar.gz; do
    tar -xf "$archive" -C "$TRIAL_ROOT/src"
done
```

Stage GCC's additional prerequisite archives before an offline transfer. From its extracted source tree, its own script downloads GMP 6.2.1, MPFR 4.1.0, MPC 1.2.1, and ISL 0.24 and verifies the bundled SHA512 checksums. Transfer the populated GCC source tree, including the prerequisite directories and symlinks, or transfer the four archives into that tree and run the script without needing a download. See the [GCC 12.5.0 prerequisite script](https://github.com/gcc-mirror/gcc/blob/releases/gcc-12.5.0/contrib/download_prerequisites).

```bash
cd "$TRIAL_ROOT/src/gcc-12.5.0"
./contrib/download_prerequisites
test -d gmp && test -d mpfr && test -d mpc && test -d isl
```

Do not regenerate or loosen checksum expectations to get past a mismatch. A mismatch means the staged source is not the recorded input.

## 4. Build private binutils, then GCC

Skip these two builds only for the transferred-toolchain route, then continue with section 5. These prefixes must be new; do not overwrite an existing compiler.

```bash
test -x "$SEED_CC" && test -x "$SEED_CXX"
test ! -e "$BINUTILS_PREFIX"
test ! -e "$TRIAL_ROOT/build/binutils-2.44"
mkdir "$TRIAL_ROOT/build/binutils-2.44"
cd "$TRIAL_ROOT/build/binutils-2.44"
CC="$SEED_CC" CXX="$SEED_CXX" \
  "$TRIAL_ROOT/src/binutils-2.44/configure" \
  --prefix="$BINUTILS_PREFIX" --disable-nls --disable-werror \
  --disable-gdb --disable-gdbserver --disable-sim \
  2>&1 | tee "$TRIAL_ROOT/logs/binutils-configure.log"
make -j "$JOBS" 2>&1 | tee "$TRIAL_ROOT/logs/binutils-build.log"
make install 2>&1 | tee "$TRIAL_ROOT/logs/binutils-install.log"
export PATH="$BINUTILS_PREFIX/bin:$PATH"

test ! -e "$GCC_PREFIX"
test ! -e "$TRIAL_ROOT/build/gcc-12.5.0"
mkdir "$TRIAL_ROOT/build/gcc-12.5.0"
cd "$TRIAL_ROOT/build/gcc-12.5.0"
CONFIG_SHELL=/bin/bash CC="$SEED_CC" CXX="$SEED_CXX" \
  "$TRIAL_ROOT/src/gcc-12.5.0/configure" \
  --prefix="$GCC_PREFIX" --enable-languages=c,c++,fortran \
  --disable-multilib --disable-nls \
  --with-as="$BINUTILS_PREFIX/bin/as" --with-ld="$BINUTILS_PREFIX/bin/ld" \
  2>&1 | tee "$TRIAL_ROOT/logs/gcc-configure.log"
make -j "$JOBS" bootstrap 2>&1 | tee "$TRIAL_ROOT/logs/gcc-bootstrap.log"
make install 2>&1 | tee "$TRIAL_ROOT/logs/gcc-install.log"
```

`--disable-multilib` avoids requiring 32-bit libc headers for this 64-bit trial. Do not disable bootstrap to work around a stage comparison failure. Investigate the seed/environment and retain the failure log. If DejaGnu/Expect/Tcl are available, run `make -k check` and review unexpected failures; the smoke checks below are not a substitute for a complete compiler qualification.

## 5. Activate GCC and establish its runtime paths

```bash
source "$TRIAL_ROOT/site-env.sh"
export PATH="$GCC_PREFIX/bin:$BINUTILS_PREFIX/bin:$TRIAL_BASE_PATH"
export CC="$GCC_PREFIX/bin/gcc"
export CXX="$GCC_PREFIX/bin/g++"
export FC="$GCC_PREFIX/bin/gfortran"
test "$("$CC" -dumpfullversion)" = 12.5.0
test "$("$CXX" -dumpfullversion)" = 12.5.0
test "$("$FC" -dumpfullversion)" = 12.5.0
export GCC_LIB_DIRS
GCC_LIB_DIRS="$(dirname "$("$FC" -print-file-name=libgfortran.so)"):$(dirname "$("$CXX" -print-file-name=libstdc++.so)"):$(dirname "$("$CC" -print-file-name=libgcc_s.so.1)")"
export LD_LIBRARY_PATH="$GCC_LIB_DIRS${TRIAL_SITE_LIB_DIRS:+:$TRIAL_SITE_LIB_DIRS}"
hash -r
"$CC" -v 2> "$TRIAL_ROOT/logs/gcc-identity.txt"
"$CC" -print-prog-name=as >> "$TRIAL_ROOT/logs/gcc-identity.txt"
"$CC" -print-prog-name=ld >> "$TRIAL_ROOT/logs/gcc-identity.txt"
"$CC" -dumpspecs > "$TRIAL_ROOT/logs/gcc-specs.txt"
"$BINUTILS_PREFIX/bin/ld" --version >> "$TRIAL_ROOT/logs/gcc-identity.txt"
"$CXX" -std=c++11 "$TRIAL_ROOT/bench/seed.cc" -o "$TRIAL_ROOT/bench/gcc-cxx-smoke"
"$TRIAL_ROOT/bench/gcc-cxx-smoke"
cat > "$TRIAL_ROOT/bench/gcc-fortran-smoke.f90" <<'F90'
program smoke
  implicit none
  real(8) :: x(3)
  x = [1.0d0, 2.0d0, 3.0d0]
  if (abs(sum(x)-6.0d0) > 1.0d-12) stop 1
end program
F90
"$FC" "$TRIAL_ROOT/bench/gcc-fortran-smoke.f90" -o "$TRIAL_ROOT/bench/gcc-fortran-smoke"
ldd "$TRIAL_ROOT/bench/gcc-fortran-smoke" | tee "$TRIAL_ROOT/logs/gcc-fortran-runtime.txt"
"$TRIAL_ROOT/bench/gcc-fortran-smoke"
```

Check that the recorded assembler/linker are the private binutils and that `ldd` has no missing dependency. If `-print-file-name` returns a bare filename rather than an existing path, resolve the missing installation before proceeding.

## 6. Build the pinned CMake when unavailable

Use an existing site CMake 3.31.12 if it is already usable and record its path. Otherwise build the staged source with the new GCC. Disable CMake's OpenSSL dependency here because this trial uses already-staged sources, not CMake HTTPS downloads.

```bash
test ! -e "$TRIAL_ROOT/build/cmake-3.31.12"
mkdir "$TRIAL_ROOT/build/cmake-3.31.12"
cd "$TRIAL_ROOT/build/cmake-3.31.12"
"$TRIAL_ROOT/src/cmake-3.31.12/bootstrap" \
  --prefix="$TRIAL_ROOT/tools/cmake-3.31.12" --parallel="$JOBS" \
  -- -DCMAKE_USE_OPENSSL=OFF \
  2>&1 | tee "$TRIAL_ROOT/logs/cmake-configure.log"
make -j "$JOBS" 2>&1 | tee "$TRIAL_ROOT/logs/cmake-build.log"
make install 2>&1 | tee "$TRIAL_ROOT/logs/cmake-install.log"
export CMAKE="$TRIAL_ROOT/tools/cmake-3.31.12/bin/cmake"
export CTEST="$TRIAL_ROOT/tools/cmake-3.31.12/bin/ctest"
"$CMAKE" --version
```

For an existing CMake, instead set `CMAKE` and `CTEST` to its absolute driver paths. Python 3 is required for the common timing harness and LAPACK test summaries; use the site's Python, with no extra Python packages.

## 7. Write a reusable environment file

```bash
export CPU_TARGET=x86-64
export HARDENING_SET=listed
export FORTIFY_LEVEL=2
export CF_MODE=full
{
  printf '%s\n' 'set -euo pipefail'
  for name in TRIAL_ROOT JOBS GCC_PREFIX BINUTILS_PREFIX GCC_LIB_DIRS CMAKE CTEST \
              CPU_TARGET HARDENING_SET FORTIFY_LEVEL CF_MODE; do
    printf 'export %s=%q\n' "$name" "${!name}"
  done
  cat <<'ENV'
source "$TRIAL_ROOT/site-env.sh"
export PATH="$GCC_PREFIX/bin:$BINUTILS_PREFIX/bin:$TRIAL_BASE_PATH"
export CC="$GCC_PREFIX/bin/gcc"
export CXX="$GCC_PREFIX/bin/g++"
export FC="$GCC_PREFIX/bin/gfortran"
export LD_LIBRARY_PATH="$GCC_LIB_DIRS${TRIAL_SITE_LIB_DIRS:+:$TRIAL_SITE_LIB_DIRS}"
hash -r
ENV
} > "$TRIAL_ROOT/env.sh"
```

In a new Bash shell, `source /absolute/path/to/hardening-trial/env.sh`, then follow [01 — Common profiles](01-common.md). `HARDENING_SET=listed` selects the supplied strong-stack/FORTIFY-2/RELRO/NOW profile, with PIE on benchmark executables. The optional broader experiment requires an explicit `extended` choice in 01. If the listed controls fail qualification, resolve that failure before building variants.
