# BizModel-Formalism

**キャッシュフロー構造としてのビジネスモデル** — 定式化・類型論・調査設計

> **v0.17.0**（2026年9月3日）— **本稿は建設中です。**
> 理論の構成、命題、実証の結論はいずれも変更されうるものです。
> 引用される場合は版を明記してください。

ビジネスモデルを「履行スケジュールから決済スケジュールへの写像 Φ」として定式化し、
信用ポジション κ、自己金融可能成長率 g*、余剰の三分解を導く。

📖 **[HTML で読む](https://cetusk.github.io/BizModel-Formalism/book/book.html)** ・
📄 **[PDF](https://cetusk.github.io/BizModel-Formalism/book.pdf)**（145ページ）

## 構成

| | |
|---|---|
| 第I部 | 理論 — 定義、命題、証明 |
| 第II部 | 写像の空間と制約 — 27類型、制約下の部分空間、無人化 |
| 第III部 | 方法論 — 検証障害の分類、選択バイアス、事前登録 |
| 第IV部 | 実証 — 理論量の測定対応、族2・族5、法人企業統計、手数料 |
| 第V部 | 総括 — 到達点と未解決問題 |
| 付録 | 証明の補遺、記号一覧、既存理論との対応、データ源、改訂履歴 |

## この文書が主張しないこと

**予測理論ではない。** 事前登録した予測の多くが棄却された。
枠組みは記述の道具として機能するが、記述された量が何を予測するかについて確立した結果を持たない。

**個々の構成要素の多くは既存理論に対応がある。** 取引信用、bonding argument、
シグナリング、前払い契約の研究などが、同一の和の項として現れることを示す点に寄与がある。

検討の過程で撤回した主張は付録Eに記録した。本文には訂正後の内容のみを残している。

## ビルド

```bash
cd src
lualatex book.tex && lualatex book.tex && lualatex book.tex   # PDF
./build-figures.sh                                            # 図を SVG 化
make4ht -l -f html5+dvisvgm_hashes -d ../docs/book book.tex "mathml,2"
python3 inject-sidebar.py ../docs/book v0.17.0                 # 目次サイドバー
```

必要なもの: TeX Live（luatexja, unicode-math）、Noto CJK、Latin Modern、
make4ht、dvisvgm、mutool。

`main` への push で GitHub Actions がビルドし Pages に反映する。
ワークフローは `texlive/texlive` コンテナ上で走るため、TeX Live の導入時間がかからない。

tex4ht は DVI 経路を通るため和文 OpenType フォントを解決できず、
TikZ 内の日本語が脱落する。そのため図は `src/figures/` に切り出し、
LuaLaTeX で個別に組版してから SVG に変換している。

## データ

`src/analysis/` に実証の処理を置いた。入力は以下の公開データ。

- 財務省「法人企業統計調査」（e-Stat 統計表ID 0003060791）
- 中小企業庁「中小企業実態基本調査」
- 厚生労働省「人材サービス総合サイト」「職業紹介事業報告書の集計結果」
- 日本資金決済業協会「発行事業実態調査統計」

## 版

版番号は付録Eの「版の履歴」に対応する。

| | 上げる条件 |
|---|---|
| 第二桁 | 構成の変更、命題の追加・撤回、新たな実証 |
| 第三桁 | 誤記の修正、体裁の調整、参照の整合 |

現在は v0.17.0（付録Dの第17段階）。

## ライセンス

本文 CC BY 4.0 ／ コード MIT
