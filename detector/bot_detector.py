from dataclasses import dataclass


@dataclass(frozen=True)
class BotRule:
    keyword: str
    category: str
    crawler_name: str


RULES = [
    BotRule("googlebot", "search_engine", "Googlebot"),
    BotRule("bingbot", "search_engine", "Bingbot"),
    BotRule("baiduspider", "search_engine", "Baiduspider"),
    BotRule("yandex", "search_engine", "YandexBot"),
    BotRule("duckduckbot", "search_engine", "DuckDuckBot"),
    BotRule("gptbot", "ai_bot", "GPTBot"),
    BotRule("chatgpt-user", "ai_bot", "ChatGPT-User"),
    BotRule("oai-searchbot", "ai_bot", "OAI-SearchBot"),
    BotRule("claudebot", "ai_bot", "ClaudeBot"),
    BotRule("anthropic-ai", "ai_bot", "Anthropic AI"),
    BotRule("perplexitybot", "ai_bot", "PerplexityBot"),
    BotRule("bytespider", "ai_bot", "Bytespider"),
    BotRule("ahrefsbot", "seo_bot", "AhrefsBot"),
    BotRule("semrushbot", "seo_bot", "SemrushBot"),
    BotRule("mj12bot", "seo_bot", "MJ12Bot"),
    BotRule("dotbot", "seo_bot", "DotBot"),
    BotRule("curl", "script_client", "curl"),
    BotRule("wget", "script_client", "wget"),
    BotRule("python-requests", "script_client", "python-requests"),
    BotRule("scrapy", "script_client", "Scrapy"),
    BotRule("okhttp", "script_client", "OkHttp"),
    BotRule("go-http-client", "script_client", "Go HTTP Client"),
    BotRule("headlesschrome", "script_client", "HeadlessChrome"),
    BotRule("slurp", "unknown_bot", "Slurp"),
    BotRule("spider", "unknown_bot", "Generic Spider"),
    BotRule("crawler", "unknown_bot", "Generic Crawler"),
    BotRule("bot", "unknown_bot", "Generic Bot"),
]

BOT_SCORES = {
    "search_engine": 70,
    "ai_bot": 75,
    "seo_bot": 80,
    "script_client": 85,
    "unknown_bot": 60,
    "human": 0,
}

RISK_LEVELS = {
    "human": "low",
    "search_engine": "low",
    "ai_bot": "medium",
    "seo_bot": "medium",
    "script_client": "high",
    "unknown_bot": "medium",
}


def detect_bot(user_agent: str | None) -> dict:
    ua = (user_agent or "").lower()
    hit_rules = [
        {"keyword": rule.keyword, "category": rule.category, "crawler_name": rule.crawler_name}
        for rule in RULES
        if rule.keyword in ua
    ]

    if not hit_rules:
        category = "human"
        crawler_name = None
    else:
        # RULES are ordered from specific/high-confidence to generic fallback.
        category = hit_rules[0]["category"]
        crawler_name = hit_rules[0]["crawler_name"]

    return {
        "is_bot": category != "human",
        "bot_score": BOT_SCORES[category],
        "bot_category": category,
        "crawler_name": crawler_name,
        "risk_level": RISK_LEVELS[category],
        "hit_rules": hit_rules,
    }
