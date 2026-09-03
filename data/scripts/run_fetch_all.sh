#!/bin/bash
# 詳細ページの取得を最後まで自動で回す。
# 1回300件で打ち切り、次まで5分空ける。公式サイトへの直接アクセスなので
# 一気に叩かない。取得済みは飛ばすので、途中で止めても再開できる。
cd "$(dirname "$0")" || exit 1
LOG=/tmp/fetch_all.log
D=../raw/jinzai/detail

say(){ echo "[$(date +%H:%M:%S)] $*" >> "$LOG"; }

# 先行するプロセスが走っていれば終わるまで待つ
while pgrep -f "fetch_jinzai_detail.py --wait" > /dev/null; do sleep 20; done
say "先行プロセス終了。$(ls $D | grep -c '\.html$') / 1130 社"

while :; do
  n=$(ls $D | grep -c '\.html$')
  [ "$n" -ge 1130 ] && { say "全件そろった（$n）"; break; }
  say "5分待機してから次の300件"
  sleep 300
  say "開始（現在 $n 社）"
  python3 fetch_jinzai_detail.py --wait=6 --limit=300 >> "$LOG" 2>&1
  m=$(ls $D | grep -c '\.html$')
  say "終了（$n → $m 社）"
  # 1件も増えなければ、残りは連番0/1では解決しないものだけ。抜ける
  [ "$m" -le "$n" ] && { say "増加なし。打ち切る"; break; }
done

# 連番0,1 で解決しなかったものを 2..5 まで広げて拾う
if [ -s "$D/failed.tsv" ]; then
  say "5分待機してから再試行 $(wc -l < $D/failed.tsv) 件"
  sleep 300
  python3 fetch_jinzai_detail.py --retry --wait=6 >> "$LOG" 2>&1
  say "再試行終了。$(ls $D | grep -c '\.html$') / 1130 社"
fi

# 解析まで通す（ネットワークは使わない）
say "解析を実行"
python3 parse_jinzai_detail.py >> "$LOG" 2>&1
python3 firms_from_detail.py >> "$LOG" 2>&1
say "完了。$(ls $D | grep -c '\.html$') / 1130 社、失敗 $(wc -l < $D/failed.tsv 2>/dev/null || echo 0) 件"
