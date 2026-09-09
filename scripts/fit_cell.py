#!/usr/bin/env python3
"""Fit over-wide text glyphs inside the monospace advance.

Kitty enforces per-cell bitmap budgets in render_bitmap(): a glyph
whose rasterized bitmap is wider than the cell is cropped (2px over)
or uniformly downscaled (3px+ over) to fit. Our widest caps -- A and
W exceed the 1233-unit advance even in Roman, and emboldening grows
them further (Bold A is 1373 units wide) -- so kitty shrinks them on
screen: the "small A" in ls listings. Flat 2-unit apex seating cannot
fix that; only the ink width matters.

Usage: python3 fit_cell.py
Runs in build/work over the eight plain faces (after all synthesis,
before the Nerd patcher, whose fontforge pass preserves widths).
Every cmap glyph below U+2500 whose ink is wider than its advance is
horizontally scaled about its ink center to TARGET = advance - MARGIN
(24 units, ~1/3px at 28ppem: insurance against hinter/rounding creep).
Ink at or below the advance can only ever rasterize to cell or
cell+1 wide at any size/position, which kitty renders untouched.

Deliberately excluded:
  * U+2500 and above (box drawing, blocks, shades -- they must bleed
    edge-to-edge to tile, and kitty draws most of them itself anyway),
  * U+0300-U+036F (combining marks -- zero-advance overlays whose
    positioning relative to the base must not move).

Scaled outlines invalidate hand-tuned hints, so touched glyphs get an
empty program (same treatment as the zero/hyphen/apex patches);
ttfautohint re-hints the synthesized faces from the final outlines
downstream. Advances stay fixed (monospace sacred); hmtx side
bearings are refreshed to the new ink edges.
"""
import glob

from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program

MARGIN = 24  # units under the advance; insurance vs rounding/hinters
ICON_CP_MIN = 0x2500  # at/above: tiling cell art, never fitted
MARK_LO, MARK_HI = 0x0300, 0x036F  # combining marks, never moved


def needs_fit(cp: int) -> bool:
    if cp >= ICON_CP_MIN:
        return False
    return not (MARK_LO <= cp <= MARK_HI)


def fit_face(path: str) -> int:
    f = TTFont(path)
    glyf = f["glyf"]
    hmtx = f["hmtx"]
    cmap = f.getBestCmap()
    glyphSet = f.getGlyphSet()

    fitted = []
    for cp in sorted(cmap):
        if not needs_fit(cp):
            continue
        name = cmap[cp]
        g = glyf[name]
        if g.isComposite():
            # Decompose via the glyph set so accents scale with base.
            rec = DecomposingRecordingPen(glyphSet)
            try:
                glyphSet[name].draw(rec)
            except Exception:
                continue
            if not rec.value:
                continue
            pen = TTGlyphPen(None)
            rec.replay(pen)
            g = pen.glyph()
            glyf[name] = g
        try:
            coords, _ends, _flags = g.getCoordinates(glyf)
        except Exception:
            continue
        if not coords:
            continue
        xs = [x for x, _y in coords]
        lo, hi = min(xs), max(xs)
        ink = hi - lo
        adv = hmtx[name][0]
        if ink <= adv:
            continue
        target = adv - MARGIN
        s = target / ink
        cx = (lo + hi) / 2
        # x' = cx + (x - cx) * s -- advance untouched, center kept.
        rec = DecomposingRecordingPen(glyphSet)
        glyphSet[name].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, Transform(s, 0, 0, 1, cx * (1 - s), 0)))
        ng = pen.glyph()
        ncoords, nends, nflags = ng.getCoordinates(glyf)
        ng.coordinates = GlyphCoordinates(
            [(int(round(x)), y) for x, y in ncoords]
        )
        ng.program = Program()
        ng.program.fromBytecode(b"")
        glyf[name] = ng
        ng.recalcBounds(glyf)
        hmtx[name] = (adv, ng.xMin)
        fitted.append((name, ink - adv, s))

    if fitted:
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
        f.save(path)

    worst = sorted(fitted, key=lambda t: -t[1])[:8]
    print(f"{path}: fitted {len(fitted)} glyphs"
          + (f" (widest: {', '.join(f'{n}+{d}s={s:.3f}' for n, d, s in worst)})"
             if worst else ""))
    return len(fitted)


def main() -> None:
    total = 0
    for path in sorted(glob.glob("HE_TERMINAL-*.ttf")):
        total += fit_face(path)
    print(f"fitted {total} glyph faces total")


if __name__ == "__main__":
    main()
