"""枠B の上位 200 件を第10.9節 表10.8 の順序で判定する。

判定順序（変更しない）
  1 受益者と支払者が異なるか（自由度(3)）      → 族7
  2 第三者間の取引に介在するか                 → 族6
  3 π が ω に可測か（自由度(4)）               → 族5
  4 履行を分割し π を意図的に偏らせるか        → 族4
  5 資産が先行し時間または稼働に比例して回収か  → 族3
  6 反復性があるか（自由度(6)）                → 族2、なければ族1

**順序の前に「これは Φ か」を問う。** 表10.8 は Φ を所与としている。
履行 δ と決済 π が区別できないものは Φ でなく、判定の対象にならない。
  - トークン台帳そのもの：決済の媒体であって、δ と π の対がない
  - なりすまし：履行が存在しない
  - 対価を伴わない基盤：π がない

Φ3 の τ（履行から決済までの遅れ）の符号も同時に埋める。
  −  決済が履行に先行する（前受け）
  0  同一の状態遷移（原子的）
  +  決済が履行に後れる
"""
import csv, re, unicodedata

SRC = "data/raw/phi/phi4_frameb_annotated.tsv"
OUT = "data/raw/phi/phi4_frameb_judged.tsv"

# --- なりすましの検出 -------------------------------------------------
# 主要な決済媒体の名を、Unicode の合成や類似字で似せたもの。
CANON = {"usdt": "TetherToken", "usdc": "USDC", "eth": "WETH9",
         "tetherusd": "TetherToken", "usdcoin": "USDC"}
REAL = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
}


def norm(s):
    """結合文字と非 ASCII を落として素の綴りに戻す。"""
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", t.lower())


def is_spoof(r):
    n = norm(r["name"]) or norm(r["token_name"])
    if not n:
        return False
    if r["address"].lower() in REAL:
        return False
    return n in CANON or n in ("token", "ether", "usd")


# --- 個別に読んで確定したもの（名前の規則より優先する） -----------------
# ソースを読んで判断した。根拠は PHI.md 第4.8節に記す。
OVERRIDE = {
    # ERC-4337 の入口。利用者操作を束ねて実行するだけで、自らは対価を取らない。
    "0x0000000071727de22e5e9d8baf0edac6f37da032":
        ("—", "—", "Φでない。ERC-4337 の実行の入口。自らは δ も π も持たない基盤", ""),
    "0x4337084d9e255ff0702461cf8895ce9e3b5ff108":
        ("—", "—", "Φでない。ERC-4337 の実行の入口。自らは δ も π も持たない基盤", ""),
    "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789":
        ("—", "—", "Φでない。ERC-4337 の実行の入口。自らは δ も π も持たない基盤", ""),
    # ガス代の肩代わり。利用者は無償、出資者が支払う。
    # ただし誰を対象にするかは署名でオフチェーンに判定を出している（11 箇所）。
    "0x777777777777aec03fd955926dbf81597e66834c":
        ("7", "7-2", "判定1。利用者は無償、出資者が肩代わりする。"
                     "ただし受益者の選定は署名によりオフチェーンで行う", "−"),
    # Uniswap v4 のフック。手数料の一部を作成者へ回すが、
    # 支払者（交換者）と受益者（交換者）は同一。介在するので族6。
    "0x025a386eaa79f6067d29848fd05ccc71beab20cc":
        ("6", "6-1", "判定2。交換に介在し取引額に応じて手数料を取る。"
                     "作成者への配分は手数料の分配であって受益者の分離ではない", "0"),
    # LI.FI の周辺部品。手数料を指定先へ転送するだけ。
    "0x685527c551cc40ce1f1c9818cd8683307076e4ed":
        ("—", "—", "Φでない。橋渡し（LI.FI）の周辺部品。手数料の転送のみで δ を持たない", ""),
    # 出品・再値付け・取得を扱う市場。
    "0xb276f62db0ce8ca2ca5bc522695be604521eac1c":
        ("6", "6-1", "判定2。出品と取得に介在する市場（FWA）", "0"),
    "0x6a1a1c0cfb3d3c538e13d36d608a5bcaa992fc78":
        ("6", "6-1", "判定2。同上の報酬側（FWA）", "0"),
    # UMA の分散型検証機構。要求者が手数料を払い価格の解決を受ける。
    # --- トークン台帳であって Φ でないもの（名前の規則が誤って拾った） ---
    # 統治トークン、受取証（利息付き・ステーク済み・持ち高）はいずれも台帳であり、
    # 手続きそのものではない。
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":
        ("—", "—", "Φでない。統治トークンの台帳（UNI）", ""),
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9":
        ("—", "—", "Φでない。統治トークンの台帳（AAVE）", ""),
    "0xd9fcd98c322942075a5c3860693e9f4f03aae07b":
        ("—", "—", "Φでない。統治トークンの台帳（EUL）", ""),
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0":
        ("—", "—", "Φでない。包み直した受取証の台帳（wstETH）", ""),
    "0xae78736cd615f374d3085123a210448e74fc6393":
        ("—", "—", "Φでない。ステーク済みの受取証の台帳（rETH）", ""),
    "0x9d39a5de30e57443bff2a8307a4256c8797a3497":
        ("—", "—", "Φでない。ステーク済みの受取証の台帳（sUSDe）", ""),
    "0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c":
        ("—", "—", "Φでない。利息付き受取証の台帳（aEthUSDC）", ""),
    "0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8":
        ("—", "—", "Φでない。利息付き受取証の台帳（aEthWETH）", ""),
    "0xc36442b4a4522e871399cd717abdd847ab11fe88":
        ("—", "—", "Φでない。持ち高を表す受取証の台帳（Uniswap v3 Positions）", ""),
    "0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e":
        ("—", "—", "Φでない。持ち高を表す受取証の台帳（Uniswap v4 Positions）", ""),
    # VaultV2 は ERC-4626 の金庫。受取証を兼ねるが、預けた資産を運用して
    # 手数料を取る手続きそのものであり Φ である（UniswapV2Pair と同じ扱い）。
    "0xbeef007ecfbfdf9b919d0050821a9b6dbd634ff0":
        ("3", "3-2", "判定5。資産が先行し、時間に比例して回収する金庫（ERC-4626）", "+"),
    "0x004395edb43efca9885cedad51ec9faf93bd34ac":
        ("2", "2-2", "判定6。要求ごとに反復して手数料を取る解決の役務（UMA）。"
                     "順序を変えれば族6にも当たる（注 rem:assignment-order-dependence）", "−"),
}

