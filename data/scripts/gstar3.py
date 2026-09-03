import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
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
tiers=[("10億円以上","10億~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千~1億"),("2千万円以上 - 5千万円未満","2千~5千万"),
 ("1千万円以上 - 2千万円未満","1千~2千万"),("1千万円未満","1千万未満")]
IND="全産業（除く金融保険業）"
print("=== I の推定方法による違い（全産業 2024）===")
print(f"{'規模':<11}{'含土地':>8}{'除土地':>8}{'除土地建仮':>11}{'資産合計伸び':>12}")
print("-"*52)
for t,lbl in tiers:
    k=(IND,t,2024); kp=(IND,t,2023)
    if k not in E or kp not in E: continue
    e,ep=E[k],E[kp]; s=Bm[k]["売上高"]
    dep=e["減価償却費"] or 0
    def fa(x, land=True, cip=True):
        v=(x["有形固定資産"] or 0)+(x["無形固定資産"] or 0)
        if not land: v-= (x["土地"] or 0)
        if not cip:  v-= (x["建設仮勘定"] or 0)
        return v
    I1=fa(e)-fa(ep)+dep
    I2=fa(e,land=False)-fa(ep,land=False)+dep
    I3=fa(e,land=False,cip=False)-fa(ep,land=False,cip=False)+dep
    growth=(e["資産合計"]/ep["資産合計"]-1)*100
    print(f"{lbl:<11}{I1/s*100:>7.1f}%{I2/s*100:>7.1f}%{I3/s*100:>10.1f}%{growth:>11.1f}%")
print()
print("=== 階層移動の検証：各階層の資産合計と社数の推移 ===")
print(f"{'規模':<11}{'2023資産':>12}{'2024資産':>12}{'増減率':>9}")
print("-"*46)
for t,lbl in tiers:
    k=(IND,t,2024); kp=(IND,t,2023)
    if k not in E or kp not in E: continue
    a0=E[kp]["資産合計"]; a1=E[k]["資産合計"]
    print(f"{lbl:<11}{a0/1e6:>11.1f}兆{a1/1e6:>11.1f}兆{(a1/a0-1)*100:>8.1f}%")
