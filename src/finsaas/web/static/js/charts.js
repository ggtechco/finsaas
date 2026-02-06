/**
 * Chart.js helpers for FinSaaS dashboard.
 * Enhanced: P&L distribution histogram, zoom/pan plugin integration.
 */
const Charts = {
    equityChart: null,
    drawdownChart: null,
    pnlChart: null,

    destroyAll() {
        if (this.equityChart) { this.equityChart.destroy(); this.equityChart = null; }
        if (this.drawdownChart) { this.drawdownChart.destroy(); this.drawdownChart = null; }
        if (this.pnlChart) { this.pnlChart.destroy(); this.pnlChart = null; }
    },

    _zoomPanConfig() {
        // Only enable if plugin is loaded
        if (typeof ChartZoom === 'undefined' && typeof Chart !== 'undefined' && !Chart.registry.plugins.get('zoom')) {
            return {};
        }
        return {
            zoom: {
                zoom: {
                    wheel: { enabled: true },
                    pinch: { enabled: true },
                    mode: 'x',
                },
                pan: {
                    enabled: true,
                    mode: 'x',
                },
                limits: {
                    x: { minRange: 5 },
                },
            },
        };
    },

    _commonOptions(extra) {
        const zoomConfig = this._zoomPanConfig();
        const base = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: Object.assign({
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 16,
                        font: { family: 'Inter', size: 11, weight: '500' },
                        color: '#64748b',
                    },
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#0f172a',
                    titleFont: { family: 'Inter', size: 12, weight: '600' },
                    bodyFont: { family: 'Inter', size: 11 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: true,
                    boxPadding: 4,
                },
            }, zoomConfig),
            scales: {
                x: {
                    display: true,
                    ticks: {
                        maxTicksLimit: 10,
                        maxRotation: 0,
                        font: { family: 'Inter', size: 10 },
                        color: '#94a3b8',
                    },
                    grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                },
                y: {
                    display: true,
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#94a3b8',
                    },
                    grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                },
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
        };

        if (extra) {
            // Deep merge plugins and scales
            if (extra.plugins) {
                Object.assign(base.plugins, extra.plugins);
            }
            if (extra.scales) {
                Object.assign(base.scales, extra.scales);
            }
            // Merge other top-level keys
            for (const key of Object.keys(extra)) {
                if (key !== 'plugins' && key !== 'scales') {
                    base[key] = extra[key];
                }
            }
        }

        return base;
    },

    renderEquity(canvasId, equityCurve, initialCapital) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const labels = equityCurve.map(p => p.timestamp.replace('T', ' ').slice(0, 16));
        const data = equityCurve.map(p => p.equity);

        if (this.equityChart) this.equityChart.destroy();

        // Gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 280);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.15)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        this.equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Equity',
                        data,
                        borderColor: '#3b82f6',
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#3b82f6',
                        borderWidth: 2.5,
                    },
                    {
                        label: 'Initial Capital',
                        data: Array(data.length).fill(initialCapital),
                        borderColor: '#94a3b8',
                        borderDash: [6, 4],
                        pointRadius: 0,
                        borderWidth: 1,
                        fill: false,
                    },
                ],
            },
            options: this._commonOptions(),
        });
    },

    renderDrawdown(canvasId, equityCurve) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const labels = equityCurve.map(p => p.timestamp.replace('T', ' ').slice(0, 16));
        const data = equityCurve.map(p => -(p.drawdown * 100));

        if (this.drawdownChart) this.drawdownChart.destroy();

        const gradient = ctx.createLinearGradient(0, 0, 0, 180);
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.0)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0.18)');

        this.drawdownChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Drawdown %',
                    data,
                    borderColor: '#ef4444',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#ef4444',
                    borderWidth: 2,
                }],
            },
            options: this._commonOptions({
                scales: {
                    x: {
                        display: true,
                        ticks: {
                            maxTicksLimit: 10,
                            maxRotation: 0,
                            font: { family: 'Inter', size: 10 },
                            color: '#94a3b8',
                        },
                        grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                    },
                    y: {
                        display: true,
                        max: 0,
                        ticks: {
                            font: { family: 'Inter', size: 10 },
                            color: '#94a3b8',
                        },
                        grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                    },
                },
            }),
        });
    },

    renderPnlDistribution(canvasId, trades) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        if (this.pnlChart) this.pnlChart.destroy();

        const pnls = trades.map(t => t.pnl);
        const min = Math.min(...pnls);
        const max = Math.max(...pnls);

        // Create histogram bins
        const binCount = Math.min(20, Math.max(5, Math.ceil(Math.sqrt(trades.length))));
        const range = max - min || 1;
        const binWidth = range / binCount;

        const bins = [];
        const labels = [];
        for (let i = 0; i < binCount; i++) {
            const lo = min + i * binWidth;
            const hi = lo + binWidth;
            bins.push(0);
            labels.push(lo.toFixed(0));
        }

        pnls.forEach(pnl => {
            let idx = Math.floor((pnl - min) / binWidth);
            if (idx >= binCount) idx = binCount - 1;
            if (idx < 0) idx = 0;
            bins[idx]++;
        });

        // Color each bin based on whether it's positive or negative
        const colors = labels.map(l => parseFloat(l) >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)');
        const borderColors = labels.map(l => parseFloat(l) >= 0 ? '#10b981' : '#ef4444');

        this.pnlChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Trade Count',
                    data: bins,
                    backgroundColor: colors,
                    borderColor: borderColors,
                    borderWidth: 1,
                    borderRadius: 3,
                }],
            },
            options: this._commonOptions({
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                const idx = items[0].dataIndex;
                                const lo = min + idx * binWidth;
                                const hi = lo + binWidth;
                                return `P&L: ${lo.toFixed(2)} to ${hi.toFixed(2)}`;
                            },
                            label: (item) => `${item.raw} trade${item.raw !== 1 ? 's' : ''}`,
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: 'P&L ($)', font: { family: 'Inter', size: 10 }, color: '#94a3b8' },
                        ticks: {
                            maxTicksLimit: 8,
                            font: { family: 'Inter', size: 10 },
                            color: '#94a3b8',
                        },
                        grid: { display: false },
                    },
                    y: {
                        display: true,
                        title: { display: true, text: 'Count', font: { family: 'Inter', size: 10 }, color: '#94a3b8' },
                        ticks: {
                            stepSize: 1,
                            font: { family: 'Inter', size: 10 },
                            color: '#94a3b8',
                        },
                        grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                    },
                },
            }),
        });
    },
};
