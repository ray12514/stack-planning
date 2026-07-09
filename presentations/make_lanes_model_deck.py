"""Generate the CSE lanes-model stakeholder deck — light theme, designed slides."""
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
boxtxt(s, 7.4, 2.55, 4.75, 0.5, WHITE, [(13, INK, True, "module load cse/gcc")], line=PANEL2)
arrow(s, 9.775, 3.05, 9.775, 3.35, TEAL)
boxtxt(s, 7.4, 3.35, 2.3, 0.62, TEAL, [(12.5, WHITE, True, "Core — automatic")])
boxtxt(s, 9.85, 3.35, 2.3, 0.62, GRAY, [(12.5, WHITE, True, "Foundation — in view")])
arrow(s, 9.775, 3.97, 9.775, 4.27, TEAL)
txt(s, 7.4, 4.27, 4.9, 0.35, [(11.5, MUTED, True, "CHOOSE EXACTLY ONE")], align=PP_ALIGN.CENTER)
boxtxt(s, 7.4, 4.62, 1.5, 0.6, AMBER, [(12.5, WHITE, True, "serial")])
boxtxt(s, 9.0, 4.62, 1.5, 0.6, BLUE, [(12.5, WHITE, True, "mpi")])
boxtxt(s, 10.6, 4.62, 1.55, 0.6, VIOLET, [(12.5, WHITE, True, "gpu")])
txt(s, 7.1, 5.45, 5.4, 1.3, [
    (13.5, TEAL, True, "You see exactly one lane."),
    (12.5, MUTED, False, "No contamination, no accidental MPI/GPU linkage ·"),
    (12.5, MUTED, False, "versions inside a lane stay a one-at-a-time module choice"),
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
lanes = [("serial", AMBER, "hdf5~mpi · fftw~mpi · boost"),
         ("mpi-craympich", BLUE, "hdf5+mpi · netcdf · tau"),
         ("gpu-craympich-gfx942", VIOLET, "kokkos — arch from the probe")]
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
       [(16, INK, True, "$ module load cse/gcc")], line=PANEL2)
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
        ("serial", AMBER, "hdf5~mpi 1.14.6 / 1.14.5 · fftw · boost"),
        ("mpi-craympich", BLUE, "hdf5+mpi · netcdf · tau"),
        ("gpu-craympich-gfx942", VIOLET, "kokkos +rocm gfx942")]):
    x = 0.75 + i * 4.0
    boxtxt(s, x, 4.75, 3.8, 1.0, color,
           [(15, WHITE, True, name), (11.5, WHITE, False, content)])
boxtxt(s, 0.75, 6.1, 11.85, 0.85, PANEL, [
    (13.5, INK, True, "Only the chosen lane is visible — no contamination, no accidental MPI/GPU linkage."),
    (12, MUTED, False, "Two HDF5 versions in a lane? The same one-at-a-time module choice users already know."),
])

# ------------------------------------------------- 6 · lane vocabulary
s = slide()
header(s, "Lane vocabulary", "Names carry facts, not contents")
vocab = [
    ("core", TEAL, "No MPI implementation exists for it, or it is a compiler-agnostic building block.",
     "gsl · python · miniforge · cmake"),
    ("serial", AMBER, "MPI-capable — deliberately built without MPI for users who want it plain.",
     "hdf5~mpi · fftw~mpi"),
    ("mpi-<impl>", BLUE, "Built against the named MPI implementation.",
     "mpi-craympich · mpi-openmpi"),
    ("gpu-<impl>-<arch>", VIOLET, "GPU backend over GPU-aware MPI, targeted at the probed architecture.",
     "gpu-craympich-gfx942"),
]
for i, (name, color, desc, ex) in enumerate(vocab):
    x = 0.6 + i * 3.22
    box(s, x, 1.8, 3.0, 3.55, PANEL)
    box(s, x, 1.8, 3.0, 0.75, color)
    txt(s, x + 0.15, 1.92, 2.7, 0.55, [(17, WHITE, True, name)], align=PP_ALIGN.CENTER)
    txt(s, x + 0.22, 2.75, 2.6, 1.7, [(12.5, TEXT, False, desc)])
    txt(s, x + 0.22, 4.55, 2.6, 0.7, [(11.5, MUTED, False, ex)])
