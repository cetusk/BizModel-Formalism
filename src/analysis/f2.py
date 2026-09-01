import json
def m(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return (ar-ap)/s*365, (ar+(r["製品又は商品"] or 0)-ap)/s*365
B=json.load(open("B.json"))
tiers=["10億円以上","1億円以上 - 10億円未満","5千万円以上 - 1億円未満",
       "2千万円以上 - 5千万円未満","1千万円以上 - 2千万円未満","1千万円未満"]
print("=== DSO-DPO（正=与信の出し手）全産業 時系列 ===")
print(f"{'規模':<22}"+"".join(f"{y:>7}" for y in range(2015,2025)))
print("-"*92)
for t in tiers:
    line=f"{t:<22}"
    for y in range(2015,2025):
        r=[x for x in B if x["ind"]=="全産業（除く金融保険業）" and x["size"]==t and x["year"]==y]
        v=m(r[0]) if r else None
        line+=f"{v[0]:>7.0f}" if v else f"{'--':>7}"
    print(line)
print()
print("=== 2024年度 業種別 DSO-DPO：最大規模 vs 最小規模 ===")
print(f"{'業種':<28}{'10億円以上':>11}{'1千万円未満':>12}{'差':>8}")
print("-"*60)
for ind in sorted({x["ind"] for x in B}):
    a=[x for x in B if x["ind"]==ind and x["size"]=="10億円以上" and x["year"]==2024]
    b=[x for x in B if x["ind"]==ind and x["size"]=="1千万円未満" and x["year"]==2024]
    if not a or not b: continue
    va,vb=m(a[0]),m(b[0])
    if not va or not vb: continue
    print(f"{ind:<28}{va[0]:>11.0f}{vb[0]:>12.0f}{va[0]-vb[0]:>8.0f}")
