# 返戻金の内容を自社サイトにのみ掲示する事業者について、そのページを取得する。
#
# 詳細ページの返戻金欄が事業者自身のURLを指す 75 件が対象。多くはトップページで、
# 返戻金の記載が別ページにあることがある。本文に見当たらない場合は、
# 同一ドメイン内のリンクのうち手数料・返戻・料金に関するものを一段だけ辿る。
#
# 【作法】相手先はそれぞれ別のドメインなので1件あたりの負荷は軽いが、
#   間隔を4秒空け、1ドメインにつき最大3ページまでとする。
import io, os, re, sys, json, time, urllib.parse, urllib.request, gzip

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "derived", "jinzai_detail.json")
OUT  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin_web")
UA   = "Mozilla/5.0 (compatible; research; +statistical study of placement fees)"
WAIT, MAXP = 4.0, 3
KEY  = re.compile(r"返戻|返金|返還|手数料|料金|ご利用の流れ|紹介料")

def get(u, timeout=35):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "ja",
                                             "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return b, (r.headers.get("Content-Type") or ""), r.geturl()

def text(b, ct):
    if "pdf" in ct.lower() or b[:4] == b"%PDF":
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b); p = f.name
        try:
            return subprocess.run(["pdftotext", "-enc", "UTF-8", p, "-"],
                                  capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
        finally:
            os.unlink(p)
    s = b.decode("utf-8", "replace")
    m = re.search(r'charset=["\']?([\w-]+)', s[:2000], re.I)
    if m and m.group(1).lower() not in ("utf-8", "utf8"):
        try: s = b.decode(m.group(1), "replace")
        except Exception: pass
    s = re.sub(r"(?is)<(script|style|nav|footer)[^>]*>.*?</\1>", " ", s)
    return re.sub(r"<[^>]+>", " ", s)

def links(html, base):
    out = []
    for m in re.finditer(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.{0,80}?)</a>', html, re.S | re.I):
        lab = re.sub(r"<[^>]+>", "", m.group(2))
        if not KEY.search(lab):
            continue
        u = urllib.parse.urljoin(base, m.group(1))
        if urllib.parse.urlparse(u).netloc == urllib.parse.urlparse(base).netloc:
            out.append(u)
    seen, o = set(), []
    for u in out:
        if u not in seen:
            seen.add(u); o.append(u)
    return o[:MAXP - 1]

def main():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(io.open(SRC, encoding="utf-8"))
    todo = [(r["permit"], r["henreikin_url"]) for r in rows
            if r["henreikin_url"] and not r["henreikin_pdf"]]
    sys.stderr.write("  対象 %d 件\n" % len(todo))
    ok = ng = hit = 0
    for i, (p, u) in enumerate(todo, 1):
        out = os.path.join(OUT, p + ".txt")
        if os.path.exists(out) and os.path.getsize(out) > 200:
            continue
        got = []
        try:
            b, ct, real = get(u)
            t = text(b, ct)
            got.append((real, t))
            if "html" in ct.lower() and not re.search(r"返戻|返金|返還", t):
                for lu in links(b.decode("utf-8", "replace"), real):
                    time.sleep(WAIT)
                    try:
                        b2, ct2, r2 = get(lu)
                        got.append((r2, text(b2, ct2)))
                    except Exception:
                        pass
            ok += 1
        except Exception as e:
            ng += 1
            sys.stderr.write("  ×  %s  %s\n" % (p, str(e)[:60]))
        if got:
            s = "\n\n".join("### %s\n%s" % (a, re.sub(r"[ \t　]+", " ", c)) for a, c in got)
            io.open(out, "w", encoding="utf-8").write(s)
            if re.search(r"返戻|返金|返還", s):
                hit += 1
        time.sleep(WAIT)
        if i % 15 == 0:
            sys.stderr.write("  … %d/%d  取得 %d 失敗 %d 返戻の語あり %d\n" % (i, len(todo), ok, ng, hit))
    sys.stderr.write("  完了。取得 %d / 失敗 %d / 返戻の語あり %d\n" % (ok, ng, hit))

if __name__ == "__main__":
    main()
