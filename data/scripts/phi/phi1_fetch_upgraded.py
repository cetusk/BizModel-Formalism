"""予測Φ1：Upgraded(address) ログを全期間走査する。

Upgraded(address) はプロキシの生成時にも発火するため、
アドレスごとの1回目は配備、2回目以降が改修にあたる。
母集団（改修されなかったものを含む）を得るには全件が要る。

出力 data/raw/phi/upgraded_logs.jsonl の1行 =
  {"a": プロキシのアドレス, "b": ブロック番号, "i": 新しい実装のアドレス}
再開可能。data/raw/phi/upgraded_progress.json に到達点を書く。
"""
import json, os, sys, time, urllib.request

RPC = "https://eth.drpc.org"
TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
START = 4_000_000          # EIP-1967 以前。取りこぼしを避けて余裕をとる
WMAX, WMIN = 5000, 250     # 窓は密度に応じて伸縮させる
INTERVAL = 0.6             # 秒。公開エンドポイントへの配慮

OUT = "data/raw/phi/upgraded_logs.jsonl"
PROG = "data/raw/phi/upgraded_progress.json"
HDR = {"Content-Type": "application/json",
       "User-Agent": "curl/8.5.0", "Accept": "*/*"}


def rpc(method, params, retry=4):
    body = json.dumps({"jsonrpc": "2.0", "id": 1,
                       "method": method, "params": params}).encode()
    last = None
    for k in range(retry):
        try:
            req = urllib.request.Request(RPC, data=body, headers=HDR)
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception as e:
            last = e
            time.sleep(2 * (k + 1))
    raise last


def main():
    head = int(rpc("eth_blockNumber", []), 16)
    start = START
    mode = "w"
    if os.path.exists(PROG):
        start = json.load(open(PROG))["next"]
        mode = "a"
        # 中断した窓の分が途中まで書かれている場合があるので落とす
        if os.path.exists(OUT):
            keep = [l for l in open(OUT)
                    if json.loads(l)["b"] < start]
            open(OUT, "w").writelines(keep)
            print(f"  再開：{start} 以降の {len(keep)} 行を残した", flush=True)
    out = open(OUT, mode)
    w, n = WMAX, 0
    t0 = time.time()
    while start <= head:
        end = min(start + w - 1, head)
        try:
            logs = rpc("eth_getLogs", [{"fromBlock": hex(start),
                                        "toBlock": hex(end),
                                        "topics": [TOPIC]}], retry=2)
        except Exception as e:
            if w > WMIN:                     # 密度が高い区間は窓を詰める
                w = max(WMIN, w // 2)
                continue
            print(f"  SKIP {start}-{end}: {str(e)[:90]}", file=sys.stderr)
            start = end + 1
            w = WMAX
            continue
        for l in logs:
            # 実装アドレスは indexed が普通だが、そうでない実装もある。
            # その場合は data の先頭ワードに入る。
            if len(l["topics"]) >= 2:
                impl = "0x" + l["topics"][1][-40:]
            else:
                d = l.get("data") or "0x"
                impl = "0x" + d[2:][:64][-40:] if len(d) >= 66 else ""
            out.write(json.dumps({"a": l["address"],
                                  "b": int(l["blockNumber"], 16),
                                  "i": impl}) + "\n")
        n += len(logs)
        out.flush()
        json.dump({"next": end + 1, "head": head, "logs": n}, open(PROG, "w"))
        if end % 500_000 < w:
            el = time.time() - t0
            print(f"  block {end:>9}/{head}  logs={n:>7}  "
                  f"{el/60:.1f}min", flush=True)
        start = end + 1
        if len(logs) < 500 and w < WMAX:     # 疎な区間では窓を戻す
            w = min(WMAX, w * 2)
        time.sleep(INTERVAL)
    out.close()
    print(f"完了 logs={n} 経過={(time.time()-t0)/60:.1f}min")


if __name__ == "__main__":
    main()
