from detector import detect_bot


def test_detect_search_engine_bot():
    result = detect_bot("Googlebot/2.1 (+http://www.google.com/bot.html)")

    assert result["is_bot"] is True
    assert result["bot_score"] == 70
    assert result["bot_category"] == "search_engine"
    assert result["crawler_name"] == "Googlebot"
    assert result["risk_level"] == "low"


def test_detect_script_client():
    result = detect_bot("curl/8.0.1")

    assert result["is_bot"] is True
    assert result["bot_category"] == "script_client"
    assert result["crawler_name"] == "curl"
    assert result["risk_level"] == "high"


def test_detect_human():
    result = detect_bot("Mozilla/5.0 Safari/537.36")

    assert result["is_bot"] is False
    assert result["bot_score"] == 0
    assert result["bot_category"] == "human"
    assert result["crawler_name"] is None


def test_detect_ai_bot_name():
    result = detect_bot("Mozilla/5.0 AppleWebKit/537.36 (compatible; GPTBot/1.2; +https://openai.com/gptbot)")

    assert result["is_bot"] is True
    assert result["bot_category"] == "ai_bot"
    assert result["crawler_name"] == "GPTBot"
