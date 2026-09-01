#!/usr/bin/env python3
"""Restore HE_TERMINAL naming (underscore preserved) on patcher output.

Usage: python3 fix_nf_names.py <Style>
Reads HETERMINALNerdFont-<Style>.ttf (font-patcher strips underscores),
writes HE_TERMINALNerdFont-<Style>.ttf.
"""
import sys

from fontTools.ttLib import TTFont


def main() -> None:
    style = sys.argv[1]
    f = TTFont(f"HETERMINALNerdFont-{style}.ttf")
    new = {
        1: "HE_TERMINAL Nerd Font",
        2: style,
        4: f"HE_TERMINAL Nerd Font {style}",
        6: f"HE_TERMINALNF-{style}",
    }
    keep = [rec for rec in f["name"].names if rec.nameID in new]
    for rec in keep:
        rec.string = new[rec.nameID]
    f["name"].names = keep
    f["name"].names.sort(key=lambda r: (r.platformID, r.platEncID, r.langID, r.nameID))
    f.save(f"HE_TERMINALNerdFont-{style}.ttf")
    print(f"named HE_TERMINALNerdFont-{style}.ttf")


if __name__ == "__main__":
    main()
