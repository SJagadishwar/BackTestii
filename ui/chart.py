import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from engine.api import STRATEGY_CHART_CONFIG
from engine.api import INDICATOR_PANELS


def render():
    open_trade = st.session_state.get("open_trade")

    chart_container = st.container()

    strategy_key = st.session_state.get("strategy_key")
    chart_cfg = STRATEGY_CHART_CONFIG.get(strategy_key, {})
    overlay_label = chart_cfg.get("overlay_label")  # e.g. "SMA Lines" / "EMA Lines"

    indicator_cfg = INDICATOR_PANELS.get(strategy_key)
    # ---------------- OSCILLATOR AVAILABILITY ----------------
    has_oscillator = indicator_cfg is not None

            
    # ---------------- LEGEND DATA (PRICE OVERLAYS ONLY) ----------------
    # This legend is ONLY for:
    # - Trend Following overlays
    # - Bollinger Mean Reversion
    # Source of truth: chart_config.py → price_overlays

    legend_items = None

    if chart_cfg.get("price_overlays"):
        legend_items = [
            {
                "label": o["label"],
                "color": o["color"],
            }
            for o in chart_cfg["price_overlays"]
        ]

    legend_json = json.dumps(legend_items) if legend_items else "null"


    with chart_container:
        st.subheader("Price Action & Strategy Overlay")
        
        # ⬅️ Create layout row
        left, spacer, right = st.columns([6, 1, 2])

        with right:
            theme_mode = st.toggle(
                "🌙 Night Mode",
                value=True,
                help="Toggle between Day and Night chart theme",
                key="chart_theme_toggle",
            )

        # pass to session (needed for reruns)
        st.session_state["chart_theme"] = "dark" if theme_mode else "light"

        show_all = st.toggle(
            "Show All",
            value=True,
            help="Toggle all chart elements on / off",
        )

        # ---------------- DYNAMIC TOGGLE ROW (NO GAPS) ----------------

        toggle_defs = [
            ("BUY Markers", True),
            ("SELL Markers", True),
            ("Trade Lines", True),
            ("Open Trade", True),
        ]

        if overlay_label:
            toggle_defs.append((overlay_label, True))

        toggle_defs.extend([
            ("Price Levels", True),
            ("Volume", True),
        ])

        if has_oscillator:
            toggle_defs.append(("Oscillator", True))

        cols = st.columns(len(toggle_defs))

        toggle_values = {}

        for col, (label, default) in zip(cols, toggle_defs):
            with col:
                toggle_values[label] = st.toggle(label, value=default)
       
        # ---------------- MAP TO VARIABLES ----------------
        show_buy_ui = toggle_values.get("BUY Markers", False)
        show_sell_ui = toggle_values.get("SELL Markers", False)
        show_trade_lines_ui = toggle_values.get("Trade Lines", False)
        show_open_trade_ui = toggle_values.get("Open Trade", False)

        show_overlay_ui = (
            toggle_values.get(overlay_label, False)
            if overlay_label
            else False
        )

        show_price_levels_ui = toggle_values.get("Price Levels", False)
        show_volume_ui = toggle_values.get("Volume", False)
        show_oscillator_ui = toggle_values.get("Oscillator", False)

        show_buy = show_all and show_buy_ui
        show_sell = show_all and show_sell_ui
        show_trade_lines = show_all and show_trade_lines_ui
        show_open_trade = show_all and show_open_trade_ui
        show_overlay = show_all and show_overlay_ui
        show_price_levels = show_all and show_price_levels_ui
        show_volume = show_all and show_volume_ui
        show_oscillator = show_all and show_oscillator_ui


        price_df = st.session_state.get("price_df")
        trades_df = st.session_state.get("trades_df")   # 🔴 ADD HERE

        if price_df is None or price_df.empty:
            st.info("Run a backtest to load price data.")
            st.stop()
       
        # 🔴 ================= ENTRY / EXIT MARKERS (FROM TRADES) =================
        # ✅ EXACT candle time lookup (CRITICAL)
        price_time_lookup = (
            price_df.reset_index()
            .assign(date=lambda x: x["date"].dt.strftime("%Y-%m-%d"))
            .set_index("date")
        )

        entry_markers = []
        exit_markers = []

        portfolio_df = st.session_state.get("portfolio_df")

        if trades_df is not None and not trades_df.empty:
            for _, row in trades_df.iterrows():
                if pd.notna(row["entry_date"]):
                    entry_date_str = pd.to_datetime(row["entry_date"]).strftime("%Y-%m-%d")

                    entry_markers.append({
                        "time": entry_date_str,                      # 🔑 EXACT candle time
                        "price": float(row["entry_price"]),
                    })


        if trades_df is not None and not trades_df.empty:
            # SELL markers
            for dt in trades_df["exit_date"].dropna():
                exit_date_str = pd.to_datetime(dt).strftime("%Y-%m-%d")

                exit_markers.append({
                    "time": exit_date_str,                        # 🔑 EXACT candle time
                    "price": float(price_df.loc[pd.to_datetime(dt), "close"]),
                })



        # ---------- OPEN TRADE ----------
        if open_trade is not None:
            open_date_str = pd.to_datetime(open_trade["entry_date"]).strftime("%Y-%m-%d")

            entry_markers.append({
                "time": open_date_str,
                "price": float(open_trade["entry_price"]),
            })


        entry_markers_json = json.dumps(entry_markers)
        exit_markers_json = json.dumps(exit_markers)

        toggle_config = {
            "showBuy": show_buy,
            "showSell": show_sell,
            "showTradeLines": show_trade_lines,
            "showOpenTrade": show_open_trade,
            "showOverlay": show_overlay,
            "showPriceLevels": show_price_levels,
            "showVolume": show_volume,
            "showOscillator": show_oscillator and has_oscillator,               
        }

        toggle_config_json = json.dumps(toggle_config)
       
        # ================= STRATEGY INDICATOR DATA =================

        indicator_json = None

        signal_df = st.session_state.get("signal_df")
        strategy_key = st.session_state.get("strategy_key")
        
        # ---------------- OVERLAY DATA (PRICE OVERLAYS) ----------------
        overlay_cfg = chart_cfg.get("price_overlays")

        overlay_data = None
        if overlay_cfg and signal_df is not None:
            overlay_cols = {o["column"] for o in overlay_cfg}

            if overlay_cols.issubset(signal_df.columns):
                overlay_df = (
                    signal_df[list(overlay_cols)]
                    .reset_index()
                    .dropna()
                )
                overlay_df["date"] = overlay_df["date"].dt.strftime("%Y-%m-%d")

                overlay_data = {
                    "overlays": [
                        {
                            "column": o["column"],
                            "label": o["label"],
                            "color": o["color"],
                        }
                        for o in overlay_cfg
                    ],
                    "data": overlay_df.to_dict(orient="records"),
                }

        final_indicator_payload = {
            "oscillator": None,
            "overlays": None,
        }

        # Oscillator
        if indicator_cfg and signal_df is not None:
            lines = indicator_cfg["lines"]
            required_cols = {l["column"] for l in lines if "column" in l}

            if required_cols.issubset(signal_df.columns):
                indicator_df = (
                    signal_df[list(required_cols)]
                    .reset_index()
                    .dropna()
                )
                indicator_df["date"] = indicator_df["date"].dt.strftime("%Y-%m-%d")

                final_indicator_payload["oscillator"] = {
                    "panel": indicator_cfg["panel"],
                    "range": indicator_cfg["range"],
                    "lines": lines,
                    "data": indicator_df.to_dict(orient="records"),
                }

        # Overlays
        if overlay_data:
            final_indicator_payload["overlays"] = overlay_data

        indicator_json = json.dumps(final_indicator_payload)



       
        # 🔴 =========================================================
       
        chart_json = st.session_state.get("chart_json")

        if chart_json is None:
            st.info("Run a backtest to load chart data.")
        else:
            components.html(                

f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />

<script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>

<script>
const RESIZER_HEIGHT = 6;
const DEFAULT_PRICE_RATIO = 0.62;   // 👈 smaller price pane
const DEFAULT_OSC_RATIO   = 0.32;   // 👈 larger oscillator

</script>

<style>

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
}}

