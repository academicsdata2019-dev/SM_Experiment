from pathlib import Path
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Top Gainers Intelligence", page_icon="📈", layout="wide")

# ---- Market-terminal visual system ----
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 82% 0%, rgba(0,190,160,.10), transparent 30%), #06172B; color:#EAF2FF; }
[data-testid="stHeader"] { background:rgba(6,23,43,.92); }
.block-container { max-width: 1680px; padding-top: 1.15rem; padding-bottom: 2.5rem; }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
[data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] { color:#B8C9DE; }
h1,h2,h3,h4 { color:#F5F8FF !important; letter-spacing:-.025em; }
.hero { position:relative; overflow:hidden; padding:1.6rem 1.75rem; border-radius:20px; margin:.2rem 0 1.15rem 0;
  background:linear-gradient(112deg,#071B31 0%,#0B2B49 58%,#075A62 100%); border:1px solid #1B4664;
  box-shadow:0 12px 34px rgba(0,0,0,.18); }
.hero:after { content:""; position:absolute; right:-50px; top:-100px; width:410px; height:260px; pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 18px,rgba(28,219,169,.055) 19px 20px),radial-gradient(circle,rgba(25,215,165,.13),transparent 65%); transform:rotate(-8deg); }
.hero h1 { color:#F7FAFF !important; margin:0 0 .42rem 0; font-size:clamp(1.8rem,3vw,2.55rem); font-weight:850; }
.hero h1 span { color:#28E0A0; }
.hero p { color:#C5D9EE; margin:0; font-size:1rem; max-width:920px; }
.kpi { padding:1rem 1.1rem; min-height:106px; border-radius:15px; border:1px solid #173B5B;
  background:linear-gradient(145deg,rgba(13,43,71,.98),rgba(7,28,50,.98)); box-shadow:0 5px 16px rgba(0,0,0,.12); }
.kpi-label { font-size:.78rem; color:#AFC5DF; margin-bottom:.35rem; }
.kpi-value { font-size:1.72rem; font-weight:800; line-height:1.2; color:#F5F8FF; }
.kpi-note { color:#8DA9C7; font-size:.76rem; margin-top:.35rem; }
.market-hero {position:relative;display:flex;align-items:center;justify-content:space-between;gap:22px;overflow:hidden;padding:19px 20px;border:1px solid #174467;border-radius:17px;background:linear-gradient(100deg,rgba(3,22,42,.98) 0%,rgba(5,31,55,.92) 53%,rgba(4,49,66,.76) 100%);box-shadow:0 10px 28px rgba(0,0,0,.2);margin:.1rem 0 13px;min-height:94px;}
.market-hero:before {content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(3,22,42,.08) 0%,rgba(3,22,42,.16) 45%,rgba(3,22,42,.35) 100%);}
.market-hero-content {position:relative;z-index:1;min-width:0;}
.market-hero-title {font-size:clamp(1.7rem,3vw,2.55rem);font-weight:850;line-height:1.12;letter-spacing:-.035em;color:#F5F8FF;margin:0 0 6px;}
.market-hero-title span {color:#27E1A0;}
.market-hero-subtitle {font-size:.93rem;line-height:1.45;color:#BED4EB;margin:0;}
.market-clock {position:relative;z-index:1;flex:0 0 auto;display:flex;align-items:center;gap:10px;padding:10px 13px;border:1px solid #245578;border-radius:12px;background:rgba(3,22,42,.78);box-shadow:0 4px 14px rgba(0,0,0,.15);}
.market-clock-icon {font-size:1.55rem;line-height:1;color:#A7C9E8;}
.market-clock-date {font-size:.76rem;font-weight:750;color:#F0F6FF;white-space:nowrap;}
.market-clock-time {font-size:.74rem;color:#AFC7E1;margin-top:3px;}
.market-kpi-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:0 0 18px;}
.market-kpi {display:flex;align-items:center;gap:13px;min-width:0;min-height:92px;padding:11px 13px;border:1px solid #173E5F;border-radius:14px;background:linear-gradient(145deg,rgba(9,35,61,.98),rgba(5,25,46,.98));box-shadow:0 5px 16px rgba(0,0,0,.13);}
.market-kpi-icon {width:56px;height:56px;flex:0 0 56px;display:flex;align-items:center;justify-content:center;border-radius:12px;font-size:1.8rem;background:#10395A;color:#48B9FF;}
.market-kpi-icon.pink {background:rgba(240,85,126,.13);color:#FF688D;}
.market-kpi-icon.green {background:rgba(26,215,157,.13);color:#25E1A0;}
.market-kpi-icon.blue {background:rgba(57,157,255,.13);color:#47B7FF;}
.market-kpi-copy {min-width:0;}
.market-kpi-label {font-size:.76rem;color:#C2D6EA;margin-bottom:3px;white-space:nowrap;}
.market-kpi-value {font-size:1.5rem;font-weight:850;line-height:1.15;color:#F7FAFF;white-space:nowrap;}
.market-kpi-value.positive {color:#28E3A0;}
.market-kpi-value.status {font-size:1.05rem;color:#2BE4A5;}
.market-kpi-note {font-size:.73rem;color:#93B0CE;margin-top:4px;white-space:normal;}
@media(max-width:1100px){.market-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.market-hero{align-items:flex-start;}}
@media(max-width:680px){.market-hero{flex-direction:column;padding:16px;}.market-clock{align-self:flex-start;}.market-kpi-grid{grid-template-columns:1fr;}.market-kpi{min-height:78px;}}
.info-banner { display:flex; gap:.8rem; align-items:flex-start; padding:.9rem 1rem; border-radius:13px; margin:.25rem 0 1rem 0;
  background:linear-gradient(100deg,#0D2B4A,#0B2943); border:1px solid #1B4668; color:#C5DDF6; font-size:.88rem; line-height:1.6; }
.info-banner strong { color:#62C6FF; }
/* Section bars: match the slim navy-blue headers in the reference design. */
[data-testid="stExpander"] {
  border:1px solid #173C5D !important;
  border-radius:10px !important;
  overflow:hidden !important;
  background:linear-gradient(180deg,rgba(7,29,51,.96),rgba(5,23,42,.96)) !important;
  box-shadow:0 3px 10px rgba(0,0,0,.10) !important;
}
[data-testid="stExpander"] summary {
  color:#EAF3FF !important;
  font-weight:750 !important;
  background:linear-gradient(100deg,#092642 0%,#071E37 58%,#08243D 100%) !important;
  border-bottom:1px solid rgba(42,91,128,.52) !important;
  min-height:32px !important;
  padding:.42rem .72rem !important;
}
[data-testid="stExpander"] summary:hover {
  color:#38E1A0 !important;
  background:linear-gradient(100deg,#0B304C 0%,#08243F 58%,#093047 100%) !important;
}
[data-testid="stExpander"] details > div {
  background:linear-gradient(180deg,rgba(7,27,48,.98),rgba(5,22,40,.98)) !important;
}
[data-testid="stFileUploader"] section { background:#0A2038 !important; border:1px dashed #2A5478 !important; border-radius:12px !important; }
[data-testid="stFileUploader"] button { background:#12365B !important; color:#EAF3FF !important; border:1px solid #2D5B82 !important; border-radius:9px !important; }
[data-testid="stDateInput"] input, [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background:#081E35 !important; color:#EAF3FF !important; border-color:#244B6D !important; border-radius:9px !important; }
label, [data-testid="stWidgetLabel"] p { color:#C6D7EA !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#041326 0%,#071D33 62%,#06172B 100%); border-right:1px solid #153854; }
[data-testid="stSidebar"] * { color:#EAF2FA; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.72rem .72rem; border-radius:11px; margin:.24rem 0; border:1px solid rgba(220,235,250,.09); background:rgba(255,255,255,.025); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(20,206,157,.09); border-color:#287B78; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { font-weight:650; font-size:.91rem; }
.nav-brand { padding:.55rem .35rem 1.25rem; margin-bottom:1rem; border-bottom:1px solid rgba(255,255,255,.12); }
.nav-brand-icon { font-size:1.8rem; color:#27DFA0; }.nav-brand-title { font-size:1.13rem; font-weight:850; line-height:1.3; color:#FFFFFF; }
.nav-brand-sub { font-size:.74rem; color:#9FB8D3; margin-top:.28rem; }.nav-section { font-size:.69rem; letter-spacing:.13em; text-transform:uppercase; color:#7F9DBD; margin:1rem .35rem .45rem; }
.stock-panel { border:1px solid #173D5D; border-radius:17px; overflow:hidden; background:linear-gradient(140deg,#0A223C,#071A30); box-shadow:0 8px 24px rgba(0,0,0,.12); }
.stock-panel-head { padding:.8rem .9rem; display:flex; justify-content:space-between; align-items:center; gap:.7rem; flex-wrap:wrap; border-bottom:1px solid #173650; }
.stock-identity { display:flex; align-items:center; gap:12px; min-width:230px; }
.stock-mark { width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1BC7C2,#22E49B);color:#06243B;font-size:16px;font-weight:850; }
.stock-title { font-size:18px;font-weight:850;color:#F3F7FF;line-height:1.2; }
.stock-subtitle { font-size:12px;color:#9FB6D0;margin-top:5px; }
.occ-kpi { min-width:140px;padding:9px 15px;text-align:left;border-radius:12px;background:rgba(224,55,91,.10);border:1px solid rgba(224,55,91,.32); }
.occ-kpi-label { font-size:11px;color:#F3A4B3;font-weight:650;letter-spacing:.03em; }
.occ-kpi-value { font-size:30px;line-height:1.15;font-weight:850;color:#FF5871; }
.color-guide { border:1px solid #173D5D;border-radius:14px;padding:12px 13px;background:#081E35;margin:.6rem 0 1rem; }
.guide-title { font-size:14px;font-weight:750;color:#B9E4FF;margin:0 0 9px 4px; }
.guide-grid { display:grid;grid-template-columns:repeat(5,minmax(80px,1fr));gap:8px; }
.guide-item { padding:9px 5px;text-align:center;border-radius:9px;font-size:12px;font-weight:800;border:1px solid transparent; }
.guide-item span { display:block;font-weight:500;margin-top:3px;font-size:11px;opacity:.9; }
.guide-blue { background:#0E3A62;color:#6AB8FF;border-color:#175487; }
.guide-green { background:#073C3A;color:#37E6A0;border-color:#08745F; }
.guide-yellow { background:#3D3513;color:#FFD54F;border-color:#7C6818; }
.guide-orange { background:#48271C;color:#FF9A55;border-color:#8D492B; }
.guide-red { background:#481E30;color:#FF5B76;border-color:#8B2947; }
.section-title { font-size:19px;font-weight:800;color:#ECF5FF;margin:.45rem 0 .35rem; }
.occ-summary { padding:15px 17px;border:1px solid #173D5D;border-radius:15px;background:#081E35;margin-top:14px; }
.occ-summary-title { font-size:15px;font-weight:800;color:#C8E7FF;margin-bottom:12px; }
.summary-count { font-size:25px;font-weight:850;line-height:1.1;margin-top:4px; }
.summary-label { font-size:12px;color:#8DA9C7; }
.summary-dot { display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px; }
div[data-testid="stButton"] button { border-radius:10px; min-height:67px; white-space:pre-line; text-align:left; padding:9px 12px; line-height:1.45; font-size:12px; font-weight:650; transition:all .16s ease; }
div[data-testid="stButton"] button p { white-space:pre-line; line-height:1.45; }
div[data-testid="stButton"] button:hover { border-color:#37DFA6 !important; transform:translateY(-1px); box-shadow:0 5px 16px rgba(0,0,0,.18); }
[data-testid="stMetric"] { background:#0A223C; border:1px solid #173D5D; border-radius:12px; padding:12px 14px; }
[data-testid="stMetricLabel"] p { color:#9FB8D3 !important; }
[data-testid="stMetricValue"] { color:#F4F8FF !important; }
[data-testid="stDataFrame"] { border:1px solid #173D5D; border-radius:10px; overflow:hidden; }
/* Compact full-page market overview matching the supplied reference */
.block-container { max-width: 1800px !important; padding-top: .45rem !important; padding-bottom: 1.1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
[data-testid="stExpander"] { margin: .35rem 0 .5rem !important; border-radius: 11px !important; }
[data-testid="stExpander"] summary { padding: .48rem .72rem !important; min-height: 34px !important; }
[data-testid="stExpander"] details > div { padding: .45rem .72rem .6rem !important; }
[data-testid="stFileUploader"] { margin-bottom: 0 !important; }
[data-testid="stFileUploaderDropzone"] { min-height: 54px !important; padding: .45rem .65rem !important; background: #071D33 !important; border: 1px dashed #2B567A !important; border-radius: 9px !important; }
[data-testid="stFileUploaderDropzone"] button { padding: .28rem .55rem !important; min-height: 30px !important; }
[data-testid="stDateInput"] input, [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { min-height: 34px !important; }
[data-testid="stButton"] button { min-height: 34px !important; }
[data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button { background: linear-gradient(100deg,#12C99A,#35E6A3) !important; color: #03253A !important; border: 1px solid #28DCA3 !important; font-weight: 800 !important; }
.info-banner { padding: .58rem .75rem !important; border-radius: 10px !important; margin: .35rem 0 .45rem !important; font-size: .76rem !important; line-height: 1.45 !important; }
.market-hero { min-height: 78px !important; padding: 12px 15px !important; margin: .05rem 0 .55rem !important; border-radius: 13px !important; }
.market-hero-title { font-size: clamp(1.5rem, 2.4vw, 2.15rem) !important; margin-bottom: 3px !important; }
.market-hero-subtitle { font-size: .82rem !important; }
.market-kpi-grid { gap: 9px !important; margin-bottom: .55rem !important; }
.market-kpi { min-height: 70px !important; padding: 8px 10px !important; border-radius: 11px !important; gap: 10px !important; }
.market-kpi-icon { width: 44px !important; height: 44px !important; flex-basis: 44px !important; font-size: 1.45rem !important; }
.market-kpi-value { font-size: 1.25rem !important; }
.market-kpi-label { font-size: .69rem !important; margin-bottom: 1px !important; }
.market-kpi-note { font-size: .66rem !important; margin-top: 2px !important; }
.color-guide { padding: 8px 9px !important; margin: .35rem 0 .65rem !important; border-radius: 10px !important; }
.guide-title { font-size: .78rem !important; margin-bottom: 6px !important; }
.guide-item { padding: 5px 3px !important; font-size: .72rem !important; border-radius: 7px !important; }
.guide-item span { font-size: .64rem !important; margin-top: 1px !important; }
@media(max-width:900px) { .market-kpi-grid { grid-template-columns: repeat(2,minmax(0,1fr)) !important; } }
@media(max-width:600px) { .market-kpi-grid { grid-template-columns: 1fr !important; } .guide-grid { grid-template-columns: repeat(2,minmax(0,1fr)) !important; } }

@media(max-width:1000px) { .hero {padding:1.2rem;} .guide-grid {grid-template-columns:repeat(3,minmax(80px,1fr));} .stock-panel-head {align-items:flex-start;} }

/* High-contrast historical OHLC dialog: override Streamlit's default light modal. */
[data-testid="stDialog"], [data-testid="stDialog"] > div,
[role="dialog"], [aria-modal="true"] { color:#EAF2FF !important; }
[data-testid="stDialog"] > div, [role="dialog"] > div, [aria-modal="true"] > div {
  background:#06172B !important; color:#EAF2FF !important;
  border:1px solid #245578 !important; border-radius:16px !important;
}
[data-testid="stDialog"] h1, [data-testid="stDialog"] h2, [data-testid="stDialog"] h3,
[role="dialog"] h1, [role="dialog"] h2, [role="dialog"] h3,
[aria-modal="true"] h1, [aria-modal="true"] h2, [aria-modal="true"] h3 { color:#F5F8FF !important; }
[data-testid="stDialog"] p, [data-testid="stDialog"] label,
[data-testid="stDialog"] [data-testid="stCaptionContainer"],
[role="dialog"] p, [role="dialog"] label, [aria-modal="true"] p, [aria-modal="true"] label { color:#B8C9DE !important; }
[data-testid="stDialog"] [data-testid="stMetric"], [role="dialog"] [data-testid="stMetric"],
[aria-modal="true"] [data-testid="stMetric"] {
  background:#0B2540 !important; border:1px solid #285477 !important;
  border-radius:12px !important; padding:14px 16px !important; min-height:104px !important;
}
[data-testid="stDialog"] [data-testid="stMetricLabel"], [data-testid="stDialog"] [data-testid="stMetricLabel"] p,
[role="dialog"] [data-testid="stMetricLabel"], [role="dialog"] [data-testid="stMetricLabel"] p,
[aria-modal="true"] [data-testid="stMetricLabel"], [aria-modal="true"] [data-testid="stMetricLabel"] p {
  color:#B7CEE5 !important; font-size:.9rem !important;
}
[data-testid="stDialog"] [data-testid="stMetricValue"], [data-testid="stDialog"] [data-testid="stMetricValue"] div,
[role="dialog"] [data-testid="stMetricValue"], [role="dialog"] [data-testid="stMetricValue"] div,
[aria-modal="true"] [data-testid="stMetricValue"], [aria-modal="true"] [data-testid="stMetricValue"] div {
  color:#F4F8FF !important; font-size:clamp(1.45rem,3vw,2rem) !important; font-weight:750 !important;
}
[data-testid="stDialog"] code, [role="dialog"] code, [aria-modal="true"] code { color:#52E2A9 !important; background:#0A2A36 !important; }
[data-testid="stDialog"] [data-testid="stMarkdownContainer"] p,
[role="dialog"] [data-testid="stMarkdownContainer"] p,
[aria-modal="true"] [data-testid="stMarkdownContainer"] p { color:#D6E4F4 !important; }
[data-testid="stDialog"] button[aria-label="Close"], [role="dialog"] button[aria-label="Close"],
[aria-modal="true"] button[aria-label="Close"] { color:#EAF2FF !important; }

/* View Details action: navy blue with strong readable contrast */
.stApp .st-key-view_stock_details [data-testid="stButton"] > button,
.stApp .st-key-view_stock_details button {
  background: linear-gradient(135deg, #0B2B4A 0%, #123E63 100%) !important;
  color: #F4FAFF !important;
  border: 1px solid #20C9B9 !important;
  border-radius: 10px !important;
  font-weight: 750 !important;
  opacity: 1 !important;
  box-shadow: 0 3px 10px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.06) !important;
}
.stApp .st-key-view_stock_details button p,
.stApp .st-key-view_stock_details button span { color: #F4FAFF !important; opacity: 1 !important; }
.stApp .st-key-view_stock_details button:hover {
  background: linear-gradient(135deg, #12466D 0%, #176080 100%) !important;
  color: #FFFFFF !important; border-color: #48F0D6 !important;
  box-shadow: 0 0 0 2px rgba(32,201,185,.18), 0 5px 14px rgba(0,0,0,.3) !important;
}
.stApp .st-key-view_stock_details button:focus { outline: 2px solid #48F0D6 !important; outline-offset: 2px !important; }


/* Reset filter button matches the View Details navy action */
.stApp .st-key-reset_market_filters [data-testid="stButton"] > button,
.stApp .st-key-reset_market_filters button {
  background: linear-gradient(135deg, #0B2B4A 0%, #123E63 100%) !important;
  color: #F4FAFF !important;
  border: 1px solid #20C9B9 !important;
  border-radius: 10px !important;
  font-weight: 750 !important;
  opacity: 1 !important;
  box-shadow: 0 3px 10px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.06) !important;
}
.stApp .st-key-reset_market_filters button p,
.stApp .st-key-reset_market_filters button span { color: #F4FAFF !important; opacity: 1 !important; }
.stApp .st-key-reset_market_filters button:hover {
  background: linear-gradient(135deg, #12466D 0%, #176080 100%) !important;
  color: #FFFFFF !important; border-color: #48F0D6 !important;
  box-shadow: 0 0 0 2px rgba(32,201,185,.18), 0 5px 14px rgba(0,0,0,.3) !important;
}
.stApp .st-key-reset_market_filters button:focus { outline: 2px solid #48F0D6 !important; outline-offset: 2px !important; }

</style>
""", unsafe_allow_html=True)

# ---- Branded navigation sidebar matching the supplied reference ----
if "main_navigation" not in st.session_state:
    st.session_state.main_navigation = "Top Gainer Intelligence"

def _set_navigation(destination):
    st.session_state.main_navigation = destination

selected_nav_key = {
    "Top Gainer Intelligence": "nav_top_gainer_intelligence",
    "MACD Cross Over Movement": "nav_macd_cross_over_movement",
    "Dashboard": "nav_dashboard",
    "Watchlist": "nav_watchlist",
    "Reports": "nav_reports",
    "Settings": "nav_settings",
}.get(st.session_state.main_navigation, "nav_top_gainer_intelligence")

st.markdown("""
<style>
/* Remove Streamlit's default sidebar toggle that can expose the raw
   Material icon name (for example, keyboard_double_arrow_left). */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebar"] button[aria-label*="Collapse"],
[data-testid="stSidebar"] button[title*="Collapse"],
button[data-testid="stSidebarCollapseButton"] {
  display:none !important;
  visibility:hidden !important;
  width:0 !important;
  height:0 !important;
  padding:0 !important;
  margin:0 !important;
}
/* Keep the branded navigation fixed without covering the main workspace.
   The explicit content offset is required because the sidebar is position:fixed. */
:root { --market-sidebar-width: 290px; }
[data-testid="stSidebar"] {
  position:fixed !important;
  top:0 !important;
  bottom:0 !important;
  left:0 !important;
  width:var(--market-sidebar-width) !important;
  min-width:var(--market-sidebar-width) !important;
  max-width:var(--market-sidebar-width) !important;
  height:100vh !important;
  overflow-y:auto !important;
  z-index:1000 !important;
}
/* Streamlit normally lays the main view alongside the sidebar. Since this
   custom sidebar is fixed, reserve its width explicitly to prevent overlap. */
div[data-testid="stAppViewContainer"] {
  margin-left:var(--market-sidebar-width) !important;
  width:calc(100% - var(--market-sidebar-width)) !important;
  min-width:0 !important;
}
div[data-testid="stAppViewContainer"] > .main {
  min-width:0 !important;
}
@media (max-width: 900px) {
  :root { --market-sidebar-width: 250px; }
}
@media (max-width: 680px) {
  :root { --market-sidebar-width: 220px; }
  .block-container { padding-left: .8rem !important; padding-right: .8rem !important; }
}
  background-color:#04172B !important;
  background-image:
    linear-gradient(180deg, rgba(3,19,37,.97) 0%, rgba(3,22,42,.90) 48%, rgba(3,20,38,.25) 78%, rgba(3,18,34,.12) 100%),
    url("data:image/png;base64,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") !important;
  background-repeat:no-repeat !important;
  background-position:center, center bottom 42px !important;
  background-size:cover, 100% auto !important;
  border-right:1px solid #123451 !important;
}
[data-testid="stSidebar"] > div:first-child {background:transparent !important; padding-top:.8rem;}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] button {font-family:Inter, "Segoe UI", Arial, sans-serif !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#D6E7F7;}
.nav-brand {display:flex; align-items:center; gap:9px; padding:.15rem .25rem .9rem; margin-bottom:.8rem; border-bottom:1px solid rgba(115,160,197,.16);}
.nav-logo {color:#24E3A1; font-size:1.65rem; line-height:1; text-shadow:0 0 15px rgba(36,227,161,.2);}
.nav-brand-title {font-size:.98rem; font-weight:850; letter-spacing:.01em; line-height:1.1; color:#F6FBFF;}
.nav-brand-title span {color:#2BE4A5;}
.nav-brand-sub {font-size:.55rem; letter-spacing:.13em; color:#91ABC5; text-transform:uppercase; margin-top:.25rem;}
.nav-section {font-size:.59rem; letter-spacing:.14em; text-transform:uppercase; color:#7899BA; margin:1.5rem .45rem .45rem;}
[data-testid="stSidebar"] [data-testid="stButton"] {margin:.12rem 0 !important;}
[data-testid="stSidebar"] [data-testid="stButton"] button {
  width:100%; min-height:35px; justify-content:flex-start; text-align:left;
  border-radius:8px; padding:.48rem .55rem; border:1px solid transparent;
  background:rgba(7,29,51,.42); color:#D5E6F6; font-size:.76rem;
  font-weight:550; box-shadow:none; transition:all .15s ease;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
  background:rgba(24,94,124,.34); border-color:rgba(49,208,174,.28);
  color:#FFFFFF; transform:translateX(1px);
}
[data-testid="stSidebar"] [class*="st-key-__SELECTED_NAV_KEY__"] button {
  background:linear-gradient(100deg,rgba(12,100,91,.52),rgba(13,48,82,.82)) !important;
  border-color:rgba(36,227,161,.48) !important;
  box-shadow:inset 2px 0 0 #20E3A1 !important;
  color:#FFFFFF !important; font-weight:750 !important;
}
.sidebar-footer {margin-top:1.6rem; padding:.45rem .2rem 0; text-align:center; font-size:.63rem; letter-spacing:.02em; color:#9AB6D0; text-shadow:0 1px 4px #001020;}
.sidebar-version {text-align:center; color:#7898B7; font-size:.56rem; margin-top:.35rem;}
</style>
""".replace("__SELECTED_NAV_KEY__", selected_nav_key), unsafe_allow_html=True)

primary_navigation = [
    ("Top Gainer Intelligence", "▥", "nav_top_gainer_intelligence"),
    ("MACD Cross Over Movement", "⌁", "nav_macd_cross_over_movement"),
]
st.sidebar.markdown("""
<div class="nav-brand">
  <div class="nav-logo">▰↗</div>
  <div>
    <div class="nav-brand-title">MARKET <span>PULSE</span></div>
    <div class="nav-brand-sub">STOCK INTELLIGENCE</div>
  </div>
</div>
""", unsafe_allow_html=True)

for destination, icon_text, nav_key in primary_navigation:
    st.sidebar.button(
        f" {icon_text}   {destination}", key=nav_key,
        use_container_width=True, on_click=_set_navigation, args=(destination,)
    )

st.sidebar.markdown('<div class="nav-section">MARKET INSIGHTS</div>', unsafe_allow_html=True)
secondary_navigation = [
    ("Dashboard", "▣", "nav_dashboard"),
    ("Watchlist", "◎", "nav_watchlist"),
    ("Reports", "▤", "nav_reports"),
    ("Settings", "⚙", "nav_settings"),
]
for destination, icon_text, nav_key in secondary_navigation:
    st.sidebar.button(
        f" {icon_text}   {destination}", key=nav_key,
        use_container_width=True, on_click=_set_navigation, args=(destination,)
    )

st.sidebar.markdown(
    '<div class="sidebar-footer">Analyze&nbsp; • &nbsp;Discover&nbsp; • &nbsp;Grow</div>'
    '<div class="sidebar-version">v1.0</div>',
    unsafe_allow_html=True
)

page = st.session_state.main_navigation

if page == "MACD Cross Over Movement":
    st.markdown("""<div class="hero"><h1>📉 MACD Cross Over <span>Movement</span></h1><p>A dedicated workspace for identifying and analysing MACD line / signal line crossovers.</p></div>""", unsafe_allow_html=True)
    st.info("This navigation page is set up. The MACD crossover analysis module has not yet been implemented in this version.")
    st.markdown("### Planned analysis workspace")
    macd_cols = st.columns(3)
    with macd_cols[0]:
        st.markdown('<div class="kpi"><div class="kpi-label">Signal detection</div><div class="kpi-value">Bullish & Bearish</div><div class="small-muted">MACD / signal-line crossover</div></div>', unsafe_allow_html=True)
    with macd_cols[1]:
        st.markdown('<div class="kpi"><div class="kpi-label">Market universe</div><div class="kpi-value">NSE stocks</div><div class="small-muted">Configurable symbol list</div></div>', unsafe_allow_html=True)
    with macd_cols[2]:
        st.markdown('<div class="kpi"><div class="kpi-label">Analysis</div><div class="kpi-value">Trend & momentum</div><div class="small-muted">Crossover date, price and follow-through</div></div>', unsafe_allow_html=True)
    st.caption("Select **Top Gainer Intelligence** in the left navigation to return to the existing dashboard.")
    st.stop()

if page in ["Dashboard", "Watchlist", "Reports", "Settings"]:
    page_copy = {
        "Dashboard": ("Market Dashboard", "Your consolidated market overview will appear here."),
        "Watchlist": ("Watchlist", "A dedicated stock watchlist workspace is ready for implementation."),
        "Reports": ("Reports", "Historical occurrence and performance reports will appear here."),
        "Settings": ("Settings", "Application preferences and data-source settings will appear here.")
    }
    page_title, page_description = page_copy[page]
    st.markdown(
        f'<div class="hero"><h1>📊 <span>{page_title}</span></h1><p>{page_description}</p></div>',
        unsafe_allow_html=True
    )
    st.info(f"The {page} menu is connected. Its detailed functionality has not yet been implemented.")
    st.caption("Choose **Top Gainer Intelligence** from the left navigation to return to the current stock analysis dashboard.")
    st.stop()

APP_DIR = Path(__file__).resolve().parent

# Placeholders reserve the exact top-to-bottom order while data is parsed below.
header_slot = st.empty()
formula_slot = st.empty()

with st.expander("🗃️  Data Source", expanded=True):
    upload_cols = st.columns(2, gap="medium")
    with upload_cols[0]:
        uploaded = st.file_uploader("Upload Backtest Top Gainers.csv", type=["csv"], key="main_csv_upload")
        st.caption("Supported format: CSV (Max 200MB)")
    with upload_cols[1]:
        svg_audit_upload = st.file_uploader("Optional: Upload SVG audit CSV", type=["csv"], key="audit_csv")
        st.caption("Supported format: CSV (Max 200MB)")

filters_slot = st.empty()
guide_slot = st.empty()
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
        st.caption("✓ CSV loaded from the application folder.")
    else:
        st.warning("Upload your `Backtest Top Gainers.csv` using the Data source section above to begin.")
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
    st.warning(f"Could not load SVG audit: {exc}")

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
    audit_status_message = (
        "SVG audit CSV not loaded. Place Backtest_Top_Gainers_CSV_vs_SVG_Audit.csv beside app.py "
        "or upload it above to use SVG timeline dates as the final source."
    )
else:
    audit_status_message = "SVG timeline dates are active and are used as the final occurrence dates."

valid_dates = df["OccurrenceDateTime"].dropna()
date_min, date_max = valid_dates.min().date(), valid_dates.max().date()

# Premium market header. The timestamp is rendered in India Standard Time.
now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
header_date = now_ist.strftime("%A, %d %b %Y")
header_time = now_ist.strftime("%I:%M %p IST")
header_stocks = int(df.loc[df["OccurrenceDateTime"].notna(), "Symbol"].nunique())
header_occurrences = int(df["OccurrenceDateTime"].notna().sum())
header_source_loaded = "CSV Loaded" if (uploaded is not None or default_path.exists()) else "No Data"
header_source_note = "SVG timeline active" if audit_df is not None and (df["OccurrenceDateSource"] == "SVG timeline").any() else "Using available occurrence dates"
header_art = "data:image/png;base64,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"


# Restore the premium Top Gainer header and live India clock ABOVE Data Source.
# header_slot was created before the upload panel so this renders in the intended top position.
header_slot.markdown(f"""
<div class="market-hero" style="background-image:linear-gradient(90deg,rgba(3,22,42,.96) 0%,rgba(3,22,42,.76) 54%,rgba(3,22,42,.42) 100%),url('{header_art}');background-position:center, right center;background-size:cover, auto 175%;background-repeat:no-repeat;">
  <div class="market-hero-content">
    <div class="market-hero-title">📊 Top Gainer <span>Intelligence</span></div>
    <p class="market-hero-subtitle">Explore recurring stocks, inspect every recorded occurrence, and click a date to view its historical price change.</p>
  </div>
  <div class="market-clock">
    <div class="market-clock-icon">▦</div>
    <div><div class="market-clock-date">{header_date}</div><div class="market-clock-time">{header_time}</div></div>
  </div>
</div>
<div class="market-kpi-grid">
  <div class="market-kpi"><div class="market-kpi-icon">▥</div><div class="market-kpi-copy"><div class="market-kpi-label">Total Stocks</div><div class="market-kpi-value">{header_stocks:,}</div><div class="market-kpi-note">from uploaded CSV</div></div></div>
  <div class="market-kpi"><div class="market-kpi-icon pink">▦</div><div class="market-kpi-copy"><div class="market-kpi-label">Total Occurrences</div><div class="market-kpi-value">{header_occurrences:,}</div><div class="market-kpi-note">across all stocks</div></div></div>
  <div class="market-kpi"><div class="market-kpi-icon green">↗</div><div class="market-kpi-copy"><div class="market-kpi-label">Avg. Daily Change</div><div class="market-kpi-value positive">{f'{pd.to_numeric(df.get("DailyChangePct", pd.Series(dtype=float)), errors="coerce").dropna().mean():+.2f}%' if "DailyChangePct" in df.columns and pd.to_numeric(df["DailyChangePct"], errors="coerce").notna().any() else '—'}</div><div class="market-kpi-note">of available occurrences</div></div></div>
  <div class="market-kpi"><div class="market-kpi-icon blue">◉</div><div class="market-kpi-copy"><div class="market-kpi-label">Data Status</div><div class="market-kpi-value status">● {header_source_loaded}</div><div class="market-kpi-note">{header_source_note}</div></div></div>
</div>
""", unsafe_allow_html=True)

formula_slot.markdown(f"""
<div class="info-banner"><span style="font-size:1.1rem">💡</span><div><strong>How percentage change is calculated:</strong> Daily change = (selected date close − previous trading-day close) ÷ previous trading-day close × 100. Intraday change = (selected date close − selected date open) ÷ selected date open × 100. SVG timeline dates are preferred for occurrence display; OHLC lookup uses the available audit/source data.</div></div>
""", unsafe_allow_html=True)

sector_options = ["All Sectors"] + sorted(df["Sector"].dropna().astype(str).unique().tolist())
cap_options = ["All Market Caps"] + sorted(df["Marketcapname"].dropna().astype(str).unique().tolist())

def _reset_market_filters(start_date, end_date):
    st.session_state["filter_date_range"] = (start_date, end_date)
    st.session_state["filter_sector"] = "All Sectors"
    st.session_state["filter_market_cap"] = "All Market Caps"

with filters_slot.container():
    with st.expander("▽  Filters", expanded=True):
        filter_cols = st.columns([1.65, 1.05, 1.05, .72, .90], gap="small")
        with filter_cols[0]:
            date_range = st.date_input(
                "Occurrence date range", value=(date_min, date_max),
                min_value=date_min, max_value=date_max, key="filter_date_range"
            )
        with filter_cols[1]:
            sector_filter = st.selectbox("Sector", sector_options, key="filter_sector")
        with filter_cols[2]:
            cap_filter = st.selectbox("Market Cap", cap_options, key="filter_market_cap")
        with filter_cols[3]:
            st.markdown('<div style="height:1.25rem"></div>', unsafe_allow_html=True)
            st.button(
                "↺ Reset", key="reset_market_filters",
                on_click=_reset_market_filters, args=(date_min, date_max),
                use_container_width=True
            )
        with filter_cols[4]:
            st.markdown('<div style="height:1.25rem"></div>', unsafe_allow_html=True)
            st.button("⚑ Apply Filters", key="apply_market_filters", type="primary", use_container_width=True)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    date_start, date_end = date_range
else:
    date_start, date_end = date_min, date_max

filtered = df.dropna(subset=["OccurrenceDateTime"]).copy()
filtered = filtered[(filtered["OccurrenceDate"] >= date_start) & (filtered["OccurrenceDate"] <= date_end)]
if sector_filter != "All Sectors":
    filtered = filtered[filtered["Sector"] == sector_filter]
if cap_filter != "All Market Caps":
    filtered = filtered[filtered["Marketcapname"] == cap_filter]

if filtered.empty:
    st.warning("No occurrences match the selected filters.")
    st.stop()

with guide_slot.container():
    st.markdown("""
    <div class="color-guide">
      <div class="guide-title">▥  % Change Color Guide <span style="font-weight:450;color:#8DA9C7">(Based on absolute value)</span></div>
      <div class="guide-grid">
        <div class="guide-item guide-blue">● &lt; 5%<span>Low Movement</span></div>
        <div class="guide-item guide-green">● 5% – &lt; 7%<span>Moderate Movement</span></div>
        <div class="guide-item guide-yellow">● 7% – &lt; 9%<span>High Movement</span></div>
        <div class="guide-item guide-orange">● 9% – 11%<span>Very High Movement</span></div>
        <div class="guide-item guide-red">● &gt; 11%<span>Extreme Movement</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

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
.top-header {display:flex;align-items:center;justify-content:space-between;gap:18px;padding:17px 19px;border:1px solid #173D5D;border-radius:17px;background:linear-gradient(115deg,#0A223C,#071A30);box-shadow:0 6px 22px rgba(0,0,0,.12);margin:8px 0 16px;}
.stock-identity {display:flex;align-items:center;gap:13px;min-width:220px;}
.stock-mark {width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1BC7C2,#22E49B);color:#06243B;font-size:16px;font-weight:850;}
.stock-title {font-size:23px;font-weight:850;color:#F3F7FF;line-height:1.2;}
.stock-subtitle {font-size:12px;color:#9FB6D0;margin-top:5px;}
.occ-kpi {min-width:140px;padding:9px 15px;text-align:left;border-radius:12px;background:rgba(224,55,91,.10);border:1px solid rgba(224,55,91,.32);}
.occ-kpi-label {font-size:11px;color:#F3A4B3;font-weight:650;letter-spacing:.03em;}
.occ-kpi-value {font-size:30px;line-height:1.15;font-weight:850;color:#FF5871;}
.color-guide {border:1px solid #173D5D;border-radius:14px;padding:12px 13px;background:#081E35;margin:.6rem 0 1rem;}
.guide-title {font-size:14px;font-weight:750;color:#B9E4FF;margin:0 0 9px 4px;}
.guide-grid {display:grid;grid-template-columns:repeat(5,minmax(80px,1fr));gap:8px;}
.guide-item {padding:9px 5px;text-align:center;border-radius:9px;font-size:12px;font-weight:800;border:1px solid transparent;}
.guide-item span {display:block;font-weight:500;margin-top:3px;font-size:11px;opacity:.9;}
.guide-blue {background:#0E3A62;color:#6AB8FF;border-color:#175487;}
.guide-green {background:#073C3A;color:#37E6A0;border-color:#08745F;}
.guide-yellow {background:#3D3513;color:#FFD54F;border-color:#7C6818;}
.guide-orange {background:#48271C;color:#FF9A55;border-color:#8D492B;}
.guide-red {background:#481E30;color:#FF5B76;border-color:#8B2947;}
.section-title {font-size:19px;font-weight:800;color:#ECF5FF;margin:.45rem 0 .35rem;}
.occ-summary {padding:15px 17px;border:1px solid #173D5D;border-radius:15px;background:#081E35;margin-top:14px;}
.occ-summary-title {font-size:15px;font-weight:800;color:#C8E7FF;margin-bottom:12px;}
.summary-count {font-size:25px;font-weight:850;line-height:1.1;margin-top:4px;}
.summary-label {font-size:12px;color:#8DA9C7;}
.summary-dot {display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;}

.occurrence-tile {
  position:relative;display:flex;align-items:center;gap:clamp(9px,1.35vw,20px);
  width:100%;min-height:78px;box-sizing:border-box;padding:12px 18px;
  border-radius:14px;border:1px solid #164D5A;
  background:linear-gradient(105deg,#073044 0%,#06283A 48%,#082D3D 100%);
  box-shadow:0 4px 12px rgba(0,0,0,.13), inset 0 1px 0 rgba(98,225,222,.06);
  margin:0 0 0.18rem 0;overflow:hidden;
}
.occurrence-tile:before {
  content:"";position:absolute;left:0;top:10px;bottom:10px;width:2px;
  border-radius:2px;background:linear-gradient(180deg,#2AE2D4,#19B88F);opacity:.8;
}
.occurrence-number {
  flex:0 0 42px;width:42px;height:42px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  border:2px solid #20C9B9;color:#E9FFFF;
  background:radial-gradient(circle at 50% 45%,rgba(34,211,201,.16),rgba(4,29,45,.8));
  box-shadow:0 0 0 3px rgba(26,204,190,.07),inset 0 0 12px rgba(24,207,193,.08);
  font-size:20px;font-weight:750;line-height:1;
}
.occurrence-calendar {flex:0 0 32px;font-size:25px;line-height:1;text-align:center;filter:saturate(1.1);}
.occurrence-date-block {min-width:0;flex:1;display:flex;flex-direction:column;gap:5px;}
.occurrence-date {color:#E6F1FC;font-size:clamp(12px,1.25vw,17px);font-weight:650;letter-spacing:.01em;line-height:1.25;white-space:nowrap;}
.occurrence-separator {color:#7D9BB3;padding:0 3px;}
.occurrence-weekday {color:#8DAEC6;font-size:clamp(11px,1.05vw,15px);line-height:1.1;font-weight:500;}
.occurrence-change {flex:0 0 auto;min-width:84px;text-align:right;font-size:clamp(20px,2.2vw,30px);font-weight:850;letter-spacing:-.035em;white-space:nowrap;text-shadow:0 0 12px rgba(36,232,160,.12);}
div[class*="st-key-occ_"] div[data-testid="stButton"] {position:relative;margin-top:-79px;height:78px;z-index:3;}
div[class*="st-key-occ_"] div[data-testid="stButton"] button {
  height:78px !important;min-height:78px !important;width:100% !important;
  opacity:0 !important;position:relative !important;z-index:4 !important;
  padding:0 !important;margin:0 !important;border:0 !important;
  background:transparent !important;box-shadow:none !important;cursor:pointer !important;
}
div[class*="st-key-occ_"] div[data-testid="stButton"] button p {font-size:1px !important;color:transparent !important;}
div[class*="st-key-occ_"] div[data-testid="stButton"] button:hover {transform:none !important;box-shadow:none !important;}
div[class*="st-key-occ_"] {margin-bottom:7px;}
@media(max-width:800px) {
  .occurrence-tile {min-height:72px;padding:10px 11px;gap:8px;}
  .occurrence-number {flex-basis:34px;width:34px;height:34px;font-size:16px;}
  .occurrence-calendar {flex-basis:24px;font-size:20px;}
  .occurrence-date {font-size:11px;white-space:normal;}
  .occurrence-weekday {font-size:11px;}
  .occurrence-change {min-width:65px;font-size:18px;}
  div[class*="st-key-occ_"] div[data-testid="stButton"] {margin-top:-73px;height:72px;}
  div[class*="st-key-occ_"] div[data-testid="stButton"] button {height:72px !important;min-height:72px !important;}
}

@media(max-width:1000px){.top-header{flex-wrap:wrap}.color-guide{min-width:100%}.guide-grid{grid-template-columns:repeat(3,minmax(80px,1fr));}}
</style>
""", unsafe_allow_html=True)

# ---- Compact stock summary + occurrence cards, matching the supplied reference ----
stock_options = sorted(filtered["Symbol"].dropna().unique().tolist())
if "focused_stock" not in st.session_state or st.session_state.focused_stock not in stock_options:
    current_selected = st.session_state.get("selected_occurrence")
    preferred = current_selected[0] if current_selected and current_selected[0] in stock_options else None
    st.session_state.focused_stock = preferred or stock_options[0]

# Keep the screenshot's clean stock-summary row free of a separate dropdown.
# Users can focus a stock through the Stock Search filter above.
focused_stock = st.session_state.focused_stock

stock_rows = filtered[filtered["Symbol"] == focused_stock].copy()
occurrence_dates = [
    pd.Timestamp(value).strftime("%Y-%m-%d")
    for value in stock_rows["OccurrenceDateTime"]
]
pct_by_date = fetch_occurrence_percentages(focused_stock, occurrence_dates)
stock_rows["DateISO"] = stock_rows["OccurrenceDateTime"].dt.strftime("%Y-%m-%d")
stock_rows["DailyChangePct"] = stock_rows["DateISO"].map(pct_by_date)

occurrence_count = len(stock_rows)
stock_meta = stock_rows.iloc[0]
sector_label = str(stock_meta.get("Sector", "—"))
cap_label = str(stock_meta.get("Marketcapname", "—"))
valid_pct = pd.to_numeric(stock_rows["DailyChangePct"], errors="coerce").dropna()
avg_change_text = f"{valid_pct.mean():+.2f}%" if not valid_pct.empty else "N/A"

def _sparkline_svg(values):
    vals = pd.to_numeric(pd.Series(values), errors="coerce").dropna().tail(18).tolist()
    if len(vals) < 2:
        vals = [0, 0]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    coords = []
    for i, val in enumerate(vals):
        x = 3 + i * (94 / max(1, len(vals) - 1))
        y = 25 - ((val - lo) / span) * 19
        coords.append(f"{x:.1f},{y:.1f}")
    stroke = "#28E0A0" if vals[-1] >= vals[0] else "#FF6078"
    points = " ".join(coords)
    return (
        f'<svg viewBox="0 0 100 30" width="100%" height="34" role="img" aria-label="Recent daily change sparkline">'
        f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{coords[-1].split(",")[0]}" cy="{coords[-1].split(",")[1]}" r="2.5" fill="{stroke}"/>'
        f'</svg>'
    )

sparkline = _sparkline_svg(valid_pct)
head_cols = st.columns([3.3, 1.0, 1.15, 1.0], gap="small")
with head_cols[0]:
    st.markdown(
        f'<div class="stock-identity">'
        f'<div class="stock-mark">{focused_stock[:2]}</div>'
        f'<div><div class="stock-title">{focused_stock}</div>'
        f'<div class="stock-subtitle">{sector_label} · {cap_label} · NSE</div></div></div>',
        unsafe_allow_html=True,
    )
with head_cols[1]:
    st.markdown(
        f'<div class="occ-kpi"><div class="occ-kpi-label">TOTAL OCCURRENCES</div>'
        f'<div class="occ-kpi-value">{occurrence_count}</div></div>',
        unsafe_allow_html=True,
    )
with head_cols[2]:
    st.markdown(
        f'<div style="padding:7px 5px 0;min-width:80px;">{sparkline}'
        f'<div style="font-size:10px;color:#91B3D0;text-align:center;">Daily change trend</div></div>',
        unsafe_allow_html=True,
    )
with head_cols[3]:
    if st.button("View Details  ›", key="view_stock_details", use_container_width=True):
        latest = stock_rows.sort_values("OccurrenceDateTime").iloc[-1]
        st.session_state.selected_occurrence = (
            focused_stock,
            pd.Timestamp(latest["OccurrenceDateTime"]).strftime("%Y-%m-%d"),
            pd.Timestamp(latest["OccurrenceDateTime"]).strftime("%I:%M %p"),
        )
        st.session_state.show_price_dialog = True
        st.rerun()

# Occurrence toolbar: title/count at left, compact sort control at right.
occ_toolbar_left, occ_toolbar_right = st.columns([3.2, 1.25], gap="small")
with occ_toolbar_left:
    st.markdown(
        f'<div class="section-title" style="margin:.2rem 0 .1rem;">▦ Occurrences '
        f'<span style="color:#28E0A0;">({occurrence_count})</span></div>',
        unsafe_allow_html=True,
    )
with occ_toolbar_right:
    sort_choice = st.selectbox(
        "Sort occurrences",
        ["Date (ascending)", "Date (descending)", "% change (highest first)", "% change (lowest first)"],
        index=0,
        key="occurrence_sort_choice",
        label_visibility="collapsed",
    )

if sort_choice == "Date (descending)":
    stock_rows = stock_rows.sort_values("OccurrenceDateTime", ascending=False)
elif sort_choice == "% change (highest first)":
    stock_rows = stock_rows.sort_values("DailyChangePct", ascending=False, na_position="last")
elif sort_choice == "% change (lowest first)":
    stock_rows = stock_rows.sort_values("DailyChangePct", ascending=True, na_position="last")
else:
    stock_rows = stock_rows.sort_values("OccurrenceDateTime", ascending=True)

def color_band(pct):
    if pct is None or pd.isna(pct):
        return ("#10263B", "#A9BDD2", "Unavailable", "#24435D")
    magnitude = abs(float(pct))
    if magnitude < 5:
        return ("#0E3151", "#75BDFF", "<5%", "#1B5B88")
    if magnitude < 7:
        return ("#073A38", "#39E5A0", "5–<7%", "#08745F")
    if magnitude < 9:
        return ("#3A3215", "#FFD34F", "7–<9%", "#80691A")
    if magnitude <= 11:
        return ("#46271D", "#FF9B5C", "9–11%", "#8A4B2C")
    return ("#471E30", "#FF5D79", ">11%", "#8B2A48")

# Wide, premium occurrence tiles matching the supplied reference image.
# Two columns provide room for the outlined index, calendar, stacked date/weekday,
# and right-aligned percentage value.
per_row = 2
for row_start in range(0, len(stock_rows), per_row):
    batch = stock_rows.iloc[row_start:row_start + per_row]
    cols = st.columns(per_row, gap="small")
    for j, (_, occ) in enumerate(batch.iterrows()):
        occurrence_dt = pd.Timestamp(occ["OccurrenceDateTime"])
        date_iso = occurrence_dt.strftime("%Y-%m-%d")
        time_text = occurrence_dt.strftime("%I:%M %p")
        pct = occ["DailyChangePct"]
        pct_text = f"{float(pct):+.2f}%" if pd.notna(pct) else "N/A"
        bg, fg, band, border_color = color_band(pct)
        ordinal = row_start + j + 1
        weekday = occurrence_dt.strftime("%a")
        selected_key = (focused_stock, date_iso, time_text)
        is_selected = st.session_state.selected_occurrence == selected_key
        key = f"occ_{re.sub(r'[^A-Za-z0-9_-]', '_', focused_stock)}_{occurrence_dt.strftime('%Y%m%d_%H%M')}_{row_start}_{j}"
        pct_color = "#24E8A0" if pd.notna(pct) and float(pct) >= 0 else "#FF667C"
        selected_shadow = "0 0 0 1px #26DFA0 inset, 0 0 18px rgba(38,223,160,.12)" if is_selected else "0 4px 12px rgba(0,0,0,.13)"
        card_html = f"""
        <div class="occurrence-tile" style="
            --tile-bg:{bg};--tile-border:{border_color};--tile-shadow:{selected_shadow};
            ">
          <div class="occurrence-number">{ordinal}</div>
          <div class="occurrence-calendar" aria-hidden="true">🗓️</div>
          <div class="occurrence-date-block">
            <div class="occurrence-date">{occurrence_dt.strftime('%d %b %Y')} <span class="occurrence-separator">•</span> {time_text}</div>
            <div class="occurrence-weekday">{weekday}</div>
          </div>
          <div class="occurrence-change" style="color:{pct_color};">{pct_text}</div>
        </div>
        """
        with cols[j].container(key=key):
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(
                "Open occurrence",
                key=f"{key}_click",
                use_container_width=True,
                help=f"Daily change: {pct_text} · Band: {band}. Click to inspect selected and previous trading-day OHLC.",
            ):
                st.session_state.selected_occurrence = selected_key
                st.session_state.show_price_dialog = True
                st.rerun()

with st.expander("🔎 Verify CSV occurrences against SVG timeline audit", expanded=False):
    if audit_df is None:
        st.info(
            "Optional audit not loaded. To cross-check stock counts against the attached SVG timeline, "
            "place `Backtest_Top_Gainers_CSV_vs_SVG_Audit.csv` beside app.py or upload it in the Data source section above."
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

@st.dialog("📊 Historical price-change analysis", width="medium")
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
