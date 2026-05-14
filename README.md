# 官网爬虫统计 SDK 系统 MVP

这个项目通过采集 Nginx access log，解析官网访问事件，使用内置规则识别爬虫请求，并提供 FastAPI 查询站点、采集结果和统计数据。

当前版本已升级为官网智能访客分析系统一期，新增企业访客识别、AI/搜索爬虫核心页面监控、高意向企业名单、核心页面可见性和页面线索价值分析。

第一版包含：日志采集 Agent、本地 Nginx combined log 解析、规则识别、PostgreSQL 入库、基础统计 API、访客识别规则、核心页面库和智能分析 API。

## 目录结构

```text
api/        FastAPI 接口与路由
agent/      本地 access.log 采集脚本
parser/     Nginx combined log 解析
detector/   爬虫识别规则
models/     SQLAlchemy 数据库模型
schemas/    Pydantic DTO
services/   业务服务
config/     配置
scripts/    初始化脚本
tests/      简单测试样例
```

## 启动步骤

复制配置示例：

```bash
cp .env.example .env
```

使用 Docker Compose 启动 PostgreSQL 和 API：

```bash
docker compose up --build
```

如果部署机器的宿主机 `5432` 已被占用，可以使用远端部署配置，它会把 PostgreSQL 映射到宿主机 `55432`：

```bash
docker-compose -f docker-compose.remote.yml up -d --build
```

服务启动后访问：

```bash
curl http://localhost:8000/health
```

浏览器打开仪表盘：

```text
http://localhost:8000/dashboard
```

默认登录账号：

```text
账号：yishankeji
密码：YishanSDK8888
```

## 初始化数据库

Docker Compose 中的 API 服务会自动执行：

```bash
python scripts/init_db.py
```

如果你只启动 PostgreSQL，也可以在本地执行：

```bash
pip install -r requirements.txt
python scripts/init_db.py
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

已有数据库升级请使用 Alembic：

```bash
alembic upgrade head
```

## 创建站点示例

```bash
curl -X POST http://localhost:8000/api/sites \
  -H "Content-Type: application/json" \
  -d '{
    "site_code": "demo",
    "site_name": "Demo 官网",
    "domain": "example.com",
    "base_url": "https://example.com",
    "status": "active"
  }'
```

查询站点：

```bash
curl http://localhost:8000/api/sites
curl http://localhost:8000/api/sites/1
```

## 上报日志示例

```bash
curl -X POST http://localhost:8000/api/collect/access-log \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "raw_log": "127.0.0.1 - - [28/Apr/2026:10:30:01 +0900] \"GET /robots.txt HTTP/1.1\" 200 612 \"-\" \"Googlebot/2.1 (+http://www.google.com/bot.html)\""
  }'
```

## 运行采集 Agent

Agent 支持增量读取，offset 默认记录在 `agent_offset.json`：

```bash
python -m agent.log_agent \
  --log-path ./sample_access.log \
  --offset-path ./agent_offset.json \
  --api-base-url http://localhost:8000 \
  --site-id 1
```

如果再次运行，Agent 会从上次 offset 后继续读取，避免重复上报。

## 查询统计示例

```bash
curl "http://localhost:8000/api/stats/overview?site_id=1"
curl "http://localhost:8000/api/stats/bot-category?site_id=1"
curl "http://localhost:8000/api/stats/top-ip?site_id=1&limit=10"
curl "http://localhost:8000/api/stats/top-path?site_id=1&limit=10"
curl "http://localhost:8000/api/stats/top-ua?site_id=1&limit=10"
curl -OJ "http://localhost:8000/api/stats/export.csv?site_id=1&limit=50"
```

也可以直接在浏览器访问 `/dashboard` 查看可视化统计，并点击“导出 CSV”下载当前站点统计报表。

## 智能分析接口

```bash
curl "http://localhost:8000/api/intelligence/overview?site_id=1"
curl "http://localhost:8000/api/intelligence/leads?site_id=1&limit=10"
curl "http://localhost:8000/api/intelligence/crawler-coverage?site_id=1"
curl "http://localhost:8000/api/intelligence/page-value?site_id=1&limit=10"
curl "http://localhost:8000/api/intelligence/anomaly-hints?site_id=1"
```

维护核心页面：

```bash
curl -X POST http://localhost:8000/api/core-pages \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "path": "/products",
    "title": "产品页",
    "category": "product",
    "priority": 90
  }'
```

维护企业访客识别规则：

```bash
curl -X POST http://localhost:8000/api/visitor-rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_type": "cidr",
    "pattern": "203.0.113.0/24",
    "organization_name": "示例企业",
    "organization_domain": "example.com",
    "organization_type": "company",
    "confidence": 90
  }'
```

## 运行测试

```bash
PYTHONPATH=. pytest
```

## 使用与开发说明

更完整的接入、API、开发和运维说明见：

```text
docs/SDK_USAGE_DEV_GUIDE.md
```
