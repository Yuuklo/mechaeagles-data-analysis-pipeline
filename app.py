import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import inch

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="MechaEagles | Data Pipeline",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Rajdhani:wght@600;700&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #05060a;
    color: #c8d8e8;
    font-size: 16px;
}

/* Full-bleed dark bg — kills Streamlit side margins */
[data-testid="stAppViewContainer"] {
    background-color: #05060a;
}
[data-testid="stSidebar"] { display: none; }

/* Scanline overlay */
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 3px,
        rgba(212,80,10,0.018) 3px,
        rgba(212,80,10,0.018) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* Corner glow — top-left */
body::after {
    content: "";
    position: fixed;
    top: -120px; left: -120px;
    width: 480px; height: 480px;
    background: radial-gradient(circle, rgba(212,80,10,0.14) 0%, transparent 70%);
    pointer-events: none;
    z-index: 1;
    animation: cornerPulse 6s ease-in-out infinite;
}
@keyframes cornerPulse {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50%       { opacity: 1;   transform: scale(1.15); }
}

/* streak canvas removed */

/* Remove Streamlit top gap, full-width, no side padding cap */
.main .block-container {
    padding: 0 2.5rem 3rem !important;
    max-width: 100% !important;
    background-color: #05060a;
}
#root > div:first-child { margin-top: 0 !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* ── Header ── */
.me-header {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 1.8rem 2rem 1.4rem;
    border-bottom: 1px solid #252530;
    margin-bottom: 1.8rem;
    background: linear-gradient(90deg, rgba(212,80,10,0.06) 0%, transparent 60%);
}
/* logo — subtle static shadow */
.me-header img {
    filter: drop-shadow(0 0 5px rgba(212,80,10,0.25));
    transition: filter 0.3s;
}
.me-header img:hover {
    filter: drop-shadow(0 0 9px rgba(212,80,10,0.45));
}
.me-brand { line-height: 1.15; }
.me-brand-name {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3.0rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    color: #d4500a;
    text-transform: uppercase;
}
.me-brand-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.92rem;
    color: #6a6a80;
    letter-spacing: 0.22em;
    text-transform: uppercase;
}

/* ── Section headers ── */
.me-section {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #d4500a;
    padding: 12px 18px 12px 18px;
    margin: 2.4rem 0 1.2rem;
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(90deg, rgba(212,80,10,0.10) 0%, rgba(212,80,10,0.02) 70%, transparent 100%);
    border-left: 4px solid #d4500a;
    border-top: 1px solid rgba(212,80,10,0.18);
    border-bottom: 1px solid rgba(212,80,10,0.08);
    border-radius: 0 4px 4px 0;
}
.me-section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(212,80,10,0.25), transparent);
    margin-left: 8px;
}

/* ── Upload zone ── */
.me-upload-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.15em;
    color: #7a7a90;
    text-transform: uppercase;
    margin-bottom: 4px;
}

/* ── CVT stat cards ── */
.cvt-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 1rem;
}
.cvt-card {
    background: #0b0d14;
    border: 1px solid #252530;
    border-left: 3px solid #d4500a;
    padding: 14px 18px;
    border-radius: 4px;
}
.cvt-card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #6a6a80;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.cvt-card-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #d4500a;
}
.cvt-card-unit {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #7a7a90;
    margin-left: 4px;
}
.cvt-card.run2 { border-left-color: #38bdf8; }
.cvt-card.run2 .cvt-card-value { color: #38bdf8; }

/* ── Anomaly table ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #252530 !important;
    border-radius: 4px;
    background: #0b0d14;
}

/* ── Plotly chart containers ── */
div[data-testid="stPlotlyChart"] {
    border: 1px solid #252530;
    border-radius: 4px;
    background: #05060a;
    padding: 4px;
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] > button,
div[data-testid="stButton"] > button {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    color: #d4500a !important;
    border: 1px solid #d4500a !important;
    border-radius: 3px !important;
    padding: 0.5rem 1.8rem !important;
    transition: all 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stButton"] > button:hover {
    background: rgba(212,80,10,0.09) !important;
    box-shadow: 0 0 16px rgba(212,80,10,0.20) !important;
}

/* ── Radio ── */
div[data-testid="stRadio"] label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #7a7a90;
}

/* Streamlit default element overrides */
h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; }
.stAlert { border-radius: 4px; }

/* ── Force Space Grotesk everywhere Streamlit injects its own font ── */
div[data-testid="stFileUploader"] *,
div[data-testid="stFileUploaderDropzoneInstructions"] *,
div[data-testid="stFileUploaderDropzoneInstructions"],
div[data-testid="uploadedFile"],
div[data-testid="uploadedFile"] *,
div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] p,
div[data-testid="stFileUploader"] span:not(button span) {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #6a6a80 !important;
    letter-spacing: 0.06em !important;
}
div[data-testid="stFileUploader"] button span {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #d4500a !important;
}
/* Dataframe table font */
div[data-testid="stDataFrame"] *,
div[data-testid="stDataFrame"] table,
div[data-testid="stDataFrame"] th,
div[data-testid="stDataFrame"] td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}
div[data-testid="stDataFrame"] th {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #d4500a !important;
}


