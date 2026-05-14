# 官网智能访客分析系统一期升级计划

## Summary

将现有“官网爬虫统计 SDK”升级为一期官网智能访客分析系统，重点交付两条业务价值线：企业访客识别和 AI/搜索爬虫核心页面监控。

在现有 FastAPI + SQLAlchemy + PostgreSQL + 静态 Dashboard 上增量演进，不重写系统；数据库迁移正式引入 Alembic。

## Key Changes

- 企业识别采用混合模式：本地规则库优先，外部 Provider 走可插拔接口；一期默认提供 `NullProvider`。
- 新增核心页面库：通过数据库和 API 手工维护官网核心页面。
- 采集入库时增加事件增强：标准化 URL path、识别 crawler_name、识别企业/机构、记录识别来源与置信度。
- Dashboard 升级为“智能访客分析”，展示高意向企业名单、AI 爬虫抓取概览、核心页面覆盖率、高价值页面排行和异常访问提示。
- 保留现有 `/api/stats/*` 接口兼容旧统计和 CSV 导出。

## Interfaces And Data

- 引入 Alembic，并生成首个迁移。
- 对 `access_event` 增加：
  - `normalized_path`
  - `crawler_name`
  - `organization_name`
  - `organization_domain`
  - `organization_type`
  - `organization_source`
  - `organization_confidence`
- 新增 `visitor_identity_rule`：维护 IP、CIDR、ASN、域名等到企业/机构的本地识别规则。
- 新增 `core_page`：维护 `site_id`、`path`、`title`、`category`、`priority`、`is_active`。
- 新增 `visitor_enrichment_cache`：缓存外部 Provider 查询结果。
- 新增 API：
  - `GET/POST/PATCH /api/core-pages`
  - `GET/POST/PATCH /api/visitor-rules`
  - `GET /api/intelligence/overview`
  - `GET /api/intelligence/leads`
  - `GET /api/intelligence/crawler-coverage`
  - `GET /api/intelligence/page-value`

## Business Logic

- 企业识别流程：本地规则匹配优先；未命中查缓存；缓存未命中调用 Provider；默认 Provider 返回空结果。
- 高意向企业评分：核心页面访问、访问次数、近 24 小时活跃、产品/案例/联系类页面访问加权，分数封顶 100。
- AI 爬虫监控：基于 `bot_category=ai_bot` 和 `crawler_name` 聚合 GPTBot、ClaudeBot、PerplexityBot、Bytespider 等。
- 核心页面覆盖率：按 `core_page` 中启用页面统计最近 30 天 AI 爬虫和搜索引擎爬虫访问情况。
- 异常提示：高频脚本客户端、核心页面 4xx/5xx、AI 爬虫长期未抓取核心页面。

## Test Plan

- 单元测试：
  - bot detector 返回 `crawler_name`、分类和风险等级。
  - path 标准化去除 query，保留根路径。
  - 本地企业识别规则支持 exact IP 和 CIDR。
  - 高意向企业评分稳定可预测。
  - 核心页面覆盖率能区分 AI、搜索和未覆盖页面。
- API 测试：
  - 核心页面 CRUD。
  - 访客规则 CRUD。
  - intelligence 聚合接口在空数据、有企业数据、有 AI 爬虫数据下均返回稳定结构。
- 回归测试：
  - 现有 parser、collector、stats API、CSV 导出保持兼容。
  - `PYTHONPATH=. pytest` 全量通过。

## Assumptions

- 一期不接具体第三方企业识别供应商，只完成可插拔 Provider、缓存和配置开关。
- 核心页面由数据库手工维护，不从 sitemap 自动导入。
- 现有生产数据需要保留，因此使用 Alembic 迁移，不重建表。
- 内容价值分析只做基础页面排行，不展开完整内容优化建议生成；该能力留到二期深化。
