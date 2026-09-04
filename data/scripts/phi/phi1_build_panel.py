"""予測Φ1：Upgraded ログから生存分析の入力を作る。

Upgraded(address) はプロキシの配備時にも発火する。
アドレスごとに時刻順に並べ、1回目を配備、2回目以降を改修として扱う。
改修が一度もないものは観測終了時点で右打ち切りになる。

出力 data/raw/phi/phi1_panel.tsv
  address  deploy_block  first_upgrade_block  n_upgrades  n_impl  duration_day  event
    event = 1 なら改修を観測、0 なら右打ち切り
"""
import json, collections, bisect, statistics, sys

LOGS = "data/raw/phi/upgraded_logs.jsonl"
TSMAP = "data/raw/phi/block_time.json"
OUT = "data/raw/phi/phi1_panel.tsv"


def load_timemap():
    """(block, timestamp) の標本から線形内挿の関数を作る。"""
    d = json.load(open(TSMAP))
    bs = [x[0] for x in d]
    ts = [x[1] for x in d]

    def f(b):
        i = bisect.bisect_left(bs, b)
        if i == 0:
            return ts[0] + (b - bs[0]) * 12.0
        if i >= len(bs):
            return ts[-1] + (b - bs[-1]) * 12.0
        b0, b1, t0, t1 = bs[i-1], bs[i], ts[i-1], ts[i]
        return t0 + (t1 - t0) * (b - b0) / (b1 - b0)
    return f, bs[-1], ts[-1]


def main():
    ev = collections.defaultdict(list)
    n = 0
    for line in open(LOGS):
        r = json.loads(line)
        ev[r["a"]].append((r["b"], r["i"]))
        n += 1
    print(f"ログ {n:,} 件、相異なるアドレス {len(ev):,} 件")

    # 同一ブロック内の重複を落とす（再開時の重なり対策）
    for a in ev:
        ev[a] = sorted(set(ev[a]))

    f, bmax, tmax = load_timemap()
    rows, up = [], 0
    for a, e in ev.items():
        blocks = [b for b, _ in e]
        impls = set(i for _, i in e if i)
        deploy = blocks[0]
        n_up = len(blocks) - 1
        if n_up > 0:
            first = blocks[1]
            dur = (f(first) - f(deploy)) / 86400.0
            event = 1
            up += 1
        else:
            first = ""
            dur = (tmax - f(deploy)) / 86400.0
            event = 0
        rows.append((a, deploy, first, n_up, len(impls), round(dur, 2), event))

    rows.sort(key=lambda r: r[1])
    with open(OUT, "w") as o:
        o.write("address\tdeploy_block\tfirst_upgrade_block\t"
                "n_upgrades\tn_impl\tduration_day\tevent\n")
        for r in rows:
            o.write("\t".join(str(x) for x in r) + "\n")

    print(f"改修を観測 {up:,} 件 / 右打ち切り {len(rows)-up:,} 件")
    dur_ev = [r[5] for r in rows if r[6] == 1]
    if dur_ev:
        print(f"改修までの日数：中央値 {statistics.median(dur_ev):.1f} 日、"
              f"平均 {statistics.mean(dur_ev):.1f} 日")
    c = collections.Counter(r[3] for r in rows)
    print("改修回数の分布:", dict(sorted(c.items())[:8]))
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
