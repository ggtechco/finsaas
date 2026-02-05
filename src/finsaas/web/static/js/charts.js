/**
 * Chart.js helpers for FinSaaS dashboard.
 */
const Charts = {
    equityChart: null,
    drawdownChart: null,

    destroyAll() {
        if (this.equityChart) { this.equityChart.destroy(); this.equityChart = null; }
        if (this.drawdownChart) { this.drawdownChart.destroy(); this.drawdownChart = null; }
    },

    _commonOptions(extra) {
        return Object.assign({
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
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
            },
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
        }, extra);
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
};
