# 詳細ページが指す返戻金制度の PDF を落とす。
#
# 【二系統】返戻金制度の欄のリンクには二種類ある。
#   /icb_data/UploadFiles/Jigyosho/{許可番号}/henreikin/*.pdf  サイトが保持する届出書類
#   http://...                                                 事業者自身のサイト
#   後者はトップページを指すことが多く、該当箇所を機械的に特定できない。
#   本スクリプトは前者だけを落とし、後者は一覧に記録して人手に回す。
import io, os, re, sys, json, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "derived", "jinzai_detail.json")
OUT  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin")
UA   = "Mozilla/5.0 (compatible; research; +statistical study of placement fees)"
WAIT = 1.5

def main():
    rows = json.load(io.open(SRC, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    ok = skip = ng = 0
    ext = []
    for r in rows:
        u = r.get("henreikin_url")
        if not u:
            continue
        if not r.get("henreikin_pdf"):
            ext.append((r["permit"], r["henreikin"], u))
            continue
        name = urllib.parse.unquote(u.rsplit("/", 1)[-1])
        suf = os.path.splitext(name)[1].lower() or ".pdf"
        path = os.path.join(OUT, r["permit"] + suf)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            skip += 1
            continue
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as f:
                b = f.read()
            io.open(path, "wb").write(b)
            ok += 1
        except Exception as e:
            ng += 1
            sys.stderr.write("  ×  %s  %s\n" % (r["permit"], e))
        time.sleep(WAIT)
    io.open(os.path.join(OUT, "external.tsv"), "w", encoding="utf-8").write(
        "許可番号\t返戻金\tURL\n" + "\n".join("\t".join(x) for x in ext) + "\n")
    sys.stderr.write("  取得 %d / 既存 %d / 失敗 %d / 自社サイト %d（external.tsv）\n"
                     % (ok, skip, ng, len(ext)))

if __name__ == "__main__":
    main()
