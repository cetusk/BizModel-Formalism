import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json, math, statistics as st
A=json.load(open(D+"A.json"))
def wr(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    W=ar+(r["製品又は商品"] or 0)-ap
    return (W,s) if W>0 else None
def leaf(n): return not ("(集約)" in n or "H20年度" in n or n in
        ("全産業（除く金融保険業）","製造業","非製造業"))
ser={}
for r in A:
    v=wr(r)
    if v and leaf(r["ind"]): ser.setdefault(r["ind"],{})[r["year"]]=v
def ols2(y,X):
    # y = a + b0*x0 + b1*x1  （正規方程式を直接解く）
    n=len(y); k=len(X)
    import itertools
    M=[[n]+[sum(x) for x in X]]
    for i in range(k):
        M.append([sum(X[i])]+[sum(X[i][t]*X[j][t] for t in range(n)) for j in range(k)])
    v=[sum(y)]+[sum(X[i][t]*y[t] for t in range(n)) for i in range(k)]
    # ガウス消去
    import copy
    Ab=[row[:]+[v[i]] for i,row in enumerate(M)]
    m=len(Ab)
    for c in range(m):
        p=max(range(c,m),key=lambda rr:abs(Ab[rr][c]))
        if abs(Ab[p][c])<1e-12: return None
        Ab[c],Ab[p]=Ab[p],Ab[c]
        for rr in range(m):
            if rr!=c:
                f=Ab[rr][c]/Ab[c][c]
                for cc in range(c,m+1): Ab[rr][cc]-=f*Ab[c][cc]
    sol=[Ab[i][m]/Ab[i][i] for i in range(m)]
    yh=[sol[0]+sum(sol[i+1]*X[i][t] for i in range(k)) for t in range(n)]
    my=sum(y)/n
    ss=sum((y[t]-my)**2 for t in range(n)); rs=sum((y[t]-yh[t])**2 for t in range(n))
    return sol, (1-rs/ss if ss>0 else 0)
rows=[]; ally=[]; allx0=[]; allx1=[]
for ind,d in ser.items():
    ys=sorted(d); y=[];x0=[];x1=[]
    for t in ys:
        if t-1 in d and t-2 in d:
            W0,S0=d[t-1]; W1,S1=d[t]; _,Sm=d[t-2]
            if min(W0,W1,S0,S1,Sm)>0:
                y.append(math.log(W1/W0)); x0.append(math.log(S1/S0)); x1.append(math.log(S0/Sm))
    if len(y)>=12:
        r=ols2(y,[x0,x1])
        if r:
            (a,b0,b1),r2=r
            cc=[d[t][0]/d[t][1]*365 for t in ys]
            rows.append((ind,b0,b1,r2,st.mean(cc)))
            ally+=y; allx0+=x0; allx1+=x1
res=ols2(ally,[allx0,allx1])
(a,B0,B1),R2=res
print(f"=== 分布ラグ推定（{len(rows)}業種、{len(ally)}観測）===")
print(f"  β0 (同時点) = {B0:.3f}")
print(f"  β1 (1期ラグ) = {B1:.3f}")
print(f"  総弾力性 β0+β1 = {B0+B1:.3f}")
print(f"  R² = {R2:.3f}   （同時点のみの推定では 0.076）")
print(f"  分母効果 1−(β0+β1) = {1-(B0+B1):.3f}")
# CCC と β1 の関係
import statistics
def corr(x,y):
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    sx=(sum((a-mx)**2 for a in x))**.5; sy=(sum((b-my)**2 for b in y))**.5
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy) if sx*sy>0 else None
ccs=[r[4] for r in rows]; b1s=[r[2] for r in rows]
print(f"\n=== 予測O：CCC と β1 の相関 ===")
print(f"  corr(CCC, β1) = {corr(ccs,b1s):+.3f}   n={len(rows)}")
lo=[r for r in rows if r[4]<30]; hi=[r for r in rows if r[4]>=60]
print(f"  CCC<30日 の業種({len(lo)}): β1 平均 {st.mean(r[2] for r in lo):+.3f}")
print(f"  CCC>=60日の業種({len(hi)}): β1 平均 {st.mean(r[2] for r in hi):+.3f}")
