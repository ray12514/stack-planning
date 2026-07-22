"""Generate the CSE lanes-model stakeholder deck — light theme, designed slides."""
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# palette — navy/gold, tuned to the HPCMP identity
BG = RGBColor(0xFF, 0xFF, 0xFF)
PANEL = RGBColor(0xF2, 0xF4, 0xF7)     # cool paper
PANEL2 = RGBColor(0xE3, 0xE7, 0xEE)
INK = RGBColor(0x16, 0x24, 0x3D)       # deep navy
TEXT = RGBColor(0x3B, 0x4A, 0x63)
MUTED = RGBColor(0x6E, 0x7B, 0x90)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GOLD = RGBColor(0x9A, 0x76, 0x14)      # kicker / accent
TEAL = RGBColor(0x11, 0x7A, 0x72)      # core
AMBER = RGBColor(0xBA, 0x74, 0x0E)     # serial
BLUE = RGBColor(0x2B, 0x62, 0xB8)      # mpi
VIOLET = RGBColor(0x6D, 0x4E, 0xAA)    # gpu
GRAY = RGBColor(0x50, 0x60, 0x7A)      # foundation
GREEN = RGBColor(0x2C, 0x7A, 0x4B)     # compiler-common

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide():
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = BG; r.line.fill.background()
    r.shadow.inherit = False
    return s


def txt(s, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    b = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    first = True
    for sz, col, bd, t in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = t; p.alignment = align
        p.font.size = Pt(sz); p.font.color.rgb = col; p.font.bold = bd
        p.font.name = "Avenir Next"
    return b


def box(s, x, y, w, h, fill, line=None, radius=True, lw=1.25):
    shp = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.shadow.inherit = False
    if line:
        shp.line.color.rgb = line; shp.line.width = Pt(lw)
    else:
        shp.line.fill.background()
    return shp


def boxtxt(s, x, y, w, h, fill, lines, line=None):
    shp = box(s, x, y, w, h, fill, line)
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.12)
    first = True
    for sz, col, bd, t in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = t; p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(sz); p.font.color.rgb = col; p.font.bold = bd
        p.font.name = "Avenir Next"
    return shp


def arrow(s, x1, y1, x2, y2, color=MUTED, w=2.25):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                               Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    c.shadow.inherit = False
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn('a:tailEnd'))
    tail.set('type', 'triangle'); tail.set('w', 'med'); tail.set('len', 'med')
    return c


def header(s, title, kicker=None):
    if kicker:
        txt(s, 0.6, 0.28, 12, 0.4, [(13, GOLD, True, kicker.upper())])
    txt(s, 0.6, 0.62, 12.1, 0.8, [(30, INK, True, title)])


def chip(s, x, y, w, label, h=0.42, size=12):
    boxtxt(s, x, y, w, h, PANEL2, [(size, TEXT, False, label)])


# ---------------------------------------------------------------- 1 · title
s = slide()
box(s, 0, 6.9, 13.333, 0.6, PANEL, radius=False)
txt(s, 0.9, 2.2, 11.5, 1.2, [(46, INK, True, "The CSE Software Stack")])
txt(s, 0.9, 3.6, 11.5, 1.4, [
    (22, TEXT, False, "One clean build surface per compiler, MPI, and GPU: the lanes model"),
    (15, MUTED, False, "How we got here, what the community runs, and where we're going"),
])
txt(s, 0.9, 6.95, 11.5, 0.5, [(12, MUTED, False, "July 2026  ·  working draft")])
for i, c in enumerate((TEAL, AMBER, BLUE, VIOLET)):
    box(s, 8.9 + i * 0.95, 2.35, 0.75, 0.75, c)

# ------------------------------------------------- 2 · today vs the model
s = slide()
header(s, "From one flat surface to lanes", "Where we are · where we're going")
box(s, 0.6, 1.75, 5.85, 5.15, PANEL)
txt(s, 0.85, 1.95, 5.4, 0.5, [(17, INK, True, "Today: CSEinit")])
txt(s, 0.85, 2.42, 5.4, 0.4, [(12.5, MUTED, False,
    "GCC- and Intel-backed flavors · standard / noloads · extends MODULEPATH")])
