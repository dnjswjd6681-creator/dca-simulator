"""블로그 본문용 이미지: 주가 차트, 정리 카드.

본문 안의 지시 형식
  [차트: NVDA | 3mo | 엔비디아 최근 3개월 주가]        → 한 종목 주가 차트
  [차트: NVDA,AMD,AVGO | 6mo | 반도체 3사 수익률 비교]  → 여러 종목 수익률(%) 비교
  [카드: 이번 주 타임라인 | 화) WSJ 보도 / 목) 앤트로픽 상장 / 금) 엔비디아 -14%]
"""
from __future__ import annotations

import glob
import logging
from pathlib import Path

from PIL import Image, ImageDraw

from thumbnail import _font, _wrap

log = logging.getLogger(__name__)
NAVY, BLUE, RED, GRAY = "#21293D", "#1971C2", "#E03131", "#868E96"
PALETTE = ["#1971C2", "#E8590C", "#2F9E44", "#7048E8", "#C2255C"]
PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "ytd"}


def _setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, pyplot as plt
    for pat in ["/usr/share/fonts/**/NotoSansCJK*-Regular.ttc", "/usr/share/fonts/**/NanumGothic.ttf",
                "/usr/share/fonts/**/wqy-zenhei.ttc"]:
        hits = glob.glob(pat, recursive=True)
        if hits:
            font_manager.fontManager.addfont(hits[0])
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=hits[0]).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def chart(tickers: list[str], period: str, title: str, out: Path, closes=None) -> Path:
    """closes: 테스트용 {ticker: pandas.Series}. 없으면 yfinance로 받는다."""
    plt = _setup_matplotlib()
    period = period if period in PERIODS else "3mo"
    if closes is None:
        import yfinance as yf
        data = yf.download(tickers, period=period, interval="1d", progress=False,
                           auto_adjust=False, group_by="ticker")
        closes = {}
        for t in tickers:
            try:
                ser = data[t]["Close"]
            except KeyError:
                ser = data["Close"]
                ser = ser[t] if hasattr(ser, "columns") and t in ser.columns else ser.squeeze()
            closes[t] = ser.dropna()
    closes = {t: s for t, s in closes.items() if len(s) > 1}
    if not closes:
        raise ValueError(f"시세 없음: {tickers}")

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=120)
    fig.patch.set_facecolor("white")
    if len(closes) == 1:
        t, s = next(iter(closes.items()))
        chg = (s.iloc[-1] / s.iloc[0] - 1) * 100
        color = RED if chg >= 0 else BLUE
        ax.plot(s.index, s.values, color=color, linewidth=2.4)
        ax.fill_between(s.index, s.values, s.min() * 0.98, color=color, alpha=0.08)
        hi, lo = s.idxmax(), s.idxmin()
        ax.scatter([hi, lo], [s[hi], s[lo]], color=[RED, BLUE], zorder=3, s=30)
        ax.annotate(f"최고 {s[hi]:,.2f}", (hi, s[hi]), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=11, color=RED)
        ax.annotate(f"최저 {s[lo]:,.2f}", (lo, s[lo]), textcoords="offset points", xytext=(0, -18),
                    ha="center", fontsize=11, color=BLUE)
        ax.annotate(f"{s.iloc[-1]:,.2f}\n({chg:+.1f}%)", (s.index[-1], s.iloc[-1]), textcoords="offset points",
                    xytext=(8, 0), va="center", fontsize=12, color=color, fontweight="bold")
        ax.set_ylim(s.min() * 0.97, s.max() * 1.04)
    else:
        for k, (t, s) in enumerate(closes.items()):
            pct = (s / s.iloc[0] - 1) * 100
            c = PALETTE[k % len(PALETTE)]
            ax.plot(pct.index, pct.values, color=c, linewidth=2.2, label=t)
            ax.annotate(f"{t} {pct.iloc[-1]:+.1f}%", (pct.index[-1], pct.iloc[-1]), textcoords="offset points",
                        xytext=(8, 0), va="center", fontsize=11, color=c, fontweight="bold")
        ax.axhline(0, color=GRAY, linewidth=1, linestyle="--")
        ax.set_ylabel("수익률 (%)", color=GRAY)
    ax.set_title(title, fontsize=17, fontweight="bold", color=NAVY, loc="left", pad=16)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#DEE2E6")
    ax.spines["bottom"].set_color("#DEE2E6")
    ax.tick_params(colors=GRAY, labelsize=10)
    ax.grid(axis="y", color="#F1F3F5")
    fig.autofmt_xdate()
    fig.text(0.99, 0.01, "자료: Yahoo Finance", ha="right", fontsize=9, color=GRAY)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return out


