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
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def make(line1: str, line2: str, category: str, date_str: str, brand: str, out: Path) -> Path:
    bg, accent = THEMES.get(category, DEFAULT_THEME)
    img = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(img)

    # 은은한 대각선 그라데이션
    for y in range(SIZE):
        t = y / SIZE
        c = tuple(int(bg[i] * (1 - 0.35 * t) + accent[i] * 0.12 * t) for i in range(3))
        d.line([(0, y), (SIZE, y)], fill=c)

    pad = 90
    # 카테고리 칩
    chip_f = _font(True, 40)
    chip = f" {category} " if category else " 마켓 "
    cw = d.textlength(chip, font=chip_f)
    d.rounded_rectangle([pad, pad, pad + cw + 30, pad + 72], radius=36, fill=accent)
    d.text((pad + 15, pad + 12), chip, font=chip_f, fill=bg)
    d.text((SIZE - pad, pad + 14), date_str, font=_font(False, 38), fill=(200, 200, 210), anchor="ra")

    # 큰 글씨
    big = _font(True, 128)
    lines = _wrap(d, line1, big, SIZE - pad * 2)
    while len(lines) > 2 and big.size > 80:
        big = _font(True, big.size - 12)
        lines = _wrap(d, line1, big, SIZE - pad * 2)
    y = 380
    for ln in lines[:3]:
        d.text((pad, y), ln, font=big, fill=(255, 255, 255))
        y += int(big.size * 1.2)

    # 포인트 밑줄
    d.rectangle([pad, y + 20, pad + 140, y + 32], fill=accent)

    # 작은 글씨
    small = _font(False, 56)
    y += 80
    for ln in _wrap(d, line2, small, SIZE - pad * 2)[:2]:
        d.text((pad, y), ln, font=small, fill=(225, 225, 235))
        y += 74

    if brand:
        d.text((SIZE - pad, SIZE - pad), brand, font=_font(True, 36), fill=accent, anchor="rs")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out
