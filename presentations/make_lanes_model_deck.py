"""Generate the CSE lanes-model stakeholder deck — light theme, designed slides."""
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# palette — light professional
BG = RGBColor(0xFF, 0xFF, 0xFF)
PANEL = RGBColor(0xF1, 0xF5, 0xF9)     # slate-100
PANEL2 = RGBColor(0xE2, 0xE8, 0xF0)    # slate-200
INK = RGBColor(0x0F, 0x17, 0x2A)       # slate-900
TEXT = RGBColor(0x33, 0x41, 0x55)      # slate-700
MUTED = RGBColor(0x64, 0x74, 0x8B)     # slate-500
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEAL = RGBColor(0x0D, 0x94, 0x88)      # core
AMBER = RGBColor(0xD9, 0x77, 0x06)     # serial
BLUE = RGBColor(0x25, 0x63, 0xEB)      # mpi
VIOLET = RGBColor(0x7C, 0x3A, 0xED)    # gpu
GRAY = RGBColor(0x47, 0x55, 0x69)      # foundation
GREEN = RGBColor(0x15, 0x80, 0x3D)

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
        txt(s, 0.6, 0.28, 12, 0.4, [(13, TEAL, True, kicker.upper())])
    txt(s, 0.6, 0.62, 12.1, 0.8, [(30, INK, True, title)])
    box(s, 0.62, 1.42, 1.6, 0.045, TEAL, radius=False)


def chip(s, x, y, w, label, h=0.42, size=12):
    boxtxt(s, x, y, w, h, PANEL2, [(size, TEXT, False, label)])


# ---------------------------------------------------------------- 1 · title
s = slide()
box(s, 0, 6.9, 13.333, 0.6, PANEL, radius=False)
txt(s, 0.9, 2.2, 11.5, 1.2, [(46, INK, True, "The CSE Software Stack")])
box(s, 0.95, 3.35, 2.4, 0.06, TEAL, radius=False)
txt(s, 0.9, 3.6, 11.5, 1.4, [
    (22, TEXT, False, "One clean build surface per compiler, MPI, and GPU — the lanes model"),
    (15, MUTED, False, "How we got here, what the community runs, and where we're going"),
])
txt(s, 0.9, 6.95, 11.5, 0.5, [(12, MUTED, False, "July 2026  ·  working draft")])
for i, c in enumerate((TEAL, AMBER, BLUE, VIOLET)):
    box(s, 8.9 + i * 0.95, 2.35, 0.75, 0.75, c)

# ------------------------------------------------- 2 · today vs the model
s = slide()
header(s, "From one flat surface to lanes", "Where we are · where we're going")
box(s, 0.6, 1.75, 5.85, 5.15, PANEL)
txt(s, 0.85, 1.95, 5.4, 0.5, [(17, INK, True, "Today — CSEinit")])
txt(s, 0.85, 2.42, 5.4, 0.4, [(12.5, MUTED, False,
    "GCC- and Intel-backed flavors · standard / noloads · extends MODULEPATH")])
names = ["hdf5/1.14.6", "hdf5/1.10", "openmpi", "boost", "netcdf", "fftw",
         "python", "mkl", "gsl", "tau", "cmake", "openblas"]
