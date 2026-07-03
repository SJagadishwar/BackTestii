import React, { useState } from 'react';
import { TrendingUp, TrendingDown, BarChart2, Clock, Target, Award, Percent, Timer, Info } from 'lucide-react';
import MetricGuideModal from './MetricGuideModal';

function fmt(val, decimals = 2) {
    if (val == null) return '—';
    return Number(val).toFixed(decimals);
}

export default function OverviewTab({ metrics, tradeMetrics }) {
    const [activeMetric, setActiveMetric] = useState(null);

    // Open/Close handlers
    const handleOpenGuide = (key, label) => {
        setActiveMetric({ key, label });
    };
    const handleCloseGuide = () => {
        setActiveMetric(null);
    };

    if (!metrics) {
        return (
            <div className="empty-state" style={{ flex: 1 }}>
                <BarChart2 size={48} className="empty-state-icon" />
                <p className="empty-state-text">Run a backtest to see the overview</p>
            </div>
        );
    }

    const kpis = [
        { key: 'Total Return (%)', label: 'Total Return', suffix: '%', icon: TrendingUp, colorFn: v => v >= 0 ? 'profit' : 'loss' },
        { key: 'CAGR (%)', label: 'CAGR', suffix: '%', icon: BarChart2, colorFn: v => v >= 0 ? 'profit' : 'loss' },
        { key: 'Max Drawdown (%)', label: 'Max Drawdown', suffix: '%', icon: TrendingDown, colorFn: () => 'loss' },
        { key: 'Max Drawdown Duration (days)', label: 'DD Duration', suffix: ' days', icon: Clock, colorFn: () => 'neutral', decimals: 0 },
    ];

    const tradeCards = tradeMetrics ? [
        { key: 'Total Trades', label: 'Total Trades', icon: Target, decimals: 0, suffix: '' },
        { key: 'Win Rate (%)', label: 'Win Rate', icon: Award, suffix: '%' },
        { key: 'Avg Win (%)', label: 'Avg Win', icon: TrendingUp, suffix: '%', colorFn: () => 'profit' },
        { key: 'Avg Loss (%)', label: 'Avg Loss', icon: TrendingDown, suffix: '%', colorFn: () => 'loss' },
        { key: 'Expectancy (%)', label: 'Expectancy', icon: Percent, suffix: '%', colorFn: v => v >= 0 ? 'profit' : 'loss' },
        { key: 'Avg Holding Days', label: 'Avg Holding', icon: Timer, suffix: ' days', decimals: 1 },
    ] : [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Metric Guide Modal Injection */}
            <MetricGuideModal 
                isOpen={!!activeMetric} 
                onClose={handleCloseGuide} 
                metricKey={activeMetric?.key}
                metricName={activeMetric?.label}
            />

            {/* Main KPIs */}
            <div className="kpi-grid">
                {kpis.map((card, i) => {
                    const val = metrics[card.key];
                    const color = card.colorFn(val);
                    const Icon = card.icon;
                    return (
                        <div key={card.key} className={`kpi-card kpi-card--${color} fade-in fade-in-delay-${i + 1}`}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span className="kpi-label">{card.label}</span>
                                    <button 
                                        className="metric-info-btn"
                                        onClick={() => handleOpenGuide(card.key, card.label)}
                                        title={`Learn about ${card.label}`}
                                        style={{ transform: 'translateY(-3px)' }}
                                    >
                                        <Info size={13} />
                                    </button>
                                </div>
                                <Icon size={16} className={`kpi-icon kpi-icon--${color}`} />
                            </div>
                            <div className={`kpi-value kpi-value--${color}`}>
                                {fmt(val, card.decimals ?? 2)}{card.suffix}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Trade Metrics */}
            {tradeCards.length > 0 && (
                <>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', margin: 0 }}>
                        Trade Metrics
                    </h3>
                    <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                        {tradeCards.map((card, i) => {
                            const val = tradeMetrics[card.key];
                            const color = card.colorFn ? card.colorFn(val) : 'neutral';
                            const Icon = card.icon;
                            return (
                                <div key={card.key} className={`kpi-card kpi-card--${color} fade-in fade-in-delay-${i + 1}`}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <span className="kpi-label">{card.label}</span>
                                            <button 
                                                className="metric-info-btn"
                                                onClick={() => handleOpenGuide(card.key, card.label)}
                                                title={`Learn about ${card.label}`}
                                                style={{ transform: 'translateY(-3px)' }}
                                            >
                                                <Info size={13} />
                                            </button>
                                        </div>
                                        <Icon size={16} className={`kpi-icon kpi-icon--${color}`} />
                                    </div>
                                    <div className={`kpi-value kpi-value--${color}`} style={{ fontSize: '1.2rem' }}>
                                        {fmt(val, card.decimals ?? 2)}{card.suffix}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </>
            )}
        </div>
    );
}
