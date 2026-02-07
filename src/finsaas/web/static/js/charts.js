/**
 * Chart.js helpers for FinSaaS dashboard.
 * Enhanced: P&L distribution histogram, zoom/pan plugin integration,
 * crosshair plugin, synchronized tooltips, trade markers, annotations.
 */

/* ── Crosshair Plugin ── */
const crosshairPlugin = {
    id: 'crosshair',
    _activeChartId: null,
    _activeIndex: null,

    afterEvent(chart, args) {
        const evt = args.event;
        if (evt.type === 'mousemove' && chart.getActiveElements().length > 0) {
            crosshairPlugin._activeChartId = chart.id;
            const el = chart.getActiveElements()[0];
            crosshairPlugin._activeIndex = el.index;
            // Sync sibling charts
            Charts._syncCharts(chart.id, el.index);
        }
        if (evt.type === 'mouseout') {
            crosshairPlugin._activeChartId = null;
            crosshairPlugin._activeIndex = null;
            Charts._clearSync(chart.id);
        }
    },

    afterDraw(chart) {
        const idx = crosshairPlugin._activeIndex;
        if (idx == null) return;
        // Only draw on timeseries charts (equity & drawdown)
        if (!Charts._isTimeseriesChart(chart)) return;

        const meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data || !meta.data[idx]) return;

        const x = meta.data[idx].x;
        const { top, bottom } = chart.chartArea;
        const ctx = chart.ctx;

        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(100, 116, 139, 0.5)';
        ctx.moveTo(x, top);
        ctx.lineTo(x, bottom);
        ctx.stroke();
        ctx.restore();
    },
};

/* ── Annotation Plugin (max DD, best/worst trade) ── */
const annotationPlugin = {
    id: 'tradeAnnotations',
    _annotations: [],

    afterDatasetsDraw(chart) {
        if (!Charts._isTimeseriesChart(chart) || chart !== Charts.equityChart) return;
        const annotations = annotationPlugin._annotations;
        if (!annotations.length) return;

        const meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data) return;
        const ctx = chart.ctx;

        annotations.forEach(ann => {
            const idx = ann.index;
            if (idx < 0 || idx >= meta.data.length) return;
            const point = meta.data[idx];
            const x = point.x;
            const y = point.y;

            ctx.save();
            ctx.font = 'bold 10px Inter, sans-serif';
            ctx.textAlign = 'center';

            if (ann.type === 'maxdd') {
                // Red diamond marker
                ctx.fillStyle = '#ef4444';
                ctx.beginPath();
                ctx.moveTo(x, y - 7);
                ctx.lineTo(x + 5, y);
                ctx.lineTo(x, y + 7);
                ctx.lineTo(x - 5, y);
                ctx.closePath();
                ctx.fill();
                // Label
                ctx.fillStyle = '#ef4444';
                ctx.fillText('Max DD', x, y - 12);
            } else if (ann.type === 'best') {
                // Gold star
                Charts._drawStar(ctx, x, y - 8, 5, 5, 2.5);
                ctx.fillStyle = '#f59e0b';
                ctx.fill();
                ctx.fillText('Best', x, y - 18);
            } else if (ann.type === 'worst') {
                // Dark red star
                Charts._drawStar(ctx, x, y + 8, 5, 5, 2.5);
                ctx.fillStyle = '#991b1b';
                ctx.fill();
                ctx.fillText('Worst', x, y + 22);
            }

            ctx.restore();
        });
    },
};

// Register plugins globally
if (typeof Chart !== 'undefined') {
    Chart.register(crosshairPlugin, annotationPlugin);
}

