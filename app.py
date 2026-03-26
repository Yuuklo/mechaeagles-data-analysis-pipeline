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
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
    background-color: #0a0e17;
    color: #c8d8e8;
}

/* Scanline overlay */
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(220,30,60,0.012) 2px,
        rgba(220,30,60,0.012) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* Remove Streamlit's default top gap so header sits flush */
.main .block-container {
    padding: 0 2rem 3rem !important;
    max-width: 1400px;
    background-color: #0a0e17;
}
#root > div:first-child {
    margin-top: 0 !important;
}
header[data-testid="stHeader"] {
    background: transparent;
    height: 0;
}

/* ── Header ── */
.me-header {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 2rem 2rem 1.4rem;
    border-bottom: 1px solid #252530;
    margin-bottom: 1.8rem;
    background: linear-gradient(90deg, rgba(224,53,69,0.05) 0%, transparent 60%);
}
.me-logo-mark {
    width: 64px; height: 64px;
    background: #e03545;
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.me-logo-inner {
    width: 38px; height: 38px;
    background: #0a0e17;
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}
.me-brand { line-height: 1.15; }
.me-brand-name {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #e03545;
    text-transform: uppercase;
}
.me-brand-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #6a6a80;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

/* ── Section headers ── */
.me-section {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #e03545;
    border-left: 3px solid #e03545;
    padding-left: 10px;
    margin: 1.6rem 0 0.8rem;
}

/* ── Upload zone ── */
.me-upload-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
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
    background: #0f1a24;
    border: 1px solid #252530;
    border-left: 3px solid #e03545;
    padding: 14px 18px;
    border-radius: 4px;
}
.cvt-card-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #6a6a80;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.cvt-card-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #e03545;
}
.cvt-card-unit {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: #7a7a90;
    margin-left: 4px;
}
.cvt-card.run2 { border-left-color: #4d9de0; }
.cvt-card.run2 .cvt-card-value { color: #4d9de0; }

/* ── Anomaly table ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #252530 !important;
    border-radius: 4px;
    background: #0f1a24;
}

/* ── Plotly chart containers ── */
div[data-testid="stPlotlyChart"] {
    border: 1px solid #252530;
    border-radius: 4px;
    background: #0d1520;
    padding: 4px;
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] > button,
div[data-testid="stButton"] > button {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    color: #e03545 !important;
    border: 1px solid #e03545 !important;
    border-radius: 3px !important;
    padding: 0.5rem 1.8rem !important;
    transition: all 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stButton"] > button:hover {
    background: rgba(224,53,69,0.08) !important;
    box-shadow: 0 0 16px rgba(224,53,69,0.20) !important;
}

/* ── Radio ── */
div[data-testid="stRadio"] label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: #7a7a90;
}

/* Streamlit default element overrides */
h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; }
.stAlert { border-radius: 4px; }

/* ── Race car SVG ── */
.me-racecar { margin-left: auto; opacity: 0.82; flex-shrink: 0; }

