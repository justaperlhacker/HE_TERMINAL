#!/usr/bin/env python3
"""Clear tt0596m_'s native PUA icons so Nerd Fonts owns that range.

The pristine source font ships 116 Private Use Area glyphs -- one
contiguous U+F020..U+F093 run of folders, locks, media symbols --
colliding with Font Awesome slots the patcher wants to fill itself.
FontPatcher never overwrites an occupied cmap entry, so without this
step those codepoints keep the source font's own shapes instead of
proper NF icons. Worst offender: U+F07B, whose ink starts 35% into
the cell and sits on the baseline, so superfile's folder icon shows
as a right-hugging sliver while yazi (U+E5FF, not native here) looks
fine. Every one of the 116 is covered by the patcher's symbol sets.

Removes the colliding cmap mappings from every face in the working
directory. Only the mappings go: the source font's metric/post tables
are too quirky to safely drop glyphs through fontTools, so the old
outlines linger as unreferenced orphans until FontPatcher's fontforge
pass rewrites each face. Downstream steps address icons purely via
cmap, and unify_icons.py derives its native-PUA exemption set from
these same pre-patch cmaps -- which this step empties by construction,
so the new icons unify across styles like every other NF glyph.

Usage: python3 clear_native_pua.py
"""
import glob

from fontTools.ttLib import TTFont

# at/below this, glyphs are cell-designed powerline/seti shapes and the
# original font has none -- only the FA-range run above it collides
ICON_CP_MAX = 0xE0FF
PUA_LAST = 0xF8FF


def main() -> None:
    for path in sorted(glob.glob("*.ttf")):
        f = TTFont(path)
        n = 0
        for t in f["cmap"].tables:
            cps = [cp for cp in t.cmap if ICON_CP_MAX < cp <= PUA_LAST]
            for cp in cps:
                del t.cmap[cp]
            n += len(cps)
        if n:
            f.save(path)
            print(f"{path}: cleared {n} native PUA cmap mappings")


if __name__ == "__main__":
    main()
