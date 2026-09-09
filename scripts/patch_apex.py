#!/usr/bin/env python3
"""Seat diagonal-apex caps exactly on the flat cap line.

The source font draws the flat tops of A V W X Y two units above the
flat caps (1423 vs 1421 for H I U R D). Optically that is nothing
(~0.02px at terminal sizes), but hinters bucket horizontal edges into
alignment zones: the 2-unit slop leaves the apex tops just outside the
cap zone, so grid-fitting can snap them a pixel below the flat-topped
letters -- the "small A" in kitty (see the ls screenshot: AI/ AUR/).

Usage: python3 patch_apex.py [dst]
Edits [dst] (default fonts/HE_TERMINAL-Roman.ttf) in place, moving
every outline point at the apex line down onto H's cap height. Only
the five apex caps are touched, and only points already at the apex
line (i.e. top edges by construction). Runs before any synthesis, so
every weight/style/Nerd/Mono face inherits the seated tops and
ttfautohint zones them with the flat caps.

The hand-tuned TT hinting of the touched glyphs assumed the old apex
position, so their per-glyph programs are dropped -- FreeType falls
back to scaled outlines for these glyphs only, same treatment as the
dotted-zero and hyphen patches.
"""

import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program

DST = sys.argv[1] if len(sys.argv) > 1 else "fonts/HE_TERMINAL-Roman.ttf"

APEX_GLYPHS = ("A", "V", "W", "X", "Y")
CAP_GLYPH = "H"  # flat cap defining the alignment line


def main() -> None:
    f = TTFont(DST)
    glyf = f["glyf"]

    cap = glyf[CAP_GLYPH]
    cap.recalcBounds(glyf)
    cap_y = cap.yMax

    for name in APEX_GLYPHS:
        g = glyf[name]
        if g.isComposite():
            sys.exit(f"unexpected composite apex glyph: {name}")
        g.recalcBounds(glyf)
        apex_y = g.yMax
        if apex_y <= cap_y:
            print(f"{name}: apex {apex_y} already at/below cap {cap_y}, skipped")
            continue
        coords, _ends, _flags = g.getCoordinates(glyf)
        moved = sum(1 for _x, y in coords if y == apex_y)
        g.coordinates = GlyphCoordinates(
            [(x, cap_y if y == apex_y else y) for x, y in coords]
        )
        # Stale hand hints assumed the old apex; drop them so this
        # glyph renders from scaled outlines like zero/hyphen do.
        g.program = Program()
        g.program.fromBytecode(b"")
        g.recalcBounds(glyf)
        print(f"{name}: seated {moved} apex points "
              f"{apex_y} -> {cap_y} (program dropped)")

    f.save(DST)


if __name__ == "__main__":
    main()
