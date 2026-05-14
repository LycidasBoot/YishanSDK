const state = {
  sites: [],
  selectedSiteId: null,
};

const els = {
  siteSelect: document.getElementById("siteSelect"),
  refreshButton: document.getElementById("refreshButton"),
  exportButton: document.getElementById("exportButton"),
  logoutButton: document.getElementById("logoutButton"),
  statusMessage: document.getElementById("statusMessage"),
  lastUpdated: document.getElementById("lastUpdated"),
  totalRequests: document.getElementById("totalRequests"),
  botRequests: document.getElementById("botRequests"),
  humanRequests: document.getElementById("humanRequests"),
  botRatio: document.getElementById("botRatio"),
  trafficRiskHint: document.getElementById("trafficRiskHint"),
  totalOrganizations: document.getElementById("totalOrganizations"),
  highIntentOrganizations: document.getElementById("highIntentOrganizations"),
  aiBotRequests: document.getElementById("aiBotRequests"),
  aiCoverageRatio: document.getElementById("aiCoverageRatio"),
  riskHint: document.getElementById("riskHint"),
  categoryList: document.getElementById("categoryList"),
  topIpList: document.getElementById("topIpList"),
  topPathList: document.getElementById("topPathList"),
  topUaList: document.getElementById("topUaList"),
  leadList: document.getElementById("leadList"),
  crawlerList: document.getElementById("crawlerList"),
  coverageList: document.getElementById("coverageList"),
  pageValueList: document.getElementById("pageValueList"),
  anomalyList: document.getElementById("anomalyList"),
};

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value || 0);
}

function formatRatio(value) {
  return `${((value || 0) * 100).toFixed(1)}%`;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function setStatus(message, isError = false) {
  if (!els.statusMessage) return;
  els.statusMessage.textContent = message;
  els.statusMessage.classList.toggle("error", isError);
}

function setText(element, value) {
  if (element) {
    element.textContent = value;
  }
}

function setMetricPlaceholders() {
  setText(els.totalRequests, "-");
  setText(els.botRequests, "-");
  setText(els.humanRequests, "-");
  setText(els.botRatio, "-");
  setText(els.trafficRiskHint, "等待统计数据");
  setText(els.totalOrganizations, "-");
  setText(els.highIntentOrganizations, "-");
  setText(els.aiBotRequests, "-");
  setText(els.aiCoverageRatio, "-");
  setText(els.riskHint, "等待智能分析数据");
}

function renderList(container, rows, color) {
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = '<div class="empty">暂无数据</div>';
    return;
  }

  const max = Math.max(...rows.map((row) => row.count), 1);
  container.innerHTML = rows
    .map((row) => {
      const width = Math.max(5, Math.round((row.count / max) * 100));
      return `
        <div class="rank-row" title="${escapeHtml(row.key)}">
          <div class="rank-main">
            <span class="rank-key">${escapeHtml(row.key || "-")}</span>
            <span class="rank-count">${formatNumber(row.count)}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:${width}%; background:${color}"></div>
          </div>
        </div>
      `;
    })
    .join("");
}

function updateTrafficOverview(overview) {
  setText(els.totalRequests, formatNumber(overview.total_requests));
  setText(els.botRequests, formatNumber(overview.bot_requests));
  setText(els.humanRequests, formatNumber(overview.human_requests));
  setText(els.botRatio, formatRatio(overview.bot_ratio));

  if (overview.bot_ratio >= 0.5) {
    setText(els.trafficRiskHint, "爬虫占比较高");
  } else if (overview.bot_ratio >= 0.2) {
    setText(els.trafficRiskHint, "建议持续观察");
  } else {
    setText(els.trafficRiskHint, "流量结构平稳");
  }
}

