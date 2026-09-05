"""予測Φ1 の推定。

  予測    依存の数が少ないほど、改修されるまでの期間が長い
          → ハザードに対する依存の数の係数は正
  対抗    改修は依存の数でなく利用量で決まる

区分指数モデル（piecewise-exponential）を用いる。
追跡期間を区分に切り、区分ごとに一定のベースラインハザードを置く。
これは Cox にベースラインを区分定数とした場合と等価であり、
同値のタイが多い（193万行に対し相異なる期間が15.9万）本データでも数値的に安定する。
lifelines の Cox は Newton-Raphson が NaN を出して収束しなかった。

説明変数は実装ごとに一定なので、(実装 × 区分) に集計しても情報は失われない。
標準誤差は実装アドレスをクラスタとする頑健標準誤差（第1.4節で確定）。

副モデルとして実装単位の指数ハザードも出す。
80.3% を占める単一クラスタ（AuthenticatedProxy）の影響を除いて見るため。
"""
import numpy as np, pandas as pd
import statsmodels.api as sm

SRC = "data/raw/phi/phi1_model.tsv"
NCUT = 10          # 区分の数。イベント時刻の分位で切る


def build_cells(df, cuts):
    """(実装 × 区分) の曝露と改修件数に集計する。"""
    d = df.duration_day.to_numpy()
    e = df.event.to_numpy()
    impl = df.impl.to_numpy()
    lo, hi = cuts[:-1], cuts[1:]
    out = []
    for k in range(len(lo)):
        expo = np.clip(d - lo[k], 0, hi[k] - lo[k])
        ev = ((e == 1) & (d > lo[k]) & (d <= hi[k])).astype(np.int64)
        m = expo > 0
        out.append(pd.DataFrame({"impl": impl[m], "k": k,
                                 "expo": expo[m], "ev": ev[m]}))
    cells = pd.concat(out, ignore_index=True)
    g = cells.groupby(["impl", "k"], observed=True).agg(
        expo=("expo", "sum"), ev=("ev", "sum")).reset_index()
    return g[g.expo > 0]


def report(name, m, cols):
    print(f"\n  [{name}]")
    for v in cols:
        print(f"    {v:<9} coef {m.params[v]:+.4f}  HR {np.exp(m.params[v]):.3f}"
              f"  se {m.bse[v]:.4f}  z {m.tvalues[v]:+.2f}  p {m.pvalues[v]:.3g}")


def main():
    df = pd.read_csv(SRC, sep="\t")
    df = df[df.duration_day > 0].copy()
    print(f"  観測 {len(df):,} 行、改修 {int(df.event.sum()):,} 件、"
          f"クラスタ（実装）{df.impl.nunique():,}")
    print(f"  依存の数: 中央値 {df.n_deps.median():.0f}、"
          f"四分位 {df.n_deps.quantile(.25):.0f}--{df.n_deps.quantile(.75):.0f}")
    print(f"  利用量>0: {(df.use>0).sum():,} 行（{(df.use>0).mean()*100:.3f}%）")

    q = np.unique(np.quantile(df.loc[df.event == 1, "duration_day"],
                              np.linspace(0, 1, NCUT + 1)))
    cuts = np.concatenate([[0.0], q[1:-1], [df.duration_day.max() + 1]])
    print(f"  区分の切れ目（日）: {np.round(cuts, 1).tolist()}")

    attr = df.groupby("impl").agg(n_deps=("n_deps", "first"),
                                  code_bytes=("code_bytes", "first"),
                                  use=("use", "max")).reset_index()
    g = build_cells(df, cuts).merge(attr, on="impl")
    g["log_dep"] = np.log1p(g.n_deps)
    g["log_use"] = np.log1p(g.use)
    g["log_size"] = np.log1p(g.code_bytes)
    K = pd.get_dummies(g.k, prefix="k", drop_first=True).astype(float)
    print(f"  セル {len(g):,} 行（実装 × 区分）、改修 {int(g.ev.sum()):,} 件\n")

    print("■ 主モデル：区分指数（識別子単位の曝露、実装をクラスタとする頑健標準誤差）")
    for name, cols in [("依存のみ", ["log_dep"]),
                       ("＋利用量", ["log_dep", "log_use"]),
                       ("＋規模", ["log_dep", "log_use", "log_size"])]:
        X = sm.add_constant(pd.concat([g[cols], K], axis=1))
        m = sm.GLM(g.ev, X, family=sm.families.Poisson(),
                   offset=np.log(g.expo)).fit(
            cov_type="cluster", cov_kwds={"groups": g.impl.to_numpy()})
        report(name, m, cols)

    print("\n■ 副モデル：実装単位の指数ハザード（単一クラスタの支配を外して見る）")
    a = df.groupby("impl").agg(events=("event", "sum"),
                               expo=("duration_day", "sum"),
                               n_deps=("n_deps", "first"),
                               code_bytes=("code_bytes", "first"),
                               use=("use", "max")).reset_index()
    a = a[a.expo > 0]
    a["log_dep"] = np.log1p(a.n_deps)
    a["log_use"] = np.log1p(a.use)
    a["log_size"] = np.log1p(a.code_bytes)
    X = sm.add_constant(a[["log_dep", "log_use", "log_size"]])
    m = sm.GLM(a.events, X, family=sm.families.Poisson(),
               offset=np.log(a.expo)).fit(cov_type="HC1")
    print(f"  実装 {len(a):,} 件、改修 {int(a.events.sum()):,} 件")
    report("実装単位", m, ["log_dep", "log_use", "log_size"])


if __name__ == "__main__":
    main()
