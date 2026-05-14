from parser import parse_access_log, parse_combined_log, parse_geo_ai_log


def test_parse_combined_log():
    raw = '127.0.0.1 - - [28/Apr/2026:10:30:01 +0900] "GET /robots.txt HTTP/1.1" 200 612 "-" "Googlebot/2.1 (+http://www.google.com/bot.html)"'

    parsed = parse_combined_log(raw)

    assert parsed["client_ip"] == "127.0.0.1"
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/robots.txt"
    assert parsed["protocol"] == "HTTP/1.1"
    assert parsed["status"] == 200
    assert parsed["bytes_sent"] == 612
    assert parsed["referer"] is None
    assert parsed["user_agent"].startswith("Googlebot")


def test_parse_geo_ai_log():
    raw = '198.244.226.14 | [10/May/2026:21:26:58 +0800] | "www.geokeji.com" | "GET /sitemap.xml HTTP/2.0" | 200 | 20240 | "-" | "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)" | 0.000 | "-" | "-"'

    parsed = parse_geo_ai_log(raw)

    assert parsed["client_ip"] == "198.244.226.14"
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/sitemap.xml"
    assert parsed["protocol"] == "HTTP/2.0"
    assert parsed["status"] == 200
    assert parsed["bytes_sent"] == 20240
    assert parsed["referer"] is None
    assert "AhrefsBot" in parsed["user_agent"]


def test_parse_access_log_falls_back_to_geo_ai():
    raw = '165.232.134.49 | [10/May/2026:21:37:35 +0800] | "www.geokeji.com" | "GET / HTTP/2.0" | 200 | 73842 | "-" | "curl/8.7.1" | 0.000 | "-" | "-"'

    parsed = parse_access_log(raw)

    assert parsed["client_ip"] == "165.232.134.49"
    assert parsed["path"] == "/"
    assert parsed["user_agent"] == "curl/8.7.1"
