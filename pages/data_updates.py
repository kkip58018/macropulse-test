import streamlit as st
from datetime import datetime
from analyzer import init_analyzer 
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = init_analyzer()

st.header("✏️ Update Market Data")
update_type = st.selectbox(
    "Select data type",
    [
        "Fundamentals (Indicator)",
        "COT Data",
        "2Y Yield Score (Asset Scorecard)",
        "Economic Strength Index Data",
    ],
)
if update_type == "Fundamentals (Indicator)":
    currency = st.selectbox("Currency", list(analyzer.currencies.keys()))
    if currency:
        indicators = list(CORE_INDICATORS) + list(SCORING_ONLY_INDICATORS)
        if currency in EXTRA_INDICATORS:
            indicators.extend(EXTRA_INDICATORS[currency])
        indicator = st.selectbox("Indicator", indicators)
        if (
            indicator
            and currency in analyzer.raw_data
            and indicator in analyzer.raw_data[currency]
        ):
            actual, forecast, date_val, prev_val = analyzer.raw_data[currency][
                indicator
            ]
            with st.form("fund_update"):
                new_date = st.text_input(
                    "Date (YYYY-MM-DD)", value=date_val if date_val else ""
                )
                new_prev = st.number_input(
                    "Previous", value=float(prev_val) if prev_val else 0.0
                )
                new_forecast = st.number_input("Forecast", value=float(forecast))
                new_actual = st.number_input("Actual", value=float(actual))
                if st.form_submit_button("Save Update"):
                    if analyzer.update_currency_indicator(
                        currency,
                        indicator,
                        new_actual,
                        new_forecast,
                        new_date,
                        new_prev if new_prev != 0 else None,
                    ):
                        st.session_state.success_msg = (
                            f"{currency} {indicator} updated successfully"
                        )
                        st.rerun()
                    else:
                        st.error("Update failed")
elif update_type == "COT Data":
    st.subheader("Insert / Update COT Record (Turso)")
    st.caption(
        "Open Interest is no longer used and will be set to 0 automatically."
    )
    all_assets = list(analyzer.cot_current.keys()) + [
        "EUR",
        "GBP",
        "JPY",
        "CHF",
        "AUD",
        "NZD",
        "CAD",
        "USD",
        "XAU",
        "XAG",
        "BTC",
        "ETH",
        "USOIL",
        "SPX500",
        "NAS100",
    ]
    asset = st.selectbox("Asset", sorted(set(all_assets)))
    asset_class = st.selectbox(
        "Asset Class", ["forex", "metal", "crypto", "index", "commodity"]
    )
    date_str = st.text_input(
        "Report Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d")
    )
    col1, col2 = st.columns(2)
    with col1:
        long_pos = st.number_input("Long Contracts", value=0.0, step=1.0)
    with col2:
        short_pos = st.number_input("Short Contracts", value=0.0, step=1.0)
    if st.button("Save COT Record"):
        if long_pos + short_pos == 0:
            st.error("Long + Short contracts cannot be zero.")
        else:
            success = analyzer.update_cot_record(
                asset=asset,
                asset_class=asset_class,
                date_str=date_str,
                long_pos=long_pos,
                short_pos=short_pos,
            )
            if success:
                st.session_state.success_msg = f"COT record for {asset} saved."
                st.rerun()
elif update_type == "2Y Yield Score (Asset Scorecard)":
    st.subheader("Update 2‑Year Yield Score (Manual)")
    st.markdown(
        "**+1** = Bullish (Yield > SMA), **0** = Neutral, **-1** = Bearish (Yield < SMA)"
    )
    analyzer._load_bond_yield_scores()
    bond_scores = getattr(analyzer, "bond_yield_scores", {})
    currency = st.selectbox("Currency", STANDARD_CURRENCIES)
    current_score = bond_scores.get(currency, 0)
    with st.form("bond_yield_score_form"):
        new_score = st.selectbox(
            "Score",
            options=[1, 0, -1],
            format_func=lambda x: f"{x:+d} ({'Bullish' if x>0 else 'Bearish' if x<0 else 'Neutral'})",
            index=(
                [1, 0, -1].index(current_score)
                if current_score in [1, 0, -1]
                else 1
            ),
        )
        if st.form_submit_button("Update Score"):
            if analyzer.update_bond_yield_score(currency, new_score):
                st.session_state.success_msg = (
                    f"2Y Yield score for {currency} updated to {new_score:+d}"
                )
                st.rerun()
            else:
                st.error("Update failed")
