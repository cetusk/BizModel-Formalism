"""raw/hojin の CSV を derived/*.json に変換する。

e-Stat の時系列データは表頭が複数行にわたるため、
「業種...コード」で始まる行を探して項目名の開始位置を決める。
文字コードは CP932。

    cd data/scripts && python3 parse.py

derived/ は git 管理外である。クローン後は必ずこれを実行する。
"""
import csv, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "..", "raw", "hojin")
DER = os.path.join(BASE, "..", "derived")

# (出力名, 入力CSV, 内容)
TABLES = [
    ("A",  "A_old_predE.csv",         "62業種×全規模。受取手形・売掛金・製品又は商品・支払手形・買掛金・売上高"),
    ("B",  "B_old_predF.csv",         "10業種×11規模。同上"),
    ("Am", "A_gyoshu_jikeiretsu.csv", "62業種×全規模。売上高・売上原価・販管費・営業利益"),
    ("Bm", "B_kibo_dammen.csv",       "10業種×11規模。同上"),
    ("C",  "C_jinkenhi.csv",          "役員給与・役員賞与・従業員給与・従業員賞与"),
    ("E",  "E_genka_setsubi.csv",     "減価償却費・棚卸資産・固定資産ほか"),
]

NA = ("", "-", "*", "***", "x")


def load(path):
    with open(path, encoding="cp932", errors="replace") as f:
        lines = list(csv.reader(f))
    hdr = next(i for i, r in enumerate(lines)
               if r and r[0].startswith("業種") and "コード" in r[0])
    names = [re.sub(r"\(.*?\)|【.*?】", "", c).strip() for c in lines[hdr][10:]]
    rows = []
    for r in lines[hdr + 1:]:
        if len(r) < 11 or not r[0].strip():
            continue
        rec = {"ind_code": r[0], "ind": r[2], "size_code": r[3],
               "size": r[5], "year": int(r[6][:4])}
        for n, v in zip(names, r[10:10 + len(names)]):
            v = v.replace(",", "").strip()
            rec[n] = None if v in NA else float(v)
        rows.append(rec)
    return rows, names


if __name__ == "__main__":
    os.makedirs(DER, exist_ok=True)
    for tag, fn, note in TABLES:
        path = os.path.join(RAW, fn)
        if not os.path.exists(path):
            print("  %-3s %s がない" % (tag, fn))
            continue
        rows, names = load(path)
        yrs = [r["year"] for r in rows]
        print("  %-3s %5d行  業種%3d  規模%2d  %d-%d  %s"
              % (tag, len(rows), len({r["ind"] for r in rows}),
                 len({r["size"] for r in rows}), min(yrs), max(yrs), note))
        print("      項目: %s" % names)
        json.dump(rows, open(os.path.join(DER, tag + ".json"), "w"),
                  ensure_ascii=False)
