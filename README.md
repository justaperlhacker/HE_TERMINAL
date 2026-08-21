# HE_TERMINAL

Personal terminal font family built from `tt0596m_.ttf` with a fully
scripted pipeline: a hand-tuned dotted zero, synthesized **Bold /
Italic / Bold Italic** faces, and **Nerd Fonts v3** icon patches in both
standard (double-width) and Mono (single-width) flavors.

## Family matrix

| Style       | Plain family (`HE_TERMINAL`) | Nerd family (`HE_TERMINAL Nerd Font`) | Mono Nerd (`HE_TERMINAL Nerd Font Mono`) |
|-------------|------------------------------|---------------------------------------|------------------------------------------|
| Regular     | `tt0596m_.ttf`               | `HE_TERMINALNerdFont-Regular.ttf`     | `HE_TERMINALNFMono-Regular.ttf`          |
| Bold        | `HE_TERMINAL-Bold.ttf`       | `HE_TERMINALNerdFont-Bold.ttf`        | `HE_TERMINALNFMono-Bold.ttf`             |
| Italic      | `HE_TERMINAL-Italic.ttf`     | `HE_TERMINALNerdFont-Italic.ttf`      | `HE_TERMINALNFMono-Italic.ttf`           |
| Bold Italic | `HE_TERMINAL-BoldItalic.ttf` | `HE_TERMINALNerdFont-BoldItalic.ttf`  | `HE_TERMINALNFMono-BoldItalic.ttf`       |

Everything is strictly monospaced at 1233 units/em (0.602 em) per cell,
including icon advances in the Mono builds. The dotted zero survives in
every face.

## Quick start

```sh
make check-deps   # verify toolchain
make install      # build everything -> ~/.fonts/HE_TERMINAL + fc-cache
```

Then point your terminal at one of:

- `HE_TERMINAL` — plain text only, no icon coverage
- `HE_TERMINAL Nerd Font` — full icon set; oversized icons occupy two cells
- `HE_TERMINAL Nerd Font Mono` — same icons squeezed into one cell
  (pick this if your terminal miscounts double-width glyphs)

For example, in kitty (`~/.config/kitty/kitty.conf`):

```conf
font_family      HE_TERMINAL Nerd Font
bold_font        auto
italic_font      auto
bold_italic_font auto
```

or alacritty (`alacritty.toml`):

```toml
[font]
normal = { family = "HE_TERMINAL Nerd Font Mono", style = "Regular" }
italic = { family = "HE_TERMINAL Nerd Font Mono", style = "Italic" }
```

## Usage

Everything is driven by the Makefile; you should never need to run the
Python scripts by hand.

```sh
make              # build all 11 TTFs in place (skips anything up to date)
make install      # build if needed, copy to ~/.fonts/HE_TERMINAL, fc-cache
make preview      # render family_preview.png for a visual check
make clean        # remove generated files (keeps tt0596m_.ttf.orig)
make -n install   # dry run: print what would execute
```

The build is incremental: each output tracks its inputs (source font,
script, patcher), so touching one script only rebuilds the faces that
depend on it. `make install` after a fresh clone does the right thing:
fetches the FontPatcher into `build/`, runs the whole pipeline, installs.

### Customizing

Two knobs are exposed as make variables:

| Variable     | Default | Meaning                                  |
|--------------|---------|------------------------------------------|
| `SLANT`      | 10      | italic slant in degrees                  |
| `BOLD_WIDTH` | 100     | emboldening stroke width in font units   |

```sh
make -B install SLANT=12 BOLD_WIDTH=120
```

Make can't detect that a variable changed, so force a rebuild with `-B`
(or `make clean` first). The italic angle applies to both Italic and
Bold Italic so they always match.

### Committing to a dotfiles repo

`.gitignore` is set up so only sources are tracked:

- **keep**: all `*.py`, `Makefile`, `README.md`, `.gitignore`, and the
  pristine `tt0596m_.ttf.orig`
