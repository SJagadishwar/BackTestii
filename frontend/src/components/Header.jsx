import { useState, useEffect } from 'react';
import { healthCheck } from '../api/client';
import { Activity, Database } from 'lucide-react';

export default function Header({ ticker, tickerName, strategyName, activeTab }) {
    const [online, setOnline] = useState(false);

    useEffect(() => {
        healthCheck().then(() => setOnline(true)).catch(() => setOnline(false));
        const interval = setInterval(() => {
            healthCheck().then(() => setOnline(true)).catch(() => setOnline(false));
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    // Clean up ticker for fallback
    const cleanTicker = ticker ? ticker.replace('.NS', '') : '';
    // Use full name if available, otherwise just use the stripped ticker
    const displayName = tickerName || cleanTicker;

    return (
        <header className="header">
            <div className="header-left">
                {ticker ? (
                    <>
                        {activeTab === 'stockData' ? (
                            <Database size={16} style={{ color: 'var(--accent-blue)' }} />
                        ) : (
                            <Activity size={16} style={{ color: 'var(--accent-blue)' }} />
                        )}
                        <span className="header-ticker">{displayName}</span>
                    </>
                ) : (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Select an instrument to begin</span>
                )}
                {strategyName && <span className="header-strategy">{strategyName}</span>}
            </div>
            <div className="header-right">
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    API {online ? 'Connected' : 'Offline'}
                </span>
                <div className={`status-dot ${online ? '' : 'status-dot--offline'}`} />
            </div>
        </header>
    );
}
