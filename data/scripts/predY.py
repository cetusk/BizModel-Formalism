# 予測Y の検定。職種別「規模と離職率の相関」の順序が東京以外でも保たれるか。
#
# 事前登録（第17章）：
#   規模 = 無期雇用就職者数の対数。無期就職者数が 0 の事業所は除く。
#   手数料を金額で表示する事業所は予測Zでのみ除き、予測Yでは用いる。
#   同定は検索結果からの取得に限る。
#
# 本文の基準値（注 副次的な観測：規模と離職率）は 307 社について算出されており、
# その標本は金額表示の事業者を除外していた。すなわち
# 登録した除外規則と基準値の構成が食い違っている。両方を報告する。
#
# 【入力の二経路】検索結果一覧のテキストは個社データなので再配布しない。
#   テキストが無い環境では derived/jinzai_firms_detail.json を読む。
#   これは permits.tsv を種に詳細ページを取得して組み立てたもので、
#   1,402 行すべてについて手数料実績率・離職率・就職者数が一覧と一致する。
import io, sys, os, math, glob, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_jinzai import parse

JOB = {"医師": "医師", "看護師、准看護師": "看護師",
       "施設介護の職業": "施設介護", "保育士": "保育士"}
ORDER = ["施設介護", "保育士", "医師", "看護師"]
BOOK = {"施設介護": 0.431, "保育士": 0.331, "医師": 0.191, "看護師": -0.009}

def corr(x, y):
    n = len(x)
    if n < 5: return float("nan"), float("nan"), n
    mx, my = st.mean(x), st.mean(y)
    sx, sy = st.pstdev(x), st.pstdev(y)
    if sx == 0 or sy == 0: return float("nan"), float("nan"), n
    r = sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n * sx * sy)
    return r, r * math.sqrt((n - 2) / max(1e-12, 1 - r * r)), n

def load_detail():
    """詳細ページ由来のデータを職種別に束ねる。テキストが無いときの経路。"""
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "derived", "jinzai_firms_detail.json")
    D, loss = {}, {}
    for r in json.load(io.open(f, encoding="utf-8")):
        key = [v for k, v in JOB.items() if k in r["job"]]
        if not key:
            continue
        D.setdefault(key[0], []).append(r)
    for k in D:
        loss[k] = (len(D[k]), len(D[k]), 0)
    return D, loss

def load(d):
    D, loss = {}, {}
    for f in sorted(glob.glob(os.path.join(d, "*.txt"))):
        key = [v for k, v in JOB.items() if k in os.path.basename(f)][0]
        p = parse(f, missing_as_zero=False)      # 「-」は欠測のまま。登録どおり除外する
        D[key] = p["firms"]; loss[key] = (p["declared"], p["rows"], p["lost"])
    return D, loss

def run(D, job, tokyo, fee_pct_only):
    S = [r for r in D[job]
         if r["to"] is not None
         and (r["pref"] == "13" if tokyo else r["pref"] != "13")
         and (r["fee_pct"] is not None if fee_pct_only else True)
         and r["emp"] is not None and r["emp"] > 0]
    return corr([math.log(r["emp"]) for r in S], [r["to"] for r in S])

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "raw", "jinzai", "search")
    # テキストがあればそれを、無ければ詳細ページ由来のデータを読む。
    if "--detail" in sys.argv or not glob.glob(os.path.join(d, "*.txt")):
        D, loss = load_detail()
        sys.stderr.write("  入力: derived/jinzai_firms_detail.json（詳細ページ由来）\n")
    else:
        D, loss = load(d)
        sys.stderr.write("  入力: %s（検索結果一覧のテキスト）\n" % d)
    print("【取得の状態】")
    for j in ORDER:
        dec, rows, lo = loss[j]
        print("  %-6s 宣言 %5d 件 / 抽出 %5d 行（欠損 %3d = %.1f%%）/ 名寄せ後 %4d 社"
              % (j, dec, rows, lo, 100 * lo / dec, len(D[j])))

    for pct, lab in [(False, "登録どおり：金額表示も用いる"), (True, "参考：金額表示を除く（本文の基準値の構成）")]:
        print("\n" + "=" * 76)
        print("【%s】" % lab)
        print("  %-6s %-24s %-24s %s" % ("職種", "東京（本文の標本）", "東京以外（標本外）", "本文"))
        for j in ORDER:
            r1, t1, n1 = run(D, j, True, pct)
            r2, t2, n2 = run(D, j, False, pct)
            print("  %-6s n=%3d r=%+.3f t=%+5.2f   n=%3d r=%+.3f t=%+5.2f   %+.3f"
                  % (j, n1, r1, t1, n2, r2, t2, BOOK[j]))
        east = [(j, run(D, j, False, pct)[0]) for j in ORDER]
        print("  東京以外の順位:", " > ".join(x[0] for x in sorted(east, key=lambda z: -z[1])))
