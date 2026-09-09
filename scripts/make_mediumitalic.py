#!/usr/bin/env python3
"""Create a Medium Italic companion for HE_TERMINAL.

Usage: python3 make_mediumitalic.py [slant_degrees]
Reads HE_TERMINAL-Medium.ttf, writes HE_TERMINAL-MediumItalic.ttf.
Same shear as make_italic.py and make_bolditalic.py so every oblique
face leans identically; stroke stays at the Medium width (500).
"""
import math
import sys

from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.ttProgram import Program

SRC = "HE_TERMINAL-Medium.ttf"
DST = "HE_TERMINAL-MediumItalic.ttf"

angle = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
k = math.tan(math.radians(angle))


def main() -> None:
    f = TTFont(SRC)
    glyf = f["glyf"]

    # x' = x + k*y: top leans right, baseline pinned at y=0.
    shear = Transform(1, 0, k, 1, 0, 0)
    glyphSet = f.getGlyphSet()
    for name in list(glyf.keys()):
        rec = DecomposingRecordingPen(glyphSet)
        glyphSet[name].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, shear))
        ng = pen.glyph()
        ng.program = Program()  # outlines changed; hinting is stale anyway
        ng.program.fromBytecode(b"")
        glyf[name] = ng

    mp = f["maxp"]
    hmtx = f["hmtx"]
    pts = ctrs = 0
    for gname in glyf.keys():
        gg = glyf[gname]
        if not gg.isComposite():
            coords, ends, _flags = gg.getCoordinates(glyf)
            pts = max(pts, len(coords))
            ctrs = max(ctrs, len(ends))
            if coords:
                # Outlines moved but hmtx still holds the source
                # bearings; a stale lsb shifts the next script's
                # glyphSet draws (offset by lsb - xMin), compounding
                # at every stage -- refresh it while we are here.
                gg.recalcBounds(glyf)
                hmtx[gname] = (hmtx[gname][0], gg.xMin)
    mp.maxPoints, mp.maxContours = pts, ctrs
    mp.maxCompositePoints, mp.maxCompositeContours = pts, ctrs

    name_tbl = f["name"]
    for rec in name_tbl.names:
        if rec.nameID == 2:
            rec.string = "Medium Italic"
        elif rec.nameID == 4:
            rec.string = "HE_TERMINAL Medium Italic"
        elif rec.nameID == 6:
            rec.string = "HE_TERMINAL-MediumItalic"
        elif rec.nameID == 16:
            rec.string = "HE_TERMINAL"
        elif rec.nameID == 17:
            rec.string = "Medium Italic"

    os2 = f["OS/2"]
    os2.usWeightClass = 500
    os2.fsSelection = (os2.fsSelection & ~(0x40 | 0x20)) | 0x01  # REGULAR/BOLD off; ITALIC on
    f["head"].macStyle |= 0x0002

    f.save(DST)
    print(f"wrote {DST} ({angle:.1f} deg slant on medium)")


if __name__ == "__main__":
    main()