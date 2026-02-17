// 应用程序JavaScript

let currentData = {
    strategies: [],
    latestPicks: null,
    historyDates: []
};

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    loadSystemStatus();
    loadStrategies();
    loadLatestPicks();
    loadHistoryDates();

    // 每30秒刷新一次数据
    setInterval(updateTime, 1000);
    setInterval(loadLatestPicks, 30000);
});

// 更新时间
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('currentTime').textContent = timeString;
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            const html = `
                <div class="row">
                    <div class="col-4 stat-card">
                        <div class="stat-value">${data.strategies.total}</div>
                        <div class="stat-label">总策略</div>
                    </div>
                    <div class="col-4 stat-card">
                        <div class="stat-value" style="color: #28a745;">${data.strategies.enabled}</div>
                        <div class="stat-label">已启用</div>
                    </div>
                    <div class="col-4 stat-card">
                        <div class="stat-value" style="color: #dc3545;">${data.strategies.disabled}</div>
                        <div class="stat-label">已禁用</div>
                    </div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-6">
                        <strong>最新选股:</strong><br>
                        ${data.latest_picks.date || '无'}
                    </div>
                    <div class="col-6">
                        <strong>命中数量:</strong><br>
                        ${data.latest_picks.count} 只
                    </div>
                </div>
            `;
            document.getElementById('systemStatus').innerHTML = html;
        }
    } catch (error) {
        console.error('加载系统状态失败:', error);
        document.getElementById('systemStatus').innerHTML = '<p class="text-danger">加载失败</p>';
    }
}

// 加载策略列表
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies');
        const result = await response.json();

        if (result.success) {
            currentData.strategies = result.data;
            renderStrategies(result.data);
        }
    } catch (error) {
        console.error('加载策略失败:', error);
        document.getElementById('strategyList').innerHTML = '<p class="text-danger">加载失败</p>';
    }
}

// 渲染策略列表
function renderStrategies(strategies) {
    const html = strategies.map(strategy => {
        const enabledBadge = strategy.enabled
            ? '<span class="badge badge-enabled">已启用</span>'
            : '<span class="badge badge-disabled">已禁用</span>';

        const paramsHtml = Object.entries(strategy.params).map(([key, value]) => {
            return `<div><strong>${key}:</strong> ${value}</div>`;
        }).join('');

        return `
            <div class="strategy-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="strategy-name">${strategy.name}</div>
                    ${enabledBadge}
                </div>
                <div class="strategy-desc">${strategy.description}</div>
                ${strategy.params && Object.keys(strategy.params).length > 0 ? `
                    <div class="strategy-params">
                        <strong>参数:</strong>
                        ${paramsHtml}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    document.getElementById('strategyList').innerHTML = html || '<p class="text-muted">暂无策略</p>';
}

// 加载最新选股结果
async function loadLatestPicks() {
    try {
        const response = await fetch('/api/picks/latest');
        const result = await response.json();

        if (result.success && result.data) {
            currentData.latestPicks = result.data;
            document.getElementById('pickDate').textContent = result.data.date;
            renderPicks(result.data.stocks);
        } else {
            document.getElementById('pickDate').textContent = '无';
            document.getElementById('pickResults').innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>暂无选股结果</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载选股结果失败:', error);
        document.getElementById('pickResults').innerHTML = '<p class="text-danger">加载失败</p>';
    }
}

// 渲染选股结果
function renderPicks(stocks) {
    if (!stocks || stocks.length === 0) {
        document.getElementById('pickResults').innerHTML = `
            <div class="empty-state">
                <i class="bi bi-search"></i>
                <p>未找到符合条件的股票</p>
            </div>
        `;
        return;
    }

    const html = stocks.map(stock => {
        const changeClass = stock.change_pct >= 0 ? 'price-up' : 'price-down';
        const changeIcon = stock.change_pct >= 0 ? '↑' : '↓';

        const strategies = stock.matched_strategies ? stock.matched_strategies.split(',') : [];

        const strategyBadges = strategies.map(s => {
            const name = s.replace('_', ' ').trim();
            return `<span class="badge bg-primary me-1">${name}</span>`;
        }).join('');

        return `
            <div class="stock-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="stock-name">${stock.name || stock.ts_code}</div>
                        <small class="text-muted">${stock.ts_code}</small>
                    </div>
                    <div class="text-end">
                        <div class="stock-price ${changeClass}">
                            ¥${stock.close.toFixed(2)}
                        </div>
                        <div class="${changeClass}">
                            ${changeIcon} ${Math.abs(stock.change_pct).toFixed(2)}%
                        </div>
                    </div>
                </div>
                <div class="stock-strategies">
                    ${strategyBadges}
                    <span class="badge bg-info">评分: ${stock.avg_score.toFixed(1)}</span>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('pickResults').innerHTML = html;
}

// 加载历史日期
async function loadHistoryDates() {
    try {
        const response = await fetch('/api/picks/dates');
        const result = await response.json();

        if (result.success) {
            currentData.historyDates = result.data;

            const select = document.getElementById('dateSelector');
            select.innerHTML = '<option value="">选择日期...</option>';

            result.data.forEach(date => {
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                select.appendChild(option);
            });

            // 日期选择事件
            select.addEventListener('change', function() {
                if (this.value) {
                    loadPicksByDate(this.value);
                }
            });
        }
    } catch (error) {
        console.error('加载历史日期失败:', error);
    }
}

// 按日期加载选股结果
async function loadPicksByDate(date) {
    try {
        const response = await fetch(`/api/picks/${date}`);
        const result = await response.json();

        if (result.success) {
            renderPicks(result.data.stocks);

            // 更新标题
            document.getElementById('pickDate').textContent = date;

            // 切换到选股结果tab
            // （如果有tab的话）
        } else {
            document.getElementById('pickResults').innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-x-circle"></i>
                    <p>${result.message}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载历史选股失败:', error);
        document.getElementById('pickResults').innerHTML = '<p class="text-danger">加载失败</p>';
    }
}
