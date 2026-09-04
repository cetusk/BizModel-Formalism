"""予測Φ2：TVL（ストック）と手数料（フロー）を突き合わせて途絶事象を作る。

途絶は手数料の系列で判定する。TVL で判定すると
「M(t)→0 を途絶と呼ぶ」ことになり、予測が定義から自明になる。

出力 data/raw/phi/phi2_panel.tsv
  slug  category  cease_date  n_days_obs  tvl_at_cease
  slope_pre_180  slope_pre_90  slope_pre_30   （途絶前の窓における日次 log TVL の傾き）
"""
import json, math, statistics, datetime as dt

TVL = "data/raw/phi/llama_tvl.jsonl"
FEES = "data/raw/phi/llama_fees.jsonl"
OUT = "data/raw/phi/phi2_panel.tsv"

CEASE_DAYS = 90        # 手数料が連続してゼロなら途絶とみなす日数。事前に固定する
MIN_ACTIVE = 180       # 途絶の前にこの日数以上の活動を要求する（下限）


def to_series(pairs):
    """[[unix, value], ...] を {date: value} に畳む。"""
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
    """手数料がゼロで CEASE_DAYS 日続く最初の日を返す。"""
    if not fees:
        return None
    days = sorted(fees)
    first, last = days[0], days[-1]
    if (last - first).days < MIN_ACTIVE:
        return None
    run, start = 0, None
    d = first
    while d <= last:
        v = fees.get(d, 0.0)
        if v is None or v <= 0:
            if run == 0:
                start = d
            run += 1
            if run >= CEASE_DAYS:
                return start
        else:
            run = 0
        d += dt.timedelta(days=1)
    # 末尾がゼロで続いている場合
    if run >= CEASE_DAYS:
        return start
    return None


def main():
    tvl = {}
    for line in open(TVL):
        r = json.loads(line)
        tvl[r["slug"]] = r
    fees = {}
    for line in open(FEES):
        r = json.loads(line)
        fees[r["slug"]] = to_series(r.get("fees"))
    print(f"TVL {len(tvl)} 件、手数料 {len(fees)} 件、"
          f"両方ある {len(set(tvl) & set(fees))} 件")

    rows, n_cease = [], 0
    for slug in sorted(set(tvl) & set(fees)):
        f = fees[slug]
        s = to_series(tvl[slug].get("tvl_eth") or tvl[slug].get("tvl_all"))
        if not s:
            continue
        c = find_cease(f)
        if c is None:
            rows.append((slug, tvl[slug].get("category"), "", len(f),
                         "", "", "", ""))
            continue
        n_cease += 1
        rows.append((slug, tvl[slug].get("category"), c.isoformat(), len(f),
                     round(s.get(c, 0)),
                     slope(s, c, 180), slope(s, c, 90), slope(s, c, 30)))

    with open(OUT, "w") as o:
        o.write("slug\tcategory\tcease_date\tn_days_obs\ttvl_at_cease\t"
                "slope_pre_180\tslope_pre_90\tslope_pre_30\n")
        for r in rows:
            o.write("\t".join(str(x) for x in r) + "\n")
    print(f"途絶を観測 {n_cease} 件 / 継続 {len(rows)-n_cease} 件 → {OUT}")

    for w in ("slope_pre_180", "slope_pre_90", "slope_pre_30"):
        i = {"slope_pre_180": 5, "slope_pre_90": 6, "slope_pre_30": 7}[w]
        v = [r[i] for r in rows if r[2] and r[i] != ""]
        if v:
            neg = sum(1 for x in v if x < 0)
            print(f"  {w}: n={len(v)}  負の割合 {neg/len(v):.1%}  "
                  f"中央値 {statistics.median(v):+.5f}")


if __name__ == "__main__":
    main()
