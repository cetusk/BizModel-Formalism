import json
A={(r["ind"],r["year"]):r for r in json.load(open("A.json"))}
def wS(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return ar+(r["製品又は商品"] or 0)-ap, s
def leaf(n): return not ("(集約)" in n or "H20年度" in n or n in
        ("全産業（除く金融保険業）","製造業","非製造業"))
def analyze(y0,y1,label):
    inds=[n for (n,y) in A if y==y0 and leaf(n) and (n,y1) in A
          and wS(A[(n,y0)]) and wS(A[(n,y1)])]
    d0={n:wS(A[(n,y0)]) for n in inds}; d1={n:wS(A[(n,y1)]) for n in inds}
    S0=sum(v[1] for v in d0.values()); S1=sum(v[1] for v in d1.values())
    c0={n:d0[n][0]/d0[n][1]*365 for n in inds}; c1={n:d1[n][0]/d1[n][1]*365 for n in inds}
    w0={n:d0[n][1]/S0 for n in inds};          w1={n:d1[n][1]/S1 for n in inds}
    C0=sum(w0[n]*c0[n] for n in inds); C1=sum(w1[n]*c1[n] for n in inds)
    within = sum((w0[n]+w1[n])/2*(c1[n]-c0[n]) for n in inds)
    between= sum((w1[n]-w0[n])*(c0[n]+c1[n])/2 for n in inds)
    print(f"\n=== {label}  共通{len(inds)}業種 ===")
    print(f"  CCC {C0:.1f} → {C1:.1f}  （ΔCCC = {C1-C0:+.1f} 日）")
    print(f"  業種内効果 {within:+6.1f} 日  ({within/(C1-C0)*100:5.1f}%)")
    print(f"  構成効果   {between:+6.1f} 日  ({between/(C1-C0)*100:5.1f}%)")
    print(f"  残差       {C1-C0-within-between:+6.1f} 日")
    con=sorted(((w1[n]-w0[n])*(c0[n]+c1[n])/2, n) for n in inds)
    print("  構成効果の寄与 上位/下位:")
    for v,n in con[-4:][::-1]: print(f"     +{v:5.2f} 日  {n[:30]}  比重 {w0[n]*100:4.1f}%→{w1[n]*100:4.1f}%  CCC {c1[n]:.0f}日")
    for v,n in con[:3]:        print(f"     {v:6.2f} 日  {n[:30]}  比重 {w0[n]*100:4.1f}%→{w1[n]*100:4.1f}%  CCC {c1[n]:.0f}日")
    wi=sorted(((w0[n]+w1[n])/2*(c1[n]-c0[n]), n) for n in inds)
    print("  業種内効果の寄与 上位:")
    for v,n in wi[-4:][::-1]: print(f"     +{v:5.2f} 日  {n[:30]}  CCC {c0[n]:.0f}→{c1[n]:.0f}日")
analyze(2000,2024,"2000→2024 全期間")
analyze(2010,2024,"2010→2024 分類安定期")
