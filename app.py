import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import date, timedelta, datetime
import calendar
import io

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
WEB_ID = "292247905"
APP_ID  = "248305344"
WINDSOR_URL = "https://connectors.windsor.ai/googleanalytics4"

RANEEN_CATS = [
    "الأجهزة المنزلية","الأثاث","الإلكترونيات","المطبخ",
    "موبايلات","المفروشات","عروض رنين","المنزل",
    "المنتجات العائلية","الأزياء و الموضة",
]
CAT_ICONS = {
    "الأجهزة المنزلية":"🏠","الأثاث":"🛋️","الإلكترونيات":"📺",
    "المطبخ":"🍳","موبايلات":"📱","المفروشات":"🛏️",
    "عروض رنين":"🏷️","المنزل":"🪴","المنتجات العائلية":"👨‍👩‍👧",
    "الأزياء و الموضة":"👗",
}

st.set_page_config(page_title="Raneen Analytics", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans Arabic',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:1rem 2rem 2rem;max-width:1440px;}

.kpi-card{background:#fff;border:1px solid #E8EDF5;border-radius:12px;
  padding:16px 18px;position:relative;overflow:hidden;transition:box-shadow .2s;}
.kpi-card:hover{box-shadow:0 4px 16px rgba(50,102,173,.12);}
.kpi-accent{position:absolute;top:0;left:0;right:0;height:3px;border-radius:12px 12px 0 0;}
.kpi-label{font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:6px;}
.kpi-value{font-size:24px;font-weight:600;color:#111827;line-height:1;margin-bottom:4px;}
.kpi-change{font-size:12px;}.kpi-sub{font-size:11px;color:#9CA3AF;margin-top:2px;}
.up{color:#059669;}.down{color:#DC2626;}.warn{color:#D97706;}.neu{color:#6B7280;}

.sec-hdr{display:flex;align-items:center;gap:8px;padding:4px 0 10px;
  border-bottom:1px solid #F3F4F6;margin-bottom:14px;}
.sec-dot{width:8px;height:8px;border-radius:50%;}
.sec-title{font-size:14px;font-weight:600;color:#111827;}
.sec-sub{font-size:11px;color:#9CA3AF;margin-left:auto;}

.bar-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;}
.bar-name{font-size:12px;color:#6B7280;min-width:120px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.bar-track{flex:1;height:8px;background:#F3F4F6;border-radius:4px;overflow:hidden;}
.bar-fill{height:100%;border-radius:4px;}
.bar-val{font-size:12px;color:#111827;min-width:72px;text-align:right;font-weight:500;}

.stbl{width:100%;border-collapse:collapse;font-size:12px;}
.stbl th{background:#F9FAFB;color:#6B7280;font-weight:500;font-size:11px;
  text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;
  border-bottom:1px solid #E5E7EB;text-align:left;}
.stbl td{padding:8px 10px;border-bottom:1px solid #F3F4F6;color:#111827;vertical-align:middle;}
.stbl tr:hover td{background:#F9FAFB;}

.badge{display:inline-block;font-size:10px;padding:2px 8px;
  border-radius:10px;font-weight:600;}
.bg{background:rgba(5,150,105,.12);color:#059669;}
.br{background:rgba(220,38,38,.12);color:#DC2626;}
.ba{background:rgba(217,119,6,.12);color:#D97706;}
.bb{background:rgba(50,102,173,.12);color:#3266AD;}
.bp{background:rgba(124,58,237,.12);color:#7C3AED;}
.bgr{background:rgba(107,114,128,.12);color:#6B7280;}

.funnel-row{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.funnel-label{font-size:12px;color:#6B7280;min-width:110px;}
.funnel-track{flex:1;height:28px;background:#F3F4F6;border-radius:4px;overflow:hidden;}
.funnel-fill{height:100%;border-radius:4px;display:flex;align-items:center;
  padding-left:10px;font-size:11px;font-weight:600;color:#fff;}
.funnel-pct{font-size:12px;min-width:50px;text-align:right;font-weight:600;}

.insight-card{border-radius:8px;padding:12px 14px;margin-bottom:8px;
  font-size:13px;line-height:1.6;border-left:4px solid;}
.i-red{background:rgba(220,38,38,.06);border-color:#DC2626;color:#991B1B;}
.i-amb{background:rgba(217,119,6,.06);border-color:#D97706;color:#92400E;}
.i-grn{background:rgba(5,150,105,.06);border-color:#059669;color:#065F46;}
.i-blu{background:rgba(50,102,173,.06);border-color:#3266AD;color:#1E3A5F;}

.top-bar{display:flex;align-items:center;justify-content:space-between;
  padding:8px 0 14px;border-bottom:1px solid #E5E7EB;margin-bottom:18px;}
.brand{font-size:20px;font-weight:700;color:#111827;}
.brand span{color:#3266AD;}
.live-badge{display:inline-flex;align-items:center;gap:6px;
  background:rgba(5,150,105,.08);border:1px solid rgba(5,150,105,.25);
  border-radius:20px;padding:3px 10px;font-size:11px;font-weight:500;color:#059669;}
.ldot{width:6px;height:6px;border-radius:50%;background:#059669;
  animation:blink 2s infinite;display:inline-block;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

section[data-testid="stSidebar"]{background:#F9FAFB;border-right:1px solid #E5E7EB;}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#6B7280", size=11),
    margin=dict(l=0,r=0,t=10,b=0),
    legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,
                bgcolor="rgba(0,0,0,0)",font=dict(size=11)),
    xaxis=dict(gridcolor="#F3F4F6",linecolor="#E5E7EB",tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#F3F4F6",linecolor="#E5E7EB",tickfont=dict(size=10)),
)

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════
def safe(v, d=0):
    try: return float(v) if v is not None else d
    except: return d

def fc(v, dec=1):
    v=safe(v)
    if v>=1_000_000: return f"{v/1_000_000:.{dec}f}M ج"
    if v>=1_000:     return f"{v/1_000:.{dec}f}K ج"
    return f"{v:,.0f} ج"

def fn(v, dec=0):
    v=safe(v)
    if v>=1_000_000: return f"{v/1_000_000:.1f}M"
    if v>=1_000:     return f"{v/1_000:.1f}K"
    return f"{v:,.{dec}f}"

def fp(v, dec=1): return f"{safe(v):.{dec}f}%"

def kpi(label, value, change, cls, sub="", color="#3266AD"):
    return f"""<div class="kpi-card">
  <div class="kpi-accent" style="background:{color}"></div>
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-change {cls}">{change}</div>
  {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
</div>"""

def sh(title, sub="", color="#3266AD"):
    return f"""<div class="sec-hdr">
  <div class="sec-dot" style="background:{color}"></div>
  <div class="sec-title">{title}</div>
  {'<div class="sec-sub">'+sub+'</div>' if sub else ''}
</div>"""

def bar(name, pct, color, val):
    return f"""<div class="bar-row">
  <div class="bar-name" title="{name}">{name}</div>
  <div class="bar-track"><div class="bar-fill" style="width:{max(pct,0.5):.1f}%;background:{color}"></div></div>
  <div class="bar-val">{val}</div>
</div>"""

def ins(icon, title, body, cls):
    return f'<div class="insight-card {cls}"><b>{icon} {title}</b><br>{body}</div>'

def csv_btn(df, label, fname):
    buf = io.BytesIO()
    buf.write(b'\xef\xbb\xbf')
    df.to_csv(buf, index=False, encoding='utf-8')
    st.download_button(label, buf.getvalue(), fname, "text/csv", key=fname+str(len(df)))

def get_dates(preset, d_from=None, d_to=None):
    today = date.today()
    if preset == "custom":
        return str(d_from), str(d_to)
    m = {"last_7d":7,"last_14d":14,"last_30d":30,"last_90d":90}
    if preset in m:
        return str(today - timedelta(m[preset])), str(today)
    if preset == "this_month":
        return str(today.replace(day=1)), str(today)
    if preset == "last_month":
        first = today.replace(day=1)
        last_m_end = first - timedelta(1)
        last_m_start = last_m_end.replace(day=1)
        return str(last_m_start), str(last_m_end)
    return str(today - timedelta(30)), str(today)

# ══════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def fetch(api_key, account_id, fields, date_from, date_to):
    params = {
        "api_key": api_key,
        "account_id": account_id,
        "fields": ",".join(fields),
        "date_from": date_from,
        "date_to": date_to,
    }
    try:
        r = requests.get(WINDSOR_URL, params=params, timeout=40)
        r.raise_for_status()
        data = r.json()
        rows = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(rows, list): rows = []
        df = pd.DataFrame(rows)
        for c in df.columns:
            try: df[c] = pd.to_numeric(df[c])
            except: pass
        return df
    except Exception as e:
        st.warning(f"API error ({account_id}): {e}")
        return pd.DataFrame()

def load(api_key, source, fields_ecom, fields_session, dim, d0, d1):
    """Load + merge ecom & session requests for given source(s)."""
    ids = []
    if source in ("All","Web"): ids.append((WEB_ID,"Web"))
    if source in ("All","App"): ids.append((APP_ID,"App"))

    frames = []
    for aid, lbl in ids:
        df_e = fetch(api_key, aid, fields_ecom, d0, d1) if fields_ecom else pd.DataFrame()
        df_s = fetch(api_key, aid, fields_session, d0, d1) if fields_session else pd.DataFrame()

        if df_e.empty and df_s.empty:
            continue
        if df_e.empty:
            df = df_s
        elif df_s.empty:
            df = df_e
        else:
            scols = [c for c in df_s.columns if c not in df_e.columns or c == dim]
            df = pd.merge(df_e, df_s[scols], on=dim, how="left")
        df["_src"] = lbl
        frames.append(df)

    if not frames: return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    for c in out.columns:
        try: out[c] = pd.to_numeric(out[c])
        except: pass
    return out

def load_single(api_key, source, fields, d0, d1):
    """Single-request load (ecom-only or session-only fields that are compatible)."""
    ids = []
    if source in ("All","Web"): ids.append((WEB_ID,"Web"))
    if source in ("All","App"): ids.append((APP_ID,"App"))
    frames = []
    for aid, lbl in ids:
        df = fetch(api_key, aid, fields, d0, d1)
        if not df.empty:
            df["_src"] = lbl
            frames.append(df)
    if not frames: return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    for c in out.columns:
        try: out[c] = pd.to_numeric(out[c])
        except: pass
    return out

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="padding:12px 0 18px">
  <div style="font-size:17px;font-weight:700;color:#111827">
    <span style="color:#3266AD">●</span> Raneen Analytics
  </div>
  <div style="font-size:11px;color:#9CA3AF;margin-top:3px">Unified GA4 Dashboard</div>
</div>""", unsafe_allow_html=True)

    API_KEY = st.secrets.get("WINDSOR_API_KEY","") if hasattr(st,"secrets") else ""
    if not API_KEY:
        API_KEY = st.text_input("Windsor API Key", type="password", placeholder="wnd_...")

    st.markdown("---")
    source = st.radio("Data Source", ["All","Web","App"],
                      format_func=lambda x:{"All":"🌐 All (Web + App)","Web":"💻 Web Only","App":"📱 App Only"}[x])

    st.markdown("---")
    preset = st.selectbox("Date Range", ["last_7d","last_14d","last_30d","last_90d","this_month","last_month","custom"],
        format_func=lambda x:{"last_7d":"Last 7 Days","last_14d":"Last 14 Days",
          "last_30d":"Last 30 Days","last_90d":"Last 90 Days",
          "this_month":"This Month","last_month":"Last Month","custom":"Custom Range"}[x])
    cf, ct = None, None
    if preset == "custom":
        cf = st.date_input("From", date.today()-timedelta(30))
        ct = st.date_input("To", date.today())
    d0, d1 = get_dates(preset, cf, ct)

    st.markdown("---")
    tab = st.radio("Section", ["Overview","Funnel","Traffic","Devices","E-Commerce","Campaigns","Users","Insights"],
                   label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f'<div style="font-size:10px;color:#9CA3AF;line-height:1.7">'
                f'GA4 via Windsor.ai<br>Web: {WEB_ID} · App: {APP_ID}<br>'
                f'<span style="color:#059669">● Live</span> · {d0} → {d1}</div>',
                unsafe_allow_html=True)

# ── TOP BAR
st.markdown(f"""<div class="top-bar">
  <div class="brand"><span>Raneen</span>.com Analytics</div>
  <div class="live-badge"><span class="ldot"></span> Live · {source} · {d0} → {d1}</div>
</div>""", unsafe_allow_html=True)

if not API_KEY:
    st.info("🔑 Enter your Windsor API Key in the sidebar to load data.")
    st.stop()

COLORS = ["#3266AD","#1D9E75","#EF9F27","#7C3AED","#D85A30","#5DCAA5","#85B7EB","#6B7280","#F472B6","#A78BFA"]

# ══════════════════════════════════════════════════════════════════
# 1. OVERVIEW
# ══════════════════════════════════════════════════════════════════
if tab == "Overview":
    st.markdown(sh("Overview","Key Performance Indicators","#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading overview data..."):
        df_ov = load(API_KEY, source,
            ["date","purchase_revenue","transactions","add_to_carts","checkouts"],
            ["date","sessions","active_users","bounce_rate","average_session_duration"],
            "date", d0, d1)

        df_nr = load(API_KEY, source,
            ["new_vs_returning","purchase_revenue","transactions"],
            ["new_vs_returning","sessions","active_users"],
            "new_vs_returning", d0, d1)

    if df_ov.empty:
        st.error("No data — check API key / date range."); st.stop()

    def num(col): return safe(df_ov[col].sum()) if col in df_ov else 0
    def avg(col): return safe(df_ov[col].mean()) if col in df_ov else 0

    tot_s   = num("sessions"); tot_r = num("purchase_revenue")
    tot_o   = num("transactions"); tot_c = num("add_to_carts")
    tot_ck  = num("checkouts"); br = avg("bounce_rate")*100
    asd     = avg("average_session_duration")
    aov     = tot_r/tot_o if tot_o else 0
    cvr     = tot_o/tot_s*100 if tot_s else 0
    ca      = (1-tot_o/tot_c)*100 if tot_c else 0
    sm,ss   = int(asd//60), int(asd%60)

    # Web vs App comparison when All
    if source == "All" and "_src" in df_ov.columns:
        st.markdown(sh("Web vs App — Quick Compare","","#7C3AED"), unsafe_allow_html=True)
        wc1,wc2 = st.columns(2)
        for col, lbl, clr in [(wc1,"Web","#3266AD"),(wc2,"App","#7C3AED")]:
            d = df_ov[df_ov["_src"]==lbl]
            _r = safe(d["purchase_revenue"].sum()) if "purchase_revenue" in d else 0
            _s = safe(d["sessions"].sum()) if "sessions" in d else 0
            _o = safe(d["transactions"].sum()) if "transactions" in d else 0
            _cvr = _o/_s*100 if _s else 0
            with col:
                st.markdown(kpi(f"{lbl} Revenue",fc(_r),f"Sessions: {fn(_s)}","neu",
                    f"Orders: {fn(_o)} · CVR: {fp(_cvr,2)}",clr), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # 8 KPIs
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi("Sessions",fn(tot_s),"▲ Live GA4","up","",COLORS[0]), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Revenue",fc(tot_r),"▲ Purchase Revenue","up","",COLORS[1]), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Orders",fn(tot_o),"▲ Transactions","up","",COLORS[1]), unsafe_allow_html=True)
    with c4: st.markdown(kpi("AOV",fc(aov,0),"Avg Order Value","neu","",COLORS[0]), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5: st.markdown(kpi("Add to Cart",fn(tot_c),f"⚠ Abandon {ca:.1f}%","warn","",COLORS[2]), unsafe_allow_html=True)
    with c6: st.markdown(kpi("Bounce Rate",fp(br),"Monitor carefully","down" if br>55 else "warn","",COLORS[4]), unsafe_allow_html=True)
    with c7: st.markdown(kpi("Avg Session",f"{sm}:{ss:02d}","minutes","neu","",COLORS[3]), unsafe_allow_html=True)
    with c8: st.markdown(kpi("CVR",fp(cvr,2),"⚠ Improve" if cvr<1 else "▲ Good","warn" if cvr<1 else "up","",COLORS[4] if cvr<1 else COLORS[1]), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Time-series charts
    if "date" in df_ov.columns:
        df_ts = df_ov.copy()
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts = df_ts.dropna(subset=["date"]).sort_values("date")

        if source == "All" and "_src" in df_ts.columns:
            df_ts_g = df_ts.groupby(["date","_src"], as_index=False).sum(numeric_only=True)
        else:
            df_ts_g = df_ts.groupby("date", as_index=False).sum(numeric_only=True)

        cl, cr = st.columns(2)
        with cl:
            st.markdown(sh("Revenue & Orders","Daily","#1D9E75"), unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y":True}]])
            if source == "All" and "_src" in df_ts_g.columns:
                for i,(s,c) in enumerate(zip(["Web","App"],["#3266AD","#7C3AED"])):
                    d = df_ts_g[df_ts_g["_src"]==s]
                    fig.add_trace(go.Bar(x=d["date"],y=d["purchase_revenue"]/1000,name=f"Rev {s}",
                        marker_color=c,opacity=.8), secondary_y=False)
            else:
                fig.add_trace(go.Bar(x=df_ts_g["date"],y=df_ts_g["purchase_revenue"]/1000,
                    name="Revenue (K ج)",marker_color="#3266AD",opacity=.8), secondary_y=False)
            fig.add_trace(go.Scatter(x=df_ts_g.groupby("date")["transactions"].sum().index if source=="All" else df_ts_g["date"],
                y=df_ts_g.groupby("date")["transactions"].sum().values if source=="All" else df_ts_g["transactions"],
                name="Orders",line=dict(color="#1D9E75",width=2),mode="lines+markers",marker_size=4),
                secondary_y=True)
            fig.update_layout(**PLOT, height=250, barmode="stack")
            fig.update_yaxes(title_text="Revenue K ج",secondary_y=False)
            fig.update_yaxes(title_text="Orders",secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

        with cr:
            st.markdown(sh("Sessions & Bounce Rate","Daily","#D85A30"), unsafe_allow_html=True)
            fig2 = make_subplots(specs=[[{"secondary_y":True}]])
            df_d = df_ts_g.groupby("date", as_index=False).sum(numeric_only=True) if source=="All" else df_ts_g
            fig2.add_trace(go.Bar(x=df_d["date"],y=df_d["sessions"]/1000,
                name="Sessions K",marker_color="rgba(50,102,173,.6)"), secondary_y=False)
            if "bounce_rate" in df_d.columns:
                fig2.add_trace(go.Scatter(x=df_d["date"],y=df_d["bounce_rate"]*100,
                    name="Bounce %",line=dict(color="#D85A30",width=2),
                    fill="tozeroy",fillcolor="rgba(220,38,38,.06)"), secondary_y=True)
            fig2.update_layout(**PLOT, height=250)
            fig2.update_yaxes(title_text="Sessions K",secondary_y=False)
            fig2.update_yaxes(title_text="Bounce %",secondary_y=True,ticksuffix="%")
            st.plotly_chart(fig2, use_container_width=True)

    # New vs Returning
    st.markdown(sh("New vs Returning","Revenue & Session Split","#7C3AED"), unsafe_allow_html=True)
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        df_nr2 = df_nr.groupby("new_vs_returning", as_index=False).sum(numeric_only=True)
        nr_cols = ["sessions","purchase_revenue","transactions"]
        for c in nr_cols:
            if c in df_nr2.columns: df_nr2[c] = df_nr2[c].apply(safe)

        fig3 = go.Figure()
        segs = df_nr2["new_vs_returning"].tolist()
        clrs = ["#3266AD" if s=="returning" else "#7C3AED" for s in segs]
        fig3.add_trace(go.Bar(x=segs,y=df_nr2["purchase_revenue"] if "purchase_revenue" in df_nr2 else [],
            name="Revenue",marker_color=clrs,text=[fc(v) for v in (df_nr2["purchase_revenue"] if "purchase_revenue" in df_nr2 else [])],
            textposition="outside"))
        fig3.update_layout(**PLOT, height=220, title_text="Revenue by User Type")
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# 2. FUNNEL
# ══════════════════════════════════════════════════════════════════
elif tab == "Funnel":
    st.markdown(sh("Sales Funnel","Item Viewed → Purchase","#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading funnel data..."):
        df_f = load_single(API_KEY, source,
            ["item_name","items_viewed","items_added_to_cart","checkouts","items_purchased"], d0, d1)
        df_ov2 = load(API_KEY, source,
            ["purchase_revenue","transactions","add_to_carts","checkouts"],
            ["sessions"], "date", d0, d1)

    viewed   = safe(df_f["items_viewed"].sum()) if not df_f.empty and "items_viewed" in df_f else 0
    carted   = safe(df_f["items_added_to_cart"].sum()) if not df_f.empty and "items_added_to_cart" in df_f else 0
    ckout    = safe(df_ov2["checkouts"].sum()) if not df_ov2.empty and "checkouts" in df_ov2 else 0
    purch    = safe(df_ov2["transactions"].sum()) if not df_ov2.empty and "transactions" in df_ov2 else 0

    if viewed == 0: viewed = safe(df_ov2["sessions"].sum()) if not df_ov2.empty and "sessions" in df_ov2 else 1

    steps = [
        ("Items Viewed", viewed, 100.0, "#3266AD"),
        ("Add to Cart",  carted, carted/viewed*100 if viewed else 0, "#378ADD"),
        ("Checkout",     ckout,  ckout/viewed*100 if viewed else 0,  "#85B7EB"),
        ("Purchase",     purch,  purch/viewed*100 if viewed else 0,  "#1D9E75"),
    ]

    for lbl, cnt, pct, clr in steps:
        w = max(pct, 0.5)
        st.markdown(f"""<div class="funnel-row">
  <div class="funnel-label">{lbl}</div>
  <div class="funnel-track">
    <div class="funnel-fill" style="width:{w}%;background:{clr}">
      {'&nbsp;'+fn(cnt) if w>8 else ''}
    </div>
  </div>
  <div class="funnel-pct" style="color:{clr}">{pct:.2f}%</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    v2c = carted/viewed*100 if viewed else 0
    c2k = ckout/carted*100 if carted else 0
    k2p = purch/ckout*100 if ckout else 0

    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(kpi("View → Cart",fp(v2c),f"⚠ {100-v2c:.1f}% drop","warn","",COLORS[2]), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Cart → Checkout",fp(c2k),f"⚠ {100-c2k:.1f}% abandon","down" if c2k<50 else "warn","",COLORS[4]), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Checkout → Buy",fp(k2p),f"⚠ {100-k2p:.1f}% drop","down" if k2p<50 else "warn","",COLORS[4] if k2p<50 else COLORS[1]), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    fig = go.Figure(go.Funnel(
        y=["Items Viewed","Add to Cart","Checkout","Purchase"],
        x=[viewed, carted, ckout, purch],
        textinfo="value+percent initial",
        marker=dict(color=["#3266AD","#378ADD","#85B7EB","#1D9E75"]),
        connector=dict(line=dict(color="#E5E7EB",width=1)),
    ))
    fig.update_layout(**PLOT, height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Web vs App funnel comparison
    if source == "All" and "_src" in df_ov2.columns:
        st.markdown(sh("Web vs App — Funnel Comparison","","#7C3AED"), unsafe_allow_html=True)
        rows = []
        for lbl in ["Web","App"]:
            d = df_ov2[df_ov2["_src"]==lbl]
            _s = safe(d["sessions"].sum()) if "sessions" in d else 0
            _c = safe(d["add_to_carts"].sum()) if "add_to_carts" in d else 0
            _k = safe(d["checkouts"].sum()) if "checkouts" in d else 0
            _p = safe(d["transactions"].sum()) if "transactions" in d else 0
            _v2c = _c/_s*100 if _s else 0
            _c2k = _k/_c*100 if _c else 0
            _k2p = _p/_k*100 if _k else 0
            rows.append(f"""<tr>
  <td><b>{lbl}</b></td><td>{fn(_s)}</td><td>{fn(_c)}</td><td>{fn(_k)}</td><td>{fn(_p)}</td>
  <td>{fp(_v2c)}</td><td>{fp(_c2k)}</td><td>{fp(_k2p)}</td>
</tr>""")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Source</th><th>Sessions</th><th>Cart</th><th>Checkout</th><th>Purchase</th>
  <th>View→Cart</th><th>Cart→CK</th><th>CK→Buy</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 3. TRAFFIC
# ══════════════════════════════════════════════════════════════════
elif tab == "Traffic":
    st.markdown(sh("Traffic Sources","Sessions & Revenue by Channel","#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading traffic data..."):
        df_ch = load(API_KEY, source,
            ["session_default_channel_group","purchase_revenue","transactions","add_to_carts"],
            ["session_default_channel_group","sessions","bounce_rate"],
            "session_default_channel_group", d0, d1)

        df_utm = load_single(API_KEY, source,
            ["session_manual_campaign_name","session_default_channel_group","sessions","purchase_revenue","transactions"], d0, d1)

    t_opts = (["Combined","Web","App"] if source=="All" else [source])
    t_sel = st.tabs(t_opts) if source=="All" else [st.container()]

    def render_traffic(df, container):
        with container:
            if df.empty or "session_default_channel_group" not in df.columns:
                st.info("No channel data available."); return
            for c in ["sessions","purchase_revenue","transactions","bounce_rate"]:
                if c in df.columns: df[c] = df[c].apply(safe)
            df = df[df["session_default_channel_group"].notna() & (df["session_default_channel_group"]!="")]
            g = df.groupby("session_default_channel_group").sum(numeric_only=True).reset_index()
            g = g[g["sessions"]>5].sort_values("purchase_revenue",ascending=False)
            if g.empty: st.info("No data."); return

            cl, cr = st.columns(2)
            max_s = g["sessions"].max() or 1
            max_r = g["purchase_revenue"].max() or 1
            with cl:
                st.markdown("**Sessions by Channel**")
                for i,(_,row) in enumerate(g.head(8).iterrows()):
                    st.markdown(bar(row["session_default_channel_group"],
                        row["sessions"]/max_s*100, COLORS[i%len(COLORS)], fn(row["sessions"])), unsafe_allow_html=True)
            with cr:
                st.markdown("**Revenue by Channel**")
                for i,(_,row) in enumerate(g.sort_values("purchase_revenue",ascending=False).head(8).iterrows()):
                    st.markdown(bar(row["session_default_channel_group"],
                        row["purchase_revenue"]/max_r*100, COLORS[i%len(COLORS)], fc(row["purchase_revenue"])), unsafe_allow_html=True)

            st.markdown(sh("Channel Efficiency","CVR & Rev/Session","#EF9F27"), unsafe_allow_html=True)
            rows_html = []
            for _,row in g.iterrows():
                s=row["sessions"]; r=row.get("purchase_revenue",0); o=row.get("transactions",0)
                _cvr=o/s*100 if s else 0; rps=r/s if s else 0
                bd = '<span class="badge bg">Best</span>' if _cvr>=1.5 else \
                     '<span class="badge bb">Good</span>' if _cvr>=0.8 else \
                     '<span class="badge ba">Review</span>' if _cvr>=0.3 else \
                     '<span class="badge br">Weak</span>'
                rows_html.append(f"<tr><td><b>{row['session_default_channel_group']}</b></td>"
                    f"<td>{fn(s)}</td><td>{fc(r)}</td><td>{fn(o)}</td>"
                    f"<td style='color:{'#059669' if _cvr>=1 else '#D97706' if _cvr>=.5 else '#DC2626'}'><b>{fp(_cvr,2)}</b></td>"
                    f"<td>{fc(rps,1)}</td><td>{bd}</td></tr>")
            st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
  <th>CVR</th><th>Rev/Session</th><th>Rating</th>
</tr></thead><tbody>{''.join(rows_html)}</tbody></table>""", unsafe_allow_html=True)
            csv_btn(g, "⬇ Export Channels CSV", f"channels_{d0}_{d1}.csv")

    if source == "All":
        with t_sel[0]: render_traffic(df_ch, st.container())
        for i, lbl in enumerate(["Web","App"],1):
            sub = df_ch[df_ch["_src"]==lbl].copy() if "_src" in df_ch.columns else pd.DataFrame()
            with t_sel[i]: render_traffic(sub, st.container())
    else:
        render_traffic(df_ch, t_sel[0])

    # UTM table
    st.markdown(sh("UTM Campaign Sources","session_manual_campaign_name","#7C3AED"), unsafe_allow_html=True)
    if not df_utm.empty and "session_manual_campaign_name" in df_utm.columns:
        ex = ["(organic)","(not set)","(referral)","(direct)","(none)",""]
        df_utmf = df_utm[~df_utm["session_manual_campaign_name"].isin(ex)].copy()
        df_utmf = df_utmf[df_utmf["session_manual_campaign_name"].notna()]
        if not df_utmf.empty:
            ug = df_utmf.groupby("session_manual_campaign_name").sum(numeric_only=True).reset_index()
            ug = ug.sort_values("purchase_revenue",ascending=False)
            rows_utm = []
            for _,row in ug.head(20).iterrows():
                s=row.get("sessions",0); r=row.get("purchase_revenue",0); o=row.get("transactions",0)
                _cvr=o/s*100 if s else 0
                rows_utm.append(f"<tr><td>{row['session_manual_campaign_name']}</td>"
                    f"<td>{fn(s)}</td><td>{fc(r)}</td><td>{fn(o)}</td>"
                    f"<td>{fp(_cvr,2)}</td></tr>")
            st.markdown(f"""<table class="stbl"><thead><tr>
  <th>UTM Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th>
</tr></thead><tbody>{''.join(rows_utm)}</tbody></table>""", unsafe_allow_html=True)
            csv_btn(ug, "⬇ Export UTM CSV", f"utm_{d0}_{d1}.csv")
        else:
            st.info("No UTM campaign data found.")


# ══════════════════════════════════════════════════════════════════
# 4. DEVICES
# ══════════════════════════════════════════════════════════════════
elif tab == "Devices":
    st.markdown(sh("Device Performance","Mobile vs Desktop vs Tablet","#7C3AED"), unsafe_allow_html=True)

    with st.spinner("Loading device data..."):
        df_dv = load(API_KEY, source,
            ["devicecategory","purchase_revenue","transactions"],
            ["devicecategory","sessions","bounce_rate","engagement_rate"],
            "devicecategory", d0, d1)

    def render_devices(df, label=""):
        if df.empty or "devicecategory" not in df.columns:
            st.info("No device data."); return
        for c in ["sessions","purchase_revenue","transactions","bounce_rate"]:
            if c in df.columns: df[c] = df[c].apply(safe)
        dev_colors = {"mobile":"#3266AD","desktop":"#6B7280","tablet":"#1D9E75"}
        main = df[df["devicecategory"].isin(["mobile","desktop","tablet"])].copy()
        if main.empty: st.info("No device data."); return

        total_s = main["sessions"].sum() or 1
        cols = st.columns(len(main))
        for i,(_,row) in enumerate(main.iterrows()):
            dev = row["devicecategory"]; clr = dev_colors.get(dev,"#6B7280")
            br_v = safe(row.get("bounce_rate",0))*100
            ses_pct = row["sessions"]/total_s*100
            with cols[i]:
                st.markdown(kpi(dev.title(), f"{ses_pct:.1f}%",
                    f"Bounce: {br_v:.1f}%", "down" if br_v>55 else "warn",
                    f"Sessions:{fn(row['sessions'])} Rev:{fc(row.get('purchase_revenue',0))}", clr),
                    unsafe_allow_html=True)

        cl, cr = st.columns(2)
        with cl:
            st.markdown(sh("Revenue Split","","#1D9E75"), unsafe_allow_html=True)
            fig = go.Figure(go.Pie(
                labels=main["devicecategory"].str.title(),
                values=main["purchase_revenue"],
                marker_colors=[dev_colors.get(d,"#6B7280") for d in main["devicecategory"]],
                hole=0.55, textinfo="label+percent", textfont_size=11,
            ))
            fig.update_layout(**PLOT, height=240)
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.markdown(sh("Bounce Rate","","#D85A30"), unsafe_allow_html=True)
            fig2 = go.Figure(go.Bar(
                x=main["devicecategory"].str.title(),
                y=main["bounce_rate"]*100 if "bounce_rate" in main else [0]*len(main),
                marker_color=[dev_colors.get(d,"#6B7280") for d in main["devicecategory"]],
                text=[f"{r*100:.1f}%" for r in main.get("bounce_rate",[0]*len(main))],
                textposition="outside",
            ))
            fig2.update_layout(**PLOT, height=240, yaxis=dict(ticksuffix="%",range=[0,80],gridcolor="#F3F4F6"))
            st.plotly_chart(fig2, use_container_width=True)
        csv_btn(main, "⬇ Export Devices CSV", f"devices{'_'+label if label else ''}_{d0}_{d1}.csv")

    if source == "All" and "_src" in df_dv.columns:
        t1,t2,t3 = st.tabs(["Combined","Web","App"])
        with t1: render_devices(df_dv.groupby("devicecategory",as_index=False).sum(numeric_only=True))
        with t2: render_devices(df_dv[df_dv["_src"]=="Web"].copy(),"web")
        with t3: render_devices(df_dv[df_dv["_src"]=="App"].copy(),"app")
    else:
        render_devices(df_dv)


# ══════════════════════════════════════════════════════════════════
# 5. E-COMMERCE
# ══════════════════════════════════════════════════════════════════
elif tab == "E-Commerce":
    st.markdown(sh("E-Commerce","Products & Categories","#1D9E75"), unsafe_allow_html=True)

    with st.spinner("Loading e-commerce data..."):
        df_cat = load_single(API_KEY, source,
            ["item_category","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart","checkouts","transactions"], d0, d1)
        df_sub = load_single(API_KEY, source,
            ["item_category","item_category2","item_category3","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"], d0, d1)
        df_prod = load_single(API_KEY, source,
            ["item_name","item_revenue","items_purchased","items_viewed","items_added_to_cart"], d0, d1)

    if not df_cat.empty and "item_category" in df_cat.columns:
        for c in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if c in df_cat.columns: df_cat[c] = df_cat[c].apply(safe)

        df_cf = df_cat[df_cat["item_category"].isin(RANEEN_CATS)].groupby("item_category",as_index=False).sum(numeric_only=True)
        df_cf = df_cf.sort_values("gross_item_revenue",ascending=False)

        tot_ir  = df_cf["gross_item_revenue"].sum()
        tot_un  = df_cf["items_purchased"].sum()
        avg_up  = tot_ir/tot_un if tot_un else 0

        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(kpi("Item Revenue",fc(tot_ir),"All categories","up","",COLORS[1]), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Units Sold",fn(tot_un),"Items purchased","up","",COLORS[0]), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Avg Unit Price",fc(avg_up,0),"Revenue / Units","neu","",COLORS[3]), unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        cl,cr = st.columns(2)
        max_r = df_cf["gross_item_revenue"].max() or 1
        with cl:
            st.markdown(sh("Revenue by Category","","#1D9E75"), unsafe_allow_html=True)
            for i,(_,row) in enumerate(df_cf.head(10).iterrows()):
                icon = CAT_ICONS.get(row["item_category"],"")
                st.markdown(bar(f"{icon} {row['item_category']}", row["gross_item_revenue"]/max_r*100,
                    COLORS[i%len(COLORS)], fc(row["gross_item_revenue"])), unsafe_allow_html=True)
        with cr:
            st.markdown(sh("Cart-to-View Rate","","#EF9F27"), unsafe_allow_html=True)
            df_cf["cvr_rate"] = df_cf.apply(
                lambda r: r["items_added_to_cart"]/r["items_viewed"]*100 if r.get("items_viewed",0)>0 else 0, axis=1)
            df_cv = df_cf.sort_values("cvr_rate",ascending=False)
            max_cv = df_cv["cvr_rate"].max() or 1
            for _,row in df_cv.head(10).iterrows():
                clr = "#059669" if row["cvr_rate"]>6 else "#D97706" if row["cvr_rate"]>3 else "#DC2626"
                icon = CAT_ICONS.get(row["item_category"],"")
                st.markdown(bar(f"{icon} {row['item_category']}", row["cvr_rate"]/max_cv*100,
                    clr, f"{row['cvr_rate']:.1f}%"), unsafe_allow_html=True)

        # Category Funnel Table
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Category Funnel","Views → Cart → Checkout → Purchase","#3266AD"), unsafe_allow_html=True)

        # 4-column funnel chart
        fig_cf = go.Figure()
        cats_sorted = df_cf.sort_values("gross_item_revenue",ascending=False).head(8)
        metrics_f = [("items_viewed","Views","#85B7EB"),("items_added_to_cart","Cart","#378ADD"),
                     ("checkouts" if "checkouts" in df_cf else "items_added_to_cart","Checkout","#3266AD"),
                     ("items_purchased","Purchase","#1D9E75")]
        for col, name, clr in metrics_f:
            if col in df_cf.columns:
                fig_cf.add_trace(go.Bar(
                    name=name,
                    x=[CAT_ICONS.get(c,"")+c for c in cats_sorted["item_category"]],
                    y=cats_sorted[col], marker_color=clr, opacity=0.85))
        fig_cf.update_layout(**PLOT, barmode="group", height=300)
        st.plotly_chart(fig_cf, use_container_width=True)

        # Funnel table
        f_rows = []
        for _,row in df_cf.iterrows():
            v=row.get("items_viewed",0); c_=row.get("items_added_to_cart",0)
            k=row.get("checkouts",c_); p=row.get("items_purchased",0); r=row.get("gross_item_revenue",0)
            v2c=c_/v*100 if v else 0; c2k=k/c_*100 if c_ else 0
            k2p=p/k*100 if k else 0; v2p=p/v*100 if v else 0
            bc=lambda x: "bg" if x>6 else "ba" if x>3 else "br"
            icon=CAT_ICONS.get(row["item_category"],"")
            f_rows.append(f"<tr><td>{icon} {row['item_category']}</td>"
                f"<td>{fn(v)}</td>"
                f"<td>{fn(c_)} <span class='badge {bc(v2c)}'>{v2c:.1f}%</span></td>"
                f"<td>{fn(k)} <span class='badge {bc(c2k)}'>{c2k:.1f}%</span></td>"
                f"<td>{fn(p)} <span class='badge {bc(k2p)}'>{k2p:.1f}%</span></td>"
                f"<td><span class='badge {bc(v2p)}'>{v2p:.1f}%</span></td>"
                f"<td><b style='color:#059669'>{fc(r)}</b></td></tr>")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Category</th><th>Views</th><th>Cart (V→C%)</th><th>Checkout (C→K%)</th>
  <th>Purchase (K→P%)</th><th>V→Buy%</th><th>Revenue</th>
</tr></thead><tbody>{''.join(f_rows)}</tbody></table>""", unsafe_allow_html=True)
        csv_btn(df_cf, "⬇ Export Category CSV", f"categories_{d0}_{d1}.csv")

    # Category Drill-Down (3 levels)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(sh("Category Drill-Down","3-Level Exploration","#7C3AED"), unsafe_allow_html=True)

    if not df_sub.empty and "item_category" in df_sub.columns:
        sel1 = st.selectbox("Category (Level 1)", [""] + RANEEN_CATS, key="dd1")
        if sel1 and "item_category2" in df_sub.columns:
            sub2 = df_sub[df_sub["item_category"]==sel1]["item_category2"].dropna().unique().tolist()
            sub2 = [s for s in sub2 if s not in ["","(not set)"]]
            sel2 = st.selectbox("Sub-Category (Level 2)", ["All"] + sub2, key="dd2")

            mask = df_sub["item_category"]==sel1
            if sel2 != "All" and sel2:
                mask &= df_sub["item_category2"]==sel2
                if "item_category3" in df_sub.columns:
                    sub3 = df_sub[mask]["item_category3"].dropna().unique().tolist()
                    sub3 = [s for s in sub3 if s not in ["","(not set)"]]
                    sel3 = st.selectbox("Sub-Sub-Category (Level 3)", ["All"] + sub3, key="dd3")
                    if sel3 != "All" and sel3: mask &= df_sub["item_category3"]==sel3

            df_drill = df_sub[mask].copy()
            for c in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
                if c in df_drill.columns: df_drill[c] = df_drill[c].apply(safe)

            dim2 = "item_category2" if sel2=="All" else ("item_category3" if "item_category3" in df_drill.columns and sel2!="All" else "item_category2")
            if dim2 in df_drill.columns:
                dg = df_drill.groupby(dim2,as_index=False).sum(numeric_only=True)
                dg = dg[dg["gross_item_revenue"]>0].sort_values("gross_item_revenue",ascending=False)
                if not dg.empty:
                    max_dr = dg["gross_item_revenue"].max() or 1
                    max_du = dg["items_purchased"].max() or 1
                    dl, dr = st.columns(2)
                    with dl:
                        st.markdown(f"**Revenue — {sel2 if sel2!='All' else sel1}**")
                        for i,(_,row) in enumerate(dg.head(10).iterrows()):
                            st.markdown(bar(str(row[dim2]),row["gross_item_revenue"]/max_dr*100,
                                COLORS[i%len(COLORS)],fc(row["gross_item_revenue"])), unsafe_allow_html=True)
                    with dr:
                        st.markdown(f"**Units — {sel2 if sel2!='All' else sel1}**")
                        for i,(_,row) in enumerate(dg.sort_values("items_purchased",ascending=False).head(10).iterrows()):
                            st.markdown(bar(str(row[dim2]),row["items_purchased"]/max_du*100,
                                COLORS[i%len(COLORS)],fn(row["items_purchased"])+" units"), unsafe_allow_html=True)
                    dr_rows = []
                    for i,(_,row) in enumerate(dg.iterrows(),1):
                        v_=row.get("items_viewed",0); c_=row.get("items_added_to_cart",0)
                        cr_=c_/v_*100 if v_ else 0; ap=row["gross_item_revenue"]/row["items_purchased"] if row["items_purchased"] else 0
                        dr_rows.append(f"<tr><td style='color:#6B7280'>{i}</td>"
                            f"<td><b>{row[dim2]}</b></td>"
                            f"<td style='color:#059669'>{fc(row['gross_item_revenue'])}</td>"
                            f"<td>{fn(row['items_purchased'])}</td>"
                            f"<td>{fn(v_)}</td>"
                            f"<td><span class='badge {'bg' if cr_>6 else 'ba' if cr_>3 else 'br'}'>{cr_:.1f}%</span></td>"
                            f"<td>{fc(ap,0)}</td></tr>")
                    st.markdown(f"""<table class="stbl"><thead><tr>
  <th>#</th><th>Name</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th><th>AOV</th>
</tr></thead><tbody>{''.join(dr_rows)}</tbody></table>""", unsafe_allow_html=True)
                    csv_btn(dg, "⬇ Export Drill-Down CSV", f"drilldown_{d0}_{d1}.csv")

    # Top 15 Products
    if not df_prod.empty and "item_name" in df_prod.columns:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Top 15 Products","by Revenue","#3266AD"), unsafe_allow_html=True)
        for c in ["item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if c in df_prod.columns: df_prod[c] = df_prod[c].apply(safe)
        df_top = df_prod[df_prod["item_revenue"]>0].sort_values("item_revenue",ascending=False).head(15)
        p_rows = []
        for i,(_,row) in enumerate(df_top.iterrows(),1):
            nm=str(row["item_name"])[:55]+("…" if len(str(row["item_name"]))>55 else "")
            v_=row.get("items_viewed",0); c_=row.get("items_added_to_cart",0)
            cr_=c_/v_*100 if v_ else 0
            p_rows.append(f"<tr><td style='color:#6B7280'>{i}</td><td>{nm}</td>"
                f"<td style='color:#059669'><b>{fc(row['item_revenue'])}</b></td>"
                f"<td>{int(row['items_purchased'])}</td><td>{fn(v_)}</td>"
                f"<td><span class='badge {'bg' if cr_>8 else 'ba' if cr_>4 else 'br'}'>{cr_:.1f}%</span></td></tr>")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th>
</tr></thead><tbody>{''.join(p_rows)}</tbody></table>""", unsafe_allow_html=True)
        csv_btn(df_top, "⬇ Export Products CSV", f"products_{d0}_{d1}.csv")


# ══════════════════════════════════════════════════════════════════
# 6. CAMPAIGNS
# ══════════════════════════════════════════════════════════════════
elif tab == "Campaigns":
    st.markdown(sh("Campaigns Performance","Google Ads & Meta","#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading campaign data..."):
        df_gads = load_single(API_KEY, source,
            ["session_google_ads_campaign_name","sessions","purchase_revenue","transactions","add_to_carts","checkouts"], d0, d1)
        df_meta = load_single(API_KEY, source,
            ["session_manual_campaign_name","sessions","purchase_revenue","transactions","add_to_carts"], d0, d1)
        df_cp = load_single(API_KEY, source,
            ["session_google_ads_campaign_name","item_name","item_revenue","items_purchased"], d0, d1)
        df_mp = load_single(API_KEY, source,
            ["session_manual_campaign_name","item_name","item_revenue","items_purchased"], d0, d1)

    t_gads, t_meta = st.tabs(["📢 Google Ads","📘 Meta Campaigns"])

    # ── GOOGLE ADS
    with t_gads:
        st.markdown(sh("Google Ads Campaigns","","#3266AD"), unsafe_allow_html=True)
        if not df_gads.empty and "session_google_ads_campaign_name" in df_gads.columns:
            ex = ["(not set)","(organic)","","(none)"]
            df_g = df_gads[~df_gads["session_google_ads_campaign_name"].isin(ex)].copy()
            df_g = df_g[df_g["session_google_ads_campaign_name"].notna()]
            for c in ["sessions","purchase_revenue","transactions","add_to_carts"]:
                if c in df_g.columns: df_g[c] = df_g[c].apply(safe)
            gg = df_g.groupby("session_google_ads_campaign_name",as_index=False).sum(numeric_only=True)
            gg["cvr"] = gg.apply(lambda r: r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0, axis=1)
            gg["rps"] = gg.apply(lambda r: r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0, axis=1)
            gg = gg.sort_values("purchase_revenue",ascending=False)

            if not gg.empty:
                best = gg.iloc[0]; worst_cvr = gg.loc[gg["cvr"].idxmin()]
                bc1,bc2,bc3,bc4 = st.columns(4)
                with bc1: st.markdown(kpi("Best Campaign",best["session_google_ads_campaign_name"][-20:],fc(best["purchase_revenue"]),"up","",COLORS[0]), unsafe_allow_html=True)
                with bc2: st.markdown(kpi("Total Sessions",fn(gg["sessions"].sum()),"Google Ads","neu","",COLORS[3]), unsafe_allow_html=True)
                with bc3: best_cvr_r = gg.loc[gg["cvr"].idxmax()]; st.markdown(kpi("Best CVR",best_cvr_r["session_google_ads_campaign_name"][-20:],fp(best_cvr_r["cvr"],2),"up","",COLORS[1]), unsafe_allow_html=True)
                with bc4: st.markdown(kpi("Worst CVR",worst_cvr["session_google_ads_campaign_name"][-20:],fp(worst_cvr["cvr"],2),"down","",COLORS[4]), unsafe_allow_html=True)

                g_rows = []
                for _,row in gg.iterrows():
                    cv=row["cvr"]
                    bd='<span class="badge bg">Best</span>' if cv>=1.5 else \
                       '<span class="badge bb">Good</span>' if cv>=0.8 else \
                       '<span class="badge ba">Review</span>' if cv>=0.3 else \
                       '<span class="badge br">Weak</span>'
                    g_rows.append(f"<tr><td style='font-size:11px'>{row['session_google_ads_campaign_name']}</td>"
                        f"<td>{fn(row['sessions'])}</td><td style='color:#059669'><b>{fc(row['purchase_revenue'])}</b></td>"
                        f"<td>{int(row['transactions'])}</td>"
                        f"<td style='color:{'#059669' if cv>=1 else '#D97706' if cv>=.5 else '#DC2626'}'><b>{fp(cv,2)}</b></td>"
                        f"<td>{fc(row['rps'],1)}</td><td>{bd}</td></tr>")
                st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
  <th>CVR</th><th>Rev/Session</th><th>Rating</th>
</tr></thead><tbody>{''.join(g_rows)}</tbody></table>""", unsafe_allow_html=True)
                csv_btn(gg, "⬇ Export Google Ads CSV", f"google_ads_{d0}_{d1}.csv")

                # Products drill-down
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                st.markdown(sh("Campaign → Products","","#7C3AED"), unsafe_allow_html=True)
                camp_sel = st.selectbox("Select Campaign", gg["session_google_ads_campaign_name"].tolist(), key="gads_camp")
                if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
                    df_cp_f = df_cp[df_cp["session_google_ads_campaign_name"]==camp_sel].copy()
                    for c in ["item_revenue","items_purchased"]:
                        if c in df_cp_f.columns: df_cp_f[c] = df_cp_f[c].apply(safe)
                    df_cp_f = df_cp_f[df_cp_f["item_revenue"]>0].sort_values("item_revenue",ascending=False)
                    if not df_cp_f.empty:
                        kk1,kk2,kk3 = st.columns(3)
                        with kk1: st.markdown(kpi("Revenue",fc(df_cp_f["item_revenue"].sum()),"","up","",COLORS[3]), unsafe_allow_html=True)
                        with kk2: st.markdown(kpi("Units",fn(df_cp_f["items_purchased"].sum()),"","up","",COLORS[0]), unsafe_allow_html=True)
                        with kk3: st.markdown(kpi("SKUs",str(len(df_cp_f)),"Products","neu","",COLORS[1]), unsafe_allow_html=True)
                        cp_rows = []
                        for i,(_,row) in enumerate(df_cp_f.iterrows(),1):
                            nm=str(row["item_name"])[:55]+("…" if len(str(row["item_name"]))>55 else "")
                            units=int(safe(row.get("items_purchased",0)))
                            rev=safe(row.get("item_revenue",0))
                            aov_=rev/units if units else 0
                            cp_rows.append(f"<tr><td style='color:#6B7280'>{i}</td><td>{nm}</td>"
                                f"<td style='color:#7C3AED'><b>{fc(rev)}</b></td><td>{units}</td>"
                                f"<td>{fc(aov_,0)}</td></tr>")
                        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>AOV</th>
</tr></thead><tbody>{''.join(cp_rows)}</tbody></table>""", unsafe_allow_html=True)
                        csv_btn(df_cp_f, "⬇ Export", f"camp_prods_{d0}_{d1}.csv")
                    else:
                        st.info("No product data for this campaign.")
        else:
            st.info("No Google Ads campaign data found.")

    # ── META
    with t_meta:
        st.markdown(sh("Meta / Facebook Campaigns","","#7C3AED"), unsafe_allow_html=True)
        if not df_meta.empty and "session_manual_campaign_name" in df_meta.columns:
            ex_meta = ["(organic)","(not set)","(referral)","(direct)","(none)","",
                       "(data deleted)","(not provided)"]
            df_m = df_meta[~df_meta["session_manual_campaign_name"].isin(ex_meta)].copy()
            df_m = df_m[df_m["session_manual_campaign_name"].notna()]
            for c in ["sessions","purchase_revenue","transactions","add_to_carts"]:
                if c in df_m.columns: df_m[c] = df_m[c].apply(safe)
            mg = df_m.groupby("session_manual_campaign_name",as_index=False).sum(numeric_only=True)
            mg["cvr"] = mg.apply(lambda r: r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0, axis=1)
            mg["rps"] = mg.apply(lambda r: r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0, axis=1)
            mg["aov"] = mg.apply(lambda r: r["purchase_revenue"]/r["transactions"] if r["transactions"]>0 else 0, axis=1)

            def detect_type(name):
                n=str(name).lower()
                if any(k in n for k in ["rt |","retarg","retention","remarketing"]): return "Retargeting"
                if any(k in n for k in ["conv","conversion","purchase"]): return "Conv"
                if any(k in n for k in ["prosp","prospecting","awareness"]): return "Prospecting"
                return "Traffic"
            mg["type"] = mg["session_manual_campaign_name"].apply(detect_type)
            type_colors = {"Retargeting":"#7C3AED","Conv":"#059669","Prospecting":"#3266AD","Traffic":"#D97706"}
            mg = mg.sort_values("purchase_revenue",ascending=False)

            if not mg.empty:
                m_rows = []
                for _,row in mg.iterrows():
                    cv=row["cvr"]; tp=row["type"]
                    tbd=f'<span class="badge" style="background:{type_colors.get(tp,"#6B7280")}22;color:{type_colors.get(tp,"#6B7280")}">{tp}</span>'
                    bd='<span class="badge bg">Best</span>' if cv>=1.5 else \
                       '<span class="badge bb">Good</span>' if cv>=0.8 else \
                       '<span class="badge ba">Review</span>' if cv>=0.3 else \
                       '<span class="badge br">Weak</span>'
                    m_rows.append(f"<tr><td style='font-size:11px'>{row['session_manual_campaign_name']}</td>"
                        f"<td>{tbd}</td><td>{fn(row['sessions'])}</td>"
                        f"<td style='color:#059669'><b>{fc(row['purchase_revenue'])}</b></td>"
                        f"<td>{int(row['transactions'])}</td>"
                        f"<td style='color:{'#059669' if cv>=1 else '#D97706' if cv>=.5 else '#DC2626'}'><b>{fp(cv,2)}</b></td>"
                        f"<td>{fc(row['rps'],1)}</td><td>{fc(row['aov'],0)}</td><td>{bd}</td></tr>")
                st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Campaign</th><th>Type</th><th>Sessions</th><th>Revenue</th>
  <th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>AOV</th><th>Rating</th>
</tr></thead><tbody>{''.join(m_rows)}</tbody></table>""", unsafe_allow_html=True)
                csv_btn(mg, "⬇ Export Meta CSV", f"meta_{d0}_{d1}.csv")

                # Meta Products drill-down
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                st.markdown(sh("Meta Campaign → Products","","#7C3AED"), unsafe_allow_html=True)
                meta_sel = st.selectbox("Select Meta Campaign", mg["session_manual_campaign_name"].tolist(), key="meta_camp")
                if not df_mp.empty and "session_manual_campaign_name" in df_mp.columns:
                    df_mp_f = df_mp[df_mp["session_manual_campaign_name"]==meta_sel].copy()
                    for c in ["item_revenue","items_purchased"]:
                        if c in df_mp_f.columns: df_mp_f[c] = df_mp_f[c].apply(safe)
                    df_mp_f = df_mp_f[df_mp_f["item_revenue"]>0].sort_values("item_revenue",ascending=False)
                    if not df_mp_f.empty:
                        mk1,mk2,mk3 = st.columns(3)
                        with mk1: st.markdown(kpi("Revenue",fc(df_mp_f["item_revenue"].sum()),"","up","",COLORS[3]), unsafe_allow_html=True)
                        with mk2: st.markdown(kpi("Units",fn(df_mp_f["items_purchased"].sum()),"","up","",COLORS[0]), unsafe_allow_html=True)
                        with mk3: st.markdown(kpi("SKUs",str(len(df_mp_f)),"","neu","",COLORS[1]), unsafe_allow_html=True)
                        mp_rows=[]
                        for i,(_,row) in enumerate(df_mp_f.iterrows(),1):
                            nm=str(row["item_name"])[:55]+("…" if len(str(row["item_name"]))>55 else "")
                            u=int(safe(row.get("items_purchased",0))); rv=safe(row.get("item_revenue",0))
                            mp_rows.append(f"<tr><td style='color:#6B7280'>{i}</td><td>{nm}</td>"
                                f"<td style='color:#7C3AED'><b>{fc(rv)}</b></td><td>{u}</td>"
                                f"<td>{fc(rv/u if u else 0,0)}</td></tr>")
                        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>AOV</th>
</tr></thead><tbody>{''.join(mp_rows)}</tbody></table>""", unsafe_allow_html=True)
                        csv_btn(df_mp_f,"⬇ Export","f_meta_prods_{d0}_{d1}.csv")
                    else:
                        st.info("No product data for this campaign.")
        else:
            st.info("No Meta campaign data found.")


# ══════════════════════════════════════════════════════════════════
# 7. USERS
# ══════════════════════════════════════════════════════════════════
elif tab == "Users":
    st.markdown(sh("Users","New vs Returning & Acquisition","#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading user data..."):
        df_nr3 = load(API_KEY, source,
            ["new_vs_returning","purchase_revenue","transactions","add_to_carts"],
            ["new_vs_returning","sessions","active_users","bounce_rate","average_session_duration"],
            "new_vs_returning", d0, d1)
        df_dev_u = load(API_KEY, source,
            ["devicecategory","purchase_revenue","transactions","add_to_carts"],
            ["devicecategory","sessions","bounce_rate","average_session_duration"],
            "devicecategory", d0, d1)
        df_acq = load(API_KEY, source,
            ["session_default_channel_group","purchase_revenue","transactions"],
            ["session_default_channel_group","sessions","active_users"],
            "session_default_channel_group", d0, d1)
        # Cohort - monthly
        df_coh = load(API_KEY, source,
            ["date","new_vs_returning","purchase_revenue","transactions"],
            ["date","new_vs_returning","sessions"],
            "date", d0, d1)

    if not df_nr3.empty and "new_vs_returning" in df_nr3.columns:
        for c in ["sessions","active_users","purchase_revenue","transactions","add_to_carts","bounce_rate","average_session_duration"]:
            if c in df_nr3.columns: df_nr3[c] = df_nr3[c].apply(safe)
        nr_g = df_nr3.groupby("new_vs_returning",as_index=False).sum(numeric_only=True)
        if "bounce_rate" in nr_g.columns:
            nr_g["bounce_rate"] = df_nr3.groupby("new_vs_returning")["bounce_rate"].mean().values

        ret = nr_g[nr_g["new_vs_returning"]=="returning"]
        new_ = nr_g[nr_g["new_vs_returning"]=="new"]
        tot_act = nr_g["active_users"].sum() if "active_users" in nr_g else 0
        ret_rv  = safe(ret["purchase_revenue"].sum()) if "purchase_revenue" in ret else 0
        new_rv  = safe(new_["purchase_revenue"].sum()) if "purchase_revenue" in new_ else 0
        tot_rv  = ret_rv + new_rv

        u1,u2,u3,u4 = st.columns(4)
        with u1: st.markdown(kpi("Active Users",fn(tot_act),"Total","neu","",COLORS[0]), unsafe_allow_html=True)
        with u2: st.markdown(kpi("New Users",fn(new_["sessions"].sum() if "sessions" in new_ else 0),"New sessions","up","",COLORS[1]), unsafe_allow_html=True)
        with u3: st.markdown(kpi("Returning Users",fn(ret["sessions"].sum() if "sessions" in ret else 0),"Returning sessions","up","",COLORS[3]), unsafe_allow_html=True)
        with u4: st.markdown(kpi("Returning Revenue",fc(ret_rv),f"▲ {ret_rv/tot_rv*100 if tot_rv else 0:.1f}% of total","up","",COLORS[1]), unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Comparison charts
        cl,cr = st.columns(2)
        segs = ["returning","new"]
        seg_colors = ["#3266AD","#7C3AED"]
        with cl:
            st.markdown(sh("Revenue by Segment","","#1D9E75"), unsafe_allow_html=True)
            fig = go.Figure()
            for s, c in zip(segs, seg_colors):
                d = nr_g[nr_g["new_vs_returning"]==s]
                r = safe(d["purchase_revenue"].sum()) if "purchase_revenue" in d else 0
                fig.add_trace(go.Bar(name=s.title(), x=[s.title()], y=[r], marker_color=c,
                    text=[fc(r)], textposition="outside"))
            fig.update_layout(**PLOT, height=220, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.markdown(sh("CVR Comparison","","#EF9F27"), unsafe_allow_html=True)
            fig2 = go.Figure()
            for s, c in zip(segs, seg_colors):
                d = nr_g[nr_g["new_vs_returning"]==s]
                ses=safe(d["sessions"].sum()) if "sessions" in d else 0
                txn=safe(d["transactions"].sum()) if "transactions" in d else 0
                cvr_=txn/ses*100 if ses else 0
                fig2.add_trace(go.Bar(name=s.title(), x=[s.title()], y=[cvr_], marker_color=c,
                    text=[fp(cvr_,2)], textposition="outside"))
            fig2.update_layout(**PLOT, height=220, showlegend=False, yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, use_container_width=True)

        # Full comparison table
        st.markdown(sh("Full Segment Comparison","","#3266AD"), unsafe_allow_html=True)
        nr_rows = []
        for s in ["returning","new","(not set)"]:
            d = nr_g[nr_g["new_vs_returning"]==s]
            if d.empty: continue
            ses=safe(d["sessions"].sum()) if "sessions" in d else 0
            rev=safe(d["purchase_revenue"].sum()) if "purchase_revenue" in d else 0
            txn=safe(d["transactions"].sum()) if "transactions" in d else 0
            crt=safe(d["add_to_carts"].sum()) if "add_to_carts" in d else 0
            br_=safe(d["bounce_rate"].mean())*100 if "bounce_rate" in d else 0
            asd_=safe(d["average_session_duration"].mean()) if "average_session_duration" in d else 0
            cvr_=txn/ses*100 if ses else 0; aov_=rev/txn if txn else 0
            ca_=(1-txn/crt)*100 if crt else 0; sm_=int(asd_//60); ss_=int(asd_%60)
            bc_="bg" if s=="returning" else "bb"
            nr_rows.append(f"<tr><td><span class='badge {bc_}'>{s}</span></td>"
                f"<td>{fn(ses)}</td><td style='color:#059669'>{fc(rev)}</td>"
                f"<td>{fn(txn)}</td><td>{fp(cvr_,2)}</td><td>{fc(aov_,0)}</td>"
                f"<td>{fp(ca_)}</td><td>{fp(br_)}</td><td>{sm_}:{ss_:02d}</td></tr>")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
  <th>CVR</th><th>AOV</th><th>Cart Abandon</th><th>Bounce</th><th>Avg Session</th>
</tr></thead><tbody>{''.join(nr_rows)}</tbody></table>""", unsafe_allow_html=True)
        csv_btn(nr_g,"⬇ Export Users CSV",f"users_{d0}_{d1}.csv")

    # Device table
    if not df_dev_u.empty and "devicecategory" in df_dev_u.columns:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Users by Device","","#7C3AED"), unsafe_allow_html=True)
        for c in ["sessions","purchase_revenue","transactions","add_to_carts","bounce_rate","average_session_duration"]:
            if c in df_dev_u.columns: df_dev_u[c] = df_dev_u[c].apply(safe)
        du_g = df_dev_u.groupby("devicecategory",as_index=False).agg({
            c:"sum" for c in ["sessions","purchase_revenue","transactions","add_to_carts"] if c in df_dev_u.columns
        })
        if "bounce_rate" in df_dev_u.columns:
            br_mean = df_dev_u.groupby("devicecategory")["bounce_rate"].mean().reset_index()
            du_g = pd.merge(du_g, br_mean, on="devicecategory", how="left")
        if "average_session_duration" in df_dev_u.columns:
            asd_mean = df_dev_u.groupby("devicecategory")["average_session_duration"].mean().reset_index()
            du_g = pd.merge(du_g, asd_mean, on="devicecategory", how="left")

        du_rows = []
        for _,row in du_g.iterrows():
            s=row.get("sessions",0); r=row.get("purchase_revenue",0); o=row.get("transactions",0)
            crt=row.get("add_to_carts",0); br__=safe(row.get("bounce_rate",0))*100
            asd__=safe(row.get("average_session_duration",0)); sm__=int(asd__//60); ss__=int(asd__%60)
            cvr__=o/s*100 if s else 0; aov__=r/o if o else 0; rps=r/s if s else 0
            du_rows.append(f"<tr><td><b>{row['devicecategory']}</b></td>"
                f"<td>{fn(s)}</td><td style='color:#059669'>{fc(r)}</td>"
                f"<td>{fn(o)}</td><td>{fp(cvr__,2)}</td><td>{fc(aov__,0)}</td>"
                f"<td>{fc(rps,1)}</td><td>{fp(br__)}</td><td>{sm__}:{ss__:02d}</td></tr>")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Device</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
  <th>CVR</th><th>AOV</th><th>Rev/Session</th><th>Bounce</th><th>Avg Session</th>
</tr></thead><tbody>{''.join(du_rows)}</tbody></table>""", unsafe_allow_html=True)
        csv_btn(du_g,"⬇ Export Device CSV",f"device_users_{d0}_{d1}.csv")

    # Acquisition Channel
    if not df_acq.empty and "session_default_channel_group" in df_acq.columns:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Acquisition Channel","","#1D9E75"), unsafe_allow_html=True)
        for c in ["sessions","purchase_revenue","transactions","active_users"]:
            if c in df_acq.columns: df_acq[c] = df_acq[c].apply(safe)
        acq_g = df_acq.groupby("session_default_channel_group",as_index=False).sum(numeric_only=True)
        acq_g = acq_g.sort_values("purchase_revenue",ascending=False)
        acq_rows = []
        for _,row in acq_g.iterrows():
            s=row.get("sessions",0); r=row.get("purchase_revenue",0); o=row.get("transactions",0)
            au=row.get("active_users",0); cvr__=o/s*100 if s else 0; aov__=r/o if o else 0
            acq_rows.append(f"<tr><td><b>{row['session_default_channel_group']}</b></td>"
                f"<td>{fn(s)}</td><td>{fn(au)}</td><td style='color:#059669'>{fc(r)}</td>"
                f"<td>{fn(o)}</td><td>{fp(cvr__,2)}</td><td>{fc(aov__,0)}</td></tr>")
        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Channel</th><th>Sessions</th><th>Active Users</th><th>Revenue</th>
  <th>Orders</th><th>CVR</th><th>AOV</th>
</tr></thead><tbody>{''.join(acq_rows)}</tbody></table>""", unsafe_allow_html=True)
        csv_btn(acq_g,"⬇ Export Acquisition CSV",f"acquisition_{d0}_{d1}.csv")

    # Cohort
    if not df_coh.empty and "new_vs_returning" in df_coh.columns and "date" in df_coh.columns:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(sh("Monthly Cohort Analysis","New vs Returning retention","#3266AD"), unsafe_allow_html=True)
        df_coh["date"] = pd.to_datetime(df_coh["date"], errors="coerce")
        df_coh = df_coh.dropna(subset=["date"])
        df_coh["month"] = df_coh["date"].dt.to_period("M").astype(str)
        for c in ["sessions","purchase_revenue","transactions"]:
            if c in df_coh.columns: df_coh[c] = df_coh[c].apply(safe)

        coh_rows_html = []
        coh_data = []
        for month, mg in df_coh.groupby("month"):
            new_d = mg[mg["new_vs_returning"]=="new"]
            ret_d = mg[mg["new_vs_returning"]=="returning"]
            ns = safe(new_d["sessions"].sum()); rs = safe(ret_d["sessions"].sum()); ts = ns+rs
            nr_rev = safe(new_d["purchase_revenue"].sum()); rr_rev = safe(ret_d["purchase_revenue"].sum())
            tot_rev_m = nr_rev + rr_rev
            ret_rate = rs/ts*100 if ts else 0
            n_txn = safe(new_d["transactions"].sum()); r_txn = safe(ret_d["transactions"].sum())
            n_cvr = n_txn/ns*100 if ns else 0; r_cvr = r_txn/rs*100 if rs else 0
            rev_ret = rr_rev/tot_rev_m*100 if tot_rev_m else 0
            clr = "#059669" if ret_rate>40 else "#D97706" if ret_rate>20 else "#DC2626"
            bar_w = min(ret_rate, 100)
            coh_rows_html.append(
                f"<tr><td><b>{month}</b></td><td>{fn(ns)}</td><td>{fn(rs)}</td>"
                f"<td><div style='display:flex;align-items:center;gap:6px'>"
                f"<div style='flex:1;height:8px;background:#F3F4F6;border-radius:4px'>"
                f"<div style='width:{bar_w:.1f}%;height:100%;background:{clr};border-radius:4px'></div></div>"
                f"<span style='color:{clr};font-weight:600;font-size:11px'>{fp(ret_rate)}</span></div></td>"
                f"<td>{fc(nr_rev)}</td><td>{fc(rr_rev)}</td>"
                f"<td><span style='color:{clr};font-weight:600'>{fp(rev_ret)}</span></td>"
                f"<td>{fp(n_cvr,2)}</td><td>{fp(r_cvr,2)}</td></tr>")
            coh_data.append({"month":month,"new_sessions":ns,"ret_sessions":rs,
                "ret_rate":ret_rate,"new_rev":nr_rev,"ret_rev":rr_rev,
                "rev_ret":rev_ret,"new_cvr":n_cvr,"ret_cvr":r_cvr})

        st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Month</th><th>New Ses</th><th>Ret Ses</th><th>Retention Rate</th>
  <th>New Rev</th><th>Ret Rev</th><th>Rev Retention</th><th>New CVR</th><th>Ret CVR</th>
</tr></thead><tbody>{''.join(coh_rows_html)}</tbody></table>""", unsafe_allow_html=True)

        if coh_data:
            df_coh_out = pd.DataFrame(coh_data)
            fig_coh = make_subplots(specs=[[{"secondary_y":True}]])
            fig_coh.add_trace(go.Bar(x=df_coh_out["month"],y=df_coh_out["new_rev"]/1000,
                name="New Rev K",marker_color="#7C3AED",opacity=.8), secondary_y=False)
            fig_coh.add_trace(go.Bar(x=df_coh_out["month"],y=df_coh_out["ret_rev"]/1000,
                name="Returning Rev K",marker_color="#3266AD",opacity=.8), secondary_y=False)
            fig_coh.add_trace(go.Scatter(x=df_coh_out["month"],y=df_coh_out["ret_rate"],
                name="Retention%",line=dict(color="#059669",width=2),mode="lines+markers",marker_size=5),
                secondary_y=True)
            fig_coh.update_layout(**PLOT, barmode="group", height=280)
            fig_coh.update_yaxes(title_text="Revenue K ج",secondary_y=False)
            fig_coh.update_yaxes(title_text="Retention %",secondary_y=True,ticksuffix="%")
            st.plotly_chart(fig_coh, use_container_width=True)
            csv_btn(df_coh_out,"⬇ Export Cohort CSV",f"cohort_{d0}_{d1}.csv")


# ══════════════════════════════════════════════════════════════════
# 8. INSIGHTS
# ══════════════════════════════════════════════════════════════════
elif tab == "Insights":
    st.markdown(sh("Strategic Insights","Auto-generated Action Plan","#DC2626"), unsafe_allow_html=True)

    with st.spinner("Analyzing data..."):
        df_ins_ov = load(API_KEY, source,
            ["purchase_revenue","transactions","add_to_carts","checkouts"],
            ["sessions","bounce_rate"],
            "date", d0, d1)
        df_ins_cp = load_single(API_KEY, source,
            ["session_google_ads_campaign_name","sessions","purchase_revenue","transactions"], d0, d1)
        df_ins_ch = load(API_KEY, source,
            ["session_default_channel_group","purchase_revenue","transactions"],
            ["session_default_channel_group","sessions"],
            "session_default_channel_group", d0, d1)
        df_ins_dv = load(API_KEY, source,
            ["devicecategory","purchase_revenue","transactions"],
            ["devicecategory","sessions","bounce_rate"],
            "devicecategory", d0, d1)
        df_ins_nr = load(API_KEY, source,
            ["new_vs_returning","purchase_revenue","transactions"],
            ["new_vs_returning","sessions"],
            "new_vs_returning", d0, d1)

    def g(df,col): return safe(df[col].sum()) if not df.empty and col in df else 0
    def ga(df,col): return safe(df[col].mean()) if not df.empty and col in df else 0

    tot_s_i  = g(df_ins_ov,"sessions"); tot_r_i  = g(df_ins_ov,"purchase_revenue")
    tot_o_i  = g(df_ins_ov,"transactions"); tot_c_i  = g(df_ins_ov,"add_to_carts")
    tot_ck_i = g(df_ins_ov,"checkouts"); br_i = ga(df_ins_ov,"bounce_rate")*100
    aov_i    = tot_r_i/tot_o_i if tot_o_i else 0
    cvr_i    = tot_o_i/tot_s_i*100 if tot_s_i else 0
    ca_i     = (1-tot_o_i/tot_c_i)*100 if tot_c_i else 0

    st.markdown("### 🔴 P1 — Immediate (This Week)")

    st.markdown(ins("🔴",f"Cart Abandonment {ca_i:.1f}%",
        f"From {fn(tot_c_i)} add-to-cart, only {fn(tot_o_i)} purchased. "
        "Abandoned Cart Email + Exit-intent popup = +15-20% revenue.", "i-red"), unsafe_allow_html=True)

    if br_i > 55:
        st.markdown(ins("🔴",f"Bounce Rate Critical: {br_i:.1f}%",
            "Above acceptable threshold. Review Landing Pages & page speed immediately.", "i-red"), unsafe_allow_html=True)

    if cvr_i < 0.5:
        st.markdown(ins("🔴",f"CVR Very Low: {cvr_i:.2f}%",
            "Conversion rate below 0.5%. Review checkout flow, trust signals, and pricing.", "i-red"), unsafe_allow_html=True)

    if not df_ins_cp.empty and "session_google_ads_campaign_name" in df_ins_cp.columns:
        for c in ["sessions","purchase_revenue","transactions"]:
            if c in df_ins_cp.columns: df_ins_cp[c] = df_ins_cp[c].apply(safe)
        weak = df_ins_cp[
            df_ins_cp["session_google_ads_campaign_name"].notna() &
            (df_ins_cp["session_google_ads_campaign_name"]!="(not set)") &
            (df_ins_cp["sessions"]>50000) &
            (df_ins_cp.apply(lambda r: r["transactions"]/r["sessions"] if r["sessions"]>0 else 0, axis=1) < 0.002)
        ]
        for _,row in weak.head(2).iterrows():
            cv=row["transactions"]/row["sessions"]*100 if row["sessions"]>0 else 0
            st.markdown(ins("🔴",f"Weak Campaign: {row['session_google_ads_campaign_name']}",
                f"{fn(row['sessions'])} sessions with CVR {cv:.2f}% only. Review targeting & landing pages.", "i-red"), unsafe_allow_html=True)

    st.markdown("### ⚠️ P2 — Important (This Month)")

    if not df_ins_dv.empty and "devicecategory" in df_ins_dv.columns:
        df_ins_dv["bounce_rate"] = df_ins_dv["bounce_rate"].apply(safe) if "bounce_rate" in df_ins_dv else 0
        desk = df_ins_dv[df_ins_dv["devicecategory"]=="desktop"]
        mob  = df_ins_dv[df_ins_dv["devicecategory"]=="mobile"]
        if not desk.empty and not mob.empty:
            d_br = safe(desk["bounce_rate"].mean())*100; m_br = safe(mob["bounce_rate"].mean())*100
            if d_br > m_br + 5:
                st.markdown(ins("⚠️",f"Desktop Bounce {d_br:.1f}% vs Mobile {m_br:.1f}%",
                    f"Desktop bounce {d_br-m_br:.1f}% higher than mobile. Improve desktop UX & page load.", "i-amb"), unsafe_allow_html=True)

    if not df_ins_ch.empty and "session_default_channel_group" in df_ins_ch.columns:
        for c in ["sessions","purchase_revenue","transactions"]:
            if c in df_ins_ch.columns: df_ins_ch[c] = df_ins_ch[c].apply(safe)
        ps = df_ins_ch[df_ins_ch["session_default_channel_group"]=="Paid Social"]
        pq = df_ins_ch[df_ins_ch["session_default_channel_group"]=="Paid Search"]
        if not ps.empty and not pq.empty:
            ps_cvr=ps["transactions"].sum()/ps["sessions"].sum()*100 if ps["sessions"].sum()>0 else 0
            pq_cvr=pq["transactions"].sum()/pq["sessions"].sum()*100 if pq["sessions"].sum()>0 else 0
            if pq_cvr > ps_cvr*1.5:
                st.markdown(ins("⚠️",f"Paid Search CVR ({pq_cvr:.2f}%) >> Paid Social ({ps_cvr:.2f}%)",
                    "Reallocate budget from Paid Social to Paid Search to improve ROAS.", "i-amb"), unsafe_allow_html=True)

    st.markdown("### ✅ P3 — Growth Opportunities (This Quarter)")

    if not df_ins_nr.empty and "new_vs_returning" in df_ins_nr.columns:
        for c in ["sessions","purchase_revenue","transactions"]:
            if c in df_ins_nr.columns: df_ins_nr[c] = df_ins_nr[c].apply(safe)
        ret_r = df_ins_nr[df_ins_nr["new_vs_returning"]=="returning"]
        ret_rv2 = safe(ret_r["purchase_revenue"].sum()) if "purchase_revenue" in ret_r else 0
        ret_pct2 = ret_rv2/tot_r_i*100 if tot_r_i else 0
        st.markdown(ins("✅",f"Returning Users = {ret_pct2:.1f}% of Revenue",
            "Strong brand loyalty. Launch Loyalty Program + Personalized offers to increase LTV.", "i-grn"), unsafe_allow_html=True)

    st.markdown(ins("✅",f"High AOV: {fc(aov_i,0)}",
        "High-ticket customers exist. Installment plans + buy-now-pay-later = improve CVR significantly.", "i-grn"), unsafe_allow_html=True)

    st.markdown(ins("▲","Checkout Drop-Off Opportunity",
        f"Cart→Checkout→Purchase: {fn(tot_c_i)}→{fn(tot_ck_i)}→{fn(tot_o_i)}. "
        "Streamline checkout (1-page checkout, saved addresses, payment variety) = quick win.", "i-blu"), unsafe_allow_html=True)

    # Summary Table
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(sh("Summary Metrics","","#6B7280"), unsafe_allow_html=True)
    summary = pd.DataFrame({
        "Metric":["Sessions","Revenue","Orders","AOV","CVR","Bounce Rate","Cart Abandon","Checkout Drop"],
        "Value":[fn(tot_s_i),fc(tot_r_i),fn(tot_o_i),fc(aov_i,0),fp(cvr_i,2),fp(br_i),fp(ca_i),
                 fp((1-tot_o_i/tot_ck_i)*100 if tot_ck_i else 0)],
        "Status":["✅","✅","✅","✅",
                  "⚠️" if cvr_i<1 else "✅",
                  "⚠️" if br_i>50 else "✅",
                  "🔴" if ca_i>85 else "⚠️",
                  "⚠️" if (1-tot_o_i/tot_ck_i)*100>50 else "✅"],
    })
    s_rows = []
    for _,row in summary.iterrows():
        s_rows.append(f"<tr><td><b>{row['Metric']}</b></td><td>{row['Value']}</td><td>{row['Status']}</td></tr>")
    st.markdown(f"""<table class="stbl"><thead><tr>
  <th>Metric</th><th>Value</th><th>Status</th>
</tr></thead><tbody>{''.join(s_rows)}</tbody></table>""", unsafe_allow_html=True)
    csv_btn(summary,"⬇ Export Summary CSV",f"insights_summary_{d0}_{d1}.csv")