#wrapper {{
    position: relative;
    width: 100%;
    height: 900px;
    min-height: 900px;
    overflow: hidden;
}}

/* PRICE PANE */
#price-chart {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1;
    pointer-events: auto;
}}



/* RESIZER */
#pane-resizer {{
    position: absolute;
    left: 0;
    width: 100%;
    height: 6px;
    cursor: row-resize;
    z-index: 2;
    background: rgba(255,255,255,0.12);
}}

#pane-resizer:hover {{
    background: rgba(255,255,255,0.4);
}}

/* OSCILLATOR PANE */
#osc-chart {{
    position: absolute;
    left: 0;
    width: 100%;
    min-height: 180px;
    z-index: 0;
}}

/* CONTROLS */
#controls {{
    position: absolute;
    top: 12px;
    right: 16px;
    z-index: 20;
    display: flex;
    gap: 6px;
    background: rgba(15,18,25,0.85);
    padding: 6px;
    border-radius: 6px;
    backdrop-filter: blur(6px);
}}

#controls button {{
    background: #1f2933;
    color: #d1d4dc;
    border: 1px solid #485c7b;
    padding: 6px 10px;
    cursor: pointer;
    border-radius: 4px;
    font-size: 13px;
}}

#price-resizer {{
    height: 6px;
    cursor: row-resize;
    background: linear-gradient(
        to bottom,
        rgba(255,255,255,0.05),
        rgba(255,255,255,0.30),
        rgba(255,255,255,0.05)
    );
}}

