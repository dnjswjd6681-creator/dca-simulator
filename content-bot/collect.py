"""시세·지표·뉴스 수집. 소스 하나가 실패해도 나머지로 계속 진행한다."""
from __future__ import annotations

import datetime as dt
import logging

import feedparser
import requests

import config

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (content-bot; market briefing)"}
TIMEOUT = 20


def _get_json(url: str, **params):
    r = requests.get(url, params=params or None, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


# ── 시세 ────────────────────────────────────────────────────
def quotes(symbols: dict[str, str]) -> list[dict]:
    """최근 종가, 전일 대비 등락률, 5일·1개월 등락률."""
    import yfinance as yf

    out = []
    try:
        data = yf.download(list(symbols.values()), period="2mo", interval="1d",
                           progress=False, auto_adjust=False, group_by="ticker", threads=True)
    except Exception as e:  # noqa: BLE001
        log.warning("yfinance 실패: %s", e)
        return out
    for name, sym in symbols.items():
        try:
            close = data[sym]["Close"].dropna()
            if len(close) < 2:
                continue
            last, prev = float(close.iloc[-1]), float(close.iloc[-2])
            w = float(close.iloc[-6]) if len(close) > 5 else prev
            m = float(close.iloc[-22]) if len(close) > 21 else float(close.iloc[0])
            out.append({
                "name": name, "symbol": sym, "date": str(close.index[-1].date()),
                "close": round(last, 2),
                "chg_1d_%": round((last / prev - 1) * 100, 2),
                "chg_5d_%": round((last / w - 1) * 100, 2),
                "chg_1m_%": round((last / m - 1) * 100, 2),
            })
        except Exception as e:  # noqa: BLE001
            log.warning("%s(%s) 시세 실패: %s", name, sym, e)
    return out


# ── 크립토 ──────────────────────────────────────────────────
def crypto() -> dict:
    res: dict = {}
    try:
        g = _get_json("https://api.coingecko.com/api/v3/global")["data"]
        res["total_mcap_usd_trillion"] = round(g["total_market_cap"]["usd"] / 1e12, 3)
        res["mcap_chg_24h_%"] = round(g["market_cap_change_percentage_24h_usd"], 2)
        res["btc_dominance_%"] = round(g["market_cap_percentage"]["btc"], 2)
        res["eth_dominance_%"] = round(g["market_cap_percentage"]["eth"], 2)
    except Exception as e:  # noqa: BLE001
        log.warning("CoinGecko global 실패: %s", e)
    try:
        p = _get_json("https://api.coingecko.com/api/v3/simple/price",
                      ids=",".join(config.CRYPTO_IDS), vs_currencies="usd,krw",
                      include_24hr_change="true")
        res["prices"] = {k: {"usd": v.get("usd"), "krw": v.get("krw"),
                             "chg_24h_%": round(v.get("usd_24h_change") or 0, 2)}
                         for k, v in p.items()}
    except Exception as e:  # noqa: BLE001
        log.warning("CoinGecko price 실패: %s", e)
    try:
        f = _get_json("https://api.alternative.me/fng/", limit=7)["data"]
        res["fear_greed"] = [{"value": int(x["value"]), "label": x["value_classification"]} for x in f]
    except Exception as e:  # noqa: BLE001
        log.warning("공포탐욕지수 실패: %s", e)
    try:
        s = _get_json("https://stablecoins.llama.fi/stablecoincharts/all")
        now, week = s[-1], s[-8]
        n = now["totalCirculatingUSD"]["peggedUSD"]
        w = week["totalCirculatingUSD"]["peggedUSD"]
        res["stablecoin_supply_usd_billion"] = round(n / 1e9, 1)
        res["stablecoin_7d_chg_usd_billion"] = round((n - w) / 1e9, 2)
    except Exception as e:  # noqa: BLE001
        log.warning("DefiLlama 실패: %s", e)
    return res


# ── 뉴스 / 커뮤니티 / 유튜브 ────────────────────────────────
def _feed(url: str, limit: int) -> list[dict]:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    items = []
    for e in parsed.entries[:limit]:
        summary = (e.get("summary") or "").replace("\n", " ")
        # HTML 태그 대충 제거
        import re
        summary = re.sub(r"<[^>]+>", "", summary)[:300]
        items.append({"title": e.get("title", "").strip(), "summary": summary,
                      "link": e.get("link", ""), "published": e.get("published", "")})
    return items


def news() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for cat, feeds in config.FEEDS.items():
        out[cat] = []
        for src, url in feeds:
            try:
                for it in _feed(url, config.ITEMS_PER_FEED):
                    it["source"] = src
                    out[cat].append(it)
            except Exception as e:  # noqa: BLE001
                log.warning("RSS 실패 %s: %s", src, e)
    return out


def youtube() -> list[dict]:
    vids = []
    for name, cid in config.YOUTUBE_CHANNELS.items():
        try:
            for it in _feed(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", 3):
                vids.append({"channel": name, "title": it["title"], "link": it["link"],
                             "published": it["published"]})
        except Exception as e:  # noqa: BLE001
            log.warning("유튜브 실패 %s: %s", name, e)
    return vids


def collect_all() -> dict:
    kst = dt.timezone(dt.timedelta(hours=9))
    return {
        "collected_at_kst": dt.datetime.now(kst).strftime("%Y-%m-%d %H:%M"),
        "us_indices": quotes(config.US_INDICES),
        "us_stocks": quotes(config.US_STOCKS),
        "kr_indices": quotes(config.KR_INDICES),
        "kr_stocks": quotes(config.KR_STOCKS),
        "macro": quotes(config.MACRO),
        "crypto": crypto(),
        "news": news(),
        "youtube": youtube(),
    }
