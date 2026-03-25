import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

COLUMN_ALIASES = {
    "time_s": ["timestamp_ms", "time", "timestamp", "t", "seconds", "sec", "time_s"],
    "speed": ["speed", "vehicle_speed", "wheel_speed", "mph", "kph", "speed_mph", "speed_kph"],
    "rpm": ["rpm", "engine_rpm", "motor_rpm"],
    "temp": ["temp", "temperature", "cvt_temp", "engine_temp", "temp_c", "temp_f"],
    "gx": ["accel_x_g", "gx", "g_x", "accel_x", "ax", "gforce_x"],
    "gy": ["accel_y_g", "gy", "g_y", "accel_y", "ay", "gforce_y"],
    "voltage": ["voltage_v", "voltage", "vbat", "battery_voltage", "vbatt", "batt_v"],
}

DTYPE_MAP = {
        "time_s":   float,
        "speed":    float,
        "rpm":      float,
        "temp":     float,
        "gx":       float,
        "gy":       float,
        "voltage":  float,
    }


def normalize_columns(df):
    """
    Checks each column name and changes it to a set alias
    """
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
        raise ValueError(f"Could not find columns for following: {missing}")

    return df.rename(columns = rename_map)


def enforce_dtypes(df):
    """
    Sets all column dtypes to float64
    """
    for col, dtype in DTYPE_MAP.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].astype(dtype)
    return df


def group_events(df_flagged, values, event_type, threshold_str, gap=200):
    """
    Collapse consecutive flagged rows into single peak events
    """
    if df_flagged.empty:
        return []

    events = []
    group_indices = []

    for idx in df_flagged.index:
        if not group_indices or (df_flagged.loc[idx, 'time_s'] - df_flagged.loc[group_indices[-1], 'time_s']) <= gap:
            group_indices.append(idx)
        else:
            peak_idx = values.loc[group_indices].idxmax()
            events.append({
                "time_s":    df_flagged.loc[peak_idx, 'time_s'],
                "type":      event_type,
                "value":     round(values.loc[peak_idx], 3),
                "threshold": threshold_str,
            })
            group_indices = [idx]

    if group_indices:
        peak_idx = values.loc[group_indices].idxmax()
        events.append({
            "time_s":    df_flagged.loc[peak_idx, 'time_s'],
            "type":      event_type,
            "value":     round(values.loc[peak_idx], 3),
            "threshold": threshold_str,
        })

    return events


def detect_anomalies(df):
    """
    Detects unusual spikes/drops in the CSV file
    """
    RPM_DROP_THRESHOLD   = 1000
    TEMP_SPIKE_THRESHOLD = 15
    MAX_G_THRESHOLD      = 0.75  
    RPM_WINDOW           = 10

    anomalies = []

    # RPM drop?
    rpm_rolling_mean = df['rpm'].rolling(window=RPM_WINDOW, center=True).mean()
    rpm_drop_mask = (rpm_rolling_mean - df['rpm']) > RPM_DROP_THRESHOLD
    anomalies += group_events(df[rpm_drop_mask], rpm_rolling_mean - df['rpm'], "rpm_drop", f">{RPM_DROP_THRESHOLD} below rolling mean")
 
    # Temp spike?
    temp_delta = df['temp'].diff().abs()
    temp_spike_mask = temp_delta > TEMP_SPIKE_THRESHOLD
    anomalies += group_events(df[temp_spike_mask], temp_delta, "temp_spike", f">{TEMP_SPIKE_THRESHOLD}° change per step")
 
    # Max-G event?
    g_magnitude = np.sqrt(df['gx']**2 + df['gy']**2)
    max_g_mask = g_magnitude > MAX_G_THRESHOLD
    anomalies += group_events(df[max_g_mask], g_magnitude, "max_g", f">{MAX_G_THRESHOLD}G combined magnitude")
 
    # Summary table
    if anomalies:
        summary = pd.DataFrame(anomalies).sort_values("time_s").reset_index(drop=True)
    else:
        summary = pd.DataFrame(columns=["time_s", "type", "value", "threshold"])

    return summary


