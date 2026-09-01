import csv, re, json, sys

def load(fn):
    rows=[]
    with open(fn, encoding="cp932", errors="replace") as f:
        lines=list(csv.reader(f))
    hdr=None
    for i,r in enumerate(lines):
        if r and r[0].startswith("業種") and "コード" in r[0]:
            hdr=i; break
    cols=lines[hdr]
    items=cols[10:]                      # 項目名列
    names=[re.sub(r'\(.*?\)|【.*?】','',c).strip() for c in items]
    for r in lines[hdr+1:]:
        if len(r)<10 or not r[0].strip(): continue
        rec={"ind_code":r[0],"ind":r[2],"size_code":r[3],"size":r[5],"year":int(r[6][:4])}
        ok=True
        for n,v in zip(names, r[10:10+len(names)]):
            v=v.replace(",","").strip()
            if v in ("","-","*","***","x"): rec[n]=None
            else:
                try: rec[n]=float(v)
                except: rec[n]=None
        rows.append(rec)
    return rows, names

for tag,fn in [("A","/mnt/user-data/uploads/ファイルA_予測E用_業種横断の時系列_.csv"),
               ("B","/mnt/user-data/uploads/ファイルB_予測F用_規模階層の断面_.csv")]:
    rows,names=load(fn)
    inds=sorted({r["ind"] for r in rows}); sizes=sorted({r["size"] for r in rows})
    yrs=sorted({r["year"] for r in rows})
    print(f"[{tag}] 行数{len(rows)}  業種{len(inds)}  規模{len(sizes)}  年{min(yrs)}-{max(yrs)}")
    print(f"     項目: {names}")
    json.dump(rows, open(f"{tag}.json","w"), ensure_ascii=False)
