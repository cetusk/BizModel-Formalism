# BizModel-Formalism

**Business Models as Cash-Flow Structure** — formalization, a catalogue of types, and survey design

🌐 **English** ・ [日本語](README.md)

> **v0.28.9** (7 September 2026) — **This text is under construction.**
> The structure of the theory, the propositions, and the empirical conclusions may all change.
> Please cite the version.

A business model is formalized as a map Φ from a schedule of deliveries to a schedule of
settlements, from which the credit position κ, the self-financeable growth rate g\*, and a
three-way decomposition of surplus are derived.

📖 **[Read in HTML](https://cetusk.github.io/BizModel-Formalism/book-en/book-en.html)** ・
📄 **[PDF](https://cetusk.github.io/BizModel-Formalism/book-en.pdf)** (241 pages)

> The English edition is a complete translation of the Japanese one and is kept in step with
> it. The Japanese edition:
> [HTML](https://cetusk.github.io/BizModel-Formalism/book/book.html) ・
> [PDF](https://cetusk.github.io/BizModel-Formalism/book.pdf) (205 pages).

## Structure

| | |
|---|---|
| Part I | Theory — definitions, propositions, proofs |
| Part II | The space of maps and its constraints — 28 types, subspaces under constraints, unmanned operation |
| Part III | Method — a taxonomy of verification obstacles, selection bias, pre-registration |
| Part IV | Empirics — measuring the theoretical quantities; families 2 and 5, corporate statistics, platform fees |
| Part V | Conclusion — what was established and what remains open |
| Appendices | Supplementary proofs, notation, correspondences with existing theory, data sources, revision history |

## What this text does not claim

**It is not a predictive theory.** Most of the pre-registered implications were rejected.
The framework works as a descriptive instrument, but there is no established result about
what the quantities it describes predict.

**Most of the individual components have counterparts in existing theory.** The contribution
lies in showing that trade credit, the bonding argument, signalling, and work on prepaid
contracts appear as terms of one and the same sum.

Claims withdrawn during the work are recorded in Appendix E. The body keeps only the
corrected content.

## Build

```bash
cd src
lualatex book.tex && lualatex book.tex && lualatex book.tex        # Japanese PDF
lualatex book-en.tex && lualatex book-en.tex && lualatex book-en.tex  # English PDF
./build-figures.sh                                                 # figures to SVG
make4ht -l -f html5+dvisvgm_hashes -d ../docs/book book.tex "mathml,2"
python3 inject-sidebar.py ../docs/book v0.28.9 ja
make4ht -l -f html5+dvisvgm_hashes -d ../docs/book-en book-en.tex "mathml,2"
python3 inject-sidebar.py ../docs/book-en v0.28.9 en
```

Requirements: TeX Live (luatexja, unicode-math), Noto CJK, Latin Modern, make4ht, dvisvgm,
mutool.

A push to `main` triggers a GitHub Actions build that publishes to Pages.

Because tex4ht goes through a DVI route it cannot resolve CJK OpenType fonts, so Japanese
inside TikZ is dropped. Figures are therefore kept in `src/figures/` (and `src/figures-en/`
for the English edition), typeset individually with LuaLaTeX and converted to SVG.

## Development

`CLAUDE.md` records the conventions and the past mistakes. Permissions are in
`.claude/settings.json`.

```bash
bash scripts/setup-dev.sh      # check the environment and install make4ht
bash scripts/build.sh all      # build PDF and HTML, then run the checks
python3 scripts/check.py       # consistency checks (run after every change)
```

`scripts/check.py` mechanically checks reference types, past-tense forward references,
unreferenced propositions, uncited works, process narrative leaking into the body, blank
pages, and over-long tables. Every one of these was missed at some point.

## Data

The inputs and processing for the empirical work are in `data/`; see `data/README.md`.

```bash
cd data/scripts
python3 parse.py      # generate derived/*.json (not in git; needed on first run)
python3 gstar4.py     # compute g*
```

The inputs are the following public statistics.

- Ministry of Finance, Financial Statements Statistics of Corporations by Industry (e-Stat table 0003060791)
- SME Agency, Basic Survey on Small and Medium Enterprises
- Ministry of Health, Labour and Welfare, Employment Service Information Site; Reports of Employment Placement Businesses
- Japan Payment Service Association, Survey of Issuers of Prepaid Payment Instruments

## Versions

Version numbers correspond to the stages in Appendix E.

| | Raised when |
|---|---|
| Second digit | structural change, a proposition added or withdrawn, new empirical work |
| Third digit | typographical corrections, formatting, consistency of references |

Currently v0.28.9 (stage 28 of Appendix E).

## Licence

Text CC BY 4.0 / code MIT

## Handling of data

All the statistics used are public. The Employment Service Information Site of the Ministry
of Health, Labour and Welfare, however, publishes the filings of individual establishments
rather than aggregates. This text **uses them as input to statistical analysis and reports
only the results**. The collected corpus of per-firm data is not reproduced or
redistributed. The acquisition procedure is described in `data/README.md`.
