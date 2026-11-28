"""블로그 썸네일 (1080x1080 PNG) 생성."""
from __future__ import annotations

import glob
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
THEMES = {  # 배경, 포인트색
    "미국주식": ((14, 27, 51), (77, 163, 255)),
    "국내주식": ((40, 16, 24), (255, 99, 112)),
    "크립토": ((28, 22, 8), (255, 176, 32)),
}
DEFAULT_THEME = ((20, 20, 24), (120, 220, 160))


def _font(bold: bool, size: int):
    pats = (["/usr/share/fonts/**/NotoSansCJK*-Bold.ttc", "/usr/share/fonts/**/NanumGothicBold.ttf",
             "/usr/share/fonts/**/wqy-zenhei.ttc"]
            if bold else ["/usr/share/fonts/**/NotoSansCJK*-Regular.ttc", "/usr/share/fonts/**/NanumGothic.ttf",
             "/usr/share/fonts/**/wqy-zenhei.ttc"])
    for p in pats:
        hits = glob.glob(p, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], size=size, index=1 if "NotoSansCJK" in hits[0] else 0)
            except Exception:  # noqa: BLE001
                return ImageFont.truetype(hits[0], size=size)
    return ImageFont.load_default(size=size)


def _wrap(draw, text, font, max_w):
    """띄어쓰기 단위로 줄바꿈 (한 단어가 너무 길면 글자 단위로 자름)."""
    lines, cur = [], ""
    for word in text.split(" "):
        cand = f"{cur} {word}" if cur else word
        if draw.textlength(cand, font=font) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:
            if draw.textlength(cur + ch, font=font) > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
    if cur:
        lines.append(cur)
    return lines


PHOTO_DIR = Path(__file__).parent / "photos"
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def _pick_photo(seed: str):
    import random
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except Exception:  # noqa: BLE001
        pass
    photos = sorted(p for p in PHOTO_DIR.glob("*") if p.suffix.lower() in PHOTO_EXT) if PHOTO_DIR.exists() else []
    if not photos:
        return None
    rnd = random.Random(seed)
    for p in rnd.sample(photos, len(photos)):
        try:
            from PIL import ImageOps
            return ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        except Exception:  # noqa: BLE001
            continue
    return None


def make(line1: str, line2: str, category: str, date_str: str, brand: str, out: Path) -> Path:
    """사진 배경 + 흰 글씨(1줄) + 노란 글씨(2줄) + 분홍 계정명. photos/ 폴더에 사진이 없으면 어두운 배경."""
    photo = _pick_photo(date_str + line1)
    if photo:
        w, h = photo.size
        side = min(w, h)
        photo = photo.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
        img = photo.resize((SIZE, SIZE))
    else:
        img = Image.new("RGB", (SIZE, SIZE), (30, 30, 34))
    # 아래쪽 어둡게 (글씨 잘 보이게)
    shade = Image.new("L", (1, SIZE))
    for y in range(SIZE):
        t = max(0.0, (y - SIZE * 0.35) / (SIZE * 0.65))
        shade.putpixel((0, y), int(255 * min(0.82, t * 1.1)))
    img = Image.composite(Image.new("RGB", (SIZE, SIZE), (0, 0, 0)), img, shade.resize((SIZE, SIZE)))
    d = ImageDraw.Draw(img)

    pad = 70
    f1, f2 = _font(True, 104), _font(True, 104)
    l1 = _wrap(d, line1, f1, SIZE - pad * 2)
    l2 = _wrap(d, line2, f2, SIZE - pad * 2)
    while len(l1) + len(l2) > 3 and f1.size > 70:
        f1 = f2 = _font(True, f1.size - 8)
        l1, l2 = _wrap(d, line1, f1, SIZE - pad * 2), _wrap(d, line2, f2, SIZE - pad * 2)
    brand_f = _font(True, 56)
    lh = int(f1.size * 1.22)
    y = SIZE - pad - (90 if brand else 10) - lh * (len(l1) + len(l2))
    for ln in l1:
        d.text((pad, y), ln, font=f1, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        y += lh
    for ln in l2:
        d.text((pad, y), ln, font=f2, fill=(255, 226, 54), stroke_width=3, stroke_fill=(0, 0, 0))
        y += lh
    if brand:
        d.text((pad, y + 20), brand, font=brand_f, fill=(255, 92, 168), stroke_width=2, stroke_fill=(0, 0, 0))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out
