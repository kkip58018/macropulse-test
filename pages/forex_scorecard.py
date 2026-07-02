import streamlit as st
from analyzer import init_analyzer as get_analyzer
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()

st.header("📊 Forex Scorecard")
# 1. Fetch enriched pairs and prepare list
all_pairs = analyzer.get_enriched_pairs()
forex_only_pairs = [
    p
    for p in all_pairs
    if p[0] in STANDARD_CURRENCIES and p[1] in STANDARD_CURRENCIES
]
pair_list = []
for (
    base,
    quote,
    bias,
    overall,
    fund,
    cot,
    retail,
    trend,
    season,
) in forex_only_pairs:
    pair_key = f"{base}/{quote}"
    if overall is not None:
        display = f"{pair_key} ({int(overall):+d})"
    else:
        display = f"{pair_key} (N/A)"
    pair_list.append(
        (
            display,
            pair_key,
            overall if overall is not None else -999,
            (base, quote, bias, overall, fund, cot, retail, trend, season),
        )
    )
pair_list.sort(key=lambda x: x[2], reverse=True)
display_options = [item[0] for item in pair_list]
pair_map = {item[0]: item[3] for item in pair_list}
# 2. Layout: left (selector + gauge + history), right (grid of 6 cards)
left_col, right_col = st.columns([1, 2])
with left_col:
    selected_display = st.selectbox(
        "", display_options, key="detail_pair_select", label_visibility="collapsed"
    )
    if not display_options or selected_display not in pair_map:
        st.error("Pair data not found. Please reload the page.")
        st.stop()
    base, quote, bias, overall, fund, cot, retail, trend, season = pair_map[
        selected_display
    ]
    pair_key = selected_display.split()[0]  # e.g. "EUR/USD"
    # ---------- COMPACT OVERALL SCORE GAUGE ----------
    score_val = overall if overall is not None else 0
    gauge_pct = (score_val + 18) / 36 * 100
    gauge_pct = max(0, min(100, gauge_pct))
    if score_val >= 9:
        g_color = "#00ff88"
    elif score_val <= -9:
        g_color = "#ff4b4b"
    else:
        g_color = "#ffaa00"
    fig_gauge = go.Figure(
        go.Pie(
            values=[gauge_pct, 100 - gauge_pct],
            labels=["", ""],
            hole=0.78,
            marker=dict(colors=[g_color, "#1e2430"]),
            textinfo="none",
            hoverinfo="skip",
            showlegend=False,
            sort=False,
            direction="clockwise",
        )
    )
    fig_gauge.add_annotation(
        text=f"<b>{score_val:+.0f}</b>",
        x=0.5,
        y=0.52,
        font=dict(size=28, color="white"),
        showarrow=False,
    )
    fig_gauge.add_annotation(
        text=bias if bias else "Neutral",
        x=0.5,
        y=0.35,
        font=dict(size=13, color="#94a3b8"),
        showarrow=False,
    )
    fig_gauge.update_layout(
        height=180,
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="#0b0f15",
        plot_bgcolor="#0b0f15",
    )
    st.plotly_chart(
        fig_gauge, use_container_width=True, config={"displayModeBar": False}
    )
    # ---------- MACROPULSE SCORE OVER TIME (from Turso) ----------
    st.markdown("---")
    try:
        history = analyzer.get_forex_score_history(pair_key)
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
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=scores_list,
                    marker_color=colors,
                    width=0.8 * 86400000,
                    hovertemplate="%{y:+.1f}<extra>%{x|%d %b %Y}</extra>",
                )
            )
            fig.add_hline(y=0, line_color="white", opacity=0.4, line_width=1)
            fig.update_layout(
                template="plotly_dark",
                title=f"MacroPulse Score Over Time — {pair_key}",
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
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No historical data points available for {pair_key} yet.")
    except Exception as e:
        st.error(f"Error loading historical scores: {e}")
# ==================== RIGHT COLUMN: 2x3 GRID OF CARDS ====================
with right_col:
    # Updated CSS: larger font, more padding
    st.markdown(
        """
    <style>
    .gauge-details {
        font-size: 0.85rem;
        color: #94a3b8;
        max-height: 150px;
        overflow-y: auto;
        line-height: 1.5;
        border-top: 1px solid #1e2430;
        padding: 6px 0 8px 0;
        margin-top: 0px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    # Helper: 5‑level bias word for component scores (-2 to 2)
    def component_bias(val):
        if val >= 2:
            return "Very Bullish"
        elif val == 1:
            return "Bullish"
        elif val == 0:
            return "Neutral"
        elif val == -1:
            return "Bearish"
        elif val <= -2:
            return "Very Bearish"
        return "Unknown"
    # Helper: invert bias for crowd (e.g., Very Bullish -> Very Bearish)
    def invert_bias(word):
        mapping = {
            "Very Bullish": "Very Bearish",
            "Bullish": "Bearish",
            "Neutral": "Neutral",
            "Bearish": "Bullish",
            "Very Bearish": "Very Bullish",
        }
        return mapping.get(word, word)
    # Indicator lists – growth list will be extended for JPY pairs later
    # Add Household Spending for JPY pairs
    if "JPY" in (base, quote):
        GROWTH.append("Household spending")
    def get_indicator_nets(base, quote, indicator_list):
        base_scores = analyzer.indicator_scores.get(base, {})
        quote_scores = analyzer.indicator_scores.get(quote, {})
        nets = {}
        for ind in indicator_list:
            if ind in base_scores or ind in quote_scores:
                b = base_scores.get(ind, 0)
                q = quote_scores.get(ind, 0)
                nets[ind] = b - q
        return nets
    # Compute the six scores
    technicals = (trend if trend is not None else 0) + (
        season if season is not None else 0
    )
    institutional = cot if cot is not None else 0
    retail_score_val = retail if retail is not None else 0
    growth_nets = get_indicator_nets(base, quote, GROWTH)
    eco_growth = sum(growth_nets.values())
    jobs_nets = get_indicator_nets(base, quote, JOBS)
    jobs = sum(jobs_nets.values())
    infl_nets = get_indicator_nets(base, quote, INFLATION)
    inflation = sum(infl_nets.values())
    # ---------- Institutional Activity breakdown ----------
    def get_institutional_details(base, quote):
        if base not in analyzer.cot_current or quote not in analyzer.cot_current:
            return ["COT data missing for one or both currencies."]
        net_base_cur = analyzer.get_net_position(analyzer.cot_current[base])
        net_quote_cur = analyzer.get_net_position(analyzer.cot_current[quote])
        net_base_prev = analyzer.get_net_position(analyzer.cot_prev.get(base, 50))
        net_quote_prev = analyzer.get_net_position(analyzer.cot_prev.get(quote, 50))
        current_diff = net_base_cur - net_quote_cur
        prev_diff = net_base_prev - net_quote_prev
        change = current_diff - prev_diff
        if current_diff >= 60:
            pos_text = "Very Bullish"
        elif current_diff >= 20:
            pos_text = "Bullish"
        elif current_diff <= -60:
            pos_text = "Very Bearish"
        elif current_diff <= -20:
            pos_text = "Bearish"
        else:
            pos_text = "Neutral"
        if change > 0.01:
            chg_text = "Bullish"
        elif change < -0.01:
            chg_text = "Bearish"
        else:
            chg_text = "Neutral"
        return [
            f"COT Net Positioning: {pos_text}",
            f"COT Weekly Change: {chg_text}",
        ]
    # ---------- Retail Bias details (based on contrarian score) ----------
    def get_retail_details(contrarian_score, is_pc=False):
        val = int(round(contrarian_score))
        sentiment = component_bias(val)
        crowd = invert_bias(sentiment)
        source = "Put/Call Sentiment" if is_pc else "Retail Sentiment"
        return [
            f"{source}: {sentiment}",
            f"Crowd bias - crowd is {crowd.lower()}",
        ]
    # Mini gauge card builder
    def mini_gauge_card(title, score, details_lines, min_val=-6, max_val=6):
        if score >= 1:
            bias_str = "Bullish"
            clr = "#00ff88"
        elif score <= -1:
            bias_str = "Bearish"
            clr = "#ff4b4b"
        else:
            bias_str = "Neutral"
            clr = "#ffaa00"
        gauge_pct = (score - min_val) / (max_val - min_val) * 100
        gauge_pct = max(0, min(100, gauge_pct))
        fig = go.Figure(
            go.Pie(
                values=[gauge_pct, 100 - gauge_pct],
                labels=["", ""],
                hole=0.75,
                marker=dict(colors=[clr, "#1e2430"]),
                textinfo="none",
                hoverinfo="skip",
                showlegend=False,
                sort=False,
                direction="clockwise",
            )
        )
        fig.add_annotation(
            text=f"{score:+.0f}",
            x=0.5,
            y=0.6,
            font=dict(size=14, color="white", family="Arial, sans-serif"),
            showarrow=False,
        )
        fig.add_annotation(
            text=bias_str,
            x=0.5,
            y=0.3,
            font=dict(size=10, color="#94a3b8"),
            showarrow=False,
        )
        fig.update_layout(
            height=140,
            margin=dict(l=5, r=5, t=35, b=5),
            paper_bgcolor="#0b0f15",
            plot_bgcolor="#0b0f15",
            title=dict(
                text=title,
                font=dict(size=12, color="#94a3b8"),
                x=0.5,
                y=0.95,
                xanchor="center",
            ),
            hovermode=False,
        )
        details_html = "<br>".join(details_lines)
        return fig, details_html
    # Build cards
    cards = []
    # 1. Technicals
    t_fig, t_det = mini_gauge_card(
        "Technicals",
        technicals,
        [
            f"Trend: {component_bias(trend)}",
            f"Seasonality: {component_bias(season)}",
        ],
    )
    cards.append((t_fig, t_det))
    # 2. Institutional Activity
    inst_lines = get_institutional_details(base, quote)
    i_fig, i_det = mini_gauge_card(
        "Institutional Activity", institutional, inst_lines
    )
    cards.append((i_fig, i_det))
    # 3. Retail Bias (contrarian score used to derive sentiment and crowd)
    is_nonforex = base in [
        "XAU",
        "XAG",
        "BTC",
        "ETH",
        "USOIL",
        "SPX500",
        "NAS100",
    ]
    uses_put_call = (is_nonforex and base != "ETH") or (base == "USD")
    retail_lines = get_retail_details(retail_score_val, is_pc=uses_put_call)
    r_fig, r_det = mini_gauge_card("Sentiment Bias", retail_score_val, retail_lines)
    cards.append((r_fig, r_det))
    # 4. Eco Growth (includes Household Spending for JPY pairs)
    growth_lines = [
        f"{ind} vs Forecast: {component_bias(net)}"
        for ind, net in growth_nets.items()
    ]
    g_fig, g_det = mini_gauge_card(
        "Economic Growth comparison", eco_growth, growth_lines
    )
    cards.append((g_fig, g_det))
    # 5. Job Market
    jobs_lines = [
        f"{ind} vs Forecast: {component_bias(net)}"
        for ind, net in jobs_nets.items()
    ]
    j_fig, j_det = mini_gauge_card("Job Market comparison", jobs, jobs_lines)
    cards.append((j_fig, j_det))
    # 6. Inflation Data
    infl_lines = [
        f"{ind} vs Forecast: {component_bias(net)}"
        for ind, net in infl_nets.items()
    ]
    infl_fig, infl_det = mini_gauge_card(
        "Inflation Data comparison", inflation, infl_lines
    )
    cards.append((infl_fig, infl_det))
    # Render 2 rows of 3
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)
    for idx, (fig, det_html) in enumerate(cards):
        if idx < 3:
            col = row1_cols[idx]
        else:
            col = row2_cols[idx - 3]
        with col:
            with st.container(border=True):
                st.plotly_chart(
                    fig, use_container_width=True, config={"displayModeBar": False}
                )
                st.markdown(
                    f'<div class="gauge-details">{det_html}</div>',
                    unsafe_allow_html=True,
                )