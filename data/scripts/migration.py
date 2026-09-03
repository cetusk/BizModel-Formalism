import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
E={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"E.json"))}
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"Bm.json"))}
B={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"B.json"))}
IND="全産業（除く金融保険業）"
tiers=[("10億円以上","10億~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千~1億"),("2千万円以上 - 5千万円未満","2千~5千万"),
 ("1千万円以上 - 2千万円未満","1千~2千万"),("1千万円未満","1千万未満")]
print("=== 階層別 売上高・資産合計の推移（全産業）===")
print("階層移動があれば、各階層の売上高が個別企業の成長と乖離する")
print(f"{'規模':<11}{'売上高 2015':>12}{'2024':>12}{'年率':>8}{'資産 2015':>12}{'2024':>12}{'年率':>8}")
print("-"*72)
for t,lbl in tiers:
    s0=Bm.get((IND,t,2015),{}).get("売上高"); s1=Bm.get((IND,t,2024),{}).get("売上高")
    a0=E.get((IND,t,2015),{}).get("資産合計"); a1=E.get((IND,t,2024),{}).get("資産合計")
    if not all([s0,s1,a0,a1]): continue
    gs=((s1/s0)**(1/9)-1)*100; ga=((a1/a0)**(1/9)-1)*100
    print(f"{lbl:<11}{s0/1e6:>11.1f}兆{s1/1e6:>11.1f}兆{gs:>7.1f}%{a0/1e6:>11.1f}兆{a1/1e6:>11.1f}兆{ga:>7.1f}%")
print()
print("=== I/r の年次推移（土地除く、全産業）===")
def fa(x): return (x["有形固定資産"] or 0)+(x["無形固定資産"] or 0)-(x["土地"] or 0)
print(f"{'規模':<11}"+"".join(f"{y:>7}" for y in range(2016,2025)))
print("-"*74)
import statistics as st
for t,lbl in tiers:
    row=f"{lbl:<11}"; vals=[]
    for y in range(2016,2025):
        k=(IND,t,y); kp=(IND,t,y-1)
        if k in E and kp in E and k in Bm:
            s=Bm[k]["売上高"]; dep=E[k]["減価償却費"] or 0
            v=(fa(E[k])-fa(E[kp])+dep)/s*100; vals.append(v)
            row+=f"{v:>7.1f}"
        else: row+=f"{'--':>7}"
    row+=f"   平均{st.mean(vals):>5.1f}  SD{st.stdev(vals):>5.1f}"
    print(row)
