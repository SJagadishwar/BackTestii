import { useState, useRef } from 'react';
import './index.css';
import LandingPage from './components/LandingPage';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import TabBar from './components/TabBar';
import OverviewTab from './components/OverviewTab';
import PerformanceTab from './components/PerformanceTab';
import ChartPanel from './components/ChartPanel';
import TradesTable from './components/TradesTable';
import ComparisonTab from './components/ComparisonTab';
import TunedLabTab from './components/TunedLabTab';
import DownloadTab from './components/DownloadTab';
import StockDataTab from './components/StockDataTab';
import ErrorBoundary from './components/ErrorBoundary';

import { BarChart3 } from 'lucide-react';

export default function App() {
  const [appMode, setAppMode] = useState(null); // null = landing, 'equity' = dashboard
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [backtestParams, setBacktestParams] = useState({});

  // Track whether first result has been shown yet
  const [tunedRuns, setTunedRuns] = useState({});
  const [tunedData, setTunedData] = useState(null);

  // ─── Comparison state (lifted here so results persist across tab switches) ───
  const [comparisonData, setComparisonData] = useState(null);
  const [comparisonSelected, setComparisonSelected] = useState([]);

  // ─── Stock Data state (lifted so Sidebar + StockDataTab share state) ───
  const [stockDataState, setStockDataState] = useState({
    assetType: 'stock', // 'stock' or 'index'
    searchTerm: '',
    selectedTicker: null,
    tickerName: '',
    startDate: (() => { const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().split('T')[0]; })(),
    endDate: new Date().toISOString().split('T')[0],
    animationKey: 0,
    isClearing: false,
  });

  const updateStockDataState = (updates) => {
    setStockDataState(prev => ({ ...prev, ...updates }));
  };

  // Track whether first result has been shown yet
  const firstResultShown = useRef(false);

  // Landing page
  if (appMode === null) {
    return <LandingPage onEnter={(mode) => setAppMode(mode)} />;
  }

  const hasStockData = stockDataState.data && stockDataState.data.length > 0;
  
  const ticker = activeTab === 'stockData'
    ? (hasStockData ? stockDataState.selectedTicker : null)
    : backtestParams.ticker || result?.ticker;
  
  const tickerName = activeTab === 'stockData'
    ? (hasStockData ? (stockDataState.activeTickerName || stockDataState.tickerName) : null)
    : backtestParams.tickerName || result?.tickerName;
    
  const strategyName = result?.strategyName;

  const handleResult = (res) => {
    setResult(res);
    // Only jump to Overview on FIRST backtest run or if currently on a tab that needs results and has none
    if (!firstResultShown.current) {
      setActiveTab('overview');
      firstResultShown.current = true;
    }
    // Otherwise, stay on the current tab (Tuned Lab, Comparison, etc.)
  };

  const handleParamsUpdate = (params) => {
    setBacktestParams(prev => ({
      ...prev,
      ...params,
      ticker: params.ticker || prev.ticker,
      tickerName: params.tickerName || prev.tickerName,
    }));
  };

  const renderTab = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab metrics={result?.metrics} tradeMetrics={result?.trade_metrics} />;
      case 'stockData':
        return (
          <ErrorBoundary>
            <StockDataTab
              stockDataState={stockDataState}
              updateStockDataState={updateStockDataState}
            />
          </ErrorBoundary>
        );
      case 'performance':
        return (
          <ErrorBoundary>
            <PerformanceTab equityCurve={result?.equity_curve} priceData={result?.price_data}
              signals={result?.signals} trades={result?.trades} />
          </ErrorBoundary>
        );
      case 'chart':
        return (
          <ErrorBoundary>
            <ChartPanel priceData={result?.price_data} signals={result?.signals}
              trades={result?.trades} openTrade={result?.open_trade}
              overlayData={result?.overlay_data} oscillatorData={result?.oscillator_data}
              chartConfig={result?.chart_config} />
          </ErrorBoundary>
        );
      case 'trades':
        return (
          <ErrorBoundary>
            <TradesTable trades={result?.trades} openTrade={result?.open_trade} tradeMetrics={result?.trade_metrics} />
          </ErrorBoundary>
        );
      case 'comparison':
        return (
          <ErrorBoundary>
            <ComparisonTab ticker={ticker} assetType={backtestParams.assetType} startDate={backtestParams.startDate} endDate={backtestParams.endDate} capital={backtestParams.capital}
              comparisonData={comparisonData} setComparisonData={setComparisonData}
              comparisonSelected={comparisonSelected} setComparisonSelected={setComparisonSelected} />
          </ErrorBoundary>
        );
      case 'tuned':
        return (
          <ErrorBoundary>
            <TunedLabTab ticker={ticker} assetType={backtestParams.assetType} startDate={backtestParams.startDate} endDate={backtestParams.endDate}
              capital={backtestParams.capital} currentStrategyKey={backtestParams.strategyKey} currentParams={backtestParams.strategyParams}
              tunedRuns={tunedRuns} setTunedRuns={setTunedRuns}
              tunedData={tunedData} setTunedData={setTunedData} />
          </ErrorBoundary>
        );
      case 'download':
        return <DownloadTab result={result} ticker={ticker} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onResult={handleResult}
        onLoading={setLoading}
        onParamsUpdate={handleParamsUpdate}
        onBackToHome={() => setAppMode(null)}
        stockDataState={stockDataState}
        updateStockDataState={updateStockDataState}
      />

      <div className="main-area">
        <Header 
          ticker={ticker} 
          tickerName={tickerName} 
          strategyName={activeTab === 'stockData' ? null : strategyName} 
          activeTab={activeTab} 
        />

        {/* Tab Navigation */}
        <TabBar activeTab={activeTab} onTabChange={setActiveTab} hasResults={!!result} />

        <div className="main-content">
          {!result && !loading ? (
            activeTab === 'overview' ? (
              <div className="empty-state" style={{ flex: 1 }}>
                <BarChart3 size={64} className="empty-state-icon" />
                <p className="empty-state-text" style={{ fontSize: '1rem' }}>
                  Configure your strategy in the sidebar and click <strong>Run Backtest</strong> to begin.
                </p>
              </div>
            ) : activeTab === 'stockData' ? (
              renderTab()
            ) : null
          ) : loading ? (
            <div className="empty-state" style={{ flex: 1 }}>
              <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
              <p className="empty-state-text">Running backtest…</p>
            </div>
          ) : (
            renderTab()
          )}
        </div>
      </div>
    </div>
  );
}
