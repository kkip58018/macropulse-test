from calendar import month_abbr




# ======================= CONSTANTS =======================
CORE_INDICATORS = [
    "GDP",
    "Retail Sales",
    "Manufacturing PMI",
    "Services PMI",
    "CPI YoY",
    "PPI YoY",
    "Unemployment Rate",
]

EXTRA_INDICATORS = {
    "USD": [
        "PCE YoY",
        "NFP",
        "Unemployment claims",
        "ADP",
        "JOLTS job openings",
        "Average Hourly Earnings",
    ],
    "JPY": ["Household spending"],
}
SCORING_ONLY_INDICATORS = ["Consumer Confidence"]
SCORING_EXCLUDED_INDICATORS = {"USD": ["Average Hourly Earnings"]}

DIRECTION = {
    "GDP": "higher",
    "Retail Sales": "higher",
    "Manufacturing PMI": "higher",
    "Services PMI": "higher",
    "CPI YoY": "higher",
    "PPI YoY": "higher",
    "Unemployment Rate": "lower",
    "PCE YoY": "higher",
    "NFP": "higher",
    "Unemployment claims": "lower",
    "ADP": "higher",
    "JOLTS job openings": "higher",
    "Average Hourly Earnings": "higher",
    "Household spending": "higher",
    "Consumer Confidence": "higher",
}

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }


