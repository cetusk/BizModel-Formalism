# 返戻金制度の PDF から「何日以内に離職したら手数料の何％を返すか」を読む。
#
# 【強度の定義】返戻金は決済 Π の状態依存的な巻き戻しである。
#   離職までの日数 d の関数 r(d)（返戻率）として書けるので、
#   サイトの離職率が就職後6ヶ月で定義されているのに合わせ、
#   その窓での平均 area = (1/180)∫_0^180 r(d) dd を強度とする。
#   併せて r(30) r(60) r(90) と、返戻が及ぶ最終日 span を出す。
#
# 【限界】書式は事業者ごとに自由である。段階表を持たず散文で書くもの、
#   スキャン画像で文字を持たないものがある。抽出できたかを ok で記録し、
#   できなかったものは人が読む。**取れた社だけで検定してはならない**（第15章）。
import io, os, re, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin")
OUT  = os.path.join(HERE, "..", "derived", "jinzai_henreikin.json")

Z = str.maketrans("０１２３４５６７８９％，．　", "0123456789%,. ")

def text(path):
    try:
        s = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"],
                           capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
    except Exception:
        return ""
    return re.sub(r"[ \t]+", " ", s.translate(Z))

def days(n, unit):
    n = float(n)
    return n * 30 if unit and unit != "日" else n

def steps(t):
    """(開始日, 終了日, 返戻率) の並びを返す。"""
    out = []
    U = r"(?:[ヶケヵか箇]?月|日)"
    pats = [
        # 31日以上90日以内 … 50%
        (r"(\d+)\s*" + U + r"\s*(?:以上|超|を超え)\s*(\d+)\s*(" + U + r")\s*(?:以内|未満|まで)", "range"),
        # 30日以内 … 80%
        (r"(\d+)\s*(" + U + r")\s*(?:以内|未満|まで)", "upto"),
    ]
    # 「31日以上90日以内」の後半は「90日以内」にも当たる。範囲の規則を先に当て、
    # 消費した位置に重なる上限だけの一致は捨てる。
    used = []
    for pat, kind in pats:
        for m in re.finditer(pat, t):
            if kind == "upto" and any(a <= m.start() < b for a, b in used):
                continue
            tail = t[m.end():m.end() + 120]
            head = t[max(0, m.start() - 60):m.start()]
            q = re.search(r"(\d+(?:\.\d+)?)\s*%", tail) or re.search(r"(\d+(?:\.\d+)?)\s*%", head)
            if not q:
                continue
            pct = float(q.group(1))
            if not (0 < pct <= 100):
                continue
            if kind == "range":
                a, b = days(m.group(1), m.group(3)), days(m.group(2), m.group(3))
            else:
                a, b = 0.0, days(m.group(1), m.group(2))
            if b > a and b <= 400:
                out.append((a, b, pct))
                if kind == "range":
                    used.append((m.start(), m.end()))
    # 同じ区間が二つの規則で重複して拾われることがある。狭いほうを残す。
    out.sort(key=lambda x: (x[0], x[1] - x[0]))
    keep = []
    for a, b, p in out:
        if any(abs(a - c) < 1 and abs(b - d) < 1 for c, d, _ in keep):
            continue
        keep.append((a, b, p))
    return keep

def summary(st):
    """日ごとの返戻率。区間が重なるときは高いほうを採る。"""
    if not st:
        return None
    r = [0.0] * 401
    for a, b, p in st:
        for d in range(int(a), min(int(b), 400) + 1):
            r[d] = max(r[d], p)
    return dict(area=round(sum(r[1:181]) / 180.0, 2),
                r30=r[30], r60=r[60], r90=r[90],
                span=max((int(b) for _, b, _ in st), default=0),
                n_steps=len(st))

def main():
    rows = []
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".pdf"):
            continue
        p = os.path.join(SRC, f)
        t = text(p)
        st = steps(t)
        s = summary(st)
        rows.append(dict(permit=f[:-4], bytes=os.path.getsize(p), chars=len(t.strip()),
                         scanned=(len(t.strip()) < 40), steps=st, **(s or {})))
    json.dump(rows, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = len(rows)
    sc = sum(1 for r in rows if r["scanned"])
    ok = sum(1 for r in rows if r.get("area"))
    sys.stderr.write("  %d 件 / 画像のみ %d / 段階を抽出できた %d → %s\n" % (n, sc, ok, OUT))

if __name__ == "__main__":
    main()
