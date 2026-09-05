"""予測Φ2：TVL（ストック）と手数料（フロー）を突き合わせて途絶事象を作る。

途絶の定義（第2.5節で確定、変更しない）
  手数料が 90 日以上連続してゼロであり、かつ最後まで再開しないこと。
  その最初の日を途絶の日とする。途絶の前に 180 日以上の活動を要求する。

途絶を TVL で判定すると「M(t)→0 を途絶と呼ぶ」ことになり
予測が定義から自明になるため、途絶はフロー（手数料）だけで判定する。

継続群にも同じ窓で傾きを測る。これを欠くと
TVL が全体として減少基調である可能性を排除できない。

出力 data/raw/phi/phi2_panel.tsv
"""
import json, math, statistics, datetime as dt

TVL = "data/raw/phi/llama_tvl.jsonl"
FEES = "data/raw/phi/llama_fees.jsonl"
OUT = "data/raw/phi/phi2_panel.tsv"

CEASE_DAYS = 90     # 第2.5節で確定
MIN_ACTIVE = 180    # 第2.5節で確定
WINDOWS = (180, 90, 30)


def to_series(pairs):
    out = {}
    for t, v in pairs or []:
        try:
            d = dt.datetime.fromtimestamp(int(t), dt.UTC).date()
        except Exception:
            continue
        if v is not None:
            out[d] = float(v)
    return out


def slope(series, end, days):
    """end から遡る days 日の log TVL の最小二乗傾き（1日あたり）。"""
    xs, ys = [], []
    for k in range(days):
        d = end - dt.timedelta(days=k)
        v = series.get(d)
        if v and v > 0:
            xs.append(-k)
            ys.append(math.log(v))
    if len(xs) < max(5, days // 6):
        return ""
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return "" if den == 0 else round(num / den, 5)


def find_cease(fees):
    """末尾まで再開しないゼロの連なりの開始日。途絶でなければ None。"""
    if not fees:
        return None
    days = sorted(fees)
    first, last = days[0], days[-1]
    if (last - first).days < MIN_ACTIVE:
        return None
    # 末尾から遡って、最後に手数料が出た日を探す
    d, last_pos = last, None
    while d >= first:
        v = fees.get(d, 0.0)
        if v and v > 0:
            last_pos = d
            break
        d -= dt.timedelta(days=1)
    if last_pos is None:                 # 一度も手数料が出ていない
        return None
    run = (last - last_pos).days
    if run < CEASE_DAYS:
        return None
    if (last_pos - first).days < MIN_ACTIVE:
        return None
    return last_pos + dt.timedelta(days=1)


def main():
    tvl = {json.loads(l)["slug"]: json.loads(l) for l in open(TVL)}
    fees = {}
    for l in open(FEES):
        r = json.loads(l)
        fees[r["slug"]] = to_series(r.get("fees"))
    both = sorted(set(tvl) & set(fees))
    print(f"TVL {len(tvl)} 件、手数料 {len(fees)} 件、両方ある {len(both)} 件")

    rows = []
    for slug in both:
        f = fees[slug]
        s = to_series(tvl[slug].get("tvl_eth") or tvl[slug].get("tvl_all"))
        if not s or not f:
            continue
        c = find_cease(f)
        # 継続群の基準日は観測の末尾（途絶群の基準日と同じ役割）
        ref = c if c else max(f)
        rows.append([slug, tvl[slug].get("category"),
                     "途絶" if c else "継続",
                     ref.isoformat(), len(f),
                     round(s.get(ref, 0))]
                    + [slope(s, ref, w) for w in WINDOWS])

    with open(OUT, "w") as o:
        o.write("slug\tcategory\tgroup\tref_date\tn_days_obs\ttvl_at_ref\t"
                + "\t".join(f"slope_pre_{w}" for w in WINDOWS) + "\n")
        for r in rows:
            o.write("\t".join(str(x) for x in r) + "\n")

    nc = sum(1 for r in rows if r[2] == "途絶")
    print(f"途絶 {nc} 件 / 継続 {len(rows)-nc} 件 → {OUT}\n")
    print(f"{'窓':>6} {'群':>4} {'n':>5} {'負の割合':>9} {'中央値':>11}")
    for i, w in enumerate(WINDOWS):
        for g in ("途絶", "継続"):
            v = [r[6 + i] for r in rows if r[2] == g and r[6 + i] != ""]
            if not v:
                continue
            neg = sum(1 for x in v if x < 0)
            print(f"{w:>5}日 {g:>4} {len(v):>5} {neg/len(v)*100:>8.1f}% "
                  f"{statistics.median(v):>+11.5f}")


if __name__ == "__main__":
    main()