#price-resizer:hover {{
    background: rgba(255,255,255,0.55);
}}

</style>
</head>

<body>

<div id="wrapper">
    <div id="controls">
        <button id="zoom-in">＋</button>
        <button id="zoom-out">－</button>
        <button id="reset">Reset</button>
    </div>
    <!-- OHLC Hover Bar -->
    <div id="ohlc-bar" style="
        position: absolute;
        top: 8px;
        left: 16px;
        z-index: 5;
        font-family: Inter, monospace;
        font-size: 16px;
        color: #d1d4dc;
        background: rgba(15,18,25,0.85);
        padding: 6px 10px;
        border-radius: 6px;
        backdrop-filter: blur(6px);
        pointer-events: none;
    ">
        <span id="ohlc-open"><b>O:</b> --</span>
        <span id="ohlc-high" style="margin-left:6px;"><b>H:</b> --</span>
        <span id="ohlc-low"  style="margin-left:6px;"><b>L:</b> --</span>
        <span id="ohlc-close"style="margin-left:6px;"><b>C:</b> --</span>
        <span id="ohlc-change" style="margin-left:10px;"><b>Δ:</b> -- (--)</span>
        <span id="ohlc-vol" style="margin-left:10px;"><b>Vol:</b> --</span>
    </div>

    <!-- ✅ DATE LABEL MUST BE GLOBAL -->
    <div id="date-label" style="
        position: absolute;
        z-index: 50;
        font-family: Inter, monospace;
        font-size: 13px;
        color: #d1d4dc;
        background: rgba(15,18,25,0.85);
        padding: 4px 10px;
        border-radius: 6px;
        backdrop-filter: blur(6px);
        pointer-events: none;
        display: none;
        white-space: nowrap;
    ">
    --
    </div>


    <!-- Oscillator Value Overlay -->
    <div id="osc-value" style="
        position: absolute;
        left: 16px;
        top: 0px;  
        z-index: 6;
        font-family: Inter, monospace;
        font-size: 14px;
        color: #FFD166;
        background: rgba(15,18,25,0.85);
        padding: 4px 8px;
        border-radius: 6px;
        backdrop-filter: blur(6px);
        display: none;
        pointer-events: none;
    ">
        RSI: --
    </div>


    <div id="price-chart"></div>
    
    <div id="pane-resizer"></div>

    <div id="osc-chart"></div>





    <!-- Indicator Legend -->
    <div id="indicator-legend" style="
        position: absolute;
        top: 60px;
        left: 16px;
        z-index: 6;
        font-family: Inter, monospace;
        font-size: 13px;
        background: rgba(15,18,25,0.85);
        padding: 6px 10px;
        border-radius: 6px;
        backdrop-filter: blur(6px);
        display: none;
    ">
    </div>
</div>

<script>
/* ================= DATA ================= */
const chartTheme = "{st.session_state.get('chart_theme', 'dark')}";
const chartData = JSON.parse(`{chart_json}`);

// ================= CANONICAL CANDLE LOOKUP (FIX) =================
// All candles indexed by YYYY-MM-DD
const candleByDate = {{}};
// 🔥 GLOBAL SHARED CROSSHAIR INDEX
let currentCrosshairIndex = null;
chartData.forEach(d => {{
    candleByDate[d.date] = d;
}});

// Normalize all LightweightCharts time formats → YYYY-MM-DD
function logicalToIndex(logical) {{
    if (logical === null || logical === undefined) return null;
    const idx = Math.round(logical);
    if (idx < 0 || idx >= chartData.length) return null;
    return idx;
}}

function normalizeTime(param) {{

    if (!param || param.time === undefined || param.time === null)
        return null;

    // param.time is already the candle date
    if (typeof param.time === 'string') {{
        currentCrosshairIndex = chartData.findIndex(d => d.date === param.time);
        return param.time;
    }}

    // BusinessDay format (LightweightCharts)
    if (typeof param.time === 'object') {{
        const y = param.time.year;
        const m = String(param.time.month).padStart(2, '0');
        const d = String(param.time.day).padStart(2, '0');

        const dateStr = `${{y}}-${{m}}-${{d}}`;

        currentCrosshairIndex = chartData.findIndex(c => c.date === dateStr);
        return dateStr;
    }}

    return null;
}}

const dateLabelEl = document.getElementById('date-label');

