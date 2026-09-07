#!/usr/bin/env bash
# TikZ 図を SVG に事前生成する。
#
# tex4ht は DVI 経路を通るため和文 OpenType フォントを解決できず、
# TikZ 内の日本語が脱落する。そこで LuaLaTeX で図を個別に組版し、
# PDF を経由して SVG に変換する。HTML 版はこの SVG を読み込む。
#
# 図の描画そのものは figures.js が行い、この SVG は JS 無効環境の
# <noscript> フォールバックである。英語版は figures-en/ から作る。
#   bash build-figures.sh            日本語（figures/ → docs/book/figures/）
#   bash build-figures.sh en         英語  （figures-en/ → docs/book-en/figures/）
set -euo pipefail

cd "$(dirname "$0")"
LANG_ARG="${1:-ja}"
if [ "$LANG_ARG" = "en" ]; then
  SRCDIR="figures-en"; OUT="../docs/book-en/figures"
else
  SRCDIR="figures";    OUT="../docs/book/figures"
fi
mkdir -p "$OUT" build

# 各図を preview で 1 図 1 ページに切り出す
for f in "$SRCDIR"/*.tex; do
  name=$(basename "$f" .tex)
  cat > "build/$name.tex" <<EOF
\\documentclass[a4paper,11pt]{ltjsbook}
\\usepackage{luatexja-fontspec}
\\usepackage{unicode-math}
\\setmainfont{Latin Modern Roman}
\\setsansfont{Latin Modern Sans}
\\setmonofont{Latin Modern Mono}
\\setmathfont{Latin Modern Math}
\\setmainjfont{Noto Serif CJK JP}
\\setsansjfont{Noto Sans CJK JP}
\\usepackage{amsmath}
\\usepackage{tikz}
\\usetikzlibrary{positioning,arrows.meta,calc,fit,backgrounds}
\\newcommand{\\R}{\\mathbb{R}}
\\newcommand{\\E}{\\mathbb{E}}
\\newcommand{\\Prob}{\\mathbb{P}}
\\newcommand{\\Ind}{\\mathbf{1}}
\\newcommand{\\dbar}{\\bar{\\delta}}
\\newcommand{\\CCC}{\\mathrm{CCC}}
\\newcommand{\\FCF}{\\mathrm{FCF}}
\\usepackage[active,tightpage]{preview}
\\PreviewEnvironment{tikzpicture}
\\setlength\\PreviewBorder{2pt}
\\begin{document}
\\input{../$f}
\\end{document}
EOF
  ( cd build && lualatex -interaction=nonstopmode -halt-on-error "$name.tex" > /dev/null 2>&1 ) \
    || { echo "FAILED to compile $name"; ( cd build && lualatex -interaction=nonstopmode "$name.tex" | tail -20 ); exit 1; }
  dvisvgm --pdf --exact-bbox --font-format=woff2 \
          --output="$OUT/$name.svg" "build/$name.pdf" > /dev/null 2>&1 \
    || dvisvgm --pdf --exact-bbox --no-fonts \
               --output="$OUT/$name.svg" "build/$name.pdf" > /dev/null 2>&1
  test -s "$OUT/$name.svg" || { echo "FAILED to convert $name"; exit 1; }
  echo "  $name.svg  $(wc -c < "$OUT/$name.svg") bytes"
done

n=$(ls "$OUT"/*.svg | wc -l)
echo "generated $n figures"
rm -rf build
