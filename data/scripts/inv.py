# 棚卸資産の範囲が CCC と弾力性に与える影響。
#
# 本文の DIO は「製品又は商品」のみを用いており、仕掛品と原材料を含まない。
# 「棚卸資産（当期末）」は総額であるから、差が過小計上の大きさになる。
# derived/B.json（受取手形・売掛金・製品又は商品・支払手形・買掛金・売上高）と
# derived/E.json（棚卸資産）を業種×規模×年で突き合わせる。
#
# 弾力性の比較は必ず共通標本で行う。定義ごとに W>0 の観測が異なるため、
# 別々の標本で比べると符号が逆に出る。
import json, os, math, statistics as st

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
B = json.load(open(D + "B.json"))
E = json.load(open(D + "E.json"))
inv = {(r["ind"], r["size"], r["year"]): r["棚卸資産"] for r in E}

rows = []
for r in B:
    s, iv = r["売上高"], inv.get((r["ind"], r["size"], r["year"]))
    if not s or s <= 0 or iv is None: continue
    if any(r[k] is None for k in ("受取手形", "売掛金", "製品又は商品", "支払手形", "買掛金")): continue
    dso = (r["受取手形"] + r["売掛金"]) / s * 365
    dpo = (r["支払手形"] + r["買掛金"]) / s * 365
    rows.append(dict(ind=r["ind"], size=r["size"], year=r["year"], r=s, dso=dso, dpo=dpo,
                     dio_n=r["製品又は商品"] / s * 365, dio_f=iv / s * 365,
                     ccc_n=dso + r["製品又は商品"] / s * 365 - dpo,
                     ccc_f=dso + iv / s * 365 - dpo))

print("突合 %d 件（業種 %d × 規模 %d × 年 %d）" % (len(rows), len({r["ind"] for r in rows}),
      len({r["size"] for r in rows}), len({r["year"] for r in rows})))

print("\n【水準】")
print("  DIO 差   中央値 %.1f 日 / 平均 %.1f 日 / 最大 %.1f 日"
      % (st.median([r["dio_f"] - r["dio_n"] for r in rows]),
         st.mean([r["dio_f"] - r["dio_n"] for r in rows]),
         max(r["dio_f"] - r["dio_n"] for r in rows)))
rt = [r["dio_f"] / r["dio_n"] for r in rows if r["dio_n"] > 0.5]
print("  DIO 倍率 中央値 %.2f 倍 / 平均 %.2f 倍" % (st.median(rt), st.mean(rt)))
print("  CCC 中央値 %.1f 日 → %.1f 日" % (st.median([r["ccc_n"] for r in rows]),
                                        st.median([r["ccc_f"] for r in rows])))

print("\n【水準】業種別（全規模・2024年度）")
print("  %-22s %8s %8s %8s %8s" % ("業種", "DIO製品", "DIO棚卸", "CCC製品", "CCC棚卸"))
for r in sorted([x for x in rows if x["size"] == "全規模" and x["year"] == 2024],
                key=lambda x: -(x["dio_f"] - x["dio_n"])):
    print("  %-22s %8.1f %8.1f %8.1f %8.1f" % (r["ind"], r["dio_n"], r["dio_f"], r["ccc_n"], r["ccc_f"]))

key = {}
for r in rows: key.setdefault((r["ind"], r["size"]), {})[r["year"]] = r

def corr(a, b):
    n = len(a); ma, mb = st.mean(a), st.mean(b)
    sa = st.pstdev(a); sb = st.pstdev(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n * sa * sb)

dn = [];  df = []
for k, ys in key.items():
    for y in sorted(ys):
        if y - 1 in ys:
            dn.append(ys[y]["ccc_n"] - ys[y - 1]["ccc_n"])
            df.append(ys[y]["ccc_f"] - ys[y - 1]["ccc_f"])
sgn = [(a, b) for a, b in zip(dn, df) if a * b != 0]
print("\n【差分】ΔCCC（%d 観測）" % len(dn))
print("  corr = %.3f / 符号一致 %.1f%% / SD %.2f → %.2f 日"
      % (corr(dn, df), 100 * sum(1 for a, b in sgn if a * b > 0) / len(sgn), st.pstdev(dn), st.pstdev(df)))

def ols(xs, ys):
    n = len(xs); mx, my = st.mean(xs), st.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)); sxx = sum((x - mx) ** 2 for x in xs)
    b = sxy / sxx
    return b, sxy ** 2 / (sxx * sum((y - my) ** 2 for y in ys))

# scripts/elast.py と同じく集約系列は除く
AGG = {"全産業（除く金融保険業）", "製造業"}

def elast(sizes):
    P = []
    for k, ys in key.items():
        if k[1] not in sizes or k[0] in AGG: continue
        for y in sorted(ys):
            if y - 1 not in ys: continue
            a, b = ys[y - 1], ys[y]
            Wn = (a["ccc_n"] * a["r"], b["ccc_n"] * b["r"])
            Wf = (a["ccc_f"] * a["r"], b["ccc_f"] * b["r"])
            if min(Wn + Wf) <= 0: continue           # 共通標本
            P.append((math.log(b["r"] / a["r"]), math.log(Wn[1] / Wn[0]), math.log(Wf[1] / Wf[0])))
    xs = [p[0] for p in P]
    return len(P), ols(xs, [p[1] for p in P]), ols(xs, [p[2] for p in P])

for sizes, lab in [(None, "全11規模階層・集約系列を除く8業種")]:
    ss = sizes or {r["size"] for r in rows}
    n, (bn, r2n), (bf, r2f) = elast(ss)
    print("\n【弾力性 β = Δln W / Δln r】%s  共通標本 n = %d" % (lab, n))
    print("  製品又は商品のみ  β = %.3f  R2 = %.3f  分母効果 1-β = %.3f" % (bn, r2n, 1 - bn))
    print("  棚卸資産（総額）  β = %.3f  R2 = %.3f  分母効果 1-β = %.3f" % (bf, r2f, 1 - bf))
