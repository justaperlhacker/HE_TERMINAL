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
# The Nerd patcher also drops IEC power symbols below that line
# (U+23FB power, U+23FC on-off, U+23FD on, U+23FE sleep); they are
# full-size symbols, not bleed-designed cell art, so treat them as
# icons wherever icon_glyphs() is used (unify, double-width, mono).
EXTRA_ICON_CPS = frozenset((0x23FB, 0x23FC, 0x23FD, 0x23FE))

STYLES = ["Roman", "Regular", "Medium", "Bold", "RomanItalic", "Italic", "BoldItalic", "MediumItalic"]

STYLE_DISPLAY = {
    "Roman": "Roman",
    "Regular": "Regular",
    "Medium": "Medium",
    "Bold": "Bold",
    "RomanItalic": "Roman Italic",
    "Italic": "Italic",
    "BoldItalic": "Bold Italic",
    "MediumItalic": "Medium Italic",
}


def icon_glyphs(f):
    """Map glyph name -> codepoint for scalable icon glyphs."""
    rev = {}
    for cp, gname in f.getBestCmap().items():
        if cp > ICON_CP_MAX or cp in EXTRA_ICON_CPS:
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


def rescale(gname, glyf, hmtx, glyphSet, s, tx):
    rec = DecomposingRecordingPen(glyphSet)
    glyphSet[gname].draw(rec)
    pen = TTGlyphPen(None)
    rec.replay(TransformPen(pen, Transform(s, 0, 0, s, tx, 0)))
    ng = pen.glyph()
    ng.program = Program()
    ng.program.fromBytecode(b"")
    glyf[gname] = ng
    # Outlines moved: refresh the bearing so no stale lsb shifts a
    # later glyphSet draw (same invariant as the synthesis scripts).
    ng.recalcBounds(glyf)
    hmtx[gname] = (hmtx[gname][0], ng.xMin)


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
        rescale(gname, glyf, hmtx, glyphSet, s, tx)
        hmtx[gname] = (CELL, hmtx[gname][1])
        scaled += 1

    style = src.split("-", 1)[1].rsplit(".", 1)[0]
    display_style = STYLE_DISPLAY.get(style, style)
    ps_suffix = "Mono-" + style
    new_names = {
        1: "HE_TERMINAL Nerd Font Mono",
        2: display_style,
        4: f"HE_TERMINAL Nerd Font Mono {display_style}",
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
