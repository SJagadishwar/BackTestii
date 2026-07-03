import { useRef, useEffect, useState, useCallback } from 'react';
import { createChart } from 'lightweight-charts';

const toDay = (d) => d ? d.split('T')[0] : d;

function fmtNum(v) {
    if (v == null) return '--';
    if (Math.abs(v) >= 1e7) return '₹' + (v / 1e7).toFixed(2) + ' Cr';
    if (Math.abs(v) >= 1e5) return '₹' + (v / 1e5).toFixed(2) + ' L';
    return '₹' + v.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

export default function PerformanceTab({ equityCurve, priceData, signals, trades }) {
    const eqRef = useRef(null);
    const eqChartRef = useRef(null);
    const eqTooltipRef = useRef(null);
    const priceRef = useRef(null);
    const priceChartRef = useRef(null);

    // Display controls (matching Streamlit)
    const [showPosition, setShowPosition] = useState(true);
    const [showEntries, setShowEntries] = useState(true);
    const [showExits, setShowExits] = useState(true);
    const [positionOpacity, setPositionOpacity] = useState(0.08);

    // Fullscreen state
    const [fullscreenPanel, setFullscreenPanel] = useState(null); // null | 'equity' | 'price'

    const toggleFullscreen = useCallback((panel) => {
        setFullscreenPanel(prev => {
            const next = prev === panel ? null : panel;
            setTimeout(() => {
                if (eqChartRef.current && eqRef.current) {
                    eqChartRef.current.applyOptions({ width: eqRef.current.clientWidth, height: eqRef.current.clientHeight });
                }
                if (priceChartRef.current && priceRef.current) {
                    priceChartRef.current.applyOptions({ width: priceRef.current.clientWidth, height: priceRef.current.clientHeight });
                }
            }, 50);
            return next;
        });
    }, []);

    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape' && fullscreenPanel) toggleFullscreen(fullscreenPanel); };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [fullscreenPanel, toggleFullscreen]);

    // Equity + Drawdown chart
    useEffect(() => {
        if (!eqRef.current || !equityCurve?.length) return;
        if (eqChartRef.current) { eqChartRef.current.remove(); eqChartRef.current = null; }

        const chart = createChart(eqRef.current, {
            layout: { background: { color: 'transparent' }, textColor: '#8b949e', fontFamily: "'Inter', sans-serif", fontSize: 11 },
            grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
            crosshair: {
                vertLine: { color: 'rgba(59,130,246,0.3)', labelBackgroundColor: '#3b82f6' },
                horzLine: { color: 'rgba(59,130,246,0.3)', labelVisible: false },
            },
            timeScale: { borderColor: 'rgba(255,255,255,0.06)' },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        });
        eqChartRef.current = chart;

        const eqSeries = chart.addAreaSeries({
            lineColor: '#3b82f6', lineWidth: 2,
            topColor: 'rgba(59,130,246,0.2)', bottomColor: 'rgba(59,130,246,0.02)',
            lastValueVisible: true, crosshairMarkerVisible: true,
        });
        const eqData = equityCurve.map(d => ({ time: toDay(d.date), value: d.equity }));
        eqSeries.setData(eqData);

        // Drawdown
        const peak = [];
        let maxEq = 0;
        for (const d of equityCurve) {
            maxEq = Math.max(maxEq, d.equity);
            const dd = ((d.equity - maxEq) / maxEq) * 100;
            peak.push({ time: toDay(d.date), value: dd });
        }

        const ddSeries = chart.addAreaSeries({
            lineColor: '#ef4444', lineWidth: 1,
            topColor: 'rgba(239,68,68,0.15)', bottomColor: 'rgba(239,68,68,0.02)',
            priceScaleId: 'dd',
            lastValueVisible: true, crosshairMarkerVisible: true,
        });
        chart.priceScale('dd').applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
            invertScale: true,
        });
        // Add margins to the main equity right scale to keep it mostly above the drawdown
        chart.priceScale('right').applyOptions({
            scaleMargins: { top: 0.1, bottom: 0.25 }
        });
        ddSeries.setData(peak);

        // Build lookup for hover tooltip
        const eqLookup = {};
        eqData.forEach((d, i) => { eqLookup[d.time] = { equity: d.value, dd: peak[i]?.value }; });

        // Hover tooltip — show equity + drawdown at top-left
        chart.subscribeCrosshairMove(param => {
            const tip = eqTooltipRef.current;
            if (!tip) return;
            if (!param || !param.time) { tip.style.display = 'none'; return; }
            const timeStr = typeof param.time === 'string' ? param.time
                : `${param.time.year}-${String(param.time.month).padStart(2, '0')}-${String(param.time.day).padStart(2, '0')}`;
            const row = eqLookup[timeStr];
            if (!row) { tip.style.display = 'none'; return; }
            tip.innerHTML = `<span style="color:#3b82f6">● Equity: <b>${fmtNum(row.equity)}</b></span> &nbsp;&nbsp; <span style="color:#ef4444">● Drawdown: <b>${row.dd != null ? row.dd.toFixed(2) + '%' : '--'}</b></span>`;
            tip.style.display = 'block';
        });

        chart.timeScale().fitContent();

        const obs = new ResizeObserver(() => {
            if (eqRef.current && eqChartRef.current) {
                eqChartRef.current.applyOptions({
                    width: eqRef.current.clientWidth,
                    height: eqRef.current.clientHeight
                });
            }
        });
        obs.observe(eqRef.current);
        return () => { obs.disconnect(); chart.remove(); eqChartRef.current = null; };
    }, [equityCurve, fullscreenPanel]);

    // Price + Entry/Exit markers + In-position shading
    useEffect(() => {
        if (!priceRef.current || !priceData?.length) return;
        if (priceChartRef.current) { priceChartRef.current.remove(); priceChartRef.current = null; }

        const chart = createChart(priceRef.current, {
            layout: { background: { color: 'transparent' }, textColor: '#8b949e', fontFamily: "'Inter', sans-serif", fontSize: 11 },
            grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
            crosshair: { vertLine: { color: 'rgba(59,130,246,0.3)', labelBackgroundColor: '#3b82f6' }, horzLine: { color: 'rgba(59,130,246,0.3)', labelBackgroundColor: '#3b82f6' } },
            timeScale: { borderColor: 'rgba(255,255,255,0.06)' },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        });
        priceChartRef.current = chart;

        const lineSeries = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 2 });
        const pricePoints = priceData.map(d => ({ time: toDay(d.date), value: d.close }));
        lineSeries.setData(pricePoints);

        // In-position shading (green area during active trades)
        if (showPosition && trades?.length) {
            // Build a map of dates → price for quick access
            const priceMap = {};
            priceData.forEach(d => { priceMap[toDay(d.date)] = d.close; });

            // Build in-position periods from trades
            trades.forEach(trade => {
                if (!trade.entry_date || !trade.exit_date) return;
                const entryDay = toDay(trade.entry_date);
                const exitDay = toDay(trade.exit_date);

                // Collect price points during this trade
                const posPoints = priceData
                    .filter(d => {
                        const day = toDay(d.date);
                        return day >= entryDay && day <= exitDay;
                    })
                    .map(d => ({ time: toDay(d.date), value: d.close }));

                if (posPoints.length >= 2) {
                    const green = Math.round(positionOpacity * 255);
                    const posSeries = chart.addAreaSeries({
                        lineColor: `rgba(16,185,129,${Math.min(positionOpacity * 3, 0.6)})`,
                        lineWidth: 0,
                        topColor: `rgba(16,185,129,${positionOpacity})`,
                        bottomColor: `rgba(16,185,129,${positionOpacity * 0.3})`,
                        lastValueVisible: false,
                        priceLineVisible: false,
                        crosshairMarkerVisible: false,
                    });
                    posSeries.setData(posPoints);
                }
            });
        }

        // Trade entry/exit markers
        const markers = [];
        if (trades?.length) {
            if (showEntries) {
                trades.forEach(t => {
                    if (t.entry_date) markers.push({ time: toDay(t.entry_date), position: 'belowBar', color: '#10b981', shape: 'arrowUp', text: 'Entry', size: 1 });
                });
            }
            if (showExits) {
                trades.forEach(t => {
                    if (t.exit_date) markers.push({ time: toDay(t.exit_date), position: 'aboveBar', color: '#ef4444', shape: 'arrowDown', text: 'Exit', size: 1 });
                });
            }
            markers.sort((a, b) => a.time < b.time ? -1 : a.time > b.time ? 1 : 0);
            lineSeries.setMarkers(markers);
        }

        chart.timeScale().fitContent();
        const obs = new ResizeObserver(() => {
            if (priceRef.current && priceChartRef.current) {
                priceChartRef.current.applyOptions({
                    width: priceRef.current.clientWidth,
                    height: priceRef.current.clientHeight
                });
            }
        });
        obs.observe(priceRef.current);
        return () => { obs.disconnect(); chart.remove(); priceChartRef.current = null; };
    }, [priceData, trades, showPosition, showEntries, showExits, positionOpacity, fullscreenPanel]);

    if (!equityCurve?.length) {
        return <div className="empty-state" style={{ flex: 1 }}><p className="empty-state-text">Run a backtest to see performance</p></div>;
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className={`chart-panel fade-in ${fullscreenPanel === 'equity' ? 'chart-panel--fullscreen' : ''}`} style={{ position: 'relative' }}>
                <div className="chart-panel-header">
                    <span className="chart-panel-title">Equity Curve & Drawdown</span>
                    <button className="chart-zoom-btn" title={fullscreenPanel === 'equity' ? 'Exit Fullscreen' : 'Fullscreen'}
                        onClick={() => toggleFullscreen('equity')}>
                        {fullscreenPanel === 'equity' ? '⊗' : '⛶'}
                    </button>
                </div>
                <div ref={eqTooltipRef} style={{
                    position: 'absolute', top: 44, left: 16, zIndex: 6,
                    fontFamily: "var(--font-mono)", fontSize: '0.78rem',
                    background: 'none', padding: '0 12px',
                    pointerEvents: 'none', display: 'none', whiteSpace: 'nowrap',
                }} />
                <div className="chart-container" ref={eqRef}
                    style={{ height: fullscreenPanel === 'equity' ? 'calc(100vh - 70px)' : 350 }}
                    onDoubleClick={() => toggleFullscreen('equity')} />
            </div>

            {priceData?.length > 0 && (
                <>
                    <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', margin: 0 }}>📍 Strategy Signal Verification</h3>
                    <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0 }}>🎛️ Chart Display Controls</h4>

                    <div className="perf-controls">
                        <label className="chart-toggle">
                            <input type="checkbox" checked={showPosition} onChange={() => setShowPosition(!showPosition)} />
                            <span>Show In-Position</span>
                        </label>
                        <label className="chart-toggle">
                            <input type="checkbox" checked={showEntries} onChange={() => setShowEntries(!showEntries)} />
                            <span>Show Entry Markers</span>
                        </label>
                        <label className="chart-toggle">
                            <input type="checkbox" checked={showExits} onChange={() => setShowExits(!showExits)} />
                            <span>Show Exit Markers</span>
                        </label>
                        <div className="perf-slider">
                            <span>Position Opacity</span>
                            <input type="range" min="0.05" max="0.3" step="0.01" value={positionOpacity}
                                onChange={e => setPositionOpacity(Number(e.target.value))} />
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{positionOpacity.toFixed(2)}</span>
                        </div>
                    </div>

                    <div className={`chart-panel fade-in ${fullscreenPanel === 'price' ? 'chart-panel--fullscreen' : ''}`}>
                        <div className="chart-panel-header">
                            <span className="chart-panel-title">Price & Trade Signals</span>
                            <button className="chart-zoom-btn" title={fullscreenPanel === 'price' ? 'Exit Fullscreen' : 'Fullscreen'}
                                onClick={() => toggleFullscreen('price')}>
                                {fullscreenPanel === 'price' ? '⊗' : '⛶'}
                            </button>
                        </div>
                        <div className="chart-container" ref={priceRef}
                            style={{ height: fullscreenPanel === 'price' ? 'calc(100vh - 70px)' : 350 }}
                            onDoubleClick={() => toggleFullscreen('price')} />
                    </div>
                </>
            )}
        </div>
    );
}
