import streamlit as st
import pandas as pd
import cloudscraper
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
from analyzer import init_analyzer 
from config import *
from utils import get_kenyan_time_str
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

title_col, filter_col = st.columns([3, 1])

with title_col:
    st.header("📅 Economic Calendar")
# Initialize session state for calendar data
if "forexfactory_events" not in st.session_state:
    st.session_state.forexfactory_events = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None
# Helper function to scrape ForexFactory
def fetch_forexfactory_calendar():
    EXCLUDED_WORDS = [
        "german", "french", "italian", "spanish", "sppi", "tokyo",
        "Retail Sales Monitor", "Trimmed", "Weekly", "Core Retail Sales",
        "RatingDog", "Empire",
    ]
    try:
        response = requests.get(url_forexfactory, headers=headers, timeout=15)
        if response.status_code != 200:
            # Fallback to cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url_forexfactory, headers=headers, timeout=15)
        if response.status_code != 200:
            st.error(f"Failed to fetch calendar (HTTP {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="calendar__table")
        if not table:
            st.error("Could not find calendar table on ForexFactory")
            return None
        parsed = []
        current_date = "Unknown Date"
        excluded_lower = [w.lower() for w in EXCLUDED_WORDS]
        for row in table.find_all("tr", class_="calendar__row"):
            # --- NEW: Parse Date & Convert ET to Kenyan Time (EAT) ---
            date_cell = row.find("td", class_="calendar__date")
            if date_cell and date_cell.text.strip():
                raw_date = " ".join(date_cell.text.split())
                
                # Look for times like "8:30am" or "2:00pm" in the scraped string
                time_match = re.search(r'(\d{1,2}:\d{2})([a-p]m)', raw_date.lower())
                if time_match:
                    try:
                        time_str = time_match.group(0)
                        dt_obj = datetime.strptime(time_str, "%I:%M%p")
                        # ForexFactory defaults to US Eastern Time. EDT to EAT is +7 hours difference
                        dt_eat = dt_obj + timedelta(hours=7) 
                        eat_time_str = dt_eat.strftime("%I:%M %p")
                        
                        # Replace the US time with Kenyan time
                        current_date = raw_date.lower().replace(time_str, f"{eat_time_str} (EAT)").upper()
                    except:
                        current_date = raw_date
                else:
                    current_date = raw_date
            # ---------------------------------------------------------
            
            # Currency
            currency_cell = row.find("td", class_="calendar__currency")
            currency = currency_cell.text.strip() if currency_cell else ""
            # Event
            event_cell = row.find("td", class_="calendar__event")
            event_name = event_cell.text.strip() if event_cell else ""
            # Actual, Forecast, Previous
            actual_cell = row.find("td", class_="calendar__actual")
            actual = actual_cell.text.strip() if actual_cell else ""
            forecast_cell = row.find("td", class_="calendar__forecast")
            forecast = forecast_cell.text.strip() if forecast_cell else ""
            previous_cell = row.find("td", class_="calendar__previous")
            previous = previous_cell.text.strip() if previous_cell else ""
            if not currency or not event_name:
                continue
            event_lower = event_name.lower()
            currency_upper = currency.upper()
            # Exclude words
            if any(word in event_lower for word in excluded_lower):
                continue
            is_matched = False
            # Global keywords
            global_keywords = [
                "gdp", "retail sales", "manufacturing pmi", "services pmi",
                "cpi", "ppi", "unemployment rate", "employment change",
                "consumer confidence", "bank holiday",
            ]
            if any(kw in event_lower for kw in global_keywords):
                is_matched = True
            # USD only
            usd_keywords = [
                "pce", "non-farm employment change", "unemployment claims",
                "adp", "jolts job openings", "average hourly earnings",
                "federal funds rate", "fomc statement",
            ]
            if currency_upper == "USD" and any(kw in event_lower for kw in usd_keywords):
                is_matched = True
            # JPY only
            jpy_keywords = ["household spending", "boj policy rate"]
            if currency_upper == "JPY" and any(kw in event_lower for kw in jpy_keywords):
                is_matched = True
            # AUD only
            aud_keywords = ["cash rate", "rba rate statement"]
            if currency_upper == "AUD" and any(kw in event_lower for kw in aud_keywords):
                is_matched = True
            # NZD only
            nzd_keywords = [
                "manufacturing index", "services index",
                "official cash rate", "rbnz rate statement",
            ]
            if currency_upper == "NZD" and any(kw in event_lower for kw in nzd_keywords):
                is_matched = True
            # CAD only
            cad_keywords = ["overnight rate", "boc rate statement"]
            if currency_upper == "CAD" and any(kw in event_lower for kw in cad_keywords):
                is_matched = True
            # GBP only
            gbp_keywords = ["official bank rate", "boe monetary policy report"]
            if currency_upper == "GBP" and any(kw in event_lower for kw in gbp_keywords):
                is_matched = True
            # EUR only
            eur_keywords = ["main refinancing rate", "monetary policy statement"]
            if currency_upper == "EUR" and any(kw in event_lower for kw in eur_keywords):
                is_matched = True
            if is_matched:
                parsed.append(
                    {
                        "Date/Time": current_date, # Updated header for clarity
                        "Currency": currency_upper,
                        "Event": event_name,
                        "Actual": actual,
                        "Forecast": forecast,
                        "Previous": previous,
                    }
                )
        return parsed
    except Exception as e:
        st.error(f"Error scraping ForexFactory: {e}")
        return None

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Upcoming economic events**")
with col2:
    if st.button("🔄 Refresh Calendar", use_container_width=True):
        with st.spinner("Fetching latest data from ForexFactory..."):
            events = fetch_forexfactory_calendar()
            if events:
                st.session_state.forexfactory_events = events
                st.session_state.last_update = get_kenyan_time_str()
                st.success(f"Calendar updated at {st.session_state.last_update}")
            else:
                st.error("Failed to update calendar. Using cached data if available.")
        st.rerun()
# Load data if needed
if st.session_state.forexfactory_events is None:
    with st.spinner("Loading economic calendar from ForexFactory..."):
        events = fetch_forexfactory_calendar()
        if events:
            st.session_state.forexfactory_events = events
            st.session_state.last_update = get_kenyan_time_str()
        else:
            st.error("Could not load calendar data. Please try again later.")
            st.stop()
# Display the calendar
events = st.session_state.forexfactory_events
if events:
    df = pd.DataFrame(events)
    df = df[["Date/Time", "Currency", "Event", "Actual", "Forecast", "Previous"]]
    
    # --- POPULATE THE TOP-RIGHT DROPDOWN ---
    unique_currencies = sorted(df["Currency"].dropna().unique().tolist())
    dropdown_options = ["All"] + unique_currencies
    
    with filter_col:
        selected_currency = st.selectbox(
            "Filter by Currency",
            options=dropdown_options,
            index=0,
            label_visibility="collapsed",
            help="Select a single currency or 'All' to see all events."
        )
    
    if selected_currency != "All":
        df = df[df["Currency"] == selected_currency]
    # ---------------------------------------
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No events found for currency: {selected_currency}")
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update}")
else:
    st.info("No events match the selected filters.")
