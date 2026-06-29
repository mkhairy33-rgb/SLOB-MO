
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta

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
.assess{color:#312e81;background:#ede9fe;border:1px solid #c4b5fd}
.section-header{font-size:1.35rem;font-weight:900;color:#0f172a;margin-top:10px}.small-muted{color:#64748b;font-size:.88rem;margin-bottom:12px}
.insight{border-left:5px solid #2563eb;background:#eff6ff;color:#1e3a8a;padding:13px 15px;border-radius:12px;margin-top:10px}
.warn{border-left:5px solid #d97706;background:#fffbeb;color:#78350f;padding:13px 15px;border-radius:12px;margin-top:10px}
.stButton > button{border-radius:12px;height:3rem;font-weight:900}

.kpi-pill{display:inline-block;border-radius:999px;background:#f1f5f9;border:1px solid #cbd5e1;color:#0f172a;font-size:.78rem;font-weight:800;padding:5px 10px;margin-right:5px;margin-bottom:5px}
.trace{background:#0f172a;color:#e5e7eb;border-radius:16px;padding:14px 16px;font-family:monospace;font-size:.82rem;white-space:pre-wrap}
.good{border-left:5px solid #16a34a;background:#f0fdf4;color:#14532d;padding:13px 15px;border-radius:12px;margin-top:10px}

</style>
""", unsafe_allow_html=True)

REQUIRED_COLUMNS = [
    "Plant","SKU","Description","Material_Type","Plant_Material_Status","Product_Family",
    "Unrestricted_Stock","Allocated_Stock","Blocked_Stock","QI_Stock","Fixed_Issue_Qty","UOM",
    "Inventory_Value","PUP_GC","Total_Shelf_Life_Days","Remaining_Shelf_Life_Days","Batch_Age_Days",
    "Batch_Conditional_Status","Expiry_Date","ABC_Indicator","XYZ_Indicator",
    "Forecast_12M","Forecast_30D","Forecast_90D","Demand_30D","Demand_90D","Avg_Consumption_For_Slow_Moving",
    "Open_PO_Qty","Open_Production_Qty","MOQ","Lead_Time_Days","Customer_Count","Material_Status",
    "Protected_Stock","Strategic_Critical","Storage_Location"
]

OPTIONAL_POLICY_COLUMNS = [
    "Slow_Moving_Months_Threshold","Slow_Moving_Value_Threshold","Excess_Value_Threshold",
    "Obsolete_Value_Threshold","Discard_Value_Threshold","Reserve_Factor"
]

OPTIONAL_PREVENTION_COLUMNS = [
    "Blanket_Contract_Remaining_Qty",
    "Forecast_Trend_90D_Pct",
    "Demand_Trend_90D_Pct",
    "Last_Consumption_Days_Ago",
    "Historical_Consumption_6M",
    "Historical_Consumption_12M",
    "Planner",
    "Customer_Name",
    "Production_Line",
    "Current_Action_Status",
    "Current_Action_Due_Date",
    "Can_Repack",
    "Can_Rework",
    "Can_Transfer",
    "Can_Substitute"
]


DISCARD_REASON_CODES = [
    # Supply Chain Related Discards - IM Decisions
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1201","Reason":"Discards old products (expired)","Description":"Disposal of operational stock as a result of business loss. Inventory authorized by Operations. Operative planning error: local decision, FIFO/FEFO issues, typo errors etc."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1200","Reason":"Discard rejected raw materials","Description":"Raw materials which are rejected and cannot be returned to vendor."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1304","Reason":"Obsolete","Description":"Discard positions with value below local threshold, for example kosher remainders."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1204","Reason":"Transport damage (return)","Description":"Returns due to damages during transportation."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1202","Reason":"Production batch size","Description":"Disposal of product manufactured to a batch dictated by technical or equipment constraints. Minimum batch size is greater than minimum sales order quantity."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1403","Reason":"Production transfer","Description":"Disposal of an item as a result of production transfers."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1203","Reason":"Purchasing position","Description":"Disposal of product purchased to a lot size in excess of EOQ dictated by supplier or procurement considerations. Minimum purchasing lot-size exceeds demand within shelf life; strategic purchasing decisions for crop and/or price reasons."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1303","Reason":"Stock degrade","Description":"Stock degrade. Not applicable in EAME."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1402","Reason":"Formula change","Description":"Disposal of an item as a result of a formula or regulation change."},
    {"Category":"Supply Chain Related Discards","Subcategory":"IM Decisions","Code":"1205","Reason":"Customer care mistakes","Description":"Customer care mistakes."},
    # Supply Chain Related Discards - Commercial
    {"Category":"Supply Chain Related Discards","Subcategory":"Commercial","Code":"1400","Reason":"Discard commercial relevant","Description":"New business but no order; lost business without alert; returns from customer error/goodwill; blanket contract no order; strategic planning decisions."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Commercial","Code":"1405","Reason":"Commercial waste (F.G.)","Description":"Others."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Commercial","Code":"1404","Reason":"Trial","Description":"Disposal of an item as a result of a trial production batch."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Commercial","Code":"1401","Reason":"Design Problem","Description":"Rejection because the flavour as developed cannot be produced at larger scale. QC reject; formula non-conformance due to design issue FC&A."},
    # Supply Chain Related Discards - Cycle Count
    {"Category":"Supply Chain Related Discards","Subcategory":"Cycle Count","Code":"300","Reason":"Lost or Found inventory","Description":"Material lost or found during the year."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Cycle Count","Code":"400","Reason":"Annual/Daily Cycle Count","Description":"Annual stock taking."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Cycle Count","Code":"500","Reason":"Daily Cycle Count","Description":"Daily cycle counting of single positions."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Cycle Count","Code":"1999","Reason":"Annual stock taking","Description":"Annual stock taking for spare parts only."},
    # Supply Chain Related Discards - Not assigned
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"101","Reason":"101","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"102","Reason":"102","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"201","Reason":"201","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"301","Reason":"301","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"401","Reason":"401","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"608","Reason":"608","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1206","Reason":"1206","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1506","Reason":"1506","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1507","Reason":"1507","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1996","Reason":"1996","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1997","Reason":"1997","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"1998","Reason":"1998","Description":"Not assigned."},
    {"Category":"Supply Chain Related Discards","Subcategory":"Not assigned","Code":"#","Reason":"Not assigned","Description":"Not assigned."},

    # Manufacturing Related Discards
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"100","Reason":"Shop Floor Adjustment","Description":"Correction of inventory quantity at container or location level. Includes material left in packaging, product lost as a result of dispensing, and all other weight corrections not listed separately."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"200","Reason":"Spillage Loss (accidental)","Description":"Record material loss as a result of a spill, container breakage, or miscellaneous issue."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"700","Reason":"Automatic Replenishment Correction","Description":"For robots: replenishment weight correction of tank farm bulk storage location. Manual virtual raw material addition so robots do not run empty; reversal done afterwards."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"800","Reason":"Automatic Consumption Correction","Description":"Consumption weight correction of tank farm bulk storage location. LCMS/CMS automatic goods issue correction."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"900","Reason":"Automatic Adjustment","Description":"Weight correction of tank farm bulk storage location when more material is taken from a handling unit than shown available in SAP."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"1000","Reason":"Repack","Description":"Standard loss during repacking activity and adjustment for interim return transport damage."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Weight Correc.SF","Code":"1100","Reason":"Empty Container","Description":"Write-off of residual raw material or finished product material left in a container and unable to be dispensed."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Proc.order scrap","Code":"1110","Reason":"Process Order Scrap Factor","Description":"NOAM: key items with alcohol; offset in material costs."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Rejections","Code":"1300","Reason":"Discard Quality Relevant","Description":"Rejection caused by quality of raw material and intermediates."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Rejections","Code":"1301","Reason":"Compounding Error","Description":"Rejection caused by compounding error: too much, too little, or the wrong ingredient was added."},
    {"Category":"Manufacturing Related Discards","Subcategory":"Rejections","Code":"1302","Reason":"Technical Failure","Description":"Rejection caused by equipment failure."},

    # Sampling Related Discards
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"600","Reason":"Write Off / Sampling Lab","Description":"Standard loss in daily compounding activity and scans to empty."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"604","Reason":"Stock correction","Description":"Adjustment of stock positions. Equal to core business Y/500."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"603","Reason":"Yield correction","Description":"Yield correction after spray dry production."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"601","Reason":"Discard finished product","Description":"Discard collection finished products, NID or expired."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"606","Reason":"Quality rejection","Description":"Quality relevant discard. Equal to core business F4/1300."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"602","Reason":"Discard raw material","Description":"Discard collection raw materials, NID or expired."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"605","Reason":"Damage","Description":"Accidental product damage. Equal to core business F3/200."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"607","Reason":"Automatic correction","Description":"System automatic adjustment. Equal to core business F1/900."},
    {"Category":"Sampling Related Discards","Subcategory":"Sampling","Code":"801","Reason":"GIBB LCMS mg","Description":"SAP / LCMS interface."},

    # Other / Miscellaneous Discards
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1","Reason":"Others","Description":"Others."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1500","Reason":"Formula Management","Description":"Formula Management."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1501","Reason":"Unit of measure allocation adjustment","Description":"Unit of measure allocation adjustment."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1502","Reason":"Quality Difference","Description":"Quality Difference."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1503","Reason":"1503","Description":"1503."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1504","Reason":"Oral Care transfer","Description":"Not for T&W."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1505","Reason":"Local Re-batch","Description":"Local Re-batch."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1600","Reason":"1600","Description":"1600."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1601","Reason":"1601","Description":"1601."},
    {"Category":"Other / Miscellaneous Discards","Subcategory":"Others","Code":"1602","Reason":"Government agency blend","Description":"Government agency blend."},
]

def reason_codes_df():
    return pd.DataFrame(DISCARD_REASON_CODES)

def get_reason_record(code):
    code = str(code)
    for r in DISCARD_REASON_CODES:
        if str(r["Code"]) == code:
            return r
    return {"Category":"Manual Review","Subcategory":"Manual Review","Code":"MANUAL_REVIEW","Reason":"Manual review required","Description":"No safe automatic discard reason code was assigned. Planner must select the correct reason code."}

def recommend_discard_reason(row):
    """Conservative mapping. Assign automatically only when the signal is clear; otherwise force manual review."""
    status = normalize(row.get("Batch_Conditional_Status", ""))
    material_type = str(row.get("Material_Type", "")).upper()
    material_status = normalize(row.get("Material_Status", ""))
    protected = normalize(row.get("Protected_Stock", "")) == "yes"
    strategic = normalize(row.get("Strategic_Critical", "")) not in ["", "no"]

    if protected or strategic:
        return "MANUAL_REVIEW"
    if "9.exp" in status or "expired" in status:
        return "1201"
    if "7.rej" in status or "reject" in status:
        if material_type == "ZROH":
            return "1200"
        return "1300"
    if row.get("Obsolete_Flag", False) or material_status in ["inactive", "phase-out", "obsolete"]:
        return "1304"
    if row.get("Excess_Flag", False) and row.get("Forecast_12M", 0) > 0:
        return "1203"
    if row.get("Slow_Moving_Flag", False):
        return "1201"
    return "MANUAL_REVIEW"

def format_reason_display(record):
    return f"{record['Code']} — {record['Reason']}"

@st.cache_data
def sample_data():
    rows = [
        ["CS01","GJ-40","Garlic Juice 40%","ZFER","40","Garlic Juice",12500,3000,0,0,700,"kg",187500,15,540,72,468,"1.UNR","2026-09-05","A","X",20800,1500,5200,2100,6100,1800,0,0,1000,14,4,"Active","No","No","A001",6,50000,50000,50000,0,0.15],
        ["CS01","GJ-45","Garlic Juice 45%","ZFER","40","Garlic Juice",4200,0,0,0,0,"kg",67200,16,540,210,330,"1.UNR","2027-01-21","B","Y",3600,300,900,0,400,250,0,0,1000,21,2,"Active","No","No","A002",9,30000,30000,30000,0,0.10],
        ["BP01","OJ-65","Onion Concentrate 65%","ZFER","40","Onion Concentrate",9800,2500,0,0,500,"kg",142100,14.5,365,45,320,"1.UNR","2026-08-09","A","Y",10000,900,2500,700,1800,800,0,0,1500,18,3,"Active","No","No","B001",6,50000,50000,50000,0,0.15],
        ["CS01","RP-20","Rosemary Powder 20 mesh","ZROH","30","Powder",1800,0,0,0,0,"kg",54000,30,720,390,330,"1.UNR","2027-07-20","A","X",10400,800,2600,650,2400,850,0,0,500,28,6,"Active","No","No","R001",6,50000,50000,50000,0,0.05],
        ["BP01","GB-A","Garlic Blend A","ZFER","40","Blend",7600,1000,500,0,0,"kg",159600,21,365,28,337,"1.UNR","2026-07-23","C","Z",1200,0,400,0,350,150,0,0,1000,15,1,"Phase-out","No","No","B010",10,30000,30000,30000,0,0.20],
        ["CS01","OB-B","Onion Blend B","ZFER","40","Blend",5200,0,0,600,0,"kg",93600,18,365,160,205,"1.UNR","2026-12-02","C","Z",900,100,300,0,0,80,0,0,1000,15,1,"Active","No","No","C002",10,30000,30000,30000,0,0.15],
        ["BP01","GCP-99","Garlic Custom Premix 99","ZFER","40","Custom Premix",1100,0,0,0,0,"kg",39600,36,365,330,35,"1.UNR","2027-05-21","C","Z",0,0,0,0,0,0,0,0,1000,30,1,"Inactive","No","No","P001",10,30000,30000,30000,0,0.05],
        ["CS01","SPC-01","Special Customer SKU 01","ZFER","40","Custom Premix",3500,0,0,0,0,"kg",87500,25,365,260,105,"1.UNR","2027-03-12","B","Y",0,0,0,0,0,0,0,0,1000,25,1,"Active","Yes","No","P002",9,30000,30000,30000,0,0.05],
        ["CS01","REJ-01","Rejected Batch Example","ZROH","30","Raw",900,0,900,0,0,"kg",18000,20,365,0,365,"7.REJ","2026-06-01","C","Z",0,0,0,0,0,0,0,0,500,10,0,"Active","No","No","Q001",10,30000,30000,30000,0,1.0],
        ["CS01","STR-01","Strategic Critical Material","ZROH","30","Raw",3000,0,0,0,0,"kg",120000,40,720,500,220,"1.UNR","2027-11-01","A","X",0,0,0,0,0,0,0,0,500,45,2,"Active","No","Permanent","S001",6,50000,50000,50000,0,0.05],
    ]
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS + OPTIONAL_POLICY_COLUMNS)

def normalize(x):
    return "" if pd.isna(x) else str(x).strip().lower()

def safe_div(a,b, fallback=np.nan):
    if b == 0 or pd.isna(b):
        return fallback
    return a / b

def in_scope(row):
    return (
        str(row["Material_Type"]).upper() in ["ZFER","ZROH"] and
        str(row["Plant_Material_Status"]) in ["30","40"] and
        row["Total_Visible_Stock"] > 0
    )

def abc_horizon_months(abc):
    abc = str(abc).upper()
    if abc == "A": return 3
    if abc == "B": return 6
    return 10

def calc_slob_categories(df):
    d = df.copy()

    numeric = [c for c in REQUIRED_COLUMNS + OPTIONAL_POLICY_COLUMNS if c not in [
        "Plant","SKU","Description","Material_Type","Plant_Material_Status","Product_Family","UOM",
        "Batch_Conditional_Status","Expiry_Date","ABC_Indicator","XYZ_Indicator","Material_Status",
        "Protected_Stock","Strategic_Critical","Storage_Location"
    ]]
    for c in numeric:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)

    # defaults if policy columns missing
    defaults = {
        "Slow_Moving_Months_Threshold": 9,
        "Slow_Moving_Value_Threshold": 30000,
        "Excess_Value_Threshold": 30000,
        "Obsolete_Value_Threshold": 30000,
        "Discard_Value_Threshold": 0,
        "Reserve_Factor": 0.0
    }
    for c, val in defaults.items():
        if c not in d.columns:
            d[c] = val

    prevention_defaults = {
        "Blanket_Contract_Remaining_Qty": 0,
        "Forecast_Trend_90D_Pct": 0,
        "Demand_Trend_90D_Pct": 0,
        "Last_Consumption_Days_Ago": 0,
        "Historical_Consumption_6M": 0,
        "Historical_Consumption_12M": 0,
        "Planner": "",
        "Customer_Name": "",
        "Production_Line": "",
        "Current_Action_Status": "Open",
        "Current_Action_Due_Date": "",
        "Can_Repack": "Unknown",
        "Can_Rework": "Unknown",
        "Can_Transfer": "Unknown",
        "Can_Substitute": "Unknown"
    }
    for c, val in prevention_defaults.items():
        if c not in d.columns:
            d[c] = val

    for c in ["Blanket_Contract_Remaining_Qty","Forecast_Trend_90D_Pct","Demand_Trend_90D_Pct","Last_Consumption_Days_Ago","Historical_Consumption_6M","Historical_Consumption_12M"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)

    d["Net_Available_Stock"] = d["Unrestricted_Stock"] - d["Allocated_Stock"]
    d["Total_Visible_Stock"] = d["Unrestricted_Stock"] + d["Blocked_Stock"] + d["QI_Stock"]
    d["Rejected_Expired_Qty"] = np.where(d["Batch_Conditional_Status"].astype(str).str.upper().isin(["7.REJ","9.EXP"]), d["Total_Visible_Stock"], 0)
    d["Non_Rejected_Expired_Stock"] = d["Total_Visible_Stock"] - d["Rejected_Expired_Qty"]
    d["Planning_Horizon_Months"] = d["ABC_Indicator"].apply(abc_horizon_months)

    # Reserve per job aid principle: stock qty * reserve factor * PUP
    d["Reserve_Qty"] = d["Total_Visible_Stock"] * d["Reserve_Factor"]
    d["Reserve_Value_GC"] = d["Reserve_Qty"] * d["PUP_GC"]
    d["Reserve_Flag"] = d["Reserve_Value_GC"] > 0

    # Slow Moving: applies if 12M forecast > 0, coverage based on consumption avg.
    d["Slow_Moving_Coverage_Months"] = d.apply(
        lambda r: safe_div(r["Total_Visible_Stock"] - r["Rejected_Expired_Qty"] - r["Fixed_Issue_Qty"],
                           r["Avg_Consumption_For_Slow_Moving"], 999999.99),
        axis=1
    )
    d["Slow_Moving_Value_GC"] = d.apply(
        lambda r: (r["Total_Visible_Stock"] - r["Rejected_Expired_Qty"] - r["Fixed_Issue_Qty"]) * r["PUP_GC"]
        if r["Forecast_12M"] > 0 else 0,
        axis=1
    )
    d["Slow_Moving_Flag"] = (
        (d["Forecast_12M"] > 0) &
        (d["Slow_Moving_Coverage_Months"] >= d["Slow_Moving_Months_Threshold"]) &
        (d["Slow_Moving_Value_GC"] >= d["Slow_Moving_Value_Threshold"])
    )

    # Excess: if annual forecast exists, compare stock vs min(horizon forecast, shelf-life constrained forecast), plus fixed issues.
    def excess_qty(r):
        if r["Forecast_12M"] <= 0:
            return 0
        horizon_months = r["Planning_Horizon_Months"]
        a = r["Forecast_12M"] * (horizon_months / 12) + r["Fixed_Issue_Qty"]
        b = r["Remaining_Shelf_Life_Days"] * (r["Forecast_12M"] / 365) * (horizon_months / 12) + r["Fixed_Issue_Qty"]
        return max(0, r["Total_Visible_Stock"] - r["Rejected_Expired_Qty"] - min(a, b))
    d["Excess_Qty"] = d.apply(excess_qty, axis=1)
    d["Excess_Value_GC"] = d["Excess_Qty"] * d["PUP_GC"]
    d["Excess_Flag"] = d["Excess_Value_GC"] >= d["Excess_Value_Threshold"]

    # Blanket contracts are not part of the official Excess calculation; this advisory field highlights possible overstatement.
    d["Blanket_Adjusted_Excess_Qty"] = d.apply(lambda r: max(r["Excess_Qty"] - r["Blanket_Contract_Remaining_Qty"], 0), axis=1)
    d["Potential_Excess_Overstatement_Value"] = d.apply(lambda r: min(r["Excess_Qty"], r["Blanket_Contract_Remaining_Qty"]) * r["PUP_GC"], axis=1)
    d["Blanket_Contract_Warning"] = d.apply(lambda r: "Excess risk may be overstated due to blanket contract remaining quantity." if r["Potential_Excess_Overstatement_Value"] > 0 else "", axis=1)

    # Obsolete: if no 12M forecast.
    d["Obsolete_Qty"] = d.apply(
        lambda r: max(0, r["Total_Visible_Stock"] - r["Rejected_Expired_Qty"] - r["Fixed_Issue_Qty"]) if r["Forecast_12M"] == 0 else 0,
        axis=1
    )
    d["Obsolete_Value_GC"] = d["Obsolete_Qty"] * d["PUP_GC"]
    d["Obsolete_Flag"] = (d["Forecast_12M"] == 0) & (d["Obsolete_Value_GC"] >= d["Obsolete_Value_Threshold"])

    # Discard: rejected/expired qty + obsolete below threshold.
    d["Discard1_Qty"] = d["Rejected_Expired_Qty"]
    d["Discard2_Qty"] = d.apply(
        lambda r: r["Obsolete_Qty"] if r["Forecast_12M"] == 0 and (r["Obsolete_Qty"] * r["PUP_GC"]) < r["Obsolete_Value_Threshold"] else 0,
        axis=1
    )
    d["Discard_Qty"] = d["Discard1_Qty"] + d["Discard2_Qty"]
    d["Discard_Value_GC"] = d["Discard_Qty"] * d["PUP_GC"]
    d["Discard_Flag"] = d["Discard_Value_GC"] > d["Discard_Value_Threshold"]

    # Scope
    d["In_Scope"] = d.apply(in_scope, axis=1)

    # Assessment and proposed action code aligned to job aid auto assessment principles.
    def auto_assessment(r):
        if not r["In_Scope"]:
            return "EXCLUDE", "NO_RISK", "OUT_OF_SCOPE", "NO_ACTION_AS_NO_RISK", "PLANNING", "Material not in SLOB scope"
        if normalize(r["Protected_Stock"]) == "yes":
            return "ACTIVE", "AT_RISK", "PROTECTED_STOCK", "DO_NOT_DISCARD", "RM PLANNING", "Protected stock must not be discarded"
        if normalize(r["Strategic_Critical"]) in ["permanent","opportunistic","yes","true"]:
            dept = "GBS_SUPPLY_PLNG" if normalize(r["Strategic_Critical"]) == "permanent" else "DIV_REG_SUP_PLNG"
            return "ACTIVE", "AT_RISK", "STRATEGIC_STOCK", "FOLLOW_UP", dept, "Strategic critical stock requires follow-up"
        if normalize(r["Batch_Conditional_Status"]) in ["7.rej","9.exp"]:
            return "ACTIVE", "AT_RISK", "TO_BE_ASSESSED", "DESTROY_AND_WRITE_OFF", "RM PLANNING", "Rejected or expired conditional status"
        if r["Discard_Flag"]:
            return "ACTIVE", "AT_RISK", "TO_BE_ASSESSED", "BATCH_LET_AGE", "RM PLANNING", "Discard category below obsolete threshold or expired/rejected stock"
        if r["Obsolete_Flag"] or r["Excess_Flag"] or r["Slow_Moving_Flag"]:
            return "ACTIVE", "AT_RISK", "TO_BE_ASSESSED", "FOLLOW_UP", "PLANNING", "SLOB category risk requires assessment and mitigation"
        return "DISAPPEAR", "NO_RISK", "NO_RISK", "NO_ACTION_AS_NO_RISK", "RM PLANNING", "No active SLOB category risk"

    d[["Assessment_Status","Assessment_Code","Reason_Code","Action_Code_Proposed","Action_Department","Auto_Assessment_Logic"]] = d.apply(lambda r: pd.Series(auto_assessment(r)), axis=1)


    # Discard reason code suggestion from the uploaded reason-code library.
    # Conservative rule: automatically assign only where the driver is clear; otherwise require manual review.
    d["Suggested_Discard_Reason_Code"] = d.apply(recommend_discard_reason, axis=1)
    d["Suggested_Discard_Reason_Category"] = d["Suggested_Discard_Reason_Code"].apply(lambda c: get_reason_record(c)["Category"])
    d["Suggested_Discard_Reason_Subcategory"] = d["Suggested_Discard_Reason_Code"].apply(lambda c: get_reason_record(c)["Subcategory"])
    d["Suggested_Discard_Reason"] = d["Suggested_Discard_Reason_Code"].apply(lambda c: get_reason_record(c)["Reason"])
    d["Suggested_Discard_Reason_Description"] = d["Suggested_Discard_Reason_Code"].apply(lambda c: get_reason_record(c)["Description"])

    # Risk scoring using category value and criticality.
    def risk_score(r):
        points = 0
        drivers = []
        if r["Discard_Flag"]:
            points += 35; drivers.append("Discard")
        if r["Obsolete_Flag"]:
            points += 30; drivers.append("Obsolete")
        if r["Excess_Flag"]:
            points += 25; drivers.append("Excess")
        if r["Slow_Moving_Flag"]:
            points += 20; drivers.append("Slow moving")
        if r["Reserve_Flag"]:
            points += 10; drivers.append("Reserve exposure")
        if r["Remaining_Shelf_Life_Days"] <= 60:
            points += 15; drivers.append("Short shelf life")
        if r["Inventory_Value"] >= 100000:
            points += 15; drivers.append("High value")
        elif r["Inventory_Value"] >= 50000:
            points += 10; drivers.append("Value exposure")
        if normalize(r["Material_Status"]) in ["inactive","phase-out","obsolete"]:
            points += 15; drivers.append("Lifecycle status")
        if normalize(r["Protected_Stock"]) == "yes":
            drivers.append("Protected stock")
        if normalize(r["Strategic_Critical"]) not in ["no",""]:
            drivers.append("Strategic critical")
        score = min(points,100)
        level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        return level, score, ", ".join(drivers) if drivers else "No active risk driver"

    d[["Risk_Level","Risk_Score","Risk_Drivers"]] = d.apply(lambda r: pd.Series(risk_score(r)), axis=1)

    # Business-oriented mitigation recommendation.
    def proposed_business_action(r):
        if r["Action_Code_Proposed"] == "DO_NOT_DISCARD":
            return "Do not discard. Validate protected stock purpose and review future utilization path.", "Medium", "High"
        if r["Action_Code_Proposed"] == "DESTROY_AND_WRITE_OFF":
            return "Prepare destruction/write-off workflow after QA and finance confirmation.", "Medium", "High"
        if r["Action_Code_Proposed"] == "BATCH_LET_AGE":
            return "Review whether batch should age, be consumed, or be prepared for discard decision.", "Low", "Medium"
        if r["Obsolete_Flag"]:
            return "Escalate for customer substitution, interplant transfer, rework, liquidation, or write-off decision.", "Medium", "High"
        if r["Excess_Flag"]:
            return "Freeze new production/procurement and consume existing stock before creating new supply.", "Low", "High"
        if r["Slow_Moving_Flag"]:
            return "Challenge forecast, review consumption plan, and assign mitigation action to planning/commercial.", "Low", "Medium"
        return "Monitor in routine SLOB review; no immediate mitigation required.", "Low", "Low"

    d[["Proposed_Action","Effort","Impact"]] = d.apply(lambda r: pd.Series(proposed_business_action(r)), axis=1)

    def rank_label(impact, effort):
        if impact == "High" and effort == "Low": return "Low Effort / High Impact"
        if impact == "High" and effort == "Medium": return "Medium Effort / High Impact"
        if impact == "Medium" and effort == "Low": return "Low Effort / Medium Impact"
        if impact == "Medium" and effort == "Medium": return "Medium Effort / Medium Impact"
        if impact == "Low" and effort == "Medium": return "Medium Effort / Low Impact"
        return "Low Effort / Low Impact"

    d["Impact_Effort_Rank"] = d.apply(lambda r: rank_label(r["Impact"], r["Effort"]), axis=1)
    rank_score = {
        "Low Effort / High Impact":1,
        "Medium Effort / High Impact":2,
        "Low Effort / Medium Impact":3,
        "Medium Effort / Medium Impact":4,
        "Medium Effort / Low Impact":5,
        "Low Effort / Low Impact":6
    }
    d["Priority_Sort"] = d["Impact_Effort_Rank"].map(rank_score).fillna(9)*1000000 - d["Risk_Score"]*1000 - d["Inventory_Value"]

    d["AI_Insight"] = d.apply(lambda r: (
        f"{r['SKU']} is {r['Risk_Level']} risk. Active SLOB categories: "
        f"{', '.join([name for name, flag in [('Slow Moving', r['Slow_Moving_Flag']), ('Excess', r['Excess_Flag']), ('Obsolete', r['Obsolete_Flag']), ('Discard', r['Discard_Flag']), ('Reserve', r['Reserve_Flag'])] if flag]) or 'None'}. "
        f"Risk drivers: {r['Risk_Drivers']}. Proposed SAP-style action code: {r['Action_Code_Proposed']}. "
        f"Suggested discard reason: {r['Suggested_Discard_Reason_Code']} — {r['Suggested_Discard_Reason']}. "
        f"Recommended mitigation: {r['Proposed_Action']}"
    ), axis=1)

    def master_data_checks(r):
        checks = []
        if r["Total_Visible_Stock"] > 0 and r["Inventory_Value"] <= 0:
            checks.append("Stock exists but inventory value is zero")
        if r["Total_Visible_Stock"] > 0 and r["PUP_GC"] <= 0:
            checks.append("PUP_GC missing or zero")
        if str(r["XYZ_Indicator"]).strip() == "":
            checks.append("XYZ indicator missing")
        if r["Total_Shelf_Life_Days"] <= 0 or r["Total_Shelf_Life_Days"] >= 9999:
            checks.append("Total shelf life invalid")
        if r["Remaining_Shelf_Life_Days"] < 0 or r["Remaining_Shelf_Life_Days"] >= 9999:
            checks.append("Remaining shelf life invalid")
        if r["Batch_Age_Days"] < 0 or r["Batch_Age_Days"] >= 9999:
            checks.append("Batch age invalid")
        if str(r["Batch_Conditional_Status"]).strip() == "":
            checks.append("Batch conditional status blank")
        if str(r["Material_Type"]).upper() not in ["ZFER","ZROH"]:
            checks.append("Material type outside ZFER/ZROH scope")
        if str(r["Plant_Material_Status"]) not in ["30","40"]:
            checks.append("Plant material status outside 30/40 scope")
        return "; ".join(checks) if checks else "OK"

    d["Master_Data_Checks"] = d.apply(master_data_checks, axis=1)
    d["Master_Data_Status"] = d["Master_Data_Checks"].apply(lambda x: "CHECK_DATA" if x != "OK" else "OK")

    def early_warning(r):
        score = 0
        drivers = []
        if not r["Slow_Moving_Flag"] and r["Forecast_12M"] > 0 and r["Slow_Moving_Coverage_Months"] >= max(r["Slow_Moving_Months_Threshold"] * 0.75, 1):
            score += 25; drivers.append("coverage approaching slow-moving threshold")
        if not r["Excess_Flag"] and r["Excess_Value_GC"] >= r["Excess_Value_Threshold"] * 0.70:
            score += 25; drivers.append("excess value approaching threshold")
        if r["Remaining_Shelf_Life_Days"] <= 120 and r["Total_Visible_Stock"] > 0:
            score += 18; drivers.append("shelf life exposure within 120 days")
        if r["Forecast_Trend_90D_Pct"] <= -20:
            score += 15; drivers.append("forecast declining")
        if r["Demand_Trend_90D_Pct"] <= -20:
            score += 15; drivers.append("demand declining")
        if (r["Open_PO_Qty"] + r["Open_Production_Qty"]) > 0 and r["Net_Available_Stock"] > 0:
            score += 12; drivers.append("new supply exists while stock is available")
        if r["Customer_Count"] <= 1 and r["Total_Visible_Stock"] > 0:
            score += 10; drivers.append("customer concentration")
        if r["Last_Consumption_Days_Ago"] >= 90:
            score += 10; drivers.append("no recent consumption")
        if normalize(r["Material_Status"]) in ["inactive","phase-out","obsolete"]:
            score += 18; drivers.append("lifecycle status risk")
        score = min(int(score), 100)
        level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        if score == 0:
            drivers = ["no early-warning signal from available fields"]
        return score, level, "; ".join(drivers)

    d[["Prevention_Score_90D","Prevention_Risk_Level","Prevention_Drivers"]] = d.apply(lambda r: pd.Series(early_warning(r)), axis=1)
    d["Preventive_Action"] = d.apply(lambda r: "Immediate preventive review: freeze new supply, validate demand, confirm customer pull-forward/substitution, and assign owner." if r["Prevention_Score_90D"] >= 70 else ("Weekly preventive watch: challenge forecast, review open supply and confirm consumption path." if r["Prevention_Score_90D"] >= 40 else "Monitor in normal planning rhythm."), axis=1)

    def calc_trace(r):
        lines = [
            f"SKU: {r['SKU']} | Plant: {r['Plant']}",
            f"Scope check: Material Type={r['Material_Type']}; Plant Material Status={r['Plant_Material_Status']}; In Scope={r['In_Scope']}",
            f"Stock: Total Visible={r['Total_Visible_Stock']:,.2f} {r['UOM']}; Allocated={r['Allocated_Stock']:,.2f}; Fixed Issues={r['Fixed_Issue_Qty']:,.2f}; Rejected/Expired={r['Rejected_Expired_Qty']:,.2f}",
            f"Slow Moving: Forecast 12M={r['Forecast_12M']:,.2f}; Coverage={r['Slow_Moving_Coverage_Months']:,.2f} months; Threshold={r['Slow_Moving_Months_Threshold']:,.2f}; Value={r['Slow_Moving_Value_GC']:,.2f}; Flag={r['Slow_Moving_Flag']}",
            f"Excess: Qty={r['Excess_Qty']:,.2f}; Value={r['Excess_Value_GC']:,.2f}; Threshold={r['Excess_Value_Threshold']:,.2f}; Flag={r['Excess_Flag']}",
            f"Blanket Contract Advisory: Remaining Qty={r['Blanket_Contract_Remaining_Qty']:,.2f}; Potential Overstatement Value={r['Potential_Excess_Overstatement_Value']:,.2f}",
            f"Obsolete: Forecast 12M={r['Forecast_12M']:,.2f}; Qty={r['Obsolete_Qty']:,.2f}; Value={r['Obsolete_Value_GC']:,.2f}; Threshold={r['Obsolete_Value_Threshold']:,.2f}; Flag={r['Obsolete_Flag']}",
            f"Discard: Qty={r['Discard_Qty']:,.2f}; Value={r['Discard_Value_GC']:,.2f}; Flag={r['Discard_Flag']}",
            f"Reserve: Factor={r['Reserve_Factor']:,.2f}; Qty={r['Reserve_Qty']:,.2f}; Value={r['Reserve_Value_GC']:,.2f}; Flag={r['Reserve_Flag']}",
            f"Governance: Assessment={r['Assessment_Code']}; Reason={r['Reason_Code']}; Proposed Action Code={r['Action_Code_Proposed']}; Department={r['Action_Department']}",
            f"Early Warning: Score={r['Prevention_Score_90D']}; Level={r['Prevention_Risk_Level']}; Drivers={r['Prevention_Drivers']}",
            f"Master Data: {r['Master_Data_Status']} — {r['Master_Data_Checks']}"
        ]
        return "\n".join(lines)

    d["Calculation_Trace"] = d.apply(calc_trace, axis=1)
    d["Action_Due_Date_Parsed"] = pd.to_datetime(d["Current_Action_Due_Date"], errors="coerce")
    d["Overdue_Action"] = d.apply(lambda r: bool(pd.notna(r["Action_Due_Date_Parsed"]) and r["Action_Due_Date_Parsed"].date() < date.today() and str(r["Current_Action_Status"]).lower() not in ["closed","completed","done"]), axis=1)
    d["Expected_Business_Benefit"] = d.apply(lambda r: max(r["Excess_Value_GC"], r["Obsolete_Value_GC"], r["Discard_Value_GC"], r["Reserve_Value_GC"], r["Potential_Excess_Overstatement_Value"]), axis=1)

    return d.sort_values("Priority_Sort")

def risk_badge(level):
    if level == "High": return '<span class="badge high">HIGH RISK</span>'
    if level == "Medium": return '<span class="badge med">MEDIUM RISK</span>'
    return '<span class="badge low">LOW RISK</span>'

def executive_summary(data):
    active_value = data.loc[data["Assessment_Status"] == "ACTIVE", "Inventory_Value"].sum()
    high = data[data["Risk_Level"] == "High"].sort_values("Inventory_Value", ascending=False).head(3)
    quick = data[data["Impact_Effort_Rank"] == "Low Effort / High Impact"].sort_values("Inventory_Value", ascending=False).head(3)
    prevention = data[data["Prevention_Risk_Level"] == "High"].sort_values("Prevention_Score_90D", ascending=False).head(3)
    master_issues = int((data["Master_Data_Status"] == "CHECK_DATA").sum())

    def sku_list(df):
        if df.empty:
            return "None identified"
        return ", ".join([f"{r.SKU} (${r.Inventory_Value:,.0f})" for _, r in df.iterrows()])

    return {
        "summary": f"Active SLOB exposure is ${active_value:,.0f}. High-risk SKUs: {sku_list(high)}. Quick wins: {sku_list(quick)}. Early-warning SKUs: {sku_list(prevention)}. Master data records needing CHECK_DATA review: {master_issues}.",
        "top_risk": sku_list(high),
        "quick_wins": sku_list(quick),
        "early_warning": sku_list(prevention),
        "master_issues": master_issues
    }

def validate_mass_upload(upload_df):
    issues = []
    mandatory = ["Plant","Material","Assessment Code","Reason Code","Action Code","Action Dept","Action Due Date","Comment"]
    for idx, row in upload_df.iterrows():
        for col in mandatory:
            if str(row.get(col, "")).strip() == "":
                issues.append({"Row": idx + 1, "Issue": f"Missing mandatory field: {col}"})
        if str(row.get("Reason Code", "")) == "MANUAL_REVIEW":
            issues.append({"Row": idx + 1, "Issue": "Reason code requires manual review"})
        try:
            due = pd.to_datetime(str(row.get("Action Due Date", "")), format="%Y%m%d").date()
            if due < date.today():
                issues.append({"Row": idx + 1, "Issue": "Action due date is in the past"})
        except Exception:
            issues.append({"Row": idx + 1, "Issue": "Invalid action due date format; expected YYYYMMDD"})
        if str(row.get("Action Code", "")) == "DO_NOT_DISCARD" and "discard" in str(row.get("Comment", "")).lower():
            issues.append({"Row": idx + 1, "Issue": "Protected/Do-not-discard record contains discard wording in comment"})
    return pd.DataFrame(issues)

def make_mass_upload(data, due_date, comment_prefix, active_only=True):
    export_df = data.copy()
    if active_only:
        export_df = export_df[export_df["Assessment_Code"] == "AT_RISK"]
    batch_col = "Batch_Number" if "Batch_Number" in export_df.columns else None
    return pd.DataFrame({
        "Plant": export_df["Plant"],
        "Material": export_df["SKU"],
        "Batch": export_df[batch_col] if batch_col else "",
        "Assessment Code": export_df["Assessment_Code"],
        "Reason Code": export_df["Suggested_Discard_Reason_Code"],
        "Action Code": export_df["Action_Code_Proposed"],
        "Action Dept": export_df["Action_Department"],
        "Action Due Date": due_date.strftime("%Y%m%d"),
        "Comment": export_df.apply(lambda r: f"{comment_prefix}: {r['AI_Insight']}", axis=1)
    })

st.markdown("""
<div class="hero">
  <h1>SLOB MRP Intelligence</h1>
  <p>SAP SLOB Toolkit-aligned SKU risk engine using Slow Moving, Excess, Obsolete, Discard, Reserve, Protected Stock and Strategic Critical logic.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## Data Input")
use_sample = st.sidebar.toggle("Use sample SAP/SLOB data", value=True)
uploaded = st.sidebar.file_uploader("Upload SAP SLOB CSV", type=["csv"])
view = st.sidebar.radio("View", [
    "Executive Control Tower",
    "Early Warning Radar",
    "SLOB Action List",
    "Action Cockpit",
    "Master Data Health",
    "Policy Simulator",
    "What-If Simulator",
    "Root Cause Pareto",
    "SKU Deep Dive",
    "SLOB Category Review",
    "Discard Reason Code Library",
    "Mass Upload Export",
    "Data Template"
])

if use_sample:
    raw = sample_data()
elif uploaded:
    raw = pd.read_csv(uploaded)
else:
    raw = pd.DataFrame()

if view == "Data Template":
    st.markdown('<div class="section-header">SAP SLOB Toolkit-Aligned Data Template</div>', unsafe_allow_html=True)
    st.dataframe(sample_data().head(0), use_container_width=True)
    st.download_button("Download CSV template", sample_data().head(0).to_csv(index=False).encode("utf-8"), "sap_slob_toolkit_aligned_template.csv", "text/csv", use_container_width=True)
    st.markdown("Required columns:")
    st.code("\n".join(REQUIRED_COLUMNS))
    st.markdown("Optional policy columns:")
    st.code("\n".join(OPTIONAL_POLICY_COLUMNS))
    st.markdown("Optional prevention / action-management columns:")
    st.code("\n".join(OPTIONAL_PREVENTION_COLUMNS))
    st.stop()

if raw.empty:
    st.info("Upload a CSV or activate sample SAP/SLOB data.")
    st.stop()

missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

data = calc_slob_categories(raw)

if view == "Executive Control Tower":
    active = data[data["Assessment_Status"]=="ACTIVE"]
    total_value = data["Inventory_Value"].sum()
    active_value = active["Inventory_Value"].sum()
    discard_value = data["Discard_Value_GC"].sum()
    excess_value = data["Excess_Value_GC"].sum()
    obsolete_value = data["Obsolete_Value_GC"].sum()
    quick_wins = len(data[data["Impact_Effort_Rank"]=="Low Effort / High Impact"])

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Total Value</div><div class="metric-value">${total_value:,.0f}</div><div class="metric-sub">visible inventory</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Active Risk Value</div><div class="metric-value">${active_value:,.0f}</div><div class="metric-sub">assessment status active</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Excess Value</div><div class="metric-value">${excess_value:,.0f}</div><div class="metric-sub">calculated category</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Obsolete/Discard</div><div class="metric-value">${obsolete_value+discard_value:,.0f}</div><div class="metric-sub">calculated category</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">Quick Wins</div><div class="metric-value">{quick_wins}</div><div class="metric-sub">low effort/high impact</div></div>', unsafe_allow_html=True)

    summary = executive_summary(data)
    st.markdown('<div class="section-header">AI Executive Summary</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
      <div class="card-title">What needs attention first</div>
      <div class="insight"><b>Summary:</b> {summary['summary']}</div>
      <div style="margin-top:10px;">
        <span class="kpi-pill">Top risk: {summary['top_risk']}</span>
        <span class="kpi-pill">Quick wins: {summary['quick_wins']}</span>
        <span class="kpi-pill">Early warning: {summary['early_warning']}</span>
      </div>
      <div class="warn"><b>Governance guardrail:</b> These are decision-support recommendations. Final SLOB assessment, reason code, action code, and discard decision must follow the official SLOB review process and responsible owner validation.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Risk Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Power BI-style visual view of SLOB exposure by category, risk level, action code, reason code and impact/effort priority.</div>', unsafe_allow_html=True)

    category_rows = []
    category_map = [
        ("Slow Moving", "Slow_Moving_Flag", "Slow_Moving_Value_GC"),
        ("Excess", "Excess_Flag", "Excess_Value_GC"),
        ("Obsolete", "Obsolete_Flag", "Obsolete_Value_GC"),
        ("Discard", "Discard_Flag", "Discard_Value_GC"),
        ("Reserve", "Reserve_Flag", "Reserve_Value_GC")
    ]
    for category_name, flag_col, value_col in category_map:
        flagged = data[data[flag_col] == True]
        category_rows.append({
            "Category": category_name,
            "Risk Value": float(data[value_col].sum()),
            "Inventory Value": float(flagged["Inventory_Value"].sum()),
            "SKU Count": int(len(flagged))
        })
    category_df = pd.DataFrame(category_rows)
    risk_level_df = data.groupby("Risk_Level", as_index=False).agg(Inventory_Value=("Inventory_Value","sum"), SKU_Count=("SKU","count"))
    action_df = data.groupby("Action_Code_Proposed", as_index=False).agg(Inventory_Value=("Inventory_Value","sum"), SKU_Count=("SKU","count")).sort_values("Inventory_Value", ascending=False)
    impact_df = data.groupby("Impact_Effort_Rank", as_index=False).agg(Inventory_Value=("Inventory_Value","sum"), SKU_Count=("SKU","count")).sort_values("Inventory_Value", ascending=False)
    reason_df = data.groupby("Suggested_Discard_Reason_Category", as_index=False).agg(Inventory_Value=("Inventory_Value","sum"), SKU_Count=("SKU","count")).sort_values("Inventory_Value", ascending=False)

    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        fig_cat = px.bar(category_df, x="Category", y="Risk Value", text="Risk Value", title="SLOB risk value by category")
        fig_cat.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_cat.update_layout(template="plotly_white", height=380, margin=dict(l=20,r=20,t=55,b=20), yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig_cat, use_container_width=True)
    with chart_col_2:
        fig_risk = px.pie(risk_level_df, names="Risk_Level", values="Inventory_Value", title="Inventory value by risk level", hole=0.42)
        fig_risk.update_layout(template="plotly_white", height=380, margin=dict(l=20,r=20,t=55,b=20))
        fig_risk.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_risk, use_container_width=True)

    chart_col_3, chart_col_4 = st.columns(2)
    with chart_col_3:
        fig_impact = px.bar(impact_df, x="Inventory_Value", y="Impact_Effort_Rank", orientation="h", text="Inventory_Value", title="Inventory value by impact / effort rank")
        fig_impact.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_impact.update_layout(template="plotly_white", height=420, margin=dict(l=20,r=20,t=55,b=20), xaxis_tickprefix="$", xaxis_tickformat=",.0f", yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_impact, use_container_width=True)
    with chart_col_4:
        fig_action = px.bar(action_df, x="Inventory_Value", y="Action_Code_Proposed", orientation="h", text="Inventory_Value", title="Inventory value by proposed action code")
        fig_action.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_action.update_layout(template="plotly_white", height=420, margin=dict(l=20,r=20,t=55,b=20), xaxis_tickprefix="$", xaxis_tickformat=",.0f", yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_action, use_container_width=True)

    chart_col_5, chart_col_6 = st.columns(2)
    with chart_col_5:
        fig_count = px.bar(category_df, x="Category", y="SKU Count", text="SKU Count", title="SKU count by SLOB category")
        fig_count.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_count.update_layout(template="plotly_white", height=360, margin=dict(l=20,r=20,t=55,b=20))
        st.plotly_chart(fig_count, use_container_width=True)
    with chart_col_6:
        fig_reason = px.bar(reason_df, x="Inventory_Value", y="Suggested_Discard_Reason_Category", orientation="h", text="Inventory_Value", title="Inventory value by discard reason category")
        fig_reason.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_reason.update_layout(template="plotly_white", height=360, margin=dict(l=20,r=20,t=55,b=20), xaxis_tickprefix="$", xaxis_tickformat=",.0f", yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig_reason, use_container_width=True)

    st.markdown('<div class="section-header">Top Priority Actions</div>', unsafe_allow_html=True)
    for _, r in data.head(6).iterrows():
        st.markdown(f"""
        <div class="card">
          <div>{risk_badge(r['Risk_Level'])} <span class="badge rank">{r['Impact_Effort_Rank']}</span> <span class="badge assess">{r['Assessment_Code']}</span></div>
          <div class="card-title">{r['SKU']} — {r['Description']}</div>
          <div class="card-sub">{r['Plant']} · {r['Material_Type']} · {r['Product_Family']} · Value ${r['Inventory_Value']:,.0f} · Shelf life {r['Remaining_Shelf_Life_Days']:,.0f} days · Status {r['Assessment_Status']}</div>
          <div class="insight"><b>AI insight:</b> {r['AI_Insight']}</div>
          <div class="warn"><b>Action code proposed:</b> {r['Action_Code_Proposed']} · <b>Dept:</b> {r['Action_Department']} · <b>Reason:</b> {r['Reason_Code']}<br><b>Business action:</b> {r['Proposed_Action']}</div>
        </div>
        """, unsafe_allow_html=True)

elif view == "SLOB Action List":
    st.markdown('<div class="section-header">Ranked SLOB Action List</div>', unsafe_allow_html=True)
    risks = st.multiselect("Risk level", ["High","Medium","Low"], default=["High","Medium","Low"])
    assessments = st.multiselect("Assessment code", sorted(data["Assessment_Code"].unique()), default=sorted(data["Assessment_Code"].unique()))
    filtered = data[data["Risk_Level"].isin(risks) & data["Assessment_Code"].isin(assessments)]

    cols = ["Plant","SKU","Description","Material_Type","Product_Family","Risk_Level","Risk_Score",
            "Assessment_Status","Assessment_Code","Reason_Code","Action_Code_Proposed","Action_Department",
            "Slow_Moving_Flag","Excess_Flag","Obsolete_Flag","Discard_Flag","Reserve_Flag",
            "Inventory_Value","Slow_Moving_Coverage_Months","Excess_Value_GC","Obsolete_Value_GC","Discard_Value_GC",
            "Remaining_Shelf_Life_Days","Batch_Conditional_Status","Protected_Stock","Strategic_Critical",
            "Suggested_Discard_Reason_Code","Suggested_Discard_Reason","Suggested_Discard_Reason_Category",
            "Prevention_Score_90D","Prevention_Risk_Level","Preventive_Action","Master_Data_Status","Blanket_Contract_Warning",
            "Impact_Effort_Rank","Proposed_Action","AI_Insight"]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)
    st.download_button("Export SLOB action list", filtered.to_csv(index=False).encode("utf-8"), "slob_toolkit_aligned_action_list.csv", "text/csv", use_container_width=True)

elif view == "SKU Deep Dive":
    st.markdown('<div class="section-header">SKU Deep Dive</div>', unsafe_allow_html=True)
    sku_list = data["SKU"].astype(str).tolist()
    c1, c2 = st.columns([1,1])
    with c1:
        selected_sku = st.selectbox("Select SKU from list", sku_list)
    with c2:
        typed_sku = st.text_input("Or type SKU code", placeholder="Example: GJ-45")
    sku = typed_sku.strip() if typed_sku.strip() else selected_sku
    matches = data[data["SKU"].astype(str).str.upper() == sku.upper()]
    if matches.empty:
        st.error(f"SKU '{sku}' was not found.")
        st.stop()
    r = matches.iloc[0]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Risk Score</div><div class="metric-value">{r["Risk_Score"]:.0f}</div><div class="metric-sub">{r["Risk_Level"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Inventory Value</div><div class="metric-value">${r["Inventory_Value"]:,.0f}</div><div class="metric-sub">current exposure</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Excess Value</div><div class="metric-value">${r["Excess_Value_GC"]:,.0f}</div><div class="metric-sub">calculated</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Obsolete Value</div><div class="metric-value">${r["Obsolete_Value_GC"]:,.0f}</div><div class="metric-sub">calculated</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-label">Discard Value</div><div class="metric-value">${r["Discard_Value_GC"]:,.0f}</div><div class="metric-sub">calculated</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
      <div>{risk_badge(r['Risk_Level'])} <span class="badge rank">{r['Impact_Effort_Rank']}</span> <span class="badge assess">{r['Assessment_Code']}</span></div>
      <div class="card-title">{r['SKU']} — {r['Description']}</div>
      <div class="card-sub">{r['Plant']} · {r['Material_Type']} · {r['Product_Family']} · Conditional status: {r['Batch_Conditional_Status']}</div>
      <div class="insight"><b>AI Insight:</b> {r['AI_Insight']}</div>
      <div class="warn"><b>SAP-style proposed action:</b> {r['Action_Code_Proposed']} · <b>Reason:</b> {r['Reason_Code']} · <b>Dept:</b> {r['Action_Department']}<br><b>Suggested discard reason:</b> {r['Suggested_Discard_Reason_Code']} — {r['Suggested_Discard_Reason']}<br><b>Auto assessment logic:</b> {r['Auto_Assessment_Logic']}</div>
    </div>
    """, unsafe_allow_html=True)

    if str(r["Blanket_Contract_Warning"]).strip():
        st.warning(f"{r['Blanket_Contract_Warning']} Potential overstatement value: ${r['Potential_Excess_Overstatement_Value']:,.0f}")

    st.markdown('<div class="section-header">Calculation Trace</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="trace">{r["Calculation_Trace"]}</div>', unsafe_allow_html=True)

    detail_cols = ["Slow_Moving_Flag","Slow_Moving_Coverage_Months","Slow_Moving_Value_GC","Excess_Flag","Excess_Qty","Excess_Value_GC","Blanket_Contract_Remaining_Qty","Blanket_Adjusted_Excess_Qty","Potential_Excess_Overstatement_Value",
                   "Obsolete_Flag","Obsolete_Qty","Obsolete_Value_GC","Discard_Flag","Discard_Qty","Discard_Value_GC",
                   "Reserve_Flag","Reserve_Qty","Reserve_Value_GC","Protected_Stock","Strategic_Critical",
                   "Prevention_Score_90D","Prevention_Risk_Level","Prevention_Drivers","Preventive_Action","Master_Data_Status","Master_Data_Checks",
                   "Suggested_Discard_Reason_Code","Suggested_Discard_Reason","Suggested_Discard_Reason_Category","Suggested_Discard_Reason_Description",
                   "Unrestricted_Stock","Allocated_Stock","Fixed_Issue_Qty","Total_Visible_Stock","Forecast_12M","ABC_Indicator","XYZ_Indicator"]
    st.dataframe(pd.DataFrame(data.loc[matches.index[0], detail_cols]).rename(columns={matches.index[0]:"Value"}), use_container_width=True)

elif view == "SLOB Category Review":
    st.markdown('<div class="section-header">SLOB Category Review</div>', unsafe_allow_html=True)
    category = st.selectbox("Category", ["Slow Moving","Excess","Obsolete","Discard","Reserve","Protected Stock","Strategic Critical"])
    flag_map = {
        "Slow Moving":"Slow_Moving_Flag",
        "Excess":"Excess_Flag",
        "Obsolete":"Obsolete_Flag",
        "Discard":"Discard_Flag",
        "Reserve":"Reserve_Flag",
        "Protected Stock":"Protected_Stock",
        "Strategic Critical":"Strategic_Critical"
    }
    if category == "Protected Stock":
        filtered = data[data["Protected_Stock"].apply(normalize) == "yes"]
    elif category == "Strategic Critical":
        filtered = data[~data["Strategic_Critical"].apply(normalize).isin(["no",""])]
    else:
        filtered = data[data[flag_map[category]] == True]

    st.dataframe(filtered, use_container_width=True, hide_index=True)


elif view == "Early Warning Radar":
    st.markdown('<div class="section-header">SLOB Early Warning Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Forward-looking prevention view. This does not replace SLOB calculation; it highlights SKUs trending toward future SLOB risk.</div>', unsafe_allow_html=True)

    risk_filter = st.multiselect("Prevention risk level", ["High","Medium","Low"], default=["High","Medium","Low"])
    radar = data[data["Prevention_Risk_Level"].isin(risk_filter)].sort_values(["Prevention_Score_90D","Inventory_Value"], ascending=False)

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">High Prevention Risk</div><div class="metric-value">{len(data[data["Prevention_Risk_Level"]=="High"])}</div><div class="metric-sub">SKUs</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Medium Prevention Risk</div><div class="metric-value">{len(data[data["Prevention_Risk_Level"]=="Medium"])}</div><div class="metric-sub">SKUs</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Open Supply Exposure</div><div class="metric-value">{len(data[(data["Open_PO_Qty"]+data["Open_Production_Qty"])>0])}</div><div class="metric-sub">SKUs with PO/production</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Single-Customer Risk</div><div class="metric-value">{len(data[data["Customer_Count"]<=1])}</div><div class="metric-sub">SKUs</div></div>', unsafe_allow_html=True)

    fig_prev = px.scatter(radar, x="Prevention_Score_90D", y="Inventory_Value", size="Total_Visible_Stock", color="Prevention_Risk_Level", hover_data=["SKU","Description","Prevention_Drivers","Preventive_Action"], title="Prevention risk score vs inventory value")
    fig_prev.update_layout(template="plotly_white", height=430, margin=dict(l=20,r=20,t=55,b=20), yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig_prev, use_container_width=True)

    cols = ["Plant","SKU","Description","Product_Family","Inventory_Value","Prevention_Score_90D","Prevention_Risk_Level","Prevention_Drivers","Preventive_Action","Open_PO_Qty","Open_Production_Qty","Forecast_Trend_90D_Pct","Demand_Trend_90D_Pct","Last_Consumption_Days_Ago","Customer_Count"]
    st.dataframe(radar[cols], use_container_width=True, hide_index=True)

elif view == "Action Cockpit":
    st.markdown('<div class="section-header">Action Cockpit</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Action-management layer for review follow-up. It supports owner tracking, due-date visibility, and export for governance discussions.</div>', unsafe_allow_html=True)

    cockpit = data[data["Assessment_Code"] == "AT_RISK"].copy()
    cockpit["Owner"] = cockpit["Action_Department"]
    cockpit["Due_Date"] = cockpit["Current_Action_Due_Date"].replace("", (date.today() + timedelta(days=7)).strftime("%Y-%m-%d"))
    cockpit["Status"] = cockpit["Current_Action_Status"]
    cockpit["Comment"] = cockpit["AI_Insight"]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Open Actions</div><div class="metric-value">{len(cockpit)}</div><div class="metric-sub">at-risk records</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Overdue</div><div class="metric-value">{int(cockpit["Overdue_Action"].sum())}</div><div class="metric-sub">based on due date</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Action Value</div><div class="metric-value">${cockpit["Inventory_Value"].sum():,.0f}</div><div class="metric-sub">inventory exposure</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Manual Review</div><div class="metric-value">{len(cockpit[cockpit["Suggested_Discard_Reason_Code"]=="MANUAL_REVIEW"])}</div><div class="metric-sub">reason-code review</div></div>', unsafe_allow_html=True)

    action_cols = ["Plant","SKU","Description","Inventory_Value","Assessment_Code","Reason_Code","Suggested_Discard_Reason_Code","Action_Code_Proposed","Owner","Due_Date","Status","Proposed_Action","Comment"]
    edited = st.data_editor(cockpit[action_cols], use_container_width=True, hide_index=True, num_rows="fixed")
    st.download_button("Export action cockpit", edited.to_csv(index=False).encode("utf-8"), "slob_action_cockpit.csv", "text/csv", use_container_width=True)

elif view == "Master Data Health":
    st.markdown('<div class="section-header">Master Data Health Check</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Governance-safe CHECK_DATA screen. Items here should be corrected before final SLOB assessment where possible.</div>', unsafe_allow_html=True)

    md = data[data["Master_Data_Status"] == "CHECK_DATA"].copy()
    ok_count = len(data) - len(md)
    c1,c2,c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">CHECK_DATA Records</div><div class="metric-value">{len(md)}</div><div class="metric-sub">need review</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">OK Records</div><div class="metric-value">{ok_count}</div><div class="metric-sub">no issue detected</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Value Impact</div><div class="metric-value">${md["Inventory_Value"].sum():,.0f}</div><div class="metric-sub">data-quality exposure</div></div>', unsafe_allow_html=True)

    if md.empty:
        st.success("No master data health issues detected in the uploaded file.")
    else:
        st.dataframe(md[["Plant","SKU","Description","Inventory_Value","Master_Data_Checks","PUP_GC","Total_Shelf_Life_Days","Remaining_Shelf_Life_Days","Batch_Age_Days","Batch_Conditional_Status","XYZ_Indicator","Material_Type","Plant_Material_Status"]], use_container_width=True, hide_index=True)

elif view == "Policy Simulator":
    st.markdown('<div class="section-header">Policy Table Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Scenario test only. This does not change SAP policy tables. Use it to understand sensitivity before governance review.</div>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        sm_months = st.number_input("Slow moving months threshold", min_value=1.0, value=9.0, step=1.0)
    with c2:
        sm_value = st.number_input("Slow moving value threshold", min_value=0.0, value=30000.0, step=5000.0)
    with c3:
        excess_thr = st.number_input("Excess value threshold", min_value=0.0, value=30000.0, step=5000.0)
    with c4:
        obsolete_thr = st.number_input("Obsolete value threshold", min_value=0.0, value=30000.0, step=5000.0)

    sim_raw = raw.copy()
    sim_raw["Slow_Moving_Months_Threshold"] = sm_months
    sim_raw["Slow_Moving_Value_Threshold"] = sm_value
    sim_raw["Excess_Value_Threshold"] = excess_thr
    sim_raw["Obsolete_Value_Threshold"] = obsolete_thr
    sim = calc_slob_categories(sim_raw)

    compare = pd.DataFrame({
        "Metric": ["Slow Moving SKUs","Excess SKUs","Obsolete SKUs","Discard SKUs","Active Risk Value"],
        "Current": [int(data["Slow_Moving_Flag"].sum()), int(data["Excess_Flag"].sum()), int(data["Obsolete_Flag"].sum()), int(data["Discard_Flag"].sum()), float(data.loc[data["Assessment_Status"]=="ACTIVE","Inventory_Value"].sum())],
        "Scenario": [int(sim["Slow_Moving_Flag"].sum()), int(sim["Excess_Flag"].sum()), int(sim["Obsolete_Flag"].sum()), int(sim["Discard_Flag"].sum()), float(sim.loc[sim["Assessment_Status"]=="ACTIVE","Inventory_Value"].sum())]
    })
    st.dataframe(compare, use_container_width=True, hide_index=True)
    fig_policy = px.bar(compare, x="Metric", y=["Current","Scenario"], barmode="group", title="Current vs scenario SLOB outcome")
    fig_policy.update_layout(template="plotly_white", height=430, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig_policy, use_container_width=True)

elif view == "What-If Simulator":
    st.markdown('<div class="section-header">What-If Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Model possible preventive actions at SKU level. This is advisory and should be validated through planning governance.</div>', unsafe_allow_html=True)

    sku = st.selectbox("Select SKU", data["SKU"].astype(str).tolist())
    r = data[data["SKU"].astype(str) == sku].iloc[0]
    c1,c2,c3 = st.columns(3)
    with c1:
        demand_pull = st.number_input("Customer pull-forward / demand increase qty", min_value=0.0, value=0.0, step=100.0)
    with c2:
        cancel_supply = st.number_input("Cancel/reschedule open supply qty", min_value=0.0, value=0.0, step=100.0)
    with c3:
        transfer_qty = st.number_input("Interplant transfer / substitution qty", min_value=0.0, value=0.0, step=100.0)

    mitigated_qty = min(r["Total_Visible_Stock"], demand_pull + transfer_qty)
    avoided_value = mitigated_qty * r["PUP_GC"]
    supply_risk_reduction = min(cancel_supply, r["Open_PO_Qty"] + r["Open_Production_Qty"]) * r["PUP_GC"]
    projected_excess = max(r["Excess_Qty"] - mitigated_qty, 0)
    projected_excess_value = projected_excess * r["PUP_GC"]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Current Excess Value</div><div class="metric-value">${r["Excess_Value_GC"]:,.0f}</div><div class="metric-sub">baseline</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Projected Excess Value</div><div class="metric-value">${projected_excess_value:,.0f}</div><div class="metric-sub">after action</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Value Avoided</div><div class="metric-value">${avoided_value:,.0f}</div><div class="metric-sub">consumption/transfer</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Supply Risk Avoided</div><div class="metric-value">${supply_risk_reduction:,.0f}</div><div class="metric-sub">cancel/reschedule</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="card-title">Scenario recommendation for {sku}</div><div class="insight">If feasible, projected excess value changes from ${r["Excess_Value_GC"]:,.0f} to ${projected_excess_value:,.0f}. Validate customer, QA, planning and commercial feasibility before execution.</div></div>', unsafe_allow_html=True)

elif view == "Root Cause Pareto":
    st.markdown('<div class="section-header">Root-Cause Pareto</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Identify systemic drivers by reason code, plant, product family, department, material type, and production line.</div>', unsafe_allow_html=True)

    pareto_axis = st.selectbox("Pareto by", ["Suggested_Discard_Reason", "Suggested_Discard_Reason_Category", "Plant", "Product_Family", "Action_Department", "Material_Type", "Production_Line"])
    pareto = data.groupby(pareto_axis, as_index=False).agg(Inventory_Value=("Inventory_Value","sum"), SKU_Count=("SKU","count")).sort_values("Inventory_Value", ascending=False)
    pareto["Cumulative_Value"] = pareto["Inventory_Value"].cumsum()
    total = pareto["Inventory_Value"].sum()
    pareto["Cumulative_%"] = np.where(total > 0, pareto["Cumulative_Value"] / total * 100, 0)

    fig_pareto = px.bar(pareto.head(20), x=pareto_axis, y="Inventory_Value", text="Inventory_Value", title=f"SLOB value Pareto by {pareto_axis}")
    fig_pareto.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig_pareto.update_layout(template="plotly_white", height=460, margin=dict(l=20,r=20,t=55,b=80), yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig_pareto, use_container_width=True)
    st.dataframe(pareto, use_container_width=True, hide_index=True)

elif view == "Discard Reason Code Library":
    st.markdown('<div class="section-header">Discard Reason Code Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Reason codes captured from the screenshots you provided. Use this library to validate discard coding before mass upload or SLOB review update.</div>', unsafe_allow_html=True)

    reason_df = reason_codes_df()
    categories = sorted(reason_df["Category"].unique())
    selected_categories = st.multiselect("Category", categories, default=categories)
    filtered_reasons = reason_df[reason_df["Category"].isin(selected_categories)]

    search = st.text_input("Search reason code / keyword", placeholder="Example: obsolete, repack, expired, 1201")
    if search.strip():
        s = search.strip().lower()
        filtered_reasons = filtered_reasons[filtered_reasons.apply(lambda r: s in str(r.to_dict()).lower(), axis=1)]

    st.dataframe(filtered_reasons, use_container_width=True, hide_index=True)
    st.download_button("Export reason-code library", filtered_reasons.to_csv(index=False).encode("utf-8"), "discard_reason_code_library.csv", "text/csv", use_container_width=True)

elif view == "Mass Upload Export":
    st.markdown('<div class="section-header">SLOB Mass Upload Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Creates a draft mass-upload file aligned with the SLOB list upload structure. Review and validate before SAP upload.</div>', unsafe_allow_html=True)

    active_only = st.checkbox("Only active / at-risk records", value=True)
    due_date = st.date_input("Action due date", value=date.today() + timedelta(days=7))
    comment_prefix = st.text_input("Comment prefix", value="AI suggested based on SLOB MRP Intelligence review")

    upload = make_mass_upload(data, due_date, comment_prefix, active_only)
    validation = validate_mass_upload(upload)

    if validation.empty:
        st.success("Validation passed: no missing mandatory fields, no past due dates, and no forced MANUAL_REVIEW reason codes.")
    else:
        st.warning(f"Validation found {len(validation)} issue(s). Resolve these before SAP upload.")
        st.dataframe(validation, use_container_width=True, hide_index=True)

    st.dataframe(upload, use_container_width=True, hide_index=True)
    st.download_button("Export SLOB mass-upload draft", upload.to_csv(index=False, sep="\t").encode("utf-8"), "slob_mass_upload_draft.txt", "text/tab-separated-values", use_container_width=True)

st.caption("Prototype aligned to SAP SLOB Toolkit job aid principles. Validate formulas, thresholds, policy tables and action codes with local/regional planning governance before production use.")
