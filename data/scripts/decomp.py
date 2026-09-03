import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "derived") + "/"
import json
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open(D+"Bm.json"))}
tiers=[("10億円以上","10億円~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千万~1億"),("2千万円以上 - 5千万円未満","2千万~5千万"),
 ("1千万円以上 - 2千万円未満","1千万~2千万"),("1千万円未満","1千万未満")]
def d(r):
    s=r["売上高"]
    return (r["売上原価"]/s, r["販売費及び一般管理費"]/s, r["営業利益"]/s)
print("=== 全産業（除く金融保険業）2024年度 ===")
print(f"{'規模':<14}{'原価率':>8}{'粗利率':>8}{'販管費率':>9}{'営業利益率':>10}")
print("-"*50)
rows=[]
for t,lbl in tiers:
    k=("全産業（除く金融保険業）",t,2024)
    if k not in Bm: continue
    c,sga,op=d(Bm[k]); rows.append((lbl,c,1-c,sga,op))
    print(f"{lbl:<14}{c*100:>7.1f}%{(1-c)*100:>7.1f}%{sga*100:>8.1f}%{op*100:>9.1f}%")
big=rows[0]; small=rows[-1]
print(f"\n大企業 - 小企業の差（ポイント）")
print(f"  粗利率     {(big[2]-small[2])*100:+.1f}")
print(f"  販管費率   {(big[3]-small[3])*100:+.1f}")
print(f"  営業利益率 {(big[4]-small[4])*100:+.1f}")
print(f"\n営業利益率の差 {(big[4]-small[4])*100:.1f}pt の内訳:")
print(f"  粗利率の差の寄与   {(big[2]-small[2])*100:+.1f}pt  ({(big[2]-small[2])/(big[4]-small[4])*100:.0f}%)")
print(f"  販管費率の差の寄与 {-(big[3]-small[3])*100:+.1f}pt  ({-(big[3]-small[3])/(big[4]-small[4])*100:.0f}%)")
