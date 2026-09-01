import json, statistics as st
E={(r["ind"],r["size"],r["year"]):r for r in json.load(open("E.json"))}
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open("Bm.json"))}
B={(r["ind"],r["size"],r["year"]):r for r in json.load(open("B.json"))}
def fa(x): return (x["有形固定資産"] or 0)+(x["無形固定資産"] or 0)-(x["土地"] or 0)
def ccc(k):
    r=B.get(k)
    if not r: return None
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return (ar+(r["製品又は商品"] or 0)-ap)/s*365
inds=sorted({k[0] for k in E})
print("=== 業種別（全規模）I/r と g* の安定性 2016-2024 ===")
print(f"{'業種':<24}{'I/r平均':>8}{'SD':>6}{'g*(2024)':>10}{'g*平均':>9}{'g*SD':>7}")
print("-"*66)
for ind in inds:
    irs=[];gs=[]
    for y in range(2016,2025):
        k=(ind,"全規模",y); kp=(ind,"全規模",y-1)
        if k not in E or kp not in E or k not in Bm: continue
        s=Bm[k]["売上高"]; c=ccc(k)
        if not s or s<=0 or not c or c<=0: continue
        dep=E[k]["減価償却費"] or 0
        ir=(fa(E[k])-fa(E[kp])+dep)/s
        m=(Bm[k]["営業利益"] or 0)/s; d=dep/s
        irs.append(ir*100); gs.append((m+d-ir)/(c/365)*100)
    if len(irs)<5: continue
    print(f"{ind[:23]:<24}{st.mean(irs):>7.1f}%{st.stdev(irs):>6.1f}{gs[-1]:>9.1f}%{st.mean(gs):>8.1f}%{st.stdev(gs):>6.1f}")
print()
print("=== 比較：規模階層別の SD（全産業）===")
tiers=[("10億円以上","10億~"),("1億円以上 - 10億円未満","1~10億"),
 ("1千万円以上 - 2千万円未満","1千~2千万"),("1千万円未満","1千万未満")]
for t,lbl in tiers:
    irs=[]
    for y in range(2016,2025):
        k=("全産業（除く金融保険業）",t,y); kp=("全産業（除く金融保険業）",t,y-1)
        if k in E and kp in E and k in Bm:
            s=Bm[k]["売上高"]; dep=E[k]["減価償却費"] or 0
            irs.append((fa(E[k])-fa(E[kp])+dep)/s*100)
    print(f"  {lbl:<10} I/r SD = {st.stdev(irs):.1f}")