function handleUnifiedCrosshair(param) {{
    if (!param || param.time === undefined || param.time === null) {{
        dateLabelEl.style.display = 'none';
        return;
    }}

    const dateStr = normalizeTime(param);
    if (!dateStr) {{
        dateLabelEl.style.display = 'none';
        return;
    }}

    const wrapper = document.getElementById('wrapper');
    const oscEl = document.getElementById('osc-chart');

    const labelWidth = dateLabelEl.offsetWidth || 60;

    // X aligned with crosshair
    let x = param.point.x - labelWidth / 2;
    x = Math.max(4, Math.min(x, wrapper.clientWidth - labelWidth - 4));
    dateLabelEl.style.left = x + 'px';

    // --- Position date label at bottom of PRICE pane ---
    const priceEl = document.getElementById('price-chart');
    const wrapRect = wrapper.getBoundingClientRect();
    const priceRect = priceEl.getBoundingClientRect();

    // place label slightly below price pane bottom
    let y = priceRect.bottom - wrapRect.top + 6;

    // 🔥 CRITICAL FIX: clamp inside wrapper
    const maxY = wrapper.clientHeight - dateLabelEl.offsetHeight - 4;

    if (y > maxY) {{
        y = maxY;
    }}

    dateLabelEl.style.top = y + 'px';

    dateLabelEl.textContent = dateStr;
    dateLabelEl.style.display = 'block';
    positionOscValue();

    // ---- OHLC update ----
    if (currentCrosshairIndex !== null) {{
        const bar = chartData[currentCrosshairIndex];
        const prev = currentCrosshairIndex > 0 ? chartData[currentCrosshairIndex - 1] : null;
        updateOHLC(bar, prev);
        updateOscillatorValue(currentCrosshairIndex);
    }}
}}
   
       

const entryMarkers = JSON.parse(`{entry_markers_json}`);
const exitMarkers = JSON.parse(`{exit_markers_json}`);
const indicatorPayload = JSON.parse(`{indicator_json}`);
// 🔥 INDEXED INDICATOR DATA
let oscillatorData = null;

if (indicatorPayload && indicatorPayload.oscillator && indicatorPayload.oscillator.data) {{
    oscillatorData = indicatorPayload.oscillator.data;
}}
const toggles = JSON.parse(`{toggle_config_json}`);
const legendItems = JSON.parse(`{legend_json}`);

/* ================= THEME COLORS ================= */

const THEMES = {{
    dark: {{
        background: '#0e1117',
        text: '#e6edf3',
        grid: '#1f2933',
        controlBg: 'rgba(15,18,25,0.85)',
    }},
    light: {{
        background: '#f4f6f9',          // soft neutral grey
        text: '#1e293b',                // softer dark blue-grey
        grid: '#e2e8f0',
        controlBg: 'rgba(248,250,252,0.92)',  // subtle frosted white
    }},
}};

const activeTheme = THEMES[chartTheme] || THEMES.dark;

document.getElementById('ohlc-bar').style.background =
    activeTheme.controlBg;

document.getElementById('controls').style.background =
    activeTheme.controlBg;



/* ================= CHART ================= */
const chartContainer = document.getElementById('price-chart');

const priceChart = LightweightCharts.createChart(
    document.getElementById('price-chart'),
    {{
        layout: {{
            background: {{ color: activeTheme.background }},
            textColor: activeTheme.text,
        }},
        grid: {{
            vertLines: {{ visible: false }},
            horzLines: {{ visible: false }},
        }},
        rightPriceScale: {{
            borderVisible: false,
            scaleMargins: {{
                top: 0.06,
                bottom: 0.04,
            }},
        }},
        timeScale: {{
            visible: true, 
            timeVisible: true,
            secondsVisible: false,
            borderVisible: true,
            borderColor: '#1f2933',
            rightBarStaysOnScroll: false,
            fixLeftEdge: false,
            fixRightEdge: false,
        }},
        crosshair: {{
            mode: LightweightCharts.CrosshairMode.Magnet,
            vertLine: {{
                visible: true,
                labelVisible: false,
            }},
            horzLine: {{
                visible: true,
                labelVisible: false,
            }},
        }},
    }}
);
const oscChart = LightweightCharts.createChart(
    document.getElementById('osc-chart'),
    {{
        layout: {{
            background: {{ color: activeTheme.background }},
            textColor: activeTheme.text,
        }},
        grid: {{
            vertLines: {{ visible: false }},
            horzLines: {{ visible: false }},
        }},
        rightPriceScale: {{
            borderVisible: true,
            autoScale: false,
        }},
        timeScale: {{
            visible: false,          // 🔑 CRITICAL
            timeVisible: false,      // 🔑 CRITICAL
            secondsVisible: false,
            borderVisible: true,
            borderColor: '#1f2933',
        }},
        crosshair: {{
            vertLine: {{
                visible: true,
                labelVisible: false,  // 🔑 do NOT show date here
            }},
            horzLine: {{
                visible: true,
                labelVisible: false,
            }},
        }},
    }}
);


oscChart.resize(
    document.getElementById('osc-chart').clientWidth,
    document.getElementById('osc-chart').clientHeight
);

function syncCrosshair(sourceChart, targetChart, param) {{

    if (!param || param.time === undefined || param.time === null) {{
        return;
    }}

    targetChart.setCrosshairPosition(param.time);
}}