for i, n in enumerate(names):
    chip(s, 0.9 + (i % 3) * 1.78, 3.0 + (i // 3) * 0.56, 1.62, n)
txt(s, 0.85, 5.45, 5.4, 1.3, [
    (13.5, AMBER, True, "Everything visible at once."),
    (12.5, MUTED, False, "Conflicts avoided by convention · MPI/GPU surfaces not isolated ·"),
    (12.5, MUTED, False, "hand-curated per system — upgrades mean rebuilding everything"),
])
box(s, 6.85, 1.75, 5.85, 5.15, PANEL)
txt(s, 7.1, 1.95, 5.4, 0.5, [(17, INK, True, "The lanes model")])
boxtxt(s, 7.4, 2.55, 4.75, 0.5, WHITE, [(13, INK, True, "module load cse/GCC")], line=PANEL2)
arrow(s, 9.775, 3.05, 9.775, 3.35, TEAL)
boxtxt(s, 7.4, 3.35, 2.3, 0.62, TEAL, [(12.5, WHITE, True, "Core — automatic")])
boxtxt(s, 9.85, 3.35, 2.3, 0.62, GRAY, [(12.5, WHITE, True, "Foundation — in view")])
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
      "compiler_mixing: false — lanes stay isolated",
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
    box(s, x, 1.75, 3.95, 0.09, color, radius=False)
    txt(s, x + 0.25, 2.0, 3.5, 0.55, [(14.5, INK, True, org)])
    txt(s, x + 0.25, 2.62, 3.5, 0.75, [(16, color, True, stat)])
    txt(s, x + 0.25, 3.55, 3.5, 2.0,
        [(12.5, TEXT, False, ln) for ln in lines])
boxtxt(s, 0.6, 6.0, 12.13, 0.62, PANEL2, [(14, INK, True,
    "Base built once  →  isolated per-compiler/MPI fan-out  →  modules are the user contract")])

# ------------------------------------------------- 4 · how it's built
s = slide()
header(s, "How a stack is built", "Schematic · generated, not hand-curated")
stages = [("PROBE", "cluster-inspector\nreads the system"),
          ("POLICY", "one small site\ndefaults file"),
          ("RENDER", "stack-composer\nemits every lane"),
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
    (14.5, INK, True, "Core + Foundation — built once per compiler surface, portable target"),
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
    (14, TEAL, True, "A new system is a probe + a render — not months of curation."),
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
boxtxt(s, cx - 4.3, 2.82, 4.1, 1.0, TEAL, [
    (14.5, WHITE, True, "Core — loads automatically"),
    (11.5, WHITE, False, "cmake · python · miniforge · gsl"),
])
boxtxt(s, cx + 0.2, 2.82, 4.1, 1.0, GRAY, [
    (14.5, WHITE, True, "Foundation — ambient in the view"),
    (11.5, WHITE, False, "zlib · xz · zstd — one pinned version"),
])
arrow(s, cx, 3.82, cx, 4.32, TEAL)
txt(s, cx - 2.5, 4.32, 5.0, 0.38, [(12.5, MUTED, True, "CHOOSE EXACTLY ONE LANE")],
    align=PP_ALIGN.CENTER)
for i, (name, color, content) in enumerate([
        ("Serial", AMBER, "non-MPI hdf5 · fftw · boost, plus openblas · gnuplot"),
        ("MPI", BLUE, "Cray MPICH · hdf5+mpi · fftw+mpi · boost+mpi · tau"),
        ("GPU", VIOLET, "the MPI roster plus kokkos +rocm gfx942")]):
    x = 0.75 + i * 4.0
    boxtxt(s, x, 4.75, 3.8, 1.0, color,
           [(15, WHITE, True, name), (11.5, WHITE, False, content)])
boxtxt(s, 0.75, 6.1, 11.85, 0.85, PANEL, [
    (13.5, INK, True, "Only the chosen lane is visible; common packages (BLAS/LAPACK, gnuplot) are reachable from every lane."),
    (12, MUTED, False, "Clean module names stay; module metadata blocks incompatible HDF5/NetCDF-style version mixes."),
])

# ------------------------------------------------- 6 · lane vocabulary
s = slide()
header(s, "Lane vocabulary", "Names carry facts, not contents")
vocab = [
    ("Core", TEAL, "Compiler-agnostic building blocks and tools. They load with the surface, before any lane is chosen.",
     "cmake · python · miniforge · gsl · sqlite"),
    ("Serial", AMBER, "Two classes: non-MPI builds of MPI-capable packages, and common compiler-dependent packages that every lane can load.",
     "hdf5~mpi · fftw~mpi  |  openblas · gnuplot"),
    ("MPI", BLUE, "Built against the system MPI. Qualified only when the system offers more than one.",
     "MPI  ·  or MPI-openmpi / MPI-mpich"),
    ("GPU", VIOLET, "Carries the full MPI roster plus the GPU payload. Load GPU instead of MPI, not in addition to it.",
     "GPU  ·  or GPU-gfx90a / GPU-gfx942"),
]
for i, (name, color, desc, ex) in enumerate(vocab):
    x = 0.6 + i * 3.22
    box(s, x, 1.8, 3.0, 3.55, PANEL)
    box(s, x, 1.8, 3.0, 0.75, color)
    txt(s, x + 0.15, 1.92, 2.7, 0.55, [(17, WHITE, True, name)], align=PP_ALIGN.CENTER)
    txt(s, x + 0.22, 2.75, 2.6, 1.7, [(12.5, TEXT, False, desc)])
    txt(s, x + 0.22, 4.55, 2.6, 0.7, [(11.5, MUTED, False, ex)])
boxtxt(s, 0.6, 5.75, 12.13, 0.62, PANEL2, [(14, INK, True,
    "Modules: cse/<Compiler>/<Lane> — short names for users; dependency compatibility is enforced by module metadata.")])

# ------------------------------------------------- 7 · pilot scope
s = slide()
header(s, "Pilot scope", "Two compiler surfaces · one Cray system first")
for i, (surf, note) in enumerate([
        ("cse/<SystemDefault>", "whatever the machine blesses as its baseline"),
        ("cse/GCC", "the portable reference surface")]):
    x = 0.6 + i * 6.25
    box(s, x, 1.8, 5.9, 2.9, PANEL)
    txt(s, x + 0.25, 1.98, 5.4, 0.5, [(16, INK, True, surf)])
    txt(s, x + 0.25, 2.5, 5.4, 0.4, [(12, MUTED, False, note)])
    boxtxt(s, x + 0.3, 3.0, 2.55, 0.55, TEAL, [(12, WHITE, True, "Core (automatic)")])
    boxtxt(s, x + 3.0, 3.0, 2.55, 0.55, GRAY, [(12, WHITE, True, "Foundation (view)")])
    boxtxt(s, x + 0.3, 3.72, 1.65, 0.62, AMBER, [(12, WHITE, True, "Serial")])
    boxtxt(s, x + 2.1, 3.72, 1.65, 0.62, BLUE, [(12, WHITE, True, "MPI")])
    boxtxt(s, x + 3.9, 3.72, 1.65, 0.62, VIOLET, [(12, WHITE, True, "GPU")])
txt(s, 0.6, 4.95, 12, 0.4, [(13, INK, True, "Representative roster — newest two supported releases")])
roster = ["HDF5", "NetCDF-C", "NetCDF-Fortran", "NetCDF-C++", "FFTW", "OpenBLAS",
          "Boost", "GSL", "TAU", "Dakota", "Kokkos", "Gnuplot", "Python", "Miniforge"]
for i, n in enumerate(roster):
    chip(s, 0.6 + (i % 7) * 1.78, 5.4 + (i // 7) * 0.56, 1.62, n)
txt(s, 0.6, 6.65, 12.1, 0.5, [(12, MUTED, False,
    "Newest-two policy: clean package names · compatible chains load · incompatible mixes fail clearly")])

# ------------------------------------------------- 8 · status / next
s = slide()
header(s, "Status and next steps", "Where the pipeline is today")
box(s, 0.6, 1.8, 5.95, 4.9, PANEL)
txt(s, 0.9, 2.0, 5.4, 0.5, [(17, GREEN, True, "Done")])
done = ["End-to-end Cray smoke: probe → render → concretize → build (PrgEnv-gnu · cray-mpich · ROCm)",
        "Second system validated the generic-Linux path and hardened the prober",
        "Science stack renders clean today: four lanes, two-version roster"]
for i, d in enumerate(done):
    txt(s, 0.9, 2.6 + i * 1.15, 0.4, 0.5, [(16, GREEN, True, "✓")])
    txt(s, 1.35, 2.6 + i * 1.15, 4.95, 1.1, [(13, TEXT, False, d)])
box(s, 6.85, 1.8, 5.85, 4.9, PANEL)
txt(s, 7.15, 2.0, 5.3, 0.5, [(17, AMBER, True, "Next")])
nxt = ["Build the science lanes on the Cray and Linux systems; verify the module/view front door",
       "Encode module compatibility checks for multi-version package chains",
       "Release process: build caches, lockfiles, release manifest"]
for i, d in enumerate(nxt):
    txt(s, 7.15, 2.6 + i * 1.15, 0.4, 0.5, [(16, AMBER, True, "→")])
    txt(s, 7.6, 2.6 + i * 1.15, 4.85, 1.1, [(13, TEXT, False, d)])

# ------------------------------------------------- appendix · build roots
# Tables mirror stack-content/package-sets/{core-foundation,science-full}.yaml
# exactly — every root spec appears. Update both together.

POLICY_FOOTER = ("Version policy: newest supported + immediate predecessor · "
                 "pinned to spack-packages v2026.06.0 (Spack v1.1.1)")


def roster_table(s, y, sections, col_pkg=2.1, col_ver=2.5):
    """One table: lane-colored section divider rows + package rows."""
    x, w = 0.6, 12.13
    nrows = 1 + sum(1 + len(rows) for _, _, rows in sections)
    frame = s.shapes.add_table(nrows, 3, Inches(x), Inches(y), Inches(w),
                               Inches(0.33 * nrows))
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


def appendix_slide(title, sections):
    s = slide()
    header(s, title, "Appendix · exact build roots")
    roster_table(s, 1.62, sections)
    txt(s, 0.6, 7.2, 12.1, 0.28, [(10.5, MUTED, False, POLICY_FOOTER)])
    return s


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
    (GREEN, "Common compiler-dependent packages — loadable from every lane",
     "openblas · netlib-lapack · gnuplot — one Serial-lane build, one install, shared module root"),
    (TEAL, "Core — loads with the compiler surface",
     "cmake · ninja · git · python · py-numpy · miniforge · gsl · sqlite"),
    (GRAY, "Foundation — ambient in the view, never a module",
     "zlib · xz · zstd, single pinned version"),
]
for i, (color, title, body) in enumerate(layers):
    boxtxt(s, 0.6, 3.5 + i * 0.83, 12.13, 0.7, color, [
        (12.5, WHITE, True, title),
        (10.5, WHITE, False, body),
    ])
boxtxt(s, 0.6, 6.02, 12.13, 0.6, WHITE, [
    (13, INK, True, "cse/<Compiler> surface — everything above sits on one compiler"),
    (10.5, MUTED, False, "lanes never mix compilers; loading a second lane fails loudly"),
], line=PANEL2)
txt(s, 0.6, 6.78, 12.1, 0.5, [(11.5, MUTED, False,
    "A user's view is one column: the surface, Foundation, Core, the common packages, "
    "and exactly one payload. The other payloads stay invisible until their lane is loaded.")])

appendix_slide("Core and foundation — built once per compiler surface", [
    ("Foundation — ambient in the lane view, never a module", GRAY, [
        ("zlib",   "1.3.1", "single pinned version (require: pin)"),
        ("xz",     "5.4.6", "single pinned version"),
        ("zstd",   "1.5.6", "single pinned version"),
    ]),
    ("Core tools — user-loadable, compiler-agnostic", TEAL, [
        ("cmake",      "4.3.3 · 4.2.3", ""),
        ("ninja · pkgconf · git", "newest", "unpinned — newest from the recipe generation"),
        ("python",     "3.14.5 · 3.13.13", "the two newest supported minor lines"),
        ("py-numpy",   "2.4.6", "built against each python line (newest non-deprecated recipe)"),
        ("miniforge3", "26.1.1-3", "single by nature — installer for user-managed environments"),
    ]),
    ("Only-serial by nature — no MPI implementation exists", TEAL, [
        ("gsl",    "2.8 · 2.7.1", ""),
        ("sqlite", "3.53.1 · 3.51.2", ""),
    ]),
])

appendix_slide("Serial lane — MPI-capable, deliberately built without MPI", [
    ("Serial data chains — each netcdf rides one named hdf5", AMBER, [
        ("hdf5",           "2.1.0 · 1.14.6", "~mpi +fortran +cxx +hl"),
        ("netcdf-c",       "4.10.0 · 4.9.3", "~mpi — paired to hdf5 2.1.0 / 1.14.6"),
        ("netcdf-fortran", "4.6.2 · 4.6.1",  "rides its paired netcdf-c / hdf5 chain"),
        ("netcdf-cxx4",    "4.3.1", "single recipe version — newest chain only"),
    ]),
    ("Serial math", AMBER, [
        ("fftw",  "3.3.11 · 3.3.10", "~mpi"),
        ("boost", "1.90.0 · 1.89.0", "~mpi here; the MPI lane carries its own +mpi build"),
    ]),
    ("Common compiler-dependent — built here once, available in every lane", GREEN, [
        ("openblas",      "0.3.33 · 0.3.32", "performance-sensitive, so payload rather than core; the BLAS every lane links"),
        ("netlib-lapack", "3.12.1 · 3.12.0", "reference LAPACK alongside openblas (flagged for team review)"),
        ("gnuplot",       "6.0.0 · 5.4.10",  "needs the surface's compiler, so payload rather than core"),
    ]),
])

appendix_slide("MPI and GPU lanes — built against the system MPI", [
    ("MPI data chains — same pairing rule as serial", BLUE, [
        ("hdf5",           "2.1.0 · 1.14.6", "+mpi +fortran +cxx +hl"),
        ("netcdf-c",       "4.10.0 · 4.9.3", "+mpi +parallel-netcdf — paired to hdf5 2.1.0 / 1.14.6"),
        ("netcdf-fortran", "4.6.2 · 4.6.1",  "rides its paired netcdf-c / hdf5 chain"),
        ("netcdf-cxx4",    "4.3.1", "single recipe version — newest chain only"),
    ]),
    ("MPI math and tools", BLUE, [
        ("fftw",   "3.3.11 · 3.3.10", "+mpi"),
        ("boost",  "1.90.0 · 1.89.0", "+mpi; the Serial lane carries its own ~mpi build"),
        ("tau",    "2.35.1 · 2.35",   "+mpi"),
        ("dakota", "6.24.0 · 6.23.0", "+mpi — heaviest build in the roster"),
    ]),
    ("GPU lane — selects the full MPI roster above, plus the GPU payload", VIOLET, [
        ("kokkos", "5.1.1 · 5.1.0",
         "+gpu → expands per lane: +rocm amdgpu_target=<arch> or +cuda cuda_arch=<n>"),
    ]),
    ("Common compiler-dependent — the Serial-lane build, available here too", GREEN, [
        ("common packages", "see Serial",
         "openblas · netlib-lapack · gnuplot: the same modules through the shared root, nothing rebuilt"),
    ]),
    ("Externals — used from the system, never built", GRAY, [
        ("externals", "system",
         "cray-mpich (Platform-backed) · openmpi, openssl (Site-external)"),
    ]),
])

out = Path(__file__).with_name("cse_lanes_model.pptx")
prs.save(str(out))
print("WROTE", out)
