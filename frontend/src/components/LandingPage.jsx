import { useState } from 'react';
import { BarChart3 } from 'lucide-react';

export default function LandingPage({ onEnter }) {
    const [hoveredNode, setHoveredNode] = useState(null);

    return (
        <div className="landing-wrap">
            <div className="landing-hero">
                <div className="landing-brand">BackTestii</div>
            </div>

            <div className="landing-stage">
                <div className="landing-glow" />

                {/* Orbit */}
                <div className="landing-orbit">
                    <div className={`landing-node landing-node--equity ${hoveredNode === 'equity' ? 'landing-node--hover' : ''}`}
                        onMouseEnter={() => setHoveredNode('equity')} onMouseLeave={() => setHoveredNode(null)}
                        onClick={() => onEnter?.('equity')}>
                        <div className="landing-node-inner">
                            <div className="landing-node-icon">📊</div>
                            <div className="landing-node-title">Equity Backtesting</div>
                            <div className="landing-node-sub">Enter</div>
                        </div>
                    </div>

                    <div className="landing-node landing-node--candle landing-node--disabled"
                        onMouseEnter={() => setHoveredNode('candle')} onMouseLeave={() => setHoveredNode(null)}>
                        <div className="landing-node-inner">
                            <div className="landing-node-icon">🕯️</div>
                            <div className="landing-node-title">Candlestick Backtesting</div>
                            <div className="landing-node-sub">Coming soon</div>
                        </div>
                    </div>

                    <div className="landing-node landing-node--options landing-node--disabled"
                        onMouseEnter={() => setHoveredNode('options')} onMouseLeave={() => setHoveredNode(null)}>
                        <div className="landing-node-inner">
                            <div className="landing-node-icon">📈</div>
                            <div className="landing-node-title">Options Backtesting</div>
                            <div className="landing-node-sub">Coming soon</div>
                        </div>
                    </div>
                </div>

                {/* Center clock */}
                <div className="landing-center">
                    <div className="landing-clock">
                        <div className="landing-hand landing-hand--hour" />
                        <div className="landing-hand landing-hand--minute" />
                        <div className="landing-hand landing-hand--second" />
                        <div className="landing-pin" />
                    </div>
                </div>
            </div>

            <div className="landing-hint">Select a module to continue</div>

            {/* Buttons */}
            <div className="landing-buttons">
                <button className="landing-btn landing-btn--primary" onClick={() => onEnter?.('equity')}>
                    Equity Backtesting
                </button>
                <button className="landing-btn" disabled>
                    Candlestick Backtesting
                </button>
                <button className="landing-btn" disabled>
                    Options Backtesting
                </button>
            </div>
        </div>
    );
}
