# 人材サービス総合サイト 詳細検索の結果一覧（手貼りテキスト）を読む。
#
# 【形式】UTF-8 / CRLF。1レコード＝4行（＋認定表示があれば追加行）。
#   1行目  許可・受理番号
#   2行目  許可年月日 TAB 事業主氏名
#   3行目  事業所名称 TAB 事業所所在地
#   4行目  電話 TAB 就職者(4ヶ月以上有期及び無期) TAB うち無期 TAB 4ヶ月未満有期(人日)
#          TAB 離職者数(無期・6ヶ月以内) TAB 職種 TAB 手数料実績率 TAB 離職率 TAB 備考
#   レコード間に大量の空行が入る。
#   許可番号の記号は ユ（有料）・ム（無料職業紹介所）・特 の三種。
#
# 【検証】データ行（タブ7個以上の行）の本数は「検索結果 N 件」と完全に一致する。
#   すなわち複写による脱落はない。抽出漏れが出たら正規表現を疑うこと。
#
# 【重要】行は事業所単位だが、就職者数・離職率・手数料は許可番号（企業）単位の値が
#   全事業所に複製されている。名寄せしないと支店の多い企業が重複して効く。
#   例：株式会社パソナ（13-ユ-010444）は医師・全国で 134 行を占める。
#
# 【注意】表示される離職率は、同じ行の就職者数・離職者数から計算できない。
#   一致するのは 471 行中 115 行のみで、両者は期間が異なる。
#   離職率はサイト側の集計値として扱う。
import io, os, re, sys, json

# 許可番号の記号は ユ（有料）だけでなく ム（無料職業紹介所）と 特 がある。
# [ユフ] に限ると無料職業紹介所を取りこぼす。
PAT = re.compile(r'^\s*\d{2}-.-\d{6}\s*$')

def num(x, default=None):
    x = x.strip().replace(",", "")
    return default if x in ("", "-", "－") else float(x)

def parse(path, missing_as_zero=True):
    """1ファイルを読み、許可番号で名寄せした企業単位のリストを返す。"""
    lines = io.open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    idx = [i for i, l in enumerate(lines) if PAT.match(l)]
    hits = re.search(r'検索結果\s*([\d,]+)\s*件', "\n".join(lines[:10]))
    declared = int(hits.group(1).replace(",", "")) if hits else None
    firms, rows = {}, 0
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(lines)
        body = [l for l in lines[i:j] if l.strip()]
        dat = [l for l in body if l.count("\t") >= 7]
        if not dat:
            continue
        f = [x.strip() for x in dat[-1].split("\t")]
        rows += 1
        p = body[0].strip()
        to = f[7].replace("％", "").strip()
        d = 0.0 if missing_as_zero else None
        firms.setdefault(p, dict(
            permit=p, pref=p[:2], kind=p.split("-")[1],
            firm=body[1].split("\t")[-1] if "\t" in body[1] else "",
            emp_all=num(f[1], d), emp=num(f[2], d), spot=num(f[3], d), sep=num(f[4], d),
            job=f[5], fee_raw=f[6],
            fee_pct=(float(f[6].replace("％", "").replace(",", "")) if "％" in f[6] else None),
            fee_yen=(float(f[6].replace("円", "").replace(",", "")) if "円" in f[6] else None),
            to=(None if to in ("-", "－", "") else float(to)),
            yuryo=any("優良" in l for l in body),
            nintei=any("適正" in l for l in body),
            branches=0))
        firms[p]["branches"] += 1
    return dict(path=os.path.basename(path), declared=declared, rows=rows,
                lost=(declared - rows if declared else None), firms=list(firms.values()))

if __name__ == "__main__":
    out = []
    for path in sys.argv[1:]:
        r = parse(path)
        out.append(r)
        print("%-28s 宣言 %s 件 / 抽出 %d 行 / 欠損 %s 行 / 名寄せ後 %d 社"
              % (r["path"], r["declared"], r["rows"], r["lost"], len(r["firms"])))
        F = r["firms"]
        print("    ％表示 %d 社 / 円表示 %d 社 / 未掲載 %d 社 / 離職率あり %d 社"
              % (sum(1 for x in F if x["fee_pct"] is not None),
                 sum(1 for x in F if x["fee_yen"] is not None),
                 sum(1 for x in F if x["fee_raw"].strip() in ("-", "－", "")),
                 sum(1 for x in F if x["to"] is not None)))
        top = sorted(F, key=lambda x: -x["branches"])[:3]
        print("    事業所数の多い企業:", [(x["firm"], x["branches"]) for x in top])
    if out:
        D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived")
        os.makedirs(D, exist_ok=True)
        json.dump(out, open(os.path.join(D, "jinzai_search.json"), "w", encoding="utf-8"), ensure_ascii=False)
        flat = []
        for r in out:
            job = r["firms"][0]["job"] if r["firms"] else r["path"]
            for x in r["firms"]:
                y = dict(x); y["src"] = r["path"]; flat.append(y)
        json.dump(flat, open(os.path.join(D, "jinzai_firms.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("→ derived/jinzai_search.json（ファイル単位）")
        print("→ derived/jinzai_firms.json（企業単位 %d 件）" % len(flat))
