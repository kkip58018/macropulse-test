import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from analyzer import init_analyzer as get_analyzer
from config import *
from utils import load_seasonality_data

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


# Title row with dropdown on far right
title_col, dropdown_col = st.columns([3, 1])
with title_col:
    st.header("📈 Annual Seasonality")
with dropdown_col:
    seasonal_pairs = FOREX_PAIRS + [
        "XAU/USD",
        "XAG/USD",
        "BTC/USD",
        "ETH/USD",
        "USOIL/USD",
        "SPX500/USD",
        "NAS100/USD",
    ]
    selected_pair = st.selectbox(
        "", seasonal_pairs, index=0, label_visibility="collapsed"
    )
with st.spinner("Fetching historical data..."):
    df = load_seasonality_data(selected_pair)
if df is None or df.empty:
    st.error(f"No data found for {selected_pair}.")
    st.stop()
df["Year"] = df.index.year
df["Year_Start_Close"] = df.groupby("Year")["Close"].transform("first")
df["Cum_Return_pct"] = (
    (df["Close"] - df["Year_Start_Close"]) / df["Year_Start_Close"]
) * 100
df["Week"] = ((df.index.dayofyear - 1) // 7) + 1
current_year = datetime.now().year
hist_df = df[df["Year"] < current_year]
weekly_avg = hist_df.groupby("Week")["Cum_Return_pct"].mean().reset_index()
curr_df = df[df["Year"] == current_year]
weekly_curr = (
    curr_df.groupby("Week")["Close"].last().reset_index()
)  # price for left axis
# Map week numbers to approximate month boundaries
month_weeks = [1, 5, 9, 14, 18, 22, 27, 31, 36, 40, 44, 49]
month_labels = month_names
fig = go.Figure()
# Left y-axis: Price (current year close) – renamed to YTD Performance, color red
fig.add_trace(
    go.Scatter(
        x=weekly_curr["Week"],
        y=weekly_curr["Close"],
        name="YTD Performance",
        line=dict(color="#ff4b4b", width=2.5),  # red line
        mode="lines+markers",
        marker=dict(size=5, color="#ff4b4b"),
        yaxis="y1",
    )
)
# Right y-axis: 10‑year average cumulative return (%)
fig.add_trace(
    go.Scatter(
        x=weekly_avg["Week"],
        y=weekly_avg["Cum_Return_pct"],
        name="10‑Year Avg Return",
        line=dict(color="#aaaaaa", width=2, dash="dash"),
        mode="lines",
        yaxis="y2",
    )
)
fig.update_layout(
    title=f"Annual Seasonality – {selected_pair}",
    xaxis=dict(
        title="",
        tickvals=month_weeks,
        ticktext=month_labels,
        tickangle=0,
        showgrid=False,
    ),
    yaxis=dict(
        title="",  # removed axis title
        tickfont=dict(color="white"),
        side="left",
        showgrid=False,
    ),
    yaxis2=dict(
        title="",  # removed axis title
        tickfont=dict(color="#aaaaaa"),
        overlaying="y",
        side="right",
        showgrid=False,
        ticksuffix="%",
    ),
    template="plotly_dark",
    hovermode="x unified",
    height=650,
    margin=dict(l=40, r=60, t=60, b=40),
    plot_bgcolor="#0b0f15",
    paper_bgcolor="#0b0f15",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(
    fig, use_container_width=True, config={"displayModeBar": False}
    )
