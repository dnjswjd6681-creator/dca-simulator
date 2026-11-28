"""수집 대상과 실행 설정. 종목·뉴스 소스를 바꾸고 싶으면 이 파일만 고치면 됩니다."""

# ── Claude 설정 ─────────────────────────────────────────────
MODEL = "claude-opus-5-5"
EFFORT = "medium"          # low | medium | high  (높을수록 꼼꼼하지만 비용↑)
WEB_SEARCH_MAX_USES = {"morning": 8, "evening": 4}  # Claude가 웹검색으로 최신 이슈를 확인하는 최대 횟수 (0이면 끔)

# ── 비중: 미주 60 / 국주 20 / 크립토 20 ─────────────────────
WEIGHTS = {"미국주식": 60, "국내주식": 20, "크립토": 20}

# ── 시세 (Yahoo Finance 심볼) ───────────────────────────────
US_INDICES = {
    "S&P500": "^GSPC", "나스닥": "^IXIC", "다우": "^DJI",
    "필라델피아반도체": "^SOX", "러셀2000": "^RUT", "VIX": "^VIX",
}
US_STOCKS = {
    "엔비디아": "NVDA", "애플": "AAPL", "마이크로소프트": "MSFT", "알파벳": "GOOGL",
    "아마존": "AMZN", "메타": "META", "테슬라": "TSLA", "브로드컴": "AVGO",
    "팔란티어": "PLTR", "TSMC": "TSM",
}
KR_INDICES = {"코스피": "^KS11", "코스닥": "^KQ11"}
KR_STOCKS = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "LG에너지솔루션": "373220.KS",
    "현대차": "005380.KS", "삼성바이오로직스": "207940.KS", "NAVER": "035420.KS",
}
MACRO = {
    "원/달러": "KRW=X", "달러인덱스": "DX-Y.NYB", "미국10년물(%)": "^TNX",
    "WTI유가": "CL=F", "금": "GC=F",
}
CRYPTO_IDS = ["bitcoin", "ethereum", "solana", "ripple"]  # CoinGecko id

# ── 뉴스·커뮤니티 RSS ───────────────────────────────────────
FEEDS = {
    "미국주식": [
        ("CNBC Markets", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
        ("CNBC Top", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
        ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
        ("Reddit r/stocks", "https://www.reddit.com/r/stocks/top/.rss?t=day"),
        ("Reddit r/wallstreetbets", "https://www.reddit.com/r/wallstreetbets/top/.rss?t=day"),
    ],
    "국내주식": [
        ("연합뉴스 경제", "https://www.yna.co.kr/rss/economy.xml"),
        ("한국경제 증권", "https://www.hankyung.com/feed/finance"),
        ("매일경제 증권", "https://www.mk.co.kr/rss/50200011/"),
    ],
    "크립토": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("Reddit r/CryptoCurrency", "https://www.reddit.com/r/CryptoCurrency/top/.rss?t=day"),
    ],
}
ITEMS_PER_FEED = 8

# ── 유튜브 (채널 ID를 넣으면 최신 영상 제목을 소재로 씀) ──────
# 채널 ID 찾는 법: 채널 페이지 → 공유 → 채널 ID 복사 (UC로 시작)
YOUTUBE_CHANNELS = {
    # "박종훈의 지식한방": "UCxxxxxxxxxxxxxxxxxxxxxx",
    # "더리브스": "UCxxxxxxxxxxxxxxxxxxxxxx",
    # "EBS 지식": "UCxxxxxxxxxxxxxxxxxxxxxx",
    # "한경 글로벌마켓": "UCxxxxxxxxxxxxxxxxxxxxxx",
}

# ── 썸네일 오른쪽 아래에 들어갈 계정명 (비워두면 안 넣음) ─────
BRAND_NAME = ""   # 예: "○○의 재테크 노트" (썸네일 맨 아래 분홍 글씨)
