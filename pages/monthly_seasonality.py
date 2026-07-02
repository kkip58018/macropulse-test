import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from analyzer import init_analyzer as get_analyzer
from config import *
from utils import load_seasonality_data

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()



title_col, dropdown_col = st.columns([3, 1])
with title_col:
    st.header("📅 Monthly Seasonality")
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
# Resample to monthly
monthly = df.resample("ME").agg({"Open": "first", "Close": "last"})
monthly["Return_pct"] = (
    (monthly["Close"] - monthly["Open"]) / monthly["Open"]
) * 100
monthly["Month"] = monthly.index.month
monthly["Year"] = monthly.index.year
# 10‑year average per month
avg_returns = (
    monthly.groupby("Month")["Return_pct"]
    .mean()
    .reindex(range(1, 13), fill_value=0.0)
)
# Current year to date
current_year = datetime.now().year
this_year = monthly[monthly["Year"] == current_year]
this_year_data = this_year.set_index("Month")["Return_pct"].reindex(
    range(1, 13), fill_value=None
)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=month_names,
        y=avg_returns.values,
        name="10‑Year Average",
        marker_color="#1d70b8",
        text=[f"{v:+.2f}%" for v in avg_returns.values],
        textposition="outside",
        textfont=dict(color="white"),
    )
)
fig.add_trace(
    go.Scatter(
        x=month_names,
        y=[
            this_year_data[m] if pd.notna(this_year_data[m]) else None
            for m in range(1, 13)
        ],
        name=f"{current_year} (YTD)",
        mode="lines+markers",
        line=dict(
            color="white", width=2, dash="dot", shape="spline"
        ),  
        marker=dict(size=8, color="white"),
        text=[f"{v:+.2f}%" if v is not None else "" for v in this_year_data.values],
        textposition="top center",
    )
)
fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig.update_layout(
    title=f"Monthly Returns – {selected_pair}",
    xaxis_title="",
    yaxis_title="",  
    yaxis=dict(showgrid=False),
    template="plotly_dark",
    hovermode="x unified",
    height=650,
    margin=dict(l=40, r=40, t=60, b=40),
    plot_bgcolor="#0b0f15",
    paper_bgcolor="#0b0f15",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(
    fig, use_container_width=True, config={"displayModeBar": False}
    )