- **ignored**: every generated TTF, `build/`, previews, stamps

A fresh machine just needs `make check-deps && make install`.

## Dependencies

| Tool              | Arch package            | Used for                          |
|-------------------|-------------------------|-----------------------------------|
| GNU make >= 4.3   | `make`                  | build orchestration               |
| fontforge         | `fontforge`             | Nerd Fonts patcher                |
| Python 3 + fontTools | `python-fonttools`   | outline surgery, name tables      |
| skia-pathops      | `python-skia-pathops`   | true outline emboldening (bold)   |
| git, unzip        | `git`, `unzip`          | fetching the FontPatcher          |
| Pillow (optional) | `python-pillow`         | `make preview` renders            |

## Make targets

| Target             | Effect                                                    |
|--------------------|-----------------------------------------------------------|
| `make`             | build all 11 TTFs                                         |
| `make check-deps`  | fail early if fontforge/fonttools/pathops missing         |
| `make preview`     | render `family_preview.png` (all styles side by side)     |
| `make install`     | copy TTFs to `~/.fonts/HE_TERMINAL`, run `fc-cache -f`    |
| `make clean`       | remove generated files (keeps `tt0596m_.ttf.orig`)        |

## Pipeline

```
tt0596m_.ttf.orig
  └─ patch_zero.py          dotted zero (third contour in 'zero')
      ├─ make_italic.py     10° baseline shear        -> Italic
      ├─ make_bold.py       skia-pathops stroke union -> Bold
      │   └─ make_bolditalic.py                       -> Bold Italic
      └─ (Roman stays as-is)
           └─ nerd-fonts FontPatcher (--complete --careful)
                └─ fix_nf_names.py    underscore back into family names
                     └─ unify_icons.py  identical icon outlines across styles
                          └─ make_mono_variants.py
                               ├─ wide icons -> double-cell advance (NF)
                               └─ wide icons -> scaled into one cell (Mono)
```

Design decisions worth knowing:

- **Stale hinting**: every outline-modifying step drops TrueType glyph
  programs; FreeType falls back to scaled outlines (the original
  hand-tuned hinting corrupts rasterization on modified outlines).
- **Icons at/below U+E0FF** (Powerline/Seti/misc) are designed to bleed
  edge-to-edge in one cell and are never rescaled or widened.
- **Icon unification**: the patcher sizes symbols relative to each
  source font's letterforms, so bold/italic sources would get slightly
  larger icons; `unify_icons.py` copies Regular's icon outlines into the
  other styles so icons match pixel-for-pixel across weights. The ~116
  PUA codepoints native to the original font are exempt (they belong to
  the text and get emboldened/sheared with it).
- **Naming**: family names keep the underscore of the original
  (`HE_TERMINAL Nerd Font`); PostScript names use `HETERMINAL*`
  following Nerd Fonts conventions.
- **No ligatures**: none anywhere, by design.

## Repository layout

```
patch_zero.py           dotted zero (run against .orig)
make_bold.py            synthetic bold via pathops stroke union
make_italic.py          oblique via outline shear
make_bolditalic.py      shear applied to the bold
fix_nf_names.py         restore HE_TERMINAL naming post-patcher
unify_icons.py          cross-style icon consistency
make_mono_variants.py   double-width fixes + NFMono derivation
make_previews.py        render family_preview.png
Makefile                orchestrates everything above (SLANT, BOLD_WIDTH knobs)
.gitignore              generated fonts/build artifacts stay out of git
tt0596m_.ttf.orig       pristine upstream source font -- the one precious file
```

## Notes

- The upstream provenance of `tt0596m_.ttf` is unclear (it has been
  floating around terminal-font circles for years); treat its license
  accordingly before redistributing. All added glyph sets ship under
  their own licenses inside the Nerd Fonts project.
- If your terminal renders the non-Mono Nerd variant with overlapping
  icons, it ignores per-glyph advances — switch to the Mono family.
