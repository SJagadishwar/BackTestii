import { TrendingUp, TrendingDown, BarChart2, Clock } from 'lucide-react';

function fmt(val, decimals = 2) {
    if (val == null) return '—';
    return Number(val).toFixed(decimals);
}

const CARDS = [
    {
        key: 'Total Return (%)',
        label: 'Total Return',
        suffix: '%',
        icon: TrendingUp,
        colorFn: v => v >= 0 ? 'profit' : 'loss',
    },
    {
        key: 'CAGR (%)',
        label: 'CAGR',
        suffix: '%',
        icon: BarChart2,
        colorFn: v => v >= 0 ? 'profit' : 'loss',
    },
    {
        key: 'Max Drawdown (%)',
        label: 'Max Drawdown',
        suffix: '%',
        icon: TrendingDown,
        colorFn: () => 'loss',
    },
    {
        key: 'Max Drawdown Duration (days)',
        label: 'DD Duration',
        suffix: ' days',
        icon: Clock,
        colorFn: () => 'neutral',
        decimals: 0,
    },
];

export default function DashboardKPIs({ metrics, tradeMetrics }) {
    if (!metrics) return null;

    return (
        <div className="kpi-grid">
            {CARDS.map((card, i) => {
                const val = metrics[card.key];
                const color = card.colorFn(val);
                const Icon = card.icon;

                return (
                    <div key={card.key} className={`kpi-card kpi-card--${color} fade-in fade-in-delay-${i + 1}`}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span className="kpi-label">{card.label}</span>
                            <Icon size={16} className={`kpi-icon kpi-icon--${color}`} />
                        </div>
                        <div className={`kpi-value kpi-value--${color}`}>
                            {fmt(val, card.decimals ?? 2)}{card.suffix}
                        </div>
                        {card.key === 'Total Return (%)' && tradeMetrics && (
                            <div className="kpi-sub">
                                Win Rate: {fmt(tradeMetrics['Win Rate (%)'])}%  ·  {fmt(tradeMetrics['Total Trades'], 0)} trades
                            </div>
                        )}
                        {card.key === 'CAGR (%)' && tradeMetrics && (
                            <div className="kpi-sub">
                                Expectancy: {fmt(tradeMetrics['Expectancy (%)'])}%
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