/* ── CVT shimmer ── */
@keyframes shimmer {
  0%   { color: #d4500a; text-shadow: none; }
  40%  { color: #ff7a2a; text-shadow: 0 0 10px rgba(255,80,100,0.7), 0 0 20px rgba(212,80,10,0.4); }
  60%  { color: #ff9044; text-shadow: 0 0 14px rgba(255,100,120,0.8), 0 0 28px rgba(224,53,69,0.5); }
  100% { color: #d4500a; text-shadow: none; }
}
@keyframes shimmer-teal {
  0%   { color: #38bdf8; text-shadow: none; }
  40%  { color: #7dd3fc; text-shadow: 0 0 10px rgba(255,160,60,0.7), 0 0 20px rgba(56,189,248,0.4); }
  60%  { color: #93dcff; text-shadow: 0 0 14px rgba(120,225,255,0.8), 0 0 28px rgba(56,189,248,0.5); }
  100% { color: #38bdf8; text-shadow: none; }
}
.cvt-card-value {
    cursor: default;
    transition: color 0.15s;
}
.cvt-card:hover .cvt-card-value {
    animation: shimmer 1.1s ease-in-out infinite;
}
.cvt-card.run2:hover .cvt-card-value {
    animation: shimmer-teal 1.1s ease-in-out infinite;
}

/* ── Hex grid background pattern ── */
.main .block-container::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(212,80,10,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,80,10,0.05) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Header glow line ── */
.me-header {
    position: relative;
}
.me-header::after {
    content: "";
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, #d4500a 0%, rgba(224,53,69,0.3) 40%, transparent 70%);
}

/* ── Section header glow dot ── */
.me-section::before {
    content: "";
    display: inline-block;
    width: 18px;
    height: 2px;
    background: #d4500a;
    margin-right: 10px;
    vertical-align: middle;
    opacity: 0.9;
}

/* ── CVT card hover lift ── */
.cvt-card {
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.cvt-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(212,80,10,0.18);
}
.cvt-card.run2:hover {
    box-shadow: 0 4px 20px rgba(56,189,248,0.18);
}

/* ── Chart container hover glow ── */
div[data-testid="stPlotlyChart"]:hover {
    border-color: rgba(212,80,10,0.4) !important;
    box-shadow: 0 0 18px rgba(212,80,10,0.10);
    transition: border-color 0.2s, box-shadow 0.2s;
}

/* ── Tab styling — sliding bar only ── */
div[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(212,80,10,0.18) !important;
    gap: 0 !important;
}
div[data-testid="stTabs"] button {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: rgba(106,106,128,0.55) !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    padding: 8px 16px !important;
    transition: color 0.25s, border-color 0.25s !important;
    position: relative !important;
}
div[data-testid="stTabs"] button:hover {
    color: #d4500a !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d4500a !important;
    border-bottom: 2px solid #d4500a !important;
}
/* Slide the active indicator with a smooth transition */
div[data-testid="stTabs"] button::after {
    content: "" !important;
    position: absolute !important;
    bottom: -1px; left: 0; right: 0 !important;
    height: 2px !important;
    background: #d4500a !important;
    transform: scaleX(0) !important;
    transition: transform 0.3s cubic-bezier(0.22,1,0.36,1) !important;
    transform-origin: left !important;
}
div[data-testid="stTabs"] button[aria-selected="true"]::after {
    transform: scaleX(1) !important;
}

/* logo pulse removed */

/* ── Dataframe hover row highlight ── */
div[data-testid="stDataFrame"] tr:hover td {
    background: rgba(212,80,10,0.07) !important;
}

/* ── Compact file uploader ── */
div[data-testid="stFileUploader"] {
    background: #0b0d14 !important;
    border: 1px dashed rgba(212,80,10,0.35) !important;
    border-radius: 6px !important;
    padding: 0 !important;
    transition: border-color 0.2s, background 0.2s !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #d4500a !important;
    background: rgba(212,80,10,0.05) !important;
}
div[data-testid="stFileUploader"] section {
    padding: 8px 14px !important;
    min-height: unset !important;
}
div[data-testid="stFileUploader"] button {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    padding: 4px 14px !important;
    height: auto !important;
    border-radius: 3px !important;
    color: #d4500a !important;
    border-color: #d4500a !important;
    background: transparent !important;
}
div[data-testid="stFileUploaderDropzoneInstructions"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #6a6a80 !important;
}
div[data-testid="uploadedFile"] {
    background: rgba(212,80,10,0.07) !important;
    border: 1px solid rgba(224,53,69,0.2) !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #d4500a !important;
    padding: 4px 10px !important;
}

/* ── Dot grid canvas (drawn by JS) ── */
#me-dotgrid {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
}

</style>

<div class="me-header">
  <img src="data:image/png;base64,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" alt="MechaEagles logo" style="height:68px;width:auto;flex-shrink:0;object-fit:contain;image-rendering:crisp-edges;filter:drop-shadow(0 0 10px rgba(212,80,10,0.6));">
  <div class="me-brand">
    <div class="me-brand-name">MechaEagles</div>
    <div class="me-brand-sub">Post-Run Data Analysis Pipeline</div>
  </div>
</div>
<div class="me-streak-canvas"></div>
<canvas id="me-dotgrid"></canvas>
<script>
(function(){
  var c=document.getElementById("me-dotgrid");
  if(!c)return;
  var ctx=c.getContext("2d");
  var mx=-9999,my=-9999;
  var SPACING=28,DOT_R=1.1,GLOW_R=120;
  var BASE="rgba(60,60,80,0.18)",HOT="212,80,10";
  function resize(){c.width=window.innerWidth;c.height=window.innerHeight;}
  resize();
  window.addEventListener("resize",resize);
  window.addEventListener("mousemove",function(e){mx=e.clientX;my=e.clientY;});
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    var cols=Math.ceil(c.width/SPACING)+1;
    var rows=Math.ceil(c.height/SPACING)+1;
    for(var r=0;r<rows;r++){
      for(var cl=0;cl<cols;cl++){
        var x=cl*SPACING,y=r*SPACING;
        var dx=x-mx,dy=y-my;
        var dist=Math.sqrt(dx*dx+dy*dy);
        var t=Math.max(0,1-dist/GLOW_R);
        var alpha=0.08+t*0.45;
        var radius=DOT_R+t*1.2;
        ctx.beginPath();
        ctx.arc(x,y,radius,0,Math.PI*2);
        if(t>0.01){ctx.fillStyle="rgba("+HOT+","+alpha.toFixed(2)+")";}
        else{ctx.fillStyle=BASE;}
        ctx.fill();
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
""", unsafe_allow_html=True)

# ── Plotly dark theme ───────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="#05060a",
    plot_bgcolor="#07090f",
    font=dict(family="Space Grotesk, sans-serif", color="#8aaabb", size=11),
    xaxis=dict(gridcolor="#1a2d3d", linecolor="#1a3a4a", tickcolor="#1a3a4a", zeroline=False),
    yaxis=dict(gridcolor="#1a2d3d", linecolor="#1a3a4a", tickcolor="#1a3a4a", zeroline=False),
    legend=dict(
        bgcolor="rgba(10,14,23,0.85)",
        bordercolor="#1a3a4a",
        borderwidth=1,
        font=dict(size=11),
        orientation="h",
        yanchor="top", y=-0.18,
        xanchor="left", x=0,
    ),
    margin=dict(l=50, r=20, t=40, b=80),
    title_font=dict(family="Rajdhani, sans-serif", size=14, color="#c8d8e8"),
)

RUN1_COLOR = "#d4500a"
RUN2_COLOR = "#38bdf8"

# ── Column config ───────────────────────────────────────────────────────────
COLUMN_ALIASES = {
    "time_s":   ["timestamp_ms", "time", "timestamp", "t", "seconds", "sec", "time_s"],
    "speed":    ["speed", "vehicle_speed", "wheel_speed", "mph", "kph", "speed_mph", "speed_kph"],
    "rpm":      ["rpm", "engine_rpm", "motor_rpm"],
    "temp":     ["temp", "temperature", "cvt_temp", "engine_temp", "temp_c", "temp_f"],
    "gx":       ["accel_x_g", "gx", "g_x", "accel_x", "ax", "gforce_x"],
    "gy":       ["accel_y_g", "gy", "g_y", "accel_y", "ay", "gforce_y"],
    "voltage":  ["voltage_v", "voltage", "vbat", "battery_voltage", "vbatt", "batt_v"],
}

DTYPE_MAP = {
    "time_s": float, "speed": float, "rpm": float,
    "temp": float, "gx": float, "gy": float, "voltage": float,
}

# ── Data functions ──────────────────────────────────────────────────────────
def normalize_columns(df):
    rename_map = {}
    actual_cols = [c.lower().strip() for c in df.columns]
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in actual_cols:
                original = df.columns[actual_cols.index(alias.lower())]
                rename_map[original] = canonical
                break
    missing = [c for c in COLUMN_ALIASES if c not in rename_map.values()]
    if missing:
        raise ValueError(f"Could not find columns: {missing}")
    return df.rename(columns=rename_map)

def enforce_dtypes(df):
    for col, dtype in DTYPE_MAP.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
    return df

def group_events(df_flagged, values, event_type, threshold_str, gap=200):
    if df_flagged.empty:
        return []
    events, group_indices = [], []
    for idx in df_flagged.index:
        if not group_indices or (df_flagged.loc[idx, 'time_s'] - df_flagged.loc[group_indices[-1], 'time_s']) <= gap:
            group_indices.append(idx)
        else:
            peak_idx = values.loc[group_indices].idxmax()
            events.append({"time_s": df_flagged.loc[peak_idx, 'time_s'], "type": event_type,
                           "value": round(values.loc[peak_idx], 3), "threshold": threshold_str})
            group_indices = [idx]
    if group_indices:
        peak_idx = values.loc[group_indices].idxmax()
        events.append({"time_s": df_flagged.loc[peak_idx, 'time_s'], "type": event_type,
                       "value": round(values.loc[peak_idx], 3), "threshold": threshold_str})
    return events

def detect_anomalies(df):
    RPM_DROP_THRESHOLD, TEMP_SPIKE_THRESHOLD, MAX_G_THRESHOLD, RPM_WINDOW = 1000, 15, 0.75, 10
    anomalies = []
    rpm_rolling_mean = df['rpm'].rolling(window=RPM_WINDOW, center=True).mean()
    rpm_drop_mask = (rpm_rolling_mean - df['rpm']) > RPM_DROP_THRESHOLD
    anomalies += group_events(df[rpm_drop_mask], rpm_rolling_mean - df['rpm'], "rpm_drop", f">{RPM_DROP_THRESHOLD} below rolling mean")
    temp_delta = df['temp'].diff().abs()
    temp_spike_mask = temp_delta > TEMP_SPIKE_THRESHOLD
    anomalies += group_events(df[temp_spike_mask], temp_delta, "temp_spike", f">{TEMP_SPIKE_THRESHOLD}° change per step")
    g_magnitude = np.sqrt(df['gx']**2 + df['gy']**2)
    max_g_mask = g_magnitude > MAX_G_THRESHOLD
    anomalies += group_events(df[max_g_mask], g_magnitude, "max_g", f">{MAX_G_THRESHOLD}G combined magnitude")
    if anomalies:
        return pd.DataFrame(anomalies).sort_values("time_s").reset_index(drop=True)
    return pd.DataFrame(columns=["time_s", "type", "value", "threshold"])

def get_cvt_engagement(df):
    mask = df['speed'] > 0.5
    return mask.idxmax() if mask.any() else None

# ── Plot functions ──────────────────────────────────────────────────────────
def make_line_plot(df1, df2, col, title, yaxis_title, cvt_idx1=None, cvt_idx2=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df1['time_s'], y=df1[col], mode='lines', name='Run 1',
        line=dict(color=RUN1_COLOR, width=1.8)
    ))
    if cvt_idx1 is not None and cvt_idx1 in df1.index:
        cvt_x = df1.loc[cvt_idx1, 'time_s']
        fig.add_vline(x=cvt_x, line_dash="dot", line_color=RUN1_COLOR, line_width=1,
                      annotation_text="CVT·1", annotation_font_size=10,
                      annotation_font_color=RUN1_COLOR, annotation_position="top right")
    if df2 is not None:
        fig.add_trace(go.Scatter(
            x=df2['time_s'], y=df2[col], mode='lines', name='Run 2',
            line=dict(color=RUN2_COLOR, width=1.8, dash='dot')
        ))
        if cvt_idx2 is not None and cvt_idx2 in df2.index:
            cvt_x2 = df2.loc[cvt_idx2, 'time_s']
            # offset annotation to avoid collision with Run 1
            fig.add_vline(x=cvt_x2, line_dash="dot", line_color=RUN2_COLOR, line_width=1,
                          annotation_text="CVT·2", annotation_font_size=10,
                          annotation_font_color=RUN2_COLOR, annotation_position="bottom right")
    fig.update_layout(**PLOT_LAYOUT, title=title,
                      yaxis_title=yaxis_title, xaxis_title="Time (ms)")
    n_pts = len(df1)
    step = max(1, n_pts // 40)
    frames = []
    for i in range(step, n_pts + step, step):
        fd = [go.Scatter(x=df1['time_s'].iloc[:i], y=df1[col].iloc[:i])]
        if df2 is not None:
            fd.append(go.Scatter(x=df2['time_s'].iloc[:i], y=df2[col].iloc[:i]))
        frames.append(go.Frame(data=fd))
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(
        type="buttons", showactive=False, visible=False,
        buttons=[dict(label="Play", method="animate",
                      args=[None, dict(frame=dict(duration=16, redraw=False),
                                       fromcurrent=True,
                                       transition=dict(duration=0))])])])
    return fig

def make_gforce_plot(df1, df2=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df1['gx'], y=df1['gy'], mode='markers', name='Run 1',
        marker=dict(color=df1['speed'], colorscale=[[0, '#0e0500'], [1, RUN1_COLOR]],
                    size=5, opacity=0.8,
                    colorbar=dict(title=dict(text='Speed R1', font=dict(size=10, color='#d4500a')),
                                  thickness=12, len=0.42, y=0.78, yanchor='middle',
                                  x=1.02, tickfont=dict(size=9), outlinewidth=0,
                                  bgcolor='rgba(0,0,0,0)'))
    ))
    if df2 is not None:
        fig.add_trace(go.Scatter(
            x=df2['gx'], y=df2['gy'], mode='markers', name='Run 2',
            marker=dict(color=df2['speed'], colorscale=[[0, '#001418'], [1, RUN2_COLOR]],
                        size=5, opacity=0.8, symbol='diamond',
                        colorbar=dict(title=dict(text='Speed R2', font=dict(size=10, color='#38bdf8')),
                                      thickness=12, len=0.42, y=0.28, yanchor='middle',
                                      x=1.02, tickfont=dict(size=9), outlinewidth=0,
                                      bgcolor='rgba(0,0,0,0)'))
        ))
    fig.add_vline(x=0, line_color='#2a4a5a', line_dash='dash', line_width=0.8)
    fig.add_hline(y=0, line_color='#2a4a5a', line_dash='dash', line_width=0.8)
    axis_style = dict(gridcolor="#1a2d3d", linecolor="#1a3a4a", tickcolor="#1a3a4a", zeroline=False)
    gforce_layout = {k: v for k, v in PLOT_LAYOUT.items() if k not in ('xaxis', 'yaxis')}
    fig.update_layout(
        **gforce_layout,
        title="G-Force XY Scatter",
        xaxis=dict(**axis_style, range=[-2, 2], title="Gx (long)"),
        yaxis=dict(**axis_style, range=[-2, 2], title="Gy (lat)"),
    )
    return fig


# ── Anomaly table CSS (injected into page when data is loaded) ──────────────
ANOMALY_CSS = (
    '<style>\n'
    '@keyframes slideInLeft {\n'
    '    from { opacity: 0; transform: translateX(-60px); }\n'
    '    to   { opacity: 1; transform: translateX(0); }\n'
    '}\n'
    '.me-anomaly-panel {\n'
    '    animation: slideInLeft 0.75s cubic-bezier(0.22,1,0.36,1) both;\n'
    '}\n'
    '.me-anomaly-wrap { margin-top: 4px; }\n'
    '.me-anomaly-table {\n'
    '    width: 100%; border-collapse: collapse;\n'
    "    font-family: 'JetBrains Mono', monospace;\n"
    '    font-size: 0.78rem;\n'
    '}\n'
    '.me-anomaly-table thead tr {\n'
    '    background: rgba(212,80,10,0.15);\n'
    '    border-bottom: 1px solid #d4500a;\n'
    '}\n'
    '.me-anomaly-table thead th {\n'
    "    font-family: 'Space Grotesk', sans-serif;\n"
    '    font-size: 0.72rem; font-weight: 600;\n'
    '    letter-spacing: 0.12em; text-transform: uppercase;\n'
    '    color: #d4500a; padding: 7px 10px;\n'
    '    text-align: left; white-space: nowrap;\n'
    '}\n'
    '.me-anomaly-table tbody tr {\n'
    '    border-bottom: 1px solid rgba(255,255,255,0.04);\n'
    '    transition: background 0.15s;\n'
    '}\n'
    '.me-anomaly-table tbody tr:hover { background: rgba(212,80,10,0.07); }\n'
    '.me-anomaly-table tbody td {\n'
    '    padding: 8px 10px; color: #c8d8e8; vertical-align: middle;\n'
    '}\n'
    '.me-badge {\n'
    '    display: inline-block; font-size: 0.72rem; font-weight: 600;\n'
    '    letter-spacing: 0.06em; text-transform: uppercase;\n'
    '    padding: 0; background: none; border: none;\n'
    '}\n'
    '.me-badge-rpm  { color: #ff7a2a; }\n'
    '.me-badge-temp { color: #f87171; }\n'
    '.me-badge-g    { color: #38bdf8; }\n'
    '.me-badge-r1   { color: #d4500a; font-size: 0.72rem; }\n'
    '.me-badge-r2   { color: #38bdf8; font-size: 0.72rem; }\n'
    '</style>\n'
)

def build_anomaly_table_html(pdf_summary):
    rows = []
    for _, row in pdf_summary.iterrows():
        atype = str(row.get('type', ''))
        if 'rpm' in atype:
            badge = '<span class="me-badge me-badge-rpm">RPM Drop</span>'
        elif 'temp' in atype:
            badge = '<span class="me-badge me-badge-temp">Temp Spike</span>'
        else:
            badge = '<span class="me-badge me-badge-g">Max-G</span>'
        run_val = str(row.get('run', ''))
        rb = '<span class="me-badge me-badge-r1">R1</span>' if '1' in run_val else '<span class="me-badge me-badge-r2">R2</span>'
        ts = row.get('time_s', 0)
        val = row.get('value', '')
        thr = row.get('threshold', '')
        rows.append(
            f'<tr><td>{rb}</td><td>{ts:.0f}</td><td>{badge}</td>'
            f'<td>{val}</td><td style="color:#6a6a80;font-size:0.62rem">{thr}</td></tr>'
        )
    body = '\n'.join(rows)
    return (
        '<div class="me-anomaly-panel me-anomaly-wrap">'
        '<table class="me-anomaly-table">'
        '<thead><tr><th>Run</th><th>Time&nbsp;(ms)</th><th>Type</th><th>Value</th><th>Threshold</th></tr></thead>'
        f'<tbody>{body}</tbody></table></div>'
    )


def create_all_plots(df1, cvt_idx1, df2=None, cvt_idx2=None):
    return {
        "Speed":       make_line_plot(df1, df2, 'speed',   'Speed vs Time',       'Speed (mph)',    cvt_idx1, cvt_idx2),
        "RPM":         make_line_plot(df1, df2, 'rpm',     'RPM vs Time',         'RPM',            cvt_idx1, cvt_idx2),
        "Temperature": make_line_plot(df1, df2, 'temp',    'Temperature Trend',   'Temp (°F)',      cvt_idx1, cvt_idx2),
        "Voltage":     make_line_plot(df1, df2, 'voltage', 'Voltage',             'Voltage (V)',    cvt_idx1, cvt_idx2),
        "G-Force":     make_gforce_plot(df1, df2),
    }

def _apply_white_bg(fig):
    """Return a copy of fig with white paper and plot background for PDF export."""
    import copy
    fig2 = copy.deepcopy(fig)
    fig2.update_layout(
        paper_bgcolor='#ffffff',
        plot_bgcolor='#f8f8f8',
        font=dict(color='#1a1a1a'),
        xaxis=dict(gridcolor='#e0e0e0', linecolor='#cccccc', tickcolor='#cccccc', zeroline=False),
        yaxis=dict(gridcolor='#e0e0e0', linecolor='#cccccc', tickcolor='#cccccc', zeroline=False),
        legend=dict(bgcolor='rgba(255,255,255,0.9)', bordercolor='#dddddd', borderwidth=1,
                    font=dict(color='#1a1a1a')),
        title_font=dict(color='#1a1a1a'),
    )
    return fig2

def create_pdf_plots(df1, cvt_idx1, df2=None, cvt_idx2=None):
    """Same plots as create_all_plots but with white backgrounds for PDF."""
    plots = create_all_plots(df1, cvt_idx1, df2, cvt_idx2)
    return {k: _apply_white_bg(v) for k, v in plots.items()}

# ── PDF export ──────────────────────────────────────────────────────────────
from reportlab.platypus import HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import datetime

def _pdf_styles():
    base = getSampleStyleSheet()

    white   = rl_colors.HexColor('#ffffff')
    orange  = rl_colors.HexColor('#d4500a')
    orange2 = rl_colors.HexColor('#f5813a')
    dark    = rl_colors.HexColor('#1a1a1a')
    muted   = rl_colors.HexColor('#666666')
    panel   = rl_colors.HexColor('#fdf6f0')
    border  = rl_colors.HexColor('#e8c4a0')
    stripe  = rl_colors.HexColor('#fff8f3')

    title = ParagraphStyle('METitle',
        fontName='Helvetica-Bold', fontSize=28, leading=32,
        textColor=orange, spaceAfter=2, alignment=TA_LEFT,
        letterSpacing=4)
    subtitle = ParagraphStyle('MESubtitle',
        fontName='Helvetica', fontSize=8, leading=12,
        textColor=muted, spaceAfter=16, alignment=TA_LEFT,
        letterSpacing=2)
    section = ParagraphStyle('MESection',
        fontName='Helvetica-Bold', fontSize=8, leading=12,
        textColor=orange, spaceBefore=20, spaceAfter=8,
        alignment=TA_LEFT, letterSpacing=3)
    body = ParagraphStyle('MEBody',
        fontName='Helvetica', fontSize=9, leading=14,
        textColor=dark, spaceAfter=4)
    meta_key = ParagraphStyle('MEMetaKey',
        fontName='Helvetica-Bold', fontSize=7,
        textColor=muted, leading=11)
    meta_val = ParagraphStyle('MEMetaVal',
        fontName='Helvetica-Bold', fontSize=12,
        textColor=orange, leading=15)

    return dict(title=title, subtitle=subtitle, section=section,
                body=body, meta_key=meta_key, meta_val=meta_val,
                white=white, orange=orange, orange2=orange2,
                dark=dark, muted=muted, panel=panel, border=border,
                stripe=stripe,
                teal=orange, light=dark)


def _divider(color):
    return HRFlowable(width='100%', thickness=0.5, color=color, spaceAfter=6, spaceBefore=2)


def _meta_table(rows, s):
    """rows = list of (label, value) tuples; renders as a clean two-row card grid"""
    col_w = (7.0 / len(rows)) * inch
    header_row = [Paragraph(k, s['meta_key']) for k, _ in rows]
    value_row  = [Paragraph(v, s['meta_val']) for _, v in rows]
    t = Table([header_row, value_row], colWidths=[col_w]*len(rows))
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), s['panel']),
        ('BOX',           (0,0), (-1,-1), 0.5,  s['border']),
        ('INNERGRID',     (0,0), (-1,-1), 0.25, s['border']),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR',     (0,0), (-1,-1), s['dark']),
    ]))
    return t


def _anomaly_table(summary_df, s):
    col_labels = ['Run', 'Time (ms)', 'Type', 'Value', 'Threshold']
    col_keys   = ['run', 'time_s', 'type', 'value', 'threshold']
    col_widths = [0.6*inch, 0.9*inch, 1.0*inch, 0.8*inch, 2.7*inch]

    header = [Paragraph(c, ParagraphStyle('AH', fontName='Helvetica-Bold',
              fontSize=8, textColor=rl_colors.HexColor('#ffffff'), leading=12)) for c in col_labels]
    rows = [header]
    for _, row in summary_df.iterrows():
        style = ParagraphStyle('AC', fontName='Helvetica', fontSize=8,
                               textColor=s['dark'], leading=12)
        rows.append([Paragraph(str(row.get(k, '')), style) for k in col_keys])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    stripe = s.get('stripe', rl_colors.HexColor('#fff8f3'))
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  s['orange']),
        ('BACKGROUND',    (0,1), (-1,-1), rl_colors.HexColor('#ffffff')),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [rl_colors.HexColor('#ffffff'), stripe]),
        ('BOX',           (0,0), (-1,-1), 0.5,  s['border']),
        ('LINEBELOW',     (0,0), (-1,0),  0.8,  s['orange']),
        ('INNERGRID',     (0,1), (-1,-1), 0.25, s['border']),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR',     (0,1), (-1,-1), s['dark']),
    ]))
    return t


class _DarkPageTemplate:
    """White background with burnt orange header bar, diagonal streak, and footer."""
    @staticmethod
    def on_page(canvas, doc):
        w, h = letter
        L = 0.75*inch
        ORANGE = rl_colors.HexColor('#d4500a')
        ORANGE_LIGHT = rl_colors.HexColor('#f5813a')
        DARK = rl_colors.HexColor('#1a1a1a')
        MUTED = rl_colors.HexColor('#999999')
        canvas.saveState()
        # white background
        canvas.setFillColor(rl_colors.HexColor('#ffffff'))
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        # top header bar — taller to avoid collision (52px)
        BAR_H = 52
        canvas.setFillColor(ORANGE)
        canvas.rect(0, h-BAR_H, w, BAR_H, fill=1, stroke=0)
        # diagonal streak accents — parallelograms
        shear = 14
        for sx, sw, col in [
            (w*0.58, 18, '#b03008'),
            (w*0.64,  7, '#c04010'),
            (w*0.75, 24, '#b03008'),
            (w*0.81,  9, '#c04010'),
        ]:
            by, bh = h-BAR_H, BAR_H
            canvas.setFillColor(rl_colors.HexColor(col))
            path = canvas.beginPath()
            path.moveTo(sx + shear, by + bh)
            path.lineTo(sx + sw + shear, by + bh)
            path.lineTo(sx + sw, by)
            path.lineTo(sx, by)
            path.close()
            canvas.drawPath(path, fill=1, stroke=0)
        # brand name — top line of header
        canvas.setFont('Helvetica-Bold', 15)
        canvas.setFillColor(rl_colors.HexColor('#ffffff'))
        canvas.drawString(L, h - 22, 'MECHAEAGLES')
        # subtitle — second line, well below brand name
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(rl_colors.HexColor('#ffe0c8'))
        canvas.drawString(L, h - 38, 'POST-RUN DATA ANALYSIS PIPELINE')
        # thin rule below header
        canvas.setStrokeColor(ORANGE_LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(0, h-BAR_H-2, w, h-BAR_H-2)
        # left accent stripe
        canvas.setFillColor(ORANGE)
        canvas.rect(0, 32, 2, h - BAR_H - 32, fill=1, stroke=0)
        # footer bar
        canvas.setFillColor(rl_colors.HexColor('#f7ede4'))
        canvas.rect(0, 0, w, 32, fill=1, stroke=0)
        canvas.setStrokeColor(ORANGE)
        canvas.setLineWidth(0.5)
        canvas.line(0, 32, w, 32)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(L, 12, 'MECHAEAGLES  ·  POST-RUN DATA ANALYSIS PIPELINE')
        canvas.setFillColor(ORANGE)
        canvas.drawRightString(w-L, 12, f'PAGE {doc.page}')
        canvas.restoreState()


@st.cache_data(show_spinner="Generating PDF report...")
def build_pdf_report(df1, cvt_idx1, df2, cvt_idx2, summary_df):
    plots = create_pdf_plots(df1, cvt_idx1, df2, cvt_idx2)
    s = _pdf_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.9*inch, bottomMargin=0.7*inch,
    )

    two_runs = df2 is not None
    now = datetime.datetime.now().strftime('%Y-%m-%d  %H:%M')
    elements = []

    # ── Cover block ──────────────────────────────────────────────────────────
    elements += [
        Paragraph('MECHAEAGLES', s['title']),
        Paragraph('POST-RUN DATA ANALYSIS REPORT  ·  ' + now, s['subtitle']),
        _divider(s['teal']),
        Spacer(1, 6),
    ]

    # ── Run metadata cards ────────────────────────────────────────────────────
    elements.append(Paragraph('RUN OVERVIEW', s['section']))
    run1_meta = [
        ('Run', 'Run 1'),
        ('Samples', str(len(df1))),
        ('Duration', f"{df1['time_s'].max():.0f} ms"),
        ('Max Speed', f"{df1['speed'].max():.1f} mph"),
        ('Max RPM', f"{df1['rpm'].max():.0f}"),
        ('Max Temp', f"{df1['temp'].max():.1f} °F"),
    ]
    elements.append(_meta_table(run1_meta, s))

    if two_runs:
        elements.append(Spacer(1, 8))
        run2_meta = [
            ('Run', 'Run 2'),
            ('Samples', str(len(df2))),
            ('Duration', f"{df2['time_s'].max():.0f} ms"),
            ('Max Speed', f"{df2['speed'].max():.1f} mph"),
            ('Max RPM', f"{df2['rpm'].max():.0f}"),
            ('Max Temp', f"{df2['temp'].max():.1f} °F"),
        ]
        elements.append(_meta_table(run2_meta, s))

    # ── CVT engagement ────────────────────────────────────────────────────────
    elements.append(Paragraph('CVT ENGAGEMENT', s['section']))
    cvt_rows = []
    if cvt_idx1 is not None and cvt_idx1 in df1.index:
        cvt_rows.append(('CVT-1 Time', f"{df1.loc[cvt_idx1,'time_s']:.0f} ms"))
        cvt_rows.append(('CVT-1 RPM',  f"{df1.loc[cvt_idx1,'rpm']:.0f}"))
    if two_runs and cvt_idx2 is not None and cvt_idx2 in df2.index:
        cvt_rows.append(('CVT-2 Time', f"{df2.loc[cvt_idx2,'time_s']:.0f} ms"))
        cvt_rows.append(('CVT-2 RPM',  f"{df2.loc[cvt_idx2,'rpm']:.0f}"))
    if cvt_rows:
        elements.append(_meta_table(cvt_rows, s))

    # ── Anomaly table ─────────────────────────────────────────────────────────
    elements.append(Paragraph('FLAGGED ANOMALIES', s['section']))
    if not summary_df.empty:
        elements.append(_anomaly_table(summary_df, s))
    else:
        elements.append(Paragraph('No anomalies detected.', s['body']))

    elements.append(Spacer(1, 14))
    _divider(s['border'])

    # ── Plots ─────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 10))
    elements.append(_divider(s['orange']))
    elements.append(Paragraph('TELEMETRY PLOTS', s['section']))
    elements.append(Spacer(1, 6))

    plot_label_style = ParagraphStyle(
        'PlotLabel', fontName='Helvetica-Bold', fontSize=10,
        textColor=s['orange'], leading=14, letterSpacing=1.5,
        spaceAfter=4, spaceBefore=18)
    plot_caption_style = ParagraphStyle(
        'PlotCaption', fontName='Helvetica', fontSize=9,
        textColor=s['muted'], leading=13, spaceAfter=6)

    plot_descriptions = {
        'Speed':       'Vehicle speed over run duration. CVT engagement point marked as dashed vertical line.',
        'RPM':         'Engine RPM over run duration. Plateau region indicates belt engagement threshold.',
        'Temperature': 'Drivetrain temperature trend across the run. Sudden rises are flagged as anomalies.',
        'Voltage':     'System voltage over run duration. Sustained sag may indicate electrical load issues.',
        'G-Force':     'Lateral (Gy) vs longitudinal (Gx) G-force. Colour-coded by speed. Circle = Run 1, Diamond = Run 2.',
    }

    for plot_title, fig in plots.items():
        img_bytes = fig.to_image(format='png', width=1000, height=500, scale=2)
        img = Image(io.BytesIO(img_bytes), width=7.0*inch, height=3.5*inch)
        img.hAlign = 'LEFT'
        block = [
            Paragraph(plot_title.upper(), plot_label_style),
            Paragraph(plot_descriptions.get(plot_title, ''), plot_caption_style),
            img,
            Spacer(1, 8),
        ]
        elements.append(KeepTogether(block))

    doc.build(elements, onFirstPage=_DarkPageTemplate.on_page,
              onLaterPages=_DarkPageTemplate.on_page)
    buffer.seek(0)
    return buffer.getvalue()

# ── Main app ────────────────────────────────────────────────────────────────
def main():
    # ── Upload section ──────────────────────────────────────────────────────
    st.markdown('<div class="me-section">Data Input</div>', unsafe_allow_html=True)

    # Track whether run1 was already loaded on last render
    had_run1_before = st.session_state.get("had_run1", False)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown('<div class="me-upload-label">Run 1 — required</div>', unsafe_allow_html=True)
        f1 = st.file_uploader("Run 1", type=["csv"], key="file1", label_visibility="collapsed")

    # Run 2 uploader: visually dimmed until Run 1 is present
    run2_disabled = f1 is None
    with col_u2:
        st.markdown(
            '<div class="me-upload-label" style="opacity:{op}">Run 2 — optional (enables comparison mode)</div>'.format(
                op="0.35" if run2_disabled else "1"
            ),
            unsafe_allow_html=True
        )
        if run2_disabled:
            # Render a dimmed placeholder instead of a real uploader
            st.markdown(
                '<div style="border:1px dashed rgba(212,80,10,0.12);border-radius:6px;'
                'padding:8px 14px;background:rgba(212,80,10,0.02);opacity:0.35;'
                'font-family:JetBrains Mono,monospace;font-size:0.78rem;color:#4a4a5a;">'
                'Add Run 1 first</div>',
                unsafe_allow_html=True
            )
            f2 = None
        else:
            f2 = st.file_uploader("Run 2", type=["csv"], key="file2", label_visibility="collapsed")

    # Load data — only proceed if at least one CSV is uploaded
    df1, df2 = None, None
    if f1:
        df1 = pd.read_csv(f1)
    if f2:
        df2 = pd.read_csv(f2)

    # If Run1 is gone but Run2 is present, promote Run2 → Run1
    if df1 is None and df2 is not None:
        df1, df2 = df2, None
        # Clear file2 state so it doesn't ghost
        if "file2" in st.session_state:
            del st.session_state["file2"]

    # If no CSV uploaded, show a prompt and stop
    if df1 is None:
        st.session_state["had_run1"] = False
        st.markdown(
            '<div id="me-empty-prompt" style="text-align:center;padding:4rem 2rem;color:#4a4a5a;'
            'font-family:JetBrains Mono,monospace;font-size:0.85rem;letter-spacing:0.1em;">'
            'Upload a CSV file above to begin analysis.</div>',
            unsafe_allow_html=True
        )
        return

    # Track whether we just got run1 for the first time (scroll trigger)
    just_got_run1 = not had_run1_before
    st.session_state["had_run1"] = True

    df1 = enforce_dtypes(normalize_columns(df1))
    if df2 is not None:
        df2 = enforce_dtypes(normalize_columns(df2))

    two_runs = df2 is not None

    # Session state reset on new data
    current_key = f"{len(df1)}_{df1['time_s'].sum()}" + (
        f"_{len(df2)}_{df2['time_s'].sum()}" if two_runs else "")
    if st.session_state.get("data_key") != current_key:
        st.session_state["data_key"] = current_key
        st.session_state["pdf_requested"] = False

    # ── CVT Engagement ──────────────────────────────────────────────────────
    cvt_idx1 = get_cvt_engagement(df1)
    cvt_idx2 = get_cvt_engagement(df2) if two_runs else None

    st.markdown('<div class="me-section">CVT Engagement</div>', unsafe_allow_html=True)
    cvt_html = '<div class="cvt-grid">'
    if cvt_idx1 is not None and cvt_idx1 in df1.index:
        t1, r1 = df1.loc[cvt_idx1, 'time_s'], df1.loc[cvt_idx1, 'rpm']
        cvt_html += (
            '<div class="cvt-card">'
            '<div class="cvt-card-label">Run 1 — Engagement Time</div>'
            f'<div class="cvt-card-value">{t1:.0f}<span class="cvt-card-unit">ms</span></div></div>'
            '<div class="cvt-card">'
            '<div class="cvt-card-label">Run 1 — Engagement RPM</div>'
            f'<div class="cvt-card-value">{r1:.0f}<span class="cvt-card-unit">rpm</span></div></div>'
        )
    if two_runs and cvt_idx2 is not None and cvt_idx2 in df2.index:
        t2, r2 = df2.loc[cvt_idx2, 'time_s'], df2.loc[cvt_idx2, 'rpm']
        cvt_html += (
            '<div class="cvt-card run2">'
            '<div class="cvt-card-label">Run 2 — Engagement Time</div>'
            f'<div class="cvt-card-value">{t2:.0f}<span class="cvt-card-unit">ms</span></div></div>'
            '<div class="cvt-card run2">'
            '<div class="cvt-card-label">Run 2 — Engagement RPM</div>'
            f'<div class="cvt-card-value">{r2:.0f}<span class="cvt-card-unit">rpm</span></div></div>'
        )
    cvt_html += '</div>'
    st.markdown(cvt_html, unsafe_allow_html=True)

    # ── Detect anomalies ────────────────────────────────────────────────────
    summary1 = detect_anomalies(df1)
    summary1.insert(0, 'run', 'Run 1')
    if two_runs:
        summary2 = detect_anomalies(df2)
        summary2.insert(0, 'run', 'Run 2')
        pdf_summary = pd.concat([summary1, summary2], ignore_index=True)
    else:
        pdf_summary = summary1.copy()

    has_anomalies = not pdf_summary.empty

    # ── Anomaly CSS (always inject so animation class exists) ────────────────
    st.markdown(ANOMALY_CSS, unsafe_allow_html=True)

    # ── Section header ───────────────────────────────────────────────────────
    st.markdown('<div class="me-section">Anomalies & Plots</div>', unsafe_allow_html=True)

    if has_anomalies:
        left_col, right_col = st.columns([1, 2], gap="medium")
        with left_col:
            st.markdown(build_anomaly_table_html(pdf_summary), unsafe_allow_html=True)
        with right_col:
            plots = create_all_plots(df1, cvt_idx1, df2, cvt_idx2)
            tabs = st.tabs(["Speed", "RPM", "Temperature", "Voltage", "G-Force"])
            for tab, key in zip(tabs, ["Speed", "RPM", "Temperature", "Voltage", "G-Force"]):
                with tab:
                    st.plotly_chart(plots[key], use_container_width=True)
    else:
        plots = create_all_plots(df1, cvt_idx1, df2, cvt_idx2)
        tabs = st.tabs(["Speed", "RPM", "Temperature", "Voltage", "G-Force"])
        for tab, key in zip(tabs, ["Speed", "RPM", "Temperature", "Voltage", "G-Force"]):
            with tab:
                st.plotly_chart(plots[key], use_container_width=True)

    # Scroll to plots section on first upload (inject AFTER content renders)
    if just_got_run1:
        st.markdown(
            '<script>'
            '(function(){\'use strict\';'
            'function scrollToPlots(){\''
            "  var els=document.querySelectorAll('[class*=stTabs],[data-testid=stTabs]');"
            "  if(els.length){els[0].scrollIntoView({behavior:'smooth',block:'center'});return true;}"
            "  var secs=document.querySelectorAll('.me-section');"
            "  if(secs.length){secs[secs.length-1].scrollIntoView({behavior:'smooth',block:'start'});return true;}"
            '  return false;'
            '}'
            'var attempts=0;'
            'var t=setInterval(function(){'
            '  attempts++;'
            '  if(scrollToPlots()||attempts>20)clearInterval(t);'
            '},150);'
            '})();'
            '</script>',
            unsafe_allow_html=True
        )

    # Auto-play animation when a tab is selected
    st.markdown(
        '<script>'
        '(function(){'
        'function go(){'
        '  document.querySelectorAll(".js-plotly-plot").forEach(function(d){'
        '    if(d._me_played)return;'
        '    if(!d._transitionData||!d._transitionData._frames||!d._transitionData._frames.length)return;'
        '    d._me_played=true;'
        '    Plotly.animate(d,null,{frame:{duration:16,redraw:false},fromcurrent:true,transition:{duration:0}});'
        '  });'
        '}'
        'document.addEventListener("click",function(e){'
        '  if(e.target.closest("button[role=tab]")){d3.timer(go,150);}'
        '});'
        'setTimeout(go,900);'
        '})();'
        '</script>',
        unsafe_allow_html=True
    )

    # ── PDF Export ──────────────────────────────────────────────────────────
    st.markdown('<div class="me-section">Export</div>', unsafe_allow_html=True)

    pdf_bytes = build_pdf_report(
        df1, cvt_idx1,
        df2 if two_runs else None,
        cvt_idx2 if two_runs else None,
        pdf_summary
    )
    st.download_button(
        label="⬇  Download Full PDF Report",
        data=pdf_bytes,
        file_name="mechaeagles_report.pdf",
        mime="application/pdf",
        use_container_width=False,
    )

if __name__ == "__main__":
    main()