#!/usr/bin/env bash
# ローカルの開発環境を整える。
#
# CI は texlive/texlive コンテナ上で走るため make4ht が最初から入っているが、
# Debian/Ubuntu の TeX Live には含まれない。ここで導入する。
set -euo pipefail

echo "=== TeX Live と関連ツールの確認 ==="
missing=()
for cmd in lualatex dvisvgm mutool pdftotext; do
  command -v "$cmd" > /dev/null || missing+=("$cmd")
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "不足: ${missing[*]}"
  echo "以下で導入してください（要 sudo）:"
  cat <<'EOF'
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    texlive-luatex texlive-latex-extra texlive-lang-japanese \
    texlive-fonts-recommended texlive-plain-generic texlive-pictures \
    fonts-noto-cjk dvisvgm poppler-utils mupdf-tools
EOF
  exit 1
fi

echo "=== フォントの確認 ==="
for f in "Noto Serif CJK JP" "Latin Modern Roman" "Latin Modern Math"; do
  if fc-list "$f" | grep -q .; then
    echo "  OK   $f"
  else
    echo "  なし $f"
    echo "       fonts-noto-cjk と fonts-lmodern を導入してください"
    exit 1
  fi
done

echo "=== make4ht の確認 ==="
if command -v make4ht > /dev/null; then
  echo "  導入済み: $(make4ht --version 2>&1 | head -1)"
else
  echo "  導入します"
  TMP=$(mktemp -d)
  git clone --depth 1 https://github.com/michal-h21/make4ht.git "$TMP/make4ht"
  cd "$TMP/make4ht"

  # 文字定義テーブルはリポジトリに含まれず、ビルド時に生成される
  texlua tools/make_chardata.lua       > make4ht-char-def.lua
  texlua tools/make_mathmlchardata.lua > make4ht-mathml-char-def.lua

  MK4HT_DIR="$HOME/texmf/scripts/lua/make4ht"
  mkdir -p "$MK4HT_DIR"
  cp ./*.lua "$MK4HT_DIR/"
  cp ./make4ht "$MK4HT_DIR/"
  cp -r domfilters filters extensions formats "$MK4HT_DIR/"
  chmod +x "$MK4HT_DIR/make4ht"
  sudo ln -sf "$MK4HT_DIR/make4ht" /usr/local/bin/make4ht
  cd - > /dev/null
  rm -rf "$TMP"
  echo "  完了"
fi

cat <<'EOF'

=== 環境変数 ===
make4ht のモジュールは kpse から見えないため、以下を設定してください。
.claude/settings.json にも同じものを入れてあります。

  export TEXMFHOME="$HOME/texmf"
  export LUAINPUTS="$HOME/texmf/scripts/lua/make4ht//:"
  export TEXINPUTS="$HOME/texmf/scripts/lua/make4ht//:"

=== ビルド ===
  cd src
  lualatex -interaction=nonstopmode book.tex   # 3 回
  bash build-figures.sh
  make4ht -l -f html5+dvisvgm_hashes -d ../docs/book book.tex "mathml,2"
  python3 inject-sidebar.py ../docs/book v0.8.0

EOF