boxtxt(s, 0.6, 5.75, 12.13, 0.62, PANEL2, [(14, INK, True,
    "The GPU lane is called gpu-craympich-gfx942 — never gpu-kokkos. Kokkos is what it carries today.")])

# ------------------------------------------------- 7 · pilot scope
s = slide()
header(s, "Pilot scope", "Two compiler surfaces · one Cray system first")
for i, (surf, note) in enumerate([
        ("cse/<system-default>", "whatever the machine blesses as its baseline"),
        ("cse/gcc", "the portable reference surface")]):
    x = 0.6 + i * 6.25
    box(s, x, 1.8, 5.9, 2.9, PANEL)
    txt(s, x + 0.25, 1.98, 5.4, 0.5, [(16, INK, True, surf)])
    txt(s, x + 0.25, 2.5, 5.4, 0.4, [(12, MUTED, False, note)])
    boxtxt(s, x + 0.3, 3.0, 2.55, 0.55, TEAL, [(12, WHITE, True, "core (automatic)")])
    boxtxt(s, x + 3.0, 3.0, 2.55, 0.55, GRAY, [(12, WHITE, True, "foundation (view)")])
    boxtxt(s, x + 0.3, 3.72, 1.65, 0.62, AMBER, [(12, WHITE, True, "serial")])
    boxtxt(s, x + 2.1, 3.72, 1.65, 0.62, BLUE, [(12, WHITE, True, "mpi")])
    boxtxt(s, x + 3.9, 3.72, 1.65, 0.62, VIOLET, [(12, WHITE, True, "gpu")])
txt(s, 0.6, 4.95, 12, 0.4, [(13, INK, True, "Representative roster — evolving, ~two versions each")])
roster = ["HDF5", "NetCDF-C", "NetCDF-Fortran", "NetCDF-C++", "FFTW", "OpenBLAS",
          "Boost", "GSL", "TAU", "Kokkos", "CMake", "Python", "Miniforge"]
for i, n in enumerate(roster):
    chip(s, 0.6 + (i % 7) * 1.78, 5.4 + (i // 7) * 0.56, 1.62, n)
txt(s, 0.6, 6.65, 12.1, 0.5, [(12, MUTED, False,
    "Multi-version by policy: unify:false lanes · single-version pinned foundation · conflicts stay a module choice")])

# ------------------------------------------------- 8 · status / next
s = slide()
header(s, "Status and next steps", "Where the pipeline is today")
box(s, 0.6, 1.8, 5.95, 4.9, PANEL)
txt(s, 0.9, 2.0, 5.4, 0.5, [(17, GREEN, True, "Done")])
done = ["End-to-end Cray smoke: probe → render → concretize → build (PrgEnv-gnu · cray-mpich · ROCm)",
        "Second system validated the generic-Linux path and hardened the prober",
        "Science stack — four lanes, two-version roster — renders clean today"]
for i, d in enumerate(done):
    txt(s, 0.9, 2.6 + i * 1.15, 0.4, 0.5, [(16, GREEN, True, "✓")])
    txt(s, 1.35, 2.6 + i * 1.15, 4.95, 1.1, [(13, TEXT, False, d)])
box(s, 6.85, 1.8, 5.85, 4.9, PANEL)
txt(s, 7.15, 2.0, 5.3, 0.5, [(17, AMBER, True, "Next")])
nxt = ["Build the science lanes on the Cray system; verify the module/view front door",
       "Add the second compiler surface, then the NVIDIA system in parallel",
       "Release process: build caches, lockfiles, release manifest"]
for i, d in enumerate(nxt):
    txt(s, 7.15, 2.6 + i * 1.15, 0.4, 0.5, [(16, AMBER, True, "→")])
    txt(s, 7.6, 2.6 + i * 1.15, 4.85, 1.1, [(13, TEXT, False, d)])

out = "/private/tmp/claude-501/-Users-ravonventers-Development-stack-composer/a23f38af-bedd-4b94-9c54-985d109b5350/scratchpad/cse_lanes_model.pptx"
prs.save(out)
print("WROTE", out)
