import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# Pure HTML/CSS animation (rendered via components.html — no links inside)
# ---------------------------------------------------------------------------
_LANDING_HTML = """\
<!DOCTYPE html>
<html>
<head>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg0:#07090d;--bg1:#0b0f16;
  --stroke:rgba(255,255,255,0.10);--stroke2:rgba(255,255,255,0.18);
  --text0:rgba(255,255,255,0.92);--text1:rgba(255,255,255,0.68);
  --gold:#d6b25e;--gold2:#f0d38a;
}
body{background:transparent;font-family:sans-serif;overflow:hidden}

.wrap{position:relative;width:100%;padding:0 0 0 0}

.hero{text-align:center;margin:-0.5rem 0 0.3rem 0}
.brand{
  font-size:3.1rem;font-weight:800;letter-spacing:-0.03em;
  background:linear-gradient(90deg,rgba(255,255,255,0.94),var(--gold),rgba(255,255,255,0.90));
  -webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 24px rgba(0,0,0,0.55));
}

.stage{
  position:relative;height:780px;border-radius:28px;
  background:
    radial-gradient(1200px 500px at 50% 0%,rgba(214,178,94,0.10),transparent 55%),
    radial-gradient(700px 420px at 60% 40%,rgba(255,255,255,0.05),transparent 60%),
    linear-gradient(180deg,var(--bg1),var(--bg0));
  border:1px solid var(--stroke);
  box-shadow:0 24px 80px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.06);
  overflow:hidden;
}
.stage::before{
  content:"";position:absolute;inset:-40px;
  background:
    radial-gradient(circle at 20% 10%,rgba(214,178,94,0.12),transparent 40%),
    radial-gradient(circle at 70% 25%,rgba(240,211,138,0.10),transparent 45%),
    radial-gradient(circle at 35% 70%,rgba(255,255,255,0.06),transparent 45%);
  filter:blur(18px);opacity:0.9;pointer-events:none;z-index:0;
}

.glow{
  position:absolute;left:50%;top:50%;width:560px;height:560px;
  margin-left:-280px;margin-top:-280px;border-radius:50%;
  background:radial-gradient(circle,rgba(214,178,94,0.10),transparent 55%);
  filter:blur(28px);opacity:0.85;pointer-events:none;z-index:1;
}

.orbit{
  position:absolute;left:50%;top:50%;
  width:540px;height:540px;margin-left:-270px;margin-top:-270px;
  border-radius:50%;border:1px dashed rgba(255,255,255,0.08);
  animation:orbit 10s linear infinite;z-index:2;
}
@keyframes orbit{from{transform:rotate(0deg)}to{transform:rotate(-360deg)}}

.node{
  position:absolute;width:160px;height:160px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  color:var(--text0);
  background:
    radial-gradient(circle at 30% 25%,rgba(240,211,138,0.18),transparent 55%),
    linear-gradient(180deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03));
  border:1px solid var(--stroke2);
  box-shadow:0 18px 44px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.08);
  animation:counterOrbit 10s linear infinite;
}
@keyframes counterOrbit{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}

.node.equity{top:-80px;left:50%;margin-left:-80px}
.node.candle{top:325px;left:37px;margin-left:-80px}
.node.options{top:325px;right:37px;margin-right:-80px}

.node-inner{text-align:center;padding:0 14px}
.node-title{font-weight:800;font-size:1.05rem;letter-spacing:-0.01em}
.node-sub{margin-top:6px;font-size:0.86rem;color:var(--text1)}

.center{
  position:absolute;left:50%;top:50%;
  width:240px;height:240px;margin-left:-120px;margin-top:-120px;
  border-radius:50%;
  background:
    radial-gradient(circle at 30% 25%,rgba(214,178,94,0.14),transparent 55%),
    linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02));
  border:1px solid rgba(255,255,255,0.12);
  box-shadow:0 22px 70px rgba(0,0,0,0.62),inset 0 1px 0 rgba(255,255,255,0.08);
  display:flex;align-items:center;justify-content:center;z-index:3;
}

.clock{
  position:relative;width:170px;height:170px;border-radius:50%;
  border:1px solid rgba(255,255,255,0.16);
  background:
    radial-gradient(circle at 30% 25%,rgba(255,255,255,0.06),transparent 55%),
    radial-gradient(circle at 50% 55%,rgba(0,0,0,0.55),rgba(0,0,0,0.85));
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.07),0 18px 60px rgba(0,0,0,0.55);
}
.clock::before{
  content:"";position:absolute;inset:14px;border-radius:50%;
  border:1px dashed rgba(214,178,94,0.35);opacity:0.8;
}

.hand{position:absolute;left:50%;top:50%;transform-origin:50% 100%;border-radius:999px}
.hand.hour{width:6px;height:54px;margin-left:-3px;margin-top:-54px;background:rgba(214,178,94,0.92);animation:spinAnti 10s linear infinite}
.hand.minute{width:4px;height:72px;margin-left:-2px;margin-top:-72px;background:rgba(255,255,255,0.86);animation:spinAnti 10s linear infinite}
.hand.second{width:2px;height:82px;margin-left:-1px;margin-top:-82px;background:rgba(240,211,138,0.86);animation:spinAnti 10s linear infinite}
@keyframes spinAnti{from{transform:translate(-50%,0) rotate(0deg)}to{transform:translate(-50%,0) rotate(-360deg)}}

.pin{
  position:absolute;left:50%;top:50%;width:10px;height:10px;
  margin-left:-5px;margin-top:-5px;border-radius:50%;
  background:rgba(214,178,94,0.95);box-shadow:0 0 0 4px rgba(214,178,94,0.15);
}

.hint{text-align:center;margin-top:0.25rem;color:rgba(255,255,255,0.50);font-size:0.95rem;letter-spacing:0.01em}

/* Buttons inside animation box */
.btn-wrap{
  position:absolute;
  right:20px;
  bottom:20px;
  display:flex;
  gap:10px;
  z-index:10;
}
.btn{
  padding:8px 16px;
  border-radius:6px;
  border:1px solid var(--stroke2);
  background:linear-gradient(180deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03));
  color:var(--text0);
  font-size:0.85rem;
  font-weight:600;
  cursor:pointer;
  transition:all 0.2s ease;
}
.btn:hover:not(:disabled){
  border-color:var(--gold);
  background:linear-gradient(180deg,rgba(214,178,94,0.15),rgba(214,178,94,0.05));
}
.btn:disabled{
  opacity:0.5;
  cursor:not-allowed;
}
.btn.active{
  border-color:var(--gold);
  background:linear-gradient(180deg,rgba(214,178,94,0.20),rgba(214,178,94,0.08));
}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero"><div class="brand">BackTestii</div></div>
  <div class="stage">
    <div class="glow"></div>
    <div class="orbit">
      <div class="node equity"><div class="node-inner"><div class="node-title">Equity Backtesting</div><div class="node-sub">Enter</div></div></div>
      <div class="node candle"><div class="node-inner"><div class="node-title">Candlestick Backtesting</div><div class="node-sub">Coming soon</div></div></div>
      <div class="node options"><div class="node-inner"><div class="node-title">Options Backtesting</div><div class="node-sub">Coming soon</div></div></div>
    </div>
    <div class="center"><div class="clock"><div class="hand hour"></div><div class="hand minute"></div><div class="hand second"></div><div class="pin"></div></div></div>
  </div>
  <div class="hint">Select a module to continue</div>
</div>
</body>
</html>
"""


