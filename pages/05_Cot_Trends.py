import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analyzer import init_analyzer as get_analyzer
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


title_col, dropdown_col = st.columns([3, 1])

with title_col:
    st.header("📈 COT Trends")
    st.markdown("Track the historical net positioning  of institutional traders over time.")
if not getattr(analyzer, "turso_session", None):
    st.warning("Turso database connection is required to view historical COT trends.")
    st.stop()
available_assets = sorted(list(analyzer.cot_current.keys()))
if not available_assets:
    st.info("No COT data available. Please fetch data first.")
    st.stop()
default_assets = ["USD", "EUR"]

with dropdown_col:
    # Push the dropdown down slightly so it aligns nicely with the header text
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    selected_assets = st.multiselect(
        "Select Assets", 
        options=available_assets,
        default=[a for a in default_assets if a in available_assets],
        label_visibility="collapsed" # Hides the label to save space
    )
if selected_assets:
    # Convert list to tuple so Streamlit can hash it for caching
    assets_tuple = tuple(selected_assets)
    
    # 2. Caching: Store results for 2 days (172800 seconds) to prevent rate limits
    @st.cache_data(ttl=172800, show_spinner=False)
    def get_cached_cot_trends(url, token, assets):
        import requests
        # Create a temporary session for the cached function to avoid hashing complex objects
        temp_session = requests.Session()
        temp_session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        
        placeholders = ", ".join(["?"] * len(assets))
        sql = f"SELECT date, asset, long_pos, short_pos FROM cot_data WHERE asset IN ({placeholders}) ORDER BY date ASC"
        args = [{"type": "text", "value": a} for a in assets]
        
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
                a = extract(row.get("asset"))
                lpos = float(extract(row.get("long_pos", 0)))
                spos = float(extract(row.get("short_pos", 0)))
            else:
                d = extract(row[0])
                a = extract(row[1])
                lpos = float(extract(row[2]))
                spos = float(extract(row[3]))
                
            total = lpos + spos
            long_pct = (lpos / total * 100) if total > 0 else 50.0
            clean_data.append({"Date": d, "Asset": a, "Long %": long_pct})
            
        return clean_data
    with st.spinner("Loading historical COT data..."):
        try:
            # Fetch data via the cached function
            clean_data = get_cached_cot_trends(
                analyzer.turso_http_endpoint, 
                analyzer.turso_token, 
                assets_tuple
            )
            
            if clean_data:
                df = pd.DataFrame(clean_data)
                df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
                df = df.dropna(subset=["Date"]).sort_values("Date")
                
                fig = go.Figure()
                for asset in selected_assets:
                    asset_df = df[df["Asset"] == asset]
                    if not asset_df.empty:
                        fig.add_trace(go.Scatter(
                            x=asset_df["Date"], 
                            y=asset_df["Long %"],
                            mode="lines+markers",
                            name=asset,
                            line=dict(width=2.5),
                            hovertemplate="%{x|%d %b %Y}<br>Long: %{y:.1f}%<extra></extra>"
                        ))
                        
                fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
                
                fig.update_layout(
                    height=700, 
                    template="plotly_dark",
                    xaxis=dict(title="", showgrid=False),
                    yaxis=dict(
                        title="Long %",
                        range=[0, 100],
                        showgrid=True,
                        gridcolor="rgba(128,128,128,0.15)"
                    ),
                    hovermode="x unified",
                    margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor="#0b0f15",
                    plot_bgcolor="#0b0f15",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(
                    fig, use_container_width=True, config={"displayModeBar": False}
                )
            else:
                st.info("No historical data found for the selected assets.")
        except Exception as e:
            st.error(f"Error fetching data from database: {e}")
