import { useRef, useEffect } from 'react';
import { createChart } from 'lightweight-charts';
import { LineChart } from 'lucide-react';

export default function EquityCurve({ equityCurve }) {
    const containerRef = useRef(null);
    const chartRef = useRef(null);

    const toDay = (d) => d ? d.split('T')[0] : d;

    useEffect(() => {
        if (!containerRef.current || !equityCurve?.length) return;

        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        const chart = createChart(containerRef.current, {
            layout: {
                background: { color: 'transparent' },
                textColor: '#8b949e',
                fontFamily: "'Inter', sans-serif",
                fontSize: 11,
            },
            grid: {
                vertLines: { color: 'rgba(255,255,255,0.03)' },
                horzLines: { color: 'rgba(255,255,255,0.03)' },
            },
            crosshair: {
                vertLine: { color: 'rgba(59,130,246,0.3)', labelBackgroundColor: '#3b82f6' },
                horzLine: { color: 'rgba(59,130,246,0.3)', labelBackgroundColor: '#3b82f6' },
            },
            timeScale: {
                borderColor: 'rgba(255,255,255,0.06)',
                timeVisible: false,
            },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.06)',
            },
            handleScroll: { vertTouchDrag: false },
        });

        chartRef.current = chart;

        const series = chart.addAreaSeries({
            lineColor: '#3b82f6',
            lineWidth: 2,
            topColor: 'rgba(59,130,246,0.25)',
            bottomColor: 'rgba(59,130,246,0.02)',
            priceFormat: {
                type: 'custom',
                formatter: (price) => '₹' + price.toLocaleString('en-IN', { maximumFractionDigits: 0 }),
            },
        });

        const data = equityCurve.map(d => ({
            time: toDay(d.date),
            value: d.equity,
        }));
        series.setData(data);

        chart.timeScale().fitContent();

        const observer = new ResizeObserver(() => {
            if (containerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        });
        observer.observe(containerRef.current);

        return () => {
            observer.disconnect();
            chart.remove();
            chartRef.current = null;
        };
    }, [equityCurve]);

    if (!equityCurve?.length) {
        return (
            <div className="chart-panel">
                <div className="chart-panel-header">
                    <span className="chart-panel-title">Equity Curve</span>
                </div>
                <div className="empty-state" style={{ height: 260 }}>
                    <LineChart size={48} className="empty-state-icon" />
                    <p className="empty-state-text">Portfolio equity over time will appear here</p>
                </div>
            </div>
        );
    }

    const firstVal = equityCurve[0]?.equity;
    const lastVal = equityCurve[equityCurve.length - 1]?.equity;
    const pctChange = firstVal ? (((lastVal - firstVal) / firstVal) * 100).toFixed(2) : '0.00';

    return (
        <div className="chart-panel fade-in">
            <div className="chart-panel-header">
                <span className="chart-panel-title">Equity Curve</span>
                <span style={{
                    fontSize: '0.78rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    color: pctChange >= 0 ? 'var(--color-profit)' : 'var(--color-loss)',
                }}>
                    {pctChange >= 0 ? '+' : ''}{pctChange}%
                </span>
            </div>
            <div className="chart-container" ref={containerRef} style={{ height: 260 }} />
        </div>
    );
}
