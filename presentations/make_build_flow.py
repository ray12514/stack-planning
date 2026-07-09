"""CSE build-flow schematic, redrawn: light theme, two pilot surfaces, clean flow."""
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BG = RGBColor(0xFF, 0xFF, 0xFF)
PANEL = RGBColor(0xF1, 0xF5, 0xF9)     # slate-100
PANEL2 = RGBColor(0xE2, 0xE8, 0xF0)    # slate-200
INK = RGBColor(0x0F, 0x17, 0x2A)       # slate-900
MUTED = RGBColor(0x64, 0x74, 0x8B)     # slate-500
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEAL = RGBColor(0x0D, 0x94, 0x88)      # core (slightly deepened for white bg)
AMBER = RGBColor(0xD9, 0x77, 0x06)     # serial
BLUE = RGBColor(0x25, 0x63, 0xEB)      # mpi
VIOLET = RGBColor(0x7C, 0x3A, 0xED)    # gpu
GRAY = RGBColor(0x47, 0x55, 0x69)      # foundation

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


def box(s, x, y, w, h, fill, line=None, lw=1.25):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
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
    tf.margin_left = tf.margin_right = Inches(0.08)
    first = True
    for sz, col, bd, t in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = t; p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(sz); p.font.color.rgb = col; p.font.bold = bd
        p.font.name = "Avenir Next"
    return shp


def arrow(s, x1, y1, x2, y2, color=MUTED, w=2.0, dashed=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                               Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    c.shadow.inherit = False
    ln = c.line._get_or_add_ln()
    if dashed:
        d = etree.SubElement(ln, qn('a:prstDash')); d.set('val', 'dash')
    tail = etree.SubElement(ln, qn('a:tailEnd'))
    tail.set('type', 'triangle'); tail.set('w', 'med'); tail.set('len', 'med')
    return c


def build_flow(system, surfaces, mpi_note, lanes_for):
    s = slide()
    txt(s, 0.6, 0.25, 12, 0.35, [(12, TEAL, True, "CSE BUILD FLOW · PILOT")])
    txt(s, 0.6, 0.55, 9.5, 0.65, [(26, INK, True, system)])
    box(s, 0.62, 1.22, 1.5, 0.045, TEAL)
    txt(s, 7.4, 0.62, 5.3, 0.6, [(11.5, MUTED, False, mpi_note)],
        align=PP_ALIGN.RIGHT)

    # pipeline
    stages = [("PROBE", "cluster-inspector\nreads the system"),
              ("POLICY", "one small site\ndefaults file"),
              ("RENDER", "stack-composer\nemits every lane"),
              ("BUILD", "Spack · lanes build\nin parallel"),
              ("VALIDATE", "tests · benchmarks\nsmoke runs"),
              ("PUBLISH", "modules · views\nbuild caches")]
    for i, (t, d) in enumerate(stages):
        x = 0.6 + i * 2.12
        boxtxt(s, x, 1.5, 1.95, 0.92, PANEL,
               [(13, INK, True, t)] + [(9.5, MUTED, False, ln) for ln in d.split("\n")],
               line=PANEL2)
        if i < 5:
            arrow(s, x + 1.96, 1.96, x + 2.11, 1.96, TEAL)

    arrow(s, 6.666, 2.42, 6.666, 2.72, TEAL)

    # core + foundation, built once
    boxtxt(s, 2.37, 2.72, 8.6, 0.9, WHITE, [
        (13.5, INK, True, "Core + Foundation — built once per surface · portable target (x86_64_v3)"),
        (10.5, MUTED, False, "core: cmake · ninja · git · python · miniforge · gsl     foundation: zlib · xz · zstd (single pinned version, ambient in the view)"),
    ], line=TEAL, )

    # reuse edges into the two surfaces
    arrow(s, 4.7, 3.62, 3.7, 4.02, GRAY, dashed=True)
    arrow(s, 8.63, 3.62, 9.63, 4.02, GRAY, dashed=True)

    # two compiler surfaces
    for i, (surf, sub) in enumerate(surfaces):
        x = 0.9 + i * 5.95
        box(s, x, 4.02, 5.55, 2.0, PANEL, line=PANEL2)
        txt(s, x + 0.22, 4.14, 5.1, 0.42, [(14.5, INK, True, surf)])
        txt(s, x + 0.22, 4.56, 5.1, 0.34, [(10.5, MUTED, False, sub)])
        for j, (name, color) in enumerate(lanes_for):
            lx = x + 0.18 + j * 1.82
            boxtxt(s, lx, 5.02, 1.72, 0.78, color,
                   [(11, WHITE, True, name.split("\n")[0])] +
                   ([(9, WHITE, False, name.split("\n")[1])] if "\n" in name else []))

    # bottom: user flow + legend
    boxtxt(s, 0.9, 6.35, 8.7, 0.68, PANEL, [
        (11.5, INK, True, "User:  module load cse/<compiler>  →  core loads · foundation in the view  →  choose exactly one lane"),
    ])
    txt(s, 9.9, 6.38, 2.9, 0.7, [
        (10, MUTED, False, "——  build flow"),
        (10, MUTED, False, "- - -  reuse (built once)"),
    ])
    return s


build_flow(
    "Cray system  ·  Blueback",
    [("cse/gcc", "PrgEnv-gnu — system default surface"),
     ("cse/cce", "PrgEnv-cray — vendor compiler surface")],
    "Cray MPICH is the primary production MPI on Cray systems.",
    [("serial", AMBER), ("mpi-\ncraympich", BLUE), ("gpu-craympich\ngfx942", VIOLET)],
)

build_flow(
    "Generic Linux system  ·  Raider",
    [("cse/gcc", "site GCC — reference surface"),
     ("cse/<system-default>", "the machine's blessed baseline")],
    "Open MPI on InfiniBand/Slingshot fabrics · newest site version by policy.",
    [("serial", AMBER), ("mpi-\nopenmpi", BLUE), ("gpu-openmpi\nsm_80", VIOLET)],
)

out = "/private/tmp/claude-501/-Users-ravonventers-Development-stack-composer/a23f38af-bedd-4b94-9c54-985d109b5350/scratchpad/cse_build_flow.pptx"
prs.save(out)
print("WROTE", out)
