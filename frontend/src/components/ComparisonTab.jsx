import { useRef, useEffect, useState } from 'react';
import { runComparison } from '../api/client';
import { createChart } from 'lightweight-charts';
import { GitCompare, Maximize2, Minimize2, X } from 'lucide-react';

const toDay = (d) => d ? d.split('T')[0] : d;
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1'];

function fmt(val, dec = 2) {
    if (val == null) return '—';
    return Number(val).toFixed(dec);
}

export default function ComparisonTab({
    ticker, assetType, startDate, endDate, capital,
    comparisonData: data, setComparisonData: setData,
    comparisonSelected: selected, setComparisonSelected: setSelected,
}) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [sortBy, setSortBy] = useState('CAGR (%)');
    const [isFullscreen, setIsFullscreen] = useState(false);
    const chartRef = useRef(null);
    const chartInstanceRef = useRef(null);
    const chartWrapRef = useRef(null);

    const handleRun = async () => {
        if (!ticker) return;
        setLoading(true); setError('');
        try {
            const result = await runComparison({ ticker, assetType, startDate, endDate, capital });
            setData(result);
            const top3 = result.comparison.slice(0, 3).map(r => r.Strategy);
            setSelected(top3);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    };

    const handleClear = () => {
        setData(null);
        setSelected([]);
        setError('');
    };

    // Fullscreen toggle
    const toggleFullscreen = () => {
        if (!chartWrapRef.current) return;
        if (!document.fullscreenElement) {
            chartWrapRef.current.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
    };

    useEffect(() => {
        const onFsChange = () => setIsFullscreen(!!document.fullscreenElement);
        document.addEventListener('fullscreenchange', onFsChange);
        return () => document.removeEventListener('fullscreenchange', onFsChange);
    }, []);

    // Equity overlay chart
    useEffect(() => {
        if (!chartRef.current || !data?.equity_curves || !selected.length) return;
        if (chartInstanceRef.current) { chartInstanceRef.current.remove(); chartInstanceRef.current = null; }

        const chart = createChart(chartRef.current, {
            layout: { background: { color: 'transparent' }, textColor: '#8b949e', fontFamily: "'Inter', sans-serif", fontSize: 11 },
            grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
            timeScale: { borderColor: 'rgba(255,255,255,0.06)' },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        });
        chartInstanceRef.current = chart;

        selected.forEach((name, i) => {
            const curve = data.equity_curves[name];
            if (!curve) return;
            const series = chart.addLineSeries({ color: COLORS[i % COLORS.length], lineWidth: 2, title: name });
            series.setData(curve.map(d => ({ time: toDay(d.date), value: d.equity })));
        });

        chart.timeScale().fitContent();
        const obs = new ResizeObserver(() => {
            if (chartRef.current && chartInstanceRef.current) {
                chartInstanceRef.current.applyOptions({
                    width: chartRef.current.clientWidth,
                    height: chartRef.current.clientHeight
                });
            }
        });
        obs.observe(chartRef.current);
        return () => { obs.disconnect(); chart.remove(); chartInstanceRef.current = null; };
    }, [data, selected]);

    const sorted = data?.comparison ? [...data.comparison].sort((a, b) => {
        const av = a[sortBy], bv = b[sortBy];
        return sortBy === 'Max Drawdown (%)' ? av - bv : bv - av;
    }) : [];

    const toggleSelect = (name) => {
        setSelected(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Toolbar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn-run" style={{ width: 'auto', padding: '8px 20px' }} onClick={handleRun} disabled={loading || !ticker}>
                    {loading ? <><span className="spinner" /> Comparing…</> : '⚡ Run Comparison'}
                </button>

                {data && (
                    <button
                        onClick={handleClear}
                        style={{
                            display: 'flex', alignItems: 'center', gap: 6,
                            padding: '8px 16px', borderRadius: 'var(--radius-sm)',
                            background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                            color: 'var(--color-loss)', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                        }}
                    >
                        <X size={14} /> Clear
                    </button>
                )}

                <select className="form-select" style={{ width: 200 }} value={sortBy} onChange={e => setSortBy(e.target.value)}>
                    <option value="CAGR (%)">Sort by CAGR</option>
                    <option value="Total Return (%)">Sort by Total Return</option>
                    <option value="Max Drawdown (%)">Sort by Max Drawdown</option>
                </select>
            </div>

            {error && <div style={{ color: 'var(--color-loss)', fontSize: '0.85rem' }}>{error}</div>}

            {sorted.length > 0 && (
                <>
                    {/* Results table */}
                    <div className="trades-panel fade-in">
                        <div className="trades-header">
                            <span className="trades-title">Strategy Comparison</span>
                            <span className="trades-count">{sorted.length} strategies</span>
                        </div>
                        <div className="trades-table-wrap">
                            <table className="trades-table">
                                <thead>
                                    <tr>
                                        <th>Rank</th>
                                        <th>Strategy</th>
                                        <th>Total Return %</th>
                                        <th>CAGR %</th>
                                        <th>Max DD %</th>
                                        <th>DD Days</th>
                                        <th>Show</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sorted.map((row, i) => (
                                        <tr key={row.Strategy}>
                                            <td>{i + 1}</td>
                                            <td style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>{row.Strategy}</td>
                                            <td className={row['Total Return (%)'] >= 0 ? 'profit' : 'loss'}>{fmt(row['Total Return (%)'])}</td>
                                            <td className={row['CAGR (%)'] >= 0 ? 'profit' : 'loss'}>{fmt(row['CAGR (%)'])}</td>
                                            <td className="loss">{fmt(row['Max Drawdown (%)'])}</td>
                                            <td>{fmt(row['Max Drawdown Duration (days)'], 0)}</td>
                                            <td>
                                                <input type="checkbox" checked={selected.includes(row.Strategy)} onChange={() => toggleSelect(row.Strategy)} />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Equity curve chart */}
                    <div className="chart-panel fade-in" ref={chartWrapRef}
                        style={isFullscreen ? { background: 'var(--bg-base)', display: 'flex', flexDirection: 'column', height: '100%' } : {}}>
                        <div className="chart-panel-header">
                            <span className="chart-panel-title">Equity Curve Overlay</span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{selected.length} selected</span>
                                <button
                                    onClick={toggleFullscreen}
                                    title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                                    style={{
                                        background: 'none', border: '1px solid var(--border-default)',
                                        borderRadius: 'var(--radius-sm)', padding: '4px 6px',
                                        color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center',
                                        transition: 'color 0.15s, border-color 0.15s',
                                    }}
                                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--accent-blue)'; }}
                                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'var(--border-default)'; }}
                                >
                                    {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                                </button>
                            </div>
                        </div>
                        <div className="chart-container" ref={chartRef}
                            onDoubleClick={toggleFullscreen}
                            title="Double-click to toggle fullscreen"
                            style={{ height: isFullscreen ? 'calc(100vh - 60px)' : 380, cursor: 'crosshair' }} />
                    </div>
                </>
            )}

            {!data && !loading && (
                <div className="empty-state" style={{ flex: 1 }}>
                    <GitCompare size={48} className="empty-state-icon" />
                    <p className="empty-state-text">Click "Run Comparison" to compare all strategies with default parameters</p>
                </div>
            )}
        </div>
    );
}
