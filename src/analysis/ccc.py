import json
def ccc(r):
    s=r["売上高"]
    if not s or s<=0: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0)
    ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    inv=r["製品又は商品"] or 0
    if r["売掛金"] is None or r["買掛金"] is None: return None
    return dict(DSO=ar/s*365, DIO=inv/s*365, DPO=ap/s*365, CCC=(ar+inv-ap)/s*365,
                NET=(ar-ap)/s*365, sales=s)
B=json.load(open("B.json"))
order=["10億円以上","5億円以上 - 10億円未満","1億円以上 - 5億円未満","5千万円以上 - 1億円未満",
 "2千万円以上 - 5千万円未満","1千万円以上 - 2千万円未満","1千万円未満","2百万円以上 - 5百万円未満",
 "5百万円以上 - 1千万円未満","2百万円未満","全規模"]
sizes=sorted({r["size"] for r in B})
print("規模階層:", sizes); print()
rows=[r for r in B if r["ind"]=="全産業（除く金融保険業）" and r["year"]==2024]
print("=== 全産業（除く金融保険業） 2024年度 ===")
print(f"{'規模':<26}{'DSO':>7}{'DIO':>7}{'DPO':>7}{'CCC':>8}{'DSO-DPO':>9}")
print("-"*66)
out=[]
for r in rows:
    c=ccc(r)
    if c: out.append((r["size"],c))
def key(s):
    try: return order.index(s)
    except: return 99
for s,c in sorted(out,key=lambda x:key(x[0])):
    print(f"{s:<26}{c['DSO']:>7.0f}{c['DIO']:>7.0f}{c['DPO']:>7.0f}{c['CCC']:>8.0f}{c['NET']:>9.0f}")
