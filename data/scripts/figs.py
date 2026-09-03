import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
def calc(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return dict(CCC=(ar+(r["製品又は商品"] or 0)-ap)/s*365, NET=(ar-ap)/s*365,
                DSO=ar/s*365, DPO=ap/s*365, sales=s)

# --- 図1: 規模別 DSO/DPO/正味 (2024, 全産業) ---
B=json.load(open(D+"B.json", encoding="utf-8"))
tiers=[("10億円以上","10億円~"),("1億円以上 - 10億円未満","1~10億円"),
       ("5千万円以上 - 1億円未満","5千万~1億"),("2千万円以上 - 5千万円未満","2千万~5千万"),
       ("1千万円以上 - 2千万円未満","1千万~2千万"),("1千万円未満","1千万未満")]
print("=== FIG1 規模別(全産業,2024) ===")
for t,lbl in tiers:
    r=[x for x in B if x["ind"]=="全産業（除く金融保険業）" and x["size"]==t and x["year"]==2024]
    c=calc(r[0]); print(f"{lbl}\t{c['DSO']:.1f}\t{c['DPO']:.1f}\t{c['NET']:.1f}")

# --- 図2: 業種別 大小比較 (2024) ---
print("\n=== FIG2 業種別 大vs小 (2024) ===")
for ind in ["情報通信業","建設業","製造業","卸売業","職業紹介・労働者派遣業","小売業"]:
    a=[x for x in B if x["ind"]==ind and x["size"]=="10億円以上" and x["year"]==2024]
    b=[x for x in B if x["ind"]==ind and x["size"]=="1千万円未満" and x["year"]==2024]
    if a and b: print(f"{ind}\t{calc(a[0])['NET']:.1f}\t{calc(b[0])['NET']:.1f}")

# --- 図3: 全産業CCCの推移 2000-2024 ---
A=json.load(open(D+"A.json", encoding="utf-8"))
print("\n=== FIG3 全産業CCC推移 ===")
for y in range(2000,2025):
    r=[x for x in A if x["ind"]=="全産業（除く金融保険業）" and x["year"]==y]
    if r: c=calc(r[0]); print(f"{y}\t{c['CCC']:.1f}\t{c['NET']:.1f}")

# --- 図4: 業種別CCC水準 2024 上位下位 ---
print("\n=== FIG4 業種別CCC水準 2024 ===")
out=[]
for x in A:
    if x["year"]!=2024: continue
    if "(集約)" in x["ind"] or "H20年度" in x["ind"]: continue
    c=calc(x)
    if c: out.append((x["ind"],c["CCC"]))
out.sort(key=lambda z:-z[1])
for n,v in out[:6]+[("...",0)]+out[-6:]: print(f"{n}\t{v:.1f}")
