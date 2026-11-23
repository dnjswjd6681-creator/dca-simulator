"""GitHub에 넣은 비밀번호 3개가 올바른 모양인지 점검한다. 값 자체는 절대 출력하지 않는다."""
from __future__ import annotations

import os
import re

RULES = {
    "ANTHROPIC_API_KEY": (r"^sk-ant-[A-Za-z0-9_\-]{20,}$", "sk-ant- 로 시작하는 Claude API 키"),
    "TELEGRAM_BOT_TOKEN": (r"^\d{6,}:[A-Za-z0-9_\-]{30,}$", "숫자:영문 모양의 텔레그램 봇 토큰 (앞에 bot 글자 없이)"),
    "TELEGRAM_CHAT_ID": (r"^-?\d{5,}$", "숫자로만 된 Chat ID"),
}


TOKEN_RE = re.compile(r"\d{6,}:[A-Za-z0-9_\-]{30,}")


def telegram_token() -> str:
    """토큰 칸에 주소 전체(https://api.telegram.org/bot.../getUpdates)를 넣었어도 토큰만 뽑아 쓴다."""
    raw = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    m = TOKEN_RE.search(raw)
    return m.group(0) if m else raw


def check() -> list[str]:
    problems = []
    for name, (pattern, desc) in RULES.items():
        raw = os.environ.get(name)
        if not raw:
            problems.append(f"❌ {name}: 비어 있어요. GitHub Secrets에 등록됐는지 확인하세요.")
            continue
        val = raw.strip()
        notes = []
        if val != raw:
            notes.append("앞뒤에 띄어쓰기/줄바꿈이 있었어요 (자동으로 지우고 진행)")
        if name == "TELEGRAM_BOT_TOKEN" and telegram_token() != val:
            notes.append("주소 전체가 들어 있어서 토큰 부분만 자동으로 뽑아 썼어요")
            val = telegram_token()
        if re.search(r"\s", val):
            notes.append("중간에 띄어쓰기나 줄바꿈이 있어요")
        if any(ord(c) > 127 for c in val):
            notes.append("한글이나 특수문자가 섞여 있어요 (예: '토큰:' 같은 설명 글자)")
        if name == "TELEGRAM_BOT_TOKEN" and val.lower().startswith("bot"):
            notes.append("맨 앞에 'bot' 글자가 붙어 있어요. 숫자부터 넣어야 해요")
        ok = re.match(pattern, val) is not None
        head = f"{len(val)}글자, 시작 '{val[:4]}…'" if name != "TELEGRAM_CHAT_ID" else f"{len(val)}자리"
        if ok:
            print(f"✅ {name}: 모양 정상 ({head})" + (f" — 참고: {', '.join(notes)}" if notes else ""))
        else:
            problems.append(f"❌ {name}: {desc}여야 하는데 모양이 달라요 ({head}). "
                            + (", ".join(notes) if notes else "복사할 때 빠지거나 더 들어간 글자가 있는지 확인하세요."))
    for p in problems:
        print(p)
    return problems


if __name__ == "__main__":
    raise SystemExit(1 if check() else 0)
