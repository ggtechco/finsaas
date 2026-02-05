/**
 * FinSaaS Dashboard - main application logic.
 * All original features preserved: CSV upload, strategy select, params, backtest, optimize.
 */
document.addEventListener('DOMContentLoaded', () => {
    const els = {
        csvFile: document.getElementById('csvFile'),
        csvDrop: document.getElementById('csvDrop'),
        fileInfo: document.getElementById('fileInfo'),
        fileList: document.getElementById('fileList'),
        strategySelect: document.getElementById('strategySelect'),
        paramsContainer: document.getElementById('paramsContainer'),
        symbol: document.getElementById('symbol'),
        capital: document.getElementById('capital'),
        commission: document.getElementById('commission'),
        slippage: document.getElementById('slippage'),
        btnBacktest: document.getElementById('btnBacktest'),
        btnOptimize: document.getElementById('btnOptimize'),
        optMethod: document.getElementById('optMethod'),
        optObjective: document.getElementById('optObjective'),
        spinner: document.getElementById('spinner'),
        results: document.getElementById('results'),
        metricsCards: document.getElementById('metricsCards'),
        tradesTable: document.getElementById('tradesTable'),
        errorAlert: document.getElementById('errorAlert'),
        errorMsg: document.getElementById('errorMsg'),
        optimizeResults: document.getElementById('optimizeResults'),
        optimizeSummary: document.getElementById('optimizeSummary'),
        optimizeTrials: document.getElementById('optimizeTrials'),
        placeholder: document.getElementById('placeholder'),
    };

    let currentFile = null;
    let currentParams = [];

    // --- Init ---
    loadStrategies();
    loadFiles();

    // --- CSV Upload ---
    els.csvDrop.addEventListener('click', () => els.csvFile.click());

    els.csvDrop.addEventListener('dragover', (e) => {
        e.preventDefault();
        els.csvDrop.classList.add('drag-over');
    });
    els.csvDrop.addEventListener('dragleave', () => {
        els.csvDrop.classList.remove('drag-over');
    });
    els.csvDrop.addEventListener('drop', (e) => {
        e.preventDefault();
        els.csvDrop.classList.remove('drag-over');
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });

    els.csvFile.addEventListener('change', () => {
        if (els.csvFile.files.length) uploadFile(els.csvFile.files[0]);
    });

    async function uploadFile(file) {
        try {
            const info = await API.uploadCSV(file);
            currentFile = info.name;
            els.fileInfo.textContent = `${info.name} (${info.bars} bars, ${(info.size / 1024).toFixed(1)} KB)`;
            els.fileInfo.classList.add('visible');
            loadFiles();
        } catch (err) {
            showError(err.message);
        }
    }

    async function loadFiles() {
        try {
            const files = await API.getFiles();
            els.fileList.innerHTML = '';
            files.forEach(f => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'file-item';
                btn.textContent = `${f.name} (${f.bars} bars)`;
                btn.addEventListener('click', () => {
                    currentFile = f.name;
                    els.fileInfo.textContent = `${f.name} (${f.bars} bars)`;
                    els.fileInfo.classList.add('visible');
                    // highlight active
                    els.fileList.querySelectorAll('.file-item').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                });
                els.fileList.appendChild(btn);
            });
        } catch (_) { /* ignore */ }
    }

    // --- Strategies ---
    async function loadStrategies() {
        try {
            const strategies = await API.getStrategies();
            els.strategySelect.innerHTML = '<option value="">-- Select strategy --</option>';
            strategies.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.name;
                opt.textContent = s.name;
                els.strategySelect.appendChild(opt);
            });
        } catch (_) { /* ignore */ }
    }

    els.strategySelect.addEventListener('change', async () => {
        const name = els.strategySelect.value;
        if (!name) { els.paramsContainer.innerHTML = ''; currentParams = []; return; }
        try {
            const info = await API.getStrategyParams(name);
            currentParams = info.params;
            renderParams(info.params);
        } catch (err) {
            showError(err.message);
        }
    });

    function renderParams(params) {
        els.paramsContainer.innerHTML = '';
        if (!params.length) {
            els.paramsContainer.innerHTML = '<p style="color:#64748b;font-size:0.75rem">No parameters</p>';
            return;
        }
        params.forEach(p => {
            const div = document.createElement('div');
            div.style.marginBottom = '0.4rem';

            const label = document.createElement('label');
            label.className = 'form-label';
            label.textContent = p.name;
            if (p.description) label.title = p.description;
            div.appendChild(label);

            let input;
            if (p.type === 'bool') {
                input = document.createElement('input');
                input.type = 'checkbox';
                input.className = 'form-check-input';
                input.style.marginLeft = '0.5rem';
                input.checked = p.default;
                input.dataset.param = p.name;
                input.dataset.ptype = 'bool';
            } else if (p.type === 'enum' && p.choices) {
                input = document.createElement('select');
                input.className = 'form-select';
                p.choices.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c;
                    opt.textContent = c;
                    if (c == p.default) opt.selected = true;
                    input.appendChild(opt);
                });
                input.dataset.param = p.name;
                input.dataset.ptype = 'enum';
            } else {
                input = document.createElement('input');
                input.type = 'number';
                input.className = 'form-control';
                input.value = p.default;
                if (p.type === 'float') input.step = p.step || 0.01;
                else input.step = p.step || 1;
                if (p.min_val != null) input.min = p.min_val;
                if (p.max_val != null) input.max = p.max_val;
                input.dataset.param = p.name;
                input.dataset.ptype = p.type;
            }

            div.appendChild(input);
            els.paramsContainer.appendChild(div);
        });
    }

    function collectParams() {
        const params = {};
        els.paramsContainer.querySelectorAll('[data-param]').forEach(el => {
            const name = el.dataset.param;
            const ptype = el.dataset.ptype;
            if (ptype === 'bool') {
                params[name] = el.checked;
            } else if (ptype === 'int') {
                params[name] = parseInt(el.value, 10);
            } else if (ptype === 'float') {
                params[name] = parseFloat(el.value);
            } else {
                params[name] = el.value;
            }
        });
        return params;
    }

    // --- Backtest ---
    els.btnBacktest.addEventListener('click', async () => {
        if (!currentFile) { showError('Please upload or select a CSV file first'); return; }
        const strategy = els.strategySelect.value;
        if (!strategy) { showError('Please select a strategy'); return; }

        const payload = {
            strategy,
            csv_file: currentFile,
            symbol: els.symbol.value || 'UNKNOWN',
            timeframe: '1h',
            initial_capital: parseFloat(els.capital.value) || 10000,
            commission: parseFloat(els.commission.value) || 0.001,
            slippage: parseFloat(els.slippage.value) || 0.0005,
            parameters: collectParams(),
        };

        hideError();
        els.spinner.classList.add('visible');
        els.results.classList.remove('visible');
        els.optimizeResults.classList.remove('visible');

        try {
            const data = await API.runBacktest(payload);
            renderResults(data, payload.initial_capital);
        } catch (err) {
            showError(err.message);
        } finally {
            els.spinner.classList.remove('visible');
        }
    });

    function renderResults(data, initialCapital) {
        els.placeholder.style.display = 'none';
        els.results.classList.add('visible');

        // Metrics
        const m = data.metrics;
        const returnPct = m.total_return_pct || 0;
        const metrics = [
            { label: 'Total Return', value: `${returnPct.toFixed(2)}%`, cls: returnPct >= 0 ? 'positive' : 'negative', accent: returnPct >= 0 ? 'green' : 'red' },
            { label: 'Final Equity', value: `$${data.final_equity.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`, cls: data.final_equity >= initialCapital ? 'positive' : 'negative', accent: data.final_equity >= initialCapital ? 'green' : 'red' },
            { label: 'Sharpe Ratio', value: (m.sharpe_ratio || 0).toFixed(4), cls: 'neutral', accent: 'blue' },
            { label: 'Max Drawdown', value: `${(m.max_drawdown_pct || 0).toFixed(2)}%`, cls: 'negative', accent: 'red' },
            { label: 'Win Rate', value: `${(m.win_rate || 0).toFixed(1)}%`, cls: 'neutral', accent: 'blue' },
            { label: 'Profit Factor', value: (m.profit_factor || 0).toFixed(2), cls: 'neutral', accent: 'orange' },
            { label: 'Total Trades', value: (m.total_trades || 0).toFixed(0), cls: 'neutral', accent: 'gray' },
            { label: 'Expectancy', value: (m.expectancy || 0).toFixed(2), cls: (m.expectancy || 0) >= 0 ? 'positive' : 'negative', accent: (m.expectancy || 0) >= 0 ? 'green' : 'red' },
        ];

        els.metricsCards.innerHTML = metrics.map(m => `
            <div class="metric-card ${m.accent}">
                <div class="metric-label">${m.label}</div>
                <div class="metric-value ${m.cls}">${m.value}</div>
            </div>
        `).join('');

        // Charts
        if (data.equity_curve.length) {
            Charts.renderEquity('equityChart', data.equity_curve, initialCapital);
            Charts.renderDrawdown('drawdownChart', data.equity_curve);
        }

        // Trades table
        const tbody = els.tradesTable.querySelector('tbody');
        tbody.innerHTML = '';
        data.trades.forEach(t => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${t.entry_time.replace('T', ' ').slice(0, 19)}</td>
                <td>${t.exit_time.replace('T', ' ').slice(0, 19)}</td>
                <td><span class="${t.side === 'long' ? 'badge-long' : 'badge-short'}">${t.side.toUpperCase()}</span></td>
                <td>${t.entry_price.toFixed(2)}</td>
                <td>${t.exit_price.toFixed(2)}</td>
                <td class="${t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}</td>
                <td class="${t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}%</td>
                <td>${t.bars_held}</td>
            `;
            tbody.appendChild(row);
        });

        if (!data.trades.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-trades">No trades executed</td></tr>';
        }
    }

    // --- Optimize ---
    els.btnOptimize.addEventListener('click', async () => {
        if (!currentFile) { showError('Please upload or select a CSV file first'); return; }
        const strategy = els.strategySelect.value;
        if (!strategy) { showError('Please select a strategy'); return; }

        const payload = {
            strategy,
            csv_file: currentFile,
            symbol: els.symbol.value || 'UNKNOWN',
            timeframe: '1h',
            initial_capital: parseFloat(els.capital.value) || 10000,
            method: els.optMethod.value,
            objective: els.optObjective.value,
            parameters: collectParams(),
        };

        hideError();
        els.spinner.classList.add('visible');
        els.results.classList.remove('visible');
        els.optimizeResults.classList.remove('visible');

        try {
            const data = await API.runOptimize(payload);
            renderOptimizeResults(data);
        } catch (err) {
            showError(err.message);
        } finally {
            els.spinner.classList.remove('visible');
        }
    });

    function renderOptimizeResults(data) {
        els.placeholder.style.display = 'none';
        els.optimizeResults.classList.add('visible');

        // Summary
        const bestParams = Object.entries(data.best_params).map(([k, v]) => `<strong>${k}</strong>=${v}`).join(', ');
        els.optimizeSummary.innerHTML = `
            <div class="optimize-summary">
                <p style="margin:0 0 0.4rem"><strong>Method:</strong> ${data.method} &nbsp;|&nbsp; <strong>Objective:</strong> ${data.objective} &nbsp;|&nbsp; <strong>Trials:</strong> ${data.total_trials}</p>
                <p style="margin:0 0 0.4rem"><strong>Best Value:</strong> <span class="pnl-positive" style="font-size:1.1rem">${data.best_value.toFixed(4)}</span></p>
                <p style="margin:0"><strong>Best Parameters:</strong> ${bestParams}</p>
            </div>
        `;

        // Trials table
        const tbody = els.optimizeTrials.querySelector('tbody');
        tbody.innerHTML = '';
        const sorted = [...data.trials].sort((a, b) => b.objective_value - a.objective_value);
        sorted.slice(0, 50).forEach((t, i) => {
            const params = Object.entries(t.parameters).map(([k, v]) => `${k}=${v}`).join(', ');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${t.trial_index}</td>
                <td>${params}</td>
                <td class="pnl-positive">${t.objective_value.toFixed(4)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // --- Helpers ---
    function showError(msg) {
        els.errorMsg.textContent = msg;
        els.errorAlert.classList.add('visible');
    }

    function hideError() {
        els.errorAlert.classList.remove('visible');
    }
});
