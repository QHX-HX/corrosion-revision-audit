#!/usr/bin/env python
"""Pre-flight check for a submission folder.

Verifies that every .docx is a valid archive, that media parts have extensions,
that images are not absurdly large, that no non-existent font is used for visible
text, and that no Chinese characters survive in visible text.

Usage:
    python verify_package.py <folder>
"""
import io
import re
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
CJK = re.compile(r"[\u4e00-\u9fff]")
BAD_FONTS = {"Times", "Tahoma", "Courier", "Calibri Light", "等线"}
LIMIT_MB = 20.0
MAX_PX = 6000


def visible_text(xml):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def check(path):
    problems = []
    z = zipfile.ZipFile(path)
    if z.testzip() is not None:
        problems.append("corrupt zip")

    media = [n for n in z.namelist() if n.startswith("word/media/")]
    max_dim = 0
    for n in media:
        if not Path(n).suffix:
            problems.append(f"media without extension: {n}")
            continue
        try:
            im = Image.open(io.BytesIO(z.read(n)))
            max_dim = max(max_dim, *im.size)
        except Exception:
            problems.append(f"undecodable image: {n}")

    try:
        doc_xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except KeyError:
        doc_xml = ""

    used_fonts = set(re.findall(r'w:(?:ascii|hAnsi|cs)="([^"]+)"', doc_xml))
    for f in sorted(used_fonts & BAD_FONTS):
        problems.append(f"font not installed on most systems: {f}")

    n_cjk = len(CJK.findall(visible_text(doc_xml)))
    if n_cjk:
        problems.append(f"{n_cjk} CJK characters in visible text")

    mb = path.stat().st_size / 1048576
    if mb > LIMIT_MB:
        problems.append(f"{mb:.1f} MB exceeds {LIMIT_MB:.0f} MB")
    if max_dim > MAX_PX:
        problems.append(f"largest image side {max_dim}px (slow to open)")
    return mb, len(media), max_dim, problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    folder = Path(argv[0])
    files = sorted(folder.glob("*.docx"))
    if not files:
        print("no .docx found")
        return 1
    total = 0
    print(f"{'file':<52}{'MB':>7}{'media':>7}{'maxpx':>7}  status")
    for f in files:
        mb, n_media, max_dim, problems = check(f)
        total += len(problems)
        status = "OK" if not problems else "; ".join(problems)
        print(f"{f.name:<52}{mb:>7.2f}{n_media:>7}{max_dim:>7}  {status}")
    print()
    print(f"{total} issue(s) found" if total else
          "all files passed structural checks (open each once visually as well)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
