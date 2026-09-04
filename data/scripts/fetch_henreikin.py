# 詳細ページが指す返戻金制度の PDF を落とす。
#
# 【二系統】返戻金制度の欄のリンクには二種類ある。
#   /icb_data/UploadFiles/Jigyosho/{許可番号}/henreikin/*.pdf  サイトが保持する届出書類
#   http://...                                                 事業者自身のサイト
#   後者はトップページを指すことが多く、該当箇所を機械的に特定できない。
#   本スクリプトは前者だけを落とし、後者は一覧に記録して人手に回す。
# 【作法】詳細ページと同じく1件6秒空ける。取得済みは飛ばすので中断・再開できる。
#   順序は固定の種で混ぜる。途中で止めたときに残りが偏らないようにするため。
import io, os, re, sys, json, time, random, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "derived", "jinzai_detail.json")
OUT  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin")
UA   = "Mozilla/5.0 (compatible; research; +statistical study of placement fees)"
WAIT = 6.0
SEED = 20260904

def main(wait=WAIT):
    rows = json.load(io.open(SRC, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    todo, ext = [], []
    for r in rows:
        u = r.get("henreikin_url")
        if not u:
            continue
        if not r.get("henreikin_pdf"):
            # 事業者自身のサイト。トップページを指すことが多く該当箇所を特定できない
            ext.append((r["permit"], r["henreikin"] or "-", u))
            continue
        name = urllib.parse.unquote(u.rsplit("/", 1)[-1])
        suf = os.path.splitext(name)[1].lower() or ".pdf"
        todo.append((r["permit"], u, os.path.join(OUT, r["permit"] + suf), r["henreikin"] or "-"))
    io.open(os.path.join(OUT, "external.tsv"), "w", encoding="utf-8").write(
        "許可番号\t返戻金\tURL\n" + "\n".join("\t".join(x) for x in ext) + "\n")

    done = [t for t in todo if os.path.exists(t[2]) and os.path.getsize(t[2]) > 1000]
    rest = [t for t in todo if t not in done]
    random.Random(SEED).shuffle(rest)
    sys.stderr.write("  対象 %d 件（有 %d / 無 %d）。取得済み %d、未取得 %d。間隔 %.1f 秒\n"
                     % (len(todo), sum(1 for t in todo if t[3] == "有"),
                        sum(1 for t in todo if t[3] == "無"), len(done), len(rest), wait))
    sys.stderr.write("  自社サイトのみ %d 件は external.tsv に記録した\n" % len(ext))

    ok = ng = 0
    t0 = time.time()
    fail = os.path.join(OUT, "failed.tsv")
    for i, (permit, u, path, flag) in enumerate(rest, 1):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as f:
                b = f.read()
            io.open(path, "wb").write(b)
            ok += 1
        except Exception as e:
            ng += 1
            io.open(fail, "a", encoding="utf-8").write("%s\t%s\n" % (permit, e))
            sys.stderr.write("  ×  %s  %s\n" % (permit, str(e)[:60]))
        if i < len(rest):
            time.sleep(wait)
        if i % 50 == 0:
            sys.stderr.write("  … %d/%d  取得 %d 失敗 %d  経過 %.0f 分\n"
                             % (i, len(rest), ok, ng, (time.time() - t0) / 60))
    sys.stderr.write("  取得 %d / 失敗 %d / 合計 %d 件\n"
                     % (ok, ng, len([1 for t in todo if os.path.exists(t[2])])))

if __name__ == "__main__":
    kw = dict((x[2:].split("=", 1) + ["1"])[:2] for x in sys.argv[1:] if x.startswith("--"))
    main(wait=float(kw.get("wait", WAIT)))
