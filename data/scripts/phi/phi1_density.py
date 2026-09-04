"""予測Φ1：Upgraded(address) ログの密度を測り、全期間の取得量を見積もる。

Upgraded(address) はプロキシの生成時にも発火する。改修の検出には
アドレスごとの2回目以降を数える必要があるため、まず全件の密度を測る。
"""
import json, time, urllib.request, sys

RPC = "https://eth.drpc.org"
TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
WINDOW = 1000
INTERVAL = 1.0   # 秒。公開エンドポイントへの配慮


def rpc(method, params, retry=3):
    body = json.dumps({"jsonrpc": "2.0", "id": 1,
                       "method": method, "params": params}).encode()
    for k in range(retry):
        try:
            req = urllib.request.Request(
                RPC, data=body, headers={"Content-Type": "application/json",
                         "User-Agent": "curl/8.5.0", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception as e:
            if k == retry - 1:
                raise
            time.sleep(3 * (k + 1))


def count(start):
    logs = rpc("eth_getLogs", [{"fromBlock": hex(start),
                                "toBlock": hex(start + WINDOW - 1),
                                "topics": [TOPIC]}])
    addrs = set(l["address"] for l in logs)
    return len(logs), len(addrs), sum(len(json.dumps(l)) for l in logs)


if __name__ == "__main__":
    head = int(rpc("eth_blockNumber", []), 16)
    # プロキシの普及以前（~2018年、block 5e6）から現在まで等間隔に標本をとる
    marks = [int(5.0e6 + (head - 5.0e6) * i / 24) for i in range(25)]
    out = []
    for b in marks:
        try:
            n, na, nb = count(b)
        except Exception as e:
            print(f"  block {b}: ERR {e}", file=sys.stderr)
            continue
        ts = int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        out.append({"block": b, "timestamp": ts, "logs": n,
                    "addresses": na, "bytes": nb})
        print(f"  {b:>9}  {time.strftime('%Y-%m', time.gmtime(ts))}  "
              f"logs={n:>4}  addr={na:>4}  bytes={nb:>7}", flush=True)
        time.sleep(INTERVAL)
    json.dump({"head": head, "window": WINDOW, "samples": out},
              open("data/raw/phi/phi1_density.json", "w"), indent=1)
