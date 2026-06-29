
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SLOB MRP Intelligence", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top:1.2rem;}
.hero{background:linear-gradient(135deg,#0f172a,#1e293b,#172554);border-radius:24px;padding:30px 34px;margin-bottom:20px;color:white}
.hero h1{font-size:2.1rem;margin-bottom:.2rem}.hero p{color:#cbd5e1;margin:0}
.metric-card{background:#fff;border:1px solid #dbe3ef;border-radius:18px;padding:18px;min-height:115px;box-shadow:0 8px 22px rgba(15,23,42,.06)}
.metric-label{color:#64748b;font-size:.78rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em}
.metric-value{color:#0f172a;font-size:1.7rem;font-weight:900;margin-top:6px}.metric-sub{color:#64748b;font-size:.85rem}
.card{background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:18px 20px;box-shadow:0 8px 22px rgba(15,23,42,.05);margin-bottom:12px}
.card-title{font-weight:900;font-size:1.08rem;color:#0f172a;margin-top:10px}.card-sub{color:#64748b;font-size:.9rem;margin-bottom:10px}
.badge{display:inline-block;padding:5px 11px;border-radius:999px;font-size:.76rem;font-weight:900}
.high{color:#7f1d1d;background:#fee2e2;border:1px solid #fca5a5}.med{color:#78350f;background:#fef3c7;border:1px solid #fcd34d}
.low{color:#14532d;background:#dcfce7;border:1px solid #86efac}.rank{color:#1e3a8a;background:#dbeafe;border:1px solid #93c5fd}
.section-header{font-size:1.35rem;font-weight:900;color:#0f172a;margin-top:10px}.small-muted{color:#64748b;font-size:.88rem;margin-bottom:12px}
.insight{border-left:5px solid #2563eb;background:#eff6ff;color:#1e3a8a;padding:13px 15px;border-radius:12px;margin-top:10px}
.warn{border-left:5px solid #d97706;background:#fffbeb;color:#78350f;padding:13px 15px;border-radius:12px;margin-top:10px}
.stButton > button{border-radius:12px;height:3rem;font-weight:900}
</style>
""", unsafe_allow_html=True)

REQUIRED_COLUMNS = [
    "Plant","SKU","Description","Product_Family","Unrestricted_Stock","Allocated_Stock","Blocked_Stock","QI_Stock","UOM",
    "Inventory_Value","Total_Shelf_Life_Days","Remaining_Shelf_Life_Days","Expiry_Date",
    "Forecast_30D","Forecast_90D","Demand_30D","Demand_90D","Avg_Monthly_Consumption",
    "Open_PO_Qty","Open_Production_Qty","MOQ","Lead_Time_Days","Customer_Count","Material_Status"
]

@st.cache_data
def sample_data():
    rows = [
        ["CS01","GJ-40","Garlic Juice 40%","Garlic Juice",12500,3000,0,0,"kg",187500,540,72,"2026-09-05",1500,5200,2100,6100,1800,0,0,1000,14,4,"Active"],
        ["CS01","GJ-45","Garlic Juice 45%","Garlic Juice",4200,0,0,0,"kg",67200,540,210,"2027-01-21",300,900,0,400,250,0,0,1000,21,2,"Active"],
        ["BP01","OJ-65","Onion Concentrate 65%","Onion Concentrate",9800,2500,0,0,"kg",142100,365,45,"2026-08-09",900,2500,700,1800,800,0,0,1500,18,3,"Active"],
        ["CS01","RP-20","Rosemary Powder 20 mesh","Powder",1800,0,0,0,"kg",54000,720,390,"2027-07-20",800,2600,650,2400,850,0,0,500,28,6,"Active"],
        ["BP01","GB-A","Garlic Blend A","Blend",7600,1000,500,0,"kg",159600,365,28,"2026-07-23",0,400,0,350,150,0,0,1000,15,1,"Phase-out"],
        ["CS01","OB-B","Onion Blend B","Blend",5200,0,0,600,"kg",93600,365,160,"2026-12-02",100,300,0,0,80,0,0,1000,15,1,"Active"],
        ["BP01","GCP-99","Garlic Custom Premix 99","Custom Premix",1100,0,0,0,"kg",39600,365,330,"2027-05-21",0,0,0,0,0,0,0,1000,30,1,"Inactive"],
        ["CS01","OJ-50","Onion Juice 50%","Onion Juice",6400,4200,0,0,"kg",96000,365,95,"2026-09-28",2500,8100,2200,7600,2600,0,0,1000,12,5,"Active"],
        ["BP01","GP-10","Garlic Puree 10%","Puree",9000,1000,0,0,"kg",81000,240,38,"2026-08-02",300,900,250,700,320,0,0,1000,10,2,"Active"],
        ["CS01","SPC-01","Special Customer SKU 01","Custom Premix",3500,0,0,0,"kg",87500,365,260,"2027-03-12",0,0,0,0,0,0,0,1000,25,1,"Active"],
    ]
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)

def safe_div(a,b):
    if b == 0 or pd.isna(b):
        return np.nan
    return a / b

def classify_risk(row):
    risk_points, drivers = 0, []
    status = str(row["Material_Status"]).strip().lower()
    rem = row["Remaining_Shelf_Life_Days"]
    value = row["Inventory_Value"]
    demand90 = row["Demand_90D"]
    fcst90 = row["Forecast_90D"]
    coverage = row["Coverage_vs_90D_Demand"]

    if status in ["inactive","phase-out","obsolete","blocked"]:
        risk_points += 35; drivers.append("material status risk")
    if rem <= 30:
        risk_points += 35; drivers.append("critical shelf life")
    elif rem <= 60:
        risk_points += 28; drivers.append("short shelf life")
    elif rem <= 90:
        risk_points += 20; drivers.append("approaching shelf-life risk")
    if demand90 <= 0 and fcst90 <= 0:
        risk_points += 30; drivers.append("no demand or forecast")
    elif not pd.isna(coverage) and coverage > 2:
        risk_points += 25; drivers.append("stock exceeds 2x 90-day demand/forecast")
    elif not pd.isna(coverage) and coverage > 1.2:
        risk_points += 15; drivers.append("stock exceeds 90-day demand/forecast")
    if value >= 100000:
        risk_points += 15; drivers.append("high inventory value")
    elif value >= 50000:
        risk_points += 10; drivers.append("material value exposure")
    if row["Blocked_Stock"] > 0 or row["QI_Stock"] > 0:
        risk_points += 8; drivers.append("blocked/QI stock present")

    level = "High" if risk_points >= 70 else "Medium" if risk_points >= 40 else "Low"
    return level, min(risk_points, 100), ", ".join(drivers) if drivers else "normal inventory position"

def proposed_action(row):
    rem = row["Remaining_Shelf_Life_Days"]
    net = row["Net_Available_Stock"]
    demand90 = row["Demand_90D"]
    fcst90 = row["Forecast_90D"]
    status = str(row["Material_Status"]).strip().lower()
    coverage = row["Coverage_vs_90D_Demand"]

    if status in ["inactive","phase-out","obsolete"] and demand90 == 0 and fcst90 == 0:
        return "Escalate for liquidation, substitution, customer proposal, or write-off decision", "Medium", "High" if row["Inventory_Value"] >= 50000 else "Medium"
    if rem <= 60 and net > 0:
        return "Prioritize immediate allocation; propose customer pull-in or discounted consumption", "Low", "High"
    if not pd.isna(coverage) and coverage > 2:
        return "Freeze new production/procurement; consume existing stock first and review forecast accuracy", "Low", "High" if row["Inventory_Value"] >= 50000 else "Medium"
    if demand90 > 0 and net > demand90:
        return "Use stock to cover near-term demand and reduce future planned receipts", "Low", "Medium"
    if row["Customer_Count"] <= 1 and net > 0:
        return "Check customer-specific conversion, substitution, or repack opportunity", "Medium", "Medium"
    if row["Blocked_Stock"] > 0 or row["QI_Stock"] > 0:
        return "Push QA disposition to release, rework, downgrade, or block for write-off", "Medium", "Medium"
    return "Monitor in weekly SLOB review; no urgent action required", "Low", "Low"

def rank_label(impact, effort):
    if impact == "High" and effort == "Low": return "Low Effort / High Impact"
    if impact == "High" and effort == "Medium": return "Medium Effort / High Impact"
    if impact == "Medium" and effort == "Low": return "Low Effort / Medium Impact"
    if impact == "Medium" and effort == "Medium": return "Medium Effort / Medium Impact"
    if impact == "Low" and effort == "Medium": return "Medium Effort / Low Impact"
    return "Low Effort / Low Impact"

def process(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, missing

    d = df.copy()
    numeric = [c for c in REQUIRED_COLUMNS if c not in ["Plant","SKU","Description","Product_Family","UOM","Expiry_Date","Material_Status"]]
    for c in numeric:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)

    d["Net_Available_Stock"] = d["Unrestricted_Stock"] - d["Allocated_Stock"]
    d["Total_Visible_Stock"] = d["Unrestricted_Stock"] + d["Blocked_Stock"] + d["QI_Stock"]
    d["Demand_Forecast_90D_Max"] = d[["Demand_90D","Forecast_90D"]].max(axis=1)
    d["Coverage_vs_90D_Demand"] = d.apply(lambda r: safe_div(r["Net_Available_Stock"], r["Demand_Forecast_90D_Max"]), axis=1)
    d["Months_of_Coverage"] = d.apply(lambda r: safe_div(r["Net_Available_Stock"], r["Avg_Monthly_Consumption"]), axis=1)
    d["Excess_vs_90D"] = d.apply(lambda r: max(r["Net_Available_Stock"] - r["Demand_Forecast_90D_Max"], 0), axis=1)
    d["Excess_Value_Estimate"] = d.apply(lambda r: (r["Excess_vs_90D"] / r["Unrestricted_Stock"] * r["Inventory_Value"]) if r["Unrestricted_Stock"] > 0 else 0, axis=1)
    d[["Risk_Level","Risk_Score","Risk_Drivers"]] = d.apply(lambda r: pd.Series(classify_risk(r)), axis=1)
    d[["Proposed_Action","Effort","Impact"]] = d.apply(lambda r: pd.Series(proposed_action(r)), axis=1)
    d["Impact_Effort_Rank"] = d.apply(lambda r: rank_label(r["Impact"], r["Effort"]), axis=1)
    rank_score = {"Low Effort / High Impact":1,"Medium Effort / High Impact":2,"Low Effort / Medium Impact":3,"Medium Effort / Medium Impact":4,"Medium Effort / Low Impact":5,"Low Effort / Low Impact":6}
    d["Priority_Sort"] = d["Impact_Effort_Rank"].map(rank_score).fillna(9)*1000000 - d["Risk_Score"]*1000 - d["Inventory_Value"]
    d["Owner_Suggestion"] = np.select(
        [
            d["Proposed_Action"].str.contains("QA", case=False, na=False),
            d["Proposed_Action"].str.contains("customer|liquidation|substitution", case=False, na=False),
            d["Proposed_Action"].str.contains("Freeze|planned receipts|forecast", case=False, na=False)
        ],
        ["QA","Customer Care / Commercial","Planner / MRP"],
        default="Planner"
    )
    d["AI_Insight"] = d.apply(lambda r: (
        f"{r['SKU']} is {r['Risk_Level']} risk. Drivers: {r['Risk_Drivers']}. "
        f"Net available stock is {r['Net_Available_Stock']:,.0f} {r['UOM']}; shelf life remaining is {r['Remaining_Shelf_Life_Days']:,.0f} days. "
        f"Recommended action: {r['Proposed_Action']}."
    ), axis=1)
    return d.sort_values("Priority_Sort"), []

def risk_badge(level):
    if level == "High": return '<span class="badge high">HIGH RISK</span>'
    if level == "Medium": return '<span class="badge med">MEDIUM RISK</span>'
    return '<span class="badge low">LOW RISK</span>'

st.markdown("""
<div class="hero">
  <h1>SLOB MRP Intelligence</h1>
  <p>SAP/MRP-style SKU risk engine using inventory value, shelf life, forecast, demand, allocated stock, blocked stock, and material status.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## Data Input")
use_sample = st.sidebar.toggle("Use sample SAP/MRP data", value=True)
uploaded = st.sidebar.file_uploader("Upload SAP SLOB CSV", type=["csv"])
view = st.sidebar.radio("View", ["Executive Control Tower", "SKU Action List", "SKU Deep Dive", "Data Template"])

if use_sample:
    raw = sample_data()
elif uploaded:
    raw = pd.read_csv(uploaded)
else:
    raw = pd.DataFrame()

if view == "Data Template":
    st.markdown('<div class="section-header">SAP/MRP SLOB Data Template</div>', unsafe_allow_html=True)
    st.dataframe(sample_data().head(0), use_container_width=True)
    st.download_button("Download CSV template", sample_data().head(0).to_csv(index=False).encode("utf-8"), "sap_mrp_slob_template.csv", "text/csv", use_container_width=True)
    st.markdown("Required columns:")
    st.code("\n".join(REQUIRED_COLUMNS))
    st.stop()

if raw.empty:
    st.info("Upload a CSV or activate sample SAP/MRP data.")
    st.stop()

data, missing = process(raw)
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

if view == "Executive Control Tower":
    total_value = data["Inventory_Value"].sum()
    high_value = data.loc[data["Risk_Level"]=="High","Inventory_Value"].sum()
    excess_value = data["Excess_Value_Estimate"].sum()
    quick_wins = len(data[data["Impact_Effort_Rank"]=="Low Effort / High Impact"])
    high_risk = len(data[data["Risk_Level"]=="High"])

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Total Value</div><div class="metric-value">${total_value:,.0f}</div><div class="metric-sub">inventory exposure</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">High Risk Value</div><div class="metric-value">${high_value:,.0f}</div><div class="metric-sub">requires action</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Excess Value</div><div class="metric-value">${excess_value:,.0f}</div><div class="metric-sub">vs 90-day demand/forecast</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Quick Wins</div><div class="metric-value">{quick_wins}</div><div class="metric-sub">low effort / high impact</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">High Risk SKUs</div><div class="metric-value">{high_risk}</div><div class="metric-sub">SKU count</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Top Priority Actions</div>', unsafe_allow_html=True)
    for _, r in data.head(6).iterrows():
        st.markdown(f"""
        <div class="card">
          <div>{risk_badge(r['Risk_Level'])} <span class="badge rank">{r['Impact_Effort_Rank']}</span></div>
          <div class="card-title">{r['SKU']} — {r['Description']}</div>
          <div class="card-sub">{r['Plant']} · {r['Product_Family']} · Value ${r['Inventory_Value']:,.0f} · Net stock {r['Net_Available_Stock']:,.0f} {r['UOM']} · Shelf life {r['Remaining_Shelf_Life_Days']:,.0f} days</div>
          <div class="insight"><b>AI insight:</b> {r['AI_Insight']}</div>
          <div class="warn"><b>Owner:</b> {r['Owner_Suggestion']} · <b>Impact:</b> {r['Impact']} · <b>Effort:</b> {r['Effort']} · <b>Risk drivers:</b> {r['Risk_Drivers']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Impact / Effort Portfolio</div>', unsafe_allow_html=True)
    summary = data.groupby(["Impact_Effort_Rank","Risk_Level"], as_index=False).agg(
        SKU_Count=("SKU","count"),
        Inventory_Value=("Inventory_Value","sum"),
        Excess_Value=("Excess_Value_Estimate","sum")
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

elif view == "SKU Action List":
    st.markdown('<div class="section-header">Ranked SKU Action List</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Sorted low-effort/high-impact first, then risk score and inventory value.</div>', unsafe_allow_html=True)

    risks = st.multiselect("Risk level", ["High","Medium","Low"], default=["High","Medium","Low"])
    ranks = st.multiselect("Impact / effort", list(data["Impact_Effort_Rank"].unique()), default=list(data["Impact_Effort_Rank"].unique()))
    f = data[data["Risk_Level"].isin(risks) & data["Impact_Effort_Rank"].isin(ranks)]

    cols = ["Plant","SKU","Description","Product_Family","Risk_Level","Risk_Score","Impact_Effort_Rank",
            "Inventory_Value","Net_Available_Stock","Allocated_Stock","Remaining_Shelf_Life_Days",
            "Demand_90D","Forecast_90D","Coverage_vs_90D_Demand","Excess_Value_Estimate",
            "Proposed_Action","Owner_Suggestion","AI_Insight"]
    st.dataframe(f[cols], use_container_width=True, hide_index=True)
    st.download_button("Export ranked action list", f.to_csv(index=False).encode("utf-8"), "ranked_slob_mrp_actions.csv", "text/csv", use_container_width=True)

elif view == "SKU Deep Dive":
    st.markdown('<div class="section-header">SKU Deep Dive</div>', unsafe_allow_html=True)
    sku = st.selectbox("Select SKU", data["SKU"].tolist())
    r = data[data["SKU"] == sku].iloc[0]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Risk Score</div><div class="metric-value">{r["Risk_Score"]:.0f}</div><div class="metric-sub">{r["Risk_Level"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Inventory Value</div><div class="metric-value">${r["Inventory_Value"]:,.0f}</div><div class="metric-sub">current exposure</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Net Stock</div><div class="metric-value">{r["Net_Available_Stock"]:,.0f}</div><div class="metric-sub">{r["UOM"]}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Shelf Life</div><div class="metric-value">{r["Remaining_Shelf_Life_Days"]:,.0f}</div><div class="metric-sub">days remaining</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
      <div>{risk_badge(r['Risk_Level'])} <span class="badge rank">{r['Impact_Effort_Rank']}</span></div>
      <div class="card-title">{r['SKU']} — {r['Description']}</div>
      <div class="card-sub">{r['Plant']} · {r['Product_Family']} · Material status: {r['Material_Status']}</div>
      <div class="insight"><b>AI Insight:</b> {r['AI_Insight']}</div>
      <div class="warn"><b>Proposed action:</b> {r['Proposed_Action']}<br><b>Owner:</b> {r['Owner_Suggestion']} · <b>Impact:</b> {r['Impact']} · <b>Effort:</b> {r['Effort']}</div>
    </div>
    """, unsafe_allow_html=True)

    detail_cols = ["Unrestricted_Stock","Allocated_Stock","Blocked_Stock","QI_Stock","Forecast_30D","Forecast_90D","Demand_30D","Demand_90D","Avg_Monthly_Consumption","Coverage_vs_90D_Demand","Months_of_Coverage","Excess_vs_90D","Excess_Value_Estimate","MOQ","Lead_Time_Days","Customer_Count"]
    st.dataframe(pd.DataFrame(data.loc[data["SKU"]==sku, detail_cols].iloc[0]).rename(columns={r.name:"Value"}), use_container_width=True)

st.caption("Prototype for SAP/MRP SLOB decision support. Production version should connect to SAP, demand planning, batch shelf-life data, and Azure OpenAI.")
