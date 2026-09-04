"""予測Φ4：枠A（DefiLlama の Ethereum プロトコル）を整理する。

第13.1節の前提(2)を満たさないもの（状態を事業者が保持するもの）を
事前確定の規則で除いたうえで、活動量の代理である TVL で順位をつける。

判定は人手で行うため、判定に要る記述を1件1行にまとめて出す。
"""
import json, csv, collections

# 前提(2)を満たさない類型。0.1節の事前確定。結果を見てから変えない。
EXCLUDE_CATEGORY = {
    "CEX",                    # 状態を取引所が保持する
    "Staking Pool",           # 実体が保管型のものを含むため個別に見る → 下の要確認へ
}
# 保管型かどうかがカテゴリだけでは決まらないもの。人手で判定する。
REVIEW_CATEGORY = {
    "Bridge", "Canonical Bridge", "Cross Chain Bridge",
    "RWA", "Staking Pool", "Services",
}


def main():
    prot = json.load(open("data/raw/phi/llama_protocols.json"))
    eth = [p for p in prot if "Ethereum" in (p.get("chains") or [])]

    rows = []
    for p in eth:
        cat = p.get("category") or ""
        if cat in EXCLUDE_CATEGORY and cat not in REVIEW_CATEGORY:
            status = "除外"
        elif cat in REVIEW_CATEGORY:
            status = "要確認"
        else:
            status = "対象"
        rows.append({
            "slug": p["slug"],
            "name": p.get("name"),
            "category": cat,
            "tvl": round(p.get("tvl") or 0),
            "listedAt": p.get("listedAt") or "",
            "url": p.get("url") or "",
            "address": p.get("address") or "",
            "区分内": status,
            "族": "",          # 人手で埋める
            "型": "",
            "根拠": "",
            "description": (p.get("description") or "").replace("\n", " ")[:400],
            "methodology": (p.get("methodology") or "").replace("\n", " ")[:400],
        })
    rows.sort(key=lambda r: -r["tvl"])

    out = "data/raw/phi/phi4_frame_a.tsv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                           delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)

    c = collections.Counter(r["区分内"] for r in rows)
    print(f"枠A {len(rows)} 件 → {dict(c)}")
    tgt = [r for r in rows if r["区分内"] != "除外"]
    print(f"判定の対象 {len(tgt)} 件、うち TVL>0 が "
          f"{sum(1 for r in tgt if r['tvl']>0)} 件、"
          f"TVL=0 が {sum(1 for r in tgt if r['tvl']==0)} 件")
    print(f"\n{out} に書いた。上位10件：")
    for r in tgt[:10]:
        print(f"  {r['tvl']/1e9:7.2f}B  {r['slug']:<24} {r['category']:<18} {r['区分内']}")


if __name__ == "__main__":
    main()
