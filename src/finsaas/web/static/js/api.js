/**
 * FinSaaS API client - fetch() wrappers for backend endpoints.
 */
const API = {
    async getStrategies() {
        const res = await fetch('/api/strategies');
        return res.json();
    },

    async getStrategyParams(name) {
        const res = await fetch(`/api/strategies/${name}/params`);
        return res.json();
    },

    async uploadCSV(file) {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch('/api/data/upload', { method: 'POST', body: form });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }
        return res.json();
    },

    async getFiles() {
        const res = await fetch('/api/data/files');
        return res.json();
    },

    async runBacktest(payload) {
        const res = await fetch('/api/backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Backtest failed');
        }
        return res.json();
    },

    async runOptimize(payload) {
        const res = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Optimization failed');
        }
        return res.json();
    },
};
