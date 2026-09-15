#!/usr/bin/env python3
"""Re-cut the dot gaps of ! ? ¿ that emboldening fuses shut.

Minkowski dilation grows every outline by width/2 per side, so the
bar-to-dot white gap shrinks by the full stroke width at each step:
Roman 119 -> Regular 94 -> Medium 69 -> Bold <= 0. In Bold the dot
fuses with the stem (! and ¿ become one contour; ? keeps only a
5-unit pinhole counter), and even Regular/Medium gaps are sub-pixel
at terminal sizes -- `!` reads as a solid bar at 12pt. Hinting is not
involved: the Bold outlines are genuinely connected pre-hint.

Usage: python3 fix_gaps.py
Runs in build/work over the eight plain faces (after all synthesis
including the obliques, before the Nerd patcher whose fontforge pass
preserves ASCII outlines, and before ttfautohint re-hints from the
final outlines). For exclam/question/questiondown it measures the
white gap between the dot island and the body island (hole counters
filtered by nesting, so a pinhole counts as fused) and, when fused or
below TRIGGER, subtracts a full-width horizontal band centered on the
Roman reference gap midpoint. The band height is tiered: faces whose
outline gap is already sub-pixel pre-hint (Medium 69, Bold fused --
the hinter's stem snap would close a Roman-sized gap entirely at
terminal sizes, verified at 12-16px) get RESULT_DEEP; the rest get
RESULT. Faces already at/above TRIGGER (Roman, RomanItalic) are left
untouched, keeping the hand-hinted Roman pristine. Advances stay fixed (monospace sacred);
carving only removes ink, so the fit_cell invariant is preserved.

Cutting rather than shifting keeps both dot and stem at their
emboldened sizes and positions; the severed edges come out flat,
matching the dilated stroke ends.
"""
import glob

import pathops
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program

GLYPHS = ("exclam", "question", "questiondown")
REFERENCE = "HE_TERMINAL-Roman.ttf"
TRIGGER = 115  # carve when the white gap drops below this (Roman: 119)
RESULT = 120       # carved band height for Regular-class faces (pre-carve gap 94)
RESULT_DEEP = 160  # carved band height for Medium/Bold-class faces ...
DEEP_BELOW = 80    # ... whose outline gap is already sub-pixel (Medium 69, Bold fused)
XPAD = 64      # rect overshoot past the ink edges


def contour_boxes(g, glyf):
    coords, ends, _flags = g.getCoordinates(glyf)
    boxes = []
    start = 0
    for end in ends:
        pts = coords[start:end + 1]
        xs = [x for x, _y in pts]
        ys = [y for _x, y in pts]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
        start = end + 1
    return boxes


def islands(boxes):
    """Drop hole counters (boxes nested inside another box)."""
    out = []
    for i, a in enumerate(boxes):
        if any(j != i and b[0] <= a[0] and b[1] <= a[1]
               and b[2] >= a[2] and b[3] >= a[3]
               for j, b in enumerate(boxes)):
            continue
        out.append(a)
    return sorted(out, key=lambda b: b[1])


def gap_of(name, glyf):
    """White gap between dot and body islands; -1 when fused."""
    g = glyf[name]
    if g.isComposite():
        return -1
    try:
        isles = islands(contour_boxes(g, glyf))
    except Exception:
        return -1
    if len(isles) != 2:
        return -1
    lo, hi = isles
    if hi[1] < lo[3]:
        return -1
    return hi[1] - lo[3]


def reference_centers():
    f = TTFont(REFERENCE)
    glyf = f["glyf"]
    centers = {}
    for name in GLYPHS:
        isles = islands(contour_boxes(glyf[name], glyf))
        assert len(isles) == 2, f"{REFERENCE} {name}: expected 2 islands"
        lo, hi = isles
        assert hi[1] >= lo[3], f"{REFERENCE} {name}: reference fused?"
        centers[name] = (lo[3] + hi[1]) // 2
    return centers


def carve(face, name, center, height):
    glyf, hmtx, glyphSet = face["glyf"], face["hmtx"], face.getGlyphSet()
    src = pathops.Path()
    glyphSet[name].draw(src.getPen(glyphSet))
    if not src.verbs:
        return False
    xs = [p[0] for p in src.points]
    lo, hi = center - height // 2, center + height // 2
    rect = pathops.Path()
    rect.moveTo(min(xs) - XPAD, lo)
    rect.lineTo(max(xs) + XPAD, lo)
    rect.lineTo(max(xs) + XPAD, hi)
    rect.lineTo(min(xs) - XPAD, hi)
    rect.close()
    out = pathops.Path()
    pathops.difference([src], [rect], out.getPen())
    if not out.verbs or not out.contours:
        print(f"  {name}: cut emptied the outline, skipped")
        return False
    pen = TTGlyphPen(None)
    out.draw(pen)
    ng = pen.glyph()
    ng.program = Program()
    ng.program.fromBytecode(b"")
    glyf[name] = ng
    ng.recalcBounds(glyf)
    hmtx[name] = (hmtx[name][0], ng.xMin)
    return True


def fix_face(path, centers):
    f = TTFont(path)
    glyf = f["glyf"]
    recut = []
    for name in GLYPHS:
        if name not in glyf.keys():
            continue
        gap = gap_of(name, glyf)
        if gap >= TRIGGER:
            continue
        height = RESULT_DEEP if gap <= DEEP_BELOW else RESULT
        if carve(f, name, centers[name], height):
            recut.append((name, gap, height))
    if not recut:
        print(f"{path}: gaps OK")
        return 0
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
    print(f"{path}: recut {len(recut)} gaps "
          f"({', '.join(f'{n} {g}->{h}' for n, g, h in recut)})")
    return len(recut)


def main() -> None:
    centers = reference_centers()
    print("reference gap centers: "
          + ", ".join(f"{n} {c}" for n, c in centers.items()))
    total = 0
    for path in sorted(glob.glob("HE_TERMINAL-*.ttf")):
        total += fix_face(path, centers)
    print(f"recut {total} gaps total")


if __name__ == "__main__":
    main()
