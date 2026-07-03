import { useState, useEffect, useCallback, useRef } from 'react';
import { getStrategies, searchInstruments, runBacktest, getStockData, getIndices } from '../api/client';
import { BarChart3, Search, Calendar, Play, RotateCcw, ChevronDown, Database } from 'lucide-react';

import StrategyGuideModal from './StrategyGuideModal';

export default function Sidebar({ activeTab, onResult, onLoading, onParamsUpdate, onBackToHome, stockDataState, updateStockDataState }) {
    // ─── Modal State ───
    const [isGuideOpen, setIsGuideOpen] = useState(false);

    // ─── Backtest state ───
    const [assetType, setAssetType] = useState('stock'); // 'stock' or 'index'
    const [instrument, setInstrument] = useState('');
    const [instrumentLabel, setInstrumentLabel] = useState('');
    const [indicesList, setIndicesList] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const searchRef = useRef(null);
    const debounceRef = useRef(null);

    const [strategies, setStrategies] = useState({});
    const [categories, setCategories] = useState([]);
    const [selectedCategory, _setSelectedCategory] = useState('All');
    const [strategyKey, setStrategyKey] = useState('');
    const [params, setParams] = useState({});
    const [startDate, setStartDate] = useState('2020-01-01');
    const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
    const [capital, setCapital] = useState(100000);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // ─── Stock Data sidebar state ───
    const [sdSearchResults, setSdSearchResults] = useState([]);
    const [sdIsSearching, setSdIsSearching] = useState(false);
    const [sdLoading, setSdLoading] = useState(false);
    const sdSearchRef = useRef(null);

    // Load strategies on mount
    useEffect(() => {
        getStrategies().then(data => {
            setStrategies(data);
            const cats = [...new Set(Object.values(data).map(s => s.category))].sort();
            setCategories(cats);
            const firstKey = Object.keys(data)[0];
            if (firstKey) {
                setStrategyKey(firstKey);
                setDefaultParams(data[firstKey]);
            }
        }).catch(() => { });

        // Load available indices
        getIndices().then(data => {
            setIndicesList(data.data || []);
        }).catch(() => { });
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (searchRef.current && !searchRef.current.contains(e.target)) {
                setShowDropdown(false);
            }
            if (sdSearchRef.current && !sdSearchRef.current.contains(e.target)) {
                setSdSearchResults([]);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // ─── Stock Data search debounce ───
    useEffect(() => {
        if (activeTab !== 'stockData') return;
        // Skip search if a ticker is already selected (it means we just select it from dropdown)
        if (stockDataState.selectedTicker) {
            setSdSearchResults([]);
            return;
        }
        const term = stockDataState.searchTerm;
        if (!term || !term.trim()) {
            setSdSearchResults([]);
            return;
        }
        const timer = setTimeout(async () => {
            setSdIsSearching(true);
            try {
                const results = await searchInstruments(term);
                setSdSearchResults(results || []);
            } catch (err) {
                console.error('Search failed:', err);
            } finally {
                setSdIsSearching(false);
            }
        }, 400);
        return () => clearTimeout(timer);
    }, [stockDataState.searchTerm, activeTab]);

    // Backtest debounced search
    const handleSearchInput = (value) => {
        setSearchQuery(value);
        setInstrument('');
        setInstrumentLabel('');

        if (debounceRef.current) clearTimeout(debounceRef.current);

        if (!value || value.trim().length < 1) {
            setSearchResults([]);
            setShowDropdown(false);
            return;
        }

        debounceRef.current = setTimeout(async () => {
            setSearchLoading(true);
            setShowDropdown(true);
            try {
                const results = await searchInstruments(value);
                setSearchResults(results);
            } catch {
                setSearchResults([]);
            } finally {
                setSearchLoading(false);
            }
        }, 300);
    };

    // Select an instrument from backtest results
    const handleSelectInstrument = (item) => {
        setInstrument(item.symbol);
        const displayName = item.name || item.nse_symbol || item.symbol.replace('.NS', '');
        const finalLabel = `${displayName} — ${item.exchange || 'NSE'}`;
        setInstrumentLabel(finalLabel);
        setSearchQuery(finalLabel);
        setShowDropdown(false);
        setSearchResults([]);
    };

    const setDefaultParams = useCallback((meta) => {
        if (!meta?.params) { setParams({}); return; }
        const defaults = {};
        for (const [k, v] of Object.entries(meta.params)) {
            defaults[k] = v.default;
        }
        setParams(defaults);
    }, []);

    // Filtered strategies
    const filteredKeys = Object.entries(strategies)
        .filter(([, meta]) => selectedCategory === 'All' || meta.category === selectedCategory)
        .map(([key]) => key);

    const handleStrategyChange = (key) => {
        setStrategyKey(key);
        if (strategies[key]) setDefaultParams(strategies[key]);
    };

    const handleParamChange = (name, value) => {
        setParams(prev => {
            const next = { ...prev, [name]: parseFloat(value) || 0 };
            return next;
        });
    };

    const handleCategoryChange = (cat) => {
        _setSelectedCategory(cat);
        const newFiltered = Object.entries(strategies)
            .filter(([, meta]) => cat === 'All' || meta.category === cat)
            .map(([key]) => key);
        if (newFiltered.length > 0) {
            const first = newFiltered[0];
            setStrategyKey(first);
            if (strategies[first]) setDefaultParams(strategies[first]);
        }
        setError('');
    };

    // Live-sync params to App whenever strategy/params/dates/capital change
    useEffect(() => {
        if (!strategyKey) return;
        onParamsUpdate?.({
            ticker: instrument || null,
            tickerName: instrumentLabel || null,
            strategyKey,
            strategyParams: params,
            strategyName: strategies[strategyKey]?.display_name || strategyKey,
            startDate,
            endDate,
            capital,
            assetType,
        });
    }, [strategyKey, params, startDate, endDate, capital, instrument, instrumentLabel, assetType]);

    const handleRun = async () => {
        if (!instrument || !strategyKey) return;
        setLoading(true);
        setError('');
        onLoading?.(true);
        try {
            onParamsUpdate?.({
                ticker: instrument,
                tickerName: instrumentLabel,
                strategyKey,
                strategyParams: params,
                strategyName: strategies[strategyKey]?.display_name || strategyKey,
                startDate,
                endDate,
                capital,
                assetType,
            });
            const result = await runBacktest({
                ticker: instrument,
                strategyKey,
                strategyParams: params,
                startDate,
                endDate,
                capital,
                assetType,
            });
            onResult?.({
                ...result,
                ticker: instrument,
                tickerName: instrumentLabel,
                strategyName: strategies[strategyKey]?.display_name || strategyKey,
                strategyKey,
            });
        } catch (e) {
            setError(typeof e === 'string' ? e : (e?.message || e?.detail || JSON.stringify(e)));
        } finally {
            setLoading(false);
            onLoading?.(false);
        }
    };

    // ─── Stock Data handlers ───
    const formatStockName = (name) => {
        if (!name) return '';
        return name.toLowerCase().split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    };

    const handleSdSelectTicker = (item) => {
        const cleanName = formatStockName(item.name);
        const finalLabel = `${cleanName} — ${item.exchange || 'NSE'}`;
        updateStockDataState({
            selectedTicker: item.symbol || item.nse_symbol,
            tickerName: finalLabel,
            searchTerm: finalLabel,
        });
        setSdSearchResults([]);
    };



    const handleSdGo = async () => {
        if (!stockDataState.selectedTicker) return;
        setSdLoading(true);
        try {
            const res = await getStockData({
                ticker: stockDataState.selectedTicker,
                startDate: stockDataState.startDate,
                endDate: stockDataState.endDate,
                assetType: stockDataState.assetType,
            });
            updateStockDataState({ 
                data: res.data || [], 
                activeTickerName: stockDataState.tickerName, 
                error: null 
            });
        } catch (err) {
            updateStockDataState({ error: err.message || 'Failed to fetch adjusted market data', data: [] });
        }
        setSdLoading(false);
    };

    const triggerParticlesBoom = () => {
        // Find the table container
        const container = document.querySelector('.stock-tabular-content');
        if (!container) return;

        const rect = container.getBoundingClientRect();
        const count = 120; // Denser explosion for the whole table
        const colors = ['#3b82f6', '#60a5fa', '#1e40af', '#d6b25e', '#ffffff'];

        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            const size = Math.random() * 5 + 2;
            
            // Randomly distribute across the entire table area
            const startX = rect.left + Math.random() * rect.width;
            const startY = rect.top + Math.random() * rect.height;

            // Explosion burst + Gravity fall
            const angle = Math.random() * Math.PI * 2;
            const burst = 20 + Math.random() * 50;
            const tx = Math.cos(angle) * burst;
            const ty = (Math.sin(angle) * burst) + (rect.height * 0.7 + Math.random() * 300); 

            const duration = 1.0 + Math.random() * 1.5;

            // Base styling
            particle.style.position = 'fixed';
            particle.style.left = `${startX}px`;
            particle.style.top = `${startY}px`;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.borderRadius = '50%';
            particle.style.pointerEvents = 'none';
            particle.style.zIndex = '9999';
            particle.style.boxShadow = `0 0 ${size}px ${particle.style.background}`;

            // Initial state
            particle.style.transform = `translate(-50%, -50%) scale(1)`;
            particle.style.opacity = '1';
            particle.style.transition = `transform ${duration}s cubic-bezier(0.5, 0, 1, 1), opacity ${duration}s ease-in`;

            document.body.appendChild(particle);

            // Animate fall
            requestAnimationFrame(() => {
                particle.style.transform = `translate(calc(-50% + ${tx}px), calc(-50% + ${ty}px)) scale(0)`;
                particle.style.opacity = '0';
            });

            // Cleanup
            setTimeout(() => {
                if (particle.parentNode) particle.parentNode.removeChild(particle);
            }, duration * 1000);
        }
    };

    const handleSdClear = (e) => {
        // Trigger the particles boom visually on click
        triggerParticlesBoom(e);

        // If there's no data showing yet, just reset search instantly
        if (!stockDataState.data && !stockDataState.error) {
            updateStockDataState({
                searchTerm: '',
                selectedTicker: null,
                tickerName: '',
                activeTickerName: '',
                isClearing: false,
                animationKey: (stockDataState.animationKey || 0) + 1,
            });
            setSdSearchResults([]);
            return;
        }

        // Trigger dissolve-out animation
        updateStockDataState({ isClearing: true });

        // Wait for the animation to mostly finish before removing data from DOM
        setTimeout(() => {
            updateStockDataState({
                searchTerm: '',
                selectedTicker: null,
                tickerName: '',
                activeTickerName: '',
                data: null,
                error: null,
                startDate: (() => { const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().split('T')[0]; })(),
                endDate: new Date().toISOString().split('T')[0],
                animationKey: (stockDataState.animationKey || 0) + 1,
                isClearing: false,
            });
            setSdSearchResults([]);
        }, 2500); // Wait 2.5s to match the 'dissolve-out' CSS animation duration
    };

    const currentMeta = strategies[strategyKey];
    const isStockDataMode = activeTab === 'stockData';

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <BarChart3 size={20} style={{ color: 'var(--accent-blue)' }} />
                <span className="sidebar-brand">BackTestii</span>
                <span className="sidebar-tag">Pro</span>
            </div>

            <div className="sidebar-body">
                {/* Back to Home */}
                <button className="btn-download" style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}
                    onClick={() => onBackToHome?.()}>← Back to Home</button>

                {isStockDataMode ? (
                    /* ═══════════ STOCK DATA CONTROLS ═══════════ */
                    <>
                        {/* Instrument Search */}
                        <div className="sidebar-section" ref={sdSearchRef} style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <label className="sidebar-label" style={{ marginBottom: 0 }}>Instrument</label>
                            </div>

                            {/* Segmented Control for Stocks vs Indices */}
                            <div className="segmented-control" style={{ marginBottom: 12 }}>
                                <button
                                    className={`segment-btn ${stockDataState.assetType === 'stock' ? 'active' : ''}`}
                                    onClick={() => {
                                        updateStockDataState({ assetType: 'stock', selectedTicker: null, tickerName: '', searchTerm: '' });
                                        setSdSearchResults([]);
                                    }}
                                >Stocks</button>
                                <button
                                    className={`segment-btn ${stockDataState.assetType === 'index' ? 'active' : ''}`}
                                    onClick={() => {
                                        updateStockDataState({ assetType: 'index', selectedTicker: null, tickerName: '', searchTerm: '' });
                                        setSdSearchResults([]);
                                    }}
                                >Indices</button>
                            </div>

                            {stockDataState.assetType === 'stock' ? (
                                <>
                                    <div className="instrument-search-wrapper">
                                        <Search size={14} className="instrument-search-icon" />
                                        <input
                                            type="text"
                                            className="form-input instrument-search-input"
                                            placeholder="Search stocks..."
                                            value={stockDataState.searchTerm}
                                            onChange={e => updateStockDataState({ searchTerm: e.target.value, selectedTicker: null, tickerName: '' })}
                                        />
                                    </div>
                                    {sdIsSearching && <div className="instrument-search-loading" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100 }}><span className="spinner" /> Searching...</div>}
                                    {sdSearchResults.length > 0 && (
                                        <div className="instrument-search-dropdown">
                                            {sdSearchResults.map((item, idx) => (
                                                <div
                                                    key={`${item.symbol}-${idx}`}
                                                    className="instrument-search-item"
                                                    onClick={() => handleSdSelectTicker(item)}
                                                >
                                                    <div className="instrument-search-item-left">
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                            <span className="instrument-search-symbol">{item.nse_symbol || item.symbol}</span>
                                                            <span style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: 4, background: item.exchange === 'BSE' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(59, 130, 246, 0.15)', color: item.exchange === 'BSE' ? '#c084fc' : '#60a5fa', fontWeight: 600 }}>{item.exchange || 'NSE'}</span>
                                                        </div>
                                                        <span className="instrument-search-name" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 2 }}>{item.name?.replace(/Limited/gi, 'Ltd.')}</span>
                                                    </div>
                                                    <div className="instrument-search-item-right" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                        <Database size={14} style={{ color: 'var(--brand-primary)', opacity: 0.8 }} />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="instrument-search-wrapper" style={{ padding: 0, border: 'none' }}>
                                    <select 
                                        className="form-select" 
                                        style={{ width: '100%', paddingLeft: 12 }}
                                        value={stockDataState.selectedTicker || ''}
                                        onChange={(e) => {
                                            const val = e.target.value;
                                            updateStockDataState({ 
                                                selectedTicker: val, 
                                                tickerName: val,
                                                searchTerm: val
                                            });
                                        }}
                                    >
                                        <option value="" disabled>Select an Index...</option>
                                        {indicesList.map(idx => (
                                            <option key={idx.index_name} value={idx.index_name}>{idx.index_name}</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                        </div>

                        {/* Date Range */}
                        <div className="sidebar-section">
                            <label className="sidebar-label">Date Range</label>
                            <div className="form-row">
                                <input type="date" className="form-input"
                                    value={stockDataState.startDate}
                                    onChange={e => updateStockDataState({ startDate: e.target.value })}
                                />
                                <input type="date" className="form-input"
                                    value={stockDataState.endDate}
                                    onChange={e => updateStockDataState({ endDate: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Go + Clear */}
                        <div className="sidebar-section" style={{ display: 'flex', gap: 8 }}>
                            <button
                                className={`btn-run ${sdLoading ? 'btn-run--loading' : ''}`}
                                disabled={!stockDataState.selectedTicker || sdLoading}
                                onClick={handleSdGo}
                                style={{ flex: 1 }}
                            >
                                {sdLoading ? <><span className="spinner" /> Loading…</> : '▶  Go'}
                            </button>
                            <button
                                className="btn-download"
                                onClick={handleSdClear}
                                style={{ flex: 1, justifyContent: 'center' }}
                            >
                                ↺ Clear
                            </button>
                        </div>
                    </>
                ) : (
                    /* ═══════════ NORMAL BACKTEST CONTROLS ═══════════ */
                    <>
                        {/* Instrument Search */}
                        <div className="sidebar-section" ref={searchRef} style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <label className="sidebar-label" style={{ marginBottom: 0 }}>Instrument</label>
                            </div>

                            {/* Segmented Control for Stocks vs Indices */}
                            <div className="segmented-control" style={{ marginBottom: 12 }}>
                                <button
                                    className={`segment-btn ${assetType === 'stock' ? 'active' : ''}`}
                                    onClick={() => {
                                        setAssetType('stock');
                                        setInstrument('');
                                        setInstrumentLabel('');
                                        setSearchQuery('');
                                    }}
                                >Stocks</button>
                                <button
                                    className={`segment-btn ${assetType === 'index' ? 'active' : ''}`}
                                    onClick={() => {
                                        setAssetType('index');
                                        setInstrument('');
                                        setInstrumentLabel('');
                                        setSearchQuery('');
                                    }}
                                >Indices</button>
                            </div>

                            {assetType === 'stock' ? (
                                <>
                                    <div className="instrument-search-wrapper">
                                        <Search size={14} className="instrument-search-icon" />
                                        <input
                                            type="text"
                                            className="form-input instrument-search-input"
                                            placeholder="Search stocks (e.g. Reliance, TCS)..."
                                            value={searchQuery}
                                            onChange={e => handleSearchInput(e.target.value)}
                                            onFocus={() => { if (searchResults.length) setShowDropdown(true); }}
                                        />
                                    </div>

                                    {showDropdown && (
                                        <div className="instrument-search-dropdown">
                                            {searchLoading ? (
                                                <div className="instrument-search-loading">
                                                    <span className="spinner" /> Searching...
                                                </div>
                                            ) : searchResults.length === 0 ? (
                                                <div className="instrument-search-empty">No results found</div>
                                            ) : (
                                                searchResults.map((item, idx) => (
                                                    <div
                                                        key={`${item.symbol}-${idx}`}
                                                        className="instrument-search-item"
                                                        onClick={() => handleSelectInstrument(item)}
                                                    >
                                                        <div className="instrument-search-item-left">
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                                <span className="instrument-search-symbol">{item.nse_symbol || item.symbol}</span>
                                                                <span style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: 4, background: item.exchange === 'BSE' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(59, 130, 246, 0.15)', color: item.exchange === 'BSE' ? '#c084fc' : '#60a5fa', fontWeight: 600 }}>{item.exchange || 'NSE'}</span>
                                                            </div>
                                                            <span className="instrument-search-name" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 2 }}>{item.name?.replace(/Limited/gi, 'Ltd.')}</span>
                                                        </div>
                                                        <div className="instrument-search-item-right">
                                                            {item.total_days > 0 ? (
                                                                <>
                                                                    <span className="instrument-search-days">{item.total_days.toLocaleString()} days</span>
                                                                    <span className="instrument-search-dates">
                                                                        {item.data_from?.slice(0, 4)} — {item.data_to?.slice(0, 4)}
                                                                    </span>
                                                                </>
                                                            ) : (
                                                                <span className="instrument-search-no-data">No data</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="instrument-search-wrapper" style={{ padding: 0, border: 'none' }}>
                                    <select 
                                        className="form-select" 
                                        style={{ width: '100%', paddingLeft: 12 }}
                                        value={instrument || ''}
                                        onChange={(e) => {
                                            const val = e.target.value;
                                            setInstrument(val);
                                            setInstrumentLabel(val);
                                            setSearchQuery(val);
                                        }}
                                    >
                                        <option value="" disabled>Select an Index...</option>
                                        {indicesList.map(idx => (
                                            <option key={idx.index_name} value={idx.index_name}>{idx.index_name}</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                        </div>

                        {/* Strategy Category */}
                        <div className="sidebar-section">
                            <label className="sidebar-label">Category</label>
                            <select className="form-select" value={selectedCategory} onChange={e => handleCategoryChange(e.target.value)}>
                                <option value="All">All Categories</option>
                                {categories.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>

                        {/* Strategy */}
                        <div className="sidebar-section">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                <label className="sidebar-label" style={{ marginBottom: 0 }}>Strategy</label>
                                <button 
                                    className="btn-learn-more"
                                    onClick={() => setIsGuideOpen(true)}
                                    title="Understand this strategy"
                                >
                                    <span style={{ fontSize: '0.8rem', marginRight: 4 }}>💡</span> Learn
                                </button>
                            </div>
                            <select className="form-select" value={strategyKey} onChange={e => handleStrategyChange(e.target.value)}>
                                {filteredKeys.map(key => (
                                    <option key={key} value={key}>{strategies[key]?.display_name || key}</option>
                                ))}
                            </select>
                        </div>

                        {/* Params */}
                        {currentMeta?.params && Object.keys(currentMeta.params).length > 0 && (
                            <div className="sidebar-section">
                                <label className="sidebar-label">Parameters</label>
                                {Object.entries(currentMeta.params).map(([name, cfg]) => (
                                    <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                        <span style={{ flex: 1, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{name}</span>
                                        <input
                                            type="number"
                                            className="form-input"
                                            style={{ width: 80, textAlign: 'right' }}
                                            value={params[name] ?? cfg.default}
                                            min={cfg.min}
                                            max={cfg.max}
                                            step={cfg.step}
                                            onChange={e => handleParamChange(name, e.target.value)}
                                        />
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Dates */}
                        <div className="sidebar-section">
                            <label className="sidebar-label">Date Range</label>
                            <div className="form-row">
                                <input type="date" className="form-input" value={startDate} onChange={e => setStartDate(e.target.value)} />
                                <input type="date" className="form-input" value={endDate} onChange={e => setEndDate(e.target.value)} />
                            </div>
                        </div>

                        {/* Capital */}
                        <div className="sidebar-section">
                            <label className="sidebar-label">Capital (₹)</label>
                            <input type="number" className="form-input" value={capital} min={1000} step={10000}
                                onChange={e => setCapital(parseFloat(e.target.value) || 0)} />
                        </div>

                        {/* Error */}
                        {error && (
                            <div style={{
                                fontSize: '0.78rem', color: 'var(--color-loss)', padding: '8px 10px',
                                background: 'rgba(239,68,68,0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239,68,68,0.2)'
                            }}>
                                {error}
                            </div>
                        )}

                        {/* Run */}
                        <button className={`btn-run ${loading ? 'btn-run--loading' : ''}`} onClick={handleRun}
                            disabled={loading || !instrument || !strategyKey}>
                            {loading ? <><span className="spinner" /> Running…</> : '▶  Run Backtest'}
                        </button>
                    </>
                )}
            </div>

            {/* Strategy Guide Modal */}
            <StrategyGuideModal 
                isOpen={isGuideOpen} 
                onClose={() => setIsGuideOpen(false)} 
                strategyKey={strategyKey}
                strategyName={strategies[strategyKey]?.display_name}
            />
        </aside>
    );
}
