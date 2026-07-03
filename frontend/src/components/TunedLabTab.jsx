import { useState, useRef, useEffect } from 'react';
import { runTunedComparison, getStrategies } from '../api/client';
import { createChart } from 'lightweight-charts';
import { FlaskConical, Maximize2, Minimize2 } from 'lucide-react';

const toDay = (d) => d ? d.split('T')[0] : d;
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

function fmt(v, d = 2) { return v == null ? '—' : Number(v).toFixed(d); }

export default function TunedLabTab({ ticker, assetType, startDate, endDate, capital, currentStrategyKey, currentParams, tunedRuns, setTunedRuns, tunedData, setTunedData }) {
    const data = tunedData;
    const setData = setTunedData;
    const [includeBH, setIncludeBH] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [sortBy, setSortBy] = useState('CAGR (%)');
    const [strategies, setStrategies] = useState({});
    const chartRef = useRef(null);
    const chartInstanceRef = useRef(null);
    const chartWrapRef = useRef(null);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const onFsChange = () => setIsFullscreen(!!document.fullscreenElement);
        document.addEventListener('fullscreenchange', onFsChange);
        return () => document.removeEventListener('fullscreenchange', onFsChange);
    }, []);

    const toggleFullscreen = () => {
        if (!chartWrapRef.current) return;
        if (!document.fullscreenElement) {
            chartWrapRef.current.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
    };

    useEffect(() => { getStrategies().then(setStrategies).catch(() => { }); }, []);

    const addCurrent = () => {
        if (!currentStrategyKey || currentStrategyKey === 'BUY_HOLD') return;
        const meta = strategies[currentStrategyKey];
        const label = meta ? `${meta.display_name} (${Object.entries(currentParams || {}).map(([k, v]) => `${k}=${v}`).join(', ')})` : currentStrategyKey;
        if (tunedRuns[label]) return;
        setTunedRuns(prev => ({ ...prev, [label]: { strategy_key: currentStrategyKey, params: currentParams || {} } }));
    };

    const removeTuned = (label) => {
        setTunedRuns(prev => { const n = { ...prev }; delete n[label]; return n; });
    };

    const handleRun = async () => {
        if (!ticker) return;
        setLoading(true); setError('');
        try {
            const result = await runTunedComparison({
                ticker, assetType, startDate, endDate, capital,
                tunedRuns, includeBuyHold: includeBH,
            });
            setData(result);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    };

    // Chart
    useEffect(() => {
        if (!chartRef.current || !data?.equity_curves) return;
        if (chartInstanceRef.current) { chartInstanceRef.current.remove(); chartInstanceRef.current = null; }
        const names = Object.keys(data.equity_curves);
        if (!names.length) return;

        const chart = createChart(chartRef.current, {
            layout: { background: { color: 'transparent' }, textColor: '#8b949e', fontFamily: "'Inter', sans-serif", fontSize: 11 },
            grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
            timeScale: { borderColor: 'rgba(255,255,255,0.06)' },
            rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        });
        chartInstanceRef.current = chart;

        names.forEach((name, i) => {
            const curve = data.equity_curves[name];
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
    }, [data]);

    const sorted = data?.comparison ? [...data.comparison].sort((a, b) => {
        return sortBy === 'Max Drawdown (%)' ? a[sortBy] - b[sortBy] : b[sortBy] - a[sortBy];
    }) : [];

    const runLabels = Object.keys(tunedRuns);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <button className="btn-run" style={{ width: 'auto', padding: '8px 16px', fontSize: '0.8rem' }} onClick={addCurrent}
                    disabled={!currentStrategyKey || currentStrategyKey === 'BUY_HOLD'}>
                    ➕ Add Current Strategy
                </button>
                <button className="btn-run" style={{ width: 'auto', padding: '8px 16px', fontSize: '0.8rem', background: 'var(--bg-elevated)' }}
                    onClick={() => setTunedRuns({})}>🧹 Clear All</button>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <input type="checkbox" checked={includeBH} onChange={e => setIncludeBH(e.target.checked)} /> Include Buy & Hold
                </label>
                <select className="form-select" style={{ width: 180 }} value={sortBy} onChange={e => setSortBy(e.target.value)}>
                    <option value="CAGR (%)">Sort by CAGR</option>
                    <option value="Total Return (%)">Sort by Return</option>
                    <option value="Max Drawdown (%)">Sort by Drawdown</option>
                </select>
            </div>

            {/* Tuned runs list */}
            {runLabels.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {runLabels.map(label => (
                        <div key={label} style={{
                            display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                            borderRadius: 'var(--radius-sm)', padding: '4px 10px', fontSize: '0.75rem', color: 'var(--text-secondary)'
                        }}>
                            {label}
                            <button onClick={() => removeTuned(label)} style={{ background: 'none', border: 'none', color: 'var(--color-loss)', cursor: 'pointer', fontSize: '0.9rem', padding: 0 }}>×</button>
                        </div>
                    ))}
                </div>
            )}

            <button className="btn-run" style={{ width: 200, padding: '10px 20px' }} onClick={handleRun}
                disabled={loading || !ticker || (runLabels.length === 0 && !includeBH)}>
                {loading ? <><span className="spinner" /> Running…</> : '🧪 Run Tuned Comparison'}
            </button>

            {error && <div style={{ color: 'var(--color-loss)', fontSize: '0.85rem' }}>{error}</div>}

            {sorted.length > 0 && (
                <>
                    <div className="trades-panel fade-in">
                        <div className="trades-header">
                            <span className="trades-title">Tuned Strategy Results</span>
                            <span className="trades-count">{sorted.length} configs</span>
                        </div>
                        <div className="trades-table-wrap">
                            <table className="trades-table">
                                <thead>
                                    <tr>
                                        <th>Rank</th><th>Strategy</th><th>Return %</th><th>CAGR %</th><th>Max DD %</th><th>DD Days</th>
                                        <th>Remove</th>
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
                                                {row.Strategy !== 'Buy & Hold' && (
                                                    <button onClick={() => removeTuned(row.Strategy)}
                                                        style={{ background: 'none', border: 'none', color: 'var(--color-loss)', cursor: 'pointer' }}>✕</button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="chart-panel fade-in" ref={chartWrapRef}
                        style={isFullscreen ? { background: 'var(--bg-base)', display: 'flex', flexDirection: 'column', height: '100%' } : {}}>
                        <div className="chart-panel-header">
                            <span className="chart-panel-title">Tuned Equity Curve Overlay</span>
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
                        <div className="chart-container" ref={chartRef}
                            onDoubleClick={toggleFullscreen}
                            title="Double-click to toggle fullscreen"
                            style={{ height: isFullscreen ? 'calc(100vh - 60px)' : 350, cursor: 'crosshair' }} />
                    </div>
                </>
            )}

            {!data && !loading && runLabels.length === 0 && (
                <div className="empty-state" style={{ flex: 1 }}>
                    <FlaskConical size={48} className="empty-state-icon" />
                    <p className="empty-state-text">Add strategy configurations using the sidebar params, then run the tuned comparison</p>
                </div>
            )}
        </div>
    );
}
