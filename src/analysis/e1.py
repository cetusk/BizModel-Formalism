import json, statistics as st
A=json.load(open("A.json"))
def calc(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    inv=r["製品又は商品"] or 0
    return dict(CCC=(ar+inv-ap)/s*365, DSO=ar/s*365, sales=s)
series={}
for r in A:
    c=calc(r)
    if c: series.setdefault(r["ind"],{})[r["year"]]=c
def corr(x,y):
    n=len(x)
    if n<8: return None
    mx,my=sum(x)/n,sum(y)/n
    sx=(sum((a-mx)**2 for a in x))**.5; sy=(sum((b-my)**2 for b in y))**.5
    if sx==0 or sy==0: return None
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy)

print("dCCC(t) と 売上高成長率 g(t+k) の相関  ※負=CCC悪化が減速に対応")
print(f"{'業種':<26}" + "".join(f"{f'k={k}':>8}" for k in (-1,0,1,2)) + f"{'n':>4}")
print("-"*70)
results={}
for ind,d in sorted(series.items()):
    ys=sorted(d)
    dccc={y:d[y]["CCC"]-d[y-1]["CCC"] for y in ys if y-1 in d}
    g={y:(d[y]["sales"]/d[y-1]["sales"]-1)*100 for y in ys if y-1 in d}
    row=f"{ind[:25]:<26}"; vals={}
    for k in (-1,0,1,2):
        xs=[dccc[y] for y in dccc if y+k in g]; zs=[g[y+k] for y in dccc if y+k in g]
        c=corr(xs,zs); vals[k]=c
        row+=f"{c:>8.2f}" if c is not None else f"{'--':>8}"
    row+=f"{len([y for y in dccc if y+1 in g]):>4}"
    results[ind]=vals
    print(row)
json.dump({k:{str(a):b for a,b in v.items()} for k,v in results.items()}, open("E.json","w"), ensure_ascii=False)
