import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analyzer import init_analyzer 
from config import *
from sidebar import render as render_sidebar


# ---------- Authentication guard ----------
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.stop()

# ---------- Render the custom sidebar ----------
render_sidebar()

# ---------- Get the analyzer ----------
analyzer = init_analyzer()  # cached

# ---------- Page content (copy from original) ----------

st.markdown(
    """<style>div[data-testid="stSelectbox"] { width: 50% !important; min-width: 120px; }</style>""",
    unsafe_allow_html=True,
)
is_admin = st.session_state.get("is_admin", False)
if is_admin:
    col1, col2, col3 = st.columns([2, 1, 2])
else:
    col1, col3 = st.columns([2, 2])
    col2 = None
with col1:
    st.title("📊 Put/Call Ratio")
if is_admin and col2 is not None:
    with col2:
        fetch_data = st.button("Refresh Data", use_container_width=True)
else:
    fetch_data = False
with col3:
    selected_asset = st.selectbox(
        "Asset",
        options=list(asset_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
    asset_cfg = asset_options[selected_asset]
    ticker_input = asset_cfg["ticker"]
# --- Fetch and store from Barchart (admin only) ---
if fetch_data and is_admin and ticker_input:
    with st.spinner(
        f"Fetching put/call ratio for {selected_asset} from Barchart..."
    ):
        ratio = analyzer.fetch_and_store_put_call_ratio(
            selected_asset, ticker_input
        )
        if ratio is not None:
            st.success(f"Fetched ratio: {ratio:.2f} → stored in database.")
            # --- Update retail score directly (bypass database) ---
            asset_map_rev = {
                "IBIT": "BTC",
                "GLD": "XAU",
                "SLV": "XAG",
                "QQQ": "NAS100",
                "SPY": "SPX500",
                "UUP": "USD",
                "USO": "USOIL",
            }
            if ticker_input in asset_map_rev:
                asset = asset_map_rev[ticker_input]
                high_put = asset_cfg["high_put"]
                high_call = asset_cfg["high_call"]
                if ratio >= high_put:
                    score = 2
                elif ratio <= high_call:
                    score = -2
                else:
                    score = 0
                # Update all relevant pairs
                if asset == "USD":
                    analyzer.usd_pc_score = score
                else:
                    target_pair = f"{asset}/USD"
                    analyzer.retail_scores[target_pair] = score
                    if target_pair in analyzer.retail_long_pct:
                        del analyzer.retail_long_pct[target_pair]
                st.info(
                    f"✅ Retail bias for {selected_asset} set to {score:+d} (Bullish if +2, Bearish if -2)."
                )
            else:
                st.warning(
                    f"Ticker {ticker_input} not recognised for direct retail update."
                )
        else:
            st.error("Failed to retrieve put/call ratio from Barchart.")
# --- CHART (reads from Turso) ---
if analyzer.turso_session:
    sql = "SELECT date, ratio FROM put_call_history WHERE ticker = ? ORDER BY date ASC"
    resp = analyzer.turso_session.post(
        analyzer.turso_http_endpoint,
        json={
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": [{"type": "text", "value": ticker_input}],
                    },
                }
            ]
        },
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
    clean = []
    for row in rows:
        if isinstance(row, dict):
            date_str = extract(row.get("date"))
            ratio_val = float(extract(row.get("ratio", 0)))
        else:
            date_str = extract(row[0])
            ratio_val = float(extract(row[1]))
        clean.append((date_str, ratio_val))
    if clean:
        df = pd.DataFrame(clean, columns=["date", "ratio"])
        df["date"] = pd.to_datetime(df["date"].str.strip(), format="%Y-%m-%d")
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["ratio"],
                mode="lines",
                line=dict(color="white", width=2.5, shape="hv"),
                name="Put-Call Ratio",
            )
        )
        # Dummy trace for secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=[df["date"].iloc[0]],
                y=[df["ratio"].iloc[0]],
                mode="markers",
                marker=dict(color="rgba(0,0,0,0)"),
                yaxis="y2",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        high_put = asset_cfg["high_put"]
        high_call = asset_cfg["high_call"]
        fig.add_hline(
            y=high_put, line_dash="dash", line_color="#ef4444", line_width=2
        )
        fig.add_hline(
            y=high_call, line_dash="dash", line_color="#3b82f6", line_width=2
        )
        first_date = df["date"].min()
        fig.add_annotation(
            x=first_date,
            y=high_put,
            text="High Put Volume",
            showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="#ef4444",
            borderpad=4,
            opacity=0.8,
            yshift=12,
            xshift=-20,
        )
        fig.add_annotation(
            x=first_date,
            y=high_call,
            text="High Call Volume",
            showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="#3b82f6",
            borderpad=4,
            opacity=0.8,
            yshift=12,
            xshift=-20,
        )
        fig.add_annotation(
            x=1,
            y=1,
            xref="paper",
            yref="paper",
            text="BEARISH SENTIMENT",
            showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="#ef4444",
            borderpad=4,
            opacity=0.6,
            xanchor="right",
            yanchor="bottom",
            yshift=10,
        )
        fig.add_annotation(
            x=1,
            y=0,
            xref="paper",
            yref="paper",
            text="BULLISH SENTIMENT",
            showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="#3b82f6",
            borderpad=4,
            opacity=0.6,
            xanchor="right",
            yanchor="bottom",
            yshift=20,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.3)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0c0c0"),
            xaxis=dict(
                showgrid=False,
                tickformat="%d %b",
                zeroline=False,
                showline=True,
                linecolor="#c0c0c0",
                linewidth=1.5,
                tickcolor="#c0c0c0",
                ticklen=6,
                ticks="outside",
                tickfont=dict(color="#c0c0c0", size=10),
            ),
            yaxis=dict(
                title="",
                range=[asset_cfg["y_min"], asset_cfg["y_max"]],
                showgrid=False,
                zeroline=False,
                side="left",
                showline=True,
                linecolor="#c0c0c0",
                linewidth=1.5,
                tickcolor="#c0c0c0",
                ticklen=6,
                ticks="outside",
                tickfont=dict(color="#c0c0c0", size=10),
            ),
            yaxis2=dict(
                title="",
                range=[asset_cfg["y_min"], asset_cfg["y_max"]],
                showgrid=False,
                zeroline=False,
                side="right",
                overlaying="y",
                showline=True,
                linecolor="#c0c0c0",
                linewidth=1.5,
                tickcolor="#c0c0c0",
                ticklen=6,
                ticks="outside",
                tickfont=dict(color="#c0c0c0", size=10),
            ),
            margin=dict(l=60, r=60, t=30, b=50),
            showlegend=False,
            height=600,
        )
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.info(
            f"No historical data for {selected_asset}. Click 'Refresh Data' to fetch from Barchart."
        )
else:
    st.warning("Cannot connect to Turso history.")