/* ================= SERIES ================= */
const candleSeries = priceChart.addCandlestickSeries({{
    upColor: '#00A86B',
    downColor: '#FF3B30',
    borderUpColor: '#00A86B',
    borderDownColor: '#FF3B30',
    wickUpColor: '#00A86B',
    wickDownColor: '#FF3B30',
    lastValueVisible: false,
}});

candleSeries.setData(
    chartData.map(d => ({{
        time: d.date,
        open: Number(d.open),
        high: Number(d.high),
        low: Number(d.low),
        close: Number(d.close),
    }}))
);


/* ================= OHLC UI ================= */
const oOpen   = document.getElementById('ohlc-open');
const oHigh   = document.getElementById('ohlc-high');
const oLow    = document.getElementById('ohlc-low');
const oClose  = document.getElementById('ohlc-close');
const oChange = document.getElementById('ohlc-change');
const oVol    = document.getElementById('ohlc-vol');


function fmt(n) {{
    return n === null || n === undefined ? '--' : n.toFixed(2);
}}

function fmtVol(v) {{
    if (v === null || v === undefined) return '--';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(2) + 'K';
    return v.toString();
}}

function updateOHLC(bar, prevBar) {{
    if (!bar) return;

    const bullish = bar.close >= bar.open;
    const main = bullish ? '#26A69A' : '#EF5350';

    oOpen.textContent  = `O: ${{fmt(bar.open)}}`;
    oHigh.textContent  = `H: ${{fmt(bar.high)}}`;
    oLow.textContent   = `L: ${{fmt(bar.low)}}`;
    oClose.textContent = `C: ${{fmt(bar.close)}}`;
    oVol.textContent   = `Vol: ${{fmtVol(bar.volume)}}`;

    [oOpen, oHigh, oLow, oClose].forEach(el => el.style.color = main);
    oVol.style.color = main;

    if (prevBar) {{
        const diff = bar.close - prevBar.close;
        const pct  = (diff / prevBar.close) * 100;
        oChange.textContent =
            `Δ: ${{diff >= 0 ? '+' : ''}}${{diff.toFixed(2)}} (${{pct >= 0 ? '+' : ''}}${{pct.toFixed(2)}}%)`;
        oChange.style.color = main;
    }} else {{
        oChange.textContent = 'Δ: -- (--)';
    }}
}}


/* ================= OHLC / VOL / % CHANGE (FINAL, INDEX-BASED) ================= */

priceChart.subscribeCrosshairMove(param => {{
    handleUnifiedCrosshair(param);

    // Sync oscillator ONLY if it exists
    if (
        indicatorPayload &&
        indicatorPayload.oscillator &&
        toggles.showOscillator
    ) {{
        oscChart.timeScale().setVisibleLogicalRange(
            priceChart.timeScale().getVisibleLogicalRange()
        );

        syncCrosshair(priceChart, oscChart, param);
    }}
}});

if (
    indicatorPayload &&
    indicatorPayload.oscillator
) {{
    oscChart.subscribeCrosshairMove(param => {{
        handleUnifiedCrosshair(param);
        syncCrosshair(oscChart, priceChart, param);
    }});
}}

priceChart.subscribeClick(param => {{
    const sp = param && param.seriesPrices;
    if (!sp) return;

    const p = sp.get(candleSeries);
    if (!p) return;

    let idx = null;
    if (typeof param.time === 'number') {{
        idx = Math.round(param.time);
    }} else if (typeof param.time === 'string') {{
        idx = chartData.findIndex(d => d.date === param.time);
    }}

    if (idx === null || idx < 0 || idx >= chartData.length) return;

    const bar = chartData[idx];
    const prev = idx > 0 ? chartData[idx - 1] : null;

    updateOHLC(bar, prev);
}});

const oscValueEl = document.getElementById('osc-value');

if (
    indicatorPayload &&
    indicatorPayload.oscillator &&
    Array.isArray(indicatorPayload.oscillator.lines) &&
    indicatorPayload.oscillator.lines.length > 0 &&
    toggles.showOscillator
) {{


    const oscLines = indicatorPayload.oscillator.lines || [];


    // Use FIRST line with a column (strategy-specific)
    const activeLine = oscLines.find(l => l.isPrimary) || oscLines[0];

    if (!activeLine) {{
        oscValueEl.style.display = 'none';
    }} else {{

        const col = activeLine.column;
        const label = activeLine.label || col.toUpperCase();
    }}
}}

function positionOscValue() {{
    const oscEl = document.getElementById('osc-chart');
    const wrapper = document.getElementById('wrapper');

    if (!oscEl || !wrapper) return;

    const oscRect = oscEl.getBoundingClientRect();
    const wrapRect = wrapper.getBoundingClientRect();

    // Position label just above oscillator panel
    oscValueEl.style.top =
        (oscRect.top - wrapRect.top - 28) + 'px';
}}

