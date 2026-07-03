/**
 * BackTestii API Client
 * All requests routed through Vite proxy: /api → FastAPI backend
 */

const BASE = import.meta.env.VITE_API_URL || '/api';
const INTERNAL_KEY = import.meta.env.VITE_INTERNAL_CLIENT_KEY || 'backtestii_internal_secret_key_2026';

function headers() {
    return {
        'Content-Type': 'application/json',
        'X-Internal-Client-Key': INTERNAL_KEY,
    };
}

async function request(method, path, body = null) {
    const opts = { method, headers: headers() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${BASE}${path}`, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

export async function healthCheck() {
    return request('GET', '/health');
}

export async function getStrategies() {
    return request('GET', '/strategies');
}

export async function getIndices() {
    return request('GET', '/indices');
}

export async function getInstruments(exchange) {
    const params = exchange ? `?exchange=${encodeURIComponent(exchange)}` : '';
    return request('GET', `/instruments${params}`);
}

export async function resolveSymbol(name, exchange) {
    const params = new URLSearchParams({ name });
    if (exchange) params.set('exchange', exchange);
    return request('GET', `/instruments/resolve?${params}`);
}

export async function searchInstruments(query) {
    if (!query || query.trim().length < 1) return [];
    const params = new URLSearchParams({ q: query.trim() });
    return request('GET', `/instruments/search?${params}`);
}

export async function getStockData({ ticker, startDate, endDate, assetType = 'stock' }) {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    if (assetType === 'index') {
        return request('GET', `/index-data/${encodeURIComponent(ticker)}?${params}`);
    }
    return request('GET', `/stock-data/${encodeURIComponent(ticker)}?${params}`);
}

export async function getCorporateActions({ ticker }) {
    return request('GET', `/corporate-actions/${encodeURIComponent(ticker)}`);
}

export async function runBacktest({ ticker, strategyKey, strategyParams, startDate, endDate, capital, assetType = 'stock' }) {
    return request('POST', '/backtest', {
        ticker,
        strategy_key: strategyKey,
        strategy_params: strategyParams || {},
        start_date: startDate,
        end_date: endDate,
        capital,
        asset_type: assetType,
    });
}

export async function runComparison({ ticker, startDate, endDate, capital, assetType = 'stock' }) {
    return request('POST', '/comparison', {
        ticker,
        start_date: startDate,
        end_date: endDate,
        capital,
        asset_type: assetType,
    });
}

export async function runTunedComparison({ ticker, startDate, endDate, capital, tunedRuns, includeBuyHold, assetType = 'stock' }) {
    return request('POST', '/tuned-comparison', {
        ticker,
        start_date: startDate,
        end_date: endDate,
        capital,
        tuned_runs: tunedRuns || {},
        include_buy_hold: includeBuyHold || false,
        asset_type: assetType,
    });
}
