# HE_TERMINAL font family build
#
# Builds the full matrix from one source TTF:
#   plain            : Roman (dotted zero, weight 300), Regular (400),
#                      Medium (500), Bold (700), plus italics
#   Nerd             : same eight styles + full Nerd Fonts v3 glyph sets,
#                      wide icons get double-cell advances
#   NerdFontMono     : wide icons scaled into a single cell
# Every synthesized face is then hinted with ttfautohint so it
# grid-fits consistently with the hand-hinted Roman.
#
# Layout:
#   src/      pristine source font (+ generated patched master)
#   scripts/  build steps
#   fonts/    built TTFs
#   previews/ rendered comparison images
#   build/    patcher checkout + work staging (not shipped)
#
# Targets:
#   make            - build every font into fonts/
#   make check-deps - verify fontforge/fonttools/skia-pathops present
#   make preview    - render previews/family_preview.png
#   make install    - copy fonts/ TTFs to ~/.fonts/HE_TERMINAL + fc-cache
#   make clean      - remove generated files (keeps src/tt0596m_.ttf.orig)

PY    ?= python3
FF    ?= fontforge

# customization knobs (changing them requires a rebuild, see README)
SLANT         ?= 10    # italic slant, degrees
BOLD_WIDTH    ?= 100   # emboldening stroke, font units (2048/em)
MEDIUM_WIDTH  ?= 50    # Medium stroke: halves Bold's, halfway to Roman
REGULAR_WIDTH ?= 25    # Regular stroke: halves Medium's, halfway to Roman

ORIG := src/tt0596m_.ttf.orig
SRC  := fonts/HE_TERMINAL-Roman.ttf

PATCHER     := build/font-patcher
PATCHERABS  := $(CURDIR)/$(PATCHER)
WORK        := build/work
STAMP       := build/.unified

# The Nerd Font patcher normalizes "Roman" → "Regular" and
# "Roman Italic" → "Italic" in output filenames. We patch
# Roman/RomanItalic first, rename those outputs, then patch
# the rest so they get their correct names.
NF_STYLES = Regular Medium Bold Italic BoldItalic MediumItalic

.PHONY: all install preview check-deps clean

all: $(STAMP)

check-deps:
	@command -v $(FF) >/dev/null || { echo "missing: fontforge"; exit 1; }
	@command -v ttfautohint >/dev/null || { echo "missing: ttfautohint"; exit 1; }
	@$(PY) -c "import fontTools" 2>/dev/null || { echo "missing: fonttools"; exit 1; }
	@$(PY) -c "import pathops"   2>/dev/null || { echo "missing: skia-pathops"; exit 1; }
	@echo "dependencies OK"

# ---- patched master --------------------------------------------------------

$(SRC): $(ORIG) scripts/patch_zero.py scripts/patch_arrows.py
	@mkdir -p fonts
	$(PY) scripts/patch_zero.py 215 $@
	$(PY) scripts/patch_arrows.py $@

# ---- nerd font pipeline ----------------------------------------------------
#
# ALL synthesis runs inside build/work and the shipped TTFs in fonts/
# are written exactly once, by the final copy step of one serialized
# recipe. Upstream stages never see the shipped files, so there is no
# way for a later step to mutate an earlier step's output -- which
# previously made every make run see the whole chain as stale (an mtime
# ping-pong that rebuilt the patcher endlessly).
#
# Any change to a script or knob requires the full chain again; that is
# the price of a DAG that cannot lie. `make clean` resets everything.

$(STAMP): $(SRC) $(wildcard scripts/*.py) | $(PATCHER)
	rm -rf $(WORK) && mkdir -p $(WORK)
	cp $(SRC) $(WORK)/
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_regular.py $(REGULAR_WIDTH)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_medium.py $(MEDIUM_WIDTH)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_bold.py $(BOLD_WIDTH)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_romanitalic.py $(SLANT)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_italic.py $(SLANT)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_bolditalic.py $(SLANT)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_mediumitalic.py $(SLANT)
	cd $(WORK) && $(PY) $(CURDIR)/scripts/clear_native_pua.py
	# Patch Roman first; patcher normalizes style → Regular in output filename
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars HE_TERMINAL-Roman.ttf
	cd $(WORK) && mv HETERMINALRomanNerdFont-Regular.ttf HETERMINALNerdFont-Roman.ttf
	# Patch RomanItalic next; patcher normalizes style → Italic
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars HE_TERMINAL-RomanItalic.ttf
	cd $(WORK) && mv HETERMINALRomanNerdFont-Italic.ttf HETERMINALNerdFont-RomanItalic.ttf
	# Patch remaining styles (no collision now)
	cd $(WORK) && for s in $(NF_STYLES); do \
	    $(FF) -script $(PATCHERABS) --complete --careful \
	        --no-progressbars HE_TERMINAL-$${s}.ttf; done
	cd $(WORK) && for s in Regular Medium Bold Italic BoldItalic MediumItalic Roman RomanItalic; do \
	    $(PY) $(CURDIR)/scripts/fix_nf_names.py $$s; done
	cd $(WORK) && $(PY) $(CURDIR)/scripts/unify_icons.py
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_nf_wide.py
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_mono_variants.py
	cd $(WORK) && $(PY) $(CURDIR)/scripts/make_hints.py
	cp $(WORK)/HE_TERMINAL-Roman.ttf \
	   $(WORK)/HE_TERMINAL-Regular.ttf \
	   $(WORK)/HE_TERMINAL-Medium.ttf \
	   $(WORK)/HE_TERMINAL-Bold.ttf \
	   $(WORK)/HE_TERMINAL-RomanItalic.ttf \
	   $(WORK)/HE_TERMINAL-Italic.ttf \
	   $(WORK)/HE_TERMINAL-BoldItalic.ttf \
	   $(WORK)/HE_TERMINAL-MediumItalic.ttf \
	   $(WORK)/HE_TERMINALNerdFont-*.ttf \
	   $(WORK)/HE_TERMINALNFMono-*.ttf fonts/
	touch $@

# ---- extras ----------------------------------------------------------------

preview: previews/family_preview.png previews/glyphs_preview.png

previews/%.png: $(STAMP) scripts/make_previews.py
	$(PY) scripts/make_previews.py

install: all
	mkdir -p $(HOME)/.fonts/HE_TERMINAL
	cp fonts/*.ttf $(HOME)/.fonts/HE_TERMINAL/
	fc-cache -f $(HOME)/.fonts/HE_TERMINAL >/dev/null
	@echo "installed $(shell ls fonts/*.ttf | wc -l) fonts to $(HOME)/.fonts/HE_TERMINAL"

clean:
	rm -rf build fonts previews

# NOT phony: presence of build/font-patcher is what satisfies the
# order-only prerequisite; cloning again would waste minutes
$(PATCHER):
	git clone --depth 1 --filter=blob:none --sparse \
	    https://github.com/ryanoasis/nerd-fonts.git build/nerd-fonts
	unzip -q -o build/nerd-fonts/FontPatcher.zip -d build
