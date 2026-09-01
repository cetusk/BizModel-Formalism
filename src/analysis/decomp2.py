import json
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open("Bm.json"))}
def d(r):
    s=r["売上高"]
    return (1-r["売上原価"]/s, r["販売費及び一般管理費"]/s, r["営業利益"]/s)
inds=sorted({k[0] for k in Bm})
print("=== 業種内での大小比較（2024年度）: 10億円以上 vs 1千万円未満 ===")
print(f"{'業種':<26}{'粗利率':>16}{'販管費率':>16}{'営業利益率':>16}")
print(f"{'':<26}{'大':>7}{'小':>8}{'大':>8}{'小':>8}{'大':>8}{'小':>8}")
print("-"*76)
agg=[]
for ind in inds:
    a=Bm.get((ind,"10億円以上",2024)); b=Bm.get((ind,"1千万円未満",2024))
    if not a or not b: continue
    ga,sa,oa=d(a); gb,sb,ob=d(b)
    agg.append((gb-ga, sb-sa, ob-oa))
    print(f"{ind[:25]:<26}{ga*100:>7.1f}{gb*100:>8.1f}{sa*100:>8.1f}{sb*100:>8.1f}{oa*100:>8.1f}{ob*100:>8.1f}")
import statistics as st
print("-"*76)
print(f"{'小-大 の平均差(pt)':<26}{st.mean(x[0] for x in agg):>15.1f}{st.mean(x[1] for x in agg):>16.1f}{st.mean(x[2] for x in agg):>16.1f}")
n=len(agg)
print(f"\n業種数 {n}: 粗利率が小>大 の業種 {sum(1 for x in agg if x[0]>0)}/{n}")
print(f"         販管費率が小>大 の業種 {sum(1 for x in agg if x[1]>0)}/{n}")
print(f"         営業利益率が小>大 の業種 {sum(1 for x in agg if x[2]>0)}/{n}")
