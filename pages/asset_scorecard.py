import streamlit as st
from datetime import datetime
from analyzer import init_analyzer as get_analyzer

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


st.markdown(
    """
<style>
.tooltip-wrapper { display: inline-block; position: relative; margin-left: 8px; }
.info-icon { background-color: #1e2430; color: #94a3b8; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; cursor: help; border: 1px solid #2a3340; }
.tooltip-content { visibility: hidden; opacity: 0; position: absolute; top: 30px; left: 0; background-color: #0f131a; border: 1px solid #1e2430; border-radius: 8px; padding: 16px 20px; width: 480px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); z-index: 1000; transition: opacity 0.2s; color: #ddd; font-size: 12px; line-height: 1.5; pointer-events: none; }
.tooltip-wrapper:hover .tooltip-content { visibility: visible; opacity: 1; }
.tooltip-section { margin-bottom: 12px; }
.tooltip-title { color: #00b8ff; font-weight: bold; margin-bottom: 4px; }
.tooltip-sub { color: #94a3b8; margin-left: 10px; }
.page-title { display: flex; align-items: center; }
</style>
<div class="page-title">
    <h2 style="margin: 0;">📋 Asset Scorecard</h2>
    <div class="tooltip-wrapper">
        <span class="info-icon">ℹ️</span>
        <div class="tooltip-content">
            <div class="tooltip-section">
                <div class="tooltip-title">📊 Fundamentals Score</div>
                <div class="tooltip-sub">Sum of individual indicator scores: +1 beat, 0 neutral, -1 miss.<br>
                For metals, USD data is inverted. Crypto, Oil, and Indices invert inflation (lower is bullish).<br>
                <b>Includes 2Y Yield score (manually set).</b></div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-title">📈 Technical Score (Range: -5 to +5)</div>
                <div class="tooltip-sub">Trend (aggregated across all pairs) + Seasonality (aggregated).</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-title">🪙 Sentiment Score (Range: -5 to +5)</div>
                <div class="tooltip-sub">Retail (contrarian) + COT Net Positioning + COT Weekly Change.</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-title">🏆 Overall Score</div>
                <div class="tooltip-sub">Sum of Fundamentals + Technical + Sentiment.</div>
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """<style>div[data-baseweb="select"] { max-width: 100% !important; }</style>""",
    unsafe_allow_html=True,
)
ASSET_DISPLAY_MAP = {
    "AU Dollar": {
        "type": "forex",
        "base": "AUD",
        "trend_symbol": "AUDUSD",
        "exchange": "FX_IDC",
        "yf": "AUD=X",
    },
    "CA Dollar": {
        "type": "forex",
        "base": "CAD",
        "trend_symbol": "CADUSD",
        "exchange": "FX_IDC",
        "yf": "CAD=X",
    },
    "Euro": {
        "type": "forex",
        "base": "EUR",
        "trend_symbol": "EURUSD",
        "exchange": "FX_IDC",
        "yf": "EUR=X",
    },
    "GB Pound": {
        "type": "forex",
        "base": "GBP",
        "trend_symbol": "GBPUSD",
        "exchange": "FX_IDC",
        "yf": "GBP=X",
    },
    "JP Yen": {
        "type": "forex",
        "base": "JPY",
        "trend_symbol": "USDJPY",
        "exchange": "FX_IDC",
        "yf": "JPY=X",
    },
    "NZ Dollar": {
        "type": "forex",
        "base": "NZD",
        "trend_symbol": "NZDUSD",
        "exchange": "FX_IDC",
        "yf": "NZD=X",
    },
    "Swiss Franc": {
        "type": "forex",
        "base": "CHF",
        "trend_symbol": "CHFUSD",
        "exchange": "FX_IDC",
        "yf": "CHF=X",
    },
    "US Dollar": {
        "type": "forex",
        "base": "USD",
        "trend_symbol": "DXY",
        "exchange": "INDEX",
        "yf": "DX-Y.NYB",
    },
    "Bitcoin": {
        "type": "crypto",
        "base": "BTC",
        "trend_symbol": "BTCUSD",
        "exchange": "COINBASE",
        "yf": "BTC-USD",
    },
    "Ethereum": {
        "type": "crypto",
        "base": "ETH",
        "trend_symbol": "ETHUSD",
        "exchange": "COINBASE",
        "yf": "ETH-USD",
    },
    "Gold": {
        "type": "metal",
        "base": "XAU",
        "trend_symbol": "XAUUSD",
        "exchange": "OANDA",
        "yf": "GC=F",
    },
    "Silver": {
        "type": "metal",
        "base": "XAG",
        "trend_symbol": "XAGUSD",
        "exchange": "OANDA",
        "yf": "SI=F",
    },
    "US Oil": {
        "type": "commodity",
        "base": "USOIL",
        "trend_symbol": "USOIL",
        "exchange": "OANDA",
        "yf": "CL=F",
    },
    "S&P 500": {
        "type": "index",
        "base": "SPX500",
        "trend_symbol": "SPX500USD",
        "exchange": "OANDA",
        "yf": "^GSPC",
    },
    "Nasdaq": {
        "type": "index",
        "base": "NAS100",
        "trend_symbol": "NAS100USD",
        "exchange": "OANDA",
        "yf": "^IXIC",
    },
}
sorted_display_names = sorted(ASSET_DISPLAY_MAP.keys())
# ==================== LEFT COLUMN (Dropdown + Gauge + History) ====================
left_col, right_col = st.columns([1, 2])
with left_col:
    selected_display = st.selectbox(
        "",
        sorted_display_names,
        key="scorecard_asset",
        label_visibility="collapsed",
    )
    asset_info = ASSET_DISPLAY_MAP[selected_display]
    asset_type = asset_info["type"]
    base = asset_info["base"]
    trend_symbol = asset_info["trend_symbol"]
    exchange = asset_info["exchange"]
    yf_symbol = asset_info["yf"]
    is_metal = asset_type == "metal"
    is_crypto = asset_type == "crypto"
    is_oil = asset_type == "commodity"
    is_index = asset_type == "index"
    is_forex = asset_type == "forex"
    # ---------- Trend fetching (unchanged) ----------
    def get_trend_for_asset(symbol, exch, yf_sym, base_curr):
        try:
            invert_trend = base_curr == "JPY"
            handler = TA_Handler(
                symbol=symbol,
                screener=(
                    "forex"
                    if exch == "FX_IDC"
                    else "crypto" if exch == "COINBASE" else "forex"
                ),
                exchange=exch,
                interval=Interval.INTERVAL_1_DAY,
            )
            analysis = handler.get_analysis()
            indicators = analysis.indicators
            ma_values = {}
            for period in analyzer.ma_periods:
                ma_key = f"SMA{period}"
                ma_values[period] = indicators.get(ma_key) or indicators.get(
                    f"EMA{period}"
                )
            close = indicators.get("close")
            if close is None or any(v is None for v in ma_values.values()):
                raise Exception("Missing data from TradingView")
            if invert_trend:
                below_count = sum(1 for ma in ma_values.values() if close < ma)
            else:
                below_count = sum(1 for ma in ma_values.values() if close > ma)
            total = len(ma_values)
            raw_score = (below_count / total) * 4 - 2
            score = max(-2, min(2, round(raw_score)))
            trend = "Up" if score >= 1 else "Down" if score <= -1 else "Sideways"
            return trend, score, "", True
        except:
            try:
                ticker = yf.Ticker(yf_sym)
                df = ticker.history(period="1y", interval="1d")
                if df.empty:
                    return "Unknown", 0, "", False
                close_prices = df["Close"]
                latest_close = close_prices.iloc[-1]
                ma_values = {}
                for period in analyzer.ma_periods:
                    if len(close_prices) >= period:
                        ma = close_prices.rolling(window=period).mean().iloc[-1]
                        ma_values[period] = ma
                invert_trend = base_curr == "JPY"
                if invert_trend:
                    below_count = sum(
                        1 for ma in ma_values.values() if latest_close < ma
                    )
                else:
                    below_count = sum(
                        1 for ma in ma_values.values() if latest_close > ma
                    )
                total = len(ma_values)
                raw_score = (below_count / total) * 4 - 2
                score = max(-2, min(2, round(raw_score)))
                trend = (
                    "Up" if score >= 1 else "Down" if score <= -1 else "Sideways"
                )
                return trend, score, "", True
            except:
                return "Error", 0, "", False
    # ---------- Indicator lists ----------
    INFLATION_INDICATORS = ["CPI YoY", "PPI YoY"]
    GROWTH_INDICATORS = [
        "GDP",
        "Retail Sales",
        "Manufacturing PMI",
        "Services PMI",
        "Consumer Confidence",
    ]
    JOBS_INDICATORS = [
        "Unemployment Rate",
        "NFP",
        "Unemployment claims",
        "ADP",
        "JOLTS job openings",
    ]
    data_currency = base if is_forex else "USD"
    invert_growth_jobs = is_metal
    invert_inflation = is_metal or is_crypto or is_oil or is_index
    if data_currency == "USD":
        INFLATION_INDICATORS.append("PCE YoY")
    if data_currency not in analyzer.raw_data:
        st.warning(
            f"No economic data loaded for {data_currency}. Please update indicators."
        )
        st.stop()
    data = analyzer.raw_data[data_currency]
    scores = analyzer.indicator_scores.get(data_currency, {})
    def get_category_summary(category_indicators, invert=False):
        rows = []
        total = 0
        for ind in category_indicators:
            if ind not in data:
                continue
            actual, forecast, date_val, prev_val = data[ind]
            if actual is None or forecast is None:
                continue
            score = scores.get(ind, 0)
            if invert:
                score = -score
            total += score
            surprise = actual - forecast
            bias = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"
            rows.append(
                {
                    "Indicator": ind,
                    "Bias": bias,
                    "Actual": f"{actual:.2f}",
                    "Forecast": f"{forecast:.2f}",
                    "Surprise": f"{surprise:+.2f}",
                }
            )
        overall_bias = (
            "Bullish" if total > 0 else "Bearish" if total < 0 else "Neutral"
        )
        return rows, total, overall_bias
    growth_rows, growth_score, growth_bias = get_category_summary(
        GROWTH_INDICATORS, invert=invert_growth_jobs
    )
    jobs_rows, jobs_score, jobs_bias = get_category_summary(
        JOBS_INDICATORS, invert=invert_growth_jobs
    )
    inflation_rows, inflation_score, inflation_bias = get_category_summary(
        INFLATION_INDICATORS, invert=invert_inflation
    )
    # Bond yield score
    bond_scores = getattr(analyzer, "bond_yield_scores", {})
    bond_score_raw = bond_scores.get(data_currency, 0)
    if invert_growth_jobs:
        bond_score_raw = -bond_score_raw
    bond_bias = (
        "Bullish"
        if bond_score_raw > 0
        else "Bearish" if bond_score_raw < 0 else "Neutral"
    )
    inflation_rows.append(
        {
            "Indicator": f"{data_currency} 2Y Yield (21d SMA)",
            "Bias": bond_bias,
            "Actual": "—",
            "Forecast": "—",
            "Surprise": "—",
        }
    )
    inflation_display_score = inflation_score + bond_score_raw
    if inflation_display_score > 0:
        inflation_bias = "Bullish"
    elif inflation_display_score < 0:
        inflation_bias = "Bearish"
    else:
        inflation_bias = "Neutral"
    # Overall fundamental score
    if is_forex:
        fund_score = analyzer.currency_scores.get(base, 0) + bond_score_raw
    else:
        fund_score = growth_score + jobs_score + inflation_score + bond_score_raw
    # Trend / retail / seasonality
    current_month = datetime.now().strftime("%b")
    pair_for_asset = f"{base}/USD" if not is_forex else None
    if is_forex:
        def get_agg_score(curr, func):
            scores = []
            for pair_str in FOREX_PAIRS:
                if curr not in pair_str:
                    continue
                base_p, quote_p = pair_str.split("/")
                sign = 1 if curr == base_p else -1
                scores.append(sign * func(pair_str))
            return sum(scores) / len(scores) if scores else 0.0
        if base == "USD" and hasattr(analyzer, "usd_pc_score"):
            retail_score_raw = analyzer.usd_pc_score
        else:
            retail_score_raw = round(
                get_agg_score(base, lambda p: analyzer.retail_scores.get(p, 0.0))
            )
        trend_score = round(
            get_agg_score(
                base,
                lambda p: analyzer.fetch_trend_from_tradingview(p, use_cache=True)[
                    1
                ],
            )
        )
        season_score = round(
            get_agg_score(
                base, lambda p: analyzer.get_seasonality_score(p, current_month)
            )
        )
    else:
        retail_score_raw = round(analyzer.retail_scores.get(pair_for_asset, 0.0))
        _, trend_score, _, _ = get_trend_for_asset(
            trend_symbol, exchange, yf_symbol, base
        )
        season_score = analyzer.get_seasonality_score(pair_for_asset, current_month)
    technical_score = max(-5, min(5, trend_score + season_score))
    # COT
    cot_net_score = 0
    cot_change_score = 0
    cot_available = base in analyzer.cot_current
    if cot_available:
        cur_long = analyzer.cot_current[base]
        cur_net = cur_long - (100 - cur_long)
        if base in analyzer.cot_prev:
            prev_long = analyzer.cot_prev[base]
            prev_net = prev_long - (100 - prev_long)
            change = cur_net - prev_net
        else:
            change = 0.0
        if cur_net >= 60:
            cot_net_score = 2
        elif cur_net >= 20:
            cot_net_score = 1
        elif cur_net <= -60:
            cot_net_score = -2
        elif cur_net <= -20:
            cot_net_score = -1
        if change > 0:
            cot_change_score = 1
        elif change < 0:
            cot_change_score = -1
    combined_sentiment_score = retail_score_raw + cot_net_score + cot_change_score
    combined_sentiment_score = max(-5, min(5, combined_sentiment_score))
    overall_score = fund_score + technical_score + combined_sentiment_score
    # ---------- Overall Score Gauge ----------
    gauge_value = max(0, min(100, (overall_score + 10) / 20 * 100))
    gauge_color = (
        "#00ff88"
        if overall_score >= 5
        else ("#ffaa00" if overall_score >= 0 else "#ff4b4b")
    )
    fig_gauge = go.Figure(
        go.Pie(
            values=[gauge_value, 100 - gauge_value],
            labels=["", ""],
            hole=0.75,
            marker=dict(colors=[gauge_color, "#1e2430"]),
            textinfo="none",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig_gauge.add_annotation(
        text=f"<b>{overall_score:+.0f}</b>",
        x=0.5,
        y=0.55,
        font=dict(size=32, color="white"),
        showarrow=False,
    )
    fig_gauge.add_annotation(
        text="Overall Score",
        x=0.5,
        y=0.35,
        font=dict(size=12, color="#94a3b8"),
        showarrow=False,
    )
    fig_gauge.update_layout(
        height=200,
        margin=dict(l=5, r=5, t=10, b=10),
        paper_bgcolor="#0f131a",
        plot_bgcolor="#0f131a",
    )
    st.plotly_chart(
        fig_gauge, use_container_width=True, config={"displayModeBar": False}
    )
    # ---------- Historical Score Chart (height reduced 15%) ----------
    st.markdown("---")
    if is_forex:
        hist_asset = base
    else:
        hist_asset = f"{base}/USD"
    try:
        history = analyzer.get_asset_score_history(hist_asset)
        if history:
            dates = [h[0] for h in history]
            scores_list = [h[1] for h in history]
            colors = []
            for v in scores_list:
                if -4 <= v <= 4:
                    colors.append("#EDEBEB")
                elif v > 4:
                    colors.append("#00ff88")
                else:
                    colors.append("#ff4b4b")
            fig_hist = go.Figure()
            fig_hist.add_trace(
                go.Bar(
                    x=dates,
                    y=scores_list,
                    marker_color=colors,
                    width=0.8 * 86400000,
                    hovertemplate="%{y:+.1f}<extra>%{x}</extra>",
                )
            )
            fig_hist.add_hline(y=0, line_color="white", opacity=0.4, line_width=1)
            fig_hist.update_layout(
                template="plotly_dark",
                title=f"MacroPulse Score Over Time — {selected_display}",
                xaxis=dict(title="", tickformat="%d %b\n%Y", showgrid=False),
                yaxis=dict(
                    title="Score",
                    zeroline=False,
                    showgrid=True,
                    gridcolor="rgba(128,128,128,0.15)",
                    range=[-18, 18],
                    tickmode="linear",
                    dtick=6,
                    showticklabels=False,
                ),
                hovermode="x unified",
                margin=dict(l=20, r=20, t=20, b=10),
                paper_bgcolor="#0b0f15",
                plot_bgcolor="#0b0f15",
                showlegend=False,
                height=380,  # ← reduced by ~15%
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info(
                f"No historical data for {selected_display} yet. Scores are stored automatically when indicators are updated."
            )
    except Exception as e:
        st.error(f"Error loading historical scores: {e}")
# ==================== RIGHT COLUMN: Detail Panels (with fixed column widths) ====================
with right_col:
    st.markdown(
        """
    <style>
    .scorecard-compact-panel {
        background-color: #0f131a; border: 1px solid #1e2430; border-radius: 8px;
        padding: 6px 8px; margin-bottom: 5px;
    }
    .scorecard-compact-title {
        font-size: 16px; font-weight: bold; color: #eee; border-bottom: 1px solid #1e2430;
        padding-bottom: 2px; margin-bottom: 4px;
        display: flex; justify-content: space-between; align-items: baseline;
    }
    .scorecard-compact-title .col-headers {
        display: flex; gap: 0.2rem; font-size: 15px; font-weight: normal; color: #94a3b8; margin-right: 2px;
    }
    .col-headers span { width: 2.8rem; text-align: right; }
    .data-table { width: 100%; border-collapse: collapse; color: #ddd; font-size: 14px; }
    .data-table th, .data-table td { text-align: left; padding: 2px 4px; border-bottom: 1px solid #1e2430; }
    .data-table .num-cell { width: 2.8rem; text-align: right; font-variant-numeric: tabular-nums; }
    .data-table .indicator-cell {
        max-width: 110px;                /* ← limits the indicator column width */
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .bullish-text { color: #00ff88; font-weight: bold; }
    .bearish-text { color: #ff4b4b; font-weight: bold; }
    .status-badge-blue { background-color: #1e3a5f; color: #00b8ff; padding: 1px 4px; border-radius: 4px; font-size: 10px; font-weight: bold; display: inline-block; }
    .status-badge-red { background-color: #5f1e1e; color: #ff4b4b; padding: 1px 4px; border-radius: 4px; font-size: 10px; font-weight: bold; display: inline-block; }
    .status-badge-grey { background-color: #2a2a2a; color: #ccc; padding: 1px 4px; border-radius: 4px; font-size: 10px; display: inline-block; }
    .panel-heading-blue { color: #00b8ff; font-weight: bold; }
    .panel-heading-red { color: #ff4b4b; font-weight: bold; }
    </style>
    """,
        unsafe_allow_html=True,
    )
    def render_row(indicator, bias, actual, forecast, surprise):
        bias_class = (
            "status-badge-blue"
            if bias == "Bullish"
            else ("status-badge-red" if bias == "Bearish" else "status-badge-grey")
        )
        surprise_class = ""
        try:
            val = float(str(surprise).replace("%", "").replace("+", ""))
            surprise_class = (
                "bullish-text" if val > 0 else ("bearish-text" if val < 0 else "")
            )
        except:
            pass
        return (
            f"<tr>"
            f"<td class='indicator-cell'>{indicator}</td>"
            f"<td><span class='{bias_class}'>{bias}</span></td>"
            f"<td class='num-cell'>{actual}</td>"
            f"<td class='num-cell'>{forecast}</td>"
            f"<td class='num-cell {surprise_class}'>{surprise}</td>"
            f"</tr>"
        )
    # Row with Technicals + Sentiment side by side
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        trend_intensity = (
            "Very Bullish"
            if trend_score >= 2
            else (
                "Bullish"
                if trend_score == 1
                else (
                    "Very Bearish"
                    if trend_score <= -2
                    else "Bearish" if trend_score == -1 else "Neutral"
                )
            )
        )
        trend_class = (
            "panel-heading-blue"
            if "Bullish" in trend_intensity
            else ("panel-heading-red" if "Bearish" in trend_intensity else "")
        )
        season_intensity = (
            "Very Bullish"
            if season_score >= 2
            else (
                "Bullish"
                if season_score == 1
                else (
                    "Very Bearish"
                    if season_score <= -2
                    else "Bearish" if season_score == -1 else "Neutral"
                )
            )
        )
        season_class = (
            "panel-heading-blue"
            if "Bullish" in season_intensity
            else ("panel-heading-red" if "Bearish" in season_intensity else "")
        )
        st.markdown(
            f"""
        <div class="scorecard-compact-panel">
            <div class="scorecard-compact-title">📈 Technicals</div>
            <span style="color: #94a3b8; font-size: 15px;">Daily chart trend:</span> <span class="{trend_class}">{trend_intensity}</span><br>
            <span style="color: #94a3b8; font-size: 15px;">Seasonality:</span> <span class="{season_class}">{season_intensity}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_r2:
        retail_intensity = (
            "Very Bullish"
            if retail_score_raw >= 2
            else (
                "Bullish"
                if retail_score_raw >= 1
                else (
                    "Very Bearish"
                    if retail_score_raw <= -2
                    else "Bearish" if retail_score_raw <= -1 else "Neutral"
                )
            )
        )
        cot_net_pos_text = "N/A"
        cot_change_text = "N/A"
        cot_net_pos_class = ""
        cot_change_class = ""
        if cot_available:
            cur_long = analyzer.cot_current[base]
            cur_net = cur_long - (100 - cur_long)
            if base in analyzer.cot_prev:
                prev_long = analyzer.cot_prev[base]
                prev_net = prev_long - (100 - prev_long)
                change = cur_net - prev_net
            else:
                change = 0.0
            if cur_net >= 60:
                cot_net_pos_text = "Very Bullish"
                cot_net_pos_class = "panel-heading-blue"
            elif cur_net >= 20:
                cot_net_pos_text = "Bullish"
                cot_net_pos_class = "panel-heading-blue"
            elif cur_net <= -60:
                cot_net_pos_text = "Very Bearish"
                cot_net_pos_class = "panel-heading-red"
            elif cur_net <= -20:
                cot_net_pos_text = "Bearish"
                cot_net_pos_class = "panel-heading-red"
            else:
                cot_net_pos_text = "Neutral"
            cot_change_text = (
                "Bullish" if change > 0 else ("Bearish" if change < 0 else "Flat")
            )
            cot_change_class = (
                "panel-heading-blue"
                if cot_change_text == "Bullish"
                else ("panel-heading-red" if cot_change_text == "Bearish" else "")
            )
        cot_net_html = (
            f'<span style="color: #94a3b8; font-size: 15px;">COT Net Positioning:</span> <span class="{cot_net_pos_class}">{cot_net_pos_text}</span><br>'
            if cot_available
            else '<span style="color: #94a3b8; font-size: 12px;">COT Net Positioning:</span> N/A<br>'
        )
        cot_change_html = (
            f'<span style="color: #94a3b8; font-size: 15px;">COT Latest Buys/Sells:</span> <span class="{cot_change_class}">{cot_change_text}</span><br>'
            if cot_available
            else '<span style="color: #94a3b8; font-size: 12px;">COT Latest Buys/Sells:</span> N/A<br>'
        )
        st.markdown(
            f"""
        <div class="scorecard-compact-panel">
            <div class="scorecard-compact-title">🪙 Sentiment + COT</div>
            <span style="color: #94a3b8; font-size: 15px;">Retail Bias:</span> <span class="{'panel-heading-blue' if 'Bullish' in retail_intensity else 'panel-heading-red' if 'Bearish' in retail_intensity else ''}">{retail_intensity}</span><br>
            {cot_net_html}
            {cot_change_html}
        </div>
        """,
            unsafe_allow_html=True,
        )
    # Growth panel
    growth_bias_span = f"<span class=\"{'panel-heading-blue' if growth_bias == 'Bullish' else 'panel-heading-red' if growth_bias == 'Bearish' else ''}\">{growth_bias}</span>"
    growth_rows_html = "".join(
        render_row(
            r["Indicator"], r["Bias"], r["Actual"], r["Forecast"], r["Surprise"]
        )
        for r in growth_rows
    )
    st.markdown(
        f"""
    <div class="scorecard-compact-panel">
        <div class="scorecard-compact-title">
            <span>📊 Growth Bias {growth_bias_span}</span>
            <span class="col-headers">
                <span>Act</span><span>Fcst</span><span>Surp</span>
            </span>
        </div>
        <table class="data-table">
            <tbody>{growth_rows_html}</tbody>
        </table>
    </div>
    """,
        unsafe_allow_html=True,
    )
    # Inflation panel
    inflation_bias_span = f"<span class=\"{'panel-heading-blue' if inflation_bias == 'Bullish' else 'panel-heading-red' if inflation_bias == 'Bearish' else ''}\">{inflation_bias}</span>"
    inflation_rows_html = "".join(
        render_row(
            r["Indicator"], r["Bias"], r["Actual"], r["Forecast"], r["Surprise"]
        )
        for r in inflation_rows
    )
    st.markdown(
        f"""
    <div class="scorecard-compact-panel">
        <div class="scorecard-compact-title">
            <span>💰 Inflation Bias {inflation_bias_span}</span>
            <span class="col-headers">
                <span>Act</span><span>Fcst</span><span>Surp</span>
            </span>
        </div>
        <table class="data-table">
            <tbody>{inflation_rows_html}</tbody>
        </table>
    </div>
    """,
        unsafe_allow_html=True,
    )
    # Jobs panel
    jobs_bias_span = f"<span class=\"{'panel-heading-blue' if jobs_bias == 'Bullish' else 'panel-heading-red' if jobs_bias == 'Bearish' else ''}\">{jobs_bias}</span>"
    jobs_rows_html = "".join(
        render_row(
            r["Indicator"], r["Bias"], r["Actual"], r["Forecast"], r["Surprise"]
        )
        for r in jobs_rows
    )
    st.markdown(
        f"""
    <div class="scorecard-compact-panel">
        <div class="scorecard-compact-title">
            <span>👥 Jobs Market Bias {jobs_bias_span}</span>
            <span class="col-headers">
                <span>Act</span><span>Fcst</span><span>Surp</span>
            </span>
        </div>
        <table class="data-table">
            <tbody>{jobs_rows_html}</tbody>
        </table>
    </div>
    """,
        unsafe_allow_html=True,
    )
