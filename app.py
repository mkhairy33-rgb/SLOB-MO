
import streamlit as st
import pandas as pd
import numpy as np
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

    return d.sort_values("Priority_Sort")

def risk_badge(level):
    if level == "High": return '<span class="badge high">HIGH RISK</span>'
    if level == "Medium": return '<span class="badge med">MEDIUM RISK</span>'
    return '<span class="badge low">LOW RISK</span>'

st.markdown("""
<div class="hero">
  <h1>SLOB MRP Intelligence</h1>
  <p>SAP SLOB Toolkit-aligned SKU risk engine using Slow Moving, Excess, Obsolete, Discard, Reserve, Protected Stock and Strategic Critical logic.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## Data Input")
use_sample = st.sidebar.toggle("Use sample SAP/SLOB data", value=True)
uploaded = st.sidebar.file_uploader("Upload SAP SLOB CSV", type=["csv"])
view = st.sidebar.radio("View", ["Executive Control Tower", "SLOB Action List", "SKU Deep Dive", "SLOB Category Review", "Discard Reason Code Library", "Mass Upload Export", "Data Template"])

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

    detail_cols = ["Slow_Moving_Flag","Slow_Moving_Coverage_Months","Slow_Moving_Value_GC","Excess_Flag","Excess_Qty","Excess_Value_GC",
                   "Obsolete_Flag","Obsolete_Qty","Obsolete_Value_GC","Discard_Flag","Discard_Qty","Discard_Value_GC",
                   "Reserve_Flag","Reserve_Qty","Reserve_Value_GC","Protected_Stock","Strategic_Critical",
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
    st.markdown('<div class="small-muted">Creates a draft mass-upload file aligned with the SLOB list upload structure. Review reason codes before upload.</div>', unsafe_allow_html=True)

    active_only = st.checkbox("Only active / at-risk records", value=True)
    export_df = data.copy()
    if active_only:
        export_df = export_df[export_df["Assessment_Code"] == "AT_RISK"]

    due_date = st.date_input("Action due date", value=date.today() + timedelta(days=7))
    comment_prefix = st.text_input("Comment prefix", value="AI suggested based on SLOB MRP Intelligence review")

    batch_col = "Batch_Number" if "Batch_Number" in export_df.columns else None
    upload = pd.DataFrame({
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

    needs_review = upload[upload["Reason Code"] == "MANUAL_REVIEW"]
    if len(needs_review) > 0:
        st.warning(f"{len(needs_review)} record(s) require manual reason-code selection before SAP upload.")

    st.dataframe(upload, use_container_width=True, hide_index=True)
    st.download_button("Export SLOB mass-upload draft", upload.to_csv(index=False, sep="\t").encode("utf-8"), "slob_mass_upload_draft.txt", "text/tab-separated-values", use_container_width=True)

st.caption("Prototype aligned to SAP SLOB Toolkit job aid principles. Validate formulas, thresholds, policy tables and action codes with local/regional planning governance before production use.")
