# 文字を持たない返戻金PDF（スキャン画像）を OCR してテキストにする。
#
# 【なぜ要るか】返戻金の書面は事業者が自由な書式で作る。約 15% は紙を
#   スキャンしたもので、pdftotext では一文字も取れない。
#   これを落とすと「テキストで出す事業者」だけが標本に残る（第15章）。
#
# 【精度】tesseract の日本語は本文をよく拾うが、% 記号を誤る。
#   「90%%」「759%6%」「年収の2096」のような出力になる。
#   数値は文脈で確定させる必要があり、機械的な後処理では復元できない。
#   本スクリプトはテキスト化までを担い、値の判読は人が行う。
import io, os, re, sys, json, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "raw", "jinzai", "henreikin")
OUT  = os.path.join(HERE, "..", "derived", "henreikin_ocr")
MAXP = 4      # 返戻金の記載は先頭数頁に収まる

def ocr(pdf, out):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "300", "-png", "-f", "1", "-l", str(MAXP),
                        pdf, os.path.join(d, "p")], capture_output=True, timeout=300)
        txt = []
        for f in sorted(os.listdir(d)):
            if not f.endswith(".png"):
                continue
            r = subprocess.run(["tesseract", os.path.join(d, f), "stdout", "-l", "jpn", "--psm", "6"],
                               capture_output=True, timeout=300)
            txt.append(r.stdout.decode("utf-8", "replace"))
    s = "\n".join(txt)
    io.open(out, "w", encoding="utf-8").write(s)
    return len(s.strip())

def main():
    os.makedirs(OUT, exist_ok=True)
    H = json.load(io.open(os.path.join(HERE, "..", "derived", "jinzai_henreikin.json"), encoding="utf-8"))
    todo = [r["permit"] for r in H if r["scanned"]]
    sys.stderr.write("  対象 %d 件\n" % len(todo))
    ok = ng = 0
    for i, p in enumerate(todo, 1):
        o = os.path.join(OUT, p + ".txt")
        if os.path.exists(o) and os.path.getsize(o) > 40:
            continue
        try:
            n = ocr(os.path.join(SRC, p + ".pdf"), o)
            ok += 1 if n > 40 else 0
            ng += 0 if n > 40 else 1
        except Exception as e:
            ng += 1
            sys.stderr.write("  ×  %s  %s\n" % (p, str(e)[:50]))
        if i % 20 == 0:
            sys.stderr.write("  … %d/%d  読めた %d 空 %d\n" % (i, len(todo), ok, ng))
    sys.stderr.write("  完了。読めた %d / 空 %d\n" % (ok, ng))

if __name__ == "__main__":
    main()
