from pathlib import Path
from io import BytesIO
import pandas as pd
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Top Gainers Intelligence", page_icon="📈", layout="wide")

# ---- Visual styling ----
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px;}
.hero {
  padding: 1.35rem 1.55rem; border-radius: 18px;
  background: linear-gradient(115deg, #10243A 0%, #1D4965 55%, #267B78 100%);
  color: white; margin-bottom: 1.1rem;
}
.hero h1 {color: white; margin: 0 0 .35rem 0; font-size: 2rem;}
.hero p {color: #DCEAF2; margin: 0; font-size: 1rem;}
.kpi {
  padding: 1rem 1.1rem; border-radius: 14px;
  border: 1px solid rgba(120,140,160,.25); background: rgba(120,140,160,.06);
}
.kpi-label {font-size: .82rem; opacity: .72; margin-bottom: .25rem;}
.kpi-value {font-size: 1.65rem; font-weight: 750; line-height: 1.2;}
.stock-card {
  border: 1px solid rgba(120,140,160,.28); border-radius: 16px;
  padding: 1rem 1.1rem; margin: .35rem 0 .8rem 0;
  background: rgba(120,140,160,.035);
}
.stock-head {display:flex; align-items:center; gap:.65rem; flex-wrap:wrap;}
.stock-name {font-size:1.1rem; font-weight:750;}
.pill {
  display:inline-block; border-radius:999px; padding:.22rem .62rem;
  font-size:.75rem; background:rgba(38,123,120,.13); color:inherit;
}
.small-muted {opacity:.68; font-size:.82rem;}
div[data-testid="stButton"] button {border-radius: 9px; min-height: 2.3rem;}
div[data-testid="stButton"] button[kind="primary"] {font-weight:700;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>📈 Top Gainers Intelligence</h1>
  <p>Explore recurring stocks, inspect every recorded occurrence, and click a date to view its historical price change.</p>
</div>
""", unsafe_allow_html=True)

st.info(
    "**How percentage change is calculated:** Daily change = (selected date close − previous trading-day close) ÷ "
    "previous trading-day close × 100. Intraday change = (selected date close − selected date open) ÷ open × 100. "
    "SVG timeline dates are preferred for occurrence display and OHLC lookup when the audit file is available; CSV dates are fallback only."
)

st.sidebar.header("📂 Data source")
uploaded = st.sidebar.file_uploader("Upload Backtest Top Gainers.csv", type=["csv"])
svg_audit_upload = st.sidebar.file_uploader("Optional: upload SVG audit CSV", type=["csv"], key="audit_csv")
APP_DIR = Path(__file__).resolve().parent
default_path = APP_DIR / "Backtest Top Gainers.csv"

@st.cache_data
def parse_csv(file_bytes=None, path_str=None):
    if file_bytes is not None:
        raw = pd.read_csv(BytesIO(file_bytes))
    else:
        raw = pd.read_csv(path_str)
    required = {"Date", "Symbol", "Marketcapname", "Sector"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = raw.copy()
    df["OriginalDate"] = df["Date"].astype(str).str.strip()
    parsed = pd.to_datetime(df["OriginalDate"], format="%d-%m-%Y %I:%M %p", errors="coerce")
    bad = parsed.isna()
    if bad.any():
        parsed.loc[bad] = pd.to_datetime(df.loc[bad, "OriginalDate"], errors="coerce", dayfirst=True)
    df["DateTime"] = parsed
    df["DateOnly"] = df["DateTime"].dt.date
    df["DateISO"] = df["DateTime"].dt.strftime("%Y-%m-%d")
    df["TimeLabel"] = df["DateTime"].dt.strftime("%I:%M %p")
    df["Symbol"] = df["Symbol"].astype("string").str.strip().str.upper()
    df["Marketcapname"] = df["Marketcapname"].astype("string").str.strip()
    df["Sector"] = df["Sector"].astype("string").str.strip()
    return raw, df

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_occurrence_percentages(symbol, date_isos):
    """Get close-to-close daily % changes for many occurrence dates in one download."""
    import yfinance as yf

    requested = sorted({pd.Timestamp(d).normalize() for d in date_isos})
    if not requested:
        return {}

    start = (min(requested) - pd.Timedelta(days=20)).date().isoformat()
    end = (max(requested) + pd.Timedelta(days=3)).date().isoformat()

    for suffix in [".NS", ".BO"]:
        ticker = f"{symbol}{suffix}"
        try:
            prices = yf.download(
                ticker, start=start, end=end, interval="1d",
                auto_adjust=False, progress=False, threads=False
            )
            if prices is None or prices.empty:
                continue
            if isinstance(prices.columns, pd.MultiIndex):
                prices.columns = prices.columns.get_level_values(0)
            prices = prices.reset_index()
            date_col = "Date" if "Date" in prices.columns else prices.columns[0]
            prices[date_col] = pd.to_datetime(prices[date_col]).dt.tz_localize(None).dt.normalize()
            prices = prices.sort_values(date_col).drop_duplicates(date_col).reset_index(drop=True)
            prices["Close"] = pd.to_numeric(prices["Close"], errors="coerce")
            prices["DailyChangePct"] = prices["Close"].pct_change() * 100

            result = {}
            for date in requested:
                matched = prices.index[prices[date_col] == date]
                value = prices.loc[int(matched[0]), "DailyChangePct"] if len(matched) else np.nan
                result[date.strftime("%Y-%m-%d")] = float(value) if pd.notna(value) else None
            return result
        except Exception:
            continue

    return {date.strftime("%Y-%m-%d"): None for date in requested}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_daily_prices(symbol, date_iso):
    import yfinance as yf
    event_date = pd.Timestamp(date_iso).normalize()
    start = (event_date - pd.Timedelta(days=14)).date().isoformat()
    end = (event_date + pd.Timedelta(days=4)).date().isoformat()
    errors = []
    for suffix in [".NS", ".BO"]:
        ticker = f"{symbol}{suffix}"
        try:
            prices = yf.download(ticker, start=start, end=end, interval="1d",
                                 auto_adjust=False, progress=False, threads=False)
            if prices is None or prices.empty:
                errors.append(f"No data for {ticker}")
                continue
            if isinstance(prices.columns, pd.MultiIndex):
                prices.columns = prices.columns.get_level_values(0)
            prices = prices.reset_index()
            date_col = "Date" if "Date" in prices.columns else prices.columns[0]
            prices[date_col] = pd.to_datetime(prices[date_col]).dt.tz_localize(None).dt.normalize()
            prices = prices.sort_values(date_col).drop_duplicates(date_col).reset_index(drop=True)
            matches = prices.index[prices[date_col] == event_date]
            if len(matches) == 0:
                errors.append(f"{ticker}: no daily candle for {event_date.date()}")
                continue
            pos = int(matches[0])
            row = prices.iloc[pos]
            prev_row = prices.iloc[pos - 1] if pos > 0 else None
            prev_open = pd.to_numeric(prev_row.get("Open"), errors="coerce") if prev_row is not None else np.nan
            prev_high = pd.to_numeric(prev_row.get("High"), errors="coerce") if prev_row is not None else np.nan
            prev_low = pd.to_numeric(prev_row.get("Low"), errors="coerce") if prev_row is not None else np.nan
            prev_close = pd.to_numeric(prev_row.get("Close"), errors="coerce") if prev_row is not None else np.nan
            prev_volume = pd.to_numeric(prev_row.get("Volume"), errors="coerce") if prev_row is not None else np.nan

            open_price = pd.to_numeric(row.get("Open"), errors="coerce")
            high_price = pd.to_numeric(row.get("High"), errors="coerce")
            low_price = pd.to_numeric(row.get("Low"), errors="coerce")
            close_price = pd.to_numeric(row.get("Close"), errors="coerce")

            # Main daily % change is close-to-close vs the previous trading session.
            daily_pct = ((close_price - prev_close) / prev_close * 100) if pd.notna(prev_close) and prev_close else np.nan
            intraday_pct = ((close_price - open_price) / open_price * 100) if pd.notna(open_price) and open_price else np.nan
            return {
                "ticker": ticker, "date": event_date.date().isoformat(),
                "open": open_price, "high": high_price, "low": low_price, "close": close_price,
                "previous_date": pd.Timestamp(prev_row[date_col]).date().isoformat() if prev_row is not None else None,
                "previous_open": prev_open, "previous_high": prev_high, "previous_low": prev_low,
                "previous_close": prev_close, "previous_volume": prev_volume,
                "daily_pct": daily_pct, "intraday_pct": intraday_pct,
                "volume": pd.to_numeric(row.get("Volume"), errors="coerce"),
                "history": prices[[date_col, "Close", "Volume"]].rename(
                    columns={date_col: "Date"}
                ).assign(Date=lambda x: pd.to_datetime(x["Date"]).dt.strftime("%d %b %Y")),
                "error": None
            }
        except Exception as exc:
            errors.append(f"{ticker}: {exc}")
    return {"error": "Price history unavailable. " + " | ".join(errors)}

try:
    if uploaded is not None:
        raw, df = parse_csv(file_bytes=uploaded.getvalue())
    elif default_path.exists():
        raw, df = parse_csv(path_str=str(default_path))
        st.sidebar.success("CSV loaded from the app folder.")
    else:
        st.warning("Upload your `Backtest Top Gainers.csv` using the sidebar to begin.")
        st.stop()
except Exception as exc:
    st.error(f"Could not load CSV: {exc}")
    st.stop()

if df["DateTime"].notna().sum() == 0:
    st.error("No dates could be parsed. Please check the Date column.")
    st.stop()


# Optional occurrence verification against the audit extracted from the SVG timeline.
# Expected audit columns: Symbol, CSV_Occurrences, SVG_Occurrences, Occurrence_Count_Match, CSV_Dates, SVG_Timeline_Dates.
audit_df = None
audit_path = APP_DIR / "Backtest_Top_Gainers_CSV_vs_SVG_Audit.csv"
try:
    if svg_audit_upload is not None:
        audit_df = pd.read_csv(svg_audit_upload)
    elif audit_path.exists():
        audit_df = pd.read_csv(audit_path)
except Exception as exc:
    st.sidebar.warning(f"Could not load SVG audit: {exc}")

# Prefer SVG timeline dates when the audit file is available.
df["OccurrenceDateTime"] = df["DateTime"]
df["OccurrenceDate"] = df["DateOnly"]
df["OccurrenceDateSource"] = "CSV fallback"

if audit_df is not None and {"Symbol", "SVG_Timeline_Dates"}.issubset(audit_df.columns):
    svg_date_map = {}
    for _, audit_row in audit_df.iterrows():
        sym_key = str(audit_row["Symbol"]).strip().upper()
        raw_dates = str(audit_row.get("SVG_Timeline_Dates", "")).strip()
        parsed_svg_dates = []
        if raw_dates and raw_dates.lower() != "nan":
            for date_part in raw_dates.split(" | "):
                try:
                    parsed_svg_dates.append(pd.to_datetime(date_part.strip(), format="%d-%b-%Y", errors="raise"))
                except Exception:
                    try:
                        parsed_svg_dates.append(pd.to_datetime(date_part.strip(), dayfirst=True, errors="raise"))
                    except Exception:
                        pass
        svg_date_map[sym_key] = parsed_svg_dates

    for sym_key, group in df.dropna(subset=["DateTime"]).groupby("Symbol", sort=False):
        ordered_indices = group.sort_values("DateTime").index.tolist()
        svg_dates_for_stock = svg_date_map.get(str(sym_key).upper(), [])
        if len(svg_dates_for_stock) == len(ordered_indices):
            for idx, svg_dt in zip(ordered_indices, svg_dates_for_stock):
                original_time = df.at[idx, "DateTime"]
                df.at[idx, "OccurrenceDateTime"] = pd.Timestamp(svg_dt).replace(
                    hour=original_time.hour, minute=original_time.minute
                )
                df.at[idx, "OccurrenceDate"] = pd.Timestamp(svg_dt).date()
                df.at[idx, "OccurrenceDateSource"] = "SVG timeline"
        elif svg_dates_for_stock:
            # SVG is authoritative; do not show CSV dates as if they were SVG dates.
            for idx in ordered_indices:
                df.at[idx, "OccurrenceDateTime"] = pd.NaT
                df.at[idx, "OccurrenceDate"] = pd.NaT
                df.at[idx, "OccurrenceDateSource"] = "SVG count mismatch"

if audit_df is None:
    st.error(
        "SVG audit file not loaded. SVG dates are the final source of truth. Upload "
        "`Backtest_Top_Gainers_CSV_vs_SVG_Audit.csv` in the sidebar or place it beside app.py."
    )
else:
    st.success("SVG timeline dates are active and are used as the final occurrence dates.")

valid_dates = df["OccurrenceDateTime"].dropna()
date_min, date_max = valid_dates.min().date(), valid_dates.max().date()

st.sidebar.header("🔎 Filters")
date_range = st.sidebar.date_input("Occurrence date range", value=(date_min, date_max),
                                   min_value=date_min, max_value=date_max)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    date_start, date_end = date_range
else:
    date_start, date_end = date_min, date_max

sector_options = ["All sectors"] + sorted(df["Sector"].dropna().unique().tolist())
cap_options = ["All market caps"] + sorted(df["Marketcapname"].dropna().unique().tolist())
sector_filter = st.sidebar.selectbox("Sector", sector_options)
cap_filter = st.sidebar.selectbox("Market cap", cap_options)
search = st.sidebar.text_input("Search stock symbol", placeholder="e.g. ATHERENERG").strip().upper()

filtered = df.dropna(subset=["OccurrenceDateTime"]).copy()
filtered = filtered[(filtered["OccurrenceDate"] >= date_start) & (filtered["OccurrenceDate"] <= date_end)]
if sector_filter != "All sectors":
    filtered = filtered[filtered["Sector"] == sector_filter]
if cap_filter != "All market caps":
    filtered = filtered[filtered["Marketcapname"] == cap_filter]
if search:
    filtered = filtered[filtered["Symbol"].str.contains(search, na=False)]

if filtered.empty:
    st.warning("No occurrences match the selected filters.")
    st.stop()


with st.expander("🔎 Verify CSV occurrences against SVG timeline audit", expanded=False):
    if audit_df is None:
        st.info(
            "Optional audit not loaded. To cross-check stock counts against the attached SVG timeline, "
            "place `Backtest_Top_Gainers_CSV_vs_SVG_Audit.csv` beside app.py or upload it in the sidebar."
        )
    elif "Symbol" not in audit_df.columns or "CSV_Occurrences" not in audit_df.columns or "SVG_Occurrences" not in audit_df.columns:
        st.warning("The audit file does not contain the expected columns.")
    else:
        audit_view = audit_df.copy()
        audit_view["Symbol"] = audit_view["Symbol"].astype(str).str.strip().str.upper()
        filtered_counts = filtered["Symbol"].value_counts().rename_axis("Symbol").reset_index(name="Current_CSV_Occurrences")
        audit_view = audit_view.merge(filtered_counts, on="Symbol", how="left")
        audit_view["Current_CSV_Occurrences"] = audit_view["Current_CSV_Occurrences"].fillna(0).astype(int)
        audit_view["CSV_vs_SVG_Count_Match"] = audit_view["CSV_Occurrences"].astype(int) == audit_view["SVG_Occurrences"].astype(int)
        audit_view["SVG_Dates_Match_CSV_Plus_1_Day"] = audit_view.get(
            "SVG_Dates_Match_CSV_Plus_1_Day", pd.Series(False, index=audit_view.index)
        )
        matching = int(audit_view["CSV_vs_SVG_Count_Match"].sum())
        total_audit = len(audit_view)
        st.metric("Stocks with matching total counts", f"{matching} / {total_audit}")
        st.caption(
            "SVG timeline dates are preferred for filtering, display, and OHLC lookup. The recorded time is retained from the CSV. "
            "If a stock's SVG and CSV occurrence counts do not align, the app flags the mismatch instead of silently substituting CSV dates."
        )
        st.dataframe(
            audit_view[[
                col for col in [
                    "Symbol", "CSV_Occurrences", "SVG_Occurrences", "CSV_vs_SVG_Count_Match",
                    "SVG_Dates_Match_CSV_Plus_1_Day", "Current_CSV_Occurrences", "CSV_Dates", "SVG_Timeline_Dates"
                ] if col in audit_view.columns
            ]],
            use_container_width=True, hide_index=True
        )

# Keep selected occurrence through reruns; date buttons act as clickable hyperlinks.
if "selected_occurrence" not in st.session_state:
    st.session_state.selected_occurrence = None
if "show_price_dialog" not in st.session_state:
    st.session_state.show_price_dialog = False

# ---- Refined stock analytics layout ----
total_occ = len(filtered)
unique_stocks = filtered["Symbol"].nunique()
unique_days = filtered["OccurrenceDate"].nunique()

st.markdown("""
<style>
.block-container {max-width: 1720px; padding-top: 1rem; padding-bottom: 2rem;}
.top-header {
  display:flex; align-items:center; justify-content:space-between; gap:18px;
  padding:20px 22px; border:1px solid #D9E3EF; border-radius:18px;
  background:linear-gradient(115deg,#FFFFFF 0%,#F5F9FF 100%);
  box-shadow:0 4px 18px rgba(25,55,90,.05); margin:8px 0 18px 0;
}
.stock-identity {display:flex; align-items:center; gap:14px; min-width:230px;}
.stock-mark {width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;
  background:#E3F4EA;color:#16804A;font-size:25px;}
.stock-title {font-size:25px;font-weight:800;color:#142A49;line-height:1.2;}
.stock-subtitle {font-size:13px;color:#6D7D91;margin-top:5px;}
.occ-kpi {min-width:155px;padding:12px 20px;text-align:center;border-radius:14px;
  background:#FFF0F0;border:1px solid #FFE0E0;}
.occ-kpi-label {font-size:12px;color:#8B4A4A;font-weight:650;}
.occ-kpi-value {font-size:36px;line-height:1.15;font-weight:850;color:#8F2020;}
.color-guide {flex:1;min-width:400px;border:1px solid #E1E8F0;border-radius:14px;padding:10px;background:#F8FAFC;}
.guide-title {font-size:13px;font-weight:750;color:#1A3154;margin:0 0 8px 4px;}
.guide-grid {display:grid;grid-template-columns:repeat(5,minmax(80px,1fr));gap:6px;}
.guide-item {padding:8px 5px;text-align:center;border-radius:9px;font-size:11px;font-weight:750;}
.guide-item span {display:block;font-weight:500;margin-top:4px;}
.guide-blue {background:#E2F0FF;color:#245B91;}
.guide-green {background:#DDF4E5;color:#176534;}
.guide-yellow {background:#FFF0C2;color:#805B00;}
.guide-orange {background:#FFE0C2;color:#8A3B00;}
.guide-red {background:#FFDCDC;color:#941E1E;}
.section-head {display:flex;align-items:center;justify-content:space-between;gap:12px;margin:12px 0 8px 0;}
.section-title {font-size:20px;font-weight:800;color:#162D50;}
.occ-summary {padding:16px 18px;border:1px solid #DCE5EF;border-radius:15px;background:#F8FAFC;margin-top:14px;}
.occ-summary-title {font-size:15px;font-weight:800;color:#1B3459;margin-bottom:12px;}
.summary-count {font-size:25px;font-weight:850;line-height:1.1;margin-top:4px;}
.summary-label {font-size:12px;color:#617187;}
.summary-dot {display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px;}
@media(max-width:1000px) {
 .top-header {flex-wrap:wrap;}
 .color-guide {min-width:100%;}
 .guide-grid {grid-template-columns:repeat(3,minmax(80px,1fr));}
}
div[data-testid="stButton"] button {border-radius:12px; min-height:76px; white-space:pre-line;
  text-align:left; padding:10px 14px; line-height:1.55; font-size:13px;
  border:1px solid #D6E4DD; box-shadow:0 2px 5px rgba(25,55,90,.035);}
div[data-testid="stButton"] button p {white-space:pre-line; line-height:1.55;}
div[data-testid="stButton"] button:hover {border-color:#8AA8C8; transform:translateY(-1px);}
</style>
""", unsafe_allow_html=True)

# Focus the screen on one stock at a time, as in the supplied design.
stock_options = sorted(filtered["Symbol"].dropna().unique().tolist())
if "focused_stock" not in st.session_state or st.session_state.focused_stock not in stock_options:
    current_selected = st.session_state.get("selected_occurrence")
    preferred = current_selected[0] if current_selected and current_selected[0] in stock_options else None
    st.session_state.focused_stock = preferred or stock_options[0]

selector_col, sort_col = st.columns([3, 2])
with selector_col:
    focused_stock = st.selectbox(
        "Stock to analyze", stock_options,
        index=stock_options.index(st.session_state.focused_stock),
        key="stock_focus_selector"
    )
    st.session_state.focused_stock = focused_stock
with sort_col:
    sort_choice = st.selectbox(
        "Sort occurrences", ["Date (ascending)", "Date (descending)", "% change (highest first)", "% change (lowest first)"],
        index=0, key="occurrence_sort_choice"
    )

stock_rows = filtered[filtered["Symbol"] == focused_stock].copy()
occurrence_dates = [
    pd.Timestamp(value).strftime("%Y-%m-%d")
    for value in stock_rows["OccurrenceDateTime"]
]
pct_by_date = fetch_occurrence_percentages(focused_stock, occurrence_dates)
stock_rows["DateISO"] = stock_rows["OccurrenceDateTime"].dt.strftime("%Y-%m-%d")
stock_rows["DailyChangePct"] = stock_rows["DateISO"].map(pct_by_date)
if sort_choice == "Date (descending)":
    stock_rows = stock_rows.sort_values("OccurrenceDateTime", ascending=False)
elif sort_choice == "% change (highest first)":
    stock_rows = stock_rows.sort_values("DailyChangePct", ascending=False, na_position="last")
elif sort_choice == "% change (lowest first)":
    stock_rows = stock_rows.sort_values("DailyChangePct", ascending=True, na_position="last")
else:
    stock_rows = stock_rows.sort_values("OccurrenceDateTime", ascending=True)

occurrence_count = len(stock_rows)
stock_meta = stock_rows.iloc[0]
sector_label = str(stock_meta.get("Sector", "—"))
cap_label = str(stock_meta.get("Marketcapname", "—"))

st.markdown(f"""
<div class="top-header">
  <div class="stock-identity">
    <div class="stock-mark">↗</div>
    <div>
      <div class="stock-title">{focused_stock}</div>
      <div class="stock-subtitle">{sector_label} · {cap_label} · NSE / BSE history where available</div>
    </div>
  </div>
  <div class="occ-kpi">
    <div class="occ-kpi-label">TOTAL OCCURRENCES</div>
    <div class="occ-kpi-value">{occurrence_count}</div>
  </div>
  <div class="color-guide">
    <div class="guide-title">📊 Daily change vs previous close · Color guide</div>
    <div class="guide-grid">
      <div class="guide-item guide-blue">&lt; 5%<span>Low</span></div>
      <div class="guide-item guide-green">5% – &lt; 7%<span>Moderate</span></div>
      <div class="guide-item guide-yellow">7% – &lt; 9%<span>High</span></div>
      <div class="guide-item guide-orange">9% – 11%<span>Very high</span></div>
      <div class="guide-item guide-red">&gt; 11%<span>Extreme</span></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="section-title">▦ Occurrences ({occurrence_count})</div>', unsafe_allow_html=True)
st.caption("Select any occurrence card to open the detailed selected-day and previous-trading-day OHLC analysis.")

def color_band(pct):
    if pct is None or pd.isna(pct):
        return ("#F1F5F9", "#536273", "Unavailable", "#DCE4EC")
    magnitude = abs(float(pct))
    if magnitude < 5:
        return ("#E2F0FF", "#245B91", "<5%", "#C6E0FF")
    if magnitude < 7:
        return ("#DDF4E5", "#176534", "5–<7%", "#C2EAD0")
    if magnitude < 9:
        return ("#FFF0C2", "#805B00", "7–<9%", "#FFE39A")
    if magnitude <= 11:
        return ("#FFE0C2", "#8A3B00", "9–11%", "#FFC99B")
    return ("#FFDCDC", "#941E1E", ">11%", "#FFC1C1")

# Grid of clean, numbered occurrence cards; buttons remain fully interactive.
per_row = 4
for row_start in range(0, len(stock_rows), per_row):
    batch = stock_rows.iloc[row_start:row_start + per_row]
    cols = st.columns(per_row, gap="medium")
    for j, (_, occ) in enumerate(batch.iterrows()):
        occurrence_dt = pd.Timestamp(occ["OccurrenceDateTime"])
        date_iso = occurrence_dt.strftime("%Y-%m-%d")
        time_text = occurrence_dt.strftime("%I:%M %p")
        pct = occ["DailyChangePct"]
        pct_text = f"{float(pct):+.2f}%" if pd.notna(pct) else "N/A"
        bg, fg, band, border_color = color_band(pct)
        ordinal = stock_rows.index.get_loc(occ.name) + 1
        weekday = occurrence_dt.strftime("%A")
        selected_key = (focused_stock, date_iso, time_text)
        is_selected = st.session_state.selected_occurrence == selected_key
        key = f"occ_{re.sub(r'[^A-Za-z0-9_-]', '_', focused_stock)}_{occurrence_dt.strftime('%Y%m%d_%H%M')}_{row_start}_{j}"
        st.markdown(
            f"<style>div[class*='st-key-{key}'] button {{"
            f"background:{bg} !important;color:{fg} !important;"
            f"border:1px solid {border_color} !important;"
            f"min-height:84px !important;font-weight:600 !important;"
            f"box-shadow:{'0 0 0 2px #244A91 inset' if is_selected else '0 2px 5px rgba(25,55,90,.04)'} !important;"
            f"}}</style>",
            unsafe_allow_html=True
        )
        label = f"{ordinal:02d}   ▦ {occurrence_dt.strftime('%d %b %Y')} · {time_text}\n{weekday}     {pct_text}"
        if cols[j].button(
            label, key=key, use_container_width=True,
            type="secondary",
            help=f"Daily change: {pct_text} · Band: {band}. Click to inspect OHLC."
        ):
            st.session_state.selected_occurrence = selected_key
            st.session_state.show_price_dialog = True
            st.rerun()

# Distribution summary for the focused stock.
band_specs = [
    ("<5%", "#2581D8"),
    ("5–<7%", "#159653"),
    ("7–<9%", "#D99A00"),
    ("9–11%", "#E87516"),
    (">11%", "#D62828"),
]
# Use vectorized pandas masks. Python chained comparisons against a Series
# raise "truth value of a Series is ambiguous".
magnitudes = pd.to_numeric(stock_rows["DailyChangePct"], errors="coerce").abs()
band_masks = [
    magnitudes < 5,
    (magnitudes >= 5) & (magnitudes < 7),
    (magnitudes >= 7) & (magnitudes < 9),
    (magnitudes >= 9) & (magnitudes <= 11),
    magnitudes > 11,
]
band_counts = [int(mask.sum()) for mask in band_masks]
st.markdown('<div class="occ-summary"><div class="occ-summary-title">▥ Occurrence analysis summary · by absolute daily % change</div>', unsafe_allow_html=True)
summary_cols = st.columns(5)
for col, (label, dot_color), count in zip(summary_cols, band_specs, band_counts):
    col.markdown(
        f'<div style="text-align:center;padding:4px 2px;">'
        f'<span class="summary-dot" style="background:{dot_color};"></span>'
        f'<span style="font-size:13px;font-weight:750;color:#1B2D4A;">{label}</span>'
        f'<div class="summary-count" style="color:#162D50;">{count}</div>'
        f'<div class="summary-label">occurrences</div></div>',
        unsafe_allow_html=True
    )
st.markdown('</div>', unsafe_allow_html=True)

# Default to most recent occurrence if user hasn't clicked one yet.
if st.session_state.selected_occurrence is None:
    last = filtered.sort_values("OccurrenceDateTime").iloc[-1]
    st.session_state.selected_occurrence = (
        str(last["Symbol"]), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%Y-%m-%d"),
        pd.Timestamp(last["OccurrenceDateTime"]).strftime("%I:%M %p")
    )

sel_sym, sel_date, sel_time = st.session_state.selected_occurrence
selection_still_valid = not filtered[
    (filtered["Symbol"] == sel_sym) &
    (filtered["OccurrenceDateTime"].dt.strftime("%Y-%m-%d") == sel_date) &
    (filtered["OccurrenceDateTime"].dt.strftime("%I:%M %p") == sel_time)
].empty

if not selection_still_valid:
    last = filtered.sort_values("OccurrenceDateTime").iloc[-1]
    sel_sym, sel_date, sel_time = str(last["Symbol"]), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%Y-%m-%d"), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%I:%M %p")
    st.session_state.selected_occurrence = (sel_sym, sel_date, sel_time)



@st.cache_data(ttl=3600, show_spinner=False)
def fetch_day_ohlc(symbol, date_iso):
    """Fetch selected-day and previous-trading-day OHLCV data from Yahoo Finance."""
    import yfinance as yf
    import numpy as np

    event_date = pd.Timestamp(date_iso).normalize()
    start = (event_date - pd.Timedelta(days=20)).date().isoformat()
    end = (event_date + pd.Timedelta(days=3)).date().isoformat()
    errors = []

    for suffix in [".NS", ".BO"]:
        ticker = f"{symbol}{suffix}"
        try:
            prices = yf.download(
                ticker, start=start, end=end, interval="1d",
                auto_adjust=False, progress=False, threads=False
            )
            if prices is None or prices.empty:
                errors.append(f"No history for {ticker}")
                continue
            if isinstance(prices.columns, pd.MultiIndex):
                prices.columns = prices.columns.get_level_values(0)
            prices = prices.reset_index()
            date_col = "Date" if "Date" in prices.columns else prices.columns[0]
            prices[date_col] = pd.to_datetime(prices[date_col]).dt.tz_localize(None).dt.normalize()
            prices = prices.sort_values(date_col).drop_duplicates(date_col).reset_index(drop=True)

            matched = prices.index[prices[date_col] == event_date]
            if len(matched) == 0:
                errors.append(f"No candle for {ticker} on {event_date.date()}")
                continue

            pos = int(matched[0])
            selected = prices.iloc[pos]
            previous = prices.iloc[pos - 1] if pos > 0 else None

            def field(row, name):
                if row is None:
                    return np.nan
                return pd.to_numeric(row.get(name), errors="coerce")

            def candle(row, row_date=None):
                return {
                    "date": pd.Timestamp(row_date).strftime("%Y-%m-%d") if row_date is not None else None,
                    "open": field(row, "Open"),
                    "high": field(row, "High"),
                    "low": field(row, "Low"),
                    "close": field(row, "Close"),
                    "volume": field(row, "Volume"),
                }

            selected_candle = candle(selected, selected[date_col])
            previous_candle = candle(previous, previous[date_col]) if previous is not None else None
            previous_close = previous_candle["close"] if previous_candle else np.nan
            selected_close = selected_candle["close"]
            daily_pct = (
                (selected_close - previous_close) / previous_close * 100
                if pd.notna(selected_close) and pd.notna(previous_close) and previous_close != 0
                else np.nan
            )
            intraday_pct = (
                (selected_candle["close"] - selected_candle["open"]) / selected_candle["open"] * 100
                if pd.notna(selected_candle["close"]) and pd.notna(selected_candle["open"]) and selected_candle["open"] != 0
                else np.nan
            )
            return {
                "ticker": ticker,
                "date": event_date.strftime("%Y-%m-%d"),
                "selected": selected_candle,
                "previous": previous_candle,
                "daily_pct": daily_pct,
                "intraday_pct": intraday_pct,
                "error": None,
            }
        except Exception as exc:
            errors.append(f"{ticker}: {exc}")
    return {"error": "Could not retrieve daily OHLC data. " + " | ".join(errors)}

@st.dialog("📊 Historical price-change analysis", width="small")
def show_price_dialog(sel_sym, sel_date, sel_time, sector_name, cap_name, occurrence_count):
    st.markdown(f"## {sel_sym}")
    st.caption(f"{pd.Timestamp(sel_date).strftime('%A, %d %B %Y')} · {sel_time}")

    with st.spinner(f"Loading selected-day and previous-day OHLC data for {sel_sym}..."):
        result = fetch_day_ohlc(sel_sym, sel_date)

    if result.get("error"):
        st.warning(result["error"])
        st.caption("Daily OHLC is retrieved from Yahoo Finance; an unavailable ticker/date may have no result.")
        return

    def show_candle(title, candle_data):
        st.markdown(f"### {title}")
        if candle_data is None:
            st.warning("Previous trading-day data is unavailable.")
            return
        candle_date = pd.Timestamp(candle_data["date"]).strftime("%A, %d %B %Y")
        st.caption(candle_date)
        a, b = st.columns(2)
        a.metric("Open", f"₹{candle_data['open']:.2f}" if pd.notna(candle_data["open"]) else "N/A")
        b.metric("High", f"₹{candle_data['high']:.2f}" if pd.notna(candle_data["high"]) else "N/A")
        c, d = st.columns(2)
        c.metric("Low", f"₹{candle_data['low']:.2f}" if pd.notna(candle_data["low"]) else "N/A")
        d.metric("Close", f"₹{candle_data['close']:.2f}" if pd.notna(candle_data["close"]) else "N/A")
        st.caption(f"Volume: {candle_data['volume']:,.0f}" if pd.notna(candle_data["volume"]) else "Volume: N/A")

    st.caption(f"Source ticker: `{result['ticker']}`")

    # Main metric requested in the highlighted popup area: close-to-close change.
    daily_pct = result.get("daily_pct", float("nan"))
    if pd.notna(daily_pct):
        pct_label = "Daily change vs previous close"
        pct_value = f"{daily_pct:+.2f}%"
        pct_help = "(Selected-day Close − Previous trading-day Close) ÷ Previous trading-day Close × 100."
        pct_delta_color = "normal"
    else:
        pct_label = "Daily change vs previous close"
        pct_value = "N/A"
        pct_help = "Percentage cannot be calculated because the selected or previous close is unavailable."
        pct_delta_color = "off"

    # A prominent right-aligned metric mirrors the user's highlighted area.
    pct_col, blank_col = st.columns([1, 1])
    with pct_col:
        st.metric(pct_label, pct_value, help=pct_help, delta_color=pct_delta_color)

    show_candle("Selected day — OHLC", result["selected"])
    st.divider()
    show_candle("Previous trading day — OHLC", result["previous"])


# Default to most recent occurrence if user hasn't clicked one yet.
if st.session_state.selected_occurrence is None:
    last = filtered.sort_values("OccurrenceDateTime").iloc[-1]
    st.session_state.selected_occurrence = (
        str(last["Symbol"]), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%Y-%m-%d"),
        pd.Timestamp(last["OccurrenceDateTime"]).strftime("%I:%M %p")
    )

sel_sym, sel_date, sel_time = st.session_state.selected_occurrence
selection_still_valid = not filtered[
    (filtered["Symbol"] == sel_sym) &
    (filtered["OccurrenceDateTime"].dt.strftime("%Y-%m-%d") == sel_date) &
    (filtered["OccurrenceDateTime"].dt.strftime("%I:%M %p") == sel_time)
].empty

if not selection_still_valid:
    last = filtered.sort_values("OccurrenceDateTime").iloc[-1]
    sel_sym, sel_date, sel_time = str(last["Symbol"]), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%Y-%m-%d"), pd.Timestamp(last["OccurrenceDateTime"]).strftime("%I:%M %p")
    st.session_state.selected_occurrence = (sel_sym, sel_date, sel_time)

detail = filtered[
    (filtered["Symbol"] == sel_sym) &
    (filtered["OccurrenceDateTime"].dt.strftime("%Y-%m-%d") == sel_date) &
    (filtered["OccurrenceDateTime"].dt.strftime("%I:%M %p") == sel_time)
].iloc[0]

if st.session_state.get("show_price_dialog", False):
    st.session_state.show_price_dialog = False
    show_price_dialog(
        sel_sym, sel_date, sel_time, str(detail["Sector"]), str(detail["Marketcapname"]),
        int((filtered["Symbol"] == sel_sym).sum())
    )

st.markdown("---")
with st.expander("Data quality & methodology"):
    quality = pd.DataFrame([
        ("Source rows", len(raw)),
        ("Missing cells in source", int(raw.isna().sum().sum())),
        ("Unparseable dates", int(df["DateTime"].isna().sum())),
        ("Exact duplicate rows", int(raw.duplicated().sum())),
        ("Duplicate timestamp + symbol pairs", int(df.duplicated(["DateTime", "Symbol"]).sum())),
    ], columns=["Check", "Result"])
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.markdown("""
    **Verified from the CSV:** stock symbols, recorded dates/times, occurrence counts, sectors and market-cap labels.

    **Fetched externally:** daily OHLC prices and percentage changes from Yahoo Finance. These can be unavailable or delayed for some symbols/dates.

    **Important timing note:** the signal timestamp may be 11:30 AM, but daily change uses the final close. That closing price was not yet known at 11:30 AM; this is an end-of-day outcome, not an executable 11:30 AM return.
    """)

st.download_button(
    "⬇ Download filtered occurrence list",
    data=filtered[["Symbol", "Date", "OriginalDate", "Sector", "Marketcapname"]].rename(
        columns={"OriginalDate": "Recorded_Date_Time", "Marketcapname": "Market_Cap"}
    ).to_csv(index=False).encode("utf-8"),
    file_name="top_gainers_occurrences.csv",
    mime="text/csv"
)
