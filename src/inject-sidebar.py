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
    # appendix: 付録の章（\appendix 以降は A/B/C... の文字番号になり、
    # tex4ht は chapterToc ではなく appendixToc という別クラスで出力する
    pat = r"<span class='(part|chapter|appendix|section|likechapter|likesection)Toc'>(.*?)</span>"
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


CROSSLINKS_RE = re.compile(r"<div class='crosslinks'><p class='noindent'>.*?</p></div>")


def file_of(href):
    return href.split("#", 1)[0]


def build_nav_maps(items):
    """章レベルと部レベル、二つの粒度のページ送りを items（TOC 順の全項目）から組む。

    tex4ht 自身の crosslinks（next/prev）は部の境界をまたぐと途切れる
    （最終章の next が空、次の部の先頭章の prev が空になる）。
    そこで tex4ht の生成物には頼らず、TOC の並び順から自前で
    「章の並び（部の区切りページを飛ばして章から章へ直結）」と
    「部の並び」を再構成する。
    """
    seen, seq = set(), []
    for kind, href, num, label in items:
        if kind not in ("part", "chapter", "appendix", "likechapter"):
            continue
        f = file_of(href)
        if f in seen:
            continue
        seen.add(f)
        seq.append({"file": f, "kind": kind, "num": num, "label": label})

    part_list = []          # [{file, num, label, first_chapter}]
    chapter_list = []       # [{file, num, label, part_idx}]  部の区切りページを除いた章の並び
    cur_part_idx = None
    for entry in seq:
        if entry["kind"] == "part":
            part_list.append({"file": entry["file"], "num": entry["num"],
                               "label": entry["label"], "first_chapter": None})
            cur_part_idx = len(part_list) - 1
        else:
            entry = dict(entry, part_idx=cur_part_idx)
            chapter_list.append(entry)
            if cur_part_idx is not None and part_list[cur_part_idx]["first_chapter"] is None:
                part_list[cur_part_idx]["first_chapter"] = entry["file"]

    chapter_index = {c["file"]: i for i, c in enumerate(chapter_list)}
    part_index = {p["file"]: i for i, p in enumerate(part_list)}
    last_chapter_of_part = {}
    for c in chapter_list:
        if c["part_idx"] is not None:
            last_chapter_of_part[c["part_idx"]] = c["file"]  # 最後に代入されたものが残る

    return {
        "chapter_list": chapter_list, "chapter_index": chapter_index,
        "part_list": part_list, "part_index": part_index,
        "last_chapter_of_part": last_chapter_of_part,
    }


def nav_targets(fname, maps):
    """指定ファイルについて (章prev, 章next, 部prev, 部next) を返す。
    各要素は None または {file, num, label}。"""
    chapter_list, chapter_index = maps["chapter_list"], maps["chapter_index"]
    part_list, part_index = maps["part_list"], maps["part_index"]
    last_chapter_of_part = maps["last_chapter_of_part"]

    chapter_prev = chapter_next = None
    part_idx = None  # このページが属する（章なら現在の部、区切りページなら自分自身の）部の位置

    if fname in chapter_index:
        i = chapter_index[fname]
        if i > 0:
            chapter_prev = chapter_list[i - 1]
        if i < len(chapter_list) - 1:
            chapter_next = chapter_list[i + 1]
        part_idx = chapter_list[i]["part_idx"]
    elif fname in part_index:
        pidx = part_index[fname]
        part_idx = pidx
        first = part_list[pidx]["first_chapter"]
        if first:
            chapter_next = next((c for c in chapter_list if c["file"] == first), None)
        if pidx > 0:
            prev_file = last_chapter_of_part.get(pidx - 1)
            if prev_file:
                chapter_prev = next((c for c in chapter_list if c["file"] == prev_file), None)

    eff_idx = part_idx if part_idx is not None else -1
    part_prev = part_next = None
    if eff_idx >= 1:
        target = part_list[eff_idx - 1]
        dest = target["first_chapter"]
        part_prev = next((c for c in chapter_list if c["file"] == dest), None) if dest else \
            {"file": target["file"], "num": target["num"], "label": target["label"]}
    if 0 <= eff_idx + 1 <= len(part_list) - 1:
        target = part_list[eff_idx + 1]
        dest = target["first_chapter"]
        part_next = next((c for c in chapter_list if c["file"] == dest), None) if dest else \
            {"file": target["file"], "num": target["num"], "label": target["label"]}
        # 部レベルのボタンには「跳び先の部」自体の番号・名前を出す（跳び先の章名ではなく）
        part_next = {**part_next, "part_num": target["num"], "part_label": target["label"]}
    if part_prev is not None:
        target = part_list[eff_idx - 1]
        part_prev = {**part_prev, "part_num": target["num"], "part_label": target["label"]}

    return chapter_prev, chapter_next, part_prev, part_next


