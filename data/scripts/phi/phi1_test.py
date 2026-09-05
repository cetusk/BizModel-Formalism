"""予測Φ1 の検定。

  予測    手続きが呼び出す他の手続きの数が少ないほど、改修されるまでの期間が長い
  対抗    改修の頻度は依存の数ではなく利用量で決まる

被説明変数は初回改修までの期間（右打ち切りあり）。
説明変数は静的に固定された依存の数（第1.4節で確定）。
統制は利用量（枠B と同じ基準期間の記録の件数、log(1+n)）。
標準誤差は実装アドレスをクラスタとする頑健標準誤差（第1.4節）。
"""
import csv, json, math, collections, statistics

PANEL = "data/raw/phi/phi1_panel.tsv"
DEPS = "data/raw/phi/phi1_deps.tsv"
LOGS = "data/raw/phi/upgraded_logs.jsonl"
FRAMEB = "data/raw/phi/phi4_frameb.tsv"
OUT = "data/raw/phi/phi1_model.tsv"


def main():
    # 実装ごとの依存の数
    dep, cbytes = {}, {}
    for r in csv.DictReader(open(DEPS), delimiter="\t"):
        dep[r["impl"]] = int(r["n_deps"])
        cbytes[r["impl"]] = int(r["code_bytes"])

    # プロキシ → 最初の実装（配備時のもの。改修の「前」の状態を説明変数にする）
    first_impl = {}
    for l in open(LOGS):
        r = json.loads(l)
        a, b, i = r["a"], r["b"], r["i"]
        if not i or int(i, 16) == 0:
            continue
        if a not in first_impl or b < first_impl[a][0]:
            first_impl[a] = (b, i)

    # 利用量（枠B の基準期間における記録の件数）
    use = {}
    for r in csv.DictReader(open(FRAMEB), delimiter="\t"):
        use[r["address"]] = int(r["n_logs"])

    n_all = n_matched = 0
    rows = []
    for r in csv.DictReader(open(PANEL), delimiter="\t"):
        n_all += 1
        a = r["address"]
        fi = first_impl.get(a)
        if not fi:
            continue
        impl = fi[1]
        if impl not in dep or cbytes.get(impl, 0) == 0:
            continue
        n_matched += 1
        rows.append({
            "address": a, "impl": impl,
            "n_deps": dep[impl],
            "code_bytes": cbytes[impl],
            "use": use.get(a, 0),
            "duration_day": float(r["duration_day"]),
            "event": int(r["event"]),
        })
    print(f"  パネル {n_all:,} 行 → 依存の数が付いた {n_matched:,} 行 "
          f"({n_matched/n_all*100:.1f}%)")

    with open(OUT, "w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    ev = sum(r["event"] for r in rows)
    print(f"  改修を観測 {ev:,} / 右打ち切り {len(rows)-ev:,}")
    cl = collections.Counter(r["impl"] for r in rows)
    print(f"  クラスタ（実装）{len(cl):,}  最大クラスタ {cl.most_common(1)[0][1]:,} 行 "
          f"({cl.most_common(1)[0][1]/len(rows)*100:.1f}%)")
    print(f"  利用量が付いた行: {sum(1 for r in rows if r['use']>0):,}")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
