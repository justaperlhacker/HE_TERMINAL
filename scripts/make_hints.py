#!/usr/bin/env python3
"""Bake ttfautohint hints into every synthesized face.

The Roman face (and the plain Roman Italic) keeps the hand-tuned
hinting of HE_TERMINAL-Roman.ttf. All other synthesized faces had
their per-glyph programs stripped during emboldening/shearing, but
the font-wide fpgm/prep/cvt tables still ride along from the source --
tuned to the ORIGINAL outlines they grid-fit the modified ones
differently at raster time (the "small bold A" effect). ttfautohint
replaces those tables wholesale and generates fresh ones matched to
the actual outlines of each face.

Always processes all faces; incremental builds are gated by the
Makefile's .hinted stamp, not by inspecting the TTFs. PUA icon glyphs
are left untouched (no --symbol), and --increase-x-height=0 stops
ttfautohint from nudging x-heights at small sizes so letterforms stay
faithful to the outlines.
"""
import os
import shutil
import subprocess
import tempfile

SYNTHESIZED_STYLES = ("Regular", "Medium", "Bold", "RomanItalic", "Italic", "BoldItalic", "MediumItalic")
NERD_STYLES = ("Roman", "Regular", "Medium", "Bold", "RomanItalic", "Italic", "BoldItalic", "MediumItalic")

FONTS = [f"HE_TERMINAL-{s}.ttf" for s in SYNTHESIZED_STYLES] \
      + [f"HE_TERMINALNerdFont-{s}.ttf" for s in NERD_STYLES] \
      + [f"HE_TERMINALNFMono-{s}.ttf" for s in NERD_STYLES]


def hint(path: str) -> None:
    fd, tmp = tempfile.mkstemp(suffix=".ttf")
    os.close(fd)
    try:
        subprocess.run(
            ["ttfautohint", "--increase-x-height=0", "--no-info", path, tmp],
            check=True,
        )
        shutil.move(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main() -> None:
    for name in FONTS:
        if not os.path.exists(name):
            raise SystemExit(f"missing: {name} (run make first)")
        hint(name)
        print(f"{name}: hinted")


if __name__ == "__main__":
    main()
