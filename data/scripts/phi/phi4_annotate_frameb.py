"""枠B の上位 200 件に、判定に要る情報を付ける。

Blockscout（無認証）からコントラクト名・検証の有無・トークン情報を取る。
判定そのものは人手で行う。ここは材料をそろえるだけである。
"""
import csv, json, time, urllib.request

BASE = "https://eth.blockscout.com/api/v2"
HDR = {"User-Agent": "curl/8.5.0", "Accept": "application/json"}
N = 200
INTERVAL = 0.5


def get(path):
    try:
        req = urllib.request.Request(BASE + path, headers=HDR)
        with urllib.request.urlopen(req, timeout=60) as x:
            return json.load(x)
    except Exception:
        return None


def main():
    rows = list(csv.DictReader(open("data/raw/phi/phi4_frameb.tsv"),
                               delimiter="\t"))
    top = [r for r in rows if int(r["n_logs"]) >= 30][:N]
    print(f"下限 30 件以上 {sum(1 for r in rows if int(r['n_logs'])>=30)} 件 → "
          f"上位 {len(top)} 件に注記を付ける")

    out = []
    for n, r in enumerate(top, 1):
        a = r["address"]
        d = get(f"/addresses/{a}") or {}
        tok = d.get("token") or {}
        impl = d.get("implementations") or []
        out.append({
            "rank": n, "address": a,
            "n_logs": r["n_logs"], "n_topics0": r["n_topics0"],
            "name": (d.get("name") or "").replace("\t", " "),
            "is_contract": d.get("is_contract"),
            "verified": d.get("is_verified"),
            "proxy": bool(impl),
            "token_type": tok.get("type") or "",
            "token_name": (tok.get("name") or "").replace("\t", " "),
            "族": "", "型": "", "根拠": "",      # Φ4：人手で埋める
            "tau_符号": "", "tau_日数": "",       # Φ3：人手で埋める
        })
        if n % 25 == 0:
            print(f"  {n}/{len(top)}", flush=True)
        time.sleep(INTERVAL)

    p = "data/raw/phi/phi4_frameb_annotated.tsv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(out)
    named = sum(1 for r in out if r["name"])
    print(f"名前が取れた {named}/{len(out)} 件 → {p}")


if __name__ == "__main__":
    main()
