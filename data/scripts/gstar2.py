import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
def ccc(r):
    s=r["売上高"]
    if not s or s<=0 or r["売掛金"] is None or r["買掛金"] is None: return None
    ar=(r["受取手形"] or 0)+(r["売掛金"] or 0); ap=(r["支払手形"] or 0)+(r["買掛金"] or 0)
    return (ar+(r["製品又は商品"] or 0)-ap)/s*365
A={(r["ind"],r["year"]):r for r in json.load(open(D+"A.json"))}
Am={(r["ind"],r["year"]):r for r in json.load(open(D+"Am.json"))}
B={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"B.json"))}
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"Bm.json"))}
print("年度\tCCC\t営業利益率\tg*")
ser=[]
for y in range(2000,2025):
    k=("全産業（除く金融保険業）",y)
    c=ccc(A[k]); op=Am[k]["営業利益"]/Am[k]["売上高"]
    g=op/(c/365)*100; ser.append((y,c,op*100,g))
    print(f"{y}\t{c:.1f}\t{op*100:.2f}\t{g:.1f}")
import statistics as st
print(f"\n2000-2024: CCC {ser[0][1]:.1f}→{ser[-1][1]:.1f} (+{(ser[-1][1]/ser[0][1]-1)*100:.0f}%)")
print(f"           m   {ser[0][2]:.2f}%→{ser[-1][2]:.2f}% (+{(ser[-1][2]/ser[0][2]-1)*100:.0f}%)")
print(f"           g*  {ser[0][3]:.1f}%→{ser[-1][3]:.1f}%")
print(f"g* 平均 {st.mean(x[3] for x in ser):.1f}%  標準偏差 {st.stdev(x[3] for x in ser):.1f}")
# 傾向：前半12年 vs 後半13年
h1=[x[3] for x in ser[:12]]; h2=[x[3] for x in ser[12:]]
print(f"g* 2000-2011平均 {st.mean(h1):.1f}%  2012-2024平均 {st.mean(h2):.1f}%")

print("\n=== 2024年度 規模階層別（全産業）===")
print(f"{'規模':<24}{'CCC':>7}{'営業利益率':>10}{'g*':>10}")
for t in ["10億円以上","1億円以上 - 10億円未満","5千万円以上 - 1億円未満",
          "2千万円以上 - 5千万円未満","1千万円以上 - 2千万円未満","1千万円未満"]:
    k=("全産業（除く金融保険業）",t,2024)
    if k not in B or k not in Bm: continue
    c=ccc(B[k]); op=Bm[k]["営業利益"]/Bm[k]["売上高"]
    print(f"{t:<24}{c:>7.0f}{op*100:>9.1f}%{op/(c/365)*100:>9.1f}%")
