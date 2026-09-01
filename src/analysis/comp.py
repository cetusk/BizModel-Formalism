import json
A={(r["ind"],r["year"]):r for r in json.load(open("A.json"))}
def parts(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0)
    ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    inv=r["製品又は商品"] or 0
    return dict(DSO=ar/s*365, DIO=inv/s*365, DPO=ap/s*365,
                CCC=(ar+inv-ap)/s*365, S=s,
                bill_r=(r["受取手形"] or 0)/s*365, bill_p=(r["支払手形"] or 0)/s*365)
def leaf(n): return not ("(集約)" in n or "H20年度" in n or n in
        ("全産業（除く金融保険業）","製造業","非製造業"))
for y0,y1,lbl in [(2000,2024,"2000→2024"),(2010,2024,"2010→2024")]:
    inds=[n for (n,y) in A if y==y0 and leaf(n) and (n,y1) in A and parts(A[(n,y0)]) and parts(A[(n,y1)])]
    p0={n:parts(A[(n,y0)]) for n in inds}; p1={n:parts(A[(n,y1)]) for n in inds}
    S0=sum(p0[n]['S'] for n in inds); S1=sum(p1[n]['S'] for n in inds)
    w={n:(p0[n]['S']/S0+p1[n]['S']/S1)/2 for n in inds}
    print(f"\n=== {lbl} 業種内効果の成分分解（共通{len(inds)}業種、加重平均）===")
    tot=0
    for k,sign in [('DSO',+1),('DIO',+1),('DPO',-1)]:
        v=sum(w[n]*(p1[n][k]-p0[n][k]) for n in inds)*sign
        lv0=sum(w[n]*p0[n][k] for n in inds); lv1=sum(w[n]*p1[n][k] for n in inds)
        tot+=v
        arrow = "増" if lv1>lv0 else "減"
        print(f"  {k}: {lv0:5.1f} → {lv1:5.1f} 日 ({arrow})   CCCへの寄与 {v:+6.2f} 日")
    print(f"  合計 {tot:+.2f} 日")
    print(f"  うち受取手形 {sum(w[n]*p0[n]['bill_r'] for n in inds):.1f} → {sum(w[n]*p1[n]['bill_r'] for n in inds):.1f} 日")
    print(f"     支払手形 {sum(w[n]*p0[n]['bill_p'] for n in inds):.1f} → {sum(w[n]*p1[n]['bill_p'] for n in inds):.1f} 日")
