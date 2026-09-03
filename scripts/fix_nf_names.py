#!/usr/bin/env python3
"""Restore HE_TERMINAL naming (underscore preserved) on patcher output.

Usage: python3 fix_nf_names.py <Style>
Reads HETERMINALNerdFont-<Style>.ttf (font-patcher strips underscores),
writes HE_TERMINALNerdFont-<Style>.ttf.
"""
import sys

from fontTools.ttLib import TTFont

STYLE_MAP = {
    "Roman": "Roman",
    "Regular": "Regular",
    "Medium": "Medium",
    "Bold": "Bold",
    "Italic": "Italic",
    "BoldItalic": "Bold Italic",
    "MediumItalic": "Medium Italic",
    "RomanItalic": "Roman Italic",
}


def main() -> None:
    style = sys.argv[1]
    f = TTFont(f"HETERMINALNerdFont-{style}.ttf")
    display_style = STYLE_MAP.get(style, style)
    new = {
        1: "HE_TERMINAL Nerd Font",
        2: display_style,
        4: f"HE_TERMINAL Nerd Font {display_style}",
        6: f"HE_TERMINALNF-{style}",
    }
    keep = [rec for rec in f["name"].names if rec.nameID in new]
    for rec in keep:
        rec.string = new[rec.nameID]
    f["name"].names = keep
    f["name"].names.sort(key=lambda r: (r.platformID, r.platEncID, r.langID, r.nameID))
    f.save(f"HE_TERMINALNerdFont-{style}.ttf")
    print(f"named HE_TERMINALNerdFont-{style}.ttf (style='{display_style}')")


if __name__ == "__main__":
    main()
