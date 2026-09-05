"""予測Φ1：実装コントラクトのバイトコードを取り、依存の数を数える。

依存の数の定義（第1.4節で確定、変更しない）
  実装バイトコードに PUSH20 で埋め込まれた、相異なるアドレスの数。
  ゼロアドレスと 2^32 未満の値（アドレスではなく定数とみなす）は除く。

192万のプロキシが指す実装は 76,609 種しかないので、実装単位で取れば足りる。
publicnode は 500 件までのバッチに応じる。
"""
import json, re, time, urllib.request, collections, os

URL = "https://ethereum-rpc.publicnode.com"
HDR = {"Content-Type": "application/json",
       "User-Agent": "curl/8.5.0", "Accept": "*/*"}
BATCH = 500
INTERVAL = 1.0
OUT = "data/raw/phi/phi1_deps.tsv"
PUSH20 = re.compile(r"73([0-9a-f]{40})")


def deps_of(code):
    """PUSH20 で埋め込まれた相異なるアドレスの数。"""
    if not code or len(code) < 4:
        return 0
    cand = {m.group(1) for m in PUSH20.finditer(code[2:])}
    return sum(1 for c in cand if int(c, 16) > 0xffffffff)


def post(payload, retry=4):
    body = json.dumps(payload).encode()
    for k in range(retry):
        try:
            req = urllib.request.Request(URL, data=body, headers=HDR)
            with urllib.request.urlopen(req, timeout=240) as x:
                return json.load(x)
        except Exception:
            if k == retry - 1:
                raise
            time.sleep(4 * (k + 1))


def main():
    impl = collections.Counter()
    for l in open("data/raw/phi/upgraded_logs.jsonl"):
        r = json.loads(l)
        if r["i"] and int(r["i"], 16) != 0:
            impl[r["i"]] += 1
    addrs = sorted(impl)
    print(f"実装アドレス {len(addrs):,} 件", flush=True)

    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            done.add(l.split("\t")[0])
        print(f"  取得済み {len(done):,} 件から再開", flush=True)
    todo = [a for a in addrs if a not in done]

    f = open(OUT, "a")
    if not done:
        f.write("impl\tn_proxy\tcode_bytes\tn_deps\n")
    t0 = time.time()
    for i in range(0, len(todo), BATCH):
        sub = todo[i:i + BATCH]
        res = post([{"jsonrpc": "2.0", "id": j, "method": "eth_getCode",
                     "params": [a, "latest"]} for j, a in enumerate(sub)])
        by = {r["id"]: r.get("result") for r in res if isinstance(r, dict)}
        for j, a in enumerate(sub):
            code = by.get(j) or "0x"
            f.write(f"{a}\t{impl[a]}\t{(len(code)-2)//2}\t{deps_of(code)}\n")
        f.flush()
        if (i // BATCH) % 20 == 0:
            print(f"  {i+len(sub):>6}/{len(todo):,}  "
                  f"{(time.time()-t0)/60:.1f}min", flush=True)
        time.sleep(INTERVAL)
    f.close()
    print(f"完了 経過 {(time.time()-t0)/60:.1f}min", flush=True)


if __name__ == "__main__":
    main()
