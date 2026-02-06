/**
 * FinSaaS Dashboard - main application logic.
 * All original features preserved: CSV upload, strategy select, params, backtest, optimize.
 * Enhanced: toast, step progress, loading animation, metric icons, sortable trades,
 * trade summary, expandable metrics, data preview, export, keyboard shortcuts, mobile sidebar.
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
        loadingText: document.getElementById('loadingText'),
        loadingSubtext: document.getElementById('loadingSubtext'),
        results: document.getElementById('results'),
        metricsCards: document.getElementById('metricsCards'),
        metricsToggle: document.getElementById('metricsToggle'),
        metricsSecondary: document.getElementById('metricsSecondary'),
        tradesTable: document.getElementById('tradesTable'),
        tradeSummary: document.getElementById('tradeSummary'),
        errorAlert: document.getElementById('errorAlert'),
        errorMsg: document.getElementById('errorMsg'),
        optimizeResults: document.getElementById('optimizeResults'),
        optimizeSummary: document.getElementById('optimizeSummary'),
        optimizeTrials: document.getElementById('optimizeTrials'),
        placeholder: document.getElementById('placeholder'),
        toastContainer: document.getElementById('toastContainer'),
        stepBarFill: document.getElementById('stepBarFill'),
        dataPreview: document.getElementById('dataPreview'),
        previewBadge: document.getElementById('previewBadge'),
        previewClose: document.getElementById('previewClose'),
        previewTable: document.getElementById('previewTable'),
        sidebarToggle: document.getElementById('sidebarToggle'),
        sidebar: document.getElementById('sidebar'),
        sidebarBackdrop: document.getElementById('sidebarBackdrop'),
        exportCSV: document.getElementById('exportCSV'),
        exportJSON: document.getElementById('exportJSON'),
        exportPNG: document.getElementById('exportPNG'),
        resetEquityZoom: document.getElementById('resetEquityZoom'),
        resetDrawdownZoom: document.getElementById('resetDrawdownZoom'),
        resetPnlZoom: document.getElementById('resetPnlZoom'),
    };

    let currentFile = null;
    let currentParams = [];
    let lastBacktestData = null;
    let lastInitialCapital = 10000;

    // Trade sort state
    let tradesData = [];
    let sortCol = null;
    let sortAsc = true;

    // Step progress state
    const steps = { data: false, strategy: false, params: false, config: true, run: false };

    // Metric icon mapping
    const metricIcons = {
        'Total Return': 'percent',
        'Final Equity': 'wallet',
        'Sharpe Ratio': 'gauge',
        'Max Drawdown': 'arrow-down-right',
        'Win Rate': 'target',
        'Profit Factor': 'scale',
        'Total Trades': 'repeat',
        'Expectancy': 'calculator',
        'Sortino Ratio': 'shield',
        'Calmar Ratio': 'mountain',
        'Winning Trades': 'trophy',
        'Losing Trades': 'x-circle',
        'Avg Win': 'trending-up',
        'Avg Loss': 'trending-down',
        'Largest Win': 'arrow-up-circle',
        'Largest Loss': 'arrow-down-circle',
        'Avg Bars Held': 'clock',
        'Total Commission': 'coins',
        'Recovery Factor': 'refresh-cw',
        'Total Return ($)': 'dollar-sign',
    };

    // Loading animation
    let loadingInterval = null;

    // --- Init ---
    loadStrategies();
    loadFiles();

    // --- Toast System ---
    function showToast(msg, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = msg;
        els.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // --- Step Progress ---
    function updateStepProgress() {
        const stepKeys = ['data', 'strategy', 'params', 'config', 'run'];
        const dots = document.querySelectorAll('.step-dot');
        let completedCount = 0;
        let lastCompleted = -1;

        stepKeys.forEach((key, i) => {
            dots[i].classList.remove('completed', 'active');
            if (steps[key]) {
                dots[i].classList.add('completed');
                completedCount++;
                lastCompleted = i;
            }
        });

        // Mark next uncompleted as active
        const nextStep = stepKeys.findIndex(k => !steps[k]);
        if (nextStep >= 0 && dots[nextStep]) {
            dots[nextStep].classList.add('active');
        }

        const pct = (completedCount / stepKeys.length) * 100;
        els.stepBarFill.style.width = pct + '%';
    }

    // --- Loading Animation ---
    function startLoadingAnimation(type) {
        const messages = type === 'optimize'
            ? ['Initializing optimizer...', 'Evaluating parameter space...', 'Running trials...', 'Computing objectives...', 'Ranking results...']
            : ['Loading data...', 'Initializing strategy...', 'Executing bar-by-bar...', 'Computing metrics...', 'Generating equity curve...'];

        let idx = 0;
        els.loadingText.textContent = messages[0];
        els.loadingSubtext.textContent = '';

        loadingInterval = setInterval(() => {
            idx++;
            if (idx < messages.length) {
                els.loadingSubtext.textContent = messages[idx];
            }
        }, 1500);
    }

    function stopLoadingAnimation() {
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
    }

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
            steps.data = true;
            updateStepProgress();
            showToast(`Uploaded ${info.name} (${info.bars} bars)`, 'success');
            loadFiles();
            showDataPreview(info.name);
        } catch (err) {
            showError(err.message);
            showToast('Upload failed: ' + err.message, 'error');
        }
    }

    async function loadFiles() {
        try {
            const files = await API.getFiles();
            els.fileList.innerHTML = '';
            files.forEach(f => {
                const isSample = f.name.startsWith('sample_');
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'file-item';
                btn.textContent = isSample
                    ? `${f.name} (${f.bars} bars) (Sample)`
                    : `${f.name} (${f.bars} bars)`;
                btn.addEventListener('click', () => {
                    currentFile = f.name;
                    els.fileInfo.textContent = `${f.name} (${f.bars} bars)`;
                    els.fileInfo.classList.add('visible');
                    els.fileList.querySelectorAll('.file-item').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    steps.data = true;
                    updateStepProgress();
                    showDataPreview(f.name);
                });
                els.fileList.appendChild(btn);
                if (isSample && !currentFile) {
                    currentFile = f.name;
                    els.fileInfo.textContent = `${f.name} (${f.bars} bars)`;
                    els.fileInfo.classList.add('visible');
                    btn.classList.add('active');
                    steps.data = true;
                    updateStepProgress();
                }
            });
        } catch (_) { /* ignore */ }
    }

    // --- Data Preview ---
    async function showDataPreview(filename) {
        try {
            const data = await API.getDataPreview(filename);
            els.previewBadge.textContent = `${filename} — ${data.total_bars} bars total (showing first ${data.rows.length})`;
            const thead = els.previewTable.querySelector('thead');
            const tbody = els.previewTable.querySelector('tbody');
            thead.innerHTML = '<tr>' + data.headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            tbody.innerHTML = data.rows.map(row =>
                '<tr>' + row.map(cell => `<td>${cell}</td>`).join('') + '</tr>'
            ).join('');
            els.dataPreview.classList.add('visible');
        } catch (_) {
            // Preview not available - silently ignore
        }
    }

    els.previewClose.addEventListener('click', () => {
        els.dataPreview.classList.remove('visible');
    });

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
        if (!name) { els.paramsContainer.innerHTML = ''; currentParams = []; steps.strategy = false; updateStepProgress(); return; }
        try {
            const info = await API.getStrategyParams(name);
            currentParams = info.params;
            renderParams(info.params);
            steps.strategy = true;
            steps.params = true;
            updateStepProgress();
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
    els.btnBacktest.addEventListener('click', runBacktest);

    async function runBacktest() {
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
        startLoadingAnimation('backtest');
        closeSidebarOnMobile();

        try {
            const data = await API.runBacktest(payload);
            lastBacktestData = data;
            lastInitialCapital = payload.initial_capital;
            renderResults(data, payload.initial_capital);
            steps.run = true;
            updateStepProgress();
            showToast(`Backtest complete — ${data.total_trades} trades`, 'success');
        } catch (err) {
            showError(err.message);
            showToast('Backtest failed', 'error');
        } finally {
            stopLoadingAnimation();
            els.spinner.classList.remove('visible');
        }
    }

    function renderResults(data, initialCapital) {
        els.placeholder.style.display = 'none';
        els.results.classList.add('visible');

        // Primary Metrics (8)
        const m = data.metrics;
        const returnPct = m.total_return_pct || 0;
        const primaryMetrics = [
            { label: 'Total Return', value: `${returnPct.toFixed(2)}%`, cls: returnPct >= 0 ? 'positive' : 'negative', accent: returnPct >= 0 ? 'green' : 'red' },
            { label: 'Final Equity', value: `$${data.final_equity.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`, cls: data.final_equity >= initialCapital ? 'positive' : 'negative', accent: data.final_equity >= initialCapital ? 'green' : 'red' },
            { label: 'Sharpe Ratio', value: (m.sharpe_ratio || 0).toFixed(4), cls: 'neutral', accent: 'blue' },
            { label: 'Max Drawdown', value: `${(m.max_drawdown_pct || 0).toFixed(2)}%`, cls: 'negative', accent: 'red' },
            { label: 'Win Rate', value: `${(m.win_rate || 0).toFixed(1)}%`, cls: 'neutral', accent: 'blue' },
            { label: 'Profit Factor', value: (m.profit_factor || 0).toFixed(2), cls: 'neutral', accent: 'orange' },
            { label: 'Total Trades', value: (m.total_trades || 0).toFixed(0), cls: 'neutral', accent: 'gray' },
            { label: 'Expectancy', value: (m.expectancy || 0).toFixed(2), cls: (m.expectancy || 0) >= 0 ? 'positive' : 'negative', accent: (m.expectancy || 0) >= 0 ? 'green' : 'red' },
        ];

        els.metricsCards.innerHTML = primaryMetrics.map(met => `
            <div class="metric-card ${met.accent}">
                <div class="metric-icon"><i data-lucide="${metricIcons[met.label] || 'activity'}"></i></div>
                <div class="metric-label">${met.label}</div>
                <div class="metric-value ${met.cls}">${met.value}</div>
            </div>
        `).join('');

        // Secondary Metrics (expandable)
        const secondaryMetrics = [
            { label: 'Sortino Ratio', value: (m.sortino_ratio || 0).toFixed(4), cls: 'neutral', accent: 'blue' },
            { label: 'Calmar Ratio', value: (m.calmar_ratio || 0).toFixed(4), cls: 'neutral', accent: 'blue' },
            { label: 'Winning Trades', value: (m.winning_trades || 0).toFixed(0), cls: 'neutral', accent: 'green' },
            { label: 'Losing Trades', value: (m.losing_trades || 0).toFixed(0), cls: 'neutral', accent: 'red' },
            { label: 'Avg Win', value: `$${(m.avg_win || 0).toFixed(2)}`, cls: 'positive', accent: 'green' },
            { label: 'Avg Loss', value: `$${(m.avg_loss || 0).toFixed(2)}`, cls: 'negative', accent: 'red' },
            { label: 'Largest Win', value: `$${(m.largest_win || 0).toFixed(2)}`, cls: 'positive', accent: 'green' },
            { label: 'Largest Loss', value: `$${(m.largest_loss || 0).toFixed(2)}`, cls: 'negative', accent: 'red' },
            { label: 'Avg Bars Held', value: (m.avg_bars_held || 0).toFixed(1), cls: 'neutral', accent: 'gray' },
            { label: 'Total Commission', value: `$${(m.total_commission || 0).toFixed(2)}`, cls: 'neutral', accent: 'orange' },
            { label: 'Recovery Factor', value: (m.recovery_factor || 0).toFixed(2), cls: 'neutral', accent: 'blue' },
            { label: 'Total Return ($)', value: `$${(m.total_return_abs || 0).toFixed(2)}`, cls: (m.total_return_abs || 0) >= 0 ? 'positive' : 'negative', accent: (m.total_return_abs || 0) >= 0 ? 'green' : 'red' },
        ];

        if (secondaryMetrics.some(met => met.value !== '$0.00' && met.value !== '0.0000' && met.value !== '0' && met.value !== '0.0')) {
            els.metricsSecondary.innerHTML = secondaryMetrics.map(met => `
                <div class="metric-card ${met.accent}">
                    <div class="metric-icon"><i data-lucide="${metricIcons[met.label] || 'activity'}"></i></div>
                    <div class="metric-label">${met.label}</div>
                    <div class="metric-value ${met.cls}">${met.value}</div>
                </div>
            `).join('');
            els.metricsToggle.style.display = 'block';
        } else {
            els.metricsToggle.style.display = 'none';
        }

        // Charts
        if (data.equity_curve.length) {
            Charts.renderEquity('equityChart', data.equity_curve, initialCapital);
            Charts.renderDrawdown('drawdownChart', data.equity_curve);
        }

        // P&L Distribution
        if (data.trades.length) {
            Charts.renderPnlDistribution('pnlChart', data.trades);
        }

        // Store trades for sorting
        tradesData = data.trades.slice();
        sortCol = null;
        sortAsc = true;
        renderTradesTable(tradesData);
        renderTradeSummary(data.trades);

        // Re-render Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // --- Metrics Toggle ---
    els.metricsToggle.addEventListener('click', () => {
        const sec = els.metricsSecondary;
        const isVisible = sec.classList.contains('visible');
        if (isVisible) {
            sec.classList.remove('visible');
            els.metricsToggle.innerHTML = '<i data-lucide="chevrons-down" class="icon-btn"></i> Show all metrics';
        } else {
            sec.classList.add('visible');
            els.metricsToggle.innerHTML = '<i data-lucide="chevrons-up" class="icon-btn"></i> Show fewer metrics';
        }
        if (typeof lucide !== 'undefined') lucide.createIcons();
    });

    // --- Sortable Trades Table ---
    function renderTradesTable(trades) {
        const tbody = els.tradesTable.querySelector('tbody');
        tbody.innerHTML = '';

        if (!trades.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-trades">No trades executed</td></tr>';
            return;
        }

        trades.forEach(t => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td data-label="Entry">${t.entry_time.replace('T', ' ').slice(0, 19)}</td>
                <td data-label="Exit">${t.exit_time.replace('T', ' ').slice(0, 19)}</td>
                <td data-label="Side"><span class="${t.side === 'long' ? 'badge-long' : 'badge-short'}">${t.side.toUpperCase()}</span></td>
                <td data-label="Entry $">${t.entry_price.toFixed(2)}</td>
                <td data-label="Exit $">${t.exit_price.toFixed(2)}</td>
                <td data-label="P&L" class="${t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}</td>
                <td data-label="P&L%" class="${t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}%</td>
                <td data-label="Bars">${t.bars_held}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Trade table header sort
    els.tradesTable.querySelector('thead').addEventListener('click', (e) => {
        const th = e.target.closest('th[data-sort]');
        if (!th || !tradesData.length) return;

        const col = th.dataset.sort;
        if (sortCol === col) {
            sortAsc = !sortAsc;
        } else {
            sortCol = col;
            sortAsc = true;
        }

        // Update active header
        els.tradesTable.querySelectorAll('th').forEach(h => h.classList.remove('sort-active'));
        th.classList.add('sort-active');

        const sorted = [...tradesData].sort((a, b) => {
            let va = a[col], vb = b[col];
            if (typeof va === 'string') {
                return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
            }
            return sortAsc ? va - vb : vb - va;
        });

        renderTradesTable(sorted);
    });

    // --- Trade Summary ---
    function renderTradeSummary(trades) {
        if (!trades.length) {
            els.tradeSummary.classList.remove('visible');
            return;
        }

        const longCount = trades.filter(t => t.side === 'long').length;
        const shortCount = trades.filter(t => t.side === 'short').length;
        const avgPnl = trades.reduce((s, t) => s + t.pnl, 0) / trades.length;
        const best = Math.max(...trades.map(t => t.pnl));
        const worst = Math.min(...trades.map(t => t.pnl));
        const avgBars = trades.reduce((s, t) => s + t.bars_held, 0) / trades.length;

        els.tradeSummary.innerHTML = `
            <div class="trade-stat"><span class="trade-stat-label">Avg P&L</span><span class="trade-stat-value ${avgPnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${avgPnl >= 0 ? '+' : ''}${avgPnl.toFixed(2)}</span></div>
            <div class="trade-stat"><span class="trade-stat-label">Best Trade</span><span class="trade-stat-value pnl-positive">+${best.toFixed(2)}</span></div>
            <div class="trade-stat"><span class="trade-stat-label">Worst Trade</span><span class="trade-stat-value pnl-negative">${worst.toFixed(2)}</span></div>
            <div class="trade-stat"><span class="trade-stat-label">Long / Short</span><span class="trade-stat-value">${longCount} / ${shortCount}</span></div>
            <div class="trade-stat"><span class="trade-stat-label">Avg Bars</span><span class="trade-stat-value">${avgBars.toFixed(1)}</span></div>
        `;
        els.tradeSummary.classList.add('visible');
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
        startLoadingAnimation('optimize');
        closeSidebarOnMobile();

        try {
            const data = await API.runOptimize(payload);
            renderOptimizeResults(data);
            showToast(`Optimization complete — ${data.total_trials} trials`, 'success');
        } catch (err) {
            showError(err.message);
            showToast('Optimization failed', 'error');
        } finally {
            stopLoadingAnimation();
            els.spinner.classList.remove('visible');
        }
    });

    function renderOptimizeResults(data) {
        els.placeholder.style.display = 'none';
        els.optimizeResults.classList.add('visible');

        const bestParams = Object.entries(data.best_params).map(([k, v]) => `<strong>${k}</strong>=${v}`).join(', ');
        els.optimizeSummary.innerHTML = `
            <div class="optimize-summary">
                <p style="margin:0 0 0.4rem"><strong>Method:</strong> ${data.method} &nbsp;|&nbsp; <strong>Objective:</strong> ${data.objective} &nbsp;|&nbsp; <strong>Trials:</strong> ${data.total_trials}</p>
                <p style="margin:0 0 0.4rem"><strong>Best Value:</strong> <span class="pnl-positive" style="font-size:1.1rem">${data.best_value.toFixed(4)}</span></p>
                <p style="margin:0"><strong>Best Parameters:</strong> ${bestParams}</p>
            </div>
        `;

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

    // --- Export ---
    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    els.exportCSV.addEventListener('click', () => {
        if (!tradesData.length) { showToast('No trades to export', 'info'); return; }
        const headers = ['Entry Time', 'Exit Time', 'Side', 'Entry Price', 'Exit Price', 'P&L', 'P&L%', 'Bars Held'];
        const rows = tradesData.map(t => [
            t.entry_time, t.exit_time, t.side,
            t.entry_price.toFixed(2), t.exit_price.toFixed(2),
            t.pnl.toFixed(2), t.pnl_pct.toFixed(2), t.bars_held,
        ]);
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        downloadFile(csv, 'trades.csv', 'text/csv');
        showToast('Trades exported as CSV', 'success');
    });

    els.exportJSON.addEventListener('click', () => {
        if (!lastBacktestData) { showToast('No metrics to export', 'info'); return; }
        const json = JSON.stringify(lastBacktestData.metrics, null, 2);
        downloadFile(json, 'metrics.json', 'application/json');
        showToast('Metrics exported as JSON', 'success');
    });

    els.exportPNG.addEventListener('click', () => {
        const canvas = document.getElementById('equityChart');
        if (!canvas) { showToast('No chart to export', 'info'); return; }
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = 'equity_chart.png';
        a.click();
        showToast('Equity chart exported as PNG', 'success');
    });

    // --- Chart Zoom Reset ---
    els.resetEquityZoom.addEventListener('click', () => {
        if (Charts.equityChart) Charts.equityChart.resetZoom();
    });
    els.resetDrawdownZoom.addEventListener('click', () => {
        if (Charts.drawdownChart) Charts.drawdownChart.resetZoom();
    });
    els.resetPnlZoom.addEventListener('click', () => {
        if (Charts.pnlChart) Charts.pnlChart.resetZoom();
    });

    // --- Mobile Sidebar Toggle ---
    els.sidebarToggle.addEventListener('click', () => {
        els.sidebar.classList.toggle('open');
        els.sidebarBackdrop.classList.toggle('visible');
    });

    els.sidebarBackdrop.addEventListener('click', () => {
        els.sidebar.classList.remove('open');
        els.sidebarBackdrop.classList.remove('visible');
    });

    function closeSidebarOnMobile() {
        if (window.innerWidth <= 992) {
            els.sidebar.classList.remove('open');
            els.sidebarBackdrop.classList.remove('visible');
        }
    }

    // --- Keyboard Shortcut ---
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runBacktest();
        }
    });

    // --- Helpers ---
    function showError(msg) {
        els.errorMsg.textContent = msg;
        els.errorAlert.classList.add('visible');
    }

    function hideError() {
        els.errorAlert.classList.remove('visible');
    }

    // Initial step progress
    updateStepProgress();
});
