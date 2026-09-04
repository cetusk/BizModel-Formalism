# 予測Z の検定。
#
# 【登録した予測（第17章）】
#   規模と離職率の相関（B1の代理）が強い職種ほど、返戻金制度が強い。
#   対抗仮説：返戻の強度は離職率の水準に対応する（B2 が支配する）。
#
# 【強度】(1/180)∫₀¹⁸⁰ r(d) dd。判読の規則は raw/jinzai/henreikin/README.md。
#
# 【欠測】undisc（開示しない）と misfiled（リンク先が別書類）は強度が不明。
#   0 と置くのは誤りである。除外した場合と 0 と置いた場合の両方で検定し、
#   結論が変わるかを示す。
import io, os, json, math, sys, statistics as st, collections

HERE = os.path.dirname(os.path.abspath(__file__))
def L(n): return json.load(io.open(os.path.join(HERE, "..", "derived", n), encoding="utf-8"))
S = L("henreikin_strength.json")
F = L("jinzai_firms_detail.json")
JOB = {"1.医師": "医師", "4.看護師、准看護師": "看護師",
       "7.施設介護の職業": "施設介護", "9.保育士": "保育士"}
ORDER = ["施設介護", "保育士", "医師", "看護師"]
# 予測Yで測った B1（東京以外・登録どおり）
B1 = {"施設介護": 0.246, "保育士": 0.163, "医師": 0.159, "看護師": 0.067}

def corr(x, y):
    n = len(x)
    if n < 5: return float("nan"), n
    mx, my = st.mean(x), st.mean(y)
    sx, sy = st.pstdev(x), st.pstdev(y)
    if sx == 0 or sy == 0: return float("nan"), n
    return sum((a-mx)*(b-my) for a, b in zip(x, y))/(n*sx*sy), n

def spearman(a, b):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); r = [0]*len(v)
        for p, i in enumerate(s): r[i] = p
        return r
    ra, rb = rk(a), rk(b); n = len(a)
    return 1 - 6*sum((ra[i]-rb[i])**2 for i in range(n))/(n*(n*n-1))

def build(fill_missing_zero):
    """職種 → 強度の並び。fill_missing_zero が真なら undisc/misfiled を 0 とする。"""
    D = collections.defaultdict(list)
    for r in F:
        j = JOB.get(r["job"])
        s = S.get(r["permit"])
        if not j or not s: continue
        a = s["area"]
        if a is None:
            if not fill_missing_zero: continue
            a = 0.0
        D[j].append((r["permit"], a, r["to"], r["emp"]))
    return D

def report(tag, fill):
    D = build(fill)
    print("\n" + "="*74)
    print("【%s】" % tag)
    print("  %-8s %6s %8s %8s %8s   %8s" % ("職種","n","強度中央値","平均","標準偏差","B1"))
    med = {}
    for k in ORDER:
        v = [x[1] for x in D[k]]
        med[k] = st.median(v)
        print("  %-8s %6d %8.1f %8.1f %8.1f   %+8.3f"
              % (k, len(v), st.median(v), st.mean(v), st.pstdev(v), B1[k]))
    xs = [B1[k] for k in ORDER]; ys = [med[k] for k in ORDER]
    print("\n  予測Z：B1 の大きい職種ほど強度が高いか")
    print("    順位相関（職種 n=4）  rho = %+.3f" % spearman(xs, ys))
    print("    順位  B1     :", " > ".join(sorted(ORDER, key=lambda k: -B1[k])))
    print("    順位  強度   :", " > ".join(sorted(ORDER, key=lambda k: -med[k])))
    # 対抗仮説：強度は離職率の水準に対応するか（企業単位、職種プール）
    a = [(x[1], x[2]) for k in ORDER for x in D[k] if x[2] is not None]
    r, n = corr([p[0] for p in a], [p[1] for p in a])
    print("\n  対抗仮説：強度と離職率の相関（企業×職種をプール） r = %+.3f  n = %d" % (r, n))
    b = [(x[1], math.log(x[3])) for k in ORDER for x in D[k] if x[3] and x[3] > 0]
    r2, n2 = corr([p[0] for p in b], [p[1] for p in b])
    print("  参考：強度と規模（無期就職者数の対数）の相関 r = %+.3f  n = %d" % (r2, n2))

report("欠測を除外（undisc・misfiled を落とす）", False)
report("欠測を 0 と置く", True)
