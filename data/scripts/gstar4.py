import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json, statistics as st
E={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"E.json"))}
B={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"B.json"))}
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"Bm.json"))}
def ccc(k):
    r=B.get(k)
    if not r: return None
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return (ar+(r["製品又は商品"] or 0)-ap)/s*365
def fa(x): return (x["有形固定資産"] or 0)+(x["無形固定資産"] or 0)-(x["土地"] or 0)
def stats(ind,size,y):
    k=(ind,size,y); kp=(ind,size,y-1)
    if k not in E or kp not in E or k not in Bm: return None
    e,ep,b=E[k],E[kp],Bm[k]; s=b["売上高"]
    if not s or s<=0: return None
    dep=e["減価償却費"] or 0
    return dict(m=(b["営業利益"] or 0)/s, d=dep/s, I_r=(fa(e)-fa(ep)+dep)/s, ccc=ccc(k))
tiers=[("10億円以上","10億~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千~1億"),("2千万円以上 - 5千万円未満","2千~5千万"),
 ("1千万円以上 - 2千万円未満","1千~2千万"),("1千万円未満","1千万未満")]
IND="全産業（除く金融保険業）"
print("=== 土地を除いた I による g*（全産業）===")
print(f"{'規模':<11}{'CCC':>6}{'m':>7}{'d':>7}{'I/r':>7}{'旧g*':>8}{'新g*':>8}{'9年平均g*':>11}")
print("-"*66)
for t,lbl in tiers:
    v=stats(IND,t,2024)
    if not v or not v['ccc']: continue
    old=v['m']/(v['ccc']/365)*100
    new=(v['m']+v['d']-v['I_r'])/(v['ccc']/365)*100
    # 9年平均で単年変動をならす。原データは2015〜2024の10年あるが、
    # I の算出に前年の固定資産が要る（fa(e)-fa(ep)）ため 2015 は計算できず、
    # 平均を取れるのは 2016〜2024 の9年になる。
    gs=[]
    for y in range(2016,2025):
        w=stats(IND,t,y)
        if w and w['ccc'] and w['ccc']>0: gs.append((w['m']+w['d']-w['I_r'])/(w['ccc']/365)*100)
    print(f"{lbl:<11}{v['ccc']:>6.0f}{v['m']*100:>6.1f}%{v['d']*100:>6.1f}%{v['I_r']*100:>6.1f}%{old:>7.1f}%{new:>7.1f}%{st.mean(gs):>10.1f}%")
print()
print("=== 業種別（全規模、2024）土地除く ===")
print(f"{'業種':<26}{'CCC':>6}{'m+d-I/r':>10}{'旧g*':>8}{'新g*':>8}")
print("-"*60)
for ind in sorted({k[0] for k in E}):
    v=stats(ind,"全規模",2024)
    if not v or not v['ccc'] or v['ccc']<=0: continue
    print(f"{ind[:25]:<26}{v['ccc']:>6.0f}{(v['m']+v['d']-v['I_r'])*100:>9.1f}%{v['m']/(v['ccc']/365)*100:>7.1f}%{(v['m']+v['d']-v['I_r'])/(v['ccc']/365)*100:>7.1f}%")
