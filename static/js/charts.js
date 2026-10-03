/* ============================================================
   EngageCharts — shared Chart.js (v4) builders for EngageRate
   All chart data comes from Django context (json_script).
   No hardcoded data here.
   ============================================================ */
(function () {
    'use strict';

    var FONT = "'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif";
    var instances = [];

    /* ---------- theme-aware palette ---------- */
    function themeColors() {
        var dark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            dark: dark,
            primary: dark ? '#8B84FF' : '#635BFF',
            primarySoft: dark ? 'rgba(139,132,255,0.25)' : 'rgba(99,91,255,0.18)',
            accent: dark ? '#33C5DC' : '#13B8D4',
            accentSoft: dark ? 'rgba(51,197,220,0.22)' : 'rgba(19,184,212,0.18)',
            grid: dark ? 'rgba(148,163,184,0.14)' : 'rgba(100,116,139,0.13)',
            tick: dark ? '#A9B4CC' : '#64748B',
            axisTitle: dark ? '#C7D0E4' : '#475569',
            tooltipBg: dark ? '#1B2338' : '#172033',
            tooltipTitle: '#F1F4FB',
            tooltipBody: dark ? '#C7D0E4' : '#E2E8F0',
            pointBorder: dark ? '#141B2F' : '#FFFFFF'
        };
    }

    /* ---------- number / date formatting ---------- */
    function num(x) {
        if (x === null || x === undefined) return 0;
        var n = Number(x);
        return isNaN(n) ? 0 : n;
    }

    function trim1(x) {
        var s = (Math.round(x * 10) / 10).toFixed(1);
        return s.slice(-2) === '.0' ? s.slice(0, -2) : s;
    }

    function abbrev(n) {
        n = num(n);
        var abs = Math.abs(n);
        if (abs >= 1e9) return trim1(n / 1e9) + 'B';
        if (abs >= 1e6) return trim1(n / 1e6) + 'M';
        if (abs >= 1e3) return trim1(n / 1e3) + 'K';
        return String(Math.round(n));
    }

    function fmtFull(n) {
        return num(n).toLocaleString('en-US');
    }

    function fmtPct(x) {
        var n = num(x);
        return (Math.round(n * 100) / 100).toFixed(2) + '%';
    }

    function parseDate(label) {
        if (!label) return null;
        // Django chart labels are 'YYYY-MM-DD'; treat as local midnight so
        // display dates never shift across timezones.
        var d = new Date(String(label).length === 10 ? label + 'T00:00:00' : label);
        return isNaN(d.getTime()) ? null : d;
    }

    function fmtShortDate(label) {
        var d = parseDate(label);
        return d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    }

    function fmtLongDate(label) {
        var d = parseDate(label);
        return d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
    }

    /* ---------- lifecycle ---------- */
    function register(chart) {
        instances.push(chart);
        return chart;
    }

    function destroyAll() {
        while (instances.length) {
            try { instances.pop().destroy(); } catch (e) { /* already destroyed */ }
        }
    }

    /* ---------- tooltip defaults ---------- */
    function tooltipBase(t) {
        return {
            enabled: true,
            backgroundColor: t.tooltipBg,
            titleColor: t.tooltipTitle,
            bodyColor: t.tooltipBody,
            padding: 12,
            cornerRadius: 10,
            displayColors: false,
            titleFont: { family: FONT, size: 13, weight: '600' },
            bodyFont: { family: FONT, size: 12 },
            boxPadding: 4
        };
    }

    function axisTitle(text, t) {
        return { display: true, text: text, color: t.axisTitle, font: { family: FONT, size: 12, weight: '500' } };
    }

    /* ============================================================
       1. Engagement Rate by Video — horizontal bar chart
       data: { labels: [..], data: [..], tooltips: [{title, engagement_rate, views, likes, comments}] }
       ============================================================ */
    function engagementBar(canvas, d, t) {
        t = t || themeColors();
        d = d || {};
        var labels = (d.labels || []).map(function (s) {
            s = String(s || '');
            return s.length > 26 ? s.slice(0, 26) + '…' : s;
        });
        var chart = register(new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Engagement Rate',
                    data: (d.data || []).map(num),
                    backgroundColor: t.primarySoft,
                    borderColor: t.primary,
                    borderWidth: 1.5,
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 26
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 450, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: Object.assign(tooltipBase(t), {
                        callbacks: {
                            title: function (ctx) {
                                var tip = (d.tooltips || [])[ctx[0].dataIndex];
                                return tip ? tip.title : '';
                            },
                            label: function (ctx) {
                                var tip = (d.tooltips || [])[ctx[0].dataIndex];
                                if (!tip) return '';
                                var total = num(tip.likes) + num(tip.comments);
                                return [
                                    'Engagement rate:  ' + fmtPct(tip.engagement_rate),
                                    'Views:  ' + fmtFull(tip.views),
                                    'Likes:  ' + fmtFull(tip.likes),
                                    'Comments:  ' + fmtFull(tip.comments),
                                    'Total engagement:  ' + fmtFull(total)
                                ];
                            }
                        }
                    })
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: axisTitle('Engagement Rate (%)', t),
                        grid: { color: t.grid },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, callback: function (v) { return v + '%'; } }
                    },
                    y: {
                        title: axisTitle('Video', t),
                        grid: { display: false },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, autoSkip: false }
                    }
                },
                interaction: { mode: 'nearest', intersect: false, axis: 'y' }
            }
        }));
        return chart;
    }

    /* ============================================================
       2. Engagement Composition — doughnut (Likes / Comments)
       data: { labels: [..], data: [likes, comments], total: n }
       ============================================================ */
    function composition(canvas, d, t) {
        t = t || themeColors();
        d = d || {};
        var labels = d.labels || ['Likes', 'Comments'];
        var data = (d.data || [0, 0]).map(num);
        var total = d.total != null ? num(d.total) : data.reduce(function (a, b) { return a + b; }, 0);
        return register(new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [t.primary, t.accent],
                    borderColor: t.pointBorder,
                    borderWidth: 2,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                layout: { padding: 8 },
                animation: { duration: 450, easing: 'easeOutQuart' },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: t.tick,
                            font: { family: FONT, size: 12, weight: '500' },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 8,
                            boxHeight: 8,
                            padding: 18
                        }
                    },
                    tooltip: Object.assign(tooltipBase(t), {
                        callbacks: {
                            label: function (ctx) {
                                var raw = num(ctx.raw);
                                var pct = total > 0 ? ((raw / total) * 100).toFixed(1) : '0.0';
                                return ctx.label + ':  ' + fmtFull(raw) + '  (' + pct + '%)';
                            }
                        }
                    })
                },
                interaction: { mode: 'nearest', intersect: true }
            }
        }));
    }

    /* ============================================================
       3. Views vs Engagement Rate — scatter
       points: [{ x, y, title, views, likes, comments, engagement_rate }]
       Log x-axis automatically when view counts span wide ranges.
       ============================================================ */
    function viewsScatter(canvas, points, t) {
        t = t || themeColors();
        points = points || [];
        var xs = points.map(function (p) { return num(p.x); }).filter(function (x) { return x > 0; });
        var useLog = xs.length > 0 && (Math.max.apply(null, xs) / Math.min.apply(null, xs)) >= 100;

        var chart = register(new Chart(canvas, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Videos',
                    data: points.map(function (p) { return { x: num(p.x), y: num(p.y) }; }),
                    backgroundColor: t.accentSoft,
                    borderColor: t.accent,
                    borderWidth: 1.5,
                    pointBackgroundColor: t.accent,
                    pointBorderColor: t.pointBorder,
                    pointBorderWidth: 1.5,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointHitRadius: 16
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 450, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: Object.assign(tooltipBase(t), {
                        callbacks: {
                            title: function (ctx) {
                                var p = points[ctx[0].dataIndex];
                                return p ? (p.title || p.label || 'Video') : '';
                            },
                            label: function (ctx) {
                                var p = points[ctx[0].dataIndex];
                                if (!p) return '';
                                var rows = ['Views:  ' + fmtFull(p.views != null ? p.views : p.x)];
                                if (p.likes != null) rows.push('Likes:  ' + fmtFull(p.likes));
                                rows.push('Engagement rate:  ' + fmtPct(p.engagement_rate != null ? p.engagement_rate : ctx.raw.y));
                                return rows;
                            }
                        }
                    })
                },
                scales: {
                    x: {
                        type: useLog ? 'logarithmic' : 'linear',
                        beginAtZero: !useLog,
                        title: axisTitle('Views', t),
                        grid: { color: t.grid },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, callback: function (v) { return abbrev(v); } }
                    },
                    y: {
                        beginAtZero: true,
                        title: axisTitle('Engagement Rate (%)', t),
                        grid: { color: t.grid },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, callback: function (v) { return v + '%'; } }
                    }
                },
                interaction: { mode: 'nearest', intersect: false }
            }
        }));
        return chart;
    }
    function trend(canvas, d, t) {
        t = t || themeColors();
        d = d || {};
        var labels = (d.labels || []).map(fmtShortDate);
        var chart = register(new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Engagement Rate',
                    data: (d.data || []).map(num),
                    borderColor: t.primary,
                    borderWidth: 2.5,
                    tension: 0.35,
                    fill: true,
                    backgroundColor: t.primarySoft,
                    pointRadius: 3.5,
                    pointHoverRadius: 6,
                    pointBackgroundColor: t.primary,
                    pointBorderColor: t.pointBorder,
                    pointBorderWidth: 1.5,
                    pointHitRadius: 14
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 450, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: Object.assign(tooltipBase(t), {
                        callbacks: {
                            title: function (ctx) {
                                var tip = (d.tooltips || [])[ctx[0].dataIndex];
                                return tip ? tip.title : '';
                            },
                            label: function (ctx) {
                                var tip = (d.tooltips || [])[ctx[0].dataIndex];
                                if (!tip) return '';
                                return [
                                    fmtLongDate(tip.published_date),
                                    'Engagement rate:  ' + fmtPct(tip.engagement_rate),
                                    'Views:  ' + fmtFull(tip.views)
                                ];
                            }
                        }
                    })
                },
                scales: {
                    x: {
                        title: axisTitle('Publication Date', t),
                        grid: { display: false },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }
                    },
                    y: {
                        beginAtZero: true,
                        title: axisTitle('Engagement Rate (%)', t),
                        grid: { color: t.grid },
                        ticks: { color: t.tick, font: { family: FONT, size: 11 }, callback: function (v) { return v + '%'; } }
                    }
                },
                interaction: { mode: 'index', intersect: false }
            }
        }));
        return chart;
    }

    /* ============================================================
       Helper: derive all chart sets from a raw video list
       (as produced by get_channel_analytics). Used by pages that
       pass raw video dicts instead of pre-built chart data.
       ============================================================ */
    function videosToChartSets(videos) {
        var rows = (videos || []).filter(function (v) { return v && v.title; });
        var sets = {
            bar: {
                labels: rows.map(function (v) { return String(v.title); }),
                data: rows.map(function (v) { return num(v.engagement_rate); }),
                tooltips: rows.map(function (v) {
                    return {
                        title: v.title,
                        engagement_rate: num(v.engagement_rate),
                        views: num(v.views),
                        likes: num(v.likes),
                        comments: num(v.comments)
                    };
                })
            },
            scatter: rows.map(function (v) {
                return {
                    x: num(v.views),
                    y: num(v.engagement_rate),
                    title: v.title,
                    views: num(v.views),
                    likes: num(v.likes),
                    comments: num(v.comments),
                    engagement_rate: num(v.engagement_rate)
                };
            })
        };
        var withDates = rows
            .filter(function (v) { return v.published_at; })
            .sort(function (a, b) { return new Date(a.published_at) - new Date(b.published_at); });
        sets.line = {
            labels: withDates.map(function (v) { return String(v.published_at).slice(0, 10); }),
            data: withDates.map(function (v) { return num(v.engagement_rate); }),
            tooltips: withDates.map(function (v) {
                return {
                    title: v.title,
                    published_date: String(v.published_at).slice(0, 10),
                    engagement_rate: num(v.engagement_rate),
                    views: num(v.views)
                };
            })
        };
        sets.composition = {
            labels: ['Likes', 'Comments'],
            data: [
                rows.reduce(function (a, v) { return a + num(v.likes); }, 0),
                rows.reduce(function (a, v) { return a + num(v.comments); }, 0)
            ],
            total: 0
        };
        return sets;
    }

    window.EngageCharts = {
        engagementBar: engagementBar,
        composition: composition,
        viewsScatter: viewsScatter,
        trend: trend,
        videosToChartSets: videosToChartSets,
        themeColors: themeColors,
        destroyAll: destroyAll,
        abbrev: abbrev,
        fmtFull: fmtFull,
        fmtPct: fmtPct,
        fmtShortDate: fmtShortDate,
        fmtLongDate: fmtLongDate
    };
})();
