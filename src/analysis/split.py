import json, statistics as st
Bm={(r["ind"],r["size"],r["year"]):r for r in json.load(open("Bm.json"))}
C ={(r["ind"],r["size"],r["year"]):r for r in json.load(open("C.json"))}
def calc(k):
    b=Bm.get(k); c=C.get(k)
    if not b or not c: return None
    s=b["売上高"]
    if not s or s<=0: return None
    off=(c["役員給与"] or 0)+(c["役員賞与"] or 0)
    emp=(c["従業員給与"] or 0)+(c["従業員賞与"] or 0)
    return dict(off=off/s, emp=emp/s, hr=(off+emp)/s, op=b["営業利益"]/s,
                ratio=off/(off+emp) if off+emp>0 else None, sales=s,
                op_abs=b["営業利益"], off_abs=off)
tiers=[("10億円以上","10億円~"),("1億円以上 - 10億円未満","1~10億"),
 ("5千万円以上 - 1億円未満","5千万~1億"),("2千万円以上 - 5千万円未満","2千万~5千万"),
 ("1千万円以上 - 2千万円未満","1千万~2千万"),("1千万円未満","1千万未満")]
print("=== 全産業 2024年度：人件費の内訳 ===")
print(f"{'規模':<12}{'役員報酬率':>11}{'従業員給与率':>13}{'人件費率':>10}{'役員比率':>10}{'営業利益率':>11}")
print("-"*70)
rows=[]
for t,lbl in tiers:
    r=calc(("全産業（除く金融保険業）",t,2024))
    if r:
        rows.append((lbl,r))
        print(f"{lbl:<12}{r['off']*100:>10.2f}%{r['emp']*100:>12.1f}%{r['hr']*100:>9.1f}%{r['ratio']*100:>9.1f}%{r['op']*100:>10.1f}%")
big=rows[0][1]; small=rows[-1][1]
print(f"\n小-大 の差（ポイント）")
print(f"  役員報酬率   {(small['off']-big['off'])*100:+.2f}")
print(f"  従業員給与率 {(small['emp']-big['emp'])*100:+.1f}")
print(f"  営業利益率   {(small['op']-big['op'])*100:+.1f}")
print(f"\n役員報酬を営業利益に戻した場合の『調整後営業利益率』")
for lbl,r in rows:
    print(f"  {lbl:<12}{r['op']*100:>6.1f}%  →  {(r['op']+r['off'])*100:>6.1f}%")
