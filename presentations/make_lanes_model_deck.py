"""Generate the CSE lanes-model stakeholder deck (editable, text-first)."""
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
TITLE, BODY = prs.slide_layouts[0], prs.slide_layouts[1]


def add(title, bullets, layout=BODY):
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    tf = slide.placeholders[1].text_frame
    tf.word_wrap = True
    first = True
    for level, text in bullets:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = text
        p.level = level
        p.font.size = Pt(20 if level == 0 else 16)
    return slide


# 1 — title
s = prs.slides.add_slide(TITLE)
s.shapes.title.text = "CSE Software Stack: The Lanes Model"
s.placeholders[1].text = "How we got here, what others do, and where we're going\nJuly 2026 — working draft"

# 2 — CSE today
add("Where CSE is today", [
    (0, "One entry module: CSEinit"),
    (1, "Two modes: standard (preloads MPI etc.) and noloads"),
    (1, "Two flavors: GCC-backed and Intel-backed"),
    (1, "Loading extends MODULEPATH and exposes compilers + packages"),
    (0, "What works: the entry-module pattern, multiple compiler surfaces"),
    (0, "What strains:"),
    (1, "Flat exposure — every package visible at once, conflicts by convention"),
    (1, "Hand-curated per system; a major upgrade means rebuilding everything"),
    (1, "No isolation between MPI/GPU build surfaces"),
])

# 3 — what others do
add("What the community runs in production", [
    (0, "NASA JSC Flight Sciences Lab (HPSF 2026)"),
    (1, "Lmod hierarchy: Core → Compiler → MPI; 1,000+ packages, 4 compiler suites, 3 MPIs"),
    (1, "“Users see modules, not spack… Users never run a spack command”"),
    (1, "Six ordered environments: compilers → base → mpis → hpc-libs → hpc-apps"),
    (0, "ALCF Polaris Spack PE"),
    (1, "spack-pe-base (system GCC, PE-agnostic) + spack-pe-gnu (PrgEnv lane)"),
    (1, "Meta-module gates MODULEPATH — packages appear after the stack loads"),
    (0, "Spack project / community (Kitware, E4S, HPSF)"),
    (1, "Incremental concretization: Foundation → GPU/MPI/Python columns → integrations"),
    (1, "Environment chaining + build caches as load-bearing infrastructure"),
])

# 4 — lessons / validation
add("The lessons that chose our route", [
    (0, "Flat environments don't scale"),
    (1, "NASA: 270+ root specs in one environment hung the concretizer → split into ordered environments"),
    (0, "Never mix compilers within a build surface"),
    (1, "NASA enforces compiler_mixing: false; mixed-Fortran apps must stay in one PrgEnv (mpi.mod)"),
    (0, "Build the common base once, portable target, reuse everywhere"),
    (0, "Users get modules and views — the package manager stays invisible"),
    (0, "Build caches turn 12-hour rebuilds into 2–3 hours (NASA)"),
    (0, "Every one of these is a first-class rule in the lanes model — by design, not by rediscovery"),
])

# 5 — the lanes model UX
add("The lanes model — what a user does", [
    (0, "1.  module load cse/<compiler>   (the compiler surface: system default or GCC)"),
    (1, "Core loads automatically: cmake, python, miniforge — the tool layer"),
    (1, "Foundation libraries (zlib, xz, zstd) arrive ambient in the view, one pinned version"),
    (0, "2.  Pick exactly one lane"),
    (1, "serial   |   mpi-craympich   |   gpu-craympich-gfx942"),
    (0, "3.  You see only that lane's packages"),
    (1, "No cross-lane contamination; no accidental MPI/GPU linkage"),
    (1, "Multiple versions inside a lane stay a familiar one-at-a-time module choice (hdf5/1.14.6 vs 1.14.5)"),
])

# 6 — lane vocabulary
add("Lane vocabulary", [
    (0, "core — packages with no MPI implementation at all (GSL) plus compiler-agnostic building blocks (Python, Miniforge, CMake); loadable"),
    (0, "serial — MPI-capable packages deliberately built without MPI (hdf5~mpi)"),
    (0, "mpi-<impl> — built against the named MPI (mpi-craympich, mpi-openmpi)"),
    (0, "gpu-<impl>-<arch> — GPU backend over GPU-aware MPI (gpu-craympich-gfx942)"),
    (0, "Names carry facts, not contents: the lane is called gpu-…, never gpu-kokkos"),
    (0, "Same vocabulary on every system — Cray or generic Linux"),
])

# 7 — pilot scope
add("Pilot scope", [
    (0, "Two compiler surfaces to start"),
    (1, "The system baseline (what the machine ships as default) and GCC"),
    (0, "One Cray system first, then a generic Linux cluster (already probed)"),
    (0, "Representative package roster (evolving; ~two versions each)"),
    (1, "Science: HDF5, NetCDF (C/Fortran/C++), FFTW, OpenBLAS, Boost, GSL, TAU"),
    (1, "GPU: Kokkos (pilot GPU lane content)"),
    (1, "Core: CMake, Python, Miniforge"),
    (0, "Multi-version by policy: unify:false lanes + single-version pinned foundation"),
])

# 8 — the differentiator
add("What's different: generated, not hand-curated", [
    (0, "NASA and ALCF hand-maintain their stacks per machine"),
    (0, "CSE generates the same shape from facts + policy:"),
    (1, "cluster-inspector probes the system → verified facts (compilers, MPIs, GPUs, fabric)"),
    (1, "site policy defaults (one small file) → which compiler family, which MPI, newest-version rules"),
    (1, "stack-composer renders every lane's configs — templates never contain policy"),
    (1, "Spack builds; modules and views are published to users"),
    (0, "A new system is a probe + a render — not months of curation"),
    (0, "Same pipeline handled a Cray EX (MI300A/ROCm) and an NVIDIA A100 Linux cluster unchanged"),
])

# 9 — status and next
add("Status and next steps", [
    (0, "Done"),
    (1, "End-to-end Cray smoke: probe → render → concretize → build (PrgEnv-gnu + cray-mpich + ROCm)"),
    (1, "Second system validated the generic-Linux path and hardened the prober"),
    (1, "Science stack (4 lanes, two-version roster) renders clean today"),
    (0, "Next"),
    (1, "Build out the science lanes on the Cray system; verify the module/view user flow"),
    (1, "Add the second compiler surface; then the NVIDIA system in parallel"),
    (1, "Release process: build caches, lockfiles, release manifest"),
])

out = "/private/tmp/claude-501/-Users-ravonventers-Development-stack-composer/a23f38af-bedd-4b94-9c54-985d109b5350/scratchpad/cse_lanes_model.pptx"
prs.save(out)
print("WROTE", out)
