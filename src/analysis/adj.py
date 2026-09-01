import json, statistics as st
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open("Bm.json"))}
C ={(r["ind"],r["size"],r["year"]):r for r in json.load(open("C.json"))}
def calc(k):
    b=Bm.get(k); c=C.get(k)
    if not b or not c: return None
    s=b["売上高"]
    if not s or s<=0: return None
    hr=sum(c[x] or 0 for x in ["役員給与","役員賞与","従業員給与","従業員賞与"])
    return dict(g=1-b["売上原価"]/s, sga=b["販売費及び一般管理費"]/s, op=b["営業利益"]/s,
                hr=hr/s, gadj=1-(b["売上原価"]+hr)/s, sadj=(b["販売費及び一般管理費"]-hr)/s)
tiers=[("10億円以上","10億円~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千万~1億"),("2千万円以上 - 5千万円未満","2千万~5千万"),
 ("1千万円以上 - 2千万円未満","1千万~2千万"),("1千万円未満","1千万未満")]
print("=== 全産業 2024年度：人件費調整の前後 ===")
print(f"{'規模':<12}{'人件費率':>9}{'粗利率':>8}{'調整後':>8}{'販管費率':>9}{'調整後':>8}{'営業利益率':>10}")
print("-"*66)
for t,lbl in tiers:
    r=calc(("全産業（除く金融保険業）",t,2024))
    if r: print(f"{lbl:<12}{r['hr']*100:>8.1f}%{r['g']*100:>7.1f}%{r['gadj']*100:>7.1f}%{r['sga']*100:>8.1f}%{r['sadj']*100:>7.1f}%{r['op']*100:>9.1f}%")
print()
print("=== 業種内 大vs小（2024）：調整後粗利率の差 小-大 ===")
inds=[i for i in sorted({k[0] for k in Bm}) if i!="全産業（除く金融保険業）"]
d_raw=[];d_adj=[];d_hr=[]
print(f"{'業種':<24}{'人件費率(大/小)':>18}{'粗利差':>9}{'調整後粗利差':>13}")
for ind in inds:
    a=calc((ind,"10億円以上",2024)); b=calc((ind,"1千万円未満",2024))
    if not a or not b: continue
    d_raw.append((b['g']-a['g'])*100); d_adj.append((b['gadj']-a['gadj'])*100)
    d_hr.append((b['hr']-a['hr'])*100)
    print(f"{ind[:23]:<24}{a['hr']*100:>9.1f}{b['hr']*100:>8.1f}{(b['g']-a['g'])*100:>9.1f}{(b['gadj']-a['gadj'])*100:>13.1f}")
print("-"*66)
print(f"{'平均':<24}{'':>9}{'':>8}{st.mean(d_raw):>9.1f}{st.mean(d_adj):>13.1f}")
print(f"\n人件費率の差(小-大) 平均 {st.mean(d_hr):+.1f}pt")
print(f"調整後も粗利率が小>大 の業種: {sum(1 for x in d_adj if x>0)}/{len(d_adj)}")
