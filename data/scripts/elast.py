import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json, math, statistics as st
A=json.load(open(D+"A.json", encoding="utf-8"))
def wr(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    W=ar+(r["製品又は商品"] or 0)-ap
    return (W, s) if W>0 else None
def leaf(n): return not ("(集約)" in n or "H20年度" in n or n in
        ("全産業（除く金融保険業）","製造業","非製造業"))
ser={}
for r in A:
    v=wr(r)
    if v and leaf(r["ind"]): ser.setdefault(r["ind"],{})[r["year"]]=v
def ols(x,y):
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    sxx=sum((a-mx)**2 for a in x); sxy=sum((a-mx)*(b-my) for a,b in zip(x,y))
    if sxx==0: return None,None,None
    b=sxy/sxx; a=my-b*mx
    syy=sum((c-my)**2 for c in y)
    r2=(sxy**2/(sxx*syy)) if syy>0 else 0
    return b,a,r2
rows=[]
allx=[];ally=[]
for ind,d in ser.items():
    ys=sorted(d)
    x=[];y=[]
    for t in ys:
        if t-1 in d:
            W0,S0=d[t-1]; W1,S1=d[t]
            if W0>0 and W1>0 and S0>0 and S1>0:
                x.append(math.log(S1/S0)); y.append(math.log(W1/W0))
    if len(x)>=10:
        b,a,r2=ols(x,y)
        if b is not None:
            rows.append((ind,b,r2,len(x))); allx+=x; ally+=y
b_all,_,r2_all=ols(allx,ally)
print(f"=== 運転資本の売上弾力性 β = Δln W / Δln r ===")
print(f"プール推定（{len(rows)}業種、{len(allx)}観測）: β = {b_all:.3f}  R² = {r2_all:.3f}")
bs=[b for _,b,_,_ in rows]
print(f"業種別 β: 平均 {st.mean(bs):.3f}  中央値 {st.median(bs):.3f}  標準偏差 {st.stdev(bs):.3f}")
print(f"         β<0.5 の業種 {sum(1 for b in bs if b<0.5)}/{len(bs)}")
print(f"         β>1.0 の業種 {sum(1 for b in bs if b>1.0)}/{len(bs)}")
print(f"\n分母効果の寄与 = 1 − β = {1-b_all:.3f}")
rows.sort(key=lambda z:z[1])
print(f"\n{'業種':<30}{'β':>8}{'R²':>8}")
print("-"*48)
for n,b,r2,_ in rows[:5]: print(f"{n[:29]:<30}{b:>8.2f}{r2:>8.2f}")
print("...")
for n,b,r2,_ in rows[-5:]: print(f"{n[:29]:<30}{b:>8.2f}{r2:>8.2f}")
