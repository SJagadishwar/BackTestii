import { TrendingUp, TrendingDown, Target, Award, Percent, Timer, Download } from 'lucide-react';

function fmt(val, dec = 2) {
    if (val == null || isNaN(val)) return '—';
    return Number(val).toFixed(dec);
}

function fmtCurrency(val) {
    if (val == null) return '—';
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(d) {
    if (!d) return '—';
    return d.split('T')[0];
}

function downloadCSV(rows, filename) {
    if (!rows?.length) return;
    const cols = Object.keys(rows[0]);
    const csv = [cols.join(','), ...rows.map(r => cols.map(c => {
        const v = r[c];
        return typeof v === 'string' && v.includes(',') ? `"${v}"` : v ?? '';
    }).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click();
}

export default function TradesTable({ trades, openTrade, tradeMetrics }) {
    // Buy & Hold safe exit
    if (!trades || trades.length === 0) {
        return (
            <div className="empty-state" style={{ flex: 1 }}>
                <p className="empty-state-text">Buy & Hold has no individual trades (single continuous position).</p>
            </div>
        );
    }

    // Build display rows with Trade No
    const displayRows = trades.map((t, i) => ({ tradeNo: i + 1, ...t }));

    // Append open trade row
    if (openTrade) {
        displayRows.push({
            tradeNo: displayRows.length + 1,
            entry_date: openTrade.entry_date,
            exit_date: null,
            entry_price: openTrade.entry_price,
            exit_price: null,
            pnl: null,
            return_pct: null,
            holding_days: openTrade.holding_days,
            _isOpen: true,
        });
    }

    // Compute trade metrics from closed trades (same as Streamlit)
    const totalTrades = trades.length;
    const winners = trades.filter(t => t.pnl > 0);
    const losers = trades.filter(t => t.pnl <= 0);
    const winRate = totalTrades ? (winners.length / totalTrades) * 100 : 0;
    const avgWin = winners.length ? winners.reduce((s, t) => s + t.return_pct, 0) / winners.length : 0;
    const avgLoss = losers.length ? losers.reduce((s, t) => s + t.return_pct, 0) / losers.length : 0;
    const expectancy = totalTrades ? (winRate / 100) * avgWin + ((100 - winRate) / 100) * avgLoss : 0;
    const avgHolding = totalTrades ? trades.reduce((s, t) => s + (t.holding_days || 0), 0) / totalTrades : 0;

    const metricCards = [
        { label: 'Total Trades', value: totalTrades, dec: 0, suffix: '', icon: Target, color: 'neutral' },
        { label: 'Win Rate', value: winRate, dec: 2, suffix: '%', icon: Award, color: 'neutral' },
        { label: 'Avg Win', value: avgWin, dec: 2, suffix: '%', icon: TrendingUp, color: 'profit' },
        { label: 'Avg Loss', value: avgLoss, dec: 2, suffix: '%', icon: TrendingDown, color: 'loss' },
        { label: 'Expectancy', value: expectancy, dec: 2, suffix: '%', icon: Percent, color: expectancy >= 0 ? 'profit' : 'loss' },
        { label: 'Avg Holding', value: avgHolding, dec: 1, suffix: ' days', icon: Timer, color: 'neutral' },
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Trade Metrics Row */}
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                {metricCards.map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <div key={card.label} className={`kpi-card kpi-card--${card.color} fade-in fade-in-delay-${i + 1}`}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                <span className="kpi-label">{card.label}</span>
                                <Icon size={16} className={`kpi-icon kpi-icon--${card.color}`} />
                            </div>
                            <div className={`kpi-value kpi-value--${card.color}`} style={{ fontSize: '1.2rem' }}>
                                {fmt(card.value, card.dec)}{card.suffix}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Trades Table */}
            <div className="trades-panel fade-in">
                <div className="trades-header">
                    <span className="trades-title">Trade Log</span>
                    <span className="trades-count">{totalTrades} closed{openTrade ? ' + 1 open' : ''}</span>
                </div>
                <div className="trades-table-wrap">
                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>Entry Date</th>
                                <th>Exit Date</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>PnL</th>
                                <th>Return %</th>
                                <th>Holding Days</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayRows.map(row => (
                                <tr key={row.tradeNo} style={row._isOpen ? { background: 'rgba(245,158,11,0.08)', borderLeft: '3px solid #f59e0b' } : {}}>
                                    <td>{row.tradeNo}</td>
                                    <td>{fmtDate(row.entry_date)}</td>
                                    <td>{row._isOpen ? <span style={{ color: '#f59e0b', fontWeight: 600 }}>OPEN</span> : fmtDate(row.exit_date)}</td>
                                    <td>{fmtCurrency(row.entry_price)}</td>
                                    <td>{row.exit_price != null ? fmtCurrency(row.exit_price) : '—'}</td>
                                    <td className={row.pnl > 0 ? 'profit' : row.pnl < 0 ? 'loss' : ''}>
                                        {row.pnl != null ? fmtCurrency(row.pnl) : '—'}
                                    </td>
                                    <td className={row.return_pct > 0 ? 'profit' : row.return_pct < 0 ? 'loss' : ''}>
                                        {row.return_pct != null ? fmt(row.return_pct) + '%' : '—'}
                                    </td>
                                    <td>{row.holding_days ?? '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* CSV Download */}
            <button className="btn-download" onClick={() => downloadCSV(displayRows.map(r => ({
                'Trade No': r.tradeNo,
                'Entry Date': fmtDate(r.entry_date),
                'Exit Date': r._isOpen ? 'OPEN' : fmtDate(r.exit_date),
                'Entry Price': r.entry_price,
                'Exit Price': r.exit_price ?? '',
                'PnL': r.pnl ?? '',
                'Return %': r.return_pct ?? '',
                'Holding Days': r.holding_days ?? '',
            })), 'trade_log.csv')}>
                <Download size={14} />
                📥 Download Trades CSV
            </button>
        </div>
    );
}
