/**
 * FinSaaS Dashboard - main application logic.
 * All original features preserved: CSV upload, strategy select, params, backtest, optimize.
 * Enhanced: toast, step progress, loading animation, metric icons, sortable trades,
 * trade summary, expandable metrics, data preview, export, keyboard shortcuts, mobile sidebar,
 * trade filtering/pagination, run history/compare, button states, count-up, skeleton, a11y.
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
        tradeFilters: document.getElementById('tradeFilters'),
        tradeSearchInput: document.getElementById('tradeSearchInput'),
        tradePagination: document.getElementById('tradePagination'),
        paginationPrev: document.getElementById('paginationPrev'),
        paginationNext: document.getElementById('paginationNext'),
        paginationInfo: document.getElementById('paginationInfo'),
        historyPanel: document.getElementById('historyPanel'),
        historyToggleHeader: document.getElementById('historyToggleHeader'),
        historyBody: document.getElementById('historyBody'),
        historyItems: document.getElementById('historyItems'),
        historyChevron: document.getElementById('historyChevron'),
        btnCompare: document.getElementById('btnCompare'),
        compareOverlay: document.getElementById('compareOverlay'),
        compareClose: document.getElementById('compareClose'),
        compareBody: document.getElementById('compareBody'),
        srAnnounce: document.getElementById('srAnnounce'),
    };

    let currentFile = null;
    let currentParams = [];
    let lastBacktestData = null;
    let lastBacktestPayload = null;
    let lastInitialCapital = 10000;

    // Trade sort state
    let tradesData = [];
    let sortCol = null;
    let sortAsc = true;

    // Trade filter/pagination state
    const PAGE_SIZE = 20;
    let filterPnl = 'all';
    let filterSide = 'all';
    let searchQuery = '';
    let currentPage = 0;
    let searchDebounceTimer = null;

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
    updateButtonStates();
    renderRunHistory();

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

    // --- Screen Reader Announce ---
    function srAnnounce(msg) {
        els.srAnnounce.textContent = msg;
        setTimeout(() => { els.srAnnounce.textContent = ''; }, 3000);
    }

    // --- Step Progress ---
    function updateStepProgress() {
        const stepKeys = ['data', 'strategy', 'params', 'config', 'run'];
        const dots = document.querySelectorAll('.step-dot');
        let completedCount = 0;

        stepKeys.forEach((key, i) => {
            dots[i].classList.remove('completed', 'active');
            if (steps[key]) {
                dots[i].classList.add('completed');
                completedCount++;
            }
        });

        const nextStep = stepKeys.findIndex(k => !steps[k]);
        if (nextStep >= 0 && dots[nextStep]) {
            dots[nextStep].classList.add('active');
        }

        const pct = (completedCount / stepKeys.length) * 100;
        els.stepBarFill.style.width = pct + '%';
    }

    // --- Button States ---
    function updateButtonStates() {
        const fileReady = !!currentFile;
        const stratReady = !!els.strategySelect.value;
        els.btnBacktest.disabled = !fileReady || !stratReady;
        els.btnOptimize.disabled = !fileReady || !stratReady;
    }

    // --- Field Validation ---
    function validateFields() {
        let valid = true;
        // Clear previous errors
        document.querySelectorAll('.field-error').forEach(e => e.remove());
        document.querySelectorAll('.form-control.is-invalid').forEach(e => e.classList.remove('is-invalid'));

        const capital = parseFloat(els.capital.value);
        if (!capital || capital <= 0) {
            markInvalid(els.capital, 'Capital must be greater than 0');
            valid = false;
        }

        const commission = parseFloat(els.commission.value);
        if (commission < 0 || commission >= 1) {
            markInvalid(els.commission, 'Commission must be between 0 and 1');
            valid = false;
        }

        const slippage = parseFloat(els.slippage.value);
        if (slippage < 0 || slippage >= 1) {
            markInvalid(els.slippage, 'Slippage must be between 0 and 1');
            valid = false;
        }

        return valid;
    }

    function markInvalid(input, msg) {
        input.classList.add('is-invalid');
        const span = document.createElement('span');
        span.className = 'field-error';
        span.textContent = msg;
        input.parentNode.appendChild(span);
    }

    // Listen for changes to update button states
    els.strategySelect.addEventListener('change', () => {
        updateButtonStates();
    });

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

    // --- Skeleton Loading ---
    function showSkeleton() {
        const skeletonHTML = Array(8).fill('').map(() => `
            <div class="metric-card skeleton gray">
                <div class="skeleton-label"></div>
                <div class="skeleton-value"></div>
            </div>
        `).join('');
        els.metricsCards.innerHTML = skeletonHTML;
    }

    // --- Count-Up Animation ---
    function animateCountUp(element, targetText) {
        // Parse numeric part from text like "$10,000.00", "45.23%", "1.5432"
        const match = targetText.match(/([^0-9\-]*)([\-]?[\d,]+\.?\d*)(.*)/);
        if (!match) {
            element.textContent = targetText;
            return;
        }

        const prefix = match[1];
        const numStr = match[2].replace(/,/g, '');
        const suffix = match[3];
        const target = parseFloat(numStr);

        if (isNaN(target)) {
            element.textContent = targetText;
            return;
        }

        const decimals = numStr.includes('.') ? numStr.split('.')[1].length : 0;
        const duration = 800;
        const startTime = performance.now();

        function update(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            let formatted = current.toFixed(decimals);
            // Reapply commas if original had them
            if (match[2].includes(',')) {
                formatted = parseFloat(formatted).toLocaleString(undefined, {
                    minimumFractionDigits: decimals,
                    maximumFractionDigits: decimals,
                });
            }

            element.textContent = prefix + formatted + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = targetText;
            }
        }

        requestAnimationFrame(update);
    }

    // --- CSV Upload ---
    els.csvDrop.addEventListener('click', () => els.csvFile.click());
    els.csvDrop.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            els.csvFile.click();
        }
    });

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
            updateButtonStates();
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
                    updateButtonStates();
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
                    updateButtonStates();
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
        if (!name) { els.paramsContainer.innerHTML = ''; currentParams = []; steps.strategy = false; updateStepProgress(); updateButtonStates(); return; }
        try {
            const info = await API.getStrategyParams(name);
            currentParams = info.params;
            renderParams(info.params);
            steps.strategy = true;
            steps.params = true;
            updateStepProgress();
            updateButtonStates();
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

                // Range bar for numeric params
                if (p.min_val != null && p.max_val != null) {
                    const rangeBar = document.createElement('div');
                    rangeBar.className = 'param-range-bar';
                    const rangeFill = document.createElement('div');
                    rangeFill.className = 'param-range-fill';
                    const pct = ((p.default - p.min_val) / (p.max_val - p.min_val)) * 100;
                    rangeFill.style.width = Math.max(0, Math.min(100, pct)) + '%';
                    rangeBar.appendChild(rangeFill);

                    input.addEventListener('input', () => {
                        const val = parseFloat(input.value) || 0;
                        const fill = ((val - p.min_val) / (p.max_val - p.min_val)) * 100;
                        rangeFill.style.width = Math.max(0, Math.min(100, fill)) + '%';
                    });

                    div.appendChild(input);
                    div.appendChild(rangeBar);
                    els.paramsContainer.appendChild(div);
                    return;
                }
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

    // --- Button Spinner Helpers ---
    function setButtonLoading(btn, text) {
        btn._origHTML = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="btn-spinner"></span> ${text}`;
    }

    function restoreButton(btn) {
        btn.disabled = false;
        if (btn._origHTML) {
            btn.innerHTML = btn._origHTML;
            delete btn._origHTML;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    // --- Backtest ---
    els.btnBacktest.addEventListener('click', runBacktest);

    async function runBacktest() {
        if (!currentFile) { showError('Please upload or select a CSV file first'); return; }
        const strategy = els.strategySelect.value;
        if (!strategy) { showError('Please select a strategy'); return; }
        if (!validateFields()) return;

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
        showSkeleton();
        els.results.classList.add('visible');
        startLoadingAnimation('backtest');
        setButtonLoading(els.btnBacktest, 'Running...');
        closeSidebarOnMobile();

        try {
            const data = await API.runBacktest(payload);
            lastBacktestData = data;
            lastBacktestPayload = payload;
            lastInitialCapital = payload.initial_capital;
            renderResults(data, payload.initial_capital);
            saveRunToHistory(data, payload);
            steps.run = true;
            updateStepProgress();
            showToast(`Backtest complete — ${data.total_trades} trades`, 'success');
            srAnnounce(`Backtest complete. ${data.total_trades} trades executed. Total return: ${(data.metrics.total_return_pct || 0).toFixed(2)} percent.`);
        } catch (err) {
            showError(err.message);
            showToast('Backtest failed', 'error');
            els.results.classList.remove('visible');
        } finally {
            stopLoadingAnimation();
            els.spinner.classList.remove('visible');
            restoreButton(els.btnBacktest);
            updateButtonStates();
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
                <div class="metric-value ${met.cls}" data-target="${met.value}"></div>
            </div>
        `).join('');

        // Trigger count-up animation for primary metrics
        els.metricsCards.querySelectorAll('.metric-value[data-target]').forEach(el => {
            animateCountUp(el, el.dataset.target);
        });

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
                    <div class="metric-value ${met.cls}" data-target="${met.value}"></div>
                </div>
            `).join('');
            els.metricsToggle.style.display = 'block';
        } else {
            els.metricsToggle.style.display = 'none';
        }

        // Charts - pass trades for markers
        if (data.equity_curve.length) {
            Charts.renderEquity('equityChart', data.equity_curve, initialCapital, data.trades);
            Charts.renderDrawdown('drawdownChart', data.equity_curve);
        }

        // P&L Distribution
        if (data.trades.length) {
            Charts.renderPnlDistribution('pnlChart', data.trades);
        }

        // Store trades for sorting/filtering
        tradesData = data.trades.slice();
        sortCol = null;
        sortAsc = true;
        filterPnl = 'all';
        filterSide = 'all';
        searchQuery = '';
        currentPage = 0;

        // Show filters if trades exist
        els.tradeFilters.style.display = tradesData.length ? 'flex' : 'none';
        // Reset filter button active states
        els.tradeFilters.querySelectorAll('[data-filter-pnl]').forEach(b => b.classList.toggle('active', b.dataset.filterPnl === 'all'));
        els.tradeFilters.querySelectorAll('[data-filter-side]').forEach(b => b.classList.toggle('active', b.dataset.filterSide === 'all'));
        els.tradeSearchInput.value = '';

        renderFilteredTrades();
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
            // Animate secondary metric count-ups
            sec.querySelectorAll('.metric-value[data-target]').forEach(el => {
                animateCountUp(el, el.dataset.target);
            });
        }
        if (typeof lucide !== 'undefined') lucide.createIcons();
    });

    // --- Trade Filtering & Pagination ---
    function getFilteredTrades() {
        let filtered = tradesData.slice();

        // Apply sort
        if (sortCol) {
            filtered.sort((a, b) => {
                let va = a[sortCol], vb = b[sortCol];
                if (typeof va === 'string') {
                    return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
                }
                return sortAsc ? va - vb : vb - va;
            });
        }

        // Apply PnL filter
        if (filterPnl === 'winning') {
            filtered = filtered.filter(t => t.pnl >= 0);
        } else if (filterPnl === 'losing') {
            filtered = filtered.filter(t => t.pnl < 0);
        }

        // Apply side filter
        if (filterSide === 'long') {
            filtered = filtered.filter(t => t.side === 'long');
        } else if (filterSide === 'short') {
            filtered = filtered.filter(t => t.side === 'short');
        }

        // Apply search
        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            filtered = filtered.filter(t =>
                t.entry_time.toLowerCase().includes(q) ||
                t.exit_time.toLowerCase().includes(q)
            );
        }

        return filtered;
    }

    function renderFilteredTrades() {
        const filtered = getFilteredTrades();
        const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
        if (currentPage >= totalPages) currentPage = totalPages - 1;
        if (currentPage < 0) currentPage = 0;

        const start = currentPage * PAGE_SIZE;
        const pageData = filtered.slice(start, start + PAGE_SIZE);

        renderTradesTable(pageData);

        // Pagination
        if (filtered.length > PAGE_SIZE) {
            els.tradePagination.style.display = 'flex';
            els.paginationPrev.disabled = currentPage === 0;
            els.paginationNext.disabled = currentPage >= totalPages - 1;
            const showStart = start + 1;
            const showEnd = Math.min(start + PAGE_SIZE, filtered.length);
            els.paginationInfo.textContent = `Showing ${showStart}-${showEnd} of ${filtered.length}`;
        } else {
            els.tradePagination.style.display = filtered.length ? 'flex' : 'none';
            els.paginationPrev.disabled = true;
            els.paginationNext.disabled = true;
            if (filtered.length) {
                els.paginationInfo.textContent = `Showing 1-${filtered.length} of ${filtered.length}`;
            }
        }
    }

    // Filter button click handlers
    els.tradeFilters.addEventListener('click', (e) => {
        const btn = e.target.closest('.filter-btn');
        if (!btn) return;

        if (btn.dataset.filterPnl) {
            filterPnl = btn.dataset.filterPnl;
            els.tradeFilters.querySelectorAll('[data-filter-pnl]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        if (btn.dataset.filterSide) {
            filterSide = btn.dataset.filterSide;
            els.tradeFilters.querySelectorAll('[data-filter-side]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        currentPage = 0;
        renderFilteredTrades();
    });

    // Search input with debounce
    els.tradeSearchInput.addEventListener('input', () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = els.tradeSearchInput.value.trim();
            currentPage = 0;
            renderFilteredTrades();
        }, 300);
    });

    // Pagination
    els.paginationPrev.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            renderFilteredTrades();
        }
    });

    els.paginationNext.addEventListener('click', () => {
        currentPage++;
        renderFilteredTrades();
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
            row.setAttribute('tabindex', '0');
            row.setAttribute('role', 'row');
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

            // Expand/collapse detail row on click
            row.addEventListener('click', () => toggleTradeDetail(row, t));
            row.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleTradeDetail(row, t);
                }
                // Arrow key navigation
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    let next = row.nextElementSibling;
                    while (next && next.classList.contains('trade-detail-row')) next = next.nextElementSibling;
                    if (next) next.focus();
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    let prev = row.previousElementSibling;
                    while (prev && prev.classList.contains('trade-detail-row')) prev = prev.previousElementSibling;
                    if (prev) prev.focus();
                }
            });

            tbody.appendChild(row);
        });
    }

    function toggleTradeDetail(row, trade) {
        const existing = row.nextElementSibling;
        if (existing && existing.classList.contains('trade-detail-row')) {
            existing.remove();
            row.classList.remove('expanded');
            return;
        }

        // Remove any other expanded rows
        els.tradesTable.querySelectorAll('.trade-detail-row').forEach(r => r.remove());
        els.tradesTable.querySelectorAll('tr.expanded').forEach(r => r.classList.remove('expanded'));

        row.classList.add('expanded');
        const detailRow = document.createElement('tr');
        detailRow.className = 'trade-detail-row';

        const qty = trade.quantity != null ? trade.quantity : '-';
        const comm = trade.commission != null ? `$${trade.commission.toFixed(4)}` : '-';
        const duration = trade.bars_held;
        const ret = `${trade.pnl_pct >= 0 ? '+' : ''}${trade.pnl_pct.toFixed(2)}%`;

        detailRow.innerHTML = `
            <td colspan="8">
                <div class="trade-detail">
                    <div class="trade-detail-item">
                        <span class="detail-label">Quantity</span>
                        <span class="detail-value">${qty}</span>
                    </div>
                    <div class="trade-detail-item">
                        <span class="detail-label">Commission</span>
                        <span class="detail-value">${comm}</span>
                    </div>
                    <div class="trade-detail-item">
                        <span class="detail-label">Duration (bars)</span>
                        <span class="detail-value">${duration}</span>
                    </div>
                    <div class="trade-detail-item">
                        <span class="detail-label">Return</span>
                        <span class="detail-value ${trade.pnl_pct >= 0 ? 'pnl-positive' : 'pnl-negative'}">${ret}</span>
                    </div>
                </div>
            </td>
        `;
        row.after(detailRow);
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

        currentPage = 0;
        renderFilteredTrades();
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

    // --- Run History ---
    const HISTORY_KEY = 'finsaas_run_history';
    const MAX_HISTORY = 5;

    function getRunHistory() {
        try {
            return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        } catch (_) {
            return [];
        }
    }

    function saveRunToHistory(data, payload) {
        const history = getRunHistory();
        const entry = {
            id: Date.now(),
            strategy: payload.strategy,
            date: new Date().toISOString(),
            returnPct: (data.metrics.total_return_pct || 0).toFixed(2),
            trades: data.total_trades || 0,
            data,
            payload,
        };
        history.unshift(entry);
        if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        renderRunHistory();
    }

    function renderRunHistory() {
        const history = getRunHistory();
        if (!history.length) {
            els.historyPanel.style.display = 'none';
            return;
        }

        els.historyPanel.style.display = 'block';
        els.historyItems.innerHTML = '';

        history.forEach((h, i) => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.dataset.idx = i;

            const dateStr = new Date(h.date).toLocaleString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
            });

            item.innerHTML = `
                <input type="checkbox" class="history-check" data-idx="${i}" aria-label="Select run ${i + 1} for comparison">
                <div class="history-item-info">
                    <span class="history-item-name">${h.strategy}</span>
                    <span class="history-item-meta">${dateStr} | ${h.returnPct}% | ${h.trades} trades</span>
                </div>
                <button class="history-load-btn" data-idx="${i}" aria-label="Load run ${i + 1}">Load</button>
            `;
            els.historyItems.appendChild(item);
        });

        // Update compare button state
        updateCompareBtn();
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // History panel toggle
    els.historyToggleHeader.addEventListener('click', () => {
        els.historyPanel.classList.toggle('collapsed');
    });

    // History item clicks
    els.historyItems.addEventListener('click', (e) => {
        const loadBtn = e.target.closest('.history-load-btn');
        if (loadBtn) {
            const idx = parseInt(loadBtn.dataset.idx);
            const history = getRunHistory();
            if (history[idx]) {
                lastBacktestData = history[idx].data;
                lastInitialCapital = history[idx].payload.initial_capital;
                renderResults(history[idx].data, history[idx].payload.initial_capital);
                showToast('Loaded previous run', 'info');
            }
            return;
        }

        const checkbox = e.target.closest('.history-check');
        if (checkbox) {
            // Enforce max 2 selections
            const checked = els.historyItems.querySelectorAll('.history-check:checked');
            if (checked.length > 2) {
                checkbox.checked = false;
            }
            updateCompareBtn();
            // Highlight selected
            els.historyItems.querySelectorAll('.history-item').forEach(item => {
                const cb = item.querySelector('.history-check');
                item.classList.toggle('selected', cb && cb.checked);
            });
        }
    });

    function updateCompareBtn() {
        const checked = els.historyItems.querySelectorAll('.history-check:checked');
        els.btnCompare.disabled = checked.length !== 2;
    }

    // Compare button
    els.btnCompare.addEventListener('click', () => {
        const checked = els.historyItems.querySelectorAll('.history-check:checked');
        if (checked.length !== 2) return;

        const history = getRunHistory();
        const idx1 = parseInt(checked[0].dataset.idx);
        const idx2 = parseInt(checked[1].dataset.idx);
        const run1 = history[idx1];
        const run2 = history[idx2];

        if (!run1 || !run2) return;
        showComparison(run1, run2);
    });

    function showComparison(run1, run2) {
        const m1 = run1.data.metrics;
        const m2 = run2.data.metrics;

        const compareMetrics = [
            { label: 'Total Return %', key: 'total_return_pct', fmt: v => v.toFixed(2) + '%' },
            { label: 'Sharpe Ratio', key: 'sharpe_ratio', fmt: v => v.toFixed(4) },
            { label: 'Max Drawdown %', key: 'max_drawdown_pct', fmt: v => v.toFixed(2) + '%', invert: true },
            { label: 'Win Rate', key: 'win_rate', fmt: v => v.toFixed(1) + '%' },
            { label: 'Profit Factor', key: 'profit_factor', fmt: v => v.toFixed(2) },
            { label: 'Total Trades', key: 'total_trades', fmt: v => v.toFixed(0) },
            { label: 'Expectancy', key: 'expectancy', fmt: v => v.toFixed(2) },
            { label: 'Sortino Ratio', key: 'sortino_ratio', fmt: v => v.toFixed(4) },
            { label: 'Avg Win', key: 'avg_win', fmt: v => '$' + v.toFixed(2) },
            { label: 'Avg Loss', key: 'avg_loss', fmt: v => '$' + v.toFixed(2), invert: true },
        ];

        const rows = compareMetrics.map(cm => {
            const v1 = m1[cm.key] || 0;
            const v2 = m2[cm.key] || 0;
            const delta = v2 - v1;
            const better = cm.invert ? delta < 0 : delta > 0;
            const deltaClass = Math.abs(delta) < 0.0001 ? '' : (better ? 'positive' : 'negative');
            const arrow = Math.abs(delta) < 0.0001 ? '' : (better ? '&#9650;' : '&#9660;');

            return `
                <tr>
                    <td style="font-weight:600">${cm.label}</td>
                    <td>${cm.fmt(v1)}</td>
                    <td>${cm.fmt(v2)}</td>
                    <td class="compare-delta ${deltaClass}">${arrow} ${Math.abs(delta) < 0.0001 ? '-' : cm.fmt(Math.abs(delta))}</td>
                </tr>
            `;
        }).join('');

        const dateStr1 = new Date(run1.date).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        const dateStr2 = new Date(run2.date).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        els.compareBody.innerHTML = `
            <table class="compare-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>${run1.strategy}<br><small style="font-weight:400;color:var(--text-secondary)">${dateStr1}</small></th>
                        <th>${run2.strategy}<br><small style="font-weight:400;color:var(--text-secondary)">${dateStr2}</small></th>
                        <th>Delta</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;

        els.compareOverlay.classList.add('visible');
    }

    els.compareClose.addEventListener('click', () => {
        els.compareOverlay.classList.remove('visible');
    });

    els.compareOverlay.addEventListener('click', (e) => {
        if (e.target === els.compareOverlay) {
            els.compareOverlay.classList.remove('visible');
        }
    });

    // --- Optimize ---
    els.btnOptimize.addEventListener('click', async () => {
        if (!currentFile) { showError('Please upload or select a CSV file first'); return; }
        const strategy = els.strategySelect.value;
        if (!strategy) { showError('Please select a strategy'); return; }
        if (!validateFields()) return;

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
        setButtonLoading(els.btnOptimize, 'Optimizing...');
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
            restoreButton(els.btnOptimize);
            updateButtonStates();
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
        // Escape to close compare overlay
        if (e.key === 'Escape') {
            if (els.compareOverlay.classList.contains('visible')) {
                els.compareOverlay.classList.remove('visible');
            }
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
