"""실행: python main.py morning | evening  [--dry-run] [--fixture data.json] [--no-telegram]

morning : 블로그 1개 + X 1개 (미장 마감 후)
evening : X 1개 (국장 마감 후)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path

import collect
import config
import thumbnail

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts"
HISTORY = DRAFTS / "history.json"
KST = dt.timezone(dt.timedelta(hours=9))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("content-bot")


def load_history() -> list[dict]:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def save_history(hist: list[dict]):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(hist[-60:], ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["morning", "evening"])
    ap.add_argument("--dry-run", action="store_true", help="Claude 호출 없이 수집 결과와 프롬프트만 저장")
    ap.add_argument("--fixture", help="수집 대신 이 JSON 파일의 데이터를 사용 (테스트용)")
    ap.add_argument("--no-telegram", action="store_true")
    args = ap.parse_args()

    now = dt.datetime.now(KST)
    day_dir = DRAFTS / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(Path(args.fixture).read_text(encoding="utf-8")) if args.fixture else collect.collect_all()
    (day_dir / f"data_{args.mode}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    counts["news"] = sum(len(v) for v in data.get("news", {}).values())
    log.info("수집 완료: %s", counts)

    history = load_history()

    import writer  # anthropic은 실제 작성할 때만 필요
    if args.dry_run:
        (day_dir / f"prompt_{args.mode}.txt").write_text(
            writer.build_user_message(args.mode, data, history), encoding="utf-8")
        log.info("dry-run: 프롬프트 저장 → %s", day_dir)
        return

    draft = writer.write(args.mode, data, history)
    (day_dir / f"raw_{args.mode}.txt").write_text(draft.pop("_raw"), encoding="utf-8")

    entry = {"date": now.strftime("%Y-%m-%d"), "mode": args.mode, "category": draft.get("category", "")}
    files = {}
    if args.mode == "morning" and "blog_body" in draft:
        blog_md = (f"# {draft.get('blog_title', '')}\n\n{draft['blog_body']}\n\n"
                   f"{draft.get('hashtags', '')}\n")
        files["blog"] = day_dir / "blog.md"
        files["blog"].write_text(blog_md, encoding="utf-8")
        files["thumb"] = thumbnail.make(draft.get("thumbnail_line1", draft.get("blog_title", "")),
                                        draft.get("thumbnail_line2", ""), draft.get("category", ""),
                                        now.strftime("%Y.%m.%d"), config.BRAND_NAME, day_dir / "thumbnail.png")
        entry["title"] = draft.get("blog_title", "")
    x_file = day_dir / f"x_{args.mode}.txt"
    x_file.write_text(draft["x_post"], encoding="utf-8")
    entry["x_post"] = draft["x_post"][:120]
    if draft.get("sources"):
        (day_dir / f"sources_{args.mode}.txt").write_text(draft["sources"], encoding="utf-8")

    history.append(entry)
    save_history(history)

    if args.no_telegram:
        log.info("텔레그램 전송 생략. 결과: %s", day_dir)
        return

    import telegram
    md = now.strftime("%m/%d")
    if args.mode == "morning":
        telegram.send_text(f"☀️ {md} 아침 초안 도착\n블로그 1개 + X 1개 · 주제: {draft.get('category', '')}\n"
                           f"아래 순서: ① 썸네일 ② 블로그 제목 ③ 본문 ④ 원본 파일 ⑤ X 글")
        if "thumb" in files:
            telegram.send_photo(files["thumb"], caption="① 썸네일")
            telegram.send_text(draft.get("blog_title", ""))
            telegram.send_text(f"{draft['blog_body']}\n\n{draft.get('hashtags', '')}")
            telegram.send_document(files["blog"], caption="④ 블로그 원본 (.md)")
        telegram.send_text("⑤ 🐦 X 초안 ↓ (그대로 복사해서 쓰세요)")
    else:
        telegram.send_text(f"🌆 {md} 오후 X 초안 ↓ (그대로 복사해서 쓰세요)")
    telegram.send_text(draft["x_post"])
    if draft.get("sources"):
        telegram.send_text("🔗 참고 출처 (팩트체크용)\n" + draft["sources"])
    log.info("텔레그램 전송 완료")


if __name__ == "__main__":
    main()