# ======================= WEB SCRAPING URLS  =======================
ECON_SCRAPE_URLS = {
    # ==========================================
    # UNITED STATES (USD)
    # ==========================================
    "USD - GDP": {
        "primary": "https://tradingeconomics.com/united-states/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/375/occurrences?domain_id=1&limit=1000",
    },
    "USD - Retail Sales": {
        "primary": "https://tradingeconomics.com/united-states/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/256/occurrences?domain_id=1&limit=1000",
    },
    "USD - Manufacturing PMI": {
        "primary": "https://tradingeconomics.com/united-states/business-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/173/occurrences?domain_id=1&limit=1000",
    },
    "USD - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/176/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "USD - Consumer Confidence": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/48/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/united-states/consumer-confidence",
    },
    "USD - CPI YoY": {
        "primary": "https://tradingeconomics.com/united-states/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/733/occurrences?domain_id=1&limit=1000",
    },
    "USD - PPI YoY": {
        "primary": "https://tradingeconomics.com/united-states/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/734/occurrences?domain_id=1&limit=1000",
    },
    "USD - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/united-states/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/300/occurrences?domain_id=1&limit=1000",
    },
    "USD - PCE YoY": {
        "primary": "https://tradingeconomics.com/united-states/core-pce-price-index-annual-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/905/occurrences?domain_id=1&limit=1000",
    },
    "USD - NFP": {
        "primary": "https://tradingeconomics.com/united-states/non-farm-payrolls",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/227/occurrences?domain_id=1&limit=1000",
    },
    "USD - ADP": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/united-states/adp-employment-change",
    },
    "USD - Unemployment claims": {
        "primary": "https://tradingeconomics.com/united-states/jobless-claims",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/294/occurrences?domain_id=1&limit=1000",
    },
    "USD - JOLTS job openings": {
        "primary": "https://tradingeconomics.com/united-states/job-offers",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1057/occurrences?domain_id=1&limit=1000",
    },
    "USD - Average Hourly Earnings": {
        "primary": "https://tradingeconomics.com/united-states/average-hourly-earnings-yoy",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1777/occurrences?domain_id=1&limit=1000",
    },
    # ==========================================
    # EURO AREA (EUR)
    # ==========================================
    "EUR - GDP": {
        "primary": "https://tradingeconomics.com/euro-area/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/120/occurrences?domain_id=1&limit=1000",
    },
    "EUR - Retail Sales": {
        "primary": "https://tradingeconomics.com/euro-area/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/255/occurrences?domain_id=1&limit=1000",
    },
    "EUR - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/201/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "EUR - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/272/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "EUR - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/euro-area/consumer-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/49/occurrences?domain_id=1&limit=1000",
    },
    "EUR - CPI YoY": {
        "primary": "https://tradingeconomics.com/euro-area/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/68/occurrences?domain_id=1&limit=1000",
    },
    "EUR - PPI YoY": {
        "primary": "https://tradingeconomics.com/euro-area/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/935/occurrences?domain_id=1&limit=1000",
    },
    "EUR - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/euro-area/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/299/occurrences?domain_id=1&limit=1000eu",
    },
    # ==========================================
    # UNITED KINGDOM (GBP)
    # ==========================================
    "GBP - GDP": {
        "primary": "https://tradingeconomics.com/united-kingdom/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/121/occurrences?domain_id=1&limit=1000",
    },
    "GBP - Retail Sales": {
        "primary": "https://tradingeconomics.com/united-kingdom/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/258/occurrences?domain_id=1&limit=1000",
    },
    "GBP - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/204/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "GBP - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/274/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "GBP - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/united-kingdom/consumer-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/330/occurrences?domain_id=1&limit=1000",
    },
    "GBP - CPI YoY": {
        "primary": "https://tradingeconomics.com/united-kingdom/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/67/occurrences?domain_id=1&limit=1000",
    },
    "GBP - PPI YoY": {
        "primary": "https://tradingeconomics.com/united-kingdom/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/730/occurrences?domain_id=1&limit=1000",
    },
    "GBP - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/united-kingdom/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/297/occurrences?domain_id=1&limit=1000",
    },
    # ==========================================
    # AUSTRALIA (AUD)
    # ==========================================
    "AUD - GDP": {
        "primary": "https://tradingeconomics.com/australia/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/124/occurrences?domain_id=1&limit=1000",
    },
    "AUD - Retail Sales": {
        "primary": "https://tradingeconomics.com/australia/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/262/occurrences?domain_id=1&limit=1000",
    },
    "AUD - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1838/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "AUD - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1839/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "AUD - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/australia/consumer-confidence",
        "fallback": "",
    },
    "AUD - CPI YoY": {
        "primary": "https://tradingeconomics.com/australia/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1011/occurrences?domain_id=1&limit=1000",
    },
    "AUD - PPI YoY": {
        "primary": "https://tradingeconomics.com/australia/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1164/occurrences?domain_id=1&limit=1000",
    },
    "AUD - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/australia/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/302/occurrences?domain_id=1&limit=1000",
    },
    # ==========================================
    # CANADA (CAD)
    # ==========================================
    "CAD - GDP": {
        "primary": "https://tradingeconomics.com/canada/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1024/occurrences?domain_id=1&limit=1000",
    },
    "CAD - Retail Sales": {
        "primary": "https://tradingeconomics.com/canada/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/260/occurrences?domain_id=1&limit=1000",
    },
    "CAD - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1029/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "CAD - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/2265/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "CAD - Consumer Confidence": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/2068/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "CAD - CPI YoY": {
        "primary": "https://tradingeconomics.com/canada/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/741/occurrences?domain_id=1&limit=1000",
    },
    "CAD - PPI YoY": {
        "primary": "https://tradingeconomics.com/canada/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/742/occurrences?domain_id=1&limit=1000",
    },
    "CAD - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/canada/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/301/occurrences?domain_id=1&limit=1000",
    },
    # ==========================================
    # NEW ZEALAND (NZD)
    # ==========================================
    "NZD - GDP": {
        "primary": "https://tradingeconomics.com/new-zealand/gdp-growth",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/125/occurrences?domain_id=1&limit=1000",
    },
    "NZD - Retail Sales": {
        "primary": "https://tradingeconomics.com/new-zealand/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/257/occurrences?domain_id=1&limit=1000",
    },
    "NZD - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/338/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "NZD - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/910/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "NZD - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/new-zealand/consumer-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/357/occurrences?domain_id=1&limit=1000",
    },
    "NZD - CPI YoY": {
        "primary": "https://tradingeconomics.com/new-zealand/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1063/occurrences?domain_id=1&limit=1000",
    },
    "NZD - PPI YoY": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/247/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/new-zealand/producer-price-inflation-mom",
    },
    "NZD - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/new-zealand/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/295/occurrences?domain_id=1&limit=1000",
    },
    # ==========================================
    # SWISS FRANC (CHF)
    # ==========================================
    "CHF - GDP": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/122/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/switzerland/gdp-growth",
    },
    "CHF - Retail Sales": {
        "primary": "https://tradingeconomics.com/switzerland/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/259/occurrences?domain_id=1&limit=1000",
    },
    "CHF - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/278/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "CHF - Services PMI": {"primary": "", "fallback": ""},
    "CHF - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/switzerland/consumer-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/362/occurrences?domain_id=1&limit=1000",
    },
    "CHF - CPI YoY": {
        "primary": "https://tradingeconomics.com/switzerland/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/956/occurrences?domain_id=1&limit=1000",
    },
    "CHF - PPI YoY": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/960/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/switzerland/producer-prices-change",
    },
    "CHF - Unemployment Rate": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/959/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/switzerland/unemployment-rate",
    },
    # ==========================================
    # JAPAN (JPY)
    # ==========================================
    "JPY - GDP": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/119/occurrences?domain_id=1&limit=1000",
        "fallback": "https://tradingeconomics.com/japan/gdp-growth",
    },
    "JPY - Retail Sales": {
        "primary": "https://tradingeconomics.com/japan/retail-sales",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/190/occurrences?domain_id=1&limit=1000",
    },
    "JPY - Manufacturing PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/202/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "JPY - Services PMI": {
        "primary": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/1912/occurrences?domain_id=1&limit=1000",
        "fallback": "",
    },
    "JPY - Consumer Confidence": {
        "primary": "https://tradingeconomics.com/japan/consumer-confidence",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/148/occurrences?domain_id=1&limit=1000",
    },
    "JPY - CPI YoY": {
        "primary": "https://tradingeconomics.com/japan/inflation-cpi",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/992/occurrences?domain_id=1&limit=1000",
    },
    "JPY - PPI YoY": {
        "primary": "https://tradingeconomics.com/japan/producer-prices-change",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/35/occurrences?domain_id=1&limit=1000",
    },
    "JPY - Unemployment Rate": {
        "primary": "https://tradingeconomics.com/japan/unemployment-rate",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/298/occurrences?domain_id=1&limit=1000",
    },
    "JPY - Household spending": {
        "primary": "https://tradingeconomics.com/japan/household-spending",
        "fallback": "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/361/occurrences?domain_id=1&limit=1000",
    },
}

