# BizModel-Formalism

キャッシュフロー構造としてビジネスモデルを定式化する文書のリポジトリ。
LaTeX ソースから PDF と HTML を生成し、GitHub Pages で公開している。

**日本語で応答すること。** コミットメッセージ、コメント、文書はすべて日本語。

---

## この文書の性格

**建設中の理論である。** 予測理論ではなく記述の枠組みであり、
事前登録した予測の多くが棄却されている。この立場を弱めないこと。

構成要素の多くは既存理論に対応がある。取引信用、bonding argument、
シグナリング、前払い契約の研究などが、式(3.7) の同一の和の項として現れる。
**寄与は接続にあり、要素の新規性にはない。**

---

## 作業の規律

これまでの検討で確立した規則。破ると同じ失敗を繰り返す。

### 1. 命題を書く前に文献を確認する

「既存理論がない」「誰も測定していない」と判断する前に必ず調べる。
過去に4回、独自性を過大評価して撤回している。

- 前受金 → reverse trade credit が既に存在した
- 労働の後払い → bonding argument が扱っていた
- 公開実績の蓄積 → Spence のシグナリング
- 族2-4 の認知余剰 → NBER 2026 が測定済み

### 2. 循環する証明を書かない

定義から自明なことを命題として証明しない。過去に2件撤回した。

- 「$C$ は $\Phi$ に依存しない」→ $C(\delta)$ と定義したのだから当然
- 「乖離の発生条件」→ 定義4.5 の言い換えにすぎない

証明の中身が「定義にそう書いたから」であれば、命題ではなく定義か注にする。

### 3. 事例から理論を書き換えない

理論部は全ての $\Phi$ を覆う抽象、実証部は特定の業種と企業に限定された具体。
**具体は網羅性を持たない。** $n=1$ の観測から式を書き換えれば、
一つの事例が27類型すべてに波及する。

理論の修正が正当化されるのは、演繹的な誤りが見つかった場合、
複数の独立な領域で同じ限界が現れた場合、第II部の演繹に影響する場合のみ。

### 4. 本文に経緯を書かない

読者は過去の版を知らない。「草稿では〜と書いたが誤りだった」は書かない。
**本文には現在の主張のみ**を残し、経緯は `src/app_revisions.tex`（付録D）に記録する。

予測の登録と棄却は別。これは事前登録という方法の実行記録であり、
第III部の規律そのものなので本文に残す。

### 5. 数値を更新したら全箇所を洗う

$g^\star$ の定義を $(m+d-I/r)/\CCC$ に変えた際、旧定義の値が11箇所残っていた。
一箇所直したら、その量が現れる全箇所を機械的に検索すること。

### 6. 検証せずに修正案を出さない

CI の修正を3回、検証せずに出して失敗させた。
**ローカルで実際に通してから**提案すること。特に、
「既に成功した状態」を使った検証は無効。まっさらな状態から通す。

---

## 記法と用語

| 記号 | 意味 | 定義箇所 |
|---|---|---|
| $\Phi:\Delta\to\Pi$ | ビジネスモデル。履行から決済への写像 | 4.1 |
| $\kappa_i = D_i - P_i$ | 信用ポジション | 3.1 |
| $\tau_i$ | 履行から決済までの平均的な遅れ | 3.1.2 |
| $\CCC = W/r = \sum\tau_i + \tau_{\rm inv}$ | キャッシュコンバージョンサイクル | 7.1 |
| $g^\star = (m+d-I/r)/\CCC$ | 自己金融可能成長率 | 系7.3 |
| $\phi = \phi_{\rm prod}+\phi_{\rm barg}+\phi_{\rm cog}$ | 余剰の三分解 | 8.1 |

**$m/\CCC$ と $g^\star$ を混同しない。** 長期系列は $d$ と $I$ を取得していないため
$m/\CCC$ で計算しており、$g^\star$ ではない。

用語は「命題」「定義」「注」「系」「例」。英語の theorem 等は使わない。

---

## ビルド

### PDF

```bash
cd src
lualatex -interaction=nonstopmode book.tex   # 3 回実行する
```

`ltjsbook` + `luatexja-fontspec` + `unicode-math`。フォントは Latin Modern と Noto CJK。

### HTML

```bash
cd src
bash build-figures.sh                        # TikZ 図を SVG 化
make4ht -l -f html5+dvisvgm_hashes -d ../docs/book book.tex "mathml,2"
python3 inject-sidebar.py ../docs/book v0.8.0
```

`make4ht` の実行には環境変数が要る。

```bash
MK=$HOME/texmf/scripts/lua/make4ht
export LUAINPUTS="$MK//:" TEXINPUTS="$MK//:" TEXMFHOME="$HOME/texmf"
```

### 図を別扱いする理由

**tex4ht は DVI 経路を通るため和文 OpenType フォントを解決できない。**
TikZ 内の日本語がすべて脱落する。`luatexja-fontspec` を使うと `.tfm` が
見つからずエラーになり、使わないとグリフが空になる。

