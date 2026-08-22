#!/usr/bin/env python3
"""Render previews/family_preview.png comparing all built faces."""
import os

from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ("fonts/HE_TERMINALNerdFont-Regular.ttf",    "NF Regular", "#e5e5e5"),
    ("fonts/HE_TERMINALNerdFont-Bold.ttf",       "NF Bold", "#ff9e3d"),
    ("fonts/HE_TERMINALNerdFont-Italic.ttf",     "NF Italic", "#7dcfff"),
    ("fonts/HE_TERMINALNerdFont-BoldItalic.ttf", "NF BoldItal", "#bb9af7"),
    ("fonts/HE_TERMINALNFMono-Regular.ttf",      "Mono Regul.", "#e5e5e5"),
    ("fonts/HE_TERMINALNFMono-Bold.ttf",         "Mono Bold", "#ff9e3d"),
]

TEXT = "\ue0b6 \uf115 HE_TERMINAL \ue0b0 \ue0a0 main 0123456789 _"


def main() -> None:
    img = Image.new("RGB", (900, 58 * len(ROWS) + 20), (30, 30, 40))
    d = ImageDraw.Draw(img)
    y = 15
    for path, label, color in ROWS:
        fnt = ImageFont.truetype(path, 30)
        d.text((24, y), f"{label:12s}{TEXT}", font=fnt, fill=color)
        y += 58
    os.makedirs("previews", exist_ok=True)
    out = "previews/family_preview.png"
    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
