import { useRef, useEffect, useState, useCallback } from 'react';
import { createChart, LineStyle, CrosshairMode } from 'lightweight-charts';

const toDay = (d) => d ? d.split('T')[0] : d;

// Module-level: persists across re-renders AND unmount/remount (tab switches)
let savedVisibleRange = null;
let savedPriceRange = null; // { top: number, bottom: number } from coordinateToPrice

const TOGGLE_DEFS = [
    { key: 'buy', label: 'BUY Markers', default: true },
    { key: 'sell', label: 'SELL Markers', default: true },
    { key: 'tradeLines', label: 'Trade Lines', default: true },
    { key: 'openTrade', label: 'Open Trade', default: true },
    { key: 'priceLevels', label: 'Price Levels', default: true },
    { key: 'volume', label: 'Volume', default: true },
];

const TIMEFRAMES = [
    { label: '1M', days: 30 },
    { label: '3M', days: 90 },
    { label: '6M', days: 180 },
    { label: '1Y', days: 365 },
    { label: 'ALL', days: 0 },
];

const CHART_THEME = {
    dark: {
        bg: '#0e1117', text: '#e6edf3', grid: 'rgba(31,41,51,0.5)',
        border: '#1f2933', crosshair: 'rgba(59,130,246,0.3)',
    },
    light: {
        bg: '#f4f6f9', text: '#1e293b', grid: '#e2e8f0',
        border: 'rgba(0,0,0,0.1)', crosshair: 'rgba(59,130,246,0.3)',
    },
};

function fmtVol(v) {
    if (v == null) return '--';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K';
    return v.toString();
}

/* Helper: normalise LightweightCharts time → YYYY-MM-DD */
function timeToStr(t) {
    if (!t) return null;
    if (typeof t === 'string') return t;
    if (typeof t === 'object' && t.year)
        return `${t.year}-${String(t.month).padStart(2, '0')}-${String(t.day).padStart(2, '0')}`;
    return null;
}

function formatCrosshairDate(t) {
    const str = timeToStr(t);
    if (!str) return '';
    const [y, m, d] = str.split('-');
    const date = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
    const mon = date.toLocaleString('en-US', { month: 'short' });
    const yy = y.slice(-2);
    return `${mon} ${d}, ${yy}`;
}

