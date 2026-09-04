"""予測Φ2：DefiLlama から M(t) の代理系列と活動の系列を取得する。

M(t) の代理には TVL（手続き上に置かれた資産）を用いる。
途絶の判定に TVL を使うと予測が定義から自明になるため
（M(t)→0 を途絶と呼べば「途絶に先行して M(t) が減る」は循環）、
活動の系列は手数料（フロー）から別に取る。

出力（いずれも1行1プロトコル）
  data/raw/phi/llama_tvl.jsonl   {"slug","category","chains","tvl":[[date,usd],...]}
  data/raw/phi/llama_fees.jsonl  {"slug","fees":[[date,usd],...]}
"""
import json, os, sys, time, urllib.request

BASE = "https://api.llama.fi"
HDR = {"User-Agent": "curl/8.5.0", "Accept": "*/*"}
INTERVAL = 1.0


def get(path, retry=3):
    for k in range(retry):
        try:
            req = urllib.request.Request(BASE + path, headers=HDR)
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception as e:
            if k == retry - 1:
                raise
            time.sleep(3 * (k + 1))


def series(chain_tvls, chain):
    """{"date":…, "totalLiquidityUSD":…} の列を [[date, usd], …] に畳む。"""
    d = (chain_tvls or {}).get(chain) or {}
    return [[x["date"], x["totalLiquidityUSD"]] for x in (d.get("tvl") or [])]


def run(targets, out_path, kind):
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                done.add(json.loads(line)["slug"])
            except Exception:
                pass
    f = open(out_path, "a")
    t0 = time.time()
    for n, slug in enumerate(targets, 1):
        if slug in done:
            continue
        try:
            if kind == "tvl":
                d = get(f"/protocol/{slug}")
                rec = {"slug": slug,
                       "category": d.get("category"),
                       "chains": d.get("chains"),
                       "listedAt": d.get("listedAt"),
                       "tvl_eth": series(d.get("chainTvls"), "Ethereum"),
                       "tvl_all": [[x["date"], x["totalLiquidityUSD"]]
                                   for x in (d.get("tvl") or [])]}
            else:
                d = get(f"/summary/fees/{slug}")
                rec = {"slug": slug,
                       "fees": d.get("totalDataChart") or []}
        except Exception as e:
            print(f"  ERR {slug}: {str(e)[:100]}", file=sys.stderr, flush=True)
            time.sleep(INTERVAL)
            continue
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        f.flush()
        if n % 50 == 0:
            print(f"  {n}/{len(targets)}  {(time.time()-t0)/60:.1f}min",
                  flush=True)
        time.sleep(INTERVAL)
    f.close()


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "tvl"
    if kind == "fees":
        # 手数料の系列を持つのは Ethereum の 587 件のみ（overview で確認）
        eth = json.load(open("data/raw/phi/fees_slugs.json"))
    else:
        prot = json.load(open("data/raw/phi/llama_protocols.json"))
        eth = [p["slug"] for p in prot
               if "Ethereum" in (p.get("chains") or [])]
    print(f"対象 {len(eth)} プロトコル（{kind}）", flush=True)
    run(eth, f"data/raw/phi/llama_{kind}.jsonl", kind)
    print("完了", flush=True)
