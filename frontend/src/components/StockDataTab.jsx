import { useState, useRef, useMemo } from 'react';
import { AlertCircle, Info, ArrowUpRight, ArrowDownRight, Database, ChevronUp, ChevronDown } from 'lucide-react';

export default function StockDataTab({ stockDataState, updateStockDataState }) {
    const tableContainerRef = useRef(null);

    // Destructure shared state
    const {
        selectedTicker,
        tickerName, // Currently selected in dropdown
        activeTickerName, // The one whose data is currently fetched
        data,
        error,
        isClearing,
    } = stockDataState;

    // Local UI state
    const [sortOrder, setSortOrder] = useState('desc');

    // Memoize sorted data
    const sortedData = useMemo(() => {
        if (!data) return [];
        return [...data].sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });
    }, [data, sortOrder]);

    const formatStockName = (name) => {
        if (!name) return '';
        return name.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '--';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const formatRatio = (row) => {
        // First try to extract a ratio pattern like "1:1" or "2:1" from remarks
        if (row.remarks) {
            if (row.actionType !== 'DIVIDEND') {
                const ratioMatch = row.remarks.match(/\b(\d+\s*:\s*\d+)\b/);
                if (ratioMatch) {
                    return ratioMatch[1].replace(/\s+/g, ''); // "1 : 1" -> "1:1"
                }

                // For splits going from Rs X to Rs Y
                const splitMatch = row.remarks.match(/From\s+Rs\.??\s*(\d+).*?To\s+R[se]\.??\s*(\d+)/i);
                if (splitMatch) {
                    return `${splitMatch[1]}:${splitMatch[2]}`;
                }
            }

            // For dividends, show the remarks string (e.g. "Dividend - Rs 5.5 Per Share")
            if (row.actionType === 'DIVIDEND') {
                const rsMatch = row.remarks.match(/R[se]\.?\s*([\d\.]+)/i);
                if (rsMatch) return `₹${rsMatch[1]}`;
            }
        }

        // Fallback for DIVIDEND using the exact amount field if available
        if (row.actionType === 'DIVIDEND' && row.amount != null) {
            return `₹${row.amount}`;
        }

        // Fallback to raw ratio if available
        if (row.ratio) {
            const num = parseFloat(row.ratio);

            // For BONUS entries the DB stores the total adjustment multiplier
            // (e.g. 2.0 for a 1:1 bonus).  Subtract 1 to get the bonus portion.
            if (row.actionType === 'BONUS') {
                const bonusNew = num - 1;            // 2.0 → 1, 1.5 → 0.5
                if (Number.isInteger(bonusNew) && bonusNew >= 1) return `${bonusNew}:1`;

                // Handle fractional bonuses like 1:2, 1:3, 2:3
                if (bonusNew > 0) {
                    // Find simplest integer ratio X:Y where X/Y ≈ bonusNew
                    for (let denom = 1; denom <= 200; denom++) {
                        const numer = Math.round(bonusNew * denom);
                        if (numer > 0 && Math.abs(numer / denom - bonusNew) < 0.001) {
                            return `${numer}:${denom}`;
                        }
                    }
                }
                return `${bonusNew.toFixed(4).replace(/\.?0+$/, '')}:1`;
            }

            // For RIGHTS entries the DB stores (new + existing) / existing
            // e.g. Rights 1:15 → ratio = 16/15 = 1.0667.  Reverse to "1:15".
            if (row.actionType === 'RIGHTS') {
                const newPart = num - 1; // fractional portion of new shares
                if (newPart > 0) {
                    // Find simplest integer ratio X:Y where X/Y ≈ newPart
                    for (let denom = 1; denom <= 200; denom++) {
                        const numer = Math.round(newPart * denom);
                        if (numer > 0 && Math.abs(numer / denom - newPart) < 0.001) {
                            return `${numer}:${denom}`;
                        }
                    }
                }
                return num.toFixed(4).replace(/\.?0+$/, '');
            }

            // For splits, ratio is direct (e.g. 2.0 → 2:1)
            if (Number.isInteger(num)) return `${num}:1`;
            return num.toFixed(4).replace(/\.?0+$/, '');
        }

        return '--';
    };

    // Determine loading/empty status from data presence (loading is managed in sidebar now)
    const isLoading = false; // Loading state now in sidebar

    return (
        <div className="stock-data-standalone fade-in" key={stockDataState.animationKey}>
            {/* Content Area */}
            <div className={`stock-tabular-content glass-panel ${isClearing ? 'dissolve-out' : 'animate-focus-slide'}`}>
                {/* --- PRICES VIEW --- */}
                {!data && !isLoading && !error ? (
                        <div className="empty-state-inner fade-in">
                            <Database size={64} className="empty-state-icon" style={{ opacity: 0.2 }} />
                            <h3>Market History Discovery</h3>
                            <p>Search and select an instrument in the sidebar, then click <strong>Go</strong> to view its adjusted historical OHLCV data.</p>
                        </div>
                    ) : error ? (
                        <div className="empty-state-inner fade-in">
                            <AlertCircle size={48} color="var(--color-loss)" />
                            <h3>Fetch Failed</h3>
                            <p>{error}</p>
                        </div>
                    ) : data && data.length === 0 ? (
                        <div className="empty-state-inner">
                            <Info size={48} color="var(--text-secondary)" style={{ opacity: 0.5 }} />
                            <h3>No Data Available</h3>
                            <p>We couldn't find any trading records for this instrument in the selected date range. It might not have been listed yet.</p>
                        </div>
                    ) : (
                        <div
                            className="stock-table-container"
                            ref={tableContainerRef}
                        >
                            <div className="stock-table-header-info brand-header-gradient animate-bloom">
                                <div className="brand-header-shine" />
                                <div className="brand-header-content animate-focus-slide">
                                    <div className="stock-table-title-row">
                                        <span className="stock-table-name-large">{activeTickerName || tickerName}</span>
                                    </div>
                                    <div className="stock-table-meta">
                                        <Info size={14} /> Adjusted for Dividends, Splits & Bonuses
                                    </div>
                                </div>
                            </div>
                            <div className="stock-grid-wrapper">
                                <table className="stock-data-table">
                                    <thead className="animate-stagger-header">
                                        <tr>
                                            <th
                                                className="sortable-header"
                                                onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
                                                style={{ animationDelay: '0.4s' }}
                                            >
                                                <div className="header-sort-content">
                                                    Date
                                                    <span className="sort-icon-wrapper">
                                                        {sortOrder === 'desc' ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                                                    </span>
                                                </div>
                                            </th>
                                            <th style={{ animationDelay: '0.45s' }}>Open</th>
                                            <th style={{ animationDelay: '0.5s' }}>High</th>
                                            <th style={{ animationDelay: '0.55s' }}>Low</th>
                                            <th style={{ animationDelay: '0.6s' }}>Close</th>
                                            <th style={{ animationDelay: '0.65s' }}>Volume</th>
                                            <th style={{ animationDelay: '0.7s' }}>Change %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedData && sortedData.map((row, idx) => {
                                            const nextRow = sortedData[idx + 1];
                                            const change = nextRow ? ((row.close - nextRow.close) / nextRow.close) * 100 : 0;
                                            const isUp = change >= 0;

                                            return (
                                                <tr
                                                    key={idx}
                                                    className="animate-row-reveal"
                                                    style={{ animationDelay: `${0.8 + (idx * 0.03)}s` }}
                                                >
                                                    <td className="col-date">
                                                        {formatDate(row.date)}
                                                    </td>
                                                    <td className="col-price">₹{row.open?.toFixed(2) || '--'}</td>
                                                    <td className="col-price">₹{row.high?.toFixed(2) || '--'}</td>
                                                    <td className="col-price">₹{row.low?.toFixed(2) || '--'}</td>
                                                    <td className="col-price price-bold">₹{row.close?.toFixed(2) || '--'}</td>
                                                    <td className="col-vol">{row.volume ? row.volume.toLocaleString() : '--'}</td>
                                                    <td className={`col-change ${isUp ? 'up' : 'down'}`}>
                                                        <div className="change-cell">
                                                            {isUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                                                            {Math.abs(change).toFixed(2)}%
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )
                }
            </div>
        </div>
    );
}