そのため図は `src/figures/*.tex` に切り出し、`build-figures.sh` が
`preview` パッケージで個別に組版して PDF 化し、`dvisvgm --pdf` で SVG に変換する。
`book.tex` の `\insertfig` マクロが PDF と HTML で切り替える。

---

## 検査

内容を変更したら必ず実行する。

```bash
cd src
lualatex -interaction=nonstopmode book.tex   # 3 回

# 以下がすべて 0 であること
grep -c "^!" book.log
grep -c "Reference.*undefined" book.log
grep -c "Citation.*undefined" book.log
grep -c "multiply defined" book.log
grep -c "Overfull \\\\hbox" book.log
```

加えて、以下を機械的に確認すること（過去に何度も見落としている）。

- **参照の型**: 第\ref{part:x}部 と書いた先が実際に部か。`.aux` の `\newlabel` で判定
- **過去形の前方参照**: 第 n 章から第 m 章（m>n）を「述べた」と参照していないか
- **未参照の命題**: `\label` を付けたのに誰も `\ref` していないもの
- **未引用の文献**: `\bibitem` があるのに `\cite` されていないもの
- **表の見切れ**: 20行を超える表はページ下端で切れる。分割する
- **白紙ページ**: `pdftotext` で各ページの文字数を数える

---

## 版

`v0.n.0` が付録Dの第 n 段階に対応する。

| 桁 | 上げる条件 |
|---|---|
| 第二桁 | 構成の変更、命題の追加・撤回、新たな実証 |
| 第三桁 | 誤記の修正、体裁の調整、参照の整合 |

版を上げるときは**5箇所**を更新する。

```
src/book.tex               \date{v0.x.y\quad ...}
.github/assets/index.html  バナー2箇所とフッター
.github/workflows/build.yml  env: VERSION
README.md                  冒頭の引用と「現在は」の行
src/app_revisions.tex      版の履歴（第二桁のときのみ行を追加）
```

タグは最新の1つのみ保持する。

```bash
git tag -d v0.8.0 && git push origin --delete v0.8.0
git tag v0.8.1 && git push origin v0.8.1
```

---

## 未解決の問題

第20章に11件を四分類で整理してある。要点のみ。

**追加のデータ取得なしに前進できる項目は現時点で残っていない。**

実行可能性が中位なのは3件。

- (3) R2 の目的関数が $H$ と $\beta$ で足りるか → 年齢別の契約形態選択分布が要る
- (5) $\Delta\ln W$ の変動要因 → 運転資本の変動をさらに分解する
- (10) 個人事業主の $\kappa$ → 調査票はあるが集計されない。集計要望か匿名データ利用

障害の分類は本稿の調査で6つに拡張した。(v) 集計の選択、(vi) 調整の不作動。
後者は**理論が想定する調整が現実に作動していない**という形で、
データを増やしても理論を精密化しても解決しない。

---

## データ

`data/` に実証の入力と処理を置いてある。詳細は `data/README.md`。

```
data/raw/       取得したままのデータ（法人企業統計、中小企業実態基本調査、人材サービス総合サイト）
data/scripts/   分析の処理 31 本
data/derived/   パース済みの JSON。git 管理外。再生成すること
```

**`data/derived/` は git に入れていない。** 初回は生成する。

```bash
cd data/scripts
python3 parse.py        # raw/hojin から derived/*.json を作る
python3 parse_m.py
```

中小企業実態基本調査の時系列を使うときは、先に zip を展開する。

```bash
cd data/raw/chusho/extracted && unzip ../timeseries_r02-r07.zip
```

いずれも公開統計。

| 統計 | 用途 |
|---|---|
| 財務省「法人企業統計調査」（e-Stat 0003060791） | $\CCC$、$m$、$d$、$I$、役員報酬 |
| 中小企業庁「中小企業実態基本調査」 | 個人企業との比較 |
| 厚生労働省「人材サービス総合サイト」 | 手数料実績率と離職率（予測X） |
| 日本資金決済業協会「発行事業実態調査統計」 | 族2 の $\kappa$ |

**e-Stat は集計値のみで個票を提供しない。** 人材サービス総合サイトは
個社データを公開しているが、詳細検索で取得できる職種は医療・介護・保育に限られる。

---

## 既知の課題

- CI は `texlive/texlive` コンテナ上で走る。ローカルの TeX Live と
  バージョンが異なる可能性がある

## 解決済みの課題（記録）

- **HTML 版の本文幅が極端に狭く表示される問題（修正済み）。**
  原因は tex4ht が生成する `book.css` の `body{max-width:80ch}` だった。
  サイドバー構成を追加した `.github/assets/style.css` はこれを上書きしておらず、
  `#content` 側で `max-width:none` を指定しても親である `body` の 80ch 制限が
  効いたままだったため、サイドバー分の余白を引いた残りの狭い領域に本文が押し込まれていた。
  `style.css` の `body` ルールに `max-width:none` を追加して解消した。
  tex4ht 由来の CSS を上書きする際は、`custom.css` 側で該当プロパティを
  明示的に指定しないと打ち消せないことに注意（同名セレクタでもプロパティ単位で継承される）。
