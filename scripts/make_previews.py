#!/usr/bin/env python3
"""Render previews/family_preview.png and previews/glyphs_preview.png."""
import os

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

BG = (22, 22, 30)
FG = (192, 202, 245)
DIM = (90, 96, 120)
ORANGE = (255, 158, 61)
CYAN = (125, 207, 255)
PURPLE = (187, 154, 247)
GREEN = (158, 206, 106)

PLAIN = "fonts/tt0596m_.ttf"
NF = "fonts/HE_TERMINALNerdFont-Regular.ttf"
NFMONO = "fonts/HE_TERMINALNFMono-Regular.ttf"

PLAIN_TEXT = "ABCDEFabcdef 0123456789 {}[]()<>~^%"
ICON_TEXT = "\ue0b6 \ue0b0 main \ue0a2 2 \uf07b code \uf121 0Oo"

GLYPH_SETS = [
    ("upper ", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ("lower ", "abcdefghijklmnopqrstuvwxyz"),
    ("digit ", "0123456789 |1lI 0Oo"),
    ("punct ", "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"),
    ("lines ", "─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬←↑→↓▲▼"),
]

ICON_CANDIDATES = (
    "\ue0b6\ue0b4\ue0b2\ue0b0 \ue0a0\ue0a1\ue0a2\ue0a3 "
    "\uf07b\uf07c\uf013\uf121\uf108\uf489\uf11c\uf021\uf001\uf185"
)

_cmaps: dict[str, object] = {}


def covered(path: str, text: str) -> str:
    """Drop characters the font has no glyph for (avoids tofu)."""
    if path not in _cmaps:
        _cmaps[path] = TTFont(path).getBestCmap()
    cmap = _cmaps[path]
    return "".join(c for c in text if c == " " or ord(c) in cmap)


def render(rows: list[tuple[str, str, str, str]], out_path: str,
           size: int) -> None:
    """Rows are (font_path, dim_label, sample_text, sample_color)."""
    pad_x, pad_y = 28, 20
    line_h = int(size * 1.75)
    fonts = [(ImageFont.truetype(p, size), lbl, txt, col)
             for p, lbl, txt, col in rows]
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    gap = int(probe.textlength("MM", font=fonts[0][0]))
    width = max(int(probe.textlength(lbl + txt, font=f))
                for f, lbl, txt, _ in fonts) + gap + 2 * pad_x
    img = Image.new("RGB", (width, len(fonts) * line_h + 2 * pad_y), BG)
    draw = ImageDraw.Draw(img)
    y = pad_y
    for f, lbl, txt, col in fonts:
        draw.text((pad_x, y), lbl, font=f, fill=DIM)
        draw.text((pad_x + gap, y), txt, font=f, fill=col)
        y += line_h
    os.makedirs("previews", exist_ok=True)
    img.save(out_path)
    print(f"wrote {out_path} ({width}x{img.height})")


def main() -> None:
    family_rows = [
        (PLAIN, "Regular", PLAIN_TEXT, FG),
        ("fonts/HE_TERMINAL-Bold.ttf", "Bold", PLAIN_TEXT, ORANGE),
        ("fonts/HE_TERMINAL-Italic.ttf", "Italic", PLAIN_TEXT, CYAN),
        ("fonts/HE_TERMINAL-BoldItalic.ttf", "BoldItal", PLAIN_TEXT, PURPLE),
        (NF, "NF", ICON_TEXT, GREEN),
        (NFMONO, "NF Mono", ICON_TEXT, GREEN),
    ]
    render(family_rows, "previews/family_preview.png", size=30)

    glyph_rows = [
        (PLAIN, label, covered(PLAIN, chars), FG if i % 2 == 0 else CYAN)
        for i, (label, chars) in enumerate(GLYPH_SETS)
    ]
    glyph_rows.append((NF, "icons ", covered(NF, ICON_CANDIDATES), GREEN))
    render(glyph_rows, "previews/glyphs_preview.png", size=34)


if __name__ == "__main__":
    main()
