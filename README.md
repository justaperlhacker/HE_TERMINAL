# HE_TERMINAL

Personal terminal font family built from `src/tt0596m_.ttf.orig` with a
fully scripted pipeline: a hand-tuned dotted zero, synthesized **Bold /
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
make              # build all 12 TTFs into fonts/
make install      # build if needed, copy to ~/.fonts/HE_TERMINAL, fc-cache
make preview      # render previews/family_preview.png for a visual check
make clean        # remove build/, fonts/, previews/ (keeps src/)
make -n install   # dry run: print what would execute
```

The build is incremental: the whole post-patcher pipeline tracks one
stamp, so touching any script rebuilds the chain from staging (the
patcher checkout in `build/` is reused). `make install` after a fresh
clone does the right thing: fetches the FontPatcher into `build/`,
runs the whole pipeline, installs.

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

- **keep**: `scripts/*.py`, `Makefile`, `README.md`, `.gitignore`, and
  the pristine `src/tt0596m_.ttf.orig`
- **ignored**: `fonts/`, `previews/`, `build/` (all generated)

A fresh machine just needs `make check-deps && make install`.

## Dependencies

| Tool              | Arch package            | Used for                          |
|-------------------|-------------------------|-----------------------------------|
| GNU make >= 4.3   | `make`                  | build orchestration               |
| fontforge         | `fontforge`             | Nerd Fonts patcher                |
| Python 3 + fontTools | `python-fonttools`   | outline surgery, name tables      |
| skia-pathops      | `python-skia-pathops`   | true outline emboldening (bold)   |

Note: if the system Python lacks `skia-pathops` (e.g. after an Arch
Python bump), build under a venv instead of changing the Makefile:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install skia-pathops
make PY=$PWD/.venv/bin/python
```
| ttfautohint       | `ttfautohint` / AUR     | hints for synthesized faces       |
| git, unzip        | `git`, `unzip`          | fetching the FontPatcher          |
| Pillow (optional) | `python-pillow`         | `make preview` renders            |

## Make targets

| Target             | Effect                                                    |
|--------------------|-----------------------------------------------------------|
| `make`             | build all 12 TTFs into `fonts/`                           |
| `make check-deps`  | fail early if fontforge/fonttools/pathops/ttfautohint missing |
| `make preview`     | render `previews/family_preview.png` (all styles side by side) |
| `make install`     | copy TTFs to `~/.fonts/HE_TERMINAL`, run `fc-cache -f`    |
| `make clean`       | remove `build/`, `fonts/`, `previews/`                    |

## Pipeline

```
tt0596m_.ttf.orig
  └─ patch_zero.py          dotted zero (third contour in 'zero')
      ├─ make_italic.py     10° baseline shear        -> Italic
      ├─ make_bold.py       skia-pathops stroke union -> Bold
      │   └─ make_bolditalic.py                       -> Bold Italic
      └─ (Roman stays as-is)
           └─ clear_native_pua.py  drop the source font's own PUA icons
                                   so FontPatcher can fill those slots
            └─ nerd-fonts FontPatcher (--complete --careful)
                └─ fix_nf_names.py    underscore back into family names
                      └─ unify_icons.py  identical icon outlines across styles
                           └─ make_nf_wide.py  wide icons -> 2-cell advance (NF)
                                └─ make_mono_variants.py  wide icons scaled
                                   into one cell (NerdFontMono variants)
                                     └─ make_hints.py  ttfautohint on every
                                        face except the hand-hinted Regulars
```

Design decisions worth knowing:

- **Stale hinting**: every outline-modifying step drops TrueType glyph
  programs (the original hand-tuned hinting corrupts rasterization on
  modified outlines). `make_hints.py` bakes fresh ttfautohint hints
  into every non-Regular face so the family behaves like a normal
  hinted font elsewhere. Caveat found in testing: with vertical
  grid-fitting active, terminals can still snap diagonal glyph tops
  (the A apex) one pixel below flat-topped letters on synthesized
  faces; forcing `hintstyle=hintnone` for the `HE_TERMINAL*` families
  via fontconfig renders all faces from raw outlines instead.
- **Icons at/below U+E0FF** (Powerline/Seti/misc) are designed to bleed
  edge-to-edge in one cell and are never rescaled or widened.
- **Native PUA cleared before patching**: the source font ships 116 of
  its own Private Use Area glyphs (U+F020–F093, Font Awesome range).
  The Nerd Fonts patcher never overwrites an occupied codepoint, so
  without `clear_native_pua.py` those slots would keep the original
  font's oddly placed shapes (e.g. a folder icon hugging the right
  cell edge), which apps like superfile render as broken or missing
  icons. All 116 are covered by the patcher's symbol sets, so their
  mappings are dropped pre-patch and proper NF outlines land there.
- **Icon unification**: the patcher sizes symbols relative to each
  source font's letterforms, so bold/italic sources would get slightly
  larger icons; `unify_icons.py` copies Regular's icon outlines into
  the other styles so icons match pixel-for-pixel across weights.
- **Naming**: family names keep the underscore of the original
  (`HE_TERMINAL Nerd Font`); PostScript names use `HETERMINAL*`
  following Nerd Fonts conventions.
- **No ligatures**: none anywhere, by design.

## Repository layout

```
Makefile                 orchestrates everything (SLANT, BOLD_WIDTH knobs)
src/
  tt0596m_.ttf.orig      pristine upstream source font -- the one precious file
scripts/
  patch_zero.py          dotted zero (run against the .orig)
  make_bold.py           synthetic bold via pathops stroke union
  make_italic.py         oblique via outline shear
  make_bolditalic.py     shear applied to the bold
  clear_native_pua.py    drop source-font PUA icons colliding with NF
  fix_nf_names.py        restore HE_TERMINAL naming post-patcher
  unify_icons.py         cross-style icon consistency
  make_nf_wide.py        double-cell advances for oversized icons
  make_mono_variants.py  NFMono derivation from the NF builds
  make_hints.py          ttfautohint for all synthesized faces
  make_previews.py       render previews/family_preview.png
fonts/                   built TTFs (generated)
previews/                rendered comparisons (generated)
build/                   FontPatcher checkout + work staging (generated)
```

## Notes

- The upstream provenance of `tt0596m_.ttf` is unclear (it has been
  floating around terminal-font circles for years); treat its license
  accordingly before redistributing. All added glyph sets ship under
  their own licenses inside the Nerd Fonts project.
- If your terminal renders the non-Mono Nerd variant with overlapping
  icons, it ignores per-glyph advances — switch to the Mono family.