const Charts = {
    equityChart: null,
    drawdownChart: null,
    pnlChart: null,

    destroyAll() {
        if (this.equityChart) { this.equityChart.destroy(); this.equityChart = null; }
        if (this.drawdownChart) { this.drawdownChart.destroy(); this.drawdownChart = null; }
        if (this.pnlChart) { this.pnlChart.destroy(); this.pnlChart = null; }
        annotationPlugin._annotations = [];
    },

    _isTimeseriesChart(chart) {
        return chart === this.equityChart || chart === this.drawdownChart;
    },

    _syncCharts(sourceId, index) {
        const charts = [this.equityChart, this.drawdownChart].filter(Boolean);
        charts.forEach(c => {
            if (c.id === sourceId) return;
            const meta = c.getDatasetMeta(0);
            if (!meta || !meta.data || !meta.data[index]) return;
            c.tooltip.setActiveElements(
                [{ datasetIndex: 0, index }],
                { x: meta.data[index].x, y: meta.data[index].y }
            );
            c.setActiveElements([{ datasetIndex: 0, index }]);
            c.update('none');
        });
    },

    _clearSync(sourceId) {
        const charts = [this.equityChart, this.drawdownChart].filter(Boolean);
        charts.forEach(c => {
            if (c.id === sourceId) return;
            c.tooltip.setActiveElements([], {});
            c.setActiveElements([]);
            c.update('none');
        });
    },

    _drawStar(ctx, cx, cy, spikes, outerR, innerR) {
        let rot = (Math.PI / 2) * 3;
        const step = Math.PI / spikes;
        ctx.beginPath();
        ctx.moveTo(cx, cy - outerR);
        for (let i = 0; i < spikes; i++) {
            ctx.lineTo(cx + Math.cos(rot) * outerR, cy + Math.sin(rot) * outerR);
            rot += step;
            ctx.lineTo(cx + Math.cos(rot) * innerR, cy + Math.sin(rot) * innerR);
            rot += step;
        }
        ctx.lineTo(cx, cy - outerR);
        ctx.closePath();
    },

    _zoomPanConfig() {
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
            if (extra.plugins) {
                Object.assign(base.plugins, extra.plugins);
            }
            if (extra.scales) {
                Object.assign(base.scales, extra.scales);
            }
            for (const key of Object.keys(extra)) {
                if (key !== 'plugins' && key !== 'scales') {
                    base[key] = extra[key];
                }
            }
        }

        return base;
    },

    renderEquity(canvasId, equityCurve, initialCapital, trades) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const labels = equityCurve.map(p => p.timestamp.replace('T', ' ').slice(0, 16));
        const data = equityCurve.map(p => p.equity);

        if (this.equityChart) this.equityChart.destroy();

        // Gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 280);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.15)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        // Build trade marker datasets
        const datasets = [
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
        ];

        // Trade markers: entries (green triangle up) and exits (red triangle down)
        if (trades && trades.length > 0) {
            const tsMap = {};
            equityCurve.forEach((p, i) => {
                const key = p.timestamp.replace('T', ' ').slice(0, 16);
                tsMap[key] = i;
            });

            const entryData = new Array(data.length).fill(null);
            const exitData = new Array(data.length).fill(null);

            trades.forEach(t => {
                const entryKey = t.entry_time.replace('T', ' ').slice(0, 16);
                const exitKey = t.exit_time.replace('T', ' ').slice(0, 16);
                const ei = tsMap[entryKey];
                const xi = tsMap[exitKey];
                if (ei != null) entryData[ei] = data[ei];
                if (xi != null) exitData[xi] = data[xi];
            });

            datasets.push({
                label: 'Entry',
                data: entryData,
                pointStyle: 'triangle',
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#10b981',
                pointBorderColor: '#10b981',
                borderColor: 'transparent',
                borderWidth: 0,
                showLine: false,
                fill: false,
            });

            datasets.push({
                label: 'Exit',
                data: exitData,
                pointStyle: 'triangle',
                pointRotation: 180,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#ef4444',
                pointBorderColor: '#ef4444',
                borderColor: 'transparent',
                borderWidth: 0,
                showLine: false,
                fill: false,
            });

            // Build annotations for max DD, best/worst trade
            this._buildAnnotations(equityCurve, trades, tsMap);
        }

        this.equityChart = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: this._commonOptions({
                plugins: {
                    tooltip: {
                        callbacks: {
                            label(tooltipItem) {
                                if (tooltipItem.raw == null) return null;
                                const dsLabel = tooltipItem.dataset.label;
                                if (dsLabel === 'Entry') return `Entry: $${tooltipItem.raw.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                                if (dsLabel === 'Exit') return `Exit: $${tooltipItem.raw.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                                return `${dsLabel}: $${tooltipItem.raw.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                            },
                        },
                        filter(tooltipItem) {
                            return tooltipItem.raw != null;
                        },
                    },
                },
            }),
        });
    },

    _buildAnnotations(equityCurve, trades, tsMap) {
        const annotations = [];

        // Max drawdown point
        let maxDdIdx = 0;
        let maxDd = 0;
        equityCurve.forEach((p, i) => {
            if (p.drawdown > maxDd) {
                maxDd = p.drawdown;
                maxDdIdx = i;
            }
        });
        if (maxDd > 0) {
            annotations.push({ type: 'maxdd', index: maxDdIdx });
        }

        // Best and worst trade by pnl
        if (trades.length > 0) {
            let bestTrade = trades[0];
            let worstTrade = trades[0];
            trades.forEach(t => {
                if (t.pnl > bestTrade.pnl) bestTrade = t;
                if (t.pnl < worstTrade.pnl) worstTrade = t;
            });

            const bestKey = bestTrade.exit_time.replace('T', ' ').slice(0, 16);
            const worstKey = worstTrade.exit_time.replace('T', ' ').slice(0, 16);
            const bestIdx = tsMap[bestKey];
            const worstIdx = tsMap[worstKey];

            if (bestIdx != null) annotations.push({ type: 'best', index: bestIdx });
            if (worstIdx != null && worstIdx !== bestIdx) annotations.push({ type: 'worst', index: worstIdx });
        }

        annotationPlugin._annotations = annotations;
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

        const binCount = Math.min(20, Math.max(5, Math.ceil(Math.sqrt(trades.length))));
        const range = max - min || 1;
        const binWidth = range / binCount;

        const bins = [];
        const labels = [];
        for (let i = 0; i < binCount; i++) {
            const lo = min + i * binWidth;
            bins.push(0);
            labels.push(lo.toFixed(0));
        }

        pnls.forEach(pnl => {
            let idx = Math.floor((pnl - min) / binWidth);
            if (idx >= binCount) idx = binCount - 1;
            if (idx < 0) idx = 0;
            bins[idx]++;
        });

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
