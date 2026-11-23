"""마크다운 초안을 네이버 블로그에 붙여넣기 좋은 형태로 바꾼다.
- 표 → PNG 이미지 (본문엔 '📊 [표 이미지 N 넣기]' 자리 표시)
- ##, **, - 같은 마크다운 기호 제거
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

import images as img_mod
from thumbnail import _font

UP, DOWN = (224, 49, 49), (25, 113, 194)  # 한국식: 상승 빨강, 하락 파랑


def _is_table_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and s.count("|") >= 3


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c) and any(cells)


def _strip_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    return text


def table_image(rows: list[list[str]], out: Path) -> Path:
    head_f, body_f = _font(True, 34), _font(False, 32)
    pad_x, row_h, margin = 28, 70, 40
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    widths = [max(tmp.textlength(r[c], font=head_f if i == 0 else body_f) for i, r in enumerate(rows)) + pad_x * 2
              for c in range(ncol)]
    W = int(sum(widths)) + margin * 2
    H = row_h * len(rows) + margin * 2
    img = Image.new("RGB", (max(W, 600), H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    y = margin
    for i, r in enumerate(rows):
        bg = (33, 41, 61) if i == 0 else ((246, 248, 251) if i % 2 == 0 else (255, 255, 255))
        d.rectangle([margin, y, margin + sum(widths), y + row_h], fill=bg)
        x = margin
        for c, cell in enumerate(r):
            cell = _strip_inline(cell)
            if i == 0:
                color, font = (255, 255, 255), head_f
            else:
                font = body_f
                color = UP if cell.startswith("+") else DOWN if re.match(r"^-\d", cell) else (33, 37, 41)
            numeric = c > 0 and (i == 0 or re.match(r"^[+\-$₩]?[\d,.]+%?[^\s]*$", cell))
            if numeric:
                d.text((x + widths[c] - pad_x, y + row_h / 2), cell, font=font, fill=color, anchor="rm")
            else:
                d.text((x + pad_x, y + row_h / 2), cell, font=font, fill=color, anchor="lm")
            x += widths[c]
        d.line([margin, y + row_h, margin + sum(widths), y + row_h], fill=(222, 226, 230), width=2)
        y += row_h
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def convert(body: str, out_dir: Path) -> tuple[str, list[Path]]:
    """(네이버용 본문, 표 이미지 경로 목록)"""
    lines = body.splitlines()
    out_lines, images, i = [], [], 0
    while i < len(lines):
        if _is_table_line(lines[i]):
            block = []
            while i < len(lines) and _is_table_line(lines[i]):
                block.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in block if not _is_separator(r)]
            n = len(images) + 1
            images.append(table_image(rows, out_dir / f"image_{n}.png"))
            out_lines.append(f"📷 [이미지 {n} 넣기]")
            continue
        line = lines[i]
        d = re.match(r"^\s*\[(차트|카드|이미지)\s*[:：]\s*(.+?)\]\s*$", line)
        if d:
            kind, spec = d.group(1), d.group(2)
            made = img_mod.from_directive(kind, spec, out_dir / f"image_{len(images) + 1}.png")
            if made:
                images.append(made)
                out_lines.append(f"📷 [이미지 {len(images)} 넣기]")
            else:
                desc = spec.split("|")[-1].strip() if kind == "차트" else spec
                out_lines.append(f"💡 추천 이미지 (직접 넣기): {desc}")
            i += 1
            continue
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
        if m:
            title = m.group(1).strip()
            line = title if title.startswith(("■", "📌", "✅")) else f"■ {title}"
        elif re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", line):
            line = re.sub(r"^\s*[-*]\s+\[[ xX]\]\s+", "✅ ", line)
        elif re.match(r"^\s*[-*]\s+", line):
            line = re.sub(r"^\s*[-*]\s+", "• ", line)
        elif re.match(r"^\s*(---+|\*\*\*+)\s*$", line):
            line = ""
        elif line.startswith(">"):
            line = line.lstrip("> ").strip()
        out_lines.append(_strip_inline(line))
        i += 1
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
    return text, images
