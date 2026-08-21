# HE_TERMINAL font family build
#
# Builds the full matrix from one source TTF:
#   plain            : Regular (dotted zero), Bold, Italic, Bold Italic
#   Nerd             : same four styles + full Nerd Fonts v3 glyph sets,
#                      wide icons get double-cell advances
#   NerdFontMono     : wide icons scaled into a single cell
#
# Targets:
#   make            - build every font
#   make check-deps - verify fontforge/fonttools/skia-pathops present
#   make preview    - render family_preview.png (all six rows)
#   make install    - copy TTFs to ~/.fonts/HE_TERMINAL + fc-cache
#   make clean      - remove generated files (keeps tt0596m_.ttf.orig)

PY    ?= python3
FF    ?= fontforge

# customization knobs (changing them requires a rebuild, see README)
SLANT      ?= 10    # italic slant, degrees
BOLD_WIDTH ?= 100   # emboldening stroke, font units (2048/em)

SRC          := tt0596m_.ttf
ORIG         := tt0596m_.ttf.orig
PLAIN_ITALIC := HE_TERMINAL-Italic.ttf
PLAIN_BOLD   := HE_TERMINAL-Bold.ttf
PLAIN_BI     := HE_TERMINAL-BoldItalic.ttf
PLAIN        := $(SRC) $(PLAIN_BOLD) $(PLAIN_ITALIC) $(PLAIN_BI)

STYLES  := Regular Bold Italic BoldItalic
MANGLED := $(STYLES:%=HETERMINALNerdFont-%.ttf)
NF      := $(STYLES:%=HE_TERMINALNerdFont-%.ttf)
MONO    := $(STYLES:%=HE_TERMINALNFMono-%.ttf)

PATCHER := build/font-patcher

.INTERMEDIATE: $(MANGLED)
.PHONY: all install preview check-deps clean

all: $(MONO) $(PLAIN)

check-deps:
	@command -v $(FF) >/dev/null || { echo "missing: fontforge"; exit 1; }
	@$(PY) -c "import fontTools" 2>/dev/null || { echo "missing: fonttools"; exit 1; }
	@$(PY) -c "import pathops"   2>/dev/null || { echo "missing: skia-pathops"; exit 1; }
	@echo "dependencies OK"

# ---- plain faces -----------------------------------------------------------

$(SRC): $(ORIG) patch_zero.py
	$(PY) patch_zero.py

$(PLAIN_BOLD): $(SRC) make_bold.py
	$(PY) make_bold.py $(BOLD_WIDTH)

$(PLAIN_ITALIC): $(SRC) make_italic.py
	$(PY) make_italic.py $(SLANT)

$(PLAIN_BI): $(PLAIN_BOLD) make_bolditalic.py
	$(PY) make_bolditalic.py $(SLANT)

# ---- nerd fonts ------------------------------------------------------------

$(PATCHER):
	git clone --depth 1 --filter=blob:none --sparse \
	    https://github.com/ryanoasis/nerd-fonts.git build/nerd-fonts
	unzip -q -o build/nerd-fonts/FontPatcher.zip -d build

HETERMINALNerdFont-Regular.ttf:    $(SRC)          | $(PATCHER)
HETERMINALNerdFont-Bold.ttf:       $(PLAIN_BOLD)   | $(PATCHER)
HETERMINALNerdFont-Italic.ttf:     $(PLAIN_ITALIC) | $(PATCHER)
HETERMINALNerdFont-BoldItalic.ttf: $(PLAIN_BI)     | $(PATCHER)

HETERMINALNerdFont-%.ttf:
	$(FF) -script $(PATCHER) --complete --careful --no-progressbars $<

# patcher strips underscores -> restore family naming
$(NF): HE_TERMINALNerdFont-%.ttf: HETERMINALNerdFont-%.ttf fix_nf_names.py
	$(PY) fix_nf_names.py $*

# icon outlines unified across styles, then double-width advances fixed
# and the Mono variants derived from the result
.unified: $(NF) unify_icons.py
	$(PY) unify_icons.py
	touch $@

$(MONO) &: .unified make_mono_variants.py
	$(PY) make_mono_variants.py

# ---- extras ----------------------------------------------------------------

preview: family_preview.png

family_preview.png: $(NF) $(MONO) make_previews.py
	$(PY) make_previews.py

install: all
	mkdir -p $(HOME)/.fonts/HE_TERMINAL
	cp HE_TERMINAL*.ttf $(HOME)/.fonts/HE_TERMINAL/
	fc-cache -f $(HOME)/.fonts/HE_TERMINAL >/dev/null
	@echo "installed $(shell ls HE_TERMINAL*.ttf | wc -l) fonts to $(HOME)/.fonts/HE_TERMINAL"

clean:
	rm -f $(PLAIN) $(MANGLED) $(NF) $(MONO) .unified *_preview.png
	rm -rf build
