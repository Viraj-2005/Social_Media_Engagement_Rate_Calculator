/* ============================================================
   EngageRate — app behavior
   Theme toggle, chart auto-init from data attributes,
   and loading states for analysis forms.
   ============================================================ */
(function () {
    'use strict';

    function readJSON(id) {
        var el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.error('Failed to parse chart data source:', id, e);
            return null;
        }
    }

    /* ---------- chart initialization ---------- */
    function initCharts() {
        // Wait for Chart.js to be fully loaded
        if (typeof window.Chart === 'undefined') {
            console.error('[EngageRate] Chart.js not loaded. Check CDN connection.');
            return;
        }
        if (!window.EngageCharts) {
            console.error('[EngageRate] EngageCharts not loaded. Check charts.js loaded.');
            return;
        }
        console.log('[EngageRate] Initializing charts...', { chartCount: document.querySelectorAll('canvas[data-chart]').length });
        window.EngageCharts.destroyAll();
        var EC = window.EngageCharts;
        var t = EC.themeColors();

        document.querySelectorAll('canvas[data-chart]').forEach(function (canvas, idx) {
            try {
                var type = canvas.getAttribute('data-chart');
                var source = canvas.getAttribute('data-source');
                var raw = readJSON(source);
                if (!raw) {
                    console.warn('[EngageRate] No data for canvas:', canvas.id);
                    return;
                }

                var payload;
                if (canvas.getAttribute('data-derive') === 'videos') {
                    var sets = EC.videosToChartSets(raw);
                    if (type === 'bar') payload = sets.bar;
                    else if (type === 'scatter') payload = sets.scatter;
                    else if (type === 'line') payload = sets.line;
                    else if (type === 'composition') payload = sets.composition;
                } else {
                    payload = raw;
                }

                // Determine emptiness
                var arr = Array.isArray(payload) ? payload : (payload && payload.data);
                var empty = !Array.isArray(arr) || arr.length === 0;

                var shell = canvas.parentElement;
                var emptyId = canvas.getAttribute('data-empty');
                var emptyEl = emptyId ? document.getElementById(emptyId) : null;

                if (empty) {
                    if (shell) shell.style.display = 'none';
                    if (emptyEl) emptyEl.hidden = false;
                    console.log('[EngageRate] Canvas empty, hiding:', canvas.id);
                    return;
                }
                if (shell) shell.style.display = '';
                if (emptyEl) emptyEl.hidden = true;

                console.log('[EngageRate] Rendering chart:', canvas.id, 'type:', type, 'data points:', Array.isArray(arr) ? arr.length : 'object');
                if (type === 'bar') EC.engagementBar(canvas, payload, t);
                else if (type === 'scatter') EC.viewsScatter(canvas, payload, t);
                else if (type === 'composition') EC.composition(canvas, payload, t);
                else if (type === 'line') EC.trend(canvas, payload, t);
                else console.warn('[EngageRate] Unknown chart type:', type);
            } catch (e) {
                console.error('[EngageRate] Error rendering chart', canvas.id, e);
            }
        });
        console.log('[EngageRate] Charts initialized');
    }

    /* ---------- theme ---------- */
    function syncThemeIcon(theme) {
        var icon = document.getElementById('themeIcon');
        if (icon) icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }

    function initTheme() {
        var root = document.documentElement;
        var toggle = document.getElementById('themeToggle');
        var theme = root.getAttribute('data-theme') || 'light';
        syncThemeIcon(theme);

        if (!toggle) return;
        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (err) { /* private mode */ }
            syncThemeIcon(next);
            initCharts(); // re-render charts with the new palette
        });
    }

    /* ---------- analysis form loading states ---------- */
    function initForms() {
        document.querySelectorAll('form[data-analyze]').forEach(function (form) {
            form.addEventListener('submit', function () {
                var label = form.getAttribute('data-analyze') || 'Working';
                var overlay = document.querySelector('[data-loading-overlay]');
                if (overlay) {
                    var title = overlay.querySelector('[data-loading-title]');
                    if (title) title.textContent = label + '…';
                    overlay.hidden = false;
                }
                var btn = form.querySelector('button[type="submit"]');
                if (btn) btn.disabled = true;
            });
        });
    }

    function waitForChartJS(maxAttempts, interval) {
        return new Promise(function (resolve, reject) {
            var attempts = 0;
            function check() {
                attempts++;
                if (typeof window.Chart !== 'undefined') {
                    console.log('[EngageRate] Chart.js loaded after', attempts, 'attempts');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    reject(new Error('Chart.js failed to load after ' + maxAttempts + ' attempts'));
                } else {
                    setTimeout(check, interval);
                }
            }
            check();
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initTheme();
        waitForChartJS(50, 100).then(function () {
            console.log('[EngageRate] Chart.js ready, initializing charts...');
            initCharts();
        }).catch(function (err) {
            console.error('[EngageRate] ' + err.message);
        });
        initForms();
    });
})();