def get_cvt_engagement(df):
    """
    Find RPM plateau where speed begins rising -> return timestamp index
    """
    mask = df['speed'] > 0.5
    if not mask.any():
        return None
    return mask.idxmax()

def create_plots(df1, cvt_idx1, df2=None, cvt_idx2=None):
    plots = {}
    
    def plot_line(y_col, title):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df1['time_s'], y=df1[y_col], mode='lines', name='Run 1', line=dict(color='blue')))
        if cvt_idx1 is not None and cvt_idx1 in df1.index:
            fig.add_vline(x=df1.loc[cvt_idx1, 'time_s'], line_dash="dash", line_color="green", annotation_text="CVT 1")
        if df2 is not None:
            fig.add_trace(go.Scatter(x=df2['time_s'], y=df2[y_col], mode='lines', name='Run 2', line=dict(color='red', dash='dot')))
            if cvt_idx2 is not None and cvt_idx2 in df2.index:
                fig.add_vline(x=df2.loc[cvt_idx2, 'time_s'], line_dash="dash", line_color="orange", annotation_text="CVT 2")
        fig.update_layout(title=title, xaxis_title='Time (s)', yaxis_title=y_col.capitalize())
        return fig
    
    plots["Speed"] = plot_line('speed', 'Speed vs Time')
    plots["RPM"] = plot_line('rpm', 'RPM vs Time')
    plots["Temperature"] = plot_line('temp', 'Temperature Trend')
    plots["Voltage"] = plot_line('voltage', 'Voltage Chart')

    # G-Force XY scatter
    fig_g = go.Figure()
    fig_g.add_trace(go.Scatter(x=df1['gx'], y=df1['gy'], mode='markers', 
                               marker=dict(color=df1['speed'], colorscale='Viridis', showscale=True, colorbar=dict(title="Speed 1")),
                               name='Run 1'))
    if df2 is not None:
        fig_g.add_trace(go.Scatter(x=df2['gx'], y=df2['gy'], mode='markers', 
                                   marker=dict(color=df2['speed'], colorscale='Plasma', showscale=True, colorbar=dict(title="Speed 2", x=1.15)),
                                   name='Run 2'))
    fig_g.add_vline(x=0, line_color='gray', line_dash='dash')
    fig_g.add_hline(y=0, line_color='gray', line_dash='dash')
    fig_g.update_layout(xaxis_range=[-2, 2], yaxis_range=[-2, 2], xaxis_title="Gx", yaxis_title="Gy", title='G-Force XY Scatter')
    plots["G-Force"] = fig_g

    return plots

import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

