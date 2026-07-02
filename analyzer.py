import streamlit as st
import pandas as pd
import json
import requests
from tradingview_ta import TA_Handler, Interval
import re
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.graph_objects as go
from db import supabase_admin
from config import *
from utils import *
try:
    import cot_reports as cot_reports_lib

    COT_AVAILABLE = True
except ImportError:
    COT_AVAILABLE = False



# ======================= MAIN ANALYZER CLASS =======================
class CurrencyFundamentalAnalyzer:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.currencies = {}
        self.currency_scores = {}
        self.currency_percentages = {}
        self.raw_data = {}
        self.indicator_scores = {}
        self.cot_current = {}  
        self.cot_prev = {}  
        self.cot_raw = []  
        self.retail_scores = {}
        self.retail_long_pct = {}
        self._seasonality_cache = {} 
        self.ma_periods = [20, 50, 100, 200]
        self.trend_cache = {}
        self.trend_config_file = Path.cwd() / "trend_config.json"
        self.bond_yield_scores = {}
        self.economic_strength = {}
        self._load_trend_config()
        self._calibrate_score_coefficients()

        # ---------- Turso (HTTP) connection ----------
        self.turso_url = st.secrets.get("TURSO_DATABASE_URL", "")
        self.turso_token = st.secrets.get("TURSO_AUTH_TOKEN", "")
        self.turso_session = None
        if self.turso_url and self.turso_token:
            host = self.turso_url.split("://")[-1].split("/")[0]
            self.turso_http_endpoint = f"https://{host}/v2/pipeline"
            self.turso_session = requests.Session()
            self.turso_session.headers.update(
                {
                    "Authorization": f"Bearer {self.turso_token}",
                    "Content-Type": "application/json",
                }
            )

        self.retail_api_url = st.secrets.get("RETAIL_API_URL", "")

    # ---------- Trend Config ----------
    def _load_trend_config(self):
        try:
            if self.trend_config_file.exists():
                with open(self.trend_config_file, "r") as f:
                    config = json.load(f)
                    self.ma_periods = config.get("ma_periods", [20, 50, 100, 200])
        except:
            self.ma_periods = [20, 50, 100, 200]

    def _save_trend_config(self):
        try:
            with open(self.trend_config_file, "w") as f:
                json.dump({"ma_periods": self.ma_periods}, f, indent=4)
            return True
        except:
            return False

    def update_ma_periods(self, periods):
        self.ma_periods = periods
        self.trend_cache.clear()
        return self._save_trend_config()

    # ---------- Load all data ----------
    def load_data(self):
        self._load_cot_data()
        self._load_economic_indicators()
        self._load_retail_sentiment()
        self._load_bond_yield_scores()
        self._load_economic_strength()
        self.save_current_scores()
        self.save_asset_scores_to_turso()
        return True

    # ---------- COT via Turso HTTP API ----------
    def _load_cot_data(self):
        self.cot_current.clear()
        self.cot_prev.clear()
        self.cot_raw = []
        if not self.turso_session:
            return
        try:
            sql = "SELECT date, asset, class, long_pos, short_pos FROM cot_data ORDER BY date DESC"
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={"requests": [{"type": "execute", "stmt": {"sql": sql}}]},
            )
            resp.raise_for_status()
            data = resp.json()
            rows = []
            if data.get("results"):
                for result in data["results"]:
                    rows_result = (
                        result.get("response", {}).get("result", {}).get("rows")
                    )
                    if rows_result:
                        rows = rows_result
                        break
            if not rows:
                return

            def extract(cell):
                if isinstance(cell, dict):
                    return cell.get("value", "")
                return cell

            asset_data = {}
            for row in rows:
                if isinstance(row, dict):
                    date = extract(row["date"])
                    asset = extract(row["asset"])
                    cls = extract(row["class"])
                    lpos_raw = row["long_pos"]
                    spos_raw = row["short_pos"]
                else:
                    date = extract(row[0])
                    asset = extract(row[1])
                    cls = extract(row[2])
                    lpos_raw = row[3]
                    spos_raw = row[4]

                lpos = float(extract(lpos_raw))
                spos = float(extract(spos_raw))
                asset_data.setdefault(asset, []).append((date, cls, lpos, spos))

            for asset, records in asset_data.items():
                latest_date, cls, lpos, spos = records[0]
                total = lpos + spos
                long_pct = (lpos / total * 100) if total > 0 else 50.0
                self.cot_current[asset] = long_pct

                if len(records) > 1:
                    prev_date, _, plpos, pspos = records[1]
                    prev_total = plpos + pspos
                    prev_long_pct = (
                        (plpos / prev_total * 100) if prev_total > 0 else 50.0
                    )
                    self.cot_prev[asset] = prev_long_pct
                else:
                    self.cot_prev[asset] = long_pct

                self.cot_raw.append(
                    {
                        "asset": asset,
                        "class": cls,
                        "latest_date": latest_date,
                        "latest_long": lpos,
                        "latest_short": spos,
                        "latest_long_pct": long_pct,
                        "prev_long": records[1][2] if len(records) > 1 else lpos,
                        "prev_short": records[1][3] if len(records) > 1 else spos,
                        "prev_long_pct": (
                            prev_long_pct if len(records) > 1 else long_pct
                        ),
                    }
                )
        except Exception as e:
            st.error(f"Failed to load COT from Turso: {e}")

    def update_cot_record(self, asset, asset_class, date_str, long_pos, short_pos):
        if not self.turso_session:
            return False
        try:
            sql = (
                "INSERT OR REPLACE INTO cot_data (date, asset, class, long_pos, short_pos) "
                "VALUES (?, ?, ?, ?, ?)"
            )
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": sql,
                                "args": [
                                    {"type": "text", "value": date_str},
                                    {"type": "text", "value": asset},
                                    {"type": "text", "value": asset_class},
                                    {"type": "float", "value": long_pos},
                                    {"type": "float", "value": short_pos},
                                ],
                            },
                        }
                    ]
                },
            )
            resp.raise_for_status()
            self._load_cot_data()
            return True
        except Exception as e:
            st.error(f"COT insert failed: {e}")
            return False

    # ---------- Economic indicators ----------
    def _load_economic_indicators(self):
        resp = self.supabase.table("economic_indicators").select("*").execute()
        if len(resp.data) == 0:
            default_date = datetime.now().strftime("%Y-%m-%d")
            for curr in STANDARD_CURRENCIES:
                indicators = list(CORE_INDICATORS) + list(SCORING_ONLY_INDICATORS)
                if curr in EXTRA_INDICATORS:
                    indicators.extend(EXTRA_INDICATORS[curr])
                for ind in indicators:
                    self.update_currency_indicator(
                        currency_code=curr,
                        indicator_name=ind,
                        actual=0.0,
                        forecast=0.0,
                        date_str=default_date,
                        previous=0.0,
                    )
            resp = self.supabase.table("economic_indicators").select("*").execute()

        self.raw_data.clear()
        self.indicator_scores.clear()
        self.currency_scores.clear()
        self.currency_percentages.clear()

        for row in resp.data:
            curr = row["currency_code"]
            if curr not in self.raw_data:
                self.raw_data[curr] = {}
                self.indicator_scores[curr] = {}
            ind = row["indicator_name"]
            actual = (
                float(row["actual_value"]) if row["actual_value"] is not None else None
            )
            forecast = (
                float(row["forecast_value"])
                if row["forecast_value"] is not None
                else None
            )
            self.raw_data[curr][ind] = (
                actual,
                forecast,
                row["release_date"],
                (
                    float(row["previous_value"])
                    if row["previous_value"] is not None
                    else None
                ),
            )
            stored_score = row.get("score")
            direction = DIRECTION.get(ind, "higher")
            if actual is None or forecast is None:
                score = 0
            else:
                if direction == "higher":
                    correct_score = (
                        1 if actual > forecast else (-1 if actual < forecast else 0)
                    )
                else:
                    correct_score = (
                        1 if actual < forecast else (-1 if actual > forecast else 0)
                    )
                if stored_score is not None and stored_score == correct_score:
                    score = stored_score
                else:
                    score = correct_score
            self.indicator_scores[curr][ind] = score

        default_date = datetime.now().strftime("%Y-%m-%d")
        for curr in STANDARD_CURRENCIES:
            for ind in SCORING_ONLY_INDICATORS:
                if ind not in self.raw_data.get(curr, {}):
                    self.supabase.table("economic_indicators").upsert(
                        {
                            "currency_code": curr,
                            "indicator_name": ind,
                            "actual_value": 0.0,
                            "forecast_value": 0.0,
                            "release_date": default_date,
                            "previous_value": 0.0,
                            "score": 0,
                        },
                        on_conflict="currency_code,indicator_name",
                    ).execute()
                    if curr not in self.raw_data:
                        self.raw_data[curr] = {}
                        self.indicator_scores[curr] = {}
                    self.raw_data[curr][ind] = (0.0, 0.0, default_date, 0.0)
                    self.indicator_scores[curr][ind] = 0

        for curr in self.raw_data:
            indicators = list(CORE_INDICATORS) + list(SCORING_ONLY_INDICATORS)
            if curr in EXTRA_INDICATORS:
                indicators.extend(EXTRA_INDICATORS[curr])
            if curr in SCORING_EXCLUDED_INDICATORS:
                for excl in SCORING_EXCLUDED_INDICATORS[curr]:
                    if excl in indicators:
                        indicators.remove(excl)
            total_score = 0
            beats = 0
            surprises = 0
            for ind in indicators:
                if ind not in self.raw_data[curr]:
                    continue
                actual, forecast, _, _ = self.raw_data[curr][ind]
                if actual is None or forecast is None:
                    continue
                direction = DIRECTION.get(ind, "higher")
                score = self.indicator_scores[curr].get(ind, 0)
                total_score += score
                if actual != forecast:
                    surprises += 1
                    if (direction == "higher" and actual > forecast) or (
                        direction == "lower" and actual < forecast
                    ):
                        beats += 1
            self.currency_scores[curr] = total_score
            self.currency_percentages[curr] = (
                (beats / surprises * 100.0) if surprises > 0 else 0.0
            )

        self.currencies = self.currency_scores.copy()

    # ---------- RETAIL SENTIMENT (Auto‑refresh twice a day,  ----------

    def fetch_and_store_put_call_ratio(self, asset_name: str, ticker: str) -> float:
        """
        Scrape Barchart for the put/call ratio, store it in Turso, and return the ratio.
        Returns None if scraping fails.
        """
        if ticker not in barchart_url_map:
            return None

        target_url = barchart_url_map[ticker]
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(target_url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Try to find the ratio in column blocks
            for block in soup.find_all("div", class_="column"):
                block_text = block.get_text(separator=" ").strip()
                if "Put/Call Vol Ratio" in block_text:
                    match = re.search(r"Put/Call Vol Ratio\s*([0-9.]+)", block_text)
                    if match:
                        ratio = float(match.group(1))
                        # Store in Turso
                        today = datetime.now().strftime("%Y-%m-%d")
                        sql = """
                            INSERT OR REPLACE INTO put_call_history (ticker, date, ratio)
                            VALUES (?, ?, ?)
                        """
                        if self.turso_session:
                            self.turso_session.post(
                                self.turso_http_endpoint,
                                json={
                                    "requests": [
                                        {
                                            "type": "execute",
                                            "stmt": {
                                                "sql": sql,
                                                "args": [
                                                    {"type": "text", "value": ticker},
                                                    {"type": "text", "value": today},
                                                    {"type": "float", "value": ratio},
                                                ],
                                            },
                                        }
                                    ]
                                },
                            )
                        return ratio

            # Fallback: search entire page text
            page_text = soup.get_text(separator=" ")
            match = re.search(r"Put/Call Vol Ratio\s*([0-9.]+)", page_text)
            if match:
                ratio = float(match.group(1))
                # Store in Turso
                today = datetime.now().strftime("%Y-%m-%d")
                sql = """
                    INSERT OR REPLACE INTO put_call_history (ticker, date, ratio)
                    VALUES (?, ?, ?)
                """
                if self.turso_session:
                    self.turso_session.post(
                        self.turso_http_endpoint,
                        json={
                            "requests": [
                                {
                                    "type": "execute",
                                    "stmt": {
                                        "sql": sql,
                                        "args": [
                                            {"type": "text", "value": ticker},
                                            {"type": "text", "value": today},
                                            {"type": "float", "value": ratio},
                                        ],
                                    },
                                }
                            ]
                        },
                    )
                return ratio

            return None
        except Exception as e:
            st.error(f"Barchart scraping error for {asset_name}: {e}")
            return None

    def _get_latest_put_call_ratio(self, ticker: str):
        """Return the latest ratio from Turso for the given ticker, or None if no data."""
        if not self.turso_session:
            return None
        try:
            sql = "SELECT ratio FROM put_call_history WHERE ticker = ? ORDER BY date DESC LIMIT 1"
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": sql,
                                "args": [{"type": "text", "value": ticker}],
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
                if isinstance(cell, dict):
                    return cell.get("value", "")
                return cell

            # Iterate over rows (should be at most one)
            for row in rows:
                # row can be a list or a dict
                if isinstance(row, list):
                    # The ratio is the first (and only) column
                    ratio_val = extract(row[0])
                    if ratio_val != "":
                        return float(ratio_val)
                elif isinstance(row, dict):
                    # In case the row is a dict with key 'ratio'
                    ratio_val = extract(row.get("ratio"))
                    if ratio_val != "":
                        return float(ratio_val)
            return None
        except Exception as e:
            st.error(f"Error reading put/call ratio from Turso: {e}")
            return None

    def get_cached_put_call_ratio(self, ticker: str) -> float:
        """Return the latest ratio from DB, or None if not available."""
        if not self.turso_session:
            return None
        try:
            sql = "SELECT ratio FROM put_call_history WHERE ticker = ? ORDER BY date DESC LIMIT 1"
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": sql,
                                "args": [{"type": "text", "value": ticker}],
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
            if rows:
                if isinstance(rows[0], dict):
                    return float(rows[0]["ratio"])
                else:
                    return float(rows[0][1])
            return None
        except Exception:
            return None

    def _load_retail_sentiment(self):
        """
        Load retail sentiment from Supabase. For non‑forex assets (BTC, Gold, Silver, Nasdaq, S&P500, USDollar, USOil),
        override the score using the latest put‑call ratio from Turso.
        """
        self.retail_scores.clear()
        self.retail_long_pct.clear()

        # First load from Supabase as before (external API)
        try:
            resp = (
                self.supabase.table("retail_sentiment")
                .select("updated_at")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            data_stale = True
            if resp.data:
                last_updated_str = resp.data[0].get("updated_at")
                if last_updated_str:
                    last_updated = datetime.fromisoformat(
                        last_updated_str.replace("Z", "+00:00")
                    )
                    age_hours = (
                        datetime.now().astimezone() - last_updated
                    ).total_seconds() / 3600
                    if age_hours < 12:
                        data_stale = False
            if not data_stale:
                all_resp = self.supabase.table("retail_sentiment").select("*").execute()
                for row in all_resp.data:
                    pair = row["pair"]
                    self.retail_scores[pair] = row["retail_score"]
                    self.retail_long_pct[pair] = row["long_pct"]
            else:
                # Data stale, fetch from API
                self._refresh_retail_sentiment_from_api(show_message=False)
        except Exception as e:
            st.warning(f"Could not load retail sentiment from Supabase: {e}")

        for asset, cfg in pc_asset_map.items():
            ticker = cfg["ticker"]
            high_put = cfg["high_put"]
            high_call = cfg["high_call"]
            pc_ratio = self._get_latest_put_call_ratio(ticker)
            if pc_ratio is None:
                score = 0  # no data → neutral
            elif pc_ratio >= high_put:
                score = 2
            elif pc_ratio <= high_call:
                score = -2
            else:
                score = 0

            if asset == "USD":
                self.usd_pc_score = score
            else:
                target_pair = f"{asset}/USD"
                self.retail_scores[target_pair] = score
                # Ensure they don't show up with dummy data on the Retail page
                if target_pair in self.retail_long_pct:
                    del self.retail_long_pct[target_pair]

    def _refresh_retail_sentiment_from_api(self, show_message=False):
        """Fetch from external API and update Supabase.

        Args:
            show_message (bool): If True, display a success message (for manual refresh).
        """
        if not self.retail_api_url:
            st.error("RETAIL_API_URL not configured.")
            return

        try:
            response = requests.get(self.retail_api_url, timeout=10)
            response.raise_for_status()
            outer_data = response.json()
            inner_data = json.loads(outer_data["bodyMessage"])
            all_brokers_data = inner_data["response"]["brokerPairValueModels"]

            my_system_pairs = FOREX_PAIRS + ["ETH/USD"]
            api_to_system = {}
            for pair in my_system_pairs:
                api_to_system[pair.replace("/", "")] = pair

            # Find the "Average" broker (brokerId == "-1")
            for broker in all_brokers_data:
                if broker.get("brokerId") == "-1":
                    for pair_model in broker.get("pairValueModels", []):
                        api_name = pair_model["pairName"]
                        if api_name in api_to_system:
                            system_pair = api_to_system[api_name]
                            long_pct = float(pair_model["value"])
                            # Contrarian score
                            if long_pct <= 20:
                                score = 2
                            elif long_pct <= 40:
                                score = 1
                            elif long_pct >= 80:
                                score = -2
                            elif long_pct >= 60:
                                score = -1
                            else:
                                score = 0
                            # Upsert to Supabase (conflict on pair)
                            self.supabase.table("retail_sentiment").upsert(
                                {
                                    "pair": system_pair,
                                    "retail_score": score,
                                    "long_pct": long_pct,
                                    "updated_at": datetime.now().isoformat(),
                                },
                                on_conflict="pair",
                            ).execute()
                    break

            # Reload from Supabase into memory
            all_resp = self.supabase.table("retail_sentiment").select("*").execute()
            self.retail_scores.clear()
            self.retail_long_pct.clear()
            for row in all_resp.data:
                self.retail_scores[row["pair"]] = row["retail_score"]
                self.retail_long_pct[row["pair"]] = row["long_pct"]

            if show_message:
                st.success("Retail sentiment manually refreshed from API.")
        except Exception as e:
            st.error(f"Failed to refresh retail sentiment: {e}")

    def _load_bond_yield_scores(self):
        resp = self.supabase.table("bond_yield_scores").select("*").execute()
        self.bond_yield_scores.clear()
        for row in resp.data:
            curr = row["currency_code"]
            self.bond_yield_scores[curr] = (
                int(row["score"]) if row["score"] is not None else 0
            )

    def _load_economic_strength(self):
        resp = self.supabase.table("economic_strength").select("*").execute()
        self.economic_strength = {}
        for row in resp.data:
            self.economic_strength[row["currency_code"]] = row

    def update_economic_strength(self, currency_code, data_dict):
        currency_code = currency_code.upper()
        data_dict["currency_code"] = currency_code
        data_dict["updated_at"] = datetime.now().isoformat()
        try:
            self.supabase.table("economic_strength").upsert(
                data_dict, on_conflict="currency_code"
            ).execute()
            self._load_economic_strength()
            return True
        except Exception as e:
            st.error(f"Database error: {e}")
            return False

    def get_latest_indicator_value(self, currency_code, indicator_name):
        try:
            resp = (
                self.supabase.table("economic_indicators")
                .select("actual_value, release_date")
                .eq("currency_code", currency_code.upper())
                .eq("indicator_name", indicator_name)
                .order("release_date", desc=True)
                .limit(1)
                .execute()
            )
            if resp.data:
                return resp.data[0]["actual_value"], resp.data[0]["release_date"]
        except:
            pass
        return None, None

    def auto_fill_economic_strength(self, currency_code):
        currency_code = currency_code.upper()
        gdp, _ = self.get_latest_indicator_value(currency_code, "GDP")
        unemp, _ = self.get_latest_indicator_value(currency_code, "Unemployment Rate")
        cpi, _ = self.get_latest_indicator_value(currency_code, "CPI YoY")
        current = self.economic_strength.get(currency_code, {})
        int_rate = current.get("interest_rate", 0.0)
        real_yield = float(int_rate) - float(cpi if cpi is not None else 0.0)
        payload = {
            "gdp_growth": (
                float(gdp) if gdp is not None else current.get("gdp_growth", 0.0)
            ),
            "unemployment_rate": (
                float(unemp)
                if unemp is not None
                else current.get("unemployment_rate", 0.0)
            ),
            "cpi_yoy": float(cpi) if cpi is not None else current.get("cpi_yoy", 0.0),
            "interest_rate": int_rate,
            "real_yield": real_yield,
        }
        suggested_score = self.calculate_economic_strength_score(payload)
        payload["relative_strength_score"] = suggested_score
        payload["bias"] = (
            "Bullish"
            if suggested_score >= 60
            else "Bearish" if suggested_score <= 39 else "Neutral"
        )
        payload["delta_score"] = current.get("delta_score", 0)
        payload["delta_real_yield"] = current.get("delta_real_yield", 0.0)
        return payload

    def _calibrate_score_coefficients(self):
        ref_data = [
            [0.80, 4.30, 4.10, 3.70, 0.40, 64],
            [-0.20, 6.70, 2.25, 1.80, 0.45, 28],
            [0.20, 3.10, 0.00, 0.30, -0.30, 55],
            [0.20, 6.20, 2.15, 2.50, -0.35, 35],
            [0.10, 5.20, 3.75, 3.00, 0.75, 45],
            [0.30, 2.60, 0.75, 1.30, -0.55, 61],
            [0.20, 5.40, 2.25, 3.10, -0.85, 36],
            [0.50, 4.30, 3.75, 3.30, 0.45, 59],
        ]
        X, y = [], []
        for row in ref_data:
            gdp, unemp, rate, cpi, ry, score = row
            X.append([gdp, unemp, rate, cpi, ry, 1.0])
            y.append(score)
        try:
            import numpy as np

            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            self._score_coeffs = coeffs.tolist()
        except ImportError:
            self._score_coeffs = [14.573, -8.492, 6.131, -3.427, 8.971, 56.805]
        self._score_ranges = {
            "gdp": (-0.5, 1.0),
            "unemp": (2.0, 7.0),
            "rate": (0.0, 4.5),
            "cpi": (0.0, 4.0),
            "real_yield": (-1.0, 1.0),
        }

    def calculate_economic_strength_score(self, data):
        if not hasattr(self, "_score_coeffs"):
            self._calibrate_score_coefficients()
        gdp = data.get("gdp_growth", 0.0)
        unemp = data.get("unemployment_rate", 0.0)
        rate = data.get("interest_rate", 0.0)
        cpi = data.get("cpi_yoy", 0.0)
        real_yield = data.get("real_yield", 0.0)
        c = self._score_coeffs
        raw = (
            c[0] * gdp
            + c[1] * unemp
            + c[2] * rate
            + c[3] * cpi
            + c[4] * real_yield
            + c[5]
        )
        return int(round(max(0, min(100, raw))))

    # ---------- Update methods ----------
    def update_bond_yield_score(self, currency_code, score):
        currency_code = currency_code.upper()
        data = {
            "currency_code": currency_code,
            "score": score,
            "updated_at": datetime.now().isoformat(),
        }
        try:
            self.supabase.table("bond_yield_scores").upsert(
                data, on_conflict="currency_code"
            ).execute()
            self._load_bond_yield_scores()
            return True
        except Exception as e:
            st.error(f"Database error: {e}")
            return False

    def update_currency_indicator(
        self, currency_code, indicator_name, actual, forecast, date_str, previous
    ):
        currency_code = currency_code.upper()
        direction = DIRECTION.get(indicator_name, "higher")
        if actual is None or forecast is None:
            score = 0
        elif direction == "higher":
            score = 1 if actual > forecast else (-1 if actual < forecast else 0)
        else:
            score = 1 if actual < forecast else (-1 if actual > forecast else 0)

        data = {
            "currency_code": currency_code,
            "indicator_name": indicator_name,
            "actual_value": actual,
            "forecast_value": forecast,
            "release_date": date_str,
            "previous_value": previous,
            "score": score,
        }
        try:
            self.supabase.table("economic_indicators").upsert(
                data, on_conflict="currency_code,indicator_name"
            ).execute()
            self._load_economic_indicators()
            return True
        except Exception as e:
            st.error(f"Database error: {e}")
            return False

    # ---------- Web scraping for economic indicators ----------

    def _clean_value(self, val):
        """Remove units and commas, return cleaned number string."""
        if val in [None, "N/A", ""]:
            return None
        val_str = str(val)
        for char in ["%", "K", "M", "B", ","]:
            val_str = val_str.replace(char, "")
        try:
            return float(val_str)
        except:
            return None

    def _scrape_indicator_data(self, url):
        """
        Fetch and parse indicator data from Trading Economics or Investing.com.
        Returns a dict with keys: date, actual, previous, forecast, source
        source is 'primary', 'fallback', or None if failed.
        """
        if not url:
            return None
        try:
            # Try standard requests first
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
            )
            source = "primary"
            if response.status_code != 200:
                # Fallback to cloudscraper
                scraper = cloudscraper.create_scraper()
                response = scraper.get(
                    url,
                    headers=headers,
                    timeout=15,
                )
                source = "fallback"
            if response.status_code != 200:
                return None

            # Investing.com JSON API
            if "investing.com" in url:
                try:
                    data = response.json()
                    occurrences = data.get("occurrences", [])
                    if not occurrences:
                        return None
                    # Find latest occurrence with actual value
                    latest = None
                    for occ in occurrences:
                        if occ.get("actual") is not None:
                            latest = occ
                            break
                    if not latest:
                        latest = occurrences[0]
                    raw_time = latest.get("occurrence_time", "")
                    date_str = raw_time.split("T")[0] if "T" in raw_time else raw_time
                    actual = latest.get("actual")
                    prev = latest.get("previous")
                    forecast = latest.get("forecast")
                    return {
                        "date": date_str,
                        "actual": self._clean_value(actual),
                        "previous": self._clean_value(prev),
                        "forecast": self._clean_value(forecast),
                        "source": source,
                    }
                except:
                    pass

            # Trading Economics HTML table
            elif "tradingeconomics.com" in url:
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table", class_="table")
                if table:
                    rows = table.find_all("tr")
                    if len(rows) > 2:
                        cols = rows[2].find_all("td")
                        if len(cols) >= 7:
                            date = cols[0].text.strip()
                            actual = cols[4].text.strip()
                            prev = cols[5].text.strip()
                            forecast = cols[6].text.strip()
                            return {
                                "date": date,
                                "actual": self._clean_value(actual),
                                "previous": self._clean_value(prev),
                                "forecast": self._clean_value(forecast),
                                "source": source,
                            }
                        elif len(cols) >= 6:
                            date = cols[0].text.strip()
                            actual = cols[3].text.strip()
                            prev = cols[4].text.strip()
                            forecast = cols[5].text.strip()
                            return {
                                "date": date,
                                "actual": self._clean_value(actual),
                                "previous": self._clean_value(prev),
                                "forecast": self._clean_value(forecast),
                                "source": source,
                            }
            return None
        except Exception:
            return None

    def refresh_currency_indicators(self, currency_code, progress_callback=None):
        """
        Fetch all indicators for a currency from web sources and update Supabase.
        progress_callback(current, total) optional.
        Returns (updated_count, message_string)
        """
        currency_code = currency_code.upper()
        all_indicators = list(CORE_INDICATORS) + list(SCORING_ONLY_INDICATORS)
        if currency_code in EXTRA_INDICATORS:
            all_indicators.extend(EXTRA_INDICATORS[currency_code])
        if currency_code in SCORING_EXCLUDED_INDICATORS:
            for excl in SCORING_EXCLUDED_INDICATORS[currency_code]:
                if excl in all_indicators:
                    all_indicators.remove(excl)

        total = len(all_indicators)
        updated = 0
        failed = 0
        source_primary = 0
        source_fallback = 0
        failed_indicators = []

        for i, ind_name in enumerate(all_indicators):
            key = f"{currency_code} - {ind_name}"
            urls = ECON_SCRAPE_URLS.get(key, {})
            scraped = None
            source_used = None

            if urls.get("primary"):
                scraped = self._scrape_indicator_data(urls["primary"])
                if scraped:
                    source_used = scraped["source"]
            if not scraped and urls.get("fallback"):
                scraped = self._scrape_indicator_data(urls["fallback"])
                if scraped:
                    source_used = scraped["source"]

            if scraped:
                date_str = scraped["date"]
                actual = scraped["actual"]
                previous = scraped["previous"]
                forecast = scraped["forecast"]

                if forecast is None and previous is not None:
                    forecast = previous
                if actual is not None and forecast is not None:
                    self.update_currency_indicator(
                        currency_code, ind_name, actual, forecast, date_str, previous
                    )
                    updated += 1
                    if source_used == "primary":
                        source_primary += 1
                    elif source_used == "fallback":
                        source_fallback += 1
                else:
                    failed += 1
                    failed_indicators.append(ind_name)
            else:
                failed += 1
                failed_indicators.append(ind_name)

            if progress_callback:
                progress_callback(i + 1, total)

        # Build message
        msg_parts = []
        if updated > 0:
            msg_parts.append(f"✅ {updated} indicators updated")
            if source_primary > 0:
                msg_parts.append(f"   └ Primary sources: {source_primary}")
            if source_fallback > 0:
                msg_parts.append(f"   └ Fallback sources: {source_fallback}")
        if failed > 0:
            msg_parts.append(f"❌ {failed} indicators failed")
            if failed_indicators:
                msg_parts.append(
                    f"   └ Failed: {', '.join(failed_indicators[:5])}"
                    + (
                        f" (+{len(failed_indicators)-5} more)"
                        if len(failed_indicators) > 5
                        else ""
                    )
                )

        message = "\n".join(msg_parts) if msg_parts else "No indicators processed."
        return updated, message

    # -------------------------- COT fetching + Web Scraping from titanfx ----------

    def _fetch_cot_from_cot_reports(self):
        """
        Exact same logic as the original COT script.
        Returns (records, release_date) where records is list of (asset, class, long, short).
        """
        try:
            current_year = datetime.now().year

            # 1. Fetch current year's file using cot_reports
            df = cot_reports_lib.cot_year(
                year=current_year, cot_report_type="legacy_fut"
            )

            # 2. Strict Column Selection (exactly as in script)
            market_col = [c for c in df.columns if "market" in c.lower()][0]
            date_col = [c for c in df.columns if "yyyy" in c.lower()][0]
            long_col = [
                c
                for c in df.columns
                if "non" in c.lower() and "comm" in c.lower() and "long" in c.lower()
            ][0]
            short_col = [
                c
                for c in df.columns
                if "non" in c.lower() and "comm" in c.lower() and "short" in c.lower()
            ][0]

            # 3. Find most recent date and isolate that week's data
            df[date_col] = pd.to_datetime(df[date_col])
            latest_date = df[date_col].max()
            latest_df = df[df[date_col] == latest_date].copy()

            # 5. Calculate Release Date (Tuesday Report + 3 Days = Friday Release)
            release_date = latest_date + timedelta(days=3)
            release_date_str = release_date.strftime("%Y-%m-%d")

            # 6. Extract data for each market
            records = []
            for display_name, search_term in markets_to_track.items():
                market_row = latest_df[
                    latest_df[market_col].str.contains(
                        search_term, case=False, na=False
                    )
                ]
                if not market_row.empty:
                    long_pos = int(
                        pd.to_numeric(market_row[long_col].values[0], errors="coerce")
                        or 0
                    )
                    short_pos = int(
                        pd.to_numeric(market_row[short_col].values[0], errors="coerce")
                        or 0
                    )
                    asset, asset_class = asset_class_map[display_name]
                    records.append((asset, asset_class, long_pos, short_pos))

            return records, release_date_str

        except Exception as e:
            st.error(f"cot_reports failed: {e}")
            return None, None

    def refresh_cot_data_from_web(self, progress_callback=None):
        """
        Fetch COT data: primary source cot_reports, fallback TitanFX scraping.
        Updates Turso database only if the fetched date is newer than the latest stored date.
        """
        # Get latest date already in database (if any)
        latest_db_date = None
        if self.cot_raw:
            dates = [
                item.get("latest_date")
                for item in self.cot_raw
                if item.get("latest_date")
            ]
            if dates:
                latest_db_date = max(dates)

        # ---------- Primary: cot_reports ---
        if COT_AVAILABLE:
            try:
                st.info(
                    "📡 Fetching COT data from official CFTC source (cot_reports)..."
                )
                records, record_date = self._fetch_cot_from_cot_reports()
                if records and record_date:
                    # Check if we already have data for this date
                    if latest_db_date and record_date <= latest_db_date:
                        st.info(
                            f"✅ COT data already up to date (latest: {latest_db_date}). No update needed."
                        )
                        return 0
                    updated = 0
                    total = len(records)
                    for i, (asset, asset_class, long_pos, short_pos) in enumerate(
                        records
                    ):
                        if self.update_cot_record(
                            asset, asset_class, record_date, long_pos, short_pos
                        ):
                            updated += 1
                        if progress_callback:
                            progress_callback(i + 1, total)
                    st.success(
                        f"✅ COT data updated from CFTC. {updated} records for date {record_date}."
                    )
                    return updated
            except Exception as e:
                st.warning(f"cot_reports failed: {e}. Falling back to TitanFX.")

        # --- ------------ Fallback: TitanFX scraper ---
        st.info("📡 Using fallback COT source (TitanFX)...")
        try:
            response = requests.get(cot_url, headers=headers, timeout=15)
        except Exception:
            response = None

        if (
            response is None
            or response.status_code in [403, 503]
            or (response.text and "Just a moment" in response.text)
        ):
            scraper = cloudscraper.create_scraper()
            response = scraper.get(cot_url, headers=headers, timeout=15)

        if response.status_code != 200:
            st.error(f"Failed to fetch COT data. HTTP {response.status_code}")
            return 0

        html_text = response.text
        soup = BeautifulSoup(html_text, "lxml")

        # Extract report date and publish date (+3 days)
        report_date = "Date not found"
        publish_date = "Date not found"
        date_match = re.search(
            r"Data Update:\s*([A-Za-z]+\s\d{1,2},\s\d{4})", soup.get_text(separator=" ")
        )
        if date_match:
            report_date = date_match.group(1)
            try:
                parsed_date = datetime.strptime(report_date, "%B %d, %Y")
            except ValueError:
                try:
                    parsed_date = datetime.strptime(report_date, "%b %d, %Y")
                except ValueError:
                    parsed_date = None
            if parsed_date:
                new_date = parsed_date + timedelta(days=3)
                publish_date = new_date.strftime("%B %d, %Y")

        record_date = publish_date
        if record_date == "Date not found":
            record_date = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                dt = datetime.strptime(record_date, "%B %d, %Y")
                record_date = dt.strftime("%Y-%m-%d")
            except:
                record_date = datetime.now().strftime("%Y-%m-%d")

        # Check if already have this date
        if latest_db_date and record_date <= latest_db_date:
            st.info(
                f"✅ COT data already up to date (latest: {latest_db_date}). No update needed."
            )
            return 0

        # Parse asset cards
        assets = soup.find_all(
            "li",
            class_="block p-[15px] md:px-[30px] md:py-[20px] bg-white rounded-[10px] shadow-[0_0_8px_0_rgba(0,0,0,0.10)]",
        )
        scraped_records = []
        for asset in assets:
            try:
                name_elem = asset.find(
                    "a",
                    class_="block mb-[20px] text-[18px] md:text-[22px] font-bold underline hover:no-underline",
                )
                if not name_elem:
                    continue
                name = name_elem.text.strip()
                name_lower = name.lower()
                if any(excl in name_lower for excl in exclude_assets):
                    continue
                if not any(target in name_lower for target in target_assets):
                    continue
                ths = asset.find_all("th", class_="font-normal")
                if len(ths) >= 2:
                    long_str = ths[0].find_next_sibling("td").text.strip()
                    short_str = ths[1].find_next_sibling("td").text.strip()
                    long_val = float(long_str.replace(",", ""))
                    short_val = float(short_str.replace(",", ""))
                    mapped = None
                    for key, (sym, cls) in asset_mapping.items():
                        if key.lower() in name_lower:
                            mapped = (sym, cls)
                            break
                    if not mapped:
                        sym = name.split()[0].upper()
                        cls = "forex"
                        mapped = (sym, cls)
                    asset_sym, asset_class = mapped
                    scraped_records.append(
                        (asset_sym, asset_class, long_val, short_val)
                    )
            except Exception:
                continue

        if not scraped_records:
            st.warning("No COT data extracted from TitanFX.")
            return 0

        updated = 0
        total = len(scraped_records)
        for i, (asset_sym, asset_class, long_pos, short_pos) in enumerate(
            scraped_records
        ):
            if self.update_cot_record(
                asset_sym, asset_class, record_date, long_pos, short_pos
            ):
                updated += 1
            if progress_callback:
                progress_callback(i + 1, total)

        st.success(
            f"✅ COT data updated from TitanFX. {updated} records for date {record_date}."
        )
        return updated

    # -------------------------- Monthly Seasonality from Yahoo Finance ----------

    def _compute_monthly_seasonality(self, pair: str) -> dict:
        """Return dict {month_name: bias} where bias is 'Bullish', 'Bearish', or 'Neutral'."""
        import yfinance as yf

        symbol = get_yf_symbol(pair)
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="10y", interval="1d")
            if df.empty:
                return {
                    m: "Neutral"
                    for m in [
                        "Jan",
                        "Feb",
                        "Mar",
                        "Apr",
                        "May",
                        "Jun",
                        "Jul",
                        "Aug",
                        "Sep",
                        "Oct",
                        "Nov",
                        "Dec",
                    ]
                }
            # Resample to month-end
            monthly = df.resample("ME").agg({"Open": "first", "Close": "last"})
            monthly["Return"] = (
                (monthly["Close"] - monthly["Open"]) / monthly["Open"]
            ) * 100
            monthly["Month"] = monthly.index.month
            # Average return per month
            avg_returns = monthly.groupby("Month")["Return"].mean()
            result = {}
            for i, month in enumerate(month_names, 1):
                ret = avg_returns.get(i, 0.0)
                if ret > 0:
                    result[month] = "Bullish"
                elif ret < 0:
                    result[month] = "Bearish"
                else:
                    result[month] = "Neutral"
            return result
        except Exception:
            return {
                m: "Neutral"
                for m in [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ]
            }

    def update_sentiment_score_pair(self, pair, long_pct):
        # Kept for backward compatibility, but no longer used for manual updates.
        pair = normalize_pair(pair)
        if long_pct <= 20:
            score = 2
        elif long_pct <= 40:
            score = 1
        elif long_pct >= 80:
            score = -2
        elif long_pct >= 60:
            score = -1
        else:
            score = 0

        self.supabase.table("retail_sentiment").upsert(
            {
                "pair": pair.upper(),
                "retail_score": score,
                "long_pct": long_pct,
                "updated_at": datetime.now().isoformat(),
            }
        ).execute()
        self._load_retail_sentiment()
        return True

    # ---------- COT / Trend utilities ----------
    def get_net_position(self, long_pct):
        return long_pct - (100 - long_pct)

    def get_cot_score(self, base, quote):
        if base not in self.cot_current or quote not in self.cot_current:
            return None
        long_base = self.cot_current[base]
        long_quote = self.cot_current[quote]
        net_base = self.get_net_position(long_base)
        net_quote = self.get_net_position(long_quote)
        long_base_prev = self.cot_prev.get(base, 50.0)
        long_quote_prev = self.cot_prev.get(quote, 50.0)
        net_base_prev = self.get_net_position(long_base_prev)
        net_quote_prev = self.get_net_position(long_quote_prev)
        current_diff = net_base - net_quote
        prev_diff = net_base_prev - net_quote_prev
        net_change = current_diff - prev_diff
        sentiment = (
            "bullish"
            if net_change > 0.01
            else ("bearish" if net_change < -0.01 else "neutral")
        )
        position = (
            "bullish"
            if current_diff >= 20
            else ("bearish" if current_diff <= -20 else "neutral")
        )
        if sentiment == "bullish" and position == "bullish":
            return 2
        if sentiment == "bearish" and position == "bearish":
            return -2
        if sentiment == "bullish" and position == "neutral":
            return 1
        if sentiment == "bearish" and position == "neutral":
            return -1
        return 0

    def _fetch_trend_from_yfinance(self, pair):
        base, quote = pair.split("/")
        symbol = f"{base}{quote}=X"
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y", interval="1d")
            if df.empty:
                return "Unknown", 0, "No data from Yahoo Finance.", False
            close_prices = df["Close"]
            latest_close = close_prices.iloc[-1]
            ma_values = {}
            for period in self.ma_periods:
                if len(close_prices) >= period:
                    ma = close_prices.rolling(window=period).mean().iloc[-1]
                    ma_values[period] = ma
                else:
                    ma_values[period] = None
            if any(v is None for v in ma_values.values()):
                return "Unknown", 0, "Insufficient data for moving averages.", False
            below_count = sum(1 for ma in ma_values.values() if latest_close > ma)
            total = len(ma_values)
            raw_score = (below_count / total) * 4 - 2
            score = max(-2, min(2, round(raw_score)))
            if score >= 2:
                trend = "Up (strong)"
            elif score >= 1:
                trend = "Up (moderate)"
            elif score <= -2:
                trend = "Down (strong)"
            elif score <= -1:
                trend = "Down (moderate)"
            else:
                trend = "Sideways"
            ma_lines = [f"SMA{period}: {ma:.5f}" for period, ma in ma_values.items()]
            explanation = f"Price: {latest_close:.5f}\n" + "\n".join(ma_lines)
            explanation += f"\n\nPrice is above {below_count} out of {total} moving averages → trend score: {score} ({trend})."
            return trend, score, explanation, True
        except Exception as e:
            return "Error", 0, f"Yahoo Finance fallback failed: {str(e)}", False

    def fetch_trend_from_tradingview(self, pair, use_cache=True):
        if use_cache and pair in self.trend_cache:
            return self.trend_cache[pair]
        base, quote = pair.split("/")
        symbol = f"{base}{quote}"
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="forex",
                exchange="FX_IDC",
                interval=Interval.INTERVAL_1_DAY,
            )
            analysis = handler.get_analysis()
            indicators = analysis.indicators
            ma_values = {}
            for period in self.ma_periods:
                ma_key = f"SMA{period}"
                if ma_key in indicators:
                    ma_values[period] = indicators[ma_key]
                else:
                    ema_key = f"EMA{period}"
                    ma_values[period] = (
                        indicators[ema_key] if ema_key in indicators else None
                    )
            close = indicators.get("close", None)
            if close is None or any(v is None for v in ma_values.values()):
                result = self._fetch_trend_from_yfinance(pair)
            else:
                below_count = sum(1 for ma in ma_values.values() if close > ma)
                total = len(ma_values)
                raw_score = (below_count / total) * 4 - 2
                score = max(-2, min(2, round(raw_score)))
                if score >= 2:
                    trend = "Up (strong)"
                elif score >= 1:
                    trend = "Up (moderate)"
                elif score <= -2:
                    trend = "Down (strong)"
                elif score <= -1:
                    trend = "Down (moderate)"
                else:
                    trend = "Sideways"
                ma_lines = [
                    f"SMA{period}: {ma_values[period]:.5f}"
                    for period in self.ma_periods
                ]
                explanation = f"Price: {close:.5f}\n" + "\n".join(ma_lines)
                explanation += f"\n\nPrice is above {below_count} out of {total} moving averages → trend score: {score} ({trend})."
                result = (trend, score, explanation, True)
            self.trend_cache[pair] = result
            return result
        except Exception as e:
            result = self._fetch_trend_from_yfinance(pair)
            self.trend_cache[pair] = result
            return result

    def refresh_all_trends(self):
        progress_bar = st.progress(0, text="Refreshing trend data...")
        total = len(FOREX_PAIRS)
        for i, pair in enumerate(FOREX_PAIRS):
            self.fetch_trend_from_tradingview(pair, use_cache=False)
            progress_bar.progress((i + 1) / total)
        progress_bar.empty()
        return True

    def _get_metal_crypto_trend_score(self, base):
        mapping = {
            "XAU": ("XAUUSD", "OANDA", "GC=F"),
            "XAG": ("XAGUSD", "OANDA", "SI=F"),
            "BTC": ("BTCUSD", "COINBASE", "BTC-USD"),
            "ETH": ("ETHUSD", "COINBASE", "ETH-USD"),
            "USOIL": ("USOIL", "OANDA", "CL=F"),
            "SPX500": ("SPX500USD", "OANDA", "^GSPC"),
            "NAS100": ("NAS100USD", "OANDA", "^IXIC"),
        }
        if base not in mapping:
            return 0
        symbol, exchange, yf_symbol = mapping[base]
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="crypto" if base in ["BTC", "ETH"] else "forex",
                exchange=exchange,
                interval=Interval.INTERVAL_1_DAY,
            )
            analysis = handler.get_analysis()
            indicators = analysis.indicators
            ma_values = {}
            for period in self.ma_periods:
                ma_key = f"SMA{period}"
                ma_values[period] = indicators.get(ma_key) or indicators.get(
                    f"EMA{period}"
                )
            close = indicators.get("close")
            if close is None or any(v is None for v in ma_values.values()):
                raise Exception("Missing data from TradingView")
            below_count = sum(1 for ma in ma_values.values() if close > ma)
            total = len(ma_values)
            raw_score = (below_count / total) * 4 - 2
            score = max(-2, min(2, round(raw_score)))
            return score
        except:
            try:
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(period="1y", interval="1d")
                if df.empty:
                    return 0
                close_prices = df["Close"]
                latest_close = close_prices.iloc[-1]
                ma_values = {}
                for period in self.ma_periods:
                    if len(close_prices) >= period:
                        ma = close_prices.rolling(window=period).mean().iloc[-1]
                        ma_values[period] = ma
                below_count = sum(1 for ma in ma_values.values() if latest_close > ma)
                total = len(ma_values)
                raw_score = (below_count / total) * 4 - 2
                score = max(-2, min(2, round(raw_score)))
                return score
            except:
                return 0

    def _compute_nonforex_fund_score(self, base):
        if base not in ["XAU", "XAG", "BTC", "ETH", "USOIL", "SPX500", "NAS100"]:
            return None
        data = self.raw_data.get("USD", {})
        scores = self.indicator_scores.get("USD", {})
        is_metal = base in ["XAU", "XAG"]
        is_crypto = base in ["BTC", "ETH"]
        is_oil = base == "USOIL"
        is_index = base in ["SPX500", "NAS100"]
        invert_growth_jobs = is_metal
        invert_inflation = is_metal or is_crypto or is_oil or is_index

        def sum_cat(indicators, invert):
            total = 0
            for ind in indicators:
                if ind not in data:
                    continue
                actual, forecast, _, _ = data[ind]
                if actual is None or forecast is None:
                    continue
                s = scores.get(ind, 0)
                if invert:
                    s = -s
                total += s
            return total

        growth = sum_cat(GROWTH, invert_growth_jobs)
        jobs = sum_cat(JOBS, invert_growth_jobs)
        inflation = sum_cat(INFLATION, invert_inflation)
        bond = self.bond_yield_scores.get("USD", 0)
        if invert_growth_jobs:
            bond = -bond
        return growth + jobs + inflation + bond

    def get_enriched_pairs(self, include_currencies=False):
        pairs = []
        current_month = datetime.now().strftime("%b")
        
        for pair_str in ALL_PAIRS:
            base, quote = pair_str.split("/")
            is_nonforex = base in [
                "XAU",
                "XAG",
                "BTC",
                "ETH",
                "USOIL",
                "SPX500",
                "NAS100",
            ]
            if is_nonforex:
                fund_score = self._compute_nonforex_fund_score(base) or 0

                # COT score with BOTH net positioning and weekly change
                cot_score = 0
                if base in self.cot_current:
                    cur_long = self.cot_current[base]
                    cur_net = cur_long - (100 - cur_long)

                    # Net positioning score
                    if cur_net >= 60:
                        pos_score = 2
                    elif cur_net >= 20:
                        pos_score = 1
                    elif cur_net <= -60:
                        pos_score = -2
                    elif cur_net <= -20:
                        pos_score = -1
                    else:
                        pos_score = 0

                    # Weekly change score
                    change_score = 0
                    if base in self.cot_prev:
                        prev_long = self.cot_prev[base]
                        prev_net = prev_long - (100 - prev_long)
                        change = cur_net - prev_net
                        if change > 0:
                            change_score = 1
                        elif change < 0:
                            change_score = -1

                    cot_score = pos_score + change_score

                retail = self.retail_scores.get(pair_str, 0.0)
                trend_score = self._get_metal_crypto_trend_score(base)
                season_score = self.get_seasonality_score(pair_str, current_month)
            else:
                if (
                    base not in self.currency_scores
                    or quote not in self.currency_scores
                ):
                    continue
                fund_score = self.currency_scores[base] - self.currency_scores[quote]
                cot_score = self.get_cot_score(base, quote)
                retail = self.retail_scores.get(pair_str, 0.0)
                _, trend_score, _, _ = self.fetch_trend_from_tradingview(
                    pair_str, use_cache=True
                )
                season_score = self.get_seasonality_score(pair_str, current_month)

            pairs.append(
                (base, quote, fund_score, cot_score, retail, trend_score, season_score)
            )

        enriched = []
        for base, quote, fund, cot, retail, trend, season in pairs:
            scores = [s for s in (fund, cot, retail, trend, season) if s is not None]
            if len(scores) == 5:
                overall = sum(scores)
                if overall >= 9:
                    bias = "Very Bullish"
                elif overall >= 5:
                    bias = "Bullish"
                elif overall <= -9:
                    bias = "Very Bearish"
                elif overall <= -5:
                    bias = "Bearish"
                else:
                    bias = "Neutral"
            else:
                overall = None
                bias = None
            enriched.append(
                (base, quote, bias, overall, fund, cot, retail, trend, season)
            )

        if include_currencies:
            for curr in STANDARD_CURRENCIES:
                fund = self.currency_scores.get(curr, 0)

                # Individual currency COT with weekly change
                cot = 0
                if curr in self.cot_current:
                    cur_long = self.cot_current[curr]
                    cur_net = cur_long - (100 - cur_long)
                    if cur_net >= 60:
                        pos_score = 2
                    elif cur_net >= 20:
                        pos_score = 1
                    elif cur_net <= -60:
                        pos_score = -2
                    elif cur_net <= -20:
                        pos_score = -1
                    else:
                        pos_score = 0
                    change_score = 0
                    if curr in self.cot_prev:
                        prev_long = self.cot_prev[curr]
                        prev_net = prev_long - (100 - prev_long)
                        change = cur_net - prev_net
                        if change > 0:
                            change_score = 1
                        elif change < 0:
                            change_score = -1
                    cot = pos_score + change_score

                if curr == "USD" and hasattr(self, "usd_pc_score"):
                    retail = self.usd_pc_score
                else:
                    retail_scores_list = []
                    for pair_str in FOREX_PAIRS:
                        if curr not in pair_str:
                            continue
                        base_p, quote_p = pair_str.split("/")
                        sign = 1 if curr == base_p else -1
                        retail_scores_list.append(
                            sign * self.retail_scores.get(pair_str, 0.0)
                        )
                    retail = (
                        round(sum(retail_scores_list) / len(retail_scores_list))
                        if retail_scores_list
                        else 0.0
                    )

                trend_scores_list = []
                for pair_str in FOREX_PAIRS:
                    if curr not in pair_str:
                        continue
                    base_p, quote_p = pair_str.split("/")
                    sign = 1 if curr == base_p else -1
                    _, ps, _, _ = self.fetch_trend_from_tradingview(
                        pair_str, use_cache=True
                    )
                    trend_scores_list.append(sign * ps)
                trend = (
                    round(sum(trend_scores_list) / len(trend_scores_list))
                    if trend_scores_list
                    else 0.0
                )

                season_scores_list = []
                for pair_str in FOREX_PAIRS:
                    if curr not in pair_str:
                        continue
                    base_p, quote_p = pair_str.split("/")
                    sign = 1 if curr == base_p else -1
                    season_scores_list.append(
                        sign * self.get_seasonality_score(pair_str, current_month)
                    )
                season = (
                    round(sum(season_scores_list) / len(season_scores_list))
                    if season_scores_list
                    else 0.0
                )

                scores = [fund, cot, retail, trend, season]
                if all(s is not None for s in scores):
                    overall = sum(scores)
                    if overall >= 9:
                        bias = "Very Bullish"
                    elif overall >= 5:
                        bias = "Bullish"
                    elif overall <= -9:
                        bias = "Very Bearish"
                    elif overall <= -5:
                        bias = "Bearish"
                    else:
                        bias = "Neutral"
                else:
                    overall = None
                    bias = None

                enriched.append(
                    (curr, "", bias, overall, fund, cot, retail, trend, season)
                )
        return enriched

    def get_seasonality_score(self, pair: str, current_month: str) -> int:
        if pair not in self._seasonality_cache:
            self._seasonality_cache[pair] = self._compute_monthly_seasonality(pair)
        monthly_bias = self._seasonality_cache[pair].get(current_month, "Neutral")
        if monthly_bias == "Bullish":
            return 1
        elif monthly_bias == "Bearish":
            return -1
        else:
            return 0

    def save_current_scores(self):
        self.save_forex_scores_to_turso()
        self.save_asset_scores_to_turso()

    # ---------- Turso Asset Historical Scores ----------
    def save_asset_scores_to_turso(self):
        if not self.turso_session:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        all_items = self.get_enriched_pairs(include_currencies=True)

        for base, quote, bias, overall, *rest in all_items:
            if overall is None:
                continue
            if quote == "":
                asset_key = base
            else:
                if f"{base}/{quote}" in FOREX_PAIRS:
                    continue
                asset_key = f"{base}/{quote}"

            try:
                sql = (
                    "INSERT OR REPLACE INTO asset_historical_scores (date, asset, score) "
                    "VALUES (?, ?, ?)"
                )
                self.turso_session.post(
                    self.turso_http_endpoint,
                    json={
                        "requests": [
                            {
                                "type": "execute",
                                "stmt": {
                                    "sql": sql,
                                    "args": [
                                        {"type": "text", "value": today},
                                        {"type": "text", "value": asset_key},
                                        {"type": "float", "value": overall},
                                    ],
                                },
                            }
                        ]
                    },
                )
            except Exception:
                pass

    def get_asset_score_history(self, asset_key):
        if not self.turso_session:
            return []
        try:
            sql = "SELECT date, score FROM asset_historical_scores WHERE asset = ? ORDER BY date"
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": sql,
                                "args": [{"type": "text", "value": asset_key}],
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
                if isinstance(cell, dict):
                    return cell.get("value", "")
                return cell

            history = []
            for row in rows:
                date = extract(row[0])
                score = float(extract(row[1]))
                history.append((date, score))
            return history
        except Exception:
            return []

    # ---------- Turso pairs  Historical Scores ----------

    def save_forex_scores_to_turso(self):
        if not self.turso_session:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        enriched_pairs = self.get_enriched_pairs()  # only forex pairs
        for base, quote, bias, overall, *rest in enriched_pairs:
            if overall is None:
                continue
            pair = f"{base}/{quote}"
            sql = """
                INSERT OR REPLACE INTO forex_historical_scores (date, pair, score)
                VALUES (?, ?, ?)
            """
            try:
                self.turso_session.post(
                    self.turso_http_endpoint,
                    json={
                        "requests": [
                            {
                                "type": "execute",
                                "stmt": {
                                    "sql": sql,
                                    "args": [
                                        {"type": "text", "value": today},
                                        {"type": "text", "value": pair},
                                        {"type": "float", "value": overall},
                                    ],
                                },
                            }
                        ]
                    },
                )
            except Exception:
                pass

    def get_forex_score_history(self, pair):
        if not self.turso_session:
            return []
        sql = "SELECT date, score FROM forex_historical_scores WHERE pair = ? ORDER BY date"
        try:
            resp = self.turso_session.post(
                self.turso_http_endpoint,
                json={
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": sql,
                                "args": [{"type": "text", "value": pair}],
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
                if isinstance(cell, dict):
                    return cell.get("value", "")
                return cell

            history = []
            for row in rows:
                date = extract(row[0])
                score = float(extract(row[1]))
                history.append((date, score))
            return history
        except Exception as e:
            st.error(f"Error reading forex history from Turso: {e}")
            return []

# ======================= INITIALIZE ANALYZER =======================

@st.cache_resource
def init_analyzer():
    analyzer = CurrencyFundamentalAnalyzer(supabase_admin)
    analyzer.load_data()
    return analyzer