# --- 名前から性格を判定する規則 ---------------------------------------
# (正規表現, 族, 型, 根拠, tau符号)
RULES = [
    # 判定1：受益者と支払者が異なる → 族7
    (r"paymaster", "7", "7-2", "判定1。利用者は無償、出資者が肩代わりする", "−"),
    # 判定2：第三者間の取引に介在する → 族6
    (r"router|aggregation|aggregator|dexrouter|metaswap|settlement|seaport|"
     r"seadrop|swap|pool|pair|diamond|relay|forwarder|offramp|endpoint|"
     r"uln302|rollup|bridge|settler|dynamicroute|swiftsource|mayan", "6", "6-1",
     "判定2。第三者間の取引に介在し、取引額に応じて手数料を得る", "0"),
    # 判定3：π が ω に可測 → 族5
    (r"lido|steth|reth|rockettoken|stakedusde|stakingrouter|numeraistaking|"
     r"^staked", "5", "5-2", "判定3。手数料が運用成果に連動する", "+"),
    (r"vault|morpho|euler|^aave|aavev3|irm|^vat$|dsslitepsm|fluidliquidity|"
     r"^core$|psm", "3", "3-2",
     "判定5。資産が先行し、時間に比例して利息を回収する", "+"),
    # 判定6：反復性
    (r"vrfcoordinator|oracle|^twap", "2", "2-2", "判定6。要求ごとに反復して課金する", "0"),
]

INFRA = re.compile(r"permit2|gnosissafeproxy|multicall|^proxy$|^erc1967proxy$|"
                   r"^transparentupgradeableproxy$|^adminupgradableproxy$|"
                   r"^beaconproxy$|^appproxyupgradeable$|^tokenproxy$|"
                   r"^initializableimmutableadmin|batchtransfer|batchzerotoken|"
                   r"mixedbatchtransfer|aggregatorguard|hook$|adapter$|"
                   r"^backedtokenproxy$|claimminter")


def judge(r):
    o = OVERRIDE.get(r["address"].lower())
    if o:
        return o
    name = (r["name"] or "").strip()
    n = name.lower()
    if is_spoof(r):
        return ("—", "—", "Φでない。決済媒体の名をまねた identity のなりすまし。履行がない", "")
    if r["token_type"] and not any(re.search(p, n) for p, *_ in RULES):
        if INFRA.search(n) and r["token_type"]:
            pass
        return ("—", "—",
                f"Φでない。{r['token_type']} の台帳そのもの。決済の媒体であって δ と π の対がない", "")
    for pat, fam, typ, why, tau in RULES:
        if re.search(pat, n):
            return (fam, typ, why, tau)
    if INFRA.search(n):
        return ("—", "—", "Φでない。対価を伴わない基盤（承認・保管・複数呼び出しの束ね）", "")
    if not name:
        return ("?", "?", "判定不能。検証済みソースも名前も無い", "")
    return ("?", "?", "判定保留。名前だけでは δ と π を同定できない", "")


def main():
    rows = list(csv.DictReader(open(SRC), delimiter="\t"))
    for r in rows:
        fam, typ, why, tau = judge(r)
        r["族"], r["型"], r["根拠"], r["tau_符号"] = fam, typ, why, tau
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    import collections
    c = collections.Counter(r["族"] for r in rows)
    print(f"  {len(rows)} 件の判定")
    for k in sorted(c, key=lambda x: (x == "?", x == "—", x)):
        print(f"    族{k}: {c[k]:>3} 件")
    print(f"\n  → {OUT}")
    print("\n  Φ でないとした内訳:")
    d = collections.Counter(r["根拠"].split("。")[1] if "。" in r["根拠"] else r["根拠"]
                            for r in rows if r["族"] == "—")
    for k, v in d.most_common():
        print(f"    {v:>3} 件  {k}")


if __name__ == "__main__":
    main()
