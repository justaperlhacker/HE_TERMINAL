# HE_TERMINAL font family build
#
# Builds the full matrix from one source TTF:
#   plain            : Regular (dotted zero), Bold, Italic, Bold Italic
#   Nerd             : same four styles + full Nerd Fonts v3 glyph sets,
#                      wide icons get double-cell advances
#   NerdFontMono     : wide icons scaled into a single cell
# Every non-Regular face is then hinted with ttfautohint so it
# grid-fits consistently with the hand-hinted Regular.
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

.PHONY: all install preview check-deps clean

all: .unified

check-deps:
	@command -v $(FF) >/dev/null || { echo "missing: fontforge"; exit 1; }
	@command -v ttfautohint >/dev/null || { echo "missing: ttfautohint"; exit 1; }
	@$(PY) -c "import fontTools" 2>/dev/null || { echo "missing: fonttools"; exit 1; }
	@$(PY) -c "import pathops"   2>/dev/null || { echo "missing: skia-pathops"; exit 1; }
	@echo "dependencies OK"

# ---- plain faces -----------------------------------------------------------

$(SRC): $(ORIG) patch_zero.py
	$(PY) patch_zero.py

# ---- nerd font pipeline ----------------------------------------------------
#
# ALL synthesis runs inside build/work and the shipped TTFs in this
# directory are written exactly once, by the final copy step of one
# serialized recipe. Upstream stages never see the shipped files, so
# there is no way for a later step to mutate an earlier step's output
# -- which previously made every make run see the whole chain as stale
# (an mtime ping-pong that rebuilt the patcher endlessly).
#
# Any change to a script or knob requires the full chain again; that is
# the price of a DAG that cannot lie. `make clean` resets everything.

WORK       := build/work
PATCHERABS := $(CURDIR)/$(PATCHER)

$(PATCHER):
	git clone --depth 1 --filter=blob:none --sparse \
	    https://github.com/ryanoasis/nerd-fonts.git build/nerd-fonts
	unzip -q -o build/nerd-fonts/FontPatcher.zip -d build

.unified: $(SRC) patch_zero.py make_bold.py make_italic.py make_bolditalic.py \
          fix_nf_names.py unify_icons.py make_nf_wide.py \
          make_mono_variants.py make_hints.py | $(PATCHER)
	rm -rf $(WORK) && mkdir -p $(WORK)
	cp $(SRC) $(WORK)/
	cd $(WORK) && $(PY) $(CURDIR)/make_bold.py $(BOLD_WIDTH)
	cd $(WORK) && $(PY) $(CURDIR)/make_italic.py $(SLANT)
	cd $(WORK) && $(PY) $(CURDIR)/make_bolditalic.py $(SLANT)
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars tt0596m_.ttf
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars HE_TERMINAL-Bold.ttf
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars HE_TERMINAL-Italic.ttf
	cd $(WORK) && $(FF) -script $(PATCHERABS) --complete --careful \
	    --no-progressbars HE_TERMINAL-BoldItalic.ttf
	cd $(WORK) && for s in Regular Bold Italic BoldItalic; do \
	    $(PY) $(CURDIR)/fix_nf_names.py $$s; done
	cd $(WORK) && $(PY) $(CURDIR)/unify_icons.py
	cd $(WORK) && $(PY) $(CURDIR)/make_nf_wide.py
	cd $(WORK) && $(PY) $(CURDIR)/make_mono_variants.py
	cd $(WORK) && $(PY) $(CURDIR)/make_hints.py
	cp $(WORK)/HE_TERMINALNerdFont-Regular.ttf \
	   $(WORK)/HE_TERMINALNFMono-Regular.ttf .
	cp $(WORK)/HE_TERMINAL-Bold.ttf $(WORK)/HE_TERMINAL-Italic.ttf \
	   $(WORK)/HE_TERMINAL-BoldItalic.ttf .
	cp $(WORK)/HE_TERMINALNerdFont-Bold.ttf \
	   $(WORK)/HE_TERMINALNerdFont-Italic.ttf \
	   $(WORK)/HE_TERMINALNerdFont-BoldItalic.ttf .
	cp $(WORK)/HE_TERMINALNFMono-Bold.ttf \
	   $(WORK)/HE_TERMINALNFMono-Italic.ttf \
	   $(WORK)/HE_TERMINALNFMono-BoldItalic.ttf .
	touch $@

# ---- extras ----------------------------------------------------------------

preview: family_preview.png

family_preview.png: .unified make_previews.py
	$(PY) make_previews.py

install: all
	mkdir -p $(HOME)/.fonts/HE_TERMINAL
	cp HE_TERMINAL*.ttf $(HOME)/.fonts/HE_TERMINAL/
	fc-cache -f $(HOME)/.fonts/HE_TERMINAL >/dev/null
	@echo "installed $(shell ls HE_TERMINAL*.ttf | wc -l) fonts to $(HOME)/.fonts/HE_TERMINAL"

clean:
	rm -f tt0596m_.ttf HE_TERMINAL*.ttf .unified *_preview.png
	rm -rf build