/* ── CVT shimmer ── */
@keyframes shimmer {
  0%   { color: #e03545; text-shadow: none; }
  40%  { color: #ff6070; text-shadow: 0 0 10px rgba(255,80,100,0.7), 0 0 20px rgba(224,53,69,0.4); }
  60%  { color: #ff7080; text-shadow: 0 0 14px rgba(255,100,120,0.8), 0 0 28px rgba(224,53,69,0.5); }
  100% { color: #e03545; text-shadow: none; }
}
@keyframes shimmer-blue {
  0%   { color: #4d9de0; text-shadow: none; }
  40%  { color: #7ab8f0; text-shadow: 0 0 10px rgba(100,180,240,0.7), 0 0 20px rgba(77,157,224,0.4); }
  60%  { color: #90c8f8; text-shadow: 0 0 14px rgba(120,200,255,0.8), 0 0 28px rgba(77,157,224,0.5); }
  100% { color: #4d9de0; text-shadow: none; }
}
.cvt-card-value {
    cursor: default;
    transition: color 0.15s;
}
.cvt-card:hover .cvt-card-value {
    animation: shimmer 1.1s ease-in-out infinite;
}
.cvt-card.run2:hover .cvt-card-value {
    animation: shimmer-blue 1.1s ease-in-out infinite;
}
</style>

<div class="me-header">
  <div class="me-logo-mark"><div class="me-logo-inner"></div></div>
  <div class="me-brand">
    <div class="me-brand-name">MechaEagles</div>
    <div class="me-brand-sub">Post-Run Data Analysis Pipeline &nbsp;·&nbsp; v1.0</div>
  </div>
  <div class="me-racecar">
    <svg xmlns="http://www.w3.org/2000/svg" width="220" height="72" viewBox="0 0 220 72">
      <!-- Shadow -->
      <ellipse cx="110" cy="66" rx="80" ry="5" fill="rgba(0,0,0,0.35)"/>
      <!-- Main body -->
      <path d="M18 46 Q22 30 48 26 L72 22 Q90 14 110 13 Q130 14 148 22 L172 26 Q198 30 202 46 L210 52 Q214 58 208 60 L16 60 Q8 58 10 52 Z"
            fill="#141418" stroke="#e03545" stroke-width="1.2"/>
      <!-- Cockpit canopy -->
      <path d="M72 25 Q90 10 110 9 Q130 10 148 25 L142 26 Q124 16 110 15 Q96 16 78 26 Z"
            fill="#0e0e12" stroke="#4d9de0" stroke-width="0.8"/>
      <!-- Cockpit glass -->
      <path d="M80 24 Q96 13 110 12 Q124 13 140 24 L134 25 Q120 15 110 14 Q100 15 86 25 Z"
            fill="rgba(200,16,46,0.15)" stroke="rgba(200,16,46,0.4)" stroke-width="0.5"/>
      <!-- Front wing -->
      <path d="M10 52 L2 56 L6 60 L18 58 Z" fill="#e03545" stroke="#4d9de0" stroke-width="0.8"/>
      <path d="M10 52 L16 58 L18 56 L14 50 Z" fill="#4d9de0"/>
      <!-- Rear wing main plane -->
      <path d="M190 38 L216 36 L218 40 L190 43 Z" fill="#e03545" stroke="#4d9de0" stroke-width="0.8"/>
      <!-- Rear wing endplate -->
      <path d="M214 34 L218 34 L218 44 L214 44 Z" fill="#4d9de0"/>
      <!-- Sidepods -->
      <path d="M60 42 Q65 36 80 34 L82 46 Q70 46 62 48 Z" fill="#1c1c22" stroke="#e03545" stroke-width="0.6"/>
      <path d="M140 34 Q155 36 160 42 L158 48 Q150 46 138 46 Z" fill="#1c1c22" stroke="#e03545" stroke-width="0.6"/>
      <!-- Front left wheel -->
      <ellipse cx="38" cy="56" rx="11" ry="7" fill="#111" stroke="#252530" stroke-width="1.2"/>
      <ellipse cx="38" cy="56" rx="6" ry="4" fill="#141418" stroke="#e03545" stroke-width="0.8"/>
      <ellipse cx="38" cy="56" rx="2" ry="1.5" fill="#e03545"/>
      <!-- Front right wheel -->
      <ellipse cx="38" cy="56" rx="11" ry="7" fill="#111" stroke="#252530" stroke-width="1.2"/>
      <!-- Rear left wheel -->
      <ellipse cx="172" cy="56" rx="13" ry="8" fill="#111" stroke="#252530" stroke-width="1.2"/>
      <ellipse cx="172" cy="56" rx="7" ry="4.5" fill="#141418" stroke="#e03545" stroke-width="0.8"/>
      <ellipse cx="172" cy="56" rx="2.5" ry="1.8" fill="#e03545"/>
      <!-- Rear right wheel same -->
      <ellipse cx="172" cy="56" rx="13" ry="8" fill="#111" stroke="#252530" stroke-width="1.2"/>
      <!-- Halo -->
      <path d="M96 19 Q110 14 124 19 L122 21 Q110 16 98 21 Z" fill="none" stroke="#e03545" stroke-width="1.5" stroke-linecap="round"/>
      <!-- Nose cone -->
      <path d="M18 46 L10 50 L12 54 L22 52 Z" fill="#e03545" stroke="#4d9de0" stroke-width="0.8"/>
      <!-- Number plate -->
      <rect x="96" y="29" width="28" height="14" rx="2" fill="#e03545" opacity="0.15" stroke="#e03545" stroke-width="0.5"/>
      <!-- Speed lines -->
      <line x1="0" y1="38" x2="14" y2="38" stroke="#e03545" stroke-width="0.8" opacity="0.5"/>
      <line x1="0" y1="43" x2="10" y2="43" stroke="#4d9de0" stroke-width="0.6" opacity="0.4"/>
      <line x1="0" y1="48" x2="8"  y2="48" stroke="#e03545" stroke-width="0.5" opacity="0.3"/>
    </svg>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Plotly dark theme ───────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="#0d1520",
    plot_bgcolor="#0d1520",
    font=dict(family="Exo 2, sans-serif", color="#8aaabb", size=11),
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

RUN1_COLOR = "#e03545"
RUN2_COLOR = "#4d9de0"

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
    return fig

def make_gforce_plot(df1, df2=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df1['gx'], y=df1['gy'], mode='markers', name='Run 1',
        marker=dict(color=df1['speed'], colorscale=[[0, '#140a14'], [1, RUN1_COLOR]],
                    size=5, opacity=0.8,
                    colorbar=dict(title=dict(text='Speed R1', font=dict(size=10, color='#e03545')),
                                  thickness=12, len=0.42, y=0.78, yanchor='middle',
                                  x=1.02, tickfont=dict(size=9), outlinewidth=0,
                                  bgcolor='rgba(0,0,0,0)'))
    ))
    if df2 is not None:
        fig.add_trace(go.Scatter(
            x=df2['gx'], y=df2['gy'], mode='markers', name='Run 2',
            marker=dict(color=df2['speed'], colorscale=[[0, '#080818'], [1, RUN2_COLOR]],
                        size=5, opacity=0.8, symbol='diamond',
                        colorbar=dict(title=dict(text='Speed R2', font=dict(size=10, color='#4d9de0')),
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

def create_all_plots(df1, cvt_idx1, df2=None, cvt_idx2=None):
    return {
        "Speed":       make_line_plot(df1, df2, 'speed',   'Speed vs Time',       'Speed (mph)',    cvt_idx1, cvt_idx2),
        "RPM":         make_line_plot(df1, df2, 'rpm',     'RPM vs Time',         'RPM',            cvt_idx1, cvt_idx2),
        "Temperature": make_line_plot(df1, df2, 'temp',    'Temperature Trend',   'Temp (°F)',      cvt_idx1, cvt_idx2),
        "Voltage":     make_line_plot(df1, df2, 'voltage', 'Voltage',             'Voltage (V)',    cvt_idx1, cvt_idx2),
        "G-Force":     make_gforce_plot(df1, df2),
    }

# ── PDF export ──────────────────────────────────────────────────────────────
from reportlab.platypus import HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import datetime

def _pdf_styles():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    base = getSampleStyleSheet()

    dark   = rl_colors.HexColor('#0a0e17')
    teal   = rl_colors.HexColor('#e03545')
    light  = rl_colors.HexColor('#c8d8e8')
    muted  = rl_colors.HexColor('#4a7a8a')
    panel  = rl_colors.HexColor('#0f1a24')
    border = rl_colors.HexColor('#1a3a4a')

    title = ParagraphStyle('METitle',
        fontName='Helvetica-Bold', fontSize=26, leading=30,
        textColor=teal, spaceAfter=2, alignment=TA_LEFT,
        letterSpacing=3)
    subtitle = ParagraphStyle('MESubtitle',
        fontName='Helvetica', fontSize=8, leading=12,
        textColor=muted, spaceAfter=14, alignment=TA_LEFT,
        letterSpacing=2)
    section = ParagraphStyle('MESection',
        fontName='Helvetica-Bold', fontSize=9, leading=14,
        textColor=teal, spaceBefore=18, spaceAfter=6,
        alignment=TA_LEFT, letterSpacing=2,
        borderPadding=(0, 0, 4, 0))
    body = ParagraphStyle('MEBody',
        fontName='Helvetica', fontSize=9, leading=14,
        textColor=light, spaceAfter=4)
    meta_key = ParagraphStyle('MEMetaKey',
        fontName='Helvetica-Bold', fontSize=8,
        textColor=muted, leading=12)
    meta_val = ParagraphStyle('MEMetaVal',
        fontName='Helvetica-Bold', fontSize=11,
        textColor=teal, leading=14)

    return dict(title=title, subtitle=subtitle, section=section,
                body=body, meta_key=meta_key, meta_val=meta_val,
                dark=dark, teal=teal, light=light, muted=muted,
                panel=panel, border=border)


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
    ]))
    return t


def _anomaly_table(summary_df, s):
    col_labels = ['Run', 'Time (ms)', 'Type', 'Value', 'Threshold']
    col_keys   = ['run', 'time_s', 'type', 'value', 'threshold']
    col_widths = [0.6*inch, 0.9*inch, 1.0*inch, 0.8*inch, 2.7*inch]

    header = [Paragraph(c, ParagraphStyle('AH', fontName='Helvetica-Bold',
              fontSize=8, textColor=s['teal'], leading=12)) for c in col_labels]
    rows = [header]
    for _, row in summary_df.iterrows():
        style = ParagraphStyle('AC', fontName='Helvetica', fontSize=8,
                               textColor=s['light'], leading=12)
        rows.append([Paragraph(str(row.get(k, '')), style) for k in col_keys])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    stripe = rl_colors.HexColor('#111e2a')
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  s['border']),
        ('BACKGROUND',    (0,1), (-1,-1), s['panel']),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [s['panel'], stripe]),
        ('BOX',           (0,0), (-1,-1), 0.5,  s['border']),
        ('LINEBELOW',     (0,0), (-1,0),  0.8,  s['teal']),
        ('INNERGRID',     (0,1), (-1,-1), 0.25, s['border']),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t


class _DarkPageTemplate:
    """Draws the dark background + header bar on every page via onPage callback."""
    @staticmethod
    def on_page(canvas, doc):
        w, h = letter
        canvas.saveState()
        # dark background
        canvas.setFillColor(rl_colors.HexColor('#0a0e17'))
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        # top accent bar
        canvas.setFillColor(rl_colors.HexColor('#00ffb4'))
        canvas.rect(0, h-3, w, 3, fill=1, stroke=0)
        # footer
        canvas.setFillColor(rl_colors.HexColor('#1a3a4a'))
        canvas.rect(0, 0, w, 24, fill=1, stroke=0)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(rl_colors.HexColor('#4a7a8a'))
        canvas.drawString(0.75*inch, 8, 'MECHAEAGLES — POST-RUN DATA ANALYSIS PIPELINE')
        canvas.drawRightString(w - 0.75*inch, 8, f'Page {doc.page}')
        canvas.restoreState()


@st.cache_data(show_spinner="Generating PDF report...")
def build_pdf_report(df1, cvt_idx1, df2, cvt_idx2, summary_df):
    plots = create_all_plots(df1, cvt_idx1, df2, cvt_idx2)
    s = _pdf_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.6*inch, bottomMargin=0.55*inch,
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
    elements.append(Paragraph('TELEMETRY PLOTS', s['section']))
    elements.append(Spacer(1, 4))

    for plot_title, fig in plots.items():
        img_bytes = fig.to_image(format='png', width=900, height=480, scale=2)
        img = Image(io.BytesIO(img_bytes), width=7.0*inch, height=3.73*inch)
        label = Paragraph(plot_title.upper(), ParagraphStyle(
            'PlotLabel', fontName='Helvetica-Bold', fontSize=8,
            textColor=s['teal'], leading=12, letterSpacing=1.5, spaceAfter=3))
        elements.append(KeepTogether([label, img, Spacer(1, 14)]))

    doc.build(elements, onFirstPage=_DarkPageTemplate.on_page,
              onLaterPages=_DarkPageTemplate.on_page)
    buffer.seek(0)
    return buffer.getvalue()

# ── Main app ────────────────────────────────────────────────────────────────
def main():
    # ── Upload section ──────────────────────────────────────────────────────
    st.markdown('<div class="me-section">Data Input</div>', unsafe_allow_html=True)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown('<div class="me-upload-label">Run 1 — required</div>', unsafe_allow_html=True)
        f1 = st.file_uploader("Run 1", type=["csv"], key="file1", label_visibility="collapsed")
    with col_u2:
        st.markdown('<div class="me-upload-label">Run 2 — optional (enables comparison mode)</div>', unsafe_allow_html=True)
        f2 = st.file_uploader("Run 2", type=["csv"], key="file2", label_visibility="collapsed")

    # Load data
    df1, df2 = None, None
    if f1:
        df1 = pd.read_csv(f1)
    else:
        try:
            df1 = pd.read_csv('./data/run_001_dummy.csv')
        except FileNotFoundError:
            st.error("No CSV uploaded and no dummy file found at ./data/run_001_dummy.csv")
            return

    if f2:
        df2 = pd.read_csv(f2)

    df1 = enforce_dtypes(normalize_columns(df1))
    if df2 is not None:
        df2 = enforce_dtypes(normalize_columns(df2))

    two_runs = df2 is not None

    # Session state reset on new data
    current_key = f"{len(df1)}_{df1['time_s'].sum()}" + (f"_{len(df2)}_{df2['time_s'].sum()}" if two_runs else "")
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
        cvt_html += f'''<div class="cvt-card">
            <div class="cvt-card-label">Run 1 — Engagement Time</div>
            <div class="cvt-card-value">{t1:.0f}<span class="cvt-card-unit">ms</span></div>
        </div>
        <div class="cvt-card">
            <div class="cvt-card-label">Run 1 — Engagement RPM</div>
            <div class="cvt-card-value">{r1:.0f}<span class="cvt-card-unit">rpm</span></div>
        </div>'''
    if two_runs and cvt_idx2 is not None and cvt_idx2 in df2.index:
        t2, r2 = df2.loc[cvt_idx2, 'time_s'], df2.loc[cvt_idx2, 'rpm']
        cvt_html += f'''<div class="cvt-card run2">
            <div class="cvt-card-label">Run 2 — Engagement Time</div>
            <div class="cvt-card-value">{t2:.0f}<span class="cvt-card-unit">ms</span></div>
        </div>
        <div class="cvt-card run2">
            <div class="cvt-card-label">Run 2 — Engagement RPM</div>
            <div class="cvt-card-value">{r2:.0f}<span class="cvt-card-unit">rpm</span></div>
        </div>'''
    cvt_html += '</div>'
    st.markdown(cvt_html, unsafe_allow_html=True)

    # ── Anomalies + Plots side by side ──────────────────────────────────────
    st.markdown('<div class="me-section">Anomalies & Plots</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 2], gap="medium")

    with left_col:
        summary1 = detect_anomalies(df1)
        summary1.insert(0, 'run', 'Run 1')
        if two_runs:
            summary2 = detect_anomalies(df2)
            summary2.insert(0, 'run', 'Run 2')
            pdf_summary = pd.concat([summary1, summary2], ignore_index=True)
        else:
            pdf_summary = summary1.copy()

        st.markdown("**Flagged Events**", help="Grouped anomalies detected across all channels")
        st.dataframe(
            pdf_summary,
            use_container_width=True,
            height=420,
            hide_index=True,
        )

    with right_col:
        plots = create_all_plots(df1, cvt_idx1, df2, cvt_idx2)
        tabs = st.tabs(["Speed", "RPM", "Temperature", "Voltage", "G-Force"])
        for tab, key in zip(tabs, ["Speed", "RPM", "Temperature", "Voltage", "G-Force"]):
            with tab:
                st.plotly_chart(plots[key], use_container_width=True)

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