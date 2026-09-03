import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
def ccc(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return (ar+(r["製品又は商品"] or 0)-ap)/s*365
def marg(r):
    s=r["売上高"]
    if not s or s<=0: return None,None
    gp=(s-(r["売上原価"] or 0))/s
    op=(r["営業利益"] or 0)/s
    return gp,op
A={(r["ind"],r["year"]):r for r in json.load(open(D+"A.json"))}
Am={(r["ind"],r["year"]):r for r in json.load(open(D+"Am.json"))}

print("=== 全産業（除く金融保険業）の時系列 ===")
print(f"{'年度':<7}{'CCC(日)':>9}{'粗利率':>9}{'営業利益率':>11}{'g*(粗利)':>11}{'g*(営業)':>11}")
print("-"*60)
for y in [2000,2005,2010,2015,2020,2024]:
    k=("全産業（除く金融保険業）",y)
    c=ccc(A[k]); gp,op=marg(Am[k])
    gs_g=gp/(c/365)*100; gs_o=op/(c/365)*100
    print(f"{y:<7}{c:>9.1f}{gp*100:>8.1f}%{op*100:>10.1f}%{gs_g:>10.1f}%{gs_o:>10.1f}%")

print("\n=== 2024年度 業種別 g*（営業利益率ベース）===")
out=[]
for (ind,y),r in A.items():
    if y!=2024 or "(集約)" in ind or "H20年度" in ind: continue
    if (ind,y) not in Am: continue
    c=ccc(r); gp,op=marg(Am[(ind,y)])
    if c is None or op is None or c<=0: continue
    out.append((ind,c,op*100,op/(c/365)*100))
out.sort(key=lambda z:z[3])
print(f"{'業種':<28}{'CCC':>7}{'営業利益率':>10}{'g*':>10}")
print("-"*56)
for n,c,o,g in out[:6]: print(f"{n:<28}{c:>7.0f}{o:>9.1f}%{g:>9.1f}%")
print(f"{'...':<28}")
for n,c,o,g in out[-6:]: print(f"{n:<28}{c:>7.0f}{o:>9.1f}%{g:>9.1f}%")