def card(title: str, items: list[str], out: Path) -> Path:
    W, pad = 1200, 70
    title_f, item_f, num_f = _font(True, 54), _font(False, 40), _font(True, 34)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    title_lines = _wrap(tmp, title, title_f, W - pad * 2)
    wrapped = [_wrap(tmp, it, item_f, W - pad * 2 - 90) for it in items]
    H = pad * 2 + len(title_lines) * 70 + 40 + sum(len(w) * 54 + 36 for w in wrapped)
    img = Image.new("RGB", (W, max(H, 500)), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, img.height], fill=BLUE)
    y = pad
    for ln in title_lines:
        d.text((pad, y), ln, font=title_f, fill=NAVY)
        y += 70
    d.rectangle([pad, y + 6, pad + 120, y + 14], fill=BLUE)
    y += 50
    for k, lines in enumerate(wrapped, 1):
        cy = y + 27
        d.ellipse([pad, cy - 26, pad + 52, cy + 26], fill=BLUE)
        d.text((pad + 26, cy), str(k), font=num_f, fill="white", anchor="mm")
        if k < len(wrapped):
            d.line([pad + 26, cy + 30, pad + 26, cy + len(lines) * 54 + 30], fill="#D0EBFF", width=4)
        for j, ln in enumerate(lines):
            d.text((pad + 90, y + j * 54), ln, font=item_f, fill=(33, 37, 41))
        y += len(lines) * 54 + 36
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


DARK_BG, DARK_BG2, DIM, TXT = (22, 22, 24), (14, 14, 16), (150, 150, 158), (236, 236, 240)


def quote_card(source: str, title: str, lines: list[str], out: Path) -> Path:
    """원문 인용 카드 (어두운 배경). 실제 앱 화면을 흉내 내지 않고 '인용'임을 표시한다."""
    W, pad = 1200, 64
    src_f, title_f, body_f = _font(True, 34), _font(True, 58), _font(False, 42)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    t_lines = _wrap(tmp, title, title_f, W - pad * 2) if title else []
    b_lines = [ln for raw in lines for ln in _wrap(tmp, raw, body_f, W - pad * 2)]
    H = pad + 50 + 40 + len(t_lines) * 76 + 24 + len(b_lines) * 62 + pad + 30
    img = Image.new("RGB", (W, H), DARK_BG)
    d = ImageDraw.Draw(img)
    d.text((pad, pad), "“ 원문 요약", font=_font(True, 30), fill=(255, 92, 168))
    d.text((pad + 210, pad), source, font=src_f, fill=DIM)
    y = pad + 90
    for ln in t_lines:
        d.text((pad, y), ln, font=title_f, fill=(255, 255, 255))
        y += 76
    y += 24
    for ln in b_lines:
        d.text((pad, y), ln, font=body_f, fill=TXT)
        y += 62
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def comment_card(question: str, answer: str, out: Path) -> Path:
    """댓글 질문 + 작성자 답변 카드."""
    W, pad = 1200, 64
    lab_f, body_f = _font(True, 30), _font(False, 42)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    q_lines = _wrap(tmp, question, body_f, W - pad * 2)
    a_lines = _wrap(tmp, answer, body_f, W - pad * 2 - 60) if answer else []
    qh = pad + 50 + len(q_lines) * 60 + pad - 20
    ah = (pad + 50 + len(a_lines) * 60 + pad - 20) if a_lines else 0
    img = Image.new("RGB", (W, qh + ah), DARK_BG)
    d = ImageDraw.Draw(img)
    d.text((pad, pad - 10), "댓글", font=lab_f, fill=DIM)
    y = pad + 40
    for ln in q_lines:
        d.text((pad, y), ln, font=body_f, fill=TXT)
        y += 60
    if a_lines:
        d.rectangle([0, qh, W, qh + ah], fill=DARK_BG2)
        d.text((pad + 60, qh + pad - 10), "└ 작성자 답글", font=lab_f, fill=(255, 92, 168))
        y = qh + pad + 40
        for ln in a_lines:
            d.text((pad + 60, y), ln, font=body_f, fill=TXT)
            y += 60
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def from_directive(kind: str, spec: str, out: Path) -> Path | None:
    parts = [p.strip() for p in spec.split("|")]
    try:
        if kind == "차트":
            tickers = [t.strip().upper() for t in parts[0].split(",") if t.strip()]
            period = parts[1].lower() if len(parts) > 1 else "3mo"
            title = parts[2] if len(parts) > 2 else " vs ".join(tickers)
            return chart(tickers, period, title, out)
        if kind == "인용":
            src = parts[0] if len(parts) > 2 else "온라인 커뮤니티"
            title = parts[1] if len(parts) > 2 else parts[0]
            body = parts[-1] if len(parts) > 1 else ""
            return quote_card(src, title, [x.strip() for x in body.split("/") if x.strip()], out)
        if kind == "댓글":
            qa = [x.strip() for x in spec.split("/")]
            return comment_card(qa[0], " ".join(qa[1:]).strip(), out)
        if kind == "카드":
            title = parts[0]
            items = [x.strip() for x in (parts[1] if len(parts) > 1 else "").split("/") if x.strip()]
            return card(title, items or [title], out)
    except Exception as e:  # noqa: BLE001
        log.warning("이미지 생성 실패 [%s: %s]: %s", kind, spec, e)
        if kind == "차트":  # 차트 실패 시 제목만 있는 카드로 대체하지 않고 건너뜀
            return None
    return None
