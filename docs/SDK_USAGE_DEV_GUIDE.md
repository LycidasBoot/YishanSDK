# 官网爬虫统计 SDK 使用与开发说明

## 1. 系统定位

官网爬虫统计 SDK 系统用于采集官网 Nginx access log，识别访问流量中的爬虫请求，并提供基础统计查询能力。

当前 MVP 已支持：

- 站点管理
- Nginx combined access log 解析
- 本地日志 Agent 增量采集
- User-Agent 规则识别爬虫
- PostgreSQL 入库
- 爬虫占比、TOP IP、TOP URL、TOP User-Agent 查询

当前 MVP 暂不包含：

- JavaScript Web SDK
- AI 模型判断
- 自动封禁
- 管理后台页面
- 多租户权限体系

## 2. 线上部署信息

当前部署机器：

```text
192.168.31.34
```

API 地址：

```text
http://192.168.31.34:8000
```

健康检查：

```bash
curl http://192.168.31.34:8000/health
```

前端仪表盘：

```text
http://192.168.31.34:8000/dashboard
```

项目目录：

```text
/opt/crawler-stats-sdk
```

API systemd 服务：

```text
crawler-stats-api
```

PostgreSQL 容器：

```text
crawler_stats_postgres
```

数据库连接：

```text
host: 192.168.31.34
port: 55432
database: crawler_stats
user: crawler
password: crawler123
```

说明：远端已有 PostgreSQL 占用宿主机 `5432`，因此本系统 PostgreSQL 映射到宿主机 `55432`。

## 3. 快速使用流程

### 3.1 创建站点

每个官网需要先创建一个站点，后续日志上报都通过 `site_id` 关联。

示例：创建“移山科技官网”：

```bash
curl -X POST http://192.168.31.34:8000/api/sites \
  -H "Content-Type: application/json" \
  -d '{
    "site_code": "yishan-official",
    "site_name": "移山科技官网",
    "domain": "yishankeji.com",
    "base_url": "https://yishankeji.com",
    "status": "active"
  }'
```

返回示例：

```json
{
  "id": 2,
  "site_code": "yishan-official",
  "site_name": "移山科技官网",
  "domain": "yishankeji.com",
  "base_url": "https://yishankeji.com",
  "status": "active",
  "created_at": "2026-04-28T03:20:12.068299Z",
  "updated_at": "2026-04-28T03:20:12.068299Z"
}
```

其中 `id` 就是后续采集和查询使用的 `site_id`。

查询站点列表：

```bash
curl http://192.168.31.34:8000/api/sites
```

查询站点详情：

```bash
curl http://192.168.31.34:8000/api/sites/2
```

### 3.2 接入 Nginx access log

如果 Nginx 在 `192.168.31.34` 本机，进入项目目录：

```bash
cd /opt/crawler-stats-sdk
```

执行 Agent：

