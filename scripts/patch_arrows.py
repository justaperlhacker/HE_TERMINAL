#!/usr/bin/env python3
"""Lift hyphen-minus onto the math axis so typed arrows line up.

The source font hangs the hyphen at y=550 while <, >, = and + all sit
on a math axis of ~730, so "->" and "<-" render as a step (~0.9px at
16pt). This shifts the hyphen up to the operator centerline --
JetBrains Mono / Fira Code convention (hyphen == minus == operator).

Usage: python3 patch_arrows.py [dst] [dy]
Edits [dst] (default tt0596m_.ttf) in place, moving the hyphen up by
[dy] (default 180) font units.
"""
import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program

DST = sys.argv[1] if len(sys.argv) > 1 else "tt0596m_.ttf"
DY = int(sys.argv[2]) if len(sys.argv) > 2 else 180

HYPHEN_MINUS = 0x2D  # the only dash a terminal can type


def main() -> None:
    f = TTFont(DST)
    glyf = f["glyf"]
    cmap = f.getBestCmap()
    name = cmap.get(HYPHEN_MINUS)
    if name is None:
        sys.exit("no hyphen-minus mapping in cmap")
    g = glyf[name]
    if g.isComposite() or g.numberOfContours != 1:
        sys.exit(f"unexpected hyphen geometry: {g.numberOfContours} contours")

    # The hand-tuned TT hinting assumes the old position; executing it
    # on the shifted outline would snap the hyphen back down (or
    # corrupt it). Replace it with an empty program -- FreeType falls
    # back to scaled outlines for this glyph only, same treatment as
    # the dotted-zero patch.
    g.program = Program()
    g.program.fromBytecode(b"")

    coords, _ends, _flags = g.getCoordinates(glyf)
    g.coordinates = GlyphCoordinates([(x, y + DY) for x, y in coords])
    g.recalcBounds(glyf)

    f.save(DST)
    ys = [y for _x, y in coords]
    print(f"moved hyphen up {DY} units in {DST} "
          f"(y {min(ys)}..{max(ys)} -> {min(ys) + DY}..{max(ys) + DY})")


if __name__ == "__main__":
    main()
