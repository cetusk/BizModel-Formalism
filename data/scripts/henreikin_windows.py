# 返戻金の書面から、判読に要る部分だけを切り出す。
#
# 正規表現で段階を取ろうとすると、余分な区間を作ったり率を取り違えたりする。
# 8件を検めたところ3件で誤りが出た。しかも誤りは強度を過大にする向きに偏る。
# したがって値の確定は人が読んで行い、本スクリプトは読む範囲を絞るだけにする。
#
# 切り出しの規則。返戻・返金・返還の最初の出現から前後を取る。
# 手数料率と返戻率が同じ書面に併記されるため、前を取りすぎると取り違える。
import io, os, re, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PDF  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin")
OCR  = os.path.join(HERE, "..", "derived", "henreikin_ocr")
OUT  = os.path.join(HERE, "..", "derived", "henreikin_windows.json")
Z    = str.maketrans("０１２３４５６７８９％，．　", "0123456789%,. ")
BEFORE, AFTER = 130, 900

def text(permit):
    o = os.path.join(OCR, permit + ".txt")
    if os.path.exists(o):
        return io.open(o, encoding="utf-8", errors="replace").read(), "ocr"
    p = os.path.join(PDF, permit + ".pdf")
    if not os.path.exists(p):
        return "", "なし"
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", p, "-"], capture_output=True, timeout=60)
    return r.stdout.decode("utf-8", "replace"), "text"

def window(s):
    s = re.sub(r"\s+", " ", s.translate(Z))
    s = re.sub(r"(?<=\d)\s+(?=\d)", "", s)
    # 表の見出しは「返 金 率」のように字間を空けて組まれることがある。
    # 和文どうしの空白を落とさないと「返金」で当たらない。
    s = re.sub(r"(?<=[\u3040-\u30ff\u4e00-\u9fff])[ ]+(?=[\u3040-\u30ff\u4e00-\u9fff])", "", s)
    # 返戻の語が複数あれば、率（%）を最も多く含む窓を選ぶ
    best, score = "", -1
    for m in re.finditer(r"返戻|返金|返還|保証期間", s):
        w = s[max(0, m.start() - BEFORE): m.start() + AFTER]
        k = len(re.findall(r"\d+\s*%", w)) * 10 + len(re.findall(r"\d+\s*[ヶケヵカかカ箇]?月|\d+\s*日", w))
        if k > score:
            best, score = w, k
    if score > 0 and re.search(r"\d+\s*%", best):
        return best.strip()
    # 返戻の語の近くに率が無い書面がある。契約書の別条や、
    # 語を伴わない表として組まれている場合である。
    # 全文を走査し、期間と率がともに濃い区間を採る。
    bw, bs = "", 0
    for m in re.finditer(r"\d+\s*%", s):
        w = s[max(0, m.start() - 300): m.start() + 320]
        k = len(re.findall(r"\d+\s*%", w)) * len(re.findall(
            r"\d+\s*[ヶケヵカかカ箇]?月|\d+\s*日|\d+\s*週", w))
        if k > bs:
            bw, bs = w, k
    if bs > 0:
        return bw.strip()
    return (best or s[:AFTER]).strip()

def main():
    H = json.load(io.open(os.path.join(HERE, "..", "derived", "jinzai_henreikin.json"), encoding="utf-8"))
    out = []
    for r in H:
        s, src = text(r["permit"])
        out.append(dict(permit=r["permit"], src=src, chars=len(s.strip()), window=window(s)))
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    c = collections.Counter(x["src"] for x in out)
    sys.stderr.write("  %d 件（%s）→ %s\n" % (len(out), dict(c), OUT))
    sys.stderr.write("  窓の平均 %d 文字 / 空の窓 %d 件\n"
                     % (sum(len(x["window"]) for x in out) / len(out),
                        sum(1 for x in out if len(x["window"]) < 20)))

if __name__ == "__main__":
    main()
