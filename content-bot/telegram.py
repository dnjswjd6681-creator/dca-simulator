"""텔레그램 봇으로 초안 전송. 복사하기 쉽게 꾸밈 없는 일반 텍스트로 보낸다."""
from __future__ import annotations

import os
from pathlib import Path

import requests

LIMIT = 4000  # 텔레그램 메시지 최대 4096자


def _api(method: str, **kw):
    token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=60, **kw)
    if not r.ok:
        raise RuntimeError(f"텔레그램 {method} 실패: {r.status_code} {r.text[:300]}")
    return r.json()


def _chat():
    return os.environ["TELEGRAM_CHAT_ID"].strip()


def _chunks(text: str):
    while text:
        if len(text) <= LIMIT:
            yield text
            return
        cut = text.rfind("\n", 0, LIMIT)
        cut = cut if cut > LIMIT // 2 else LIMIT
        yield text[:cut]
        text = text[cut:].lstrip("\n")


def send_text(text: str):
    for part in _chunks(text):
        _api("sendMessage", data={"chat_id": _chat(), "text": part,
                                  "disable_web_page_preview": "true"})


def send_photo(path: Path, caption: str = ""):
    with open(path, "rb") as f:
        _api("sendPhoto", data={"chat_id": _chat(), "caption": caption[:1000]}, files={"photo": f})


def send_document(path: Path, caption: str = ""):
    with open(path, "rb") as f:
        _api("sendDocument", data={"chat_id": _chat(), "caption": caption[:1000]}, files={"document": f})
