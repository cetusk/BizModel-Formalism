"""予測Φ1：本走査で取り逃した区間を、窓を詰めて埋める。

全数を謳う以上、穴を残さない。窓を 25 ブロックまで落とし、
それでも通らなければ 1 ブロックずつ試す。
"""
import json, re, sys, time, urllib.request

RPC = "https://eth.drpc.org"
TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
HDR = {"Content-Type": "application/json",
       "User-Agent": "curl/8.5.0", "Accept": "*/*"}
LOG = "data/raw/phi/phi1_fetch.log"
OUT = "data/raw/phi/upgraded_logs.jsonl"


def rpc(params, retry=5):
    body = json.dumps({"jsonrpc": "2.0", "id": 1,
                       "method": "eth_getLogs", "params": params}).encode()
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
            time.sleep(3 * (k + 1))
    raise last


def fetch(a, b):
    return rpc([{"fromBlock": hex(a), "toBlock": hex(b), "topics": [TOPIC]}])


def main():
    gaps = []
    for line in open(LOG):
        m = re.search(r"SKIP (\d+)-(\d+)", line)
        if m:
            gaps.append((int(m.group(1)), int(m.group(2))))
    gaps = sorted(set(gaps))
    print(f"取り逃した区間 {len(gaps)} 件、計 "
          f"{sum(b - a + 1 for a, b in gaps):,} ブロック")

    got, failed = [], []
    for a, b in gaps:
        cur, n = a, 0
        while cur <= b:
            for w in (25, 5, 1):
                end = min(cur + w - 1, b)
                try:
                    logs = fetch(cur, end)
                except Exception as e:
                    if w == 1:
                        failed.append((cur, end, str(e)[:60]))
                        cur = end + 1
                    continue
                got.extend(logs)
                n += len(logs)
                cur = end + 1
                time.sleep(0.4)
                break
            else:
                cur += 1
        print(f"  {a}-{b}: {n} 件", flush=True)

    with open(OUT, "a") as o:
        for l in got:
            if len(l["topics"]) >= 2:
                impl = "0x" + l["topics"][1][-40:]
            else:
                d = l.get("data") or "0x"
                impl = "0x" + d[2:][:64][-40:] if len(d) >= 66 else ""
            o.write(json.dumps({"a": l["address"],
                                "b": int(l["blockNumber"], 16),
                                "i": impl}) + "\n")
    print(f"補充 {len(got)} 件を追記した")
    if failed:
        print("なお埋まらなかった区間:", failed)
        json.dump(failed, open("data/raw/phi/phi1_unfilled.json", "w"))
    else:
        print("**全区間を埋めた。母集団に穴はない。**")


if __name__ == "__main__":
    main()
