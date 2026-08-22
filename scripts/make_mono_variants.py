#!/usr/bin/env python3
"""Create NerdFontMono variants of the HE_TERMINAL Nerd Fonts.

Usage: python3 make_mono_variants.py

Cell = 1233 units. Icons in U+E000..U+E0FF are powerline/seti/misc,
designed to bleed edge-to-edge in a single cell -- never touched.
Everything else (FA, octicons, mdi, codicons, weather...) wider than
a cell is proportionally scaled down and centered. Reads the finished
NF files (double-width advances applied by make_nf_wide.py) and writes
only the Mono TTFs, so it never disturbs upstream make stamps.
"""
import os

from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.ttProgram import Program

CELL = 1233
BLEED = 1.02          # tolerate ~25 units of edge bleed before acting
PAD = 0.96            # mono icons are shrunk to 96% of the cell
ICON_CP_MAX = 0xE0FF  # codepoints at/below this are cell-designed glyphs

STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]


def icon_glyphs(f):
    """Map glyph name -> codepoint for scalable icon glyphs."""
    rev = {}
    for cp, gname in f.getBestCmap().items():
        if cp > ICON_CP_MAX:
            rev[gname] = cp
    return rev


def bbox_of(gname, glyf, glyphSet):
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(glyphSet)
    try:
        glyf[gname].draw(bp, glyf)
    except Exception:
        return None
    return bp.bounds


def rescale(gname, glyf, glyphSet, s, tx):
    rec = DecomposingRecordingPen(glyphSet)
    glyphSet[gname].draw(rec)
    pen = TTGlyphPen(None)
    rec.replay(TransformPen(pen, Transform(s, 0, 0, s, tx, 0)))
    ng = pen.glyph()
    ng.program = Program()
    ng.program.fromBytecode(b"")
    glyf[gname] = ng


def make_mono(src, dst):
    """Mono variant: oversized icons scaled to fit one cell."""
    f = TTFont(src)
    glyf, hmtx = f["glyf"], f["hmtx"]
    glyphSet = f.getGlyphSet()
    scaled = 0
    for gname in icon_glyphs(f):
        bb = bbox_of(gname, glyf, glyphSet)
        if not bb:
            continue
        w = bb[2] - bb[0]
        if w <= CELL * BLEED:
            continue
        s = CELL * PAD / w
        tx = CELL / 2 - s * (bb[0] + bb[2]) / 2
        rescale(gname, glyf, glyphSet, s, tx)
        hmtx[gname] = (CELL, hmtx[gname][1])
        scaled += 1

    style = src.split("-", 1)[1].rsplit(".", 1)[0]
    ps_suffix = "Mono-" + style
    new_names = {
        1: "HE_TERMINAL Nerd Font Mono",
        4: f"HE_TERMINAL Nerd Font Mono {style}",
        6: "HE_TERMINALNFMono-" + style,
        16: "HE_TERMINAL Nerd Font Mono",
    }
    for rec in f["name"].names:
        if rec.nameID in new_names:
            rec.string = new_names[rec.nameID]
        elif rec.nameID == 3:
            rec.string = "HE_TERMINAL Nerd Font Mono 3.5.1"

    mp = f["maxp"]
    pts = ctrs = 0
    for gname in glyf.keys():
        gg = glyf[gname]
        if not gg.isComposite():
            coords, ends, _flags = gg.getCoordinates(glyf)
            pts = max(pts, len(coords))
            ctrs = max(ctrs, len(ends))
    mp.maxPoints, mp.maxContours = pts, ctrs
    mp.maxCompositePoints, mp.maxCompositeContours = pts, ctrs

    f.save(dst)
    return scaled


def main() -> None:
    for style in STYLES:
        nf = f"HE_TERMINALNerdFont-{style}.ttf"
        mono = f"HE_TERMINALNFMono-{style}.ttf"
        s = make_mono(nf, mono)
        print(f"{mono} scaled {s} icons")


if __name__ == "__main__":
    main()
