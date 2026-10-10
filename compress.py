"""Compress every image in images/original to <=25 KB JPG (1200x675) in images/compressed.
Usage: pip install pillow && python compress.py
"""
import io, sys
from pathlib import Path
from PIL import Image, ImageFilter

SRC, DST = Path("images/original"), Path("images/compressed")
LIMIT = 25 * 1024
SIZES = [(1200, 675), (1080, 608), (960, 540), (854, 480)]

def encode(img, q):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q, optimize=True, progressive=True, subsampling=2)
    return buf.getvalue()

def compress(path):
    img = Image.open(path).convert("RGB")
    for w, h in SIZES:
        # crop to 16:9 and resize with a light sharpen so the result isn't blurry
        r = img.width / img.height
        if r > 16 / 9:
            nw = int(img.height * 16 / 9); box = ((img.width - nw) // 2, 0, (img.width + nw) // 2, img.height)
        else:
            nh = int(img.width * 9 / 16); box = (0, (img.height - nh) // 2, img.width, (img.height + nh) // 2)
        im = img.crop(box).resize((w, h), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))
        lo, hi, best = 20, 92, None
        while lo <= hi:  # highest quality that fits in 25 KB
            q = (lo + hi) // 2
            data = encode(im, q)
            if len(data) <= LIMIT: best, lo = data, q + 1
            else: hi = q - 1
        if best: return best, (w, h)
    for q in range(19, 4, -1):
        data = encode(im, q)
        if len(data) <= LIMIT: return data, (w, h)
    w, h = 640, 360
    im = im.resize((w, h), Image.LANCZOS)
    return encode(im, 40), (w, h)

DST.mkdir(parents=True, exist_ok=True)
files = [p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
if not files: sys.exit(f"Put your images in {SRC}/ first")
for p in sorted(files):
    data, size = compress(p)
    out = DST / (p.stem + ".jpg")
    out.write_bytes(data)
    print(f"{out.name}: {len(data)/1024:.1f} KB  {size[0]}x{size[1]}")