names = ["hdf5/1.14.6", "hdf5/1.10", "openmpi", "boost", "netcdf", "fftw",
         "python", "mkl", "gsl", "tau", "cmake", "openblas"]
for i, n in enumerate(names):
    chip(s, 0.9 + (i % 3) * 1.78, 3.0 + (i // 3) * 0.56, 1.62, n)
txt(s, 0.85, 5.45, 5.4, 1.3, [
    (13.5, AMBER, True, "Everything visible at once."),
    (12.5, MUTED, False, "Conflicts avoided by convention · MPI/GPU surfaces not isolated ·"),
    (12.5, MUTED, False, "hand-curated per system; upgrades mean rebuilding everything"),
])
box(s, 6.85, 1.75, 5.85, 5.15, PANEL)
txt(s, 7.1, 1.95, 5.4, 0.5, [(17, INK, True, "The lanes model")])
boxtxt(s, 7.4, 2.55, 4.75, 0.5, WHITE, [(13, INK, True, "module load cse/GCC")], line=PANEL2)
arrow(s, 9.775, 3.05, 9.775, 3.35, TEAL)
boxtxt(s, 7.4, 3.35, 1.5, 0.62, TEAL, [(11.5, WHITE, True, "Core"), (9.5, WHITE, False, "modules")])
boxtxt(s, 9.0, 3.35, 1.5, 0.62, GREEN, [(11.5, WHITE, True, "Common"), (9.5, WHITE, False, "modules")])
boxtxt(s, 10.6, 3.35, 1.55, 0.62, GRAY, [(11.5, WHITE, True, "Foundation"), (9.5, WHITE, False, "on the path")])
arrow(s, 9.775, 3.97, 9.775, 4.27, TEAL)
txt(s, 7.4, 4.27, 4.9, 0.35, [(11.5, MUTED, True, "CHOOSE EXACTLY ONE")], align=PP_ALIGN.CENTER)
boxtxt(s, 7.4, 4.62, 1.5, 0.6, AMBER, [(12.5, WHITE, True, "Serial")])
boxtxt(s, 9.0, 4.62, 1.5, 0.6, BLUE, [(12.5, WHITE, True, "MPI")])
boxtxt(s, 10.6, 4.62, 1.55, 0.6, VIOLET, [(12.5, WHITE, True, "GPU")])
txt(s, 7.1, 5.45, 5.4, 1.3, [
    (13.5, TEAL, True, "You see exactly one lane."),
    (12.5, MUTED, False, "GPU is a complete MPI-capable lane when the selected toolchain supports it ·"),
    (12.5, MUTED, False, "package modules prevent incompatible version mixes"),
])

# ------------------------------------------------- 3 · community validation
s = slide()
header(s, "The shape everyone converges on", "Validation · production prior art")
cards = [
    ("NASA JSC  ·  Flight Sciences Lab", BLUE,
     "1,000+ packages · 4 compiler suites · 3 MPIs",
     ["Lmod hierarchy: Core → Compiler → MPI",
      "compiler_mixing: false keeps lanes isolated",
      "“Users never run a spack command.”"]),
    ("ALCF  ·  Polaris Spack PE", VIOLET,
     "spack-pe-base + spack-pe-gnu",
     ["Base built once with system GCC, PE-agnostic",
      "Meta-module gates MODULEPATH",
      "Packages appear only after the stack loads"]),
    ("Spack project  ·  E4S / HPSF", TEAL,
     "Incremental concretization",
     ["Foundation → GPU/MPI/Python → integrations",
      "Flat 270-spec environments hang the solver",
      "Build caches are load-bearing, not optional"]),
]
for i, (org, color, stat, lines) in enumerate(cards):
    x = 0.6 + i * 4.18
    box(s, x, 1.75, 3.95, 3.9, PANEL)
    txt(s, x + 0.25, 2.0, 3.5, 0.55, [(14.5, color, True, org)])
    txt(s, x + 0.25, 2.62, 3.5, 0.75, [(16, color, True, stat)])
    txt(s, x + 0.25, 3.55, 3.5, 2.0,
        [(12.5, TEXT, False, ln) for ln in lines])
boxtxt(s, 0.6, 6.0, 12.13, 0.62, PANEL2, [(14, INK, True,
    "Base built once  →  isolated per-compiler/MPI fan-out  →  modules are the user contract")])

# ------------------------------------------------- 4 · how it's built
s = slide()
header(s, "How a stack is built", "Schematic · generated, not hand-curated")
stages = [("PROBE", "record the system's\nfacts, once"),
          ("POLICY", "one small site\ndefaults file"),
          ("RENDER", "derive every lane's\nbuild input"),
          ("BUILD", "Spack · lanes build\nin parallel"),
          ("PUBLISH", "modules · views\nbuild caches")]
for i, (t, d) in enumerate(stages):
    x = 0.6 + i * 2.52
    boxtxt(s, x, 1.8, 2.25, 1.05, PANEL,
           [(15, INK, True, t)] + [(11, MUTED, False, ln) for ln in d.split("\n")],
           line=PANEL2)
    if i < 4:
        arrow(s, x + 2.27, 2.32, x + 2.5, 2.32, TEAL)
boxtxt(s, 2.35, 3.4, 8.6, 0.75, WHITE, [
    (14.5, INK, True, "Core + Foundation: built once per compiler surface, portable target"),
    (11.5, MUTED, False, "cmake · python · miniforge   |   zlib · xz · zstd (single pinned version)"),
], line=TEAL)
lanes = [("Serial", AMBER, "non-MPI hdf5 · fftw · boost, plus common BLAS/LAPACK"),
         ("MPI", BLUE, "Cray MPICH · hdf5+mpi · fftw+mpi · tau · dakota"),
         ("GPU", VIOLET, "the MPI roster plus kokkos · rocm/cuda arch from the probe")]
for i, (name, color, content) in enumerate(lanes):
    x = 1.5 + i * 3.6
    arrow(s, 6.65, 4.15, x + 1.65, 4.75, color)
    boxtxt(s, x, 4.75, 3.3, 0.95, color,
           [(14.5, WHITE, True, name), (11, WHITE, False, content)])
txt(s, 0.6, 6.15, 12.1, 0.9, [
    (14, TEAL, True, "A new system is a probe and a render, not months of curation."),
    (12.5, MUTED, False,
     "The same pipeline produced a Cray EX (MI300A · ROCm) stack and an NVIDIA A100 Linux stack, unchanged."),
])

# ------------------------------------------------- 5 · user flow
s = slide()
header(s, "What a user experiences", "Schematic · the front door")
cx = 6.666
boxtxt(s, cx - 2.5, 1.8, 5.0, 0.62, WHITE,
       [(16, INK, True, "$ module load cse/GCC")], line=PANEL2)
arrow(s, cx, 2.42, cx, 2.82, TEAL)
boxtxt(s, 0.75, 2.82, 3.8, 1.0, TEAL, [
    (13, WHITE, True, "Core: modules available"),
    (10.5, WHITE, False, "cmake · python · miniforge · gsl"),
])
boxtxt(s, 4.77, 2.82, 3.8, 1.0, GREEN, [
    (13, WHITE, True, "GCC Common: modules available"),
    (10.5, WHITE, False, "openblas · gnuplot"),
])
boxtxt(s, 8.79, 2.82, 3.8, 1.0, GRAY, [
    (13, WHITE, True, "Foundation: on your paths"),
    (10.5, WHITE, False, "zlib · xz · zstd · one pinned version"),
])
arrow(s, cx, 3.82, cx, 4.32, TEAL)
txt(s, cx - 2.5, 4.32, 5.0, 0.38, [(12.5, MUTED, True, "CHOOSE EXACTLY ONE LANE")],
    align=PP_ALIGN.CENTER)
for i, (name, color, content) in enumerate([
        ("Serial", AMBER, "non-MPI hdf5 · netcdf · fftw · boost"),
        ("MPI", BLUE, "Cray MPICH · hdf5+mpi · fftw+mpi · boost+mpi · tau"),
        ("GPU", VIOLET, "the MPI roster plus kokkos +rocm gfx942")]):
    x = 0.75 + i * 4.0
    boxtxt(s, x, 4.75, 3.8, 1.0, color,
           [(15, WHITE, True, name), (11.5, WHITE, False, content)])
boxtxt(s, 0.75, 6.1, 11.85, 0.85, PANEL, [
    (13.5, INK, True, "Only the chosen lane is visible; common packages (BLAS/LAPACK, gnuplot) load from the surface itself."),
    (12, MUTED, False, "Clean module names stay; module metadata blocks incompatible HDF5/NetCDF-style version mixes."),
])

# ------------------------------------------------- 6 · lane vocabulary
s = slide()
header(s, "Lane vocabulary", "Names carry facts, not contents")
vocab = [
    ("Core", TEAL, "Compiler-agnostic building blocks and tools. Available as soon as the surface loads.",
     "cmake · python · miniforge · gsl"),
    ("Common", GREEN, "Built for this compiler, one build for every lane. Available with the surface, like Core.",
     "openblas · gnuplot"),
    ("Serial", AMBER, "MPI-capable packages built without MPI on purpose, for work that never launches a parallel job.",
     "hdf5~mpi · fftw~mpi · boost~mpi"),
    ("MPI", BLUE, "Built against the system MPI. Qualified only when the system offers more than one.",
     "MPI · or MPI-openmpi / MPI-mpich"),
    ("GPU", VIOLET, "The full MPI roster plus the GPU payload. Load GPU instead of MPI, not in addition.",
     "GPU · or GPU-gfx90a / GPU-gfx942"),
]
for i, (name, color, desc, ex) in enumerate(vocab):
    x = 0.6 + i * 2.36
    box(s, x, 1.8, 2.24, 3.75, PANEL)
    box(s, x, 1.8, 2.24, 0.65, color)
    txt(s, x + 0.1, 1.94, 2.04, 0.5, [(15, WHITE, True, name)], align=PP_ALIGN.CENTER)
    txt(s, x + 0.16, 2.6, 1.95, 2.1, [(11, TEXT, False, desc)])
    txt(s, x + 0.16, 4.75, 1.95, 0.7, [(10, MUTED, False, ex)])
boxtxt(s, 0.6, 5.75, 12.13, 0.62, PANEL2, [(14, INK, True,
    "Modules: cse/<Compiler>/<Lane>. Short names for users; dependency compatibility is enforced by module metadata.")])

# ------------------------------------------------- 7 · pilot scope
s = slide()
header(s, "Pilot scope", "Two compiler surfaces · four-system validation")
for i, (surf, note) in enumerate([
        ("cse/<SystemDefault>", "whatever the machine blesses as its baseline"),
        ("cse/GCC", "the portable reference surface")]):
    x = 0.6 + i * 6.25
    box(s, x, 1.8, 5.9, 2.9, PANEL)
    txt(s, x + 0.25, 1.98, 5.4, 0.5, [(16, INK, True, surf)])
    txt(s, x + 0.25, 2.5, 5.4, 0.4, [(12, MUTED, False, note)])
    boxtxt(s, x + 0.3, 3.0, 1.65, 0.55, TEAL, [(11, WHITE, True, "Core")])
    boxtxt(s, x + 2.1, 3.0, 1.65, 0.55, GREEN, [(11, WHITE, True, "Common")])
    boxtxt(s, x + 3.9, 3.0, 1.65, 0.55, GRAY, [(11, WHITE, True, "Foundation")])
    boxtxt(s, x + 0.3, 3.72, 1.65, 0.62, AMBER, [(12, WHITE, True, "Serial")])
    boxtxt(s, x + 2.1, 3.72, 1.65, 0.62, BLUE, [(12, WHITE, True, "MPI")])
    boxtxt(s, x + 3.9, 3.72, 1.65, 0.62, VIOLET, [(12, WHITE, True, "GPU")])
txt(s, 0.6, 4.95, 12, 0.4, [(13, INK, True, "Representative roster: newest two supported releases")])
roster = ["HDF5", "NetCDF-C", "NetCDF-Fortran", "NetCDF-C++", "FFTW", "OpenBLAS",
          "Boost", "GSL", "TAU", "Dakota", "Kokkos", "Gnuplot", "Python", "Miniforge"]
for i, n in enumerate(roster):
    chip(s, 0.6 + (i % 7) * 1.78, 5.4 + (i // 7) * 0.56, 1.62, n)
txt(s, 0.6, 6.65, 12.1, 0.5, [(12, MUTED, False,
    "Newest-two policy: clean package names · compatible chains load · incompatible mixes fail clearly")])

# ------------------------------------------------- 8 · pilot systems
s = slide()
header(s, "Four systems will prove the pilot", "Test matrix · breadth by design")
systems = [
    ("Blueback", "NAVY · HPE Cray EX4000 · SLES · Slurm",
     "Standard: AMD EPYC 9654 Genoa, 192 cores",
     "AI/ML: AMD Instinct MI300A APU, 96 cores + 4 × MI300A",
     VIOLET, "Cray PE · AMD APU"),
    ("Fran", "ARL · HPE Cray EX4000 · RHEL 9 · Slurm",
     "Standard: AMD EPYC Genoa, 192 cores",
     "AI/ML: NVIDIA H200",
     BLUE, "second Cray site · newest NVIDIA"),
    ("Raider", "AFRL · Penguin TrueHPC · RHEL 8 · Slurm",
     "Standard: AMD EPYC 7713 Milan, 128 cores",
     "AI/ML: same CPU + 4 × NVIDIA A100 SXM4",
     TEAL, "generic Linux · CUDA"),
    ("Wheat", "ERDC · Liqid composable · RHEL 8 · PBS",
     "Standard: Intel Xeon 9242 Cascade Lake, 92 cores",
     "AI/ML: same CPU + 4 or 6 × NVIDIA A100",
     AMBER, "Intel CPU · composable GPU"),
]
for i, (name, platform, cpu, gpu, color, proof) in enumerate(systems):
    x = 0.6 + (i % 2) * 6.25
    y = 1.78 + (i // 2) * 2.25
    box(s, x, y, 5.9, 1.95, PANEL)
    txt(s, x + 0.3, y + 0.16, 2.1, 0.4, [(17, color, True, name)])
    txt(s, x + 2.35, y + 0.19, 3.25, 0.35, [(11.5, color, True, proof.upper())],
        align=PP_ALIGN.RIGHT)
    txt(s, x + 0.3, y + 0.65, 5.3, 0.32, [(12.5, TEXT, True, platform)])
    txt(s, x + 0.3, y + 1.04, 5.3, 0.3, [(12, MUTED, False, cpu)])
    txt(s, x + 0.3, y + 1.4, 5.3, 0.3, [(12, MUTED, False, gpu)])
boxtxt(s, 0.6, 6.35, 12.13, 0.58, PANEL2, [(13, INK, True,
    "Coverage: SLES + RHEL 8/9 · AMD + Intel CPUs · MI300A + H200 + A100 · Slurm + PBS")])
txt(s, 0.6, 7.02, 12.1, 0.24, [(9.5, MUTED, False,
    "Source: HPC Centers hardware inventory, July 2026")],
    align=PP_ALIGN.RIGHT)

# ------------------------------------------------- 9 · status / next
s = slide()
header(s, "What happens next", "The plan from here")
steps = [
    ("Build the pilot stack on the four systems", TEAL,
     "Probe each machine, render its lanes, concretize, install. The front door is the first real "
     "test of the naming: one compiler surface, then one lane, then a package."),
    ("Prove the module contract", BLUE,
     "Compatible chains load and incompatible mixes fail. Lane purity and version pairing are "
     "checked in the concretized lockfile, never assumed from the render."),
    ("Stand up the release process", VIOLET,
     "Build caches, a lockfile per lane, and a release manifest, so a release can be rebuilt "
     "exactly, promoted deliberately, and rolled back by moving a pointer."),
    ("Settle the open decisions", AMBER,
     "Vendor math libraries, compiler surfaces, the Serial tier, and when performance targeting "
     "turns on. These shape the roster before it is fixed for v1."),
]
for i, (title, color, detail) in enumerate(steps):
    y = 1.8 + i * 1.32
    box(s, 0.6, y, 12.13, 1.15, PANEL)
    boxtxt(s, 0.6, y, 0.62, 1.15, color, [(19, WHITE, True, str(i + 1))])
    txt(s, 1.45, y + 0.18, 11.0, 0.34, [(15.5, INK, True, title)])
    txt(s, 1.45, y + 0.58, 11.0, 0.46, [(11.5, MUTED, False, detail)])

# ------------------------------------------------- appendix · build roots
# Tables mirror stack-content/package-sets/{core-foundation,science-full}.yaml
# exactly — every root spec appears. Update both together.

POLICY_FOOTER = "Version policy: the newest supported release and its immediate predecessor"


def roster_table(s, y, sections, col_pkg=2.1, col_ver=2.5, row_h=0.33):
    """One table: lane-colored section divider rows + package rows."""
    x, w = 0.6, 12.13
    nrows = 1 + sum(1 + len(rows) for _, _, rows in sections)
    frame = s.shapes.add_table(nrows, 3, Inches(x), Inches(y), Inches(w),
                               Inches(row_h * nrows))
    tbl = frame.table
    tbl.first_row = False; tbl.horz_banding = False
    tbl.columns[0].width = Inches(col_pkg)
    tbl.columns[1].width = Inches(col_ver)
    tbl.columns[2].width = Inches(w - col_pkg - col_ver)

    def style(cell, text, size, color, bold, fill):
        cell.fill.solid(); cell.fill.fore_color.rgb = fill
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.08)
        cell.margin_top = cell.margin_bottom = Inches(0.015)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.size = Pt(size); p.font.color.rgb = color; p.font.bold = bold
        p.font.name = "Avenir Next"

    for c, head in enumerate(("Package", "Versions", "Built as · pairing")):
        style(tbl.cell(0, c), head, 11, MUTED, True, WHITE)
    r = 1
    for label, color, rows in sections:
        sec = tbl.cell(r, 0); sec.merge(tbl.cell(r, 2))
        style(sec, label, 11.5, WHITE, True, color)
        r += 1
        for pkg, vers, note in rows:
            style(tbl.cell(r, 0), pkg, 11, INK, True, WHITE)
            style(tbl.cell(r, 1), vers, 11, TEXT, False, WHITE)
            style(tbl.cell(r, 2), note, 10.5, MUTED, False, WHITE)
            r += 1
    return frame


def appendix_slide(title, sections, row_h=0.33):
    s = slide()
    header(s, title, "Appendix · exact build roots")
    roster_table(s, 1.62, sections, row_h=row_h)
    txt(s, 0.6, 7.2, 12.1, 0.28, [(10.5, MUTED, False, POLICY_FOOTER)])
    return s


# ------------------------------------------------- 10 · open questions
s = slide()
header(s, "Open questions for the team", "Decisions we need · not settled yet")
questions = [
    (GREEN, "Do we offer the vendor's math libraries as well as OpenBLAS?",
     "OpenBLAS is now the one BLAS and LAPACK, so users get the same library on every system. "
     "Cray LibSci is already on the path on Blueback and Fran, and Intel systems would expect MKL. "
     "Both are registered rather than built, so this is policy per system, not build cost."),
    (TEAL, "Which compiler surfaces does the pilot carry?",
     "The pilot carries two per system: the one the machine blesses as its baseline, plus GCC as "
     "the portable reference. CSEinit offers GCC and Intel today, so whether Intel is one of the "
     "two on the systems that have it is the open part."),
    (AMBER, "Does the Serial lane stay?",
     "Serial exists so users who are not running parallel do not carry the MPI runtime: analysis "
     "and post-processing on a login node, small tools, anything linking HDF5 or NetCDF without "
     "wanting libmpi behind it. An MPI build on one rank does the same work, so dropping Serial "
     "would halve the build matrix and push the MPI runtime onto everyone."),
    (VIOLET, "Performance targeting: baseline first, tuning after.",
     "The plan is to build every lane at the portable baseline, prove the model, then turn on "
     "per-lane tuning for Genoa, Milan, or Cascade Lake. Each target is a flag plus a full "
     "rebuild, so the open part is when, not whether."),
    (GOLD, "Consistency means the same functionality, not the same implementations.",
     "A user builds and runs the same way on every system: same front door, same rosters, "
     "same workflow, with each machine's native MPI and compiler underneath. The open part is "
     "the floor: which capabilities every system must provide, and whether one pinned CSE GCC "
     "anchors the compilers."),
]
for i, (color, q, detail) in enumerate(questions):
    y = 1.66 + i * 1.06
    box(s, 0.6, y, 12.13, 0.98, PANEL)
    txt(s, 0.95, y + 0.1, 11.5, 0.3, [(13, color, True, q)])
    txt(s, 0.95, y + 0.41, 11.5, 0.54, [(10.5, MUTED, False, detail)])

# ------------------------------------------------- 11 · starter questions
s = slide()
header(s, "If we start building: what has to be decided?", "Discussion \u00b7 starter questions for the build")
starters = [
    (TEAL, "Which compiler anchors each system's stack?",
     "Every package on a system builds against this choice, so it comes first. The system's own "
     "compiler, one common version everywhere, or something else?"),
    (BLUE, "Which MPI pairs with it on each system?",
     "Whatever we pick has to work with each machine's fabric and job launcher. Do we take what "
     "each site provides, and what do we do where that answer is unclear?"),
    (AMBER, "What CPU baseline do we build for?",
     "One portable target that runs on every pilot system, or per-system tuning from day one? "
     "This sets how many builds exist and where they can run."),
    (VIOLET, "Where does the software live on each system?",
     "Install locations, and who owns them, per system. Nothing installs until someone can answer "
     "this for their machine."),
    (GOLD, "What has to pass before a build counts as done?",
     "A shared finish line, agreed before the first build starts: what compiles, what runs, and "
     "what we can rebuild from scratch."),
]
for i, (color, q, detail) in enumerate(starters):
    y = 1.66 + i * 1.06
    box(s, 0.6, y, 12.13, 0.98, PANEL)
    txt(s, 0.95, y + 0.1, 11.5, 0.3, [(13, color, True, q)])
    txt(s, 0.95, y + 0.41, 11.5, 0.54, [(10.5, MUTED, False, detail)])
boxtxt(s, 0.6, 6.98, 12.13, 0.42, PANEL2, [(12, INK, True,
    "And just as useful: which of these can wait until after the first builds?")])

# ------------------------------------------------- appendix · layer stacking
s = slide()
header(s, "What each lane exposes", "Appendix · how the layers stack")
txt(s, 0.6, 1.52, 12.1, 0.3, [(11.5, MUTED, True, "CHOOSE EXACTLY ONE LANE")],
    align=PP_ALIGN.CENTER)
payloads = [
    ("Serial", AMBER, "hdf5 · netcdf · fftw · boost",
     "the same packages, built without MPI"),
    ("MPI", BLUE, "hdf5 · netcdf · fftw · boost · tau · dakota",
     "built against the system MPI"),
    ("GPU", VIOLET, "the MPI roster, plus kokkos",
     "+rocm / +cuda, arch from the probe"),
]
for i, (name, color, content, note) in enumerate(payloads):
    boxtxt(s, 0.6 + i * 4.18, 1.88, 3.95, 1.45, color, [
        (15, WHITE, True, name),
        (11, WHITE, False, content),
        (10, WHITE, False, note),
    ])
layers = [
    (GREEN, "Compiler-common: built for this compiler, independent of the lane",
     "openblas · gnuplot · loadable as soon as the surface loads, before any lane; one build, one install"),
    (TEAL, "Core: loads with the compiler surface",
     "cmake · ninja · git · python · py-numpy · miniforge · gsl · sqlite"),
    (GRAY, "Foundation: on your paths automatically, nothing to load",
     "zlib · xz · zstd, single pinned version"),
]
for i, (color, title, body) in enumerate(layers):
    boxtxt(s, 0.6, 3.5 + i * 0.83, 12.13, 0.7, color, [
        (12.5, WHITE, True, title),
        (10.5, WHITE, False, body),
    ])
boxtxt(s, 0.6, 6.02, 12.13, 0.6, WHITE, [
    (13, INK, True, "cse/<Compiler> surface: everything above sits on one compiler"),
    (10.5, MUTED, False, "lanes never mix compilers; loading a second lane fails loudly"),
], line=PANEL2)
txt(s, 0.6, 6.78, 12.1, 0.5, [(11.5, MUTED, False,
    "A user's view is one column: the surface, Foundation, Core, the common packages, "
    "and exactly one payload. The other payloads stay invisible until their lane is loaded.")])

appendix_slide("Core and foundation: built once per compiler surface", [
    ("Foundation: on your paths automatically, never a loadable module", GRAY, [
        ("zlib",   "1.3.1", "single pinned version (require: pin)"),
        ("xz",     "5.4.6", "single pinned version"),
        ("zstd",   "1.5.6", "single pinned version"),
    ]),
    ("Core tools: user-loadable, compiler-agnostic", TEAL, [
        ("cmake",      "4.3.3 · 4.2.3", ""),
        ("ninja · pkgconf · git", "newest", "unpinned; newest from the recipe generation"),
        ("python",     "3.14.5 · 3.13.13", "the two newest supported minor lines"),
        ("py-numpy",   "2.4.6", "built against each python line (newest non-deprecated recipe)"),
        ("miniforge3", "26.1.1-3", "single by nature; installer for user-managed environments"),
    ]),
    ("Only-serial by nature: no MPI implementation exists", TEAL, [
        ("gsl",    "2.8 · 2.7.1", ""),
        ("sqlite", "3.53.1 · 3.51.2", ""),
    ]),
    ("Compiler-common: its own group, loadable before any lane", GREEN, [
        ("openblas", "0.3.33 · 0.3.32", "the one BLAS and LAPACK: openblas provides both APIs"),
        ("gnuplot",  "6.0.0 · 5.4.10",  "needs the surface's compiler, so not Core"),
    ]),
])

appendix_slide("Serial lane: MPI-capable, deliberately built without MPI", [
    ("Serial data chains: each netcdf rides one named hdf5", AMBER, [
        ("hdf5",           "2.1.0 · 1.14.6", "~mpi +fortran +cxx +hl"),
        ("netcdf-c",       "4.10.0 · 4.9.3", "~mpi, paired to hdf5 2.1.0 / 1.14.6"),
        ("netcdf-fortran", "4.6.2 · 4.6.1",  "rides its paired netcdf-c / hdf5 chain"),
        ("netcdf-cxx4",    "4.3.1", "single recipe version; newest chain only"),
    ]),
    ("Serial math", AMBER, [
        ("fftw",  "3.3.11 · 3.3.10", "~mpi"),
        ("boost", "1.90.0 · 1.89.0", "~mpi here; the MPI lane carries its own +mpi build"),
    ]),
])

appendix_slide("MPI and GPU lanes: built against the system MPI", row_h=0.278, sections=[
    ("MPI data chains: same pairing rule as serial", BLUE, [
        ("hdf5",           "2.1.0 · 1.14.6", "+mpi +fortran +cxx +hl"),
        ("netcdf-c",       "4.10.0 · 4.9.3", "+mpi +parallel-netcdf, paired to hdf5 2.1.0 / 1.14.6"),
        ("netcdf-fortran", "4.6.2 · 4.6.1",  "rides its paired netcdf-c / hdf5 chain"),
        ("netcdf-cxx4",    "4.3.1", "single recipe version; newest chain only"),
    ]),
    ("MPI math and tools", BLUE, [
        ("fftw",   "3.3.11 · 3.3.10", "+mpi"),
        ("boost",  "1.90.0 · 1.89.0", "+mpi; the Serial lane carries its own ~mpi build"),
        ("netlib-scalapack", "2.2.3 · 2.2.2", "distributed dense solvers; MPI by nature, no serial form"),
        ("tau",    "2.35.1",   "+mpi; one version, a tool users run"),
        ("dakota", "6.24.0 · 6.23.0", "+mpi; heaviest build in the roster"),
    ]),
    ("GPU lane: selects the full MPI roster above, plus the GPU payload", VIOLET, [
        ("tau", "2.35.1", "built with MPI and the lane's GPU backend, so it sees kernels as well as MPI"),
        ("kokkos", "5.1.1 · 5.1.0",
         "built for the lane's GPU architecture from the probe; new here, it proves the GPU path"),
    ]),
    ("Compiler-common: loadable here too, from the surface", GREEN, [
        ("compiler-common", "see Core slide",
         "openblas · gnuplot: available before and regardless of the lane choice"),
    ]),
    ("Externals: used from the system, never built", GRAY, [
        ("externals", "system",
         "cray-mpich (Platform-backed) · openmpi, openssl (Site-external)"),
    ]),
])

out = Path(__file__).with_name("cse_lanes_model.pptx")
prs.save(str(out))
print("WROTE", out)
