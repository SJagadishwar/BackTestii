import { LayoutDashboard, LineChart, CandlestickChart, List, GitCompare, FlaskConical, Download, Activity } from 'lucide-react';

const TABS = [
    { key: 'overview', label: 'Overview', icon: LayoutDashboard },
    { key: 'performance', label: 'Performance', icon: LineChart },
    { key: 'chart', label: 'Chart', icon: CandlestickChart },
    { key: 'trades', label: 'Trades', icon: List },
    { key: 'comparison', label: 'Comparison', icon: GitCompare },
    { key: 'tuned', label: 'Tuned Lab', icon: FlaskConical },
    { key: 'download', label: 'Download', icon: Download },
    { key: 'stockData', label: 'Stock Data', icon: Activity },
];

export default function TabBar({ activeTab, onTabChange, hasResults }) {
    return (
        <nav className="tab-bar">
            {TABS.map(tab => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.key;
                // 'overview' and 'stockData' are always enabled. The rest require results.
                const disabled = !hasResults && tab.key !== 'overview' && tab.key !== 'stockData';
                return (
                    <button
                        key={tab.key}
                        className={`tab-item ${isActive ? 'tab-item--active' : ''} ${disabled ? 'tab-item--disabled' : ''}`}
                        onClick={() => !disabled && onTabChange(tab.key)}
                        disabled={disabled}
                    >
                        <Icon size={14} />
                        <span>{tab.label}</span>
                    </button>
                );
            })}
        </nav>
    );
}