cot_url = "https://research.titanfx.com/cftc"
url_forexfactory = "https://www.forexfactory.com/calendar?week=this"

STANDARD_CURRENCIES = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"]
MONTHS = [month_abbr[i] for i in range(1, 13)]

FOREX_PAIRS = [
    "AUD/CAD",
    "AUD/CHF",
    "AUD/JPY",
    "AUD/NZD",
    "AUD/USD",
    "CAD/CHF",
    "CAD/JPY",
    "CHF/JPY",
    "EUR/AUD",
    "EUR/CAD",
    "EUR/CHF",
    "EUR/GBP",
    "EUR/JPY",
    "EUR/NZD",
    "EUR/USD",
    "GBP/AUD",
    "GBP/CAD",
    "GBP/CHF",
    "GBP/JPY",
    "GBP/NZD",
    "GBP/USD",
    "NZD/CAD",
    "NZD/CHF",
    "NZD/JPY",
    "NZD/USD",
    "USD/CAD",
    "USD/CHF",
    "USD/JPY",
]
ALL_PAIRS = FOREX_PAIRS + [
            "XAU/USD",
            "XAG/USD",
            "BTC/USD",
            "ETH/USD",
            "USOIL/USD",
            "SPX500/USD",
            "NAS100/USD",
        ]
INFLATION = ["CPI YoY", "PPI YoY", "PCE YoY"]
GROWTH = [
    "GDP",
    "Retail Sales",
    "Manufacturing PMI",
    "Services PMI",
    "Consumer Confidence",
]
JOBS = [
    "Unemployment Rate",
    "NFP",
    "Unemployment claims",
    "ADP",
    "JOLTS job openings",
]

# Barchart URL mapping
barchart_url_map = {
    "IBIT": "https://www.barchart.com/etfs-funds/quotes/IBIT/overview",
    "GLD": "https://www.barchart.com/etfs-funds/quotes/GLD/overview",
    "SLV": "https://www.barchart.com/etfs-funds/quotes/SLV/overview",
    "QQQ": "https://www.barchart.com/etfs-funds/quotes/QQQ/overview",
    "SPY": "https://www.barchart.com/etfs-funds/quotes/SPY/overview",
    "UUP": "https://www.barchart.com/etfs-funds/quotes/UUP/overview",
    "USO": "https://www.barchart.com/etfs-funds/quotes/USO/overview",
}

pc_asset_map = {
            "BTC": {"ticker": "IBIT", "high_put": 1.4, "high_call": 0.60},
            "XAU": {"ticker": "GLD", "high_put": 0.84, "high_call": 0.32},
            "XAG": {"ticker": "SLV", "high_put": 0.50, "high_call": 0.29},
            "NAS100": {"ticker": "QQQ", "high_put": 1.58, "high_call": 1.22},
            "SPX500": {"ticker": "SPY", "high_put": 1.35, "high_call": 0.95},
            "USD": {"ticker": "UUP", "high_put": 0.89, "high_call": 0.08},
            "USOIL": {"ticker": "USO", "high_put": 1.71, "high_call": 0.82},
        }

