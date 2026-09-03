# 人材サービス総合サイトの「職業紹介事業詳細」ページを読む。
# fetch_jinzai_detail.py が保存した raw/jinzai/detail/*.html を
# derived/jinzai_detail.json にする。
#
# 【一覧との違い】詳細ページは次の三点で検索結果一覧より情報が多い。
#   1. 就職者数・離職者数が令和02年度からの年度別。一覧は最新年度の断面のみ
#   2. 手数料実績率が職業分類の細分類別にも出る。一覧の値は集計後のもの
#   3. 返戻金制度の有無と、その内容を記した PDF へのリンク
#
# 【返戻金】値は「有」「無」「-」の三種。リンクが伴う場合があり二系統ある。
#   /icb_data/UploadFiles/Jigyosho/{許可番号}/henreikin/*.pdf  サイトが保持する PDF
#   http://...                                                 事業者自身のサイト
#   PDF は返戻の率と期間を段階表で書いたものが多いが、画像のみの scan もある。
#
# 【注意】最新年度の離職者数は「-」になる。就職後6ヶ月の観測期間が閉じていないため。
#   0 と区別すること。
import io, os, re, sys, json, html, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "raw", "jinzai", "detail")
OUT  = os.path.join(HERE, "..", "derived", "jinzai_detail.json")
BASE = "https://jinzai.hellowork.mhlw.go.jp"

def T(x):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x))).replace("\xa0", " ").strip()

def num(x):
    x = x.replace(",", "").strip()
    return None if x in ("", "-", "－") else float(x)

def wareki(s):
    """令和02年度 → 2020。平成にも備える。"""
    # 昭和が現れることがある。事業者の届出の誤りだが、そのまま記録する。
    base = {"令和": 2018, "平成": 1988, "昭和": 1925}
    m = re.match(r"(令和|平成|昭和)(\d+)年度", s or "")
    return base[m.group(1)] + int(m.group(2)) if m else None

def parse(path):
    s = io.open(path, encoding="utf-8").read()
    d = {}
    for m in re.finditer(r'<td class="searchDet_title"[^>]*>(.*?)</td>\s*'
                         r'<td class="searchDet_data"[^>]*>(.*?)</td>', s, re.S):
        d[T(m.group(1))] = m.group(2)

    def link(k):
        h = d.get(k, "")
        u = re.search(r'href="([^"]+)"', h)
        u = u.group(1) if u else None
        return T(h) or None, (BASE + u if u and u.startswith("/") else u)

    hen, hen_u = link("返戻金制度")
    fee, fee_u = link("手数料")
    permit = T(d.get("許可・届出受理番号", ""))

    # 年度別のパネル。列は 就職者(4ヶ月以上有期及び無期) / うち無期 /
    # 4ヶ月未満有期(人日) / 離職者数 / 離職が判明せず の順。
    panel = []
    for tb in re.findall(r"<table[^>]*>.*?</table>", s, re.S):
        if "情報登録年度" not in tb:
            continue
        for tr in re.findall(r"<tr.*?</tr>", tb, re.S):
            c = [T(x) for x in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
            y = wareki(c[0]) if c else None
            if y is None or len(c) < 6:
                continue
            panel.append(dict(year=y, emp_all=num(c[1]), emp=num(c[2]),
                              spot=num(c[3]), sep=num(c[4]), sep_unknown=num(c[5])))
        break

    # 職種別の 手数料実績率／離職率。この表は事業所が届け出た全職種を並べる。
    # 一覧に出ていたのは、検索で指定した職種に対応する行の値である。
    # 【重要】手数料実績率と離職率は年度が違う。前者は最新年度、後者はその前年度。
    #   離職率は就職後6ヶ月を観測するため、最新年度は確定しない。
    # 入れ子の table があるため、行の分割は職種の span を目印にする。
    jobs = []
    m = re.search(r"取扱業務の職種別の手数料実績率および離職率(.*?)(?:<h3|</body)", s, re.S)
    if m:
        block = m.group(1)
        parts = re.split(r'<span id="ID_lbShokushu"[^>]*>', block)[1:]
        for q in parts:
            name = T(q.split("</span>")[0])
            # 手数料の欄と離職率の欄は列で決まる。片方が空（「-」）のことがあるので、
            # 出現順で拾うと取り違える。外側の td の class で列を分ける。
            col = q.split('class="searchDet_data_center"')[1:3]
            def cell(x):
                if x is None:
                    return None, None
                m2 = re.search(r"<td[^>]*>\s*((?:令和|平成|昭和)\d+年度)\s*</td>\s*"
                               r"<td[^>]*>\s*([\d.,]+(?:％|円))\s*</td>", x)
                return (m2.group(1), m2.group(2)) if m2 else (None, None)
            fy, fr = cell(col[0] if len(col) > 0 else None)
            ty, tr = cell(col[1] if len(col) > 1 else None)
            jobs.append(dict(job=name, fee_year=wareki(fy), fee_raw=fr,
                             to_year=wareki(ty), to_raw=tr))
    # 職種の細分類別の手数料実績率（「その②」）。離職率は付かない。
    fine = []
    for q in re.finditer(r'<span id="ID_uneiTesuryoShokushu_\d+">(.*?)</span>.*?'
                         r'<span id="ID_uneiTesuryoNendo_\d+">(.*?)</span>.*?'
                         r'<span id="ID_uneiTesuryo_\d+">(.*?)</span>', s, re.S):
        t = T(q.group(1))
        c = re.match(r"(\d{3})\s*(.*)", t)
        fine.append(dict(code=c.group(1) if c else None, name=c.group(2) if c else t,
                         year=wareki(T(q.group(2))), fee_raw=T(q.group(3))))
    bikou = T(d.get("備考", ""))
    return dict(
        permit=permit,
        date=T(d.get("許可届出受理年月日", "")) or None,
        firm=T(d.get("事業主名称", "")) or None,
        office=T(d.get("事業所名称", "")) or None,
        addr=T(d.get("事業所所在地", "")) or None,
        tel=T(d.get("電話番号", "")) or None,
        shokushu=T(d.get("取扱職種", "")) or None,
        chiiki=T(d.get("取扱地域", "")) or None,
        fee_flag=fee, fee_url=fee_u,
        henreikin=hen, henreikin_url=hen_u,
        henreikin_pdf=bool(hen_u and "/icb_data/" in hen_u),
        bikou=bikou or None,
        nintei=("適正" in bikou), yuryo=("優良" in bikou),
        panel=panel, jobs=jobs, fine=fine)

def main():
    rows = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".html"):
            continue
        p = os.path.join(SRC, f)
        if os.path.getsize(p) < 5000:
            sys.stderr.write("  小さすぎる（エラーページ）: %s\n" % f)
            continue
        r = parse(p)
        if r["permit"] != f[:-5]:
            sys.stderr.write("  ★許可番号が不一致: %s → %s\n" % (f, r["permit"]))
            continue
        rows.append(r)
    json.dump(rows, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.stderr.write("  %d 件 → %s\n" % (len(rows), OUT))

if __name__ == "__main__":
    main()
