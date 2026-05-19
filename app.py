import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import io

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCOUNTS = {
    "web": {"label": "🌐 Website",    "account_id": "292247905"},
    "app": {"label": "📱 Mobile App", "account_id": "248305344"},
}
WINDSOR_KEY  = st.secrets.get("WINDSOR_API_KEY", "")
WINDSOR_BASE = "https://connectors.windsor.ai/googleanalytics4"

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def _dates(preset, custom_from=None, custom_to=None):
    from datetime import date, timedelta
    if custom_from and custom_to:
        return str(custom_from), str(custom_to)
    t = date.today()
    m = {
        "last_7d":    (t-timedelta(7),  t-timedelta(1)),
        "last_14d":   (t-timedelta(14), t-timedelta(1)),
        "last_30d":   (t-timedelta(30), t-timedelta(1)),
        "last_90d":   (t-timedelta(90), t-timedelta(1)),
        "this_month": (t.replace(day=1), t-timedelta(1)),
        "last_month": ((t.replace(day=1)-__import__('datetime').timedelta(1)).replace(day=1),
                       t.replace(day=1)-__import__('datetime').timedelta(1)),
    }
    df, dt = m.get(preset, (t-timedelta(30), t-timedelta(1)))
    return str(df), str(dt)

@st.cache_data(ttl=300, show_spinner=False)
def _fetch(account_id, fields_key, date_from, date_to):
    """Cached fetch — keyed by account_id + fields tuple + dates."""
    if not WINDSOR_KEY:
        return pd.DataFrame()
    fields = list(fields_key)
    params = {
        "api_key":    WINDSOR_KEY,
        "fields":     ",".join(fields),
        "date_from":  date_from,
        "date_to":    date_to,
        "account_id": account_id,
    }
    try:
        r = requests.get(WINDSOR_BASE, params=params, timeout=40)
        r.raise_for_status()
        data = r.json()
        rows = data["data"] if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        for c in df.columns:
            try: df[c] = pd.to_numeric(df[c])
            except: pass
        return df
    except Exception as e:
        st.warning(f"Windsor ({account_id}): {e}")
        return pd.DataFrame()

def _are_identical(df_w, df_a, check_cols=None):
    """Return True if web and app dataframes have identical numeric totals — means App not connected."""
    if df_w.empty or df_a.empty:
        return False
    cols = check_cols or [c for c in ["sessions","purchase_revenue","transactions"] if c in df_w.columns and c in df_a.columns]
    if not cols:
        return False
    for c in cols:
        w_tot = df_w[c].sum() if c in df_w.columns else 0
        a_tot = df_a[c].sum() if c in df_a.columns else 0
        if abs(w_tot - a_tot) > 0.01:
            return False
    return True

def load_source(source_key, fields, date_from, date_to):
    """Load data for a single source (web or app)."""
    acc_id = ACCOUNTS[source_key]["account_id"]
    df = _fetch(acc_id, tuple(fields), date_from, date_to)
    if not df.empty:
        df["_src"] = source_key
    return df

def load_combined(fields, d_from, d_to):
    """
    Load from web + app based on sidebar filter.
    If 'all': fetch both, detect if App is returning same data as Web,
    show warning and use Web only in that case.
    """
    if source_filter == "web":
        df = load_source("web", fields, d_from, d_to)
        return df

    elif source_filter == "app":
        df = load_source("app", fields, d_from, d_to)
        if df.empty:
            st.info("📱 App data not available — account may not be connected in Windsor yet.")
        return df

    else:  # all
        df_w = load_source("web", fields, d_from, d_to)
        df_a = load_source("app", fields, d_from, d_to)

        if _are_identical(df_w, df_a):
            # App not connected — silently use web only, flag set globally
            st.session_state["_app_not_connected"] = True
            return df_w
        else:
            st.session_state["_app_not_connected"] = False
            frames = []
            if not df_w.empty: frames.append(df_w)
            if not df_a.empty: frames.append(df_a)
            if not frames: return pd.DataFrame()
            combined = pd.concat(frames, ignore_index=True)
            for c in combined.columns:
                if c not in ["_src"] and combined[c].dtype == object:
                    try: combined[c] = pd.to_numeric(combined[c])
                    except: pass
            return combined

def safe_num(v, d=0):
    try: return float(v) if v is not None else d
    except: return d

def fmt_c(v, dec=1):
    v = safe_num(v)
    if v >= 1e6: return f"{v/1e6:.{dec}f}M ج"
    if v >= 1e3: return f"{v/1e3:.{dec}f}K ج"
    return f"{v:,.0f} ج"

def fmt_n(v):
    v = safe_num(v)
    if v >= 1e6: return f"{v/1e6:.1f}M"
    if v >= 1e3: return f"{v/1e3:.1f}K"
    return f"{v:,.0f}"

def fmt_p(v, d=1): return f"{safe_num(v):.{d}f}%"

