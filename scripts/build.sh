#!/usr/bin/env bash
# PDF と HTML をまとめて作り、検査まで通す。
#   bash scripts/build.sh pdf     PDF のみ（3 回組版）
#   bash scripts/build.sh all     PDF + 図 + HTML + サイドバー + PDF 再組版
# 版はコマンドラインで渡す（省略時は book.tex から拾う）。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src"
MODE="${1:-pdf}"
VER="${2:-}"
[ -z "$VER" ] && VER="$(grep -o 'v0\.[0-9]*\.[0-9]*' "$SRC/book.tex" | head -1)"

cd "$SRC" || exit 1

pdf() { for _ in 1 2 3; do timeout 500 lualatex -interaction=nonstopmode book.tex >/dev/null 2>&1; done; }

pdf
if [ "$MODE" = "all" ]; then
  bash build-figures.sh >/dev/null 2>&1
  export TEXMFHOME="$HOME/texmf"
  MK="$HOME/texmf/scripts/lua/make4ht"
  export LUAINPUTS="$MK//:" TEXINPUTS="$MK//:"
  make4ht -l -f html5+dvisvgm_hashes -d "$ROOT/docs/book" book.tex "mathml,2" >/tmp/mk.log 2>&1
  echo "make4ht exit=$?  Unbalanced=$(grep -c 'Unbalanced' /tmp/mk.log)"
  python3 inject-sidebar.py "$ROOT/docs/book" "$VER" 2>&1 | tail -1
  echo "MathML の化け: $(grep -o 'mstyle[^>]*/mo&gt;' "$ROOT"/docs/book/*.html | wc -l)"
  pdf   # book.log を PDF ビルドのものに戻す
fi

P=$(grep -o 'on book.pdf ([0-9]* pages' book.log | grep -o '[0-9]*' | head -1)
echo "ページ数: $P"
# README と index.html のページ数を実測値に合わせる
sed -i "s/[0-9]\{3\}ページ/${P}ページ/g" "$ROOT/README.md" "$ROOT/.github/assets/index.html"

cd "$ROOT" || exit 1
python3 scripts/check.py
