import { Download as DownloadIcon } from 'lucide-react';

function downloadCSV(data, filename) {
    if (!data?.length) return;
    const cols = Object.keys(data[0]);
    const csv = [cols.join(','), ...data.map(row => cols.map(c => {
        const v = row[c];
        return typeof v === 'string' && v.includes(',') ? `"${v}"` : v ?? '';
    }).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
}

function DownloadButton({ label, data, filename, disabled }) {
    return (
        <button className="btn-download" onClick={() => downloadCSV(data, filename)} disabled={disabled || !data?.length}>
            <DownloadIcon size={14} />
            {label}
        </button>
    );
}

export default function DownloadTab({ result, ticker }) {
    const equityCurve = result?.equity_curve;
    const trades = result?.trades;
    const priceData = result?.price_data;

    if (!result) {
        return (
            <div className="empty-state" style={{ flex: 1 }}>
                <DownloadIcon size={48} className="empty-state-icon" />
                <p className="empty-state-text">Run a backtest first to download results</p>
            </div>
        );
    }

    // Detailed equity: add daily_pnl
    const detailedEquity = equityCurve?.map((d, i) => ({
        ...d,
        daily_pnl: i > 0 ? (d.equity - equityCurve[i - 1].equity).toFixed(2) : '0.00',
    }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', margin: 0 }}>📈 Equity Curve</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <DownloadButton label="Equity Curve (Simple)" data={equityCurve?.map(d => ({ Date: d.date, portfolio_value: d.equity }))}
                    filename={`equity_curve_${ticker}.csv`} />
                <DownloadButton label="Equity Curve (Detailed)" data={detailedEquity}
                    filename={`equity_curve_detailed_${ticker}.csv`} />
            </div>

            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', margin: 0 }}>📋 Trades</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <DownloadButton label="Trade Log (CSV)" data={trades} filename={`trade_log_${ticker}.csv`} />
            </div>

            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', margin: 0 }}>📊 Price Data</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <DownloadButton label="OHLCV Price Data" data={priceData} filename={`price_data_${ticker}.csv`} />
            </div>
        </div>
    );
}