elif update_type == "Economic Strength Index Data":
    st.subheader("Update Economic Strength Index")
    analyzer._load_economic_strength()
    data = getattr(analyzer, "economic_strength", {})
    currency = st.selectbox(
        "Currency", STANDARD_CURRENCIES, key="eco_strength_currency"
    )
    current = data.get(currency, {})
    auto_key = f"eco_autofill_{currency}"
    if st.button(
        "🔄 Auto‑fill from existing indicator data", key=f"btn_autofill_{currency}"
    ):
        suggested = analyzer.auto_fill_economic_strength(currency)
        st.session_state[auto_key] = suggested
        st.rerun()
    prefilled = st.session_state.get(auto_key, current)
    with st.form("eco_strength_form"):
        col1, col2 = st.columns(2)
        with col1:
            gdp = st.number_input(
                "GDP Growth (%)",
                value=float(prefilled.get("gdp_growth", 0.0)),
                step=0.1,
                format="%.2f",
                key=f"gdp_{currency}",
            )
            unemp = st.number_input(
                "Unemployment Rate (%)",
                value=float(prefilled.get("unemployment_rate", 0.0)),
                step=0.1,
                format="%.2f",
                key=f"unemp_{currency}",
            )
            int_rate = st.number_input(
                "Interest Rate (%)",
                value=float(prefilled.get("interest_rate", 0.0)),
                step=0.1,
                format="%.2f",
                key=f"intrate_{currency}",
            )
        with col2:
            cpi = st.number_input(
                "CPI YoY (%)",
                value=float(prefilled.get("cpi_yoy", 0.0)),
                step=0.1,
                format="%.2f",
                key=f"cpi_{currency}",
            )
            real_yield = int_rate - cpi
            st.metric("Real Yield (%)", f"{real_yield:.2f}%")
        new_score = analyzer.calculate_economic_strength_score(
            {
                "gdp_growth": gdp,
                "unemployment_rate": unemp,
                "interest_rate": int_rate,
                "cpi_yoy": cpi,
                "real_yield": real_yield,
            }
        )
        new_bias = (
            "Bullish"
            if new_score >= 60
            else "Bearish" if new_score <= 39 else "Neutral"
        )
        prev_score = current.get("relative_strength_score", new_score)
        prev_real_yield = current.get("real_yield", real_yield)
        delta_score = new_score - prev_score
        delta_real_yield = real_yield - prev_real_yield
        col_score, col_bias = st.columns(2)
        with col_score:
            st.metric(
                "Relative Strength Score", new_score, delta=f"{delta_score:+d}"
            )
        with col_bias:
            st.markdown(f"**Bias:** {new_bias}")
        st.markdown("---")
        st.markdown(
            f"Δ Score: {delta_score:+d}  |  Δ Real Yield: {delta_real_yield:+.2f}%"
        )
        if st.form_submit_button("Save"):
            payload = {
                "gdp_growth": gdp,
                "unemployment_rate": unemp,
                "interest_rate": int_rate,
                "cpi_yoy": cpi,
                "real_yield": real_yield,
                "bias": new_bias,
                "relative_strength_score": new_score,
                "delta_score": delta_score,
                "delta_real_yield": delta_real_yield,
            }
            if analyzer.update_economic_strength(currency, payload):
                if auto_key in st.session_state:
                    del st.session_state[auto_key]
                st.session_state.success_msg = (
                    f"Economic Strength data for {currency} updated."
                )
                st.rerun()
            else:
                st.error("Update failed.")
