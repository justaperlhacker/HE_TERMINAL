#!/usr/bin/env python3
"""Deepen the tilde wave so it survives synthetic emboldening.

The source font draws a shallow tilde: peak-to-trough amplitude is 86
units (4.2% of the 2048-unit em, ~0.67px at 16px). Emboldening is an
isotropic Minkowski dilation -- it adds stroke thickness (+25 Regular,
+50 Medium, +125 Bold stacked on Regular) while the amplitude stays
exactly 86. The thicker the stem, the more the sub-pixel wiggle
disappears into the rasterized bar, so Regular and heavier render `~`
as a straight dash at terminal sizes while thin Roman still shows the
dip (same outlines in plain and Nerd faces -- the patcher never touches
ASCII, both were verified outline-identical per weight).

Usage: python3 patch_tilde.py [dst] [boost]
Edits [dst] (default fonts/HE_TERMINAL-Roman.ttf) in place, moving the
wave extrema apart by [boost] (default 35) font units: peaks up,
valleys down. Only points on the glyph's horizontal-tangent y-lines
move, so end caps flex smoothly, local stroke thickness is unchanged
(top and bottom edges move symmetrically about the glyph center), and
the vertical center stays put (combining-mark positioning safe). Runs
before any synthesis, so every weight/style/Nerd/Mono face inherits
the deeper wave (dilation preserves amplitude downstream).

Amplitude goes 86 -> 156 units (~1.2px at 16px): clearly wavy at
terminal sizes without touching the 150-unit stem thickness shared
with `-`/`=`. Covers U+007E, U+02DC, and U+0303 (same design).

The hand-tuned TT hinting of the touched glyphs assumed the old wave,
so their per-glyph programs are dropped -- FreeType falls back to
scaled outlines for these glyphs only, same treatment as the
dotted-zero, hyphen, and apex patches.
"""

import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program

DST = sys.argv[1] if len(sys.argv) > 1 else "fonts/HE_TERMINAL-Roman.ttf"
BOOST = int(sys.argv[2]) if len(sys.argv) > 2 else 35

B = BOOST  # short alias for the tables below

# Glyph name -> {y-line: dy}. A line is a horizontal tangent of the
# wave (shared by 2+ points: the on-curve extremum plus its controls),
# measured on the pristine source; end-cap points never sit on these
# lines, so caps are left to flex. c1380 (U+0303) shares the outline
# design of tilde (U+02DC).
PATCHES = {
    # U+007E: peaks 748/735 up, dip 662 down, hump 598 up, floor 512 down
    "asciitilde": {748: +B, 735: +B, 662: -B, 598: +B, 512: -B},
    # U+02DC: peak 1524/1499 up, dip 1454 down, hump 1364 up,
    #         valley 1319/1294 down
    "tilde": {1524: +B, 1499: +B, 1454: -B, 1364: +B, 1319: -B, 1294: -B},
    "c1380": {1524: +B, 1499: +B, 1454: -B, 1364: +B, 1319: -B, 1294: -B},
}


def main() -> None:
    f = TTFont(DST)
    glyf = f["glyf"]

    for name, lines in PATCHES.items():
        if name not in glyf.keys():
            print(f"{name}: missing, skipped")
            continue
        g = glyf[name]
        if g.isComposite():
            sys.exit(f"unexpected composite tilde glyph: {name}")
        coords, _ends, _flags = g.getCoordinates(glyf)
        ys = [y for _x, y in coords]
        lo, hi = min(ys), max(ys)
        cy = (lo + hi) / 2

        moved = 0
        for y, dy in lines.items():
            n = sum(1 for _x, py in coords if py == y)
            if n < 2:
                sys.exit(f"{name}: y-line {y} matched {n} points "
                         f"(source geometry changed?), aborting")
            moved += n
        g.coordinates = GlyphCoordinates(
            [(x, y + lines[y]) if y in lines else (x, y) for x, y in coords]
        )
        # Stale hand hints assumed the old wave; drop them so this
        # glyph renders from scaled outlines like zero/hyphen/apex do.
        g.program = Program()
        g.program.fromBytecode(b"")
        g.recalcBounds(glyf)
        nys = [y for _x, y in g.coordinates]
        assert (min(nys) + max(nys)) / 2 == cy, f"{name}: center moved"
        print(f"{name}: deepened {moved} wave points by {BOOST} "
              f"(y {lo}..{hi} -> {min(nys)}..{max(nys)}, program dropped)")

    f.save(DST)


if __name__ == "__main__":
    main()