```bash
/opt/crawler-stats-sdk/.venv/bin/python -m agent.log_agent \
  --log-path /var/log/nginx/access.log \
  --offset-path ./yishan_agent_offset.json \
  --api-base-url http://192.168.31.34:8000 \
  --site-id 2
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `--log-path` | Nginx access.log 文件路径 |
| `--offset-path` | 记录读取 offset 的本地文件 |
| `--api-base-url` | 采集 API 地址 |
| `--site-id` | 站点 ID |

Agent 会从上次 offset 后继续读取，避免重复上报。

如果 Nginx 在其他官网服务器，需要把项目代码或至少 Agent 相关代码部署到那台服务器，然后将 `--api-base-url` 指向：

```text
http://192.168.31.34:8000
```

### 3.3 使用 cron 定时采集

当前 Agent 是“执行一次，读取当前新增日志”。生产上可以先用 cron 每分钟执行一次：

```cron
* * * * * cd /opt/crawler-stats-sdk && /opt/crawler-stats-sdk/.venv/bin/python -m agent.log_agent --log-path /var/log/nginx/access.log --offset-path ./yishan_agent_offset.json --api-base-url http://192.168.31.34:8000 --site-id 2 >> ./agent.log 2>&1
```

## 4. 前端仪表盘

SDK 内置了一个轻量统计页面：

```text
/dashboard
```

主要能力：

- 选择站点
- 查看总请求数、爬虫请求、人工访问、爬虫占比
- 查看爬虫分类统计
- 查看 TOP IP
- 查看 TOP URL Path
- 查看 TOP User-Agent

页面直接调用当前服务的 `/api/sites` 和 `/api/stats/*` 接口。只要 Agent 持续把官网 access log 上报进来，页面数据就会刷新。

当前部署访问地址：

```text
http://192.168.31.34:8000/dashboard
http://100.112.159.103:8000/dashboard
```

## 5. API 使用说明

### 5.1 站点接口

#### 新增站点

```http
POST /api/sites
```

请求体：

```json
{
  "site_code": "yishan-official",
  "site_name": "移山科技官网",
  "domain": "yishankeji.com",
  "base_url": "https://yishankeji.com",
  "status": "active"
}
```

#### 查询站点列表

```http
GET /api/sites
```

#### 查询站点详情

```http
GET /api/sites/{site_id}
```

### 5.2 日志接入接口

```http
POST /api/collect/access-log
```

请求体：

```json
{
  "site_id": 2,
  "raw_log": "127.0.0.1 - - [28/Apr/2026:10:30:01 +0900] \"GET /robots.txt HTTP/1.1\" 200 612 \"-\" \"Googlebot/2.1 (+http://www.google.com/bot.html)\""
}
```

返回示例：

```json
{
  "event_id": 1,
  "site_id": 2,
  "event_time": "2026-04-28T01:30:01Z",
  "client_ip": "127.0.0.1",
  "path": "/robots.txt",
  "user_agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
  "is_bot": true,
  "bot_score": 70,
  "bot_category": "search_engine",
  "risk_level": "low",
  "hit_rules": [
    {
      "keyword": "googlebot",
      "category": "search_engine"
    }
  ]
}
```

### 5.3 统计接口

#### 总览

```http
GET /api/stats/overview?site_id=2
```

返回：

```json
{
  "total_requests": 1000,
  "bot_requests": 300,
  "human_requests": 700,
  "bot_ratio": 0.3
}
```

#### 爬虫分类统计

```http
GET /api/stats/bot-category?site_id=2
```

返回：

```json
[
  {
    "key": "search_engine",
    "count": 120
  },
  {
    "key": "ai_bot",
    "count": 40
  }
]
```

#### TOP IP

```http
GET /api/stats/top-ip?site_id=2&limit=10
```

#### TOP URL Path

```http
GET /api/stats/top-path?site_id=2&limit=10
```

#### TOP User-Agent

```http
GET /api/stats/top-ua?site_id=2&limit=10
```

## 6. Nginx 日志格式要求

当前解析器支持 Nginx 默认 combined log 格式：

```text
127.0.0.1 - - [28/Apr/2026:10:30:01 +0900] "GET /robots.txt HTTP/1.1" 200 612 "-" "Googlebot/2.1 (+http://www.google.com/bot.html)"
```

对应字段：

| 字段 | 示例 |
| --- | --- |
| `client_ip` | `127.0.0.1` |
| `request_time` | `28/Apr/2026:10:30:01 +0900` |
| `method` | `GET` |
| `path` | `/robots.txt` |
| `protocol` | `HTTP/1.1` |
| `status` | `200` |
| `bytes_sent` | `612` |
| `referer` | `-` |
| `user_agent` | `Googlebot/2.1 ...` |

如果官网 Nginx 使用了自定义 log_format，需要扩展 `parser/nginx_parser.py`。

## 7. 爬虫识别规则

当前版本基于 User-Agent 关键词识别。

### 7.1 分类

| 分类 | 说明 | 分数 | 风险 |
| --- | --- | --- | --- |
| `human` | 未命中爬虫规则 | 0 | `low` |
| `search_engine` | 搜索引擎爬虫 | 70 | `low` |
| `ai_bot` | AI 训练/检索类爬虫 | 75 | `medium` |
| `seo_bot` | SEO 工具爬虫 | 80 | `medium` |
| `script_client` | 脚本或命令行客户端 | 85 | `high` |
| `unknown_bot` | 未分类爬虫 | 60 | `medium` |

### 7.2 关键词规则

搜索引擎：

```text
googlebot, bingbot, baiduspider, yandex, duckduckbot
```

AI Bot：

```text
gptbot, claudebot, perplexitybot, bytespider
```

SEO Bot：

```text
ahrefsbot, semrushbot, mj12bot, dotbot
```

脚本客户端：

```text
curl, wget, python-requests, scrapy, okhttp, go-http-client, headlesschrome
```

未知爬虫：

```text
bot, spider, crawler, slurp
```

扩展规则文件：

```text
detector/bot_detector.py
```

## 8. 数据库表说明

### 8.1 site

站点表。

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `site_code` | 站点编码，唯一 |
| `site_name` | 站点名称 |
| `domain` | 域名 |
| `base_url` | 官网地址 |
| `status` | 状态 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 8.2 access_event

访问事件表。

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `site_id` | 站点 ID |
| `event_time` | 日志中的请求时间 |
| `client_ip` | 客户端 IP |
| `method` | HTTP 方法 |
| `path` | URL path |
| `protocol` | HTTP 协议 |
| `status` | HTTP 状态码 |
| `bytes_sent` | 响应字节数 |
| `referer` | Referer |
| `user_agent` | User-Agent |
| `is_bot` | 是否爬虫 |
| `bot_score` | 爬虫分数 |
| `bot_category` | 爬虫分类 |
| `risk_level` | 风险等级 |
| `hit_rules` | 命中规则，JSONB |
| `created_at` | 入库时间 |

## 9. 开发说明

### 9.1 本地启动

安装依赖：

```bash
pip install -r requirements.txt
```

启动 PostgreSQL：

```bash
docker compose up -d postgres
```

初始化表：

```bash
python scripts/init_db.py
```

启动 API：

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

运行测试：

```bash
pytest
```

### 9.2 模块职责

| 目录 | 职责 |
| --- | --- |
| `api/` | FastAPI 应用和路由 |
| `agent/` | 本地日志采集 Agent |
| `parser/` | Nginx 日志解析 |
| `detector/` | 爬虫识别规则 |
| `models/` | SQLAlchemy ORM 模型 |
| `schemas/` | Pydantic DTO |
| `services/` | 业务逻辑 |
| `config/` | 配置读取 |
| `scripts/` | 初始化脚本 |
| `tests/` | 测试样例 |

### 9.3 常见扩展点

#### 新增爬虫规则

修改：

```text
detector/bot_detector.py
```

在 `RULES` 中增加关键词和分类。

#### 支持新的日志格式

修改：

```text
parser/nginx_parser.py
```

建议新增独立解析函数，不要直接破坏 combined log 的兼容性。

#### 增加新的统计接口

通常需要修改：

```text
services/stats_service.py
api/routes/stats.py
schemas/stats.py
```

#### 增加字段

通常需要修改：

```text
models/access_event.py
schemas/access_log.py
services/access_log_service.py
scripts/init_db.py
```

当前 MVP 使用 `create_all` 初始化表，没有 Alembic 迁移。生产演进时建议引入 Alembic。

## 10. 远端运维命令

查看 API 状态：

```bash
sudo systemctl status crawler-stats-api --no-pager
```

重启 API：

```bash
sudo systemctl restart crawler-stats-api
```

查看 API 日志：

```bash
sudo journalctl -u crawler-stats-api -f
```

查看 PostgreSQL 容器：

```bash
sudo docker ps --filter name=crawler_stats_postgres
```

查看 PostgreSQL 日志：

```bash
sudo docker logs crawler_stats_postgres --tail 100
```

进入数据库：

```bash
sudo docker exec -it crawler_stats_postgres psql -U crawler -d crawler_stats
```

## 11. 常见问题

### 11.1 Agent 没有新增数据

检查：

- `--log-path` 是否正确
- 当前用户是否有权限读取 Nginx access.log
- `--site-id` 是否存在
- `--api-base-url` 是否可访问
- offset 文件是否已经读到文件末尾

如果需要从头重读，可以删除 offset 文件：

```bash
rm ./yishan_agent_offset.json
```

### 11.2 解析失败

通常是 Nginx 日志格式不是 combined log。检查日志是否类似：

```text
IP - - [time] "METHOD path PROTOCOL" status bytes "referer" "user-agent"
```

如果不一致，需要扩展 parser。

### 11.3 API 访问不了

检查服务：

```bash
sudo systemctl status crawler-stats-api --no-pager
curl http://127.0.0.1:8000/health
```

检查端口：

```bash
ss -ltnp | grep 8000
```

### 11.4 数据库连接失败

检查容器：

```bash
sudo docker ps --filter name=crawler_stats_postgres
sudo docker exec crawler_stats_postgres pg_isready -U crawler -d crawler_stats
```

检查 `.env`：

```text
DATABASE_URL=postgresql+psycopg://crawler:crawler123@localhost:55432/crawler_stats
```

## 12. 推荐后续版本

建议按以下顺序演进：

1. Agent 改为常驻进程，支持 tail -f。
2. 增加时间范围查询，例如按小时、天统计。
3. 增加站点维度鉴权 token，避免任意上报。
4. 引入 Alembic 管理数据库迁移。
5. 增加 Web 管理后台。
6. 增加 IP 反查、ASN、国家地区分析。
7. 增加风险策略和封禁建议，但先只做建议，不自动封禁。