def render():
    # Hide sidebar on landing
    st.markdown(
        """<style>
        section[data-testid='stSidebar']{display:none}
        /* Premium button styling to match landing page */
        div[data-testid="stButton"] > button {
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            color: rgba(255,255,255,0.92) !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button:hover:not(:disabled) {
            border-color: #d6b25e !important;
            background: linear-gradient(180deg, rgba(214,178,94,0.15), rgba(214,178,94,0.05)) !important;
            box-shadow: 0 0 20px rgba(214,178,94,0.2) !important;
        }
        div[data-testid="stButton"] > button:disabled {
            background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)) !important;
            border-color: rgba(255,255,255,0.10) !important;
            color: rgba(255,255,255,0.50) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(180deg, rgba(214,178,94,0.20), rgba(214,178,94,0.08)) !important;
            border-color: #d6b25e !important;
            color: rgba(255,255,255,0.94) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: linear-gradient(180deg, rgba(214,178,94,0.30), rgba(214,178,94,0.12)) !important;
            box-shadow: 0 0 25px rgba(214,178,94,0.3) !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    # Detect navigation from URL
    if st.query_params.get("navigate") == "equity":
        st.session_state["app_mode"] = "equity"
        st.query_params.clear()
        st.rerun()
        return

    # Visual animation
    components.html(_LANDING_HTML, height=840, scrolling=False)

    # Streamlit buttons styled to match design
    cols = st.columns([1, 2, 2, 2, 1])
    with cols[1]:
        if st.button("Equity Backtesting", use_container_width=True, type="primary"):
            st.session_state["app_mode"] = "equity"
            st.rerun()
    with cols[2]:
        st.button("Candlestick Backtesting", use_container_width=True, disabled=True)
    with cols[3]:
        st.button("Options Backtesting", use_container_width=True, disabled=True)