function renderLeadList(container, rows) {
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = '<div class="empty">暂无已识别企业线索</div>';
    return;
  }

  container.innerHTML = rows
    .map((row) => {
      const title = [row.organization_domain, row.organization_type].filter(Boolean).join(" · ");
      return `
        <div class="lead-row">
          <div class="lead-main">
            <div>
              <strong>${escapeHtml(row.organization_name)}</strong>
              <span>${escapeHtml(title || "未知类型")}</span>
            </div>
            <b>${formatNumber(row.intent_score)}</b>
          </div>
          <div class="lead-meta">
            <span>${formatNumber(row.request_count)} 次访问</span>
            <span>${formatNumber(row.core_page_hits)} 次核心页面</span>
            <span>${formatNumber(row.recent_hits)} 次近 24h</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderCoverageList(container, coverage) {
  if (!container) return;
  const rows = coverage.pages || [];
  if (!rows.length) {
    container.innerHTML = '<div class="empty">暂无核心页面，请先通过 /api/core-pages 维护</div>';
    return;
  }

  container.innerHTML = rows
    .map((row) => {
      const aiState = row.ai_hits > 0 ? `AI ${formatNumber(row.ai_hits)}` : "AI 未覆盖";
      const searchState = row.search_hits > 0 ? `搜索 ${formatNumber(row.search_hits)}` : "搜索未覆盖";
      const errorState = row.status_errors > 0 ? `${formatNumber(row.status_errors)} 个错误` : "状态正常";
      return `
        <div class="coverage-row">
          <div class="rank-main">
            <span class="rank-key">${escapeHtml(row.title)} · ${escapeHtml(row.path)}</span>
            <span class="rank-count">${formatNumber(row.priority)}</span>
          </div>
          <div class="lead-meta">
            <span>${escapeHtml(aiState)}</span>
            <span>${escapeHtml(searchState)}</span>
            <span>${escapeHtml(errorState)}</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderHints(container, rows) {
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = '<div class="empty compact">暂无异常提示</div>';
    return;
  }

  container.innerHTML = rows.map((row) => `<div class="hint-item">${escapeHtml(row)}</div>`).join("");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadSites() {
  state.sites = await fetchJson("/api/sites");
  els.siteSelect.innerHTML = "";

  if (!state.sites.length) {
    const option = document.createElement("option");
    option.textContent = "暂无站点，请先创建站点";
    option.value = "";
    els.siteSelect.appendChild(option);
    state.selectedSiteId = null;
    return;
  }

  state.sites.forEach((site) => {
    const option = document.createElement("option");
    option.value = site.id;
    option.textContent = `${site.site_name} (${site.domain})`;
    els.siteSelect.appendChild(option);
  });

  state.selectedSiteId = Number(els.siteSelect.value || state.sites[0].id);
}

function updateOverview(overview) {
  setText(els.totalOrganizations, formatNumber(overview.total_organizations));
  setText(els.highIntentOrganizations, formatNumber(overview.high_intent_organizations));
  setText(els.aiBotRequests, formatNumber(overview.ai_bot_requests));
  setText(els.aiCoverageRatio, formatRatio(overview.ai_coverage_ratio));

  if (overview.alert_count > 0) {
    setText(els.riskHint, `${formatNumber(overview.alert_count)} 条待关注提示`);
  } else if (overview.active_core_pages === 0) {
    setText(els.riskHint, "请维护核心页面");
  } else {
    setText(els.riskHint, "核心页面覆盖平稳");
  }
}

async function loadDashboard() {
  if (!state.selectedSiteId) {
    setMetricPlaceholders();
    renderList(els.categoryList, [], "#245BDB");
    renderList(els.topIpList, [], "#D97706");
    renderList(els.topPathList, [], "#059669");
    renderList(els.topUaList, [], "#7C3AED");
    renderLeadList(els.leadList, []);
    renderList(els.crawlerList, [], "#D97706");
    renderCoverageList(els.coverageList, { pages: [] });
    renderList(els.pageValueList, [], "#059669");
    renderHints(els.anomalyList, []);
    setStatus("暂无站点。请先通过 POST /api/sites 创建站点。", true);
    return;
  }

  setStatus("正在刷新智能分析数据...");
  if (els.refreshButton) {
    els.refreshButton.disabled = true;
  }

  try {
    const siteId = state.selectedSiteId;
    const trafficResults = await Promise.allSettled([
      fetchJson(`/api/stats/overview?site_id=${siteId}`),
      fetchJson(`/api/stats/bot-category?site_id=${siteId}`),
      fetchJson(`/api/stats/top-ip?site_id=${siteId}&limit=10`),
      fetchJson(`/api/stats/top-path?site_id=${siteId}&limit=10`),
      fetchJson(`/api/stats/top-ua?site_id=${siteId}&limit=10`),
    ]);

    if (trafficResults[0].status === "fulfilled") updateTrafficOverview(trafficResults[0].value);
    if (trafficResults[1].status === "fulfilled") renderList(els.categoryList, trafficResults[1].value, "#245BDB");
    if (trafficResults[2].status === "fulfilled") renderList(els.topIpList, trafficResults[2].value, "#D97706");
    if (trafficResults[3].status === "fulfilled") renderList(els.topPathList, trafficResults[3].value, "#059669");
    if (trafficResults[4].status === "fulfilled") renderList(els.topUaList, trafficResults[4].value, "#7C3AED");

    const intelligenceResults = await Promise.allSettled([
      fetchJson(`/api/intelligence/overview?site_id=${siteId}`),
      fetchJson(`/api/intelligence/leads?site_id=${siteId}&limit=10`),
      fetchJson(`/api/intelligence/crawler-names?site_id=${siteId}`),
      fetchJson(`/api/intelligence/crawler-coverage?site_id=${siteId}`),
      fetchJson(`/api/intelligence/page-value?site_id=${siteId}&limit=10`),
      fetchJson(`/api/intelligence/anomaly-hints?site_id=${siteId}`),
    ]);

    if (intelligenceResults[0].status === "fulfilled") updateOverview(intelligenceResults[0].value);
    if (intelligenceResults[1].status === "fulfilled") renderLeadList(els.leadList, intelligenceResults[1].value);
    if (intelligenceResults[2].status === "fulfilled") renderList(els.crawlerList, intelligenceResults[2].value, "#D97706");
    if (intelligenceResults[3].status === "fulfilled") renderCoverageList(els.coverageList, intelligenceResults[3].value);
    if (intelligenceResults[4].status === "fulfilled") {
      renderList(
        els.pageValueList,
        intelligenceResults[4].value.map((row) => ({ key: row.path, count: row.value_score })),
        "#059669",
      );
    }
    if (intelligenceResults[5].status === "fulfilled") renderHints(els.anomalyList, intelligenceResults[5].value);

    const failed = [...trafficResults, ...intelligenceResults].filter((result) => result.status === "rejected");
    if (failed.length) {
      setStatus(`部分模块加载失败：${failed.length} 个请求未完成`, true);
      return;
    }
    setStatus("智能分析数据已更新");
    setText(els.lastUpdated, `更新时间 ${new Date().toLocaleString("zh-CN")}`);
  } catch (error) {
    setStatus(`加载失败：${error.message}`, true);
  } finally {
    if (els.refreshButton) {
      els.refreshButton.disabled = false;
    }
  }
}

async function init() {
  try {
    await loadSites();
    await loadDashboard();
  } catch (error) {
    setMetricPlaceholders();
    setStatus(`初始化失败：${error.message}`, true);
  }
}

els.siteSelect?.addEventListener("change", () => {
  state.selectedSiteId = Number(els.siteSelect.value);
  loadDashboard();
});

els.refreshButton?.addEventListener("click", loadDashboard);
els.exportButton?.addEventListener("click", () => {
  if (!state.selectedSiteId) {
    setStatus("暂无可导出的站点数据", true);
    return;
  }

  const siteId = encodeURIComponent(state.selectedSiteId);
  window.location.href = `/api/stats/export.csv?site_id=${siteId}&limit=50`;
});
els.logoutButton?.addEventListener("click", async () => {
  await fetch("/logout", { method: "POST" });
  window.location.href = "/login";
});

init();
