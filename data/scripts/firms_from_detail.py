# 事業所詳細ページから、検索結果一覧と同じ形の企業単位データを組み立てる。
#
# 【なぜ要るか】一覧のテキストは個社データなので再配布しない。
#   それを唯一の入口にすると、テキストが無い環境では予測X・Y・Zを再現できない。
#   詳細ページには一覧と同じ量がすべて含まれるので、
#   **許可番号の一覧（permits.tsv）だけを種として同じ標本を作り直せる。**
#
# 【対応】一覧の列 → 詳細ページの位置
#   emp_all/emp/spot  … 年度別パネルの最新年度（就職者の3列）
#   sep               … 同じ行の離職者数。最新年度は「-」で確定しない
#   fee_raw/to        … 職種別の表。手数料は最新年度、離職率はその前年度
#   nintei/yuryo      … 備考の「適正」「優良」
#
# 【一覧に無い列】branches（事業所数）は作れない。詳細ページは1事業所を指すため。
#   名寄せの重みを論じる第17.5節の注はテキスト側の観察であり、ここでは再現しない。
import io, os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
DET  = os.path.join(HERE, "..", "derived", "jinzai_detail.json")
SEED = os.path.join(HERE, "..", "raw", "jinzai", "permits.tsv")
OUT  = os.path.join(HERE, "..", "derived", "jinzai_firms_detail.json")

def num(x):
    if x is None:
        return None
    x = str(x).replace("％", "").replace("円", "").replace(",", "").strip()
    return None if x in ("", "-", "－") else float(x)

def main():
    det = {r["permit"]: r for r in json.load(io.open(DET, encoding="utf-8"))}
    want = []
    for line in io.open(SEED, encoding="utf-8"):
        if line.startswith("#") or "\t" not in line:
            continue
        p, j = [x.strip() for x in line.split("\t")[:2]]
        if re.match(r"^\d{2}-.-\d{6}$", p):
            want.append((p, j))

    out, miss_page, miss_job = [], set(), []
    for p, j in want:
        d = det.get(p)
        if d is None:
            miss_page.add(p)
            continue
        jj = [x for x in d["jobs"] if x["job"] == j]
        if not jj:
            miss_job.append((p, j))
            continue
        jj = jj[0]
        pan = d["panel"][-1] if d["panel"] else {}
        fee = jj.get("fee_raw")
        out.append(dict(
            permit=p, pref=p[:2], kind=p.split("-")[1], firm=d.get("firm") or "",
            emp_all=pan.get("emp_all"), emp=pan.get("emp"),
            spot=pan.get("spot"), sep=pan.get("sep"),
            job=j, fee_raw=fee or "-",
            fee_pct=num(fee) if fee and "％" in fee else None,
            fee_yen=num(fee) if fee and "円" in fee else None,
            to=num(jj.get("to_raw")),
            yuryo=bool(d.get("yuryo")), nintei=bool(d.get("nintei")),
            fee_year=jj.get("fee_year"), to_year=jj.get("to_year"),
            src="detail"))
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.stderr.write("  %d / %d 行  （詳細ページ未取得 %d 社、職種が無い %d 行） → %s\n"
                     % (len(out), len(want), len(miss_page), len(miss_job), OUT))
    if miss_job:
        sys.stderr.write("  職種が無い例: %s\n" % (miss_job[:3],))

if __name__ == "__main__":
    main()
