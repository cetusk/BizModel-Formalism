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
    s = re.sub(r"[ \t]+", " ", s.translate(Z))
    # 「5 0%」「雇 用 後 3ヶ 月」のように字間を空けた PDF がある。
    # 数字どうし、和文どうしのあいだの空白を落とす。
    s = re.sub(r"(?<=\d)\s+(?=\d)", "", s)
    s = re.sub(r"(?<=[\u3040-\u30ff\u4e00-\u9fff])[ \t]+(?=[\u3040-\u30ff\u4e00-\u9fff])", "", s)
    return s

def days(n, unit):
    n = float(n)
    return n * 30 if unit and unit != "日" else n

def steps(t):
    """(開始日, 終了日, 返戻率) の並びを返す。

    書式は事業者ごとに自由で、実際に次の四つが現れる。
      1. 「30日以内 80%」        期間と率が近接する
      2. 「31日以上90日以内 50%」 範囲で書く
      3. 「1ヶ月（100%）2ヶ月（50%）」括弧で率を添える
      4. 期間だけを横一列に並べ、率を次の行に並べる表
    4 は期間と率が離れるため、近接では対応が取れない。
    期間の並びの後ろに同数の率が並ぶ場合は、順序で対応させる。

    手数料率と返戻率を取り違えないよう、返戻に触れる最初の位置から後ろだけを見る。
    """
    m = re.search(r"返戻|返金|返還", t)
    if m:
        t = t[m.start():]
    U = r"(?:[ヶケヵカかカ箇个]?月|日)"

    # 期間の並び。(開始日, 終了日, 出現位置の終わり)
    per = []
    used = []
    def add(a, b, st_, en_):
        if b > a and b <= 400:
            per.append((a, b, st_, en_))
            used.append((st_, en_))
    def ov(i):
        return any(a <= i < b for a, b in used)

    for m in re.finditer(r"(\d+)\s*" + U + r"\s*(?:以上|超|を超え)\s*(\d+)\s*(" + U + r")\s*(?:以内|未満|まで)", t):
        add(days(m.group(1), m.group(3)), days(m.group(2), m.group(3)), m.start(), m.end())
    for m in re.finditer(r"(\d+)\s*(" + U + r")\s*[~～〜\-–—]\s*(\d+)\s*(" + U + r")?", t):
        if ov(m.start()):
            continue
        u = m.group(4) or m.group(2)
        add(days(m.group(1), m.group(2)), days(m.group(3), u), m.start(), m.end())
    for m in re.finditer(r"(\d+)\s*(" + U + r")\s*(?:以内|未満|まで|間)", t):
        if ov(m.start()):
            continue
        add(0.0, days(m.group(1), m.group(2)), m.start(), m.end())
    for m in re.finditer(r"(\d+)\s*(" + U + r")\s*[（(]", t):
        if ov(m.start()):
            continue
        add(0.0, days(m.group(1), m.group(2)), m.start(), m.end())
    if not per:
        return []
    per.sort(key=lambda x: x[2])

    pct = [(m.start(), float(m.group(1)))
           for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", t)
           if 0 < float(m.group(1)) <= 100]
    if not pct:
        return []

    out = []
    if len(pct) == len(per) and pct[0][0] > per[-1][3]:
        # 表形式。期間が並び切ってから率が並ぶ。順序で対応させる
        for (a, b, _, _), (_, p) in zip(per, pct):
            out.append((a, b, p))
    else:
        for a, b, s_, e_ in per:
            nxt = [(i - e_, p) for i, p in pct if i >= e_ and i - e_ < 140]
            prv = [(s_ - i, p) for i, p in pct if i < s_ and s_ - i < 70]
            cand = sorted(nxt) or sorted(prv)
            if cand:
                out.append((a, b, cand[0][1]))

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
