#!/usr/bin/env python3
"""生成された HTML に固定の目次サイドバーを注入する。

tex4ht は各ページに前後リンクしか置かないため、
book.html の目次を抽出して全ページ共通のサイドバーとして埋め込む。
"""
import re, sys, os, glob, html

BOOK_DIR = sys.argv[1] if len(sys.argv) > 1 else "../docs/book"
VERSION  = sys.argv[2] if len(sys.argv) > 2 else "v0.8.0"

BANNER = (
    f'<div class="wip"><strong>{VERSION}</strong> &mdash; 本稿は建設中です。'
    '理論の構成、命題、実証の結論はいずれも変更されうるものです。'
    '<a href="../index.html">概要</a></div>'
)


def extract_toc(path):
    s = open(path, encoding="utf-8").read()
    items = []
    pat = r"<span class='(part|chapter|section|likechapter|likesection)Toc'>(.*?)</span>"
    for m in re.finditer(pat, s, re.S):
        kind, inner = m.group(1), m.group(2)
        a = re.search(r"<a href='([^']+)'[^>]*>(.*?)</a>", inner, re.S)
        if not a:
            continue
        num = re.sub(r"<[^>]+>", "", inner[: inner.find("<a")]).strip()
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", a.group(2))).strip()
        href = a.group(1)
        # book.html 内のアンカーは他ページからは解決できないため補う
        if href.startswith("#"):
            href = "book.html" + href
        items.append((kind, href, num, label))
    return items


CROSSLINKS_RE = re.compile(r"<div class='crosslinks'><p class='noindent'>(.*?)</p></div>")
LINK_RE = re.compile(r"<a href='([^']+)'>([^<]+)</a>")


def rebuild_pagenav(html):
    """tex4ht の crosslinks（next/prev/prev-tail/tail/front/up の羅列）を、
    前へ・目次・次へ の3ボタンに作り直す。prev-tail/tail/front/up は捨てる。"""
    def repl(m):
        links = {label: href for href, label in LINK_RE.findall(m.group(1))}
        parts = ['<nav class="pagenav">']
        if "prev" in links:
            parts.append(f'<a class="pagenav-link pagenav-prev" href="{links["prev"]}">&larr; 前へ</a>')
        else:
            parts.append('<span class="pagenav-link pagenav-prev pagenav-disabled">&larr; 前へ</span>')
        parts.append('<a class="pagenav-link pagenav-toc" href="bookli1.html#contents">目次</a>')
        if "next" in links:
            parts.append(f'<a class="pagenav-link pagenav-next" href="{links["next"]}">次へ &rarr;</a>')
        else:
            parts.append('<span class="pagenav-link pagenav-next pagenav-disabled">次へ &rarr;</span>')
        parts.append('</nav>')
        return "".join(parts)
    return CROSSLINKS_RE.sub(repl, html)


def build_sidebar(items):
    out = ['<nav id="toc"><div class="toc-head">'
           '<a href="../index.html">目次</a>'
           '<button id="toc-close" aria-label="閉じる">&times;</button></div><ul>']
    for kind, href, num, label in items:
        cls = {"part": "t-part", "chapter": "t-chap", "section": "t-sec",
               "likechapter": "t-chap", "likesection": "t-chap"}[kind]
        n = f'<span class="tn">{html.escape(num)}</span> ' if num else ""
        out.append(f'<li class="{cls}"><a href="{href}">{n}{html.escape(label)}</a></li>')
    out.append("</ul></nav>")
    return "".join(out)


def main():
    book = os.path.join(BOOK_DIR, "book.html")
    items = extract_toc(book)
    if len(items) < 20:
        print(f"ERROR: only {len(items)} toc entries found", file=sys.stderr)
        sys.exit(1)
    sidebar = build_sidebar(items)
    toggle = ('<button id="toc-toggle" aria-label="目次">&#9776;</button>'
              '<div id="toc-resize" title="ドラッグで幅を変更、ダブルクリックで既定に戻す"></div>')

    # 本文フォント（M PLUS Rounded 1c）。和文込みの可変幅フォントで
    # Google 側が unicode-range ごとに数百のサブセットに分割配信するため、
    # Latin Modern（欧文のみ・4ファイル）と異なり自前バンドルはしない。
    head_extra = (
        "<link rel='preconnect' href='https://fonts.googleapis.com' />"
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin />"
        "<link href='https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap' rel='stylesheet' />"
        "<link href='custom.css' rel='stylesheet' type='text/css' />"
        "<script defer src='toc.js'></script>"
    )

    n = 0
    for f in sorted(glob.glob(os.path.join(BOOK_DIR, "*.html"))):
        s = open(f, encoding="utf-8").read()
        if "id=\"toc\"" in s:
            continue
        s = rebuild_pagenav(s)
        s = s.replace("</head>", head_extra + "</head>", 1)
        s = s.replace("<body>", "<body>" + sidebar + toggle
                      + '<div id="content">' + BANNER, 1)
        s = s.replace("</body>", "</div></body>", 1)
        open(f, "w", encoding="utf-8").write(s)
        n += 1
    print(f"sidebar injected into {n} files ({len(items)} toc entries)")


if __name__ == "__main__":
    main()