# 4. Map display names to CFTC keywords (exactly as script)
markets_to_track = {
    "Australian Dollar": "AUSTRALIAN DOLLAR",
    "Bitcoin": "BITCOIN",
    "British Pound": "BRITISH POUND",
    "Canadian Dollar": "CANADIAN DOLLAR",
    "Crude Oil WTI": "WTI-PHYSICAL",
    "Ethereum": "ETHER -",
    "Euro FX": "EURO FX",
    "Gold": "GOLD -",
    "Japanese Yen": "JAPANESE YEN",
    "Nasdaq 100": "NASDAQ MINI",
    "New Zealand Dollar": "NZ DOLLAR",
    "S&P 500": "S&P 500 Consolidated",
    "Silver": "SILVER -",
    "Swiss Franc": "SWISS FRANC",
    "US Dollar Index": "USD INDEX",
}

            # Map to your asset symbols and classes
asset_class_map = {
    "Australian Dollar": ("AUD", "forex"),
    "Bitcoin": ("BTC", "crypto"),
    "British Pound": ("GBP", "forex"),
    "Canadian Dollar": ("CAD", "forex"),
    "Crude Oil WTI": ("USOIL", "commodity"),
    "Ethereum": ("ETH", "crypto"),
    "Euro FX": ("EUR", "forex"),
    "Gold": ("XAU", "metal"),
    "Japanese Yen": ("JPY", "forex"),
    "Nasdaq 100": ("NAS100", "index"),
    "New Zealand Dollar": ("NZD", "forex"),
    "S&P 500": ("SPX500", "index"),
    "Silver": ("XAG", "metal"),
    "Swiss Franc": ("CHF", "forex"),
    "US Dollar Index": ("USD", "forex"),
}
target_assets = [
    "eur",
    "gbp",
    "jpy",
    "chf",
    "aud",
    "cad",
    "nzd",
    "usd",
    "dollar index",
    "bitcoin",
    "ethereum",
    "gold",
    "silver",
    "nasdaq",
    "s&p",
    "crude",
    "wti",
    "oil",
]
exclude_assets = ["mini", "micro"]
asset_mapping = {
    "EUR": ("EUR", "forex"),
    "Euro": ("EUR", "forex"),
    "GBP": ("GBP", "forex"),
    "JPY": ("JPY", "forex"),
    "CHF": ("CHF", "forex"),
    "AUD": ("AUD", "forex"),
    "CAD": ("CAD", "forex"),
    "NZD": ("NZD", "forex"),
    "USD": ("USD", "forex"),
    "Dollar Index": ("USD", "forex"),
    "Gold": ("XAU", "metal"),
    "Silver": ("XAG", "metal"),
    "Bitcoin": ("BTC", "crypto"),
    "Ethereum": ("ETH", "crypto"),
    "Nasdaq": ("NAS100", "index"),
    "S&P": ("SPX500", "index"),
    "Crude Oil WTI": ("USOIL", "commodity"),
    "WTI": ("USOIL", "commodity"),
    "Crude": ("USOIL", "commodity"),
}
month_names = [
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

asset_options = {
    "Bitcoin": {
        "ticker": "IBIT",
        "y_min": 0.1,
        "y_max": 1.5,
        "high_put": 1.4,
        "high_call": 0.6,
    },
    "Gold": {
        "ticker": "GLD",
        "y_min": 0.0,
        "y_max": 1.5,
        "high_put": 0.84,
        "high_call": 0.32,
    },
    "Silver": {
        "ticker": "SLV",
        "y_min": 0.0,
        "y_max": 1.0,
        "high_put": 0.50,
        "high_call": 0.29,
    },
    "Nasdaq": {
        "ticker": "QQQ",
        "y_min": 0.0,
        "y_max": 2.0,
        "high_put": 1.58,
        "high_call": 1.22,
    },
    "S&P500": {
        "ticker": "SPY",
        "y_min": 0.6,
        "y_max": 1.6,
        "high_put": 1.35,
        "high_call": 0.95,
    },
    "USDollar": {
        "ticker": "UUP",
        "y_min": 0.0,
        "y_max": 2.5,
        "high_put": 0.89,
        "high_call": 0.08,
    },
    "USOil": {
        "ticker": "USO",
        "y_min": 0.0,
        "y_max": 2.5,
        "high_put": 1.71,
        "high_call": 0.82,
    },
}