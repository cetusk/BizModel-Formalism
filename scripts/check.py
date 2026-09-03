#!/usr/bin/env python3
"""文書の整合性を機械的に検査する。

これまで手作業で見落としてきた項目をまとめてある。
内容を変更したら必ず実行すること。

    python3 scripts/check.py

src/book.log と src/book.aux が必要なので、先に lualatex を 3 回通しておく。
"""
import re
import sys
import glob
import os
import subprocess

SRC = "src"
TEX = [f for f in glob.glob(os.path.join(SRC, "*.tex"))
       if os.path.basename(f) != "book.tex"]

# 章の順序。前方参照の検査に使う。
# 固定リストにすると章を挿入したときに古いままになり、
# 新しい章が検査対象から漏れる。book.tex の \input の並びから毎回導出する。
APPENDIX = {"appendix.tex", "app_revisions.tex"}


def build_order():
    r"""book.tex の \input 順に (ファイル名, その章の先頭章番号) を返す"""
    bt = open(os.path.join(SRC, "book.tex"), encoding="utf-8").read()
    order, n = [], 0
    for m in re.finditer(r"\\input\{([^}]+)\}", bt):
        name = os.path.basename(m.group(1))
        if not name.endswith(".tex"):
            name += ".tex"
        if name in APPENDIX:
            break
        f = os.path.join(SRC, name)
        if not os.path.exists(f):
            continue
        order.append((name, n + 1))
        n += len(re.findall(r"^\\chapter\{", open(f, encoding="utf-8").read(), re.M))
    return order


PAST = re.compile(
    r"(用いた|扱った|述べた|記録した|示した|導いた|確認した|得られた|判明した|であった|とした|できた)")

fail = 0


def err(msg):
    global fail
    print(f"  NG  {msg}")
    fail = 1


def ok(msg):
    print(f"  OK  {msg}")


def load_labels():
    """.aux から label の種別（部・章・節）を得る"""
    path = os.path.join(SRC, "book.aux")
    if not os.path.exists(path):
        print("book.aux がない。先に lualatex を通すこと")
        sys.exit(2)
    aux = open(path, encoding="utf-8", errors="replace").read()
    typ, num = {}, {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux):
        lab, v = m.group(1), m.group(2)
        if lab.endswith("@cref"):
            continue
        if re.fullmatch(r"[IVX]+", v):
            typ[lab] = "部"
        elif re.fullmatch(r"\d+", v):
            typ[lab] = "章"; num[lab] = int(v)
        elif re.fullmatch(r"\d+\.\d+(\.\d+)?", v):
            typ[lab] = "節"; num[lab] = int(v.split(".")[0])
    return typ, num


def check_log():
    print("\n[1] LaTeX のログ")
    path = os.path.join(SRC, "book.log")
    if not os.path.exists(path):
        err("book.log がない")
        return
    log = open(path, encoding="utf-8", errors="replace").read()
    # make4ht は同じ book.log を上書きする。HTML 変換のログでは行分割が
    # 意味を持たないためオーバーフルが大量に出る。PDF のログか確かめる。
    if "Output written on book.pdf" not in log:
        if "tex4ht" in log or "4ht.sty" in log:
            err("book.log が make4ht のもの。PDF ビルドを最後に流すこと")
        else:
            err("book.log に PDF 出力の記録がない。lualatex を通すこと")
        return
    # ログが古くないか
    newer = [os.path.basename(f) for f in TEX + [os.path.join(SRC, "book.tex")]
             if os.path.getmtime(f) > os.path.getmtime(path)]
    if newer:
        err("book.log より新しい .tex がある: " + ", ".join(sorted(newer)[:5]))
        return
    ok("book.log は PDF ビルドのもので、.tex より新しい")
    if re.search(r"^!", log, re.M):
        err("LaTeX エラーがある")
        for line in re.findall(r"^!.*", log, re.M)[:5]:
            print(f"      {line}")
    else:
        ok("LaTeX エラーなし")
    for pat, name in [(r"Reference.*undefined", "未定義参照"),
                      (r"Citation.*undefined", "未定義引用"),
                      (r"multiply defined", "重複ラベル"),
                      (r"Overfull \\hbox", "オーバーフル")]:
        n = len(re.findall(pat, log))
        if n:
            err(f"{name}: {n} 件")
        else:
            ok(f"{name}: 0")


def check_ref_types(typ):
    print("\n[2] 参照の型（部・章・節の取り違え）")
    n = 0
    for f in TEX + [os.path.join(SRC, "book.tex")]:
        for i, line in enumerate(open(f, encoding="utf-8"), 1):
            for m in re.finditer(r"第\\ref\{([^}]+)\}(部|章|節)", line):
                t = typ.get(m.group(1))
                if t and t != m.group(2):
                    err(f"{os.path.basename(f)}:{i} {m.group(1)} を「{m.group(2)}」→ 実際は「{t}」")
                    n += 1
    if not n:
        ok("型不整合なし")


def check_forward(num):
    """第 n 章から第 m 章（m>n）を過去形で参照していないか。

    ch_theory.tex は第1章から第9章までを含むため、
    ファイル内の位置から章番号を推定する必要がある。
    """
    print("\n[3] 過去形の前方参照")
    n = 0
    for name, base in build_order():
        f = os.path.join(SRC, name)
        if not os.path.exists(f):
            continue
        lines = open(f, encoding="utf-8").readlines()
        # ファイル内の \chapter 出現位置から、各行がどの章に属するかを決める
        cur = base
        for i, line in enumerate(lines, 1):
            if re.match(r"\\chapter\{", line):
                # 直後の \label から章番号を引く
                for j in range(i, min(i + 3, len(lines))):
                    m = re.search(r"\\label\{([^}]+)\}", lines[j - 1])
                    if m and m.group(1) in num:
                        cur = num[m.group(1)]
                        break
                else:
                    cur += 1
            for m in re.finditer(r"\\ref\{([^}]+)\}", line):
                t = num.get(m.group(1))
                if t and t > cur and PAST.search(line):
                    err(f"{name}:{i} 第{cur}章 → 第{t}章 を過去形で参照")
                    n += 1
    if not n:
        ok("前方参照なし")


def check_orphans():
    print("\n[4] 未参照・未引用")
    defs, refs = set(), set()
    for f in TEX:
        s = open(f, encoding="utf-8").read()
        pat = (r"\\begin\{(proposition|corollary|remark|example|definition)\}"
               r"(?:\[[^\]]*\])?\s*\n?\\label\{([^}]+)\}")
        for m in re.finditer(pat, s):
            defs.add(m.group(2))
        for m in re.finditer(r"\\ref\{((?:prop|cor|rem|ex|def)[^}]*)\}", s):
            refs.add(m.group(1))
    un = sorted(defs - refs)
    if un:
        err(f"未参照の命題等: {un}")
    else:
        ok("命題等はすべて参照されている")

    ap = os.path.join(SRC, "appendix.tex")
    bib = set(re.findall(r"\\bibitem\{([^}]+)\}", open(ap, encoding="utf-8").read()))
    cited = set()
    for f in TEX:
        for m in re.finditer(r"\\cite\{([^}]+)\}", open(f, encoding="utf-8").read()):
            cited |= {x.strip() for x in m.group(1).split(",")}
    unc = sorted(bib - cited)
    if unc:
        err(f"未引用の文献: {unc}")
    else:
        ok(f"文献 {len(bib)} 件すべて引用されている")


def check_narration():
    print("\n[5] 本文に経緯が混入していないか")
    pat = re.compile(r"(草稿段階|草案では|議論の途上|誤りであった|不正確であった)")
    n = 0
    for f in TEX:
        if os.path.basename(f) == "app_revisions.tex":
            continue
        for i, line in enumerate(open(f, encoding="utf-8"), 1):
            if pat.search(line):
                err(f"{os.path.basename(f)}:{i} {line.strip()[:50]}")
                n += 1
    if not n:
        ok("経緯の混入なし")


def check_pdf():
    print("\n[6] PDF の体裁")
    pdf = os.path.join(SRC, "book.pdf")
    if not os.path.exists(pdf):
        err("book.pdf がない")
        return
    try:
        out = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                             capture_output=True).stdout.decode("utf-8", "replace")
    except FileNotFoundError:
        print("      pdftotext がないため省略")
        return
    pages = out.split("\f")
    blank = [i + 1 for i, p in enumerate(pages) if len(p.strip()) < 6]
    # 末尾の 1 ページは pdftotext の仕様で必ず空になる
    blank = [p for p in blank if p < len(pages)]
    if blank:
        err(f"白紙ページ: {blank}")
    else:
        ok(f"白紙なし（全 {len(pages) - 1} ページ）")

    # 20 行を超える表はページ下端で切れる恐れがある
    long_tables = []
    for f in TEX:
        s = open(f, encoding="utf-8").read()
        for env in ("tabularx", "tabular"):
            for m in re.finditer(
                    r"\\begin\{" + env + r"\}(?:\{[^}]*\})?\{[^}]*\}(.*?)\\end\{" + env + r"\}",
                    s, re.S):
                rows = [r for r in m.group(1).split(r"\\") if "&" in r]
                if len(rows) >= 18:
                    line = s[:m.start()].count("\n") + 1
                    long_tables.append(f"{os.path.basename(f)}:{line} ({len(rows)}行)")
    if long_tables:
        print(f"  --  長い表（要確認）: {long_tables}")
    else:
        ok("18行を超える表なし")


def main():
    print("=" * 56)
    print("BizModel-Formalism 整合性検査")
    print("=" * 56)
    typ, num = load_labels()
    check_log()
    check_ref_types(typ)
    check_forward(num)
    check_orphans()
    check_narration()
    check_pdf()
    print("\n" + "=" * 56)
    print("すべて通過" if not fail else "問題あり")
    sys.exit(fail)


if __name__ == "__main__":
    main()
