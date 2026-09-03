exec(open('../raw/jinzai/nurse.py', encoding="utf-8").read())
import math, statistics as st
def corr(x,y):
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    sx=(sum((a-mx)**2 for a in x))**.5; sy=(sum((b-my)**2 for b in y))**.5
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy) if sx*sy>0 else None
def spearman(x,y):
    def rank(v):
        s=sorted(range(len(v)), key=lambda i:v[i]); r=[0]*len(v)
        for k,i in enumerate(s): r[i]=k+1
        return r
    return corr(rank(x),rank(y))
def tstat(r,n): return r*math.sqrt((n-2)/(1-r*r)) if abs(r)<1 else float('inf')

pct=[d for d in D if d[3]=='p']
print(f"=== 標本 ===")
print(f"全108社。料率%表示 {len(pct)}社")
for lbl,sub in [("(a) %表示・全件", pct),
                ("(b) %表示・無期就職>0", [d for d in pct if d[1]>0]),
                ("(c) %表示・無期就職>=10", [d for d in pct if d[1]>=10]),
                ("(d) %表示・無期就職>=50", [d for d in pct if d[1]>=50])]:
    if len(sub)<5: continue
    f=[d[2] for d in sub]; t=[d[4] for d in sub]
    r=corr(f,t); rs=spearman(f,t); n=len(sub)
    print(f"\n{lbl}  n={n}")
    print(f"  手数料率 平均{st.mean(f):.1f}% 中央{st.median(f):.1f}% SD{st.stdev(f):.1f}")
    print(f"  離職率   平均{st.mean(t):.1f}% 中央{st.median(t):.1f}% SD{st.stdev(t):.1f}")
    print(f"  Pearson r = {r:+.3f}  (t={tstat(r,n):+.2f})")
    print(f"  Spearman ρ = {rs:+.3f}")
