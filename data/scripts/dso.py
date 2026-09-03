import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
A={(r["ind"],r["year"]):r for r in json.load(open(D+"A.json"))}
def parts(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    return dict(DSO=((r["受取手形"] or 0)+(r["売掛金"] or 0))/s*365,
                bill=(r["受取手形"] or 0)/s*365,
                ar=(r["売掛金"] or 0)/s*365, S=s)
def leaf(n): return not ("(集約)" in n or "H20年度" in n or n in
        ("全産業（除く金融保険業）","製造業","非製造業"))
y0,y1=2010,2024
inds=[n for (n,y) in A if y==y0 and leaf(n) and (n,y1) in A and parts(A[(n,y0)]) and parts(A[(n,y1)])]
p0={n:parts(A[(n,y0)]) for n in inds}; p1={n:parts(A[(n,y1)]) for n in inds}
S0=sum(p0[n]['S'] for n in inds); S1=sum(p1[n]['S'] for n in inds)
w={n:(p0[n]['S']/S0+p1[n]['S']/S1)/2 for n in inds}
con=sorted((w[n]*(p1[n]['DSO']-p0[n]['DSO']), n) for n in inds)
print("=== 2010→2024 DSO伸長への寄与（上位・下位）===")
print(f"{'業種':<30}{'寄与':>7}{'DSO':>14}{'うち手形':>14}{'うち売掛':>14}")
print("-"*80)
for v,n in con[-8:][::-1]:
    print(f"{n[:29]:<30}{v:>+7.2f}{p0[n]['DSO']:>7.0f}→{p1[n]['DSO']:<6.0f}{p0[n]['bill']:>7.1f}→{p1[n]['bill']:<6.1f}{p0[n]['ar']:>7.0f}→{p1[n]['ar']:<6.0f}")
print("...")
for v,n in con[:3]:
    print(f"{n[:29]:<30}{v:>+7.2f}{p0[n]['DSO']:>7.0f}→{p1[n]['DSO']:<6.0f}{p0[n]['bill']:>7.1f}→{p1[n]['bill']:<6.1f}{p0[n]['ar']:>7.0f}→{p1[n]['ar']:<6.0f}")
print()
tot=sum(v for v,_ in con)
pos=sum(v for v,_ in con if v>0); neg=sum(v for v,_ in con if v<0)
print(f"合計 {tot:+.2f} 日  （増加寄与 {pos:+.2f} / 減少寄与 {neg:+.2f}）")
print(f"DSOが増えた業種 {sum(1 for v,_ in con if v>0)}/{len(con)}")
# 手形と売掛の分離
bill=sum(w[n]*(p1[n]['bill']-p0[n]['bill']) for n in inds)
ar  =sum(w[n]*(p1[n]['ar']-p0[n]['ar']) for n in inds)
print(f"\nDSO変化の内訳: 受取手形 {bill:+.2f} 日 / 売掛金 {ar:+.2f} 日")
