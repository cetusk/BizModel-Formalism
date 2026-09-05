"""予測Φ4／Φ3：枠B（分野中立な稼働 Φ の枠）を台帳から構成する。

抽出規則（第4.4節で確定、変更しない）
  基準期間 2026-08-01--08-31（UTC）= block 25,656,292--25,878,704
  等間隔に 28 の窓、各 8 ブロック（計 224 ブロック、0.10%）
  稼働の指標は、窓の中で当該アドレスが発火した記録の件数
  下限は 30 件、判定するのは上位 200 件

出力 data/raw/phi/phi4_frameb.tsv  address / n_logs / n_topics0
"""
import json, time, urllib.request, collections

RPC = "https://eth.drpc.org"
HDR = {"Content-Type": "application/json",
       "User-Agent": "curl/8.5.0", "Accept": "*/*"}
NWIN, WIN = 28, 8
INTERVAL = 1.0


def rpc(m, p, retry=4):
    b = json.dumps({"jsonrpc": "2.0", "id": 1,
                    "method": m, "params": p}).encode()
    for k in range(retry):
        try:
            r = urllib.request.Request(RPC, data=b, headers=HDR)
            with urllib.request.urlopen(r, timeout=180) as x:
                d = json.load(x)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception:
            if k == retry - 1:
                raise
            time.sleep(3 * (k + 1))


def main():
    rng = json.load(open("data/raw/phi/aug2026_range.json"))
    a, b = rng["start"], rng["end"]
    cnt = collections.Counter()
    tops = collections.defaultdict(set)
    tot = 0
    t0 = time.time()
    for i in range(NWIN):
        s = a + (b - a) * i // NWIN
        logs = rpc("eth_getLogs", [{"fromBlock": hex(s),
                                    "toBlock": hex(s + WIN - 1)}])
        for l in logs:
            cnt[l["address"]] += 1
            if l["topics"]:
                tops[l["address"]].add(l["topics"][0])
        tot += len(logs)
        print(f"  窓 {i+1}/{NWIN}  block {s}  ログ {len(logs):>6}  "
              f"累計 {tot:,}", flush=True)
        time.sleep(INTERVAL)

    with open("data/raw/phi/phi4_frameb.tsv", "w") as f:
        f.write("address\tn_logs\tn_topics0\n")
        for addr, n in cnt.most_common():
            f.write(f"{addr}\t{n}\t{len(tops[addr])}\n")
    ge30 = sum(1 for v in cnt.values() if v >= 30)
    print(f"\n  {NWIN*WIN} ブロック、ログ {tot:,} 件、"
          f"相異なるアドレス {len(cnt):,}")
    print(f"  下限 30 件以上: {ge30} 件 → 上位 200 件を判定の対象とする")
    print(f"  経過 {(time.time()-t0)/60:.1f}min")


if __name__ == "__main__":
    main()
