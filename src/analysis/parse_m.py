import csv, re, json
def load(fn):
    lines=list(csv.reader(open(fn, encoding="cp932", errors="replace")))
    h=[i for i,r in enumerate(lines) if r and r[0].startswith("業種") and "コード" in r[0]][0]
    names=[re.sub(r'\(.*?\)|【.*?】','',c).strip() for c in lines[h][10:]]
    rows=[]
    for r in lines[h+1:]:
        if len(r)<11 or not r[0].strip(): continue
        rec={"ind":r[2],"size":r[5],"year":int(r[6][:4])}
        for n,v in zip(names, r[10:10+len(names)]):
            v=v.replace(",","").strip()
            rec[n]=None if v in ("","-","*","***","x") else float(v)
        rows.append(rec)
    return rows,names
for tag,fn in [("Am","/mnt/user-data/uploads/ファイルA__業種横断_時系列_.csv"),
               ("Bm","/mnt/user-data/uploads/ファイルB__規模階層_断面_.csv")]:
    rows,names=load(fn)
    print(f"[{tag}] {len(rows)}行 業種{len({r['ind'] for r in rows})} 規模{len({r['size'] for r in rows})} 年{min(r['year'] for r in rows)}-{max(r['year'] for r in rows)}")
    print("   項目:",names)
    json.dump(rows, open(f"{tag}.json","w"), ensure_ascii=False)
