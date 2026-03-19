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
    """Collapse consecutive flagged rows into single peak events"""
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


df = pd.read_csv('./data/run_001_dummy.csv')
df = normalize_columns(df)
df = enforce_dtypes(df)
summary = detect_anomalies(df)
print(summary)



