function updateOscillatorValue(index) {{

    if (!oscillatorData || index === null) {{
        oscValueEl.style.display = 'none';
        return;
    }}

    const candleDate = chartData[index].date;

    const row = oscillatorData.find(r => r.date === candleDate);

    if (!row) {{
        oscValueEl.style.display = 'none';
        return;
    }}

    const keys = Object.keys(row).filter(k => k !== 'date');
    if (!keys.length) return;

    const val = row[keys[0]];

    // 🔥 Dynamic oscillator label
    let oscLabel = '';

    if (
        indicatorPayload &&
        indicatorPayload.oscillator &&
        Array.isArray(indicatorPayload.oscillator.lines)
    ) {{
        const primaryLine =
            indicatorPayload.oscillator.lines.find(l => l.isPrimary) ||
            indicatorPayload.oscillator.lines[0];

        oscLabel = primaryLine.label || primaryLine.column.toUpperCase();
    }}

    oscValueEl.innerHTML = `${{oscLabel}}: <b>${{val.toFixed(2)}}</b>`;
    oscValueEl.style.display = 'block';
}}
        
/* ================= PRICE LEVELS ================= */
const priceLines = [];

// 🔴 DEFAULT LTP (ALWAYS VISIBLE WHEN TOGGLE IS OFF)
const defaultLTP = candleSeries.createPriceLine({{
    price: chartData[chartData.length - 1].close,
    color: '#EF5350',
    lineWidth: 1,
    lineStyle: LightweightCharts.LineStyle.Solid,
    axisLabelVisible: true,
    title: 'LTP',
}});

// 🔵 EXTRA LEVELS ONLY WHEN TOGGLE IS ON
if (toggles.showPriceLevels) {{
    candleSeries.removePriceLine(defaultLTP);

    priceLines.push(
        candleSeries.createPriceLine({{
            price: chartData[chartData.length - 1].close,
            color: '#3DA5FF',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            axisLabelVisible: true,
            title: 'LTP',
        }})
    );
}}

/* ================= ENTRY / EXIT MARKERS ================= */
const tradeMarkers = [];

if (toggles.showBuy) {{
    entryMarkers.forEach(m => {{
        tradeMarkers.push({{
            time: m.time,
            position: 'belowBar',
            price: m.price,
            shape: 'arrowUp',
            color: '#00FF9C',
            text: 'BUY',
        }});
    }});
}}

if (toggles.showSell) {{
    exitMarkers.forEach(m => {{
        tradeMarkers.push({{
            time: m.time,
            position: 'aboveBar',
            price: m.price,
            shape: 'arrowDown',
            color: '#FF2E63',
            text: 'SELL',
        }});
    }});
}}

tradeMarkers.sort((a, b) => a.time.localeCompare(b.time));
candleSeries.setMarkers(tradeMarkers);

// expose for debugging
window.tradeMarkers = tradeMarkers;

/* ================= VOLUME ================= */
let volumeSeries = null;

if (toggles.showVolume) {{
    volumeSeries = priceChart.addHistogramSeries({{
        priceScaleId: 'vol',
        priceFormat: {{ type: 'volume' }},
    }});

    volumeSeries.priceScale().applyOptions({{
        scaleMargins: {{ top: 0.80, bottom: 0.02 }},
    }});

    volumeSeries.setData(
        chartData.map(d => ({{
            time: d.date,
            value: d.volume || 0,
            color: d.close >= d.open ? 'rgba(38,166,154,0.45)' : 'rgba(239,83,80,0.45)',
        }}))
    );
}}

/* ================= OSCILLATOR CHART ================= */

if (indicatorPayload && indicatorPayload.oscillator && toggles.showOscillator) {{

    const indicatorData = indicatorPayload.oscillator;

    // ---------------- PRICE SCALE ----------------
    oscChart.priceScale('right').applyOptions({{
        autoScale: false,
        minValue: indicatorData.range[0],
        maxValue: indicatorData.range[1],
        borderVisible: true,
        scaleMargins: {{ top: 0.15, bottom: 0.15 }},
    }});


    // ---------------- OSCILLATOR LINES ----------------
    indicatorData.lines.forEach(line => {{

        // Main oscillator line
        if (line.column) {{
            const series = oscChart.addLineSeries({{
                color: line.color,
                lineWidth: 1.5,
                lastValueVisible: false,
                priceLineVisible: false,
            }});

            series.setData(
                indicatorData.data.map(d => ({{
                    time: d.date,
                    value: d[line.column],
                }}))
            );
        }}

        // Reference levels (RSI 30 / 70, etc.)
        if (line.level !== undefined) {{
            const lvl = oscChart.addLineSeries({{
                color: line.color,
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                lastValueVisible: false,
                priceLineVisible: false,
            }});

            lvl.setData(
                indicatorData.data.map(d => ({{
                    time: d.date,
                    value: line.level,
                }}))
            );
        }}
        requestAnimationFrame(positionOscValue);
    }});
}}


