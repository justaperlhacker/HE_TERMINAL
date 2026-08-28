#!/usr/bin/env python3
"""Create a synthetic Medium companion for HE_TERMINAL.

Usage: python3 make_medium.py [added_stroke_width]
Reads tt0596m_.ttf (dotted zero included), writes HE_TERMINAL-Medium.ttf.

Same Minkowski-dilation emboldening as make_bold.py, just lighter: the
default stroke sits halfway between Regular (~0) and Bold (100, the
BOLD_WIDTH knob), landing in the 500 weight class.
"""
import sys

import pathops
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program

SRC = "tt0596m_.ttf"
DST = "HE_TERMINAL-Medium.ttf"

width = float(sys.argv[1]) if len(sys.argv) > 1 else 50.0


def embolden(glyph_name: str, glyph, glyphSet):
    src = pathops.Path()
    glyphSet[glyph_name].draw(src.getPen(glyphSet))
    if not src.verbs:
        return None
    try:
        src = pathops.simplify(src) or src
    except pathops.PathOpsError:
        pass
    band = pathops.Path()
    band.addPath(src)
    band.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4.0)
    band.convertConicsToQuads()
    out = pathops.Path()
    pathops.union((src, band), out.getPen())
    out.convertConicsToQuads()
    return out


def main() -> None:
    f = TTFont(SRC)
    glyf = f["glyf"]
    glyphSet = f.getGlyphSet()

    failed = []
    for name in list(glyf.keys()):
        try:
            med_path = embolden(name, glyf[name], glyphSet)
        except pathops.PathOpsError:
            failed.append(name)
            continue
        if med_path is None:
            continue
        pen = TTGlyphPen(None)
        med_path.draw(pen)
        ng = pen.glyph()
        ng.program = Program()
        ng.program.fromBytecode(b"")
        glyf[name] = ng

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

    name_tbl = f["name"]
    for rec in name_tbl.names:
        if rec.nameID == 2:
            rec.string = "Medium"
        elif rec.nameID == 4:
            rec.string = "HE_TERMINAL Medium"
        elif rec.nameID == 6:
            rec.string = "HE_TERMINAL-Medium"

    os2 = f["OS/2"]
    os2.usWeightClass = 500
    os2.fsSelection = os2.fsSelection & ~(0x40 | 0x20)  # neither REGULAR nor BOLD
    f["head"].macStyle &= ~0x0001

    f.save(DST)
    print(f"wrote {DST} (+{width:g} units stroke, ~{width / 20.48:.1f}% em)")
    if failed:
        print(f"WARNING: {len(failed)} glyphs failed emboldening (kept regular): "
              f"{failed[:20]}{'...' if len(failed) > 20 else ''}")


if __name__ == "__main__":
    main()