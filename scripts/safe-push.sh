#!/usr/bin/env bash
# Windows 側マウントの書き込みが落ちることがあり、コミットが参照する
# loose object が実在しないまま残ることがある。push がそれで失敗したら、
# 直前の push 済みコミットまで戻し、作業ツリーのファイルを書き直してから
# 同じメッセージで作り直す。
#   bash scripts/safe-push.sh "<コミットメッセージのファイル>"
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
MSGFILE="${1:-}"

git config http.postBuffer 524288000
git config http.version HTTP/1.1

try_push() { git push origin main 2>&1; }

for attempt in 1 2 3; do
  OUT="$(try_push)"
  if echo "$OUT" | grep -q "main -> main\|Everything up-to-date"; then
    echo "push 成功（試行 $attempt）"; exit 0
  fi
  MISS="$(echo "$OUT" | grep -o 'unable to open loose object [0-9a-f]\{40\}' | grep -o '[0-9a-f]\{40\}' | head -1)"
  if [ -z "$MISS" ]; then
    echo "push 失敗（オブジェクト欠損ではない）:"; echo "$OUT" | tail -3; exit 1
  fi
  echo "  試行 $attempt: オブジェクト $MISS が欠損。コミットを作り直す"
  BASE="$(git rev-parse origin/main)"
  [ -z "$MSGFILE" ] && { git log -1 --pretty=%B > /tmp/_msg.txt; MSGFILE=/tmp/_msg.txt; }
  git reset --mixed "$BASE" >/dev/null 2>&1
  python3 - <<'PY'
import subprocess, pathlib
out = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True).stdout
n = 0
for line in out.splitlines():
    p = pathlib.Path(line[3:].strip().strip('"'))
    if p.is_file():
        p.write_bytes(p.read_bytes()); n += 1
print(f"  {n} ファイルを書き直した")
PY
  git add -A && git commit -q -F "$MSGFILE"
done
echo "3 回試しても push できなかった"; exit 1