@st.cache_data(show_spinner="Generating PDF...")
def build_pdf_report(df1, cvt_idx1, df2, cvt_idx2, summary_df):
    plots = create_plots(df1, cvt_idx1, df2, cvt_idx2)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Post-Run Data Analysis Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Anomalies
    elements.append(Paragraph("Anomaly Summary", styles['Heading2']))
    if not summary_df.empty:
        # Convert df to string to ensure table format works
        data = [summary_df.columns.to_list()] + summary_df.astype(str).values.tolist()
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No anomalies detected.", styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # Export plots to images and add to PDF
    for title, fig in plots.items():
        elements.append(Paragraph(title, styles['Heading2']))
        img_bytes = fig.to_image(format="png", width=600, height=400)
        img_io = io.BytesIO(img_bytes)
        img = Image(img_io, width=400, height=266)
        elements.append(img)
        elements.append(Spacer(1, 12))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def main():
    st.set_page_config(page_title="Data Analysis Pipeline", layout="wide")
    st.title("Post-Run Data Analysis Pipeline")
    
    mode = st.radio("Mode", ["Single-CSV", "Two-CSV Comparison"])
    
    df1, df2 = None, None
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Upload Run 1 CSV")
        uploaded_file1 = st.file_uploader("Run 1", type=["csv"], key="file1")
        if uploaded_file1 is not None:
            df1 = pd.read_csv(uploaded_file1)
        else:
            try:
                df1 = pd.read_csv('./data/run_001_dummy.csv')
            except FileNotFoundError:
                st.error("No dummy file found! Please upload a file.")
                return
                
    if mode == "Two-CSV Comparison":
        with col2:
            st.write("Upload Run 2 CSV")
            uploaded_file2 = st.file_uploader("Run 2", type=["csv"], key="file2")
            if uploaded_file2 is not None:
                df2 = pd.read_csv(uploaded_file2)
    
    if df1 is None:
        return
        
    df1 = enforce_dtypes(normalize_columns(df1))
    if df2 is not None:
        df2 = enforce_dtypes(normalize_columns(df2))
        
    # App State logic to reset PDF generation flag when new data comes in
    current_key = f"{len(df1)}_{df1['time_s'].sum()}"
    if df2 is not None:
        current_key += f"_{len(df2)}_{df2['time_s'].sum()}"
        
    if st.session_state.get("data_key") != current_key:
        st.session_state["data_key"] = current_key
        st.session_state["pdf_requested"] = False

    st.header("Data Anomalies")
    if df2 is None:
        summary1 = detect_anomalies(df1)
        summary1.insert(0, 'Run', 'Run 1')
        st.dataframe(summary1)
        pdf_summary = summary1.copy()
    else:
        st.subheader("Run 1 Anomalies")
        summary1 = detect_anomalies(df1)
        summary1.insert(0, 'Run', 'Run 1')
        st.dataframe(summary1)
        st.subheader("Run 2 Anomalies")
        summary2 = detect_anomalies(df2)
        summary2.insert(0, 'Run', 'Run 2')
        st.dataframe(summary2)
        pdf_summary = pd.concat([summary1, summary2], ignore_index=True)

    st.header("CVT Engagement")
    cvt_idx1 = get_cvt_engagement(df1)
    if cvt_idx1 is not None and cvt_idx1 in df1.index:
        v1_time, v1_rpm = df1.loc[cvt_idx1, 'time_s'], df1.loc[cvt_idx1, 'rpm']
        st.write(f"**Run 1 CVT Engagement:** `{v1_time}` ms | **RPM:** `{v1_rpm}`")
    else:
        st.write("**Run 1 CVT Engagement:** None")
    
    cvt_idx2 = None
    if df2 is not None:
        cvt_idx2 = get_cvt_engagement(df2)
        if cvt_idx2 is not None and cvt_idx2 in df2.index:
            v2_time, v2_rpm = df2.loc[cvt_idx2, 'time_s'], df2.loc[cvt_idx2, 'rpm']
            st.write(f"**Run 2 CVT Engagement:** `{v2_time}` ms | **RPM:** `{v2_rpm}`")
        else:
            st.write("**Run 2 CVT Engagement:** None")
            
    st.header("Plots")
    plots = create_plots(df1, cvt_idx1, df2, cvt_idx2)
    
    pc1, pc2 = st.columns(2)
    with pc1:
        st.plotly_chart(plots["Speed"], use_container_width=True)
        st.plotly_chart(plots["Temperature"], use_container_width=True)
        st.plotly_chart(plots["G-Force"], use_container_width=True)
    with pc2:
        st.plotly_chart(plots["RPM"], use_container_width=True)
        st.plotly_chart(plots["Voltage"], use_container_width=True)
        
    st.header("Export Report")
    
    if st.button("Prepare PDF Report"):
        st.session_state["pdf_requested"] = True
        
    if st.session_state.get("pdf_requested", False):
        pdf_bytes = build_pdf_report(df1, cvt_idx1, df2, cvt_idx2, pdf_summary)
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="report.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()



































