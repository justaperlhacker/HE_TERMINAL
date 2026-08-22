#!/usr/bin/env python3
"""Give oversized icons a two-cell advance in the plain NF variants.

Official Nerd Fonts convention: icons wider than one cell (FA, octicons,
mdi, codicons, weather...) get advance 2*CELL instead of overlapping the
following text. Icons at/below U+E0FF are powerline/seti/misc, designed
to bleed edge-to-edge in a single cell and are never touched.

Runs inside the Makefile's .unified step (after unify_icons.py, before
the Mono variants are derived from the result). Files are only rewritten
when something actually changed, keeping the make stamps honest.
"""
from fontTools.ttLib import TTFont

from make_mono_variants import BLEED, CELL, STYLES, bbox_of, icon_glyphs


def main() -> None:
    for style in STYLES:
        path = f"HE_TERMINALNerdFont-{style}.ttf"
        f = TTFont(path)
        glyf, hmtx = f["glyf"], f["hmtx"]
        glyphSet = f.getGlyphSet()
        doubled = 0
        for gname in icon_glyphs(f):
            bb = bbox_of(gname, glyf, glyphSet)
            if bb and (bb[2] - bb[0]) > CELL * BLEED \
                    and hmtx[gname][0] != 2 * CELL:
                hmtx[gname] = (2 * CELL, hmtx[gname][1])
                doubled += 1
        if doubled:
            f.save(path)
        print(f"{path}: double-widthed {doubled} icons")


if __name__ == "__main__":
    main()