def rebuild_pagenav(html_text, fname, maps):
    """tex4ht の crosslinks（next/prev/prev-tail/tail/front/up の羅列）を、
    部レベル（前の部／次の部）と章レベル（前へ／次へ／目次）の
    二段構成に作り直す。粒度ごとに別々の行にする。"""
    if not CROSSLINKS_RE.search(html_text):
        return html_text

    chapter_prev, chapter_next, part_prev, part_next = nav_targets(fname, maps)

    def link(cls, target, label, disabled_label):
        if target is None:
            return f'<span class="{cls} pagenav-disabled">{disabled_label}</span>'
        return f'<a class="{cls}" href="{target["file"]}">{label}</a>'

    part_row = (
        '<div class="pagenav-part-row">'
        + link("pagenav-part-link pagenav-part-prev", part_prev,
               f'&laquo; 第{html.escape(part_prev["part_num"])}部 {html.escape(part_prev["part_label"])}'
               if part_prev else "", "&laquo; 前の部")
        + link("pagenav-part-link pagenav-part-next", part_next,
               f'第{html.escape(part_next["part_num"])}部 {html.escape(part_next["part_label"])} &raquo;'
               if part_next else "", "次の部 &raquo;")
        + '</div>'
    )
    chapter_row = (
        '<div class="pagenav-chapter-row">'
        + link("pagenav-link pagenav-prev", chapter_prev, "&larr; 前へ", "&larr; 前へ")
        + '<a class="pagenav-link pagenav-toc" href="bookli1.html#contents">目次</a>'
        + link("pagenav-link pagenav-next", chapter_next, "次へ &rarr;", "次へ &rarr;")
        + '</div>'
    )
    replacement = f'<nav class="pagenav">{part_row}{chapter_row}</nav>'
    return CROSSLINKS_RE.sub(replacement, html_text)


def build_sidebar(items):
    out = ['<nav id="toc"><div class="toc-head">'
           '<a href="../index.html">目次</a>'
           '<button id="toc-close" aria-label="閉じる">&times;</button></div><ul>']
    for kind, href, num, label in items:
        cls = {"part": "t-part", "chapter": "t-chap", "appendix": "t-chap", "section": "t-sec",
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
    maps = build_nav_maps(items)
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
        "<script defer src='figures.js'></script>"
    )

    n = 0
    for f in sorted(glob.glob(os.path.join(BOOK_DIR, "*.html"))):
        s = open(f, encoding="utf-8").read()
        if "id=\"toc\"" in s:
            continue
        s = rebuild_pagenav(s, os.path.basename(f), maps)
        s = s.replace("</head>", head_extra + "</head>", 1)
        s = s.replace("<body>", "<body>" + sidebar + toggle
                      + '<div id="content">' + BANNER, 1)
        s = s.replace("</body>", "</div></body>", 1)
        open(f, "w", encoding="utf-8").write(s)
        n += 1
    print(f"sidebar injected into {n} files ({len(items)} toc entries)")


if __name__ == "__main__":
    main()
