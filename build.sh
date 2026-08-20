#!/usr/bin/env bash
# HARDBRUT build — bundles the Inter 900 latin font into hardbrut.css (and
# minified + gzipped variants) from src/hardbrut.css.
#
# The template (src/hardbrut.css) carries the literal placeholder __FONT_B64__
# inside its @font-face src: url(). This script reads the vendored font
# (vendor/inter-900-latin.woff2, a browser WOFF2 of Inter weight 900, latin
# subset), base64-encodes it, and substitutes it for the placeholder — so no
# build source ever leaks into the shipped CSS (the v0.8 bug).
#
# Usage:  ./build.sh            # bundle from the vendored font
#         ./build.sh --fetch    # re-download the pinned font, then bundle
set -euo pipefail

cd "$(dirname "$0")"

TEMPLATE="src/hardbrut.css"
FONT="vendor/inter-900-latin.woff2"
# Pinned Google Fonts WOFF2 (Inter 900, latin): the exact file the CSS2 API
# serves to modern browsers for the "latin" unicode-range block.
FONT_URL="https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuBWYAZ9hiA.woff2"

if [[ "${1:-}" == "--fetch" ]]; then
  echo "fetching Inter 900 (latin) -> $FONT"
  mkdir -p vendor
  curl -fsSL -A "Mozilla/5.0" -o "$FONT" "$FONT_URL"
fi

if [[ ! -f "$FONT" ]]; then
  echo "font missing: $FONT  (run: ./build.sh --fetch)" >&2
  exit 1
fi

B64="$(base64 -w0 "$FONT")"
echo "font: $FONT ($(wc -c < "$FONT") bytes, base64 $(( ${#B64} )) chars)"

# Read template and substitute the placeholder with the base64 blob.
CSS="$(sed "s|__FONT_B64__|${B64}|g" "$TEMPLATE")"

# Guard: the placeholder must be gone, and no shell/heredoc marker may remain.
if grep -q '__FONT_B64__' <<< "$CSS"; then
  echo "ERROR: __FONT_B64__ placeholder still present after substitution" >&2
  exit 1
fi
for bad in 'echo -n' '${B64}' '<<' 'EOF'; do
  if grep -qF "$bad" <<< "$CSS"; then
    echo "ERROR: leaked build-source marker ($bad) in output CSS" >&2
    exit 1
  fi
done

printf '%s' "$CSS" > hardbrut.css
echo "wrote hardbrut.css ($(wc -c < hardbrut.css) bytes)"

# Minify (whitespace/comments only — no structural change, safe for this CSS).
if command -v pnpm >/dev/null 2>&1; then
  : # keep it dependency-free: use our own naive minifier below
fi
MIN="$(printf '%s' "$CSS" | sed -E 's@/\*[^*]*\*+([^/*][^*]*\*+)*/@ @g' | tr -s '[:space:]' ' ' | sed -E 's/[[:space:]]*([{};,>:])[[:space:]]*/\1/g; s/[[:space:]]+/ /g')"
printf '%s' "$MIN" > hardbrut.min.css
echo "wrote hardbrut.min.css ($(wc -c < hardbrut.min.css) bytes)"

gzip -9 -c hardbrut.min.css > hardbrut.min.css.gz
echo "wrote hardbrut.min.css.gz ($(wc -c < hardbrut.min.css.gz) bytes)"

echo "done — hardbrut.css carries the embedded Inter 900 (zero external requests)."