def export_btn(df, filename):
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Export CSV", buf.getvalue(), filename, "text/csv", key=filename)

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans Arabic',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:1rem 2rem 2rem;max-width:1400px}
section[data-testid="stSidebar"]{background:#F5F7FA;border-right:1px solid #E2E6EA}
.kpi{background:#fff;border:1px solid #E2E6EA;border-radius:12px;padding:14px 16px;position:relative;overflow:hidden;transition:border-color .2s}
.kpi:hover{border-color:#3266AD}
.kpi-a{position:absolute;top:0;left:0;right:0;height:3px;border-radius:12px 12px 0 0}
.kpi-l{font-size:10px;color:#73726C;font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}
.kpi-v{font-size:22px;font-weight:600;color:#1A1A2E;line-height:1;margin-bottom:4px}
.kpi-s{font-size:11px}.kpi-b{font-size:10px;color:#9A9A8E;margin-top:2px}
.up{color:#1D9E75}.dn{color:#D85A30}.wn{color:#EF9F27}.nu{color:#888780}
.sh{display:flex;align-items:center;gap:9px;padding:5px 0 9px;border-bottom:1px solid #E2E6EA;margin-bottom:14px}
.sd{width:8px;height:8px;border-radius:50%}
.st_{font-size:14px;font-weight:600;color:#1A1A2E}
.ss_{font-size:11px;color:#73726C;margin-left:auto}
.tb{display:flex;align-items:center;justify-content:space-between;padding:8px 0 14px;border-bottom:1px solid #E2E6EA;margin-bottom:18px}
.bn_{font-size:20px;font-weight:700;color:#1A1A2E}.bn_ span{color:#3266AD}
.lv{display:inline-flex;align-items:center;gap:6px;background:#EAF7F2;border:1px solid rgba(29,158,117,.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#1D9E75}
.ld{width:6px;height:6px;border-radius:50%;background:#1D9E75;animation:blink 2s infinite;display:inline-block}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.src-web{background:#E6F1FB;color:#185FA5;padding:2px 7px;border-radius:6px;font-size:10px;font-weight:600}
.src-app{background:#EAF7F2;color:#0D6B4F;padding:2px 7px;border-radius:6px;font-size:10px;font-weight:600}
.br_{display:flex;align-items:center;gap:9px;margin-bottom:8px}
.bn2{font-size:11px;color:#73726C;min-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bt_{flex:1;height:7px;background:#F0F2F5;border-radius:4px;overflow:hidden}
.bf_{height:100%;border-radius:4px}
.bv_{font-size:11px;color:#1A1A2E;min-width:65px;text-align:right;font-weight:500}
table{width:100%;border-collapse:collapse;font-size:11.5px}
th{background:#F5F7FA;color:#73726C;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.05em;padding:7px 9px;border-bottom:1px solid #E2E6EA;text-align:left}
td{padding:8px 9px;border-bottom:1px solid #F0F2F5;color:#1A1A2E;vertical-align:middle}
tr:hover td{background:rgba(50,102,173,.04)}
.b{display:inline-block;font-size:10px;padding:2px 7px;border-radius:9px;font-weight:600}
.bg_{background:rgba(29,158,117,.15);color:#1D9E75}
.br2{background:rgba(216,90,48,.15);color:#D85A30}
.ba_{background:rgba(239,159,39,.15);color:#EF9F27}
.bb_{background:rgba(50,102,173,.15);color:#3266AD}
.bp_{background:rgba(127,119,221,.15);color:#7F77DD}
.bx_{background:rgba(136,135,128,.15);color:#888780}
.ic{border-radius:8px;padding:11px 13px;margin-bottom:7px;font-size:12px;line-height:1.6;border-left:4px solid}
.ir{background:#FEF3EF;border-color:#D85A30;color:#A33A15}
.iw{background:#FEF9EF;border-color:#EF9F27;color:#8A5A10}
.ig{background:#EAF7F2;border-color:#1D9E75;color:#0D6B4F}
.ib{background:#EAF0FB;border-color:#3266AD;color:#1A4A8A}
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#73726C", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
)

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="padding:14px 0 18px">
    <div style="font-size:17px;font-weight:700;color:#1A1A2E"><span style="color:#3266AD">●</span> Analytics</div>
    <div style="font-size:11px;color:#73726C;margin-top:3px">Unified Dashboard</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px;font-weight:600;color:#73726C;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">Data Source</div>', unsafe_allow_html=True)
    source_filter = st.radio("", ["all","web","app"],
        format_func=lambda x: {"all":"🌐📱 All (Web + App)","web":"🌐 Website Only","app":"📱 App Only"}.get(x,x),
        label_visibility="collapsed", key="source_filter")

    st.markdown("---")
    preset = st.selectbox("", ["last_30d","last_7d","last_14d","last_90d","this_month","last_month","custom"],
        format_func=lambda x: {"last_7d":"Last 7 Days","last_14d":"Last 14 Days","last_30d":"Last 30 Days",
        "last_90d":"Last 90 Days","this_month":"This Month","last_month":"Last Month","custom":"Custom Range"}.get(x,x),
        label_visibility="collapsed")

    custom_from, custom_to = None, None
    if preset == "custom":
        from datetime import date, timedelta
        custom_from = st.date_input("From", date.today()-timedelta(30))
        custom_to   = st.date_input("To",   date.today()-timedelta(1))

    d_from, d_to = _dates(preset, custom_from, custom_to)
    st.markdown("---")

    tab = st.radio("", ["📊 Overview","🔽 Funnel","📡 Traffic","📱 Devices","🛒 E-Commerce","🎯 Campaigns","👥 Users","💡 Insights"],
        label_visibility="collapsed")
    st.markdown("---")

    if WINDSOR_KEY:
        st.success("✅ Connected", icon="🔒")
    else:
        st.error("⚠️ Add WINDSOR_API_KEY to Secrets")

    st.markdown(f'<div style="font-size:10px;color:#9A9A8E;line-height:1.7">'
                f'{"🌐📱 Web + App" if source_filter=="all" else "🌐 Web Only" if source_filter=="web" else "📱 App Only"}<br>'
                f'{d_from} → {d_to}<br><span style="color:#1D9E75">● Live</span> · Windsor GA4</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════
src_label = {"all":"Web + App","web":"Website","app":"Mobile App"}.get(source_filter,"")
st.markdown(f"""<div class="tb">
  <div class="bn_"><span>Analytics</span> Dashboard
    <span style="font-size:13px;font-weight:400;color:#73726C;margin-left:10px">· {src_label}</span>
  </div>
  <div class="lv"><span class="ld"></span> Live · GA4 · Windsor</div>
</div>""", unsafe_allow_html=True)

if not WINDSOR_KEY:
    st.info("🔑 Add WINDSOR_API_KEY to Streamlit Secrets to load data.")
    st.stop()

# ══════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════
def kpi(l, v, s, sc, sub="", c="#3266AD"):
    return f"""<div class="kpi"><div class="kpi-a" style="background:{c}"></div>
    <div class="kpi-l">{l}</div><div class="kpi-v">{v}</div>
    <div class="kpi-s {sc}">{s}</div>
    {'<div class="kpi-b">'+sub+'</div>' if sub else ''}</div>"""

def sh(t, s="", c="#3266AD"):
    return f"""<div class="sh"><div class="sd" style="background:{c}"></div>
    <div class="st_">{t}</div>{'<div class="ss_">'+s+'</div>' if s else ''}</div>"""

def bar(n, p, c, v):
    return f"""<div class="br_"><div class="bn2">{n}</div>
    <div class="bt_"><div class="bf_" style="width:{max(p,1)}%;background:{c}"></div></div>
    <div class="bv_">{v}</div></div>"""

def ins(icon, title, body, cls):
    return f'<div class="ic {cls}"><b>{icon} {title}</b><br/>{body}</div>'

COLORS = ["#3266AD","#378ADD","#85B7EB","#1D9E75","#5DCAA5","#EF9F27","#7F77DD","#D85A30","#888780","#B5D4F4"]

# ══════════════════════════════════════════════════════════════
# LOAD MAIN DATA
# ══════════════════════════════════════════════════════════════
if "_app_not_connected" not in st.session_state:
    st.session_state["_app_not_connected"] = False

with st.spinner("⏳ Loading data..."):
    df_ov1 = load_combined(["date","sessions","active_users","bounce_rate","average_session_duration"], d_from, d_to)
    df_ov2 = load_combined(["date","purchase_revenue","transactions","add_to_carts","checkouts"], d_from, d_to)

# Show App warning banner once if detected
if source_filter == "all" and st.session_state.get("_app_not_connected"):
    st.warning("⚠️ **App data not connected yet in Windsor** — showing Web data only. Connect account `248305344` at [onboard.windsor.ai](https://onboard.windsor.ai?datasource=googleanalytics4) to see App data separately.", icon="📱")

# Merge overview
if not df_ov1.empty and not df_ov2.empty:
    try:
        merge_keys = ["date","_src"] if "_src" in df_ov1.columns and "_src" in df_ov2.columns else ["date"]
        df_ov = pd.merge(df_ov1, df_ov2, on=merge_keys, how="outer")
    except: df_ov = df_ov1
elif not df_ov1.empty: df_ov = df_ov1
elif not df_ov2.empty: df_ov = df_ov2
else: df_ov = pd.DataFrame()

if df_ov.empty:
    st.error("❌ No data — check Account IDs and API Key in Secrets.")
    st.stop()

for c in ["sessions","purchase_revenue","transactions","add_to_carts","checkouts","bounce_rate","average_session_duration","active_users"]:
    if c in df_ov.columns: df_ov[c] = df_ov[c].apply(safe_num)

ts   = df_ov["sessions"].sum()              if "sessions"                 in df_ov.columns else 0
tr   = df_ov["purchase_revenue"].sum()      if "purchase_revenue"         in df_ov.columns else 0
to_  = df_ov["transactions"].sum()          if "transactions"             in df_ov.columns else 0
tc   = df_ov["add_to_carts"].sum()          if "add_to_carts"             in df_ov.columns else 0
tck  = df_ov["checkouts"].sum()             if "checkouts"                in df_ov.columns else 0
ab   = df_ov["bounce_rate"].mean()*100      if "bounce_rate"              in df_ov.columns else 0
ase  = df_ov["average_session_duration"].mean() if "average_session_duration" in df_ov.columns else 0
aov_ = tr/to_ if to_>0 else 0
cvr_ = to_/ts*100 if ts>0 else 0
ca   = (1-to_/tc)*100 if tc>0 else 0
am, as_ = int(ase//60), int(ase%60)

# ══════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════
if tab == "📊 Overview":
    st.markdown(sh("Overview","Key Performance Indicators"), unsafe_allow_html=True)

    # Web vs App cards — only show if actually different data
    if source_filter == "all" and "_src" in df_ov.columns and not st.session_state.get("_app_not_connected"):
        df_w = df_ov[df_ov["_src"]=="web"]
        df_a = df_ov[df_ov["_src"]=="app"]
        w_rev = df_w["purchase_revenue"].sum() if not df_w.empty else 0
        a_rev = df_a["purchase_revenue"].sum() if not df_a.empty else 0
        w_ses = df_w["sessions"].sum() if not df_w.empty else 0
        a_ses = df_a["sessions"].sum() if not df_a.empty else 0
        w_ord = df_w["transactions"].sum() if not df_w.empty else 0
        a_ord = df_a["transactions"].sum() if not df_a.empty else 0

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"""<div style="background:#E6F1FB;border-radius:10px;padding:14px 16px;border-left:4px solid #3266AD;margin-bottom:12px">
            <div style="font-size:11px;color:#185FA5;font-weight:600;margin-bottom:8px">🌐 Website</div>
            <div style="display:flex;gap:24px">
              <div><div style="font-size:10px;color:#73726C">Sessions</div><div style="font-size:20px;font-weight:600;color:#1A1A2E">{fmt_n(w_ses)}</div></div>
              <div><div style="font-size:10px;color:#73726C">Revenue</div><div style="font-size:20px;font-weight:600;color:#1D9E75">{fmt_c(w_rev)}</div></div>
              <div><div style="font-size:10px;color:#73726C">Orders</div><div style="font-size:20px;font-weight:600;color:#1A1A2E">{fmt_n(w_ord)}</div></div>
            </div></div>""", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""<div style="background:#EAF7F2;border-radius:10px;padding:14px 16px;border-left:4px solid #1D9E75;margin-bottom:12px">
            <div style="font-size:11px;color:#0D6B4F;font-weight:600;margin-bottom:8px">📱 Mobile App</div>
            <div style="display:flex;gap:24px">
              <div><div style="font-size:10px;color:#73726C">Sessions</div><div style="font-size:20px;font-weight:600;color:#1A1A2E">{fmt_n(a_ses)}</div></div>
              <div><div style="font-size:10px;color:#73726C">Revenue</div><div style="font-size:20px;font-weight:600;color:#1D9E75">{fmt_c(a_rev)}</div></div>
              <div><div style="font-size:10px;color:#73726C">Orders</div><div style="font-size:20px;font-weight:600;color:#1A1A2E">{fmt_n(a_ord)}</div></div>
            </div></div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi("Sessions",fmt_n(ts),"▲ Live","up",c="#3266AD"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Revenue",fmt_c(tr),"▲ Purchase Revenue","up",c="#1D9E75"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Orders",fmt_n(to_),"▲ Transactions","up",c="#1D9E75"), unsafe_allow_html=True)
    with c4: st.markdown(kpi("AOV",fmt_c(aov_,0),"متوسط قيمة الطلب","nu",c="#3266AD"), unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5: st.markdown(kpi("Add to Cart",fmt_n(tc),f"⚠ Abandon {ca:.1f}%","wn",c="#EF9F27"), unsafe_allow_html=True)
    with c6: st.markdown(kpi("Bounce Rate",fmt_p(ab),"▼ Monitor","dn" if ab>50 else "wn",c="#D85A30"), unsafe_allow_html=True)
    with c7: st.markdown(kpi("Avg Session",f"{am}:{as_:02d} min","▲ Engagement","up",c="#7F77DD"), unsafe_allow_html=True)
    with c8: st.markdown(kpi("CVR",fmt_p(cvr_,2),"⚠ Needs work" if cvr_<1 else "▲ Good","wn" if cvr_<1 else "up",c="#D85A30" if cvr_<1 else "#1D9E75"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if "date" in df_ov.columns:
        df_ts = df_ov.copy()
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts = df_ts.dropna(subset=["date"])
        df_ts_agg = df_ts.groupby("date")[["purchase_revenue","transactions","sessions","bounce_rate"]].sum().reset_index()
        df_ts_agg = df_ts_agg.sort_values("date")

        cl, cr = st.columns(2)
        with cl:
            st.markdown(sh("Revenue Over Time","","#1D9E75"), unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y":True}]])
            # If all + both connected, show stacked web/app bars
            if source_filter == "all" and "_src" in df_ts.columns and not st.session_state.get("_app_not_connected"):
                for src, clr in [("web","#3266AD"),("app","#1D9E75")]:
                    d = df_ts[df_ts["_src"]==src].groupby("date")["purchase_revenue"].sum().reset_index()
                    fig.add_trace(go.Bar(x=d["date"],y=d["purchase_revenue"]/1000,name=f"Rev {src.title()}",marker_color=clr,opacity=0.8),secondary_y=False)
            else:
                fig.add_trace(go.Bar(x=df_ts_agg["date"],y=df_ts_agg["purchase_revenue"]/1000,name="Revenue K ج",marker_color="#3266AD",opacity=0.8),secondary_y=False)
            fig.add_trace(go.Scatter(x=df_ts_agg["date"],y=df_ts_agg["transactions"],name="Orders",line=dict(color="#1D9E75",width=2),mode="lines+markers",marker_size=4),secondary_y=True)
            fig.update_layout(**PLOT_LAYOUT,height=250,barmode="stack")
            st.plotly_chart(fig,use_container_width=True)
        with cr:
            st.markdown(sh("Sessions & Bounce","","#D85A30"), unsafe_allow_html=True)
            fig2 = make_subplots(specs=[[{"secondary_y":True}]])
            fig2.add_trace(go.Bar(x=df_ts_agg["date"],y=df_ts_agg["sessions"]/1000,name="Sessions K",marker_color="rgba(50,102,173,0.7)"),secondary_y=False)
            if "bounce_rate" in df_ts_agg.columns:
                fig2.add_trace(go.Scatter(x=df_ts_agg["date"],y=df_ts_agg["bounce_rate"]*100,name="Bounce%",line=dict(color="#D85A30",width=2),fill="tozeroy",fillcolor="rgba(216,90,48,0.08)"),secondary_y=True)
            fig2.update_layout(**PLOT_LAYOUT,height=250)
            st.plotly_chart(fig2,use_container_width=True)

# ══════════════════════════════════════════════════════════════
# FUNNEL
# ══════════════════════════════════════════════════════════════
elif tab == "🔽 Funnel":
    st.markdown(sh("Sales Funnel","Session → Purchase"), unsafe_allow_html=True)

    for label,count,pct,color in [
        ("Sessions",ts,100,"#3266AD"),
        ("Add to Cart",tc,tc/ts*100 if ts else 0,"#378ADD"),
        ("Checkout",tck,tck/ts*100 if ts else 0,"#85B7EB"),
        ("Purchase",to_,cvr_,"#1D9E75"),
    ]:
        bw=max(pct,.5)
        st.markdown(f"""<div style="display:flex;align-items:center;gap:11px;margin-bottom:9px">
        <div style="font-size:11px;color:#73726C;min-width:110px">{label}</div>
        <div style="flex:1;height:26px;background:#F0F2F5;border-radius:4px;overflow:hidden">
          <div style="width:{bw}%;height:100%;background:{color};border-radius:4px;display:flex;align-items:center;padding-left:9px;font-size:10px;font-weight:600;color:#fff">
            {'&nbsp;'+fmt_n(count) if bw>8 else ''}</div></div>
        <div style="font-size:11px;min-width:42px;text-align:right;font-weight:600;color:{color}">{pct:.2f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    cd=(1-tc/ts)*100 if ts else 0; ckd=(1-tck/tc)*100 if tc else 0; pd_=(1-to_/tck)*100 if tck else 0
    with c1: st.markdown(kpi("Session→Cart",fmt_p(100-cd,1),f"⚠ {cd:.1f}% drop","wn",c="#EF9F27"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Cart→Checkout",fmt_p(100-ckd,1),f"⚠ {ckd:.1f}% abandon","dn",c="#D85A30"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Checkout→Buy",fmt_p(100-pd_,1),f"⚠ {pd_:.1f}% drop","dn" if pd_>50 else "wn",c="#D85A30"), unsafe_allow_html=True)

    fig=go.Figure(go.Funnel(y=["Sessions","Add to Cart","Checkout","Purchase"],x=[ts,tc,tck,to_],
        textinfo="value+percent initial",marker=dict(color=["#3266AD","#378ADD","#85B7EB","#1D9E75"])))
    fig.update_layout(**PLOT_LAYOUT,height=300)
    st.plotly_chart(fig,use_container_width=True)

    # Web vs App funnel — only if actually have different data
    if source_filter == "all" and "_src" in df_ov.columns and not st.session_state.get("_app_not_connected"):
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Web vs App Funnel","","#7F77DD"), unsafe_allow_html=True)
        funnel_rows = []
        for src, lbl, badge in [("web","Website","src-web"),("app","Mobile App","src-app")]:
            d = df_ov[df_ov["_src"]==src]
            if d.empty: continue
            s=d["sessions"].sum(); r=d["purchase_revenue"].sum()
            c_=d["add_to_carts"].sum(); ck=d["checkouts"].sum(); o=d["transactions"].sum()
            _cvr=o/s*100 if s>0 else 0; _aov=r/o if o>0 else 0
            funnel_rows.append(f"""<tr>
              <td><span class="{badge}">{lbl}</span></td>
              <td>{fmt_n(s)}</td><td>{fmt_n(c_)}</td><td>{fmt_n(ck)}</td>
              <td><b style="color:#1D9E75">{fmt_n(o)}</b></td>
              <td><b style="color:{'#1D9E75' if _cvr>=1 else '#EF9F27'}">{fmt_p(_cvr,2)}</b></td>
              <td>{fmt_c(_aov,0)}</td></tr>""")
        if funnel_rows:
            st.markdown(f"""<table><thead><tr>
              <th>Source</th><th>Sessions</th><th>Cart</th><th>Checkout</th>
              <th>Orders</th><th>CVR</th><th>AOV</th>
            </tr></thead><tbody>{''.join(funnel_rows)}</tbody></table>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TRAFFIC
# ══════════════════════════════════════════════════════════════
elif tab == "📡 Traffic":
    st.markdown(sh("Traffic Sources","Sessions & Revenue by Channel"), unsafe_allow_html=True)

    with st.spinner(""):
        df_ch_raw = load_combined(
            ["session_default_channel_group","sessions","purchase_revenue","transactions","add_to_carts"],
            d_from, d_to)

    if not df_ch_raw.empty and "session_default_channel_group" in df_ch_raw.columns:
        for c in ["sessions","purchase_revenue","transactions","add_to_carts"]:
            if c in df_ch_raw.columns: df_ch_raw[c] = df_ch_raw[c].apply(safe_num)

        df_ch = df_ch_raw[df_ch_raw["session_default_channel_group"].notna()&(df_ch_raw["session_default_channel_group"]!="")]

        show_tabs = source_filter == "all" and "_src" in df_ch.columns and not st.session_state.get("_app_not_connected")

        if show_tabs:
            src_tabs = st.tabs(["🌐📱 Combined","🌐 Web","📱 App"])
            sources_to_show = [("all", df_ch), ("web", df_ch[df_ch["_src"]=="web"]), ("app", df_ch[df_ch["_src"]=="app"])]
        else:
            src_tabs = [st.container()]
            sources_to_show = [("single", df_ch)]

        for idx, (src_key, src_df) in enumerate(sources_to_show):
            with src_tabs[idx]:
                if src_df.empty: st.info("No data."); continue
                dg = src_df.groupby("session_default_channel_group").sum(numeric_only=True).reset_index()
                dg = dg[dg["sessions"]>5].sort_values("purchase_revenue",ascending=False)
                cl2,cr2=st.columns(2)
                with cl2:
                    st.markdown("**Sessions**")
                    mx=dg["sessions"].max()
                    for i,(_,r) in enumerate(dg.head(8).iterrows()):
                        st.markdown(bar(r["session_default_channel_group"],r["sessions"]/mx*100 if mx else 0,COLORS[i%len(COLORS)],fmt_n(r["sessions"])),unsafe_allow_html=True)
                with cr2:
                    st.markdown("**Revenue**")
                    mx=dg["purchase_revenue"].max()
                    for i,(_,r) in enumerate(dg.sort_values("purchase_revenue",ascending=False).head(8).iterrows()):
                        st.markdown(bar(r["session_default_channel_group"],r["purchase_revenue"]/mx*100 if mx else 0,COLORS[i%len(COLORS)],fmt_c(r["purchase_revenue"])),unsafe_allow_html=True)
                rows=[]
                for _,r in dg.iterrows():
                    s=r["sessions"]; rv=r["purchase_revenue"]; tx=r["transactions"]
                    cv=tx/s*100 if s>0 else 0; rps=rv/s if s>0 else 0
                    if cv>=1.5: bdg='<span class="b bg_">الأقوى</span>'
                    elif cv>=0.8: bdg='<span class="b bb_">جيد</span>'
                    elif cv>=0.4: bdg='<span class="b ba_">راجع</span>'
                    else: bdg='<span class="b br2">ضعيف</span>'
                    rows.append(f"<tr><td><b>{r['session_default_channel_group']}</b></td><td>{fmt_n(s)}</td><td>{fmt_c(rv)}</td><td>{fmt_n(tx)}</td><td><b style='color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.5 else '#D85A30'}'>{fmt_p(cv,2)}</b></td><td>{fmt_c(rps,1)}</td><td>{bdg}</td></tr>")
                st.markdown(f"<table><thead><tr><th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",unsafe_allow_html=True)
                export_btn(dg[["session_default_channel_group","sessions","purchase_revenue","transactions"]],f"channels_{src_key}.csv")

# ══════════════════════════════════════════════════════════════
# DEVICES
# ══════════════════════════════════════════════════════════════
elif tab == "📱 Devices":
    st.markdown(sh("Device Performance","Mobile vs Desktop vs Tablet","#7F77DD"), unsafe_allow_html=True)

    with st.spinner(""):
        df_dv_raw = load_combined(
            ["devicecategory","sessions","purchase_revenue","transactions","bounce_rate"],
            d_from, d_to)

    if not df_dv_raw.empty and "devicecategory" in df_dv_raw.columns:
        for c in ["sessions","purchase_revenue","transactions","bounce_rate"]:
            if c in df_dv_raw.columns: df_dv_raw[c] = df_dv_raw[c].apply(safe_num)

        DC={"mobile":"#3266AD","desktop":"#888780","tablet":"#1D9E75"}

        show_split = source_filter=="all" and "_src" in df_dv_raw.columns and not st.session_state.get("_app_not_connected")

        if show_split:
            for src,lbl in [("web","🌐 Website"),("app","📱 Mobile App")]:
                d=df_dv_raw[df_dv_raw["_src"]==src]
                if d.empty: continue
                d=d[d["devicecategory"].isin(["mobile","desktop","tablet"])].copy()
                st.markdown(f"**{lbl}**")
                cols=st.columns(max(len(d),1))
                for i,(_,r) in enumerate(d.iterrows()):
                    dev=r["devicecategory"]; clr=DC.get(dev,"#888780")
                    br_=r["bounce_rate"]*100; sp=r["sessions"]/d["sessions"].sum()*100 if d["sessions"].sum()>0 else 0
                    with cols[i]: st.markdown(kpi(dev.title(),f"{sp:.1f}%",f"Bounce: {br_:.1f}%","dn" if br_>55 else "wn",f"Rev: {fmt_c(r['purchase_revenue'])}",c=clr),unsafe_allow_html=True)
                st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)
        else:
            df_dv=df_dv_raw.groupby("devicecategory").sum(numeric_only=True).reset_index()
            md=df_dv[df_dv["devicecategory"].isin(["mobile","desktop","tablet"])]
            cols=st.columns(max(len(md),1))
            for i,(_,r) in enumerate(md.iterrows()):
                dev=r["devicecategory"]; clr=DC.get(dev,"#888780")
                br_=r["bounce_rate"]*100; sp=r["sessions"]/md["sessions"].sum()*100 if md["sessions"].sum()>0 else 0
                with cols[i]: st.markdown(kpi(dev.title(),f"{sp:.1f}%",f"Bounce: {br_:.1f}%","dn" if br_>55 else "wn",f"Rev: {fmt_c(r['purchase_revenue'])}",c=clr),unsafe_allow_html=True)
            export_btn(md[["devicecategory","sessions","purchase_revenue","transactions","bounce_rate"]],"devices.csv")

# ══════════════════════════════════════════════════════════════
# E-COMMERCE
# ══════════════════════════════════════════════════════════════
elif tab == "🛒 E-Commerce":
    st.markdown(sh("E-Commerce","Products & Categories","#1D9E75"), unsafe_allow_html=True)

    with st.spinner("Loading..."):
        df_cat_raw = load_combined(
            ["item_category","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"],
            d_from, d_to)
        df_prod_raw = load_combined(
            ["item_name","item_revenue","items_purchased","items_viewed","items_added_to_cart"],
            d_from, d_to)

    RANEEN_CATS=["الأجهزة المنزلية","الأثاث","الإلكترونيات","المطبخ","موبايلات","المفروشات","عروض رنين","المنزل","المنتجات العائلية","الأزياء و الموضة"]
    CAT_ICONS={"الأجهزة المنزلية":"🏠","الأثاث":"🛋️","الإلكترونيات":"📺","المطبخ":"🍳","موبايلات":"📱","المفروشات":"🛏️","عروض رنين":"🏷️","المنزل":"🪴","المنتجات العائلية":"👨‍👩‍👧","الأزياء و الموضة":"👗"}

    if not df_cat_raw.empty and "item_category" in df_cat_raw.columns:
        for c in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if c in df_cat_raw.columns: df_cat_raw[c] = df_cat_raw[c].apply(safe_num)
        df_cat=df_cat_raw.groupby("item_category").sum(numeric_only=True).reset_index()
        df_cf=df_cat[df_cat["item_category"].isin(RANEEN_CATS)].sort_values("gross_item_revenue",ascending=False)
        ti=df_cf["gross_item_revenue"].sum(); tu=df_cf["items_purchased"].sum()
        c1,c2,c3=st.columns(3)
        with c1: st.markdown(kpi("Item Revenue",fmt_c(ti),"All categories","up",c="#1D9E75"),unsafe_allow_html=True)
        with c2: st.markdown(kpi("Units Sold",fmt_n(tu),"Items purchased","up",c="#3266AD"),unsafe_allow_html=True)
        with c3: st.markdown(kpi("Avg Price",fmt_c(ti/tu,0) if tu else "—","Rev/Units","nu",c="#7F77DD"),unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
        cl2,cr2=st.columns(2)
        with cl2:
            st.markdown(sh("Revenue by Category","","#1D9E75"),unsafe_allow_html=True)
            mx=df_cf["gross_item_revenue"].max()
            for i,(_,r) in enumerate(df_cf.head(10).iterrows()):
                st.markdown(bar(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}",r["gross_item_revenue"]/mx*100 if mx else 0,COLORS[i%len(COLORS)],fmt_c(r["gross_item_revenue"])),unsafe_allow_html=True)
        with cr2:
            st.markdown(sh("Cart-to-View Rate","","#EF9F27"),unsafe_allow_html=True)
            df_cf=df_cf.copy()
            df_cf["cr"]=df_cf.apply(lambda r:r["items_added_to_cart"]/r["items_viewed"]*100 if r.get("items_viewed",0)>0 else 0,axis=1)
            mx=df_cf["cr"].max()
            for _,r in df_cf.sort_values("cr",ascending=False).head(10).iterrows():
                c="#1D9E75" if r["cr"]>6 else "#EF9F27" if r["cr"]>3 else "#D85A30"
                st.markdown(bar(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}",r["cr"]/mx*100 if mx else 0,c,f"{r['cr']:.1f}%"),unsafe_allow_html=True)
        export_btn(df_cf[["item_category","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]],"categories.csv")

    if not df_prod_raw.empty and "item_name" in df_prod_raw.columns:
        for c in ["item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if c in df_prod_raw.columns: df_prod_raw[c] = df_prod_raw[c].apply(safe_num)
        df_prod=df_prod_raw.groupby("item_name").sum(numeric_only=True).reset_index()
        df_top=df_prod[df_prod["item_revenue"]>0].sort_values("item_revenue",ascending=False).head(15)
        st.markdown("<div style='height:14px'></div>",unsafe_allow_html=True)
        st.markdown(sh("Top 15 Products","","#3266AD"),unsafe_allow_html=True)
        rows=[]
        for i,(_,r) in enumerate(df_top.iterrows(),1):
            nm=str(r["item_name"])[:55]+("..." if len(str(r["item_name"]))>55 else "")
            vw=safe_num(r.get("items_viewed",0)); cr_=safe_num(r.get("items_added_to_cart",0))/vw*100 if vw>0 else 0
            bc="bg_" if cr_>8 else "ba_" if cr_>4 else "br2"
            rows.append(f"<tr><td style='color:#9A9A8E'>{i}</td><td>{nm}</td><td><b style='color:#1D9E75'>{fmt_c(r['item_revenue'])}</b></td><td>{int(r['items_purchased'])}</td><td>{fmt_n(vw)}</td><td><span class='b {bc}'>{cr_:.1f}%</span></td></tr>")
        st.markdown(f"<table><thead><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",unsafe_allow_html=True)
        export_btn(df_top[["item_name","item_revenue","items_purchased","items_viewed"]],"top_products.csv")

# ══════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════
elif tab == "🎯 Campaigns":
    st.markdown(sh("Campaigns","Google Ads + Meta"), unsafe_allow_html=True)

    with st.spinner(""):
        df_gads = load_combined(
            ["session_google_ads_campaign_name","sessions","purchase_revenue","transactions","add_to_carts","checkouts"],
            d_from, d_to)
        df_meta = load_combined(
            ["session_manual_campaign_name","sessions","purchase_revenue","transactions","add_to_carts"],
            d_from, d_to)

    camp_tabs = st.tabs(["🟦 Google Ads","🟦 Meta Campaigns"])

    with camp_tabs[0]:
        if not df_gads.empty and "session_google_ads_campaign_name" in df_gads.columns:
            for c in ["sessions","purchase_revenue","transactions","add_to_carts","checkouts"]:
                if c in df_gads.columns: df_gads[c] = df_gads[c].apply(safe_num)
            dg=df_gads.groupby("session_google_ads_campaign_name").sum(numeric_only=True).reset_index()
            dg=dg[dg["session_google_ads_campaign_name"].notna()&(dg["session_google_ads_campaign_name"]!="(not set)")&(dg["sessions"]>100)].copy()
            dg["cvr"]=dg.apply(lambda r:r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0,axis=1)
            dg["rps"]=dg.apply(lambda r:r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0,axis=1)
            dg=dg.sort_values("purchase_revenue",ascending=False)
            rows=[]
            for _,r in dg.iterrows():
                cv=r["cvr"]
                if cv>=1.5: bdg='<span class="b bg_">الأقوى</span>'
                elif cv>=0.8: bdg='<span class="b bb_">جيد</span>'
                elif cv>=0.3: bdg='<span class="b ba_">راجع</span>'
                else: bdg='<span class="b br2">ضعيف</span>'
                rows.append(f"<tr><td style='font-size:10px'>{r['session_google_ads_campaign_name']}</td><td>{fmt_n(r['sessions'])}</td><td><b style='color:#1D9E75'>{fmt_c(r['purchase_revenue'])}</b></td><td>{int(r['transactions'])}</td><td><b style='color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.5 else '#D85A30'}'>{fmt_p(cv,2)}</b></td><td>{fmt_c(r['rps'],1)}</td><td>{bdg}</td></tr>")
            st.markdown(f"<table><thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",unsafe_allow_html=True)
            export_btn(dg[["session_google_ads_campaign_name","sessions","purchase_revenue","transactions","cvr","rps"]],"google_campaigns.csv")

    with camp_tabs[1]:
        if not df_meta.empty and "session_manual_campaign_name" in df_meta.columns:
            for c in ["sessions","purchase_revenue","transactions","add_to_carts"]:
                if c in df_meta.columns: df_meta[c] = df_meta[c].apply(safe_num)
            dm=df_meta.groupby("session_manual_campaign_name").sum(numeric_only=True).reset_index()
            exclude=["(organic)","(not set)","(referral)","(direct)",""]
            dm=dm[~dm["session_manual_campaign_name"].isin(exclude)&dm["session_manual_campaign_name"].notna()&(dm["sessions"]>5)].copy()
            dm["cvr"]=dm.apply(lambda r:r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0,axis=1)
            dm["rps"]=dm.apply(lambda r:r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0,axis=1)
            dm=dm.sort_values("purchase_revenue",ascending=False)
            rows=[]
            for _,r in dm.head(50).iterrows():
                cv=r["cvr"]; nm=str(r["session_manual_campaign_name"])
                nm_l=nm.lower()
                if "rt |" in nm_l or nm_l.startswith("rt "): ct='<span class="b bp_">🔄 RT</span>'
                elif "prosp" in nm_l: ct='<span class="b bb_">🎯 Prosp</span>'
                elif "conv" in nm_l: ct='<span class="b bg_">💰 Conv</span>'
                else: ct='<span class="b bx_">📌</span>'
                if cv>=1.5: bdg='<span class="b bg_">الأقوى</span>'
                elif cv>=0.8: bdg='<span class="b bb_">جيد</span>'
                elif cv>=0.3: bdg='<span class="b ba_">راجع</span>'
                else: bdg='<span class="b br2">ضعيف</span>'
                rows.append(f"<tr><td style='font-size:10px'>{nm[:55]}{'...' if len(nm)>55 else ''}</td><td>{ct}</td><td>{fmt_n(r['sessions'])}</td><td><b style='color:#1877F2'>{fmt_c(r['purchase_revenue'])}</b></td><td>{int(r['transactions'])}</td><td><b style='color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.5 else '#D85A30'}'>{fmt_p(cv,2)}</b></td><td>{fmt_c(r['rps'],1)}</td><td>{bdg}</td></tr>")
            st.markdown(f"<table><thead><tr><th>Campaign</th><th>Type</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",unsafe_allow_html=True)
            export_btn(dm[["session_manual_campaign_name","sessions","purchase_revenue","transactions","cvr","rps"]],"meta_campaigns.csv")

# ══════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════
elif tab == "👥 Users":
    st.markdown(sh("Users Analytics","New vs Returning · Cohort","#7F77DD"), unsafe_allow_html=True)

    with st.spinner(""):
        df_nr_raw = load_combined(
            ["new_vs_returning","sessions","active_users","purchase_revenue","transactions","bounce_rate"],
            d_from, d_to)

    if not df_nr_raw.empty and "new_vs_returning" in df_nr_raw.columns:
        for c in ["sessions","active_users","purchase_revenue","transactions","bounce_rate"]:
            if c in df_nr_raw.columns: df_nr_raw[c] = df_nr_raw[c].apply(safe_num)
        df_nr_agg = df_nr_raw[df_nr_raw["new_vs_returning"].isin(["new","returning"])].groupby("new_vs_returning").sum(numeric_only=True).reset_index()
        seg_rows=[]
        for seg in ["returning","new"]:
            d=df_nr_agg[df_nr_agg["new_vs_returning"]==seg]
            if d.empty: continue
            s=d["sessions"].sum(); rv=d["purchase_revenue"].sum()
            tx=d["transactions"].sum(); br=d["bounce_rate"].mean()*100 if "bounce_rate" in d.columns else 0
            cv=tx/s*100 if s>0 else 0; av=rv/tx if tx>0 else 0
            bc="bg_" if seg=="returning" else "bb_"
            seg_rows.append(f"<tr><td><span class='b {bc}'>{seg.title()}</span></td><td>{fmt_n(s)}</td><td><b style='color:#1D9E75'>{fmt_c(rv)}</b></td><td>{fmt_n(tx)}</td><td><b style='color:{'#1D9E75' if cv>=0.8 else '#EF9F27'}'>{fmt_p(cv,2)}</b></td><td>{fmt_c(av,0)}</td><td style='color:{'#D85A30' if br>55 else '#EF9F27'}'>{fmt_p(br,1)}</td></tr>")
        if seg_rows:
            st.markdown(f"<table><thead><tr><th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th><th>Bounce</th></tr></thead><tbody>{''.join(seg_rows)}</tbody></table>",unsafe_allow_html=True)
            export_btn(df_nr_agg,"users_segments.csv")

    # Cohort
    st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
    st.markdown(sh("Cohort Analysis","Retention بالشهر","#D85A30"), unsafe_allow_html=True)
    with st.spinner("Loading cohort (90d)..."):
        from datetime import date, timedelta
        c_from = str(date.today()-timedelta(90)); c_to = str(date.today()-timedelta(1))
        df_coh = load_combined(["date","new_vs_returning","sessions","purchase_revenue","transactions"], c_from, c_to)

    if not df_coh.empty and "date" in df_coh.columns:
        for c in ["sessions","purchase_revenue","transactions"]:
            if c in df_coh.columns: df_coh[c] = df_coh[c].apply(safe_num)
        df_coh["date"]=pd.to_datetime(df_coh["date"],errors="coerce")
        df_coh=df_coh.dropna(subset=["date"])
        df_coh["month"]=df_coh["date"].dt.to_period("M").astype(str)
        dm=df_coh.groupby(["month","new_vs_returning"]).agg(sessions=("sessions","sum"),revenue=("purchase_revenue","sum"),orders=("transactions","sum")).reset_index()
        months=sorted(dm["month"].unique())
        crows=[]
        for month in months:
            md=dm[dm["month"]==month]
            ns=safe_num(md[md["new_vs_returning"]=="new"]["sessions"].sum())
            rs=safe_num(md[md["new_vs_returning"]=="returning"]["sessions"].sum())
            nr=safe_num(md[md["new_vs_returning"]=="new"]["revenue"].sum())
            rr=safe_num(md[md["new_vs_returning"]=="returning"]["revenue"].sum())
            no_=safe_num(md[md["new_vs_returning"]=="new"]["orders"].sum())
            ro_=safe_num(md[md["new_vs_returning"]=="returning"]["orders"].sum())
            tot=ns+rs; ret=rs/tot*100 if tot>0 else 0
            rv_tot=nr+rr; rrp=rr/rv_tot*100 if rv_tot>0 else 0
            ncvr=no_/ns*100 if ns>0 else 0; rcvr=ro_/rs*100 if rs>0 else 0
            rc="#1D9E75" if ret>50 else "#EF9F27" if ret>30 else "#D85A30"
            crows.append(f"<tr><td><b>{month}</b></td><td>{fmt_n(ns)}</td><td>{fmt_n(rs)}</td><td><div style='display:flex;align-items:center;gap:6px'><div style='flex:1;height:5px;background:#F0F2F5;border-radius:3px;overflow:hidden'><div style='width:{min(ret,100):.0f}%;height:100%;background:{rc}'></div></div><span style='color:{rc};font-weight:600'>{ret:.1f}%</span></div></td><td>{fmt_c(nr)}</td><td>{fmt_c(rr)}</td><td style='color:{rc}'><b>{rrp:.1f}%</b></td><td style='color:#EF9F27'>{fmt_p(ncvr,2)}</td><td style='color:#1D9E75;font-weight:600'>{fmt_p(rcvr,2)}</td></tr>")
        st.markdown(f"<table><thead><tr><th>Month</th><th>New Ses</th><th>Ret Ses</th><th>Retention</th><th>New Rev</th><th>Ret Rev</th><th>Rev Ret%</th><th>New CVR</th><th>Ret CVR</th></tr></thead><tbody>{''.join(crows)}</tbody></table>",unsafe_allow_html=True)
        export_btn(dm,"cohort.csv")

# ══════════════════════════════════════════════════════════════
# INSIGHTS
# ══════════════════════════════════════════════════════════════
elif tab == "💡 Insights":
    st.markdown(sh("Strategic Insights","Action Plan","#D85A30"), unsafe_allow_html=True)

    src_note = f" ({src_label})" if src_label else ""
    st.markdown("### 🔴 P1 — فوري")
    st.markdown(ins("🔴",f"Cart Abandonment {ca:.1f}%{src_note}",f"من {fmt_n(tc)} add-to-cart، بس {fmt_n(to_)} اشتروا. Email Series + Exit-intent = +15-20% revenue.","ir"),unsafe_allow_html=True)
    if ab>55: st.markdown(ins("🔴",f"Bounce Rate {ab:.1f}%{src_note}","راجع الـ Landing Pages وسرعة التحميل.","ir"),unsafe_allow_html=True)

    st.markdown("### ⚠ P2 — مهم")
    st.markdown(ins("⚠",f"CVR {fmt_p(cvr_,2)}{src_note}",f"Sessions: {fmt_n(ts)} · Revenue: {fmt_c(tr)} · AOV: {fmt_c(aov_,0)}. تحسين الـ CVR بـ 0.1% = +{fmt_c(ts*0.001*aov_)} إضافية.","iw"),unsafe_allow_html=True)

    if source_filter == "all" and st.session_state.get("_app_not_connected"):
        st.markdown(ins("⚠","App Data غير متاحة","ربط account الـ App في Windsor سيتيح مقارنة Web vs App لاتخاذ قرارات الـ budget.","ib"),unsafe_allow_html=True)

    st.markdown("### ✅ P3 — فرص نمو")
    st.markdown(ins("✅",f"AOV {fmt_c(aov_,0)}","Installment plans + messaging واضح = رفع CVR.","ig"),unsafe_allow_html=True)
    st.markdown(ins("▲","Cart مرتفع — Checkout منخفض",f"Cart: {fmt_n(tc)} → Purchase: {fmt_n(to_)}. Streamline الـ checkout.","ib"),unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>",unsafe_allow_html=True)
    st.markdown(sh("Summary","","#2A3050"),unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Metric":["Sessions","Revenue","Orders","AOV","CVR","Bounce","Cart Abandon","Avg Session","Source"],
        "Value":[fmt_n(ts),fmt_c(tr),fmt_n(to_),fmt_c(aov_,0),fmt_p(cvr_,2),fmt_p(ab),fmt_p(ca),f"{am}:{as_:02d} min",src_label],
        "Status":["✅","✅","✅","✅","⚠" if cvr_<1 else "✅","⚠" if ab>50 else "✅","🔴" if ca>85 else "⚠","✅","📊"],
    }),use_container_width=True,hide_index=True)
    export_btn(pd.DataFrame({"Metric":["Sessions","Revenue","Orders","AOV","CVR","Bounce","Cart Abandon"],"Value":[ts,tr,to_,aov_,cvr_,ab,ca]}),"summary.csv")
