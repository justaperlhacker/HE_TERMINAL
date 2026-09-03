#!/usr/bin/env python3
"""Add a Hack-style dotted zero to HE_TERMINAL.

Usage: python3 patch_zero.py [radius] [dst]
Reads src/tt0596m_.ttf.orig, writes tt0596m_.ttf (or [dst]).
"""
import math
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

SRC = "src/tt0596m_.ttf.orig"
DST = sys.argv[2] if len(sys.argv) > 2 else "tt0596m_.ttf"

# center of the zero's inner counter, measured from outlines
CX, CY = 615, 694

radius = int(sys.argv[1]) if len(sys.argv) > 1 else 215


def main() -> None:
    f = TTFont(SRC)
    glyf = f["glyf"]
    g = glyf["zero"]
    # The font's hand-tuned TT hinting assumes the original two contours;
    # executing it on a three-contour glyph corrupts rasterization
    # (stretched bitmaps, filled bottoms). Drop it -- FreeType falls back
    # to scaled outlines for this glyph only.
    g.program = None

    # quadratic quarter-circle control-point offset
    c = radius * (4 - math.sqrt(2)) / 2
    d = c / math.sqrt(2)

    pen = TTGlyphPen(None)
    g.draw(pen, glyf)
    # Wind the dot the SAME direction as the font's counter contour
    # (this font's counter is CW/negative-area -- nonstandard). Opposite
    # winding would cancel the counter under the nonzero fill rule and
    # render as a second hole instead of ink.
    pen.moveTo((CX + radius, CY))
    pen.qCurveTo((CX + d, CY - d), (CX, CY - radius))
    pen.qCurveTo((CX - d, CY - d), (CX - radius, CY))
    pen.qCurveTo((CX - d, CY + d), (CX, CY + radius))
    pen.qCurveTo((CX + d, CY + d), (CX + radius, CY))
    pen.closePath()
    ng = pen.glyph()
    glyf["zero"] = ng

    mp = f["maxp"]
    pts = ctrs = cpts = cctrs = 0
    for name in glyf.keys():
        gg = glyf[name]
        if gg.isComposite():
            cpts = max(cpts, sum(1 for _ in gg.components))
            cctrs += 1
        else:
            coords, ends, _flags = gg.getCoordinates(glyf)
            pts = max(pts, len(coords))
            ctrs = max(ctrs, len(ends))
    mp.maxPoints, mp.maxContours = pts, ctrs
    mp.maxCompositePoints, mp.maxCompositeContours = max(cpts, pts), max(cctrs, ctrs)

    name_tbl = f["name"]
    for rec in name_tbl.names:
        if rec.nameID == 2:
            rec.string = "Roman"
        elif rec.nameID == 4:
            rec.string = "HE_TERMINAL Roman"
        elif rec.nameID == 6:
            rec.string = "HE_TERMINAL-Roman"
        elif rec.nameID == 16:
            rec.string = "HE_TERMINAL"
        elif rec.nameID == 17:
            rec.string = "Roman"

    os2 = f["OS/2"]
    os2.usWeightClass = 300
    os2.fsSelection = os2.fsSelection & ~0x40  # REGULAR off
    f["head"].macStyle &= ~0x0001

    f.save(DST)
    print(f"wrote {DST} with dot radius {radius} "
          f"(~{2 * radius * 12 / 2048:.1f}px at 12pt)")


if __name__ == "__main__":
    main()