export default function ChartPanel({ priceData, signals, trades, openTrade, overlayData, oscillatorData, chartConfig }) {
    const wrapperRef = useRef(null);
    const priceRef = useRef(null);
    const chartRef = useRef(null);
    const candleSeriesRef = useRef(null);
    const tooltipRef = useRef(null);
    const oscValueRef = useRef(null);
    const prevTimeframeRef = useRef('ALL');
    const [showAll, setShowAll] = useState(true);
    const [nightMode, setNightMode] = useState(true);
    const [toggles, setToggles] = useState(() => {
        const t = {};
        TOGGLE_DEFS.forEach(d => { t[d.key] = d.default; });
        t.overlay = true;
        t.oscillator = true;
        return t;
    });
    const [activeTimeframe, setActiveTimeframe] = useState('ALL');
    const [showGoTo, setShowGoTo] = useState(false);
    const [goToDate, setGoToDate] = useState('');
    const goToHighlightRef = useRef(null);
    const [fullscreenPanel, setFullscreenPanel] = useState(null); // null | 'price'

    // Toggle fullscreen for a chart panel
    const toggleFullscreen = useCallback((panel) => {
        setFullscreenPanel(prev => {
            const next = prev === panel ? null : panel;
            setTimeout(() => {
                if (chartRef.current && priceRef.current) {
                    chartRef.current.applyOptions({ width: priceRef.current.clientWidth, height: priceRef.current.clientHeight });
                }
            }, 50);
            return next;
        });
    }, []);

    // ESC key to exit fullscreen
    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape' && fullscreenPanel) { toggleFullscreen(fullscreenPanel); } };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [fullscreenPanel, toggleFullscreen]);

    // Navigate to a date and highlight the candle for 5 seconds
    const navigateToDate = useCallback((targetDate) => {
        const chart = chartRef.current;
        const cs = candleSeriesRef.current;
        if (!chart || !cs || !priceData?.length) return;

        const candles = priceData.map(d => toDay(d.date));
        let idx = candles.indexOf(targetDate);
        if (idx === -1) {
            idx = candles.findIndex(d => d >= targetDate);
            if (idx === -1) idx = candles.length - 1;
        }
        const actualDate = candles[idx];

        // Navigate to the date
        const halfWindow = 20;
        chart.timeScale().setVisibleLogicalRange({
            from: Math.max(0, idx - halfWindow),
            to: Math.min(candles.length - 1, idx + halfWindow),
        });

        // Build current markers (from series-update effect) + highlight marker
        const currentMarkers = cs.markers ? [...cs.markers()] : [];
        const highlightMarker = {
            time: actualDate,
            position: 'aboveBar',
            color: '#FFD700',
            shape: 'circle',
            text: '▶ Hi',
            size: 2,
        };
        const withHighlight = [...currentMarkers, highlightMarker];
        withHighlight.sort((a, b) => a.time < b.time ? -1 : a.time > b.time ? 1 : 0);
        cs.setMarkers(withHighlight);

        // Clear any previous highlight timer
        if (goToHighlightRef.current) clearTimeout(goToHighlightRef.current);

        // Remove highlight after 5 seconds
        goToHighlightRef.current = setTimeout(() => {
            if (candleSeriesRef.current) {
                // Restore original markers without the highlight
                currentMarkers.sort((a, b) => a.time < b.time ? -1 : a.time > b.time ? 1 : 0);
                candleSeriesRef.current.setMarkers(currentMarkers);
            }
            goToHighlightRef.current = null;
        }, 5000);
    }, [priceData]);

    const theme = nightMode ? CHART_THEME.dark : CHART_THEME.light;
    const toggle = (key) => setToggles(prev => ({ ...prev, [key]: !prev[key] }));
    const isOn = useCallback((key) => showAll && toggles[key], [showAll, toggles]);

    const overlayLabel = chartConfig?.overlay_label || (overlayData ? 'Overlay' : null);
    const hasOscillator = !!(oscillatorData?.data?.length);
    const showOsc = hasOscillator && isOn('oscillator');

    const allToggles = [...TOGGLE_DEFS];
    if (overlayLabel) allToggles.splice(4, 0, { key: 'overlay', label: overlayLabel, default: true });
    if (hasOscillator) allToggles.push({ key: 'oscillator', label: 'Oscillator', default: true });

    // Build indexed price lookup
    const priceLookup = useRef({});
    useEffect(() => {
        const m = {};
        if (priceData?.length) {
            priceData.forEach((d, i) => { m[toDay(d.date)] = { ...d, _idx: i }; });
        }
        priceLookup.current = m;
    }, [priceData]);

    // ─── Ref to track dynamic series (everything except candlestick) ───
    const dynamicSeriesRef = useRef([]);
    const priceLinesRef = useRef([]);

    // ─── Price chart creation (only depends on data, height) ───
    useEffect(() => {
        if (!priceRef.current || !priceData?.length) return;
        if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }
        
        const currentTheme = nightMode ? CHART_THEME.dark : CHART_THEME.light;

        const chart = createChart(priceRef.current, {
            layout: { background: { color: currentTheme.bg }, textColor: currentTheme.text, fontFamily: "'Inter', sans-serif", fontSize: 11 },
            grid: { vertLines: { visible: false }, horzLines: { visible: false } },
            crosshair: {
                mode: CrosshairMode.Magnet,
                vertLine: { visible: true, labelVisible: true, color: theme.crosshair },
                horzLine: { visible: true, labelVisible: false, color: theme.crosshair },
            },
            localization: {
                timeFormatter: formatCrosshairDate,
            },
            timeScale: {
                borderColor: theme.border, timeVisible: false, secondsVisible: false,
                rightBarStaysOnScroll: false,
            },
            rightPriceScale: {
                borderVisible: false,
                scaleMargins: { top: 0.1, bottom: 0.25 },
                autoScale: !savedPriceRange,
            },
            leftPriceScale: {
                visible: false,
            }
        });
        chartRef.current = chart;

        // Candlestick
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#00A86B', downColor: '#FF3B30',
            borderUpColor: '#00A86B', borderDownColor: '#FF3B30',
            wickUpColor: '#00A86B', wickDownColor: '#FF3B30',
            lastValueVisible: false,
        });
        const candles = priceData.map(d => ({
            time: toDay(d.date), open: d.open, high: d.high, low: d.low, close: d.close,
        }));
        candleSeries.setData(candles);
        candleSeriesRef.current = candleSeries;

        // OHLC + Date Label + Oscillator value on crosshair
        chart.subscribeCrosshairMove(param => {
            const tooltipEl = tooltipRef.current;

            if (!param || !param.time || !param.seriesData) {
                if (tooltipEl) tooltipEl.style.display = 'none';
                if (oscValueRef.current) oscValueRef.current.style.display = 'none';
                return;
            }

            const dateStr = timeToStr(param.time);
            if (!dateStr) return;

            // ── OHLC bar ──
            const bar = priceLookup.current[dateStr];
            if (tooltipEl) {
                if (!bar) { tooltipEl.style.display = 'none'; }
                else {
                    const prevIdx = (bar._idx || 0) - 1;
                    const prevBar = prevIdx >= 0 ? priceData[prevIdx] : null;
                    const bullish = bar.close >= bar.open;
                    const mainColor = bullish ? '#26A69A' : '#EF5350';
                    let changeHtml = '<b>Δ:</b> -- (--)';
                    if (prevBar) {
                        const diff = bar.close - prevBar.close;
                        const pct = (diff / prevBar.close) * 100;
                        changeHtml = `<b>Δ:</b> ${diff >= 0 ? '+' : ''}${diff.toFixed(2)} (${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%)`;
                    }
                    tooltipEl.innerHTML = `<span style="color:${mainColor}"><b>O:</b> ${bar.open.toFixed(2)}</span> &nbsp; <span style="color:${mainColor}"><b>H:</b> ${bar.high.toFixed(2)}</span> &nbsp; <span style="color:${mainColor}"><b>L:</b> ${bar.low.toFixed(2)}</span> &nbsp; <span style="color:${mainColor}"><b>C:</b> ${bar.close.toFixed(2)}</span> &nbsp; <span style="color:${mainColor}">${changeHtml}</span> &nbsp; <span style="color:${mainColor}"><b>Vol:</b> ${fmtVol(bar.volume)}</span>`;
                    tooltipEl.style.display = 'block';
                }
            }

            // ── Oscillator hover value (append inline after OHLC) ──
            if (tooltipEl && oscillatorData?.data?.length && isOn('oscillator')) {
                const oscRow = oscillatorData.data.find(r => r.date === dateStr);
                if (oscRow) {
                    const primaryLine = oscillatorData.lines?.find(l => l.isPrimary) || oscillatorData.lines?.find(l => l.column);
                    if (primaryLine?.column) {
                        const val = oscRow[primaryLine.column];
                        if (val != null) {
                            tooltipEl.innerHTML += ` &nbsp; <span style="color:#F5C542"><b>${primaryLine.label || primaryLine.column.toUpperCase()}:</b> ${val.toFixed(2)}</span>`;
                        }
                    }
                }
            }
        });

        // Restore saved x-axis range (from tab switch) or fit all content
        if (savedVisibleRange) {
            const rangeToRestore = savedVisibleRange;
            const priceToRestore = savedPriceRange;
            try { chart.timeScale().setVisibleLogicalRange(rangeToRestore); } catch (e) { }
            // Re-apply after chart settles (series-update effect may cause drift)
            requestAnimationFrame(() => {
                if (chartRef.current !== chart) return;
                try { chart.timeScale().setVisibleLogicalRange(rangeToRestore); } catch (e) { }
                // Also re-apply y-axis
                if (priceToRestore) {
                    try {
                        let dH = -Infinity, dL = Infinity;
                        candles.forEach(c => { if (c.high > dH) dH = c.high; if (c.low < dL) dL = c.low; });
                        const fR = priceToRestore.top - priceToRestore.bottom;
                        if (fR > 0) {
                            chart.priceScale('right').applyOptions({
                                autoScale: false,
                                scaleMargins: {
                                    top: Math.max(0, (priceToRestore.top - dH) / fR),
                                    bottom: Math.max(0, (dL - priceToRestore.bottom) / fR),
                                },
                            });
                        }
                    } catch (e) { }
                }
            });
        } else if (activeTimeframe !== 'ALL' && candles.length) {
            const tf = TIMEFRAMES.find(t => t.label === activeTimeframe);
            if (tf) {
                const from = new Date();
                from.setDate(from.getDate() - tf.days);
                chart.timeScale().setVisibleRange({
                    from: from.toISOString().slice(0, 10),
                    to: candles[candles.length - 1].time,
                });
            }
        } else {
            chart.timeScale().fitContent();
        }

        // Restore saved y-axis (price scale) range (immediate application)
        if (savedPriceRange) {
            try {
                let dataHigh = -Infinity, dataLow = Infinity;
                candles.forEach(c => {
                    if (c.high > dataHigh) dataHigh = c.high;
                    if (c.low < dataLow) dataLow = c.low;
                });
                const priceTop = savedPriceRange.top;
                const priceBottom = savedPriceRange.bottom;
                const fullRange = priceTop - priceBottom;
                if (fullRange > 0) {
                    const marginTop = (priceTop - dataHigh) / fullRange;
                    const marginBottom = (dataLow - priceBottom) / fullRange;
                    chart.priceScale('right').applyOptions({
                        autoScale: false,
                        scaleMargins: {
                            top: Math.max(0, marginTop),
                            bottom: Math.max(0, marginBottom),
                        },
                    });
                }
            } catch (e) { }
        }

        const obs = new ResizeObserver(() => { if (priceRef.current) chart.applyOptions({ width: priceRef.current.clientWidth }); });
        obs.observe(priceRef.current);
        return () => {
            // Save visible range before destroying (x-axis + y-axis)
            try { savedVisibleRange = chart.timeScale().getVisibleLogicalRange(); } catch (e) { }
            // Save y-axis price range using coordinateToPrice
            try {
                const cs = candleSeriesRef.current;
                const h = priceRef.current?.clientHeight || 0;
                if (cs && h > 0) {
                    const topPrice = cs.coordinateToPrice(0);
                    const bottomPrice = cs.coordinateToPrice(h);
                    if (topPrice != null && bottomPrice != null && topPrice !== bottomPrice) {
                        savedPriceRange = { top: topPrice, bottom: bottomPrice };
                    }
                }
            } catch (e) { savedPriceRange = null; }
            // Clear dynamic series refs before chart removal
            dynamicSeriesRef.current = [];
            priceLinesRef.current = [];
            obs.disconnect(); chart.remove(); chartRef.current = null; candleSeriesRef.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [priceData]);

    // ─── Theme toggle effect (applies options without destroying the chart) ───
    useEffect(() => {
        if (!chartRef.current) return;
        const currentTheme = nightMode ? CHART_THEME.dark : CHART_THEME.light;
        chartRef.current.applyOptions({
            layout: { background: { color: currentTheme.bg }, textColor: currentTheme.text },
            grid: { vertLines: { color: currentTheme.grid }, horzLines: { color: currentTheme.grid } },
            crosshair: { vertLine: { color: currentTheme.crosshair }, horzLine: { color: currentTheme.crosshair } },
            timeScale: { borderColor: currentTheme.border },
        });
    }, [nightMode]);

    // ─── Series update effect (toggles, overlays, markers — no chart recreation) ───
    useEffect(() => {
        const chart = chartRef.current;
        const candleSeries = candleSeriesRef.current;
        if (!chart || !candleSeries || !priceData?.length) return;

        // Remove all previously added dynamic series
        dynamicSeriesRef.current.forEach(s => {
            try { chart.removeSeries(s); } catch (e) { }
        });
        dynamicSeriesRef.current = [];

        // Remove old price lines from candle series
        priceLinesRef.current.forEach(pl => {
            try { candleSeries.removePriceLine(pl); } catch (e) { }
        });
        priceLinesRef.current = [];

        const candles = priceData.map(d => ({
            time: toDay(d.date), open: d.open, high: d.high, low: d.low, close: d.close,
        }));

        // Volume
        if (isOn('volume')) {
            const volSeries = chart.addHistogramSeries({
                priceFormat: { type: 'volume' }, priceScaleId: 'vol',
            });
            volSeries.priceScale().applyOptions({ scaleMargins: { top: 0.80, bottom: 0.02 } });
            volSeries.setData(priceData.map(d => ({
                time: toDay(d.date), value: d.volume || 0,
                color: d.close >= d.open ? 'rgba(38,166,154,0.45)' : 'rgba(239,83,80,0.45)',
            })));
            dynamicSeriesRef.current.push(volSeries);
        }

        // BUY/SELL markers
        const markers = [];
        if (isOn('buy') && signals?.length) {
            signals.filter(s => s.signal === 'BUY').forEach(s => {
                markers.push({ time: toDay(s.date), position: 'belowBar', color: '#00FF9C', shape: 'arrowUp', text: 'BUY', size: 1 });
            });
        }
        if (isOn('sell') && signals?.length) {
            signals.filter(s => s.signal === 'SELL').forEach(s => {
                markers.push({ time: toDay(s.date), position: 'aboveBar', color: '#FF2E63', shape: 'arrowDown', text: 'SELL', size: 1 });
            });
        }
        if (isOn('openTrade') && openTrade?.entry_date) {
            markers.push({ time: toDay(openTrade.entry_date), position: 'belowBar', color: '#FFD166', shape: 'arrowUp', text: 'OPEN', size: 1.5 });
        }
        markers.sort((a, b) => a.time < b.time ? -1 : a.time > b.time ? 1 : 0);
        candleSeries.setMarkers(markers);

        // Trade lines (entry → exit)
        if (isOn('tradeLines') && trades?.length) {
            trades.forEach(t => {
                if (!t.entry_date || !t.exit_date) return;
                const isProfit = t.exit_price >= t.entry_price;
                const lineSeries = chart.addLineSeries({
                    color: isProfit ? '#00FF9C' : '#FF2E63', lineWidth: 2,
                    priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
                });
                lineSeries.setData([
                    { time: toDay(t.entry_date), value: t.entry_price },
                    { time: toDay(t.exit_date), value: t.exit_price },
                ]);
                dynamicSeriesRef.current.push(lineSeries);
            });
        }

        // Open trade line
        if (isOn('openTrade') && openTrade?.entry_date && candles.length) {
            const lastCandle = candles[candles.length - 1];
            const openLine = chart.addLineSeries({
                color: '#FFD166', lineWidth: 2, lineStyle: LineStyle.Dashed,
                priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
            });
            openLine.setData([
                { time: toDay(openTrade.entry_date), value: openTrade.entry_price },
                { time: lastCandle.time, value: lastCandle.close },
            ]);
            dynamicSeriesRef.current.push(openLine);
        }

        // Price levels
        if (isOn('priceLevels') && candles.length) {
            const ltpLine = candleSeries.createPriceLine({
                price: candles[candles.length - 1].close, color: '#3DA5FF', lineWidth: 1,
                lineStyle: LineStyle.Dotted, axisLabelVisible: true, title: 'LTP',
            });
            priceLinesRef.current.push(ltpLine);
            const maxPrice = Math.max(...candles.map(c => c.high));
            const minPrice = Math.min(...candles.map(c => c.low));
            const highLine = candleSeries.createPriceLine({ price: maxPrice, color: '#10b981', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: `High ₹${maxPrice.toFixed(2)}` });
            const lowLine = candleSeries.createPriceLine({ price: minPrice, color: '#ef4444', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: `Low ₹${minPrice.toFixed(2)}` });
            priceLinesRef.current.push(highLine, lowLine);
        } else if (candles.length) {
            const ltpLine = candleSeries.createPriceLine({
                price: candles[candles.length - 1].close, color: '#EF5350', lineWidth: 1,
                lineStyle: LineStyle.Solid, axisLabelVisible: true, title: 'LTP',
            });
            priceLinesRef.current.push(ltpLine);
        }

        // Strategy overlays (SMA/EMA/Bollinger)
        if (isOn('overlay') && overlayData?.data?.length) {
            overlayData.overlays.forEach(ov => {
                const series = chart.addLineSeries({
                    color: ov.color, lineWidth: 1.5,
                    priceLineVisible: isOn('priceLevels'), lastValueVisible: isOn('priceLevels'),
                    crosshairMarkerVisible: false, priceLineWidth: 1,
                });
                series.setData(overlayData.data.map(d => ({ time: toDay(d.date), value: d[ov.column] })).filter(d => d.value != null));
                dynamicSeriesRef.current.push(series);
            });
        }

        // Oscillator series (rsi, macd, etc.)
        if (showOsc && oscillatorData?.data?.length) {
            const oscRange = oscillatorData.range || [0, 100];

            oscillatorData.lines.forEach(line => {
                if (line.column) {
                    const series = chart.addLineSeries({
                        color: line.color, lineWidth: line.isPrimary ? 2 : 1.5,
                        priceScaleId: 'osc', // Overlay scale (renders on right)
                        lastValueVisible: true, priceLineVisible: true,
                        crosshairMarkerVisible: true,
                        title: line.label || line.column,
                    });
                    series.setData(
                        oscillatorData.data
                            .map(d => ({ time: toDay(d.date), value: d[line.column] }))
                            .filter(d => d.value != null)
                    );
                    dynamicSeriesRef.current.push(series);
                } else if (line.level != null && isOn('priceLevels')) {
                    const lvlSeries = chart.addLineSeries({
                        color: line.color, lineWidth: 1, lineStyle: LineStyle.Dashed,
                        priceScaleId: 'osc', // Overlay scale (renders on right)
                        lastValueVisible: true, priceLineVisible: true,
                        crosshairMarkerVisible: false,
                        title: line.label || `Level ${line.level}`,
                    });
                    if (oscillatorData.data.length >= 2) {
                        lvlSeries.setData([
                            { time: toDay(oscillatorData.data[0].date), value: line.level },
                            { time: toDay(oscillatorData.data[oscillatorData.data.length - 1].date), value: line.level },
                        ]);
                    }
                    dynamicSeriesRef.current.push(lvlSeries);
                }
            });

            // Now that series are added, configure the 'osc' overlay scale
            chart.priceScale('osc').applyOptions({
                scaleMargins: { top: 0.8, bottom: 0.02 },
                autoScale: true,
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [priceData, signals, trades, openTrade, overlayData, toggles, showAll, showOsc, oscillatorData]);

    // ─── Timeframe effect (applies timeframe to existing chart without recreation) ───
    useEffect(() => {
        const chart = chartRef.current;
        if (!chart || !priceData?.length) return;

        const timeframeChanged = activeTimeframe !== prevTimeframeRef.current;
        prevTimeframeRef.current = activeTimeframe;

        if (!timeframeChanged) return; // Only act when timeframe actually changes

        const candles = priceData.map(d => ({ time: toDay(d.date) }));

        if (activeTimeframe !== 'ALL' && candles.length) {
            const tf = TIMEFRAMES.find(t => t.label === activeTimeframe);
            if (tf) {
                const from = new Date();
                from.setDate(from.getDate() - tf.days);
                chart.timeScale().setVisibleRange({
                    from: from.toISOString().slice(0, 10),
                    to: candles[candles.length - 1].time,
                });
            }
        } else {
            chart.timeScale().fitContent();
        }

        // Clear saved ranges when timeframe changes
        savedVisibleRange = null;
        savedPriceRange = null;
        chart.priceScale('right').applyOptions({ autoScale: true });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTimeframe]);

    // Removed second oscillator component logic

    if (!priceData?.length) {
        return <div className="empty-state" style={{ flex: 1 }}><p className="empty-state-text">Run a backtest to see the chart</p></div>;
    }

    return (
        <div ref={wrapperRef} style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {/* Controls Row */}
            <div className="chart-controls">
                <div className="chart-controls-left">
                    <label className="chart-toggle">
                        <input type="checkbox" checked={showAll} onChange={() => setShowAll(!showAll)} />
                        <span>Show All</span>
                    </label>
                    <span className="chart-controls-divider" />
                    {allToggles.map(t => (
                        <label key={t.key} className={`chart-toggle ${!showAll ? 'chart-toggle--muted' : ''}`}>
                            <input type="checkbox" checked={toggles[t.key]} onChange={() => toggle(t.key)} disabled={!showAll} />
                            <span>{t.label}</span>
                        </label>
                    ))}
                    <span className="chart-controls-divider" />
                    <label className="chart-toggle">
                        <input type="checkbox" checked={nightMode} onChange={() => setNightMode(!nightMode)} />
                        <span>🌙 Night</span>
                    </label>
                </div>
                <div className="chart-controls-right">
                    {TIMEFRAMES.map(tf => (
                        <button key={tf.label}
                            className={`chart-tf-btn ${activeTimeframe === tf.label ? 'chart-tf-btn--active' : ''}`}
                            onClick={() => { savedVisibleRange = null; setActiveTimeframe(tf.label); }}>
                            {tf.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Price Chart */}
            <div className={`chart-panel fade-in ${fullscreenPanel === 'price' ? 'chart-panel--fullscreen' : ''}`} style={{ position: 'relative', marginBottom: 0 }}>
                <div className="chart-panel-header">
                    <span className="chart-panel-title">Price Action & Strategy Overlay</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        {overlayData && overlayData.overlays.map(ov => (
                            <span key={ov.column} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                <span style={{ width: 10, height: 3, borderRadius: 2, background: ov.color, display: 'inline-block' }} />
                                {ov.label}
                            </span>
                        ))}
                        {/* Zoom Controls */}
                        <div className="chart-zoom-controls">
                            <button className="chart-zoom-btn" title="Zoom In" onClick={() => {
                                if (!chartRef.current) return;
                                const r = chartRef.current.timeScale().getVisibleLogicalRange();
                                if (!r) return;
                                const c = (r.from + r.to) / 2, h = (r.to - r.from) / 2 * 0.75;
                                chartRef.current.timeScale().setVisibleLogicalRange({ from: c - h, to: c + h });
                            }}>＋</button>
                            <button className="chart-zoom-btn" title="Zoom Out" onClick={() => {
                                if (!chartRef.current) return;
                                const r = chartRef.current.timeScale().getVisibleLogicalRange();
                                if (!r) return;
                                const c = (r.from + r.to) / 2, h = (r.to - r.from) / 2 * 1.35;
                                chartRef.current.timeScale().setVisibleLogicalRange({ from: c - h, to: c + h });
                            }}>ー</button>
                            <button className="chart-zoom-btn" title="Reset View" onClick={() => {
                                savedVisibleRange = null;
                                savedPriceRange = null;
                                prevTimeframeRef.current = 'ALL';
                                if (chartRef.current) {
                                    chartRef.current.timeScale().fitContent();
                                    chartRef.current.priceScale('right').applyOptions({
                                        autoScale: true,
                                        scaleMargins: { top: 0.06, bottom: 0.04 },
                                    });
                                }
                                setActiveTimeframe('ALL');
                            }}>⟳</button>
                        </div>
                        {/* Go To Date */}
                        <div style={{ position: 'relative' }}>
                            <button className="chart-zoom-btn" title="Go to Date" style={{ fontSize: '0.7rem', width: 'auto', padding: '0 8px' }}
                                onClick={() => { setShowGoTo(v => !v); setGoToDate(''); }}>
                                📅
                            </button>
                            {showGoTo && (
                                <div className="chart-goto-popup">
                                    <label style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Go to Date</label>
                                    <input
                                        type="date"
                                        className="chart-goto-input"
                                        value={goToDate}
                                        onChange={e => setGoToDate(e.target.value)}
                                        autoFocus
                                        onKeyDown={e => {
                                            if (e.key === 'Enter' && goToDate) { navigateToDate(goToDate); setShowGoTo(false); }
                                            if (e.key === 'Escape') setShowGoTo(false);
                                        }}
                                    />
                                    <div style={{ display: 'flex', gap: 4 }}>
                                        <button className="chart-goto-ok" onClick={() => {
                                            if (goToDate) { navigateToDate(goToDate); setShowGoTo(false); }
                                        }}>Go</button>
                                        <button className="chart-goto-cancel" onClick={() => setShowGoTo(false)}>✕</button>
                                    </div>
                                </div>
                            )}
                        </div>
                        {/* Fullscreen Toggle */}
                        <button className="chart-zoom-btn" title={fullscreenPanel === 'price' ? 'Exit Fullscreen' : 'Fullscreen'}
                            onClick={() => toggleFullscreen('price')}>
                            {fullscreenPanel === 'price' ? '⊗' : '⛶'}
                        </button>
                    </div>
                </div>
                {/* OHLC Bar */}
                <div ref={tooltipRef} className="chart-ohlc-bar" style={{ display: 'none' }} />
                {/* Oscillator hover value - no longer needed, value is inline with OHLC */}
                <div className="chart-container" ref={priceRef}
                    style={{ height: fullscreenPanel === 'price' ? 'calc(100vh - 90px)' : 600 }}
                    onDoubleClick={() => toggleFullscreen('price')} />
            </div>
        </div>
    );
}