/* ================= TRADE LINES ================= */
const tradeLineSeries = [];

if (toggles.showTradeLines) {{
    for (let i = 0; i < entryMarkers.length; i++) {{
        const entry = entryMarkers[i];
        const exit = exitMarkers[i];
        if (!exit) continue;

        const isProfit = exit.price >= entry.price;

        const line = priceChart.addLineSeries({{
            color: isProfit ? '#00FF9C' : '#FF2E63',
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        }});

        line.setData([
            {{ time: entry.time, value: entry.price }},
            {{ time: exit.time, value: exit.price }},
        ]);

        tradeLineSeries.push(line);
    }}
}}

/* ================= OPEN TRADE LINE ================= */
if (toggles.showOpenTrade && entryMarkers.length > exitMarkers.length) {{
    const openEntry = entryMarkers[entryMarkers.length - 1];
    const lastCandle = chartData[chartData.length - 1];

    const openLine = priceChart.addLineSeries({{
        color: '#FFD166',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
    }});

    openLine.setData([
        {{ time: openEntry.time, value: openEntry.price }},
        {{ time: lastCandle.date, value: lastCandle.close }},
    ]);
}}

/* ================= STRATEGY PRICE OVERLAYS ================= */

if (indicatorPayload && indicatorPayload.overlays && toggles.showOverlay) {{
    const overlays = indicatorPayload.overlays.overlays;
    const data = indicatorPayload.overlays.data;

    overlays.forEach(overlay => {{
        const series = priceChart.addLineSeries({{
            color: overlay.color,
            lineWidth: 1.5,
            priceLineVisible: toggles.showPriceLevels,
            lastValueVisible: toggles.showPriceLevels,
            crosshairMarkerVisible: false,
            priceLineWidth: 1,
        }});

        series.setData(
            data.map(d => ({{
                time: d.date,
                value: d[overlay.column],
            }}))
        );
    }});
}}


/* ================= PRICE OVERLAY LEGEND (CANONICAL) ================= */

const legend = document.getElementById('indicator-legend');

function renderLegend(items, visible) {{
    if (!items || items.length === 0 || !visible) {{
        legend.style.display = 'none';
        return;
    }}

    // ✅ THIS WAS MISSING
    legend.style.display = 'block';

    legend.innerHTML = items.map(item => `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="
                width:22px;
                height:2px;
                background:${{item.color}};
                display:inline-block;
            "></span>
            <span style="
                color:${{item.color}};
                font-weight:500;
            ">
                ${{item.label}}
            </span>
        </div>
    `).join('');
}}


// Initial render
renderLegend(legendItems, toggles.showOverlay);


/* ================= ZOOM (CORRECT WAY) ================= */
const timeScale = priceChart.timeScale();

let isChartReady = false;

function markChartReady() {{
    const range = timeScale.getVisibleLogicalRange();
    if (range && range.from !== null && range.to !== null) {{
        isChartReady = true;
    }} else {{
        requestAnimationFrame(markChartReady);
    }}
}}


function zoomIn() {{
    const r = timeScale.getVisibleLogicalRange();
    if (!r || r.from === null || r.to === null) return;

    const span = r.to - r.from;
    const middle = (r.from + r.to) / 2;

    timeScale.setVisibleLogicalRange({{
        from: middle - span * 0.35,
        to: middle + span * 0.35,
    }});
}}

function zoomOut() {{
    const r = timeScale.getVisibleLogicalRange();
    if (!r || r.from === null || r.to === null) return;

    const span = r.to - r.from;
    const middle = (r.from + r.to) / 2;

    timeScale.setVisibleLogicalRange({{
        from: middle - span * 0.65,
        to: middle + span * 0.65,
    }});
}}


let zoomQueued = false;

function runZoomSafely(fn) {{
    if (zoomQueued) return;
    zoomQueued = true;

    requestAnimationFrame(() => {{
        fn();
        zoomQueued = false;
    }});
}}

document.getElementById('zoom-in').onclick = () =>
    runZoomSafely(zoomIn);

document.getElementById('zoom-out').onclick = () =>
    runZoomSafely(zoomOut);

document.getElementById('reset').onclick = () =>
    runZoomSafely(() => timeScale.fitContent());


/* ================= FULLSCREEN (DOUBLE CLICK) ================= */
const wrapper = document.getElementById('wrapper');

wrapper.addEventListener('dblclick', () => {{
    if (!document.fullscreenElement) {{
        wrapper.requestFullscreen();
    }} else {{
        document.exitFullscreen();
    }}
}});

/* ================= FULLSCREEN RESIZE (CANONICAL) ================= */
document.addEventListener('fullscreenchange', () => {{
    requestAnimationFrame(() => {{
        requestAnimationFrame(() => {{
            const wrapper = document.getElementById('wrapper');
            const priceEl = document.getElementById('price-chart');
            const oscEl   = document.getElementById('osc-chart');

            wrapper.style.height = '100%';

            applyLayout(true);

            priceChart.resize(wrapper.clientWidth, priceEl.clientHeight);

            if (toggles.showOscillator && oscEl.clientHeight > 0) {{
                oscChart.resize(wrapper.clientWidth, oscEl.clientHeight);
            }}

            priceChart.timeScale().fitContent();
        }});
    }});
}});



