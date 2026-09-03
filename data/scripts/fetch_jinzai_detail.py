# 人材サービス総合サイトの「職業紹介事業詳細」を許可番号で取得して保存する。
#
# 【URL】許可・届出受理番号を XXX、事業所の連番を n とすると
#   .../GICB102030.do?screenId=GICB102030&action=detail&detkey_Detail={XXX}%2C{n}+++++
#   連番は6桁に左詰めで空白詰めする（"1     " のように）。
#
# 【連番】検索結果一覧の detkey_Detail を数えると 0 か 1 の二値である（1 が 64、0 が 14）。
#   0 を試さないと 3 割前後が「サーバーでエラーが発生しました」を返し、
#   しかも取れる社と取れない社は事業所数とも種別とも相関しない。
#   非ランダムな欠測になるので、必ず両方を試すこと。
#
# 【注意】解決に失敗した番号にはエラーでなく直前の結果が返ることがある。
#   保存前に必ずページ内の許可番号を照合し、不一致なら捨てる（第17.4節）。
#
# 【作法】公式サイトへの直接アクセスである。次を守る。
#   - 既定で1件あたり6秒空ける（--wait）
#   - 1回の実行を300件で打ち切る（--limit）。日を分けて回す
#   - 取得済みは再取得しない。何度でも中断・再開できる
#   - 失敗は failed.tsv に記録し、同じ実行では追わない
#
# 【順序】未取得のものは固定の種で並べ替えてから回す。
#   許可番号順や職種ファイル順のまま回すと、途中で止めたときに
#   残りが特定の県や職種に偏る。**部分的な取得が無作為な部分標本になるようにする。**
import io, os, re, sys, time, json, random, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "raw", "jinzai", "detail")
URL  = ("https://jinzai.hellowork.mhlw.go.jp/JinzaiWeb/GICB102030.do"
        "?screenId=GICB102030&action=detail&detkey_Detail={}%2C{}")
SEQ  = (1, 0)   # 出現の多い順
UA   = "Mozilla/5.0 (compatible; research; +statistical study of placement fees)"
WAIT = 6.0     # 1件あたりの間隔（秒）
LIMIT = 300    # 1回の実行で取る上限
SEED = 20260903

def one(permit, seq, retries=1):
    url = URL.format(urllib.parse.quote(permit, safe="-"),
                     urllib.parse.quote(str(seq).ljust(6)))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    for k in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace"), None
        except Exception as e:
            if k == retries:
                return None, "取得失敗: %s" % e
            time.sleep(WAIT * 3)
    return None, "取得失敗"

def fetch(permit):
    """連番を順に試して HTML を返す。許可番号が一致しなければ捨てる。"""
    last = "該当なし"
    for seq in SEQ:
        s, err = one(permit, seq)
        if s is None:
            last = err
            continue
        got = set(re.findall(r'\d{2}-.-\d{6}', re.sub(r'<[^>]+>', ' ', s)))
        if got == {permit}:
            return s, seq, None
        last = ("許可番号が不一致（%s）" % ",".join(sorted(got))[:24]) if got else "該当なし"
        time.sleep(WAIT)
    return None, None, last

def main(permits, wait=WAIT, limit=LIMIT):
    os.makedirs(OUT, exist_ok=True)
    def path_of(p):
        return os.path.join(OUT, p.replace("/", "_") + ".html")

    done = [p for p in permits if os.path.exists(path_of(p)) and os.path.getsize(path_of(p)) > 5000]
    todo = [p for p in permits if p not in set(done)]
    # 固定の種で混ぜる。途中で止めても残りが偏らないようにするため。
    random.Random(SEED).shuffle(todo)
    sys.stderr.write("  取得済み %d / 未取得 %d / 今回の上限 %d（間隔 %.1f 秒）\n"
                     % (len(done), len(todo), limit, wait))
    todo = todo[:limit]

    fail = os.path.join(OUT, "failed.tsv")
    ok = ng = 0
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        s, seq, err = fetch(p)
        if s is None:
            ng += 1
            io.open(fail, "a", encoding="utf-8").write("%s\t%s\n" % (p, err))
            sys.stderr.write("  ×  %s  %s\n" % (p, err))
        else:
            io.open(path_of(p), "w", encoding="utf-8").write(s)
            io.open(path_of(p) + ".seq", "w", encoding="utf-8").write(str(seq))
            ok += 1
        if i < len(todo):
            time.sleep(wait)
        if i % 25 == 0:
            sys.stderr.write("  … %d/%d  取得 %d 失敗 %d  経過 %.0f 分\n"
                             % (i, len(todo), ok, ng, (time.time() - t0) / 60))
    left = len(permits) - len(done) - ok
    sys.stderr.write("  取得 %d / 失敗 %d / 残り %d\n" % (ok, ng, left))
    if left:
        sys.stderr.write("  続きは日を改めて同じコマンドを実行する。\n")

def load_failed():
    """failed.tsv に残ったものを、連番の範囲を広げて拾い直す。
    本取得を止めてから走らせること（同時に叩かない）。"""
    f = os.path.join(OUT, "failed.tsv")
    if not os.path.exists(f):
        return []
    seen, out = set(), []
    for line in io.open(f, encoding="utf-8"):
        p = line.split("\t")[0].strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out

def load_permits():
    """取得の種は raw/jinzai/permits.tsv（許可番号と職種のみ。値は含まない）。

    検索結果一覧のテキストは再配布しないため git に入れていない。
    それを唯一の入口にすると、テキストが無い環境では取得対象が決まらず、
    値も取り直せなくなる。**種を値から切り離しておく。**

    permits.tsv は (企業 × 職種) の 1,402 行だが、相異なる許可番号は 1,130 で、
    詳細ページは企業単位なので重複を除く。
    """
    seed = os.path.join(HERE, "..", "raw", "jinzai", "permits.tsv")
    seen, out = set(), []
    if os.path.exists(seed):
        for line in io.open(seed, encoding="utf-8"):
            if line.startswith("#"):
                continue
            p = line.split("\t")[0].strip()
            if re.match(r"^\d{2}-.-\d{6}$", p) and p not in seen:
                seen.add(p)
                out.append(p)
        return out
    # 種が無ければ、手元にテキストがある場合に限り中間データから拾う
    d = json.load(io.open(os.path.join(HERE, "..", "derived", "jinzai_firms.json"), encoding="utf-8"))
    for r in d:
        if r["permit"] not in seen:
            seen.add(r["permit"])
            out.append(r["permit"])
    return out

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    kw = dict((x[2:].split("=", 1) + ["1"])[:2] for x in sys.argv[1:] if x.startswith("--"))
    if "retry" in kw:
        # 連番 0,1 で解決しなかったものを 2..5 まで広げて試す
        SEQ = tuple(range(0, 6))
        globals()["SEQ"] = SEQ
        a = load_failed()
        os.rename(os.path.join(OUT, "failed.tsv"), os.path.join(OUT, "failed.prev.tsv"))
        sys.stderr.write("  再試行 %d 件（連番 %s）\n" % (len(a), ",".join(map(str, SEQ))))
    main(a or load_permits(),
         wait=float(kw.get("wait", WAIT)), limit=int(kw.get("limit", LIMIT)))
