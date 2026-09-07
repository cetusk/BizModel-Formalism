#!/usr/bin/env bash
# PDF と HTML をまとめて作り、検査まで通す。
#   bash scripts/build.sh pdf      日本語 PDF のみ（3 回組版）
#   bash scripts/build.sh en       英語 PDF のみ
#   bash scripts/build.sh all      日本語の PDF + 図 + HTML + サイドバー、および英語の PDF
#   bash scripts/build.sh all-en   上に加えて英語 HTML も作る
# 版はコマンドラインで渡す（省略時は book.tex から拾う）。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src"
MODE="${1:-pdf}"
VER="${2:-}"
[ -z "$VER" ] && VER="$(grep -o 'v0\.[0-9]*\.[0-9]*' "$SRC/book.tex" | head -1)"

cd "$SRC" || exit 1

pdf()    { for _ in 1 2 3; do timeout 500 lualatex -interaction=nonstopmode book.tex    >/dev/null 2>&1; done; }
pdf_en() { for _ in 1 2 3; do timeout 500 lualatex -interaction=nonstopmode book-en.tex >/dev/null 2>&1; done; }

html_env() {
  export TEXMFHOME="$HOME/texmf"
  MK="$HOME/texmf/scripts/lua/make4ht"
  export LUAINPUTS="$MK//:" TEXINPUTS="$MK//:"
}

case "$MODE" in
  en)
    pdf_en
    echo "英語版 $(grep -o 'on book-en.pdf ([0-9]* pages' book-en.log | grep -o '[0-9]*' | head -1) ページ / エラー $(grep -c '^!' book-en.log)"
    exit 0
    ;;
esac

pdf
if [ "$MODE" = "all" ] || [ "$MODE" = "all-en" ]; then
  bash build-figures.sh >/dev/null 2>&1
  bash build-figures.sh en >/dev/null 2>&1
  html_env
  make4ht -l -f html5+dvisvgm_hashes -d "$ROOT/docs/book" book.tex "mathml,2" >/tmp/mk.log 2>&1
  echo "make4ht(ja) exit=$?  Unbalanced=$(grep -c 'Unbalanced' /tmp/mk.log)"
  python3 inject-sidebar.py "$ROOT/docs/book" "$VER" ja 2>&1 | tail -1
  echo "MathML の化け: $(grep -o 'mstyle[^>]*/mo&gt;' "$ROOT"/docs/book/*.html | wc -l)"
fi

if [ "$MODE" = "all-en" ]; then
  html_env
  [ -d "$ROOT/docs/book-en/figures" ] && mv "$ROOT/docs/book-en/figures" /tmp/figs-en
  rm -rf "$ROOT/docs/book-en"
  make4ht -l -f html5+dvisvgm_hashes -d "$ROOT/docs/book-en" book-en.tex "mathml,2" >/tmp/mk-en.log 2>&1
  RC=$?
  [ -d /tmp/figs-en ] && mv /tmp/figs-en "$ROOT/docs/book-en/figures"
  echo "make4ht(en) exit=$RC  Unbalanced=$(grep -c 'Unbalanced' /tmp/mk-en.log)"
  python3 inject-sidebar.py "$ROOT/docs/book-en" "$VER" en 2>&1 | tail -1
fi

if [ "$MODE" = "all" ] || [ "$MODE" = "all-en" ]; then
  pdf_en
  pdf   # book.log を日本語 PDF ビルドのものに戻す（check.py が見る）
fi

P=$(grep -o 'on book.pdf ([0-9]* pages' book.log | grep -o '[0-9]*' | head -1)
echo "ページ数: $P"
sed -i "s/[0-9]\{3\}ページ/${P}ページ/g" "$ROOT/README.md" "$ROOT/.github/assets/index.html"
sed -i "s/([0-9]\{3\} pages)/(${P} pages)/g" "$ROOT/README.en.md"

cd "$ROOT" || exit 1
python3 scripts/check.py