/* ================= OSCILLATOR DRAG RESIZER ================= */

const resizer = document.getElementById('pane-resizer');

let dragging = null;

function startDrag(type) {{
    dragging = type;
    document.body.style.cursor = 'row-resize';
}}

function stopDrag() {{
    if (!dragging) return;

    toggles.priceHeightRatio =
        priceEl.clientHeight / wrapper.clientHeight;

    toggles.oscHeightRatio =
        oscEl.clientHeight / wrapper.clientHeight;

    dragging = null;
    document.body.style.cursor = 'default';
}}


document.addEventListener('mouseup', stopDrag);

document.getElementById('pane-resizer')
    .addEventListener('mousedown', (e) => {{
        e.preventDefault();
        startDrag('osc');
    }});

document.addEventListener('mousemove', (e) => {{
    if (!dragging) return;
   
    const rect = wrapper.getBoundingClientRect();
    const total = wrapper.clientHeight;

    // 👇 mouse position relative to wrapper
    const y = e.clientY - rect.top;

    const MIN_PRICE = 220;   // 👈 allow price pane to shrink
    const MIN_OSC   = 180;


    if (dragging === 'osc') {{
        // dragging middle resizer → resize oscillator
        let oscHeight = Math.max(
            MIN_OSC,
            Math.min(total - MIN_PRICE - RESIZER_HEIGHT, total - y)
        );

        let priceHeight = total - oscHeight - RESIZER_HEIGHT;

        priceEl.style.height = priceHeight + 'px';
        oscEl.style.height   = oscHeight + 'px';

        resizer.style.top = priceHeight + 'px';
        oscEl.style.top = (priceHeight + RESIZER_HEIGHT) + 'px';


        priceChart.applyOptions({{ height: priceHeight }});


        oscChart.applyOptions({{ height: oscHeight }});

        toggles.priceHeightRatio = priceHeight / total;
        toggles.oscHeightRatio   = oscHeight / total;
    }}
    
    requestAnimationFrame(positionOscValue);
}});

// ================= TIME SCALE SYNC (LOGICAL ↔ LOGICAL) =================

let syncInProgress = false;

// Price → Oscillator
priceChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
    if (!toggles.showOscillator || syncInProgress || !range) return;

    syncInProgress = true;

    requestAnimationFrame(() => {{
        oscChart.timeScale().setVisibleLogicalRange(range);
        syncInProgress = false;
    }});
}});



// ---------- INITIAL HEIGHT FIX (SAFE) ----------
const wrapperEl = document.getElementById('wrapper');
const priceEl   = document.getElementById('price-chart');
const oscEl     = document.getElementById('osc-chart');

if (toggles.priceHeightRatio === undefined) {{
    toggles.priceHeightRatio = DEFAULT_PRICE_RATIO;
}}

if (toggles.oscHeightRatio === undefined) {{
    toggles.oscHeightRatio = DEFAULT_OSC_RATIO;
}}

function applyLayout(force = false) {{
    if (dragging) return;

    const total = wrapperEl.clientHeight;
    const oscVisible =
        indicatorPayload &&
        indicatorPayload.oscillator &&
        toggles.showOscillator;




    let priceHeight, oscHeight;

    if (oscVisible) {{
        priceHeight = Math.max(280, Math.floor(total * toggles.priceHeightRatio));
        oscHeight   = Math.max(180, total - priceHeight - RESIZER_HEIGHT);
    }} else {{
        priceHeight = total;
        oscHeight = 0;
        oscEl.style.top = total + 'px';   // move it out of view
    }}

    priceEl.style.top = '0px';
    priceEl.style.height = priceHeight + 'px';

    resizer.style.top = priceHeight + 'px';

    oscEl.style.top = (priceHeight + RESIZER_HEIGHT) + 'px';
    oscEl.style.height = oscHeight + 'px';

    priceChart.applyOptions({{ height: priceHeight }});


    if (oscVisible) oscChart.applyOptions({{ height: oscHeight }});

    requestAnimationFrame(positionOscValue);
}}

/* ================= INIT ================= */
setTimeout(() => {{
    applyLayout(true);

    priceChart.resize(
        wrapperEl.clientWidth,
        priceEl.clientHeight
    );

    if (indicatorPayload && indicatorPayload.oscillator) {{
        oscChart.resize(
            wrapperEl.clientWidth,
            oscEl.clientHeight
        );
    }}

    priceChart.timeScale().fitContent();
}}, 100);

</script>
</body>
</html>
""",
height=2200,
scrolling=True,
)
