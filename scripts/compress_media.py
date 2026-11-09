#!/usr/bin/env python
"""Downsample embedded images and rebuild a .docx without moving the layout.

Pixel data changes; part names and EMU extents stay the same, so captions and
figure positions are unaffected.

Usage:
    python compress_media.py in.docx out.docx [--max-px 3000] [--quality 90]
"""
import io
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def recompress(data, max_px, quality):
    im = Image.open(io.BytesIO(data))
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > max_px:
        scale = max_px / max(w, h)
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, subsampling=0, optimize=True)
    return buf.getvalue()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src, dst = Path(argv[0]), Path(argv[1])
    max_px = int(argv[argv.index("--max-px") + 1]) if "--max-px" in argv else 3000
    quality = int(argv[argv.index("--quality") + 1]) if "--quality" in argv else 90

    zin = zipfile.ZipFile(src)
    media_before = media_after = 0
    count = 0
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/media/"):
                before = len(data)
                data = recompress(data, max_px, quality)
                media_before += before
                media_after += len(data)
                count += 1
            zout.writestr(item, data)
    zin.close()

    print(f"{src.name}: {src.stat().st_size / 1048576:.1f} MB -> "
          f"{dst.stat().st_size / 1048576:.1f} MB")
    print(f"  images recompressed: {count}, media {media_before / 1048576:.1f} MB -> "
          f"{media_after / 1048576:.1f} MB, max side {max_px}px, q{quality}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
