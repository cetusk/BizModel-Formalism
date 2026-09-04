"""ブロック番号から時刻への対応表を作る。内挿の基点にする。"""
import json, time, urllib.request

RPC = "https://eth.drpc.org"
HDR = {"Content-Type": "application/json",
       "User-Agent": "curl/8.5.0", "Accept": "*/*"}


def rpc(m, p, retry=3):
    b = json.dumps({"jsonrpc": "2.0", "id": 1,
                    "method": m, "params": p}).encode()
    for k in range(retry):
        try:
            r = urllib.request.Request(RPC, data=b, headers=HDR)
            with urllib.request.urlopen(r, timeout=90) as x:
                d = json.load(x)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception:
            if k == retry - 1:
                raise
            time.sleep(3 * (k + 1))


if __name__ == "__main__":
    head = int(rpc("eth_blockNumber", []), 16)
    marks = [int(4_000_000 + (head - 4_000_000) * i / 300) for i in range(301)]
    out = []
    for b in marks:
        ts = int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        out.append([b, ts])
        time.sleep(0.4)
    json.dump(out, open("data/raw/phi/block_time.json", "w"))
    print(f"{len(out)} 点、block {marks[0]}--{marks[-1]}")
