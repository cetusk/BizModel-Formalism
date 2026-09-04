# 判読した返戻の段階から、返戻金制度の強度を算出する。
#
# 【定義】離職までの日数 d に対する返戻率 r(d)（％）として、
#   強度 = (1/180) ∫₀¹⁸⁰ r(d) dd
# 窓を180日に取るのは、サイト側の離職率が就職後6ヶ月で定義されているため。
# 区間が重なるときは高いほうの率を採る（規則は raw/jinzai/henreikin/README.md）。
#
# 【欠測の扱い】undisc・misfiled は強度が分からない。0 と置いてはならない。
#   none・zero は強度 0 の観測であり、集計に入れる。
import io, os, json, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
R    = json.load(io.open(os.path.join(HERE, "..", "derived", "henreikin_read.json"), encoding="utf-8"))
OUT  = os.path.join(HERE, "..", "derived", "henreikin_strength.json")
OBS  = {"ok", "none", "zero"}      # 強度が観測できた区分
W    = 180

def curve(steps):
    r = [0.0] * (W + 1)
    for a, b, p in steps:
        for d in range(int(a), min(int(b), W) + 1):
            r[d] = max(r[d], p)
    return r

def main():
    out = {}
    for p, v in R.items():
        if v["status"] not in OBS:
            out[p] = dict(status=v["status"], area=None)
            continue
        r = curve(v["steps"])
        out[p] = dict(status=v["status"],
                      area=round(sum(r[1:W + 1]) / W, 2),
                      r30=r[30], r60=r[60], r90=r[90], r180=r[W],
                      span=max((int(b) for _, b, _ in v["steps"]), default=0),
                      tiers=len(v["steps"]))
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = collections.Counter(v["status"] for v in out.values())
    n = [v for v in out.values() if v["area"] is not None]
    a = sorted(v["area"] for v in n)
    sys.stderr.write("  %d 件 → %s\n" % (len(out), OUT))
    sys.stderr.write("  強度を算出できた %d 件（%s）\n" % (len(n), dict(c)))
    sys.stderr.write("  強度  中央値 %.1f / 平均 %.1f / 最小 %.1f / 最大 %.1f\n"
                     % (a[len(a)//2], sum(a)/len(a), a[0], a[-1]))

if __name__ == "__main__":
    main()
