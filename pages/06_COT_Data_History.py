import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import *
from sidebar import render as render_sidebar
from analyzer import init_analyzer

# ---------- Authentication guard ----------
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.stop()

# ---------- Render the custom sidebar ----------
render_sidebar()

# ---------- Get the analyzer ----------
analyzer = init_analyzer()  # cached

# ---------- Page content (copy from original) ----------

title_col, dropdown_col = st.columns([3, 1])

with title_col:
    st.header("📊 COT Data History")
if not getattr(analyzer, "turso_session", None):
    st.warning("Turso database connection is required to view historical COT data.")
    st.stop()
available_assets = sorted(list(analyzer.cot_current.keys()))
if not available_assets:
    st.info("No COT data available. Please fetch data first.")
    st.stop()
with dropdown_col:
    # Push the dropdown down slightly so it aligns with the header text
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    selected_asset = st.selectbox(
        "Select Asset", 
        options=available_assets, 
        index=available_assets.index("USD") if "USD" in available_assets else 0,
        label_visibility="collapsed" # Hides the label to save space
    )
# Cache results for 2 days to prevent database rate limits
@st.cache_data(ttl=172800, show_spinner=False)
def get_cached_cot_history(url, token, asset):
    temp_session = requests.Session()
    temp_session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    
    sql = "SELECT date, long_pos, short_pos FROM cot_data WHERE asset = ? ORDER BY date ASC"
    args = [{"type": "text", "value": asset}]
    
    resp = temp_session.post(
        url,
        json={"requests": [{"type": "execute", "stmt": {"sql": sql, "args": args}}]}
    )
    resp.raise_for_status()
    data = resp.json()
    
    rows = []
    if data.get("results"):
        for result in data["results"]:
            r = result.get("response", {}).get("result", {}).get("rows")
            if r:
                rows = r
                break
                
    def extract(cell):
        return cell.get("value", "") if isinstance(cell, dict) else cell
        
    clean_data = []
    for row in rows:
        if isinstance(row, dict):
            d = extract(row.get("date"))
            lp = float(extract(row.get("long_pos")) or 0)
            sp = float(extract(row.get("short_pos")) or 0)
            clean_data.append({"date": d, "long_pos": lp, "short_pos": sp})
        elif isinstance(row, list) and len(row) >= 3:
            d = extract(row[0])
            lp = float(extract(row[1]) or 0)
            sp = float(extract(row[2]) or 0)
            clean_data.append({"date": d, "long_pos": lp, "short_pos": sp})
            
    return pd.DataFrame(clean_data)
with st.spinner(f"Loading history for {selected_asset}..."):
    df = get_cached_cot_history(
        analyzer.turso_http_endpoint, 
        analyzer.turso_token, 
        selected_asset
    )
if df.empty:
    st.warning(f"No historical data found for {selected_asset}.")
else:
    # Data preparation and indexing
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Total calculated for percentage mapping
    df["total_contracts"] = df["long_pos"] + df["short_pos"]
    
    # Calculate the line chart positioning percentage
    df["long_pct"] = df.apply(
        lambda x: (x["long_pos"] / x["total_contracts"] * 100) if x["total_contracts"] > 0 else 0, 
        axis=1
    )
    
    # Explicit user boundary ranges mapping for the right y-axis
    MAX_Y_RIGHT = {
        "AUD": 225000,
        "CAD": 250000,
        "BTC": 70000,
        "CHF": 80000,
        "EUR": 500000,
        "GBP": 225000,
        "gold": 450000,
        "JPY": 400000,
        "NAS100": 200000,
        "NZD": 100000,
        "silver": 120000,
        "SPX": 800000,
        "USD": 60000,
        "USOIL": 700000,
    }
    
    # Create canvas configuration allocating independent dual axes
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 1a. Long Contracts Bar (Primary Axis drawn at bottom layer, forced to right side)
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["long_pos"],
            name="Long Contracts",
            marker_color="#1e3a5f" 
        ),
        secondary_y=False,
    )
    # 1b. Short Contracts Bar (Primary Axis drawn at bottom layer, forced to right side)
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["short_pos"],
            name="Short Contracts",
            marker_color="#5f1e1e" 
        ),
        secondary_y=False,
    )
    
    # 2. Long % Line Graph (Secondary Axis always draws on top layer, forced to left side)
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["long_pct"],
            name="Long %",
            mode="lines",
            line=dict(color="#FF8C00", width=3) 
        ),
        secondary_y=True,
    )
    # 3. 50% Horizontal Line (Secondary Axis drawn on top layer, forced to left side)
    fig.add_trace(
        go.Scatter(
            x=[df["date"].min(), df["date"].max()],
            y=[50, 50],
            mode="lines",
            name="50% Mark",
            line=dict(color="grey", width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip" # Prevents tooltip interference on this line
        ),
        secondary_y=True,
    )
    
    right_max = MAX_Y_RIGHT.get(selected_asset)
    
    # Global Figure Settings (Fixed 700px height, stacked bars, removed x-axis label)
    fig.update_layout(
        barmode='stack',
        height=700,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=60, b=50),
        xaxis=dict(title_text="") 
    )
    
    # Enforce Left Y-Axis Constraints for the Percentages (Mapped to secondary_y layer to force z-index front)
    fig.update_yaxes(
        title_text="", 
        range=[0, 100], 
        side="left",
        secondary_y=True, 
        ticksuffix="%",
        showgrid=False # Avoid overlapping gridlines
    )
    
    # Enforce Right Y-Axis Constraints for Total Contracts (Mapped to primary_y layer)
    if right_max:
        fig.update_yaxes(
            title_text="", 
            range=[0, right_max], 
            side="right",
            secondary_y=False
        )
    else:
        fig.update_yaxes(
            title_text="", 
            side="right",
            secondary_y=False, 
            rangemode="tozero"
        )
        
    st.plotly_chart(
        fig, 
        use_container_width=True, 
        config={"displayModeBar": False}
    )
