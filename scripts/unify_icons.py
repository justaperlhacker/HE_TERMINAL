#!/usr/bin/env python3
"""Unify icon outlines across the NF style variants.

The patcher scales symbols relative to each source font's measured
letterforms, so Bold/Italic/BoldItalic got slightly larger icons than
Regular (the patcher saw fatter/taller reference letters). This script
copies NF-Regular's icon outlines + metrics into the other styles so
icons are pixel-identical across the family -- except the ~116 PUA
codepoints native to HE_TERMINAL itself, which must stay
style-specific (they are emboldened/sheared with the text).
"""
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.ttProgram import Program

from make_mono_variants import ICON_CP_MAX, icon_glyphs

MASTER = "HE_TERMINALNerdFont-Regular.ttf"
OTHERS = [f"HE_TERMINALNerdFont-{s}.ttf" for s in
          ("Roman", "Medium", "Bold", "RomanItalic", "Italic",
           "BoldItalic", "MediumItalic")]


def main() -> None:
    src = TTFont(MASTER)
    native_cps = {cp for cp in TTFont("HE_TERMINAL-Roman.ttf").getBestCmap()
                  if cp > ICON_CP_MAX}
    shared = set(icon_glyphs(src).values()) - native_cps
    print(f"master icons: {len(icon_glyphs(src))}, "
          f"native PUA kept style-specific: {len(native_cps)}, "
          f"unifying: {len(shared)}")

    for path in OTHERS:
        dst = TTFont(path)
        s_glyf, s_hmtx, s_gs = src["glyf"], src["hmtx"], src.getGlyphSet()
        d_glyf, d_hmtx = dst["glyf"], dst["hmtx"]
        rev = icon_glyphs(dst)
        copied = 0
        for gname, cp in rev.items():
            if cp not in shared or gname not in s_glyf:
                continue
            rec = DecomposingRecordingPen(s_gs)
            s_gs[gname].draw(rec)
            pen = TTGlyphPen(None)
            rec.replay(pen)
            ng = pen.glyph()
            ng.program = Program()
            ng.program.fromBytecode(b"")
            d_glyf[gname] = ng
            d_hmtx[gname] = s_hmtx[gname]
            copied += 1

        mp = dst["maxp"]
        pts = ctrs = 0
        for gn in d_glyf.keys():
            gg = d_glyf[gn]
            if not gg.isComposite():
                coords, ends, _flags = gg.getCoordinates(d_glyf)
                pts = max(pts, len(coords))
                ctrs = max(ctrs, len(ends))
        mp.maxPoints, mp.maxContours = pts, ctrs
        mp.maxCompositePoints, mp.maxCompositeContours = pts, ctrs

        dst.save(path)
        print(f"{path}: unified {copied} icons")


if __name__ == "__main__":
    main()
