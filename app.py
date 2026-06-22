
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(
    page_title="SLOB Intelligence Copilot",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Styling
# -----------------------------

st.markdown("""
<style>
:root {
    --bg: #0F172A;
    --panel: #111827;
    --panel2: #1F2937;
    --muted: #94A3B8;
    --text: #F8FAFC;
    --line: rgba(148, 163, 184, 0.22);
    --green: #16A34A;
    --yellow: #D97706;
    --red: #DC2626;
    --blue: #2563EB;
    --cyan: #06B6D4;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #111827 100%);
}
[data-testid="stSidebar"] * {
    color: #E5E7EB;
}
.hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #312E81 100%);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 24px;
    padding: 28px 32px;
    margin-bottom: 20px;
    color: white;
}
.hero h1 {
    font-size: 2.1rem;
    margin-bottom: 0.25rem;
    letter-spacing: -0.02em;
}
.hero p {
    color: #CBD5E1;
    font-size: 1rem;
    margin-bottom: 0;
}
.metric-card {
    border: 1px solid rgba(148, 163, 184, 0.25);
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    border-radius: 18px;
    padding: 18px 18px;
    min-height: 118px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}
.metric-label {
    color: #64748B;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.metric-value {
    color: #0F172A;
    font-size: 1.85rem;
    font-weight: 800;
    margin-top: 6px;
}
.metric-sub {
    color: #64748B;
    font-size: .86rem;
    margin-top: 2px;
}
.card {
    border: 1px solid rgba(148, 163, 184, 0.25);
    background: #FFFFFF;
    border-radius: 20px;
    padding: 18px 20px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    margin-bottom: 14px;
}
.card-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 4px;
}
.card-subtitle {
    font-size: .9rem;
    color: #64748B;
    margin-bottom: 12px;
}
.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 5px 11px;
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .02em;
}
.badge-green {
    color: #14532D;
    background: #DCFCE7;
    border: 1px solid #86EFAC;
}
.badge-yellow {
    color: #78350F;
    background: #FEF3C7;
    border: 1px solid #FCD34D;
}
.badge-red {
    color: #7F1D1D;
    background: #FEE2E2;
    border: 1px solid #FCA5A5;
}
.action-box {
    border-left: 5px solid #2563EB;
    background: #EFF6FF;
    color: #1E3A8A;
    padding: 14px 16px;
    border-radius: 12px;
    margin-top: 10px;
}
.risk-box {
    border-left: 5px solid #D97706;
    background: #FFFBEB;
    color: #78350F;
    padding: 14px 16px;
    border-radius: 12px;
    margin-top: 10px;
}
.small-muted {
    color: #64748B;
    font-size: .85rem;
}
.section-header {
    color: #0F172A;
    font-size: 1.35rem;
    font-weight: 850;
    margin-top: 10px;
    margin-bottom: 4px;
}
.stButton > button {
    border-radius: 12px;
    font-weight: 800;
    height: 3rem;
}
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 16px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Sample data
# -----------------------------

@st.cache_data
def load_sample_data():
    inventory = pd.DataFrame([
        ["GJ-40", "Garlic Juice 40%", "GJ24088", "Garlic Juice", 900, "kg", "2025-11-01", "2026-08-15", "Released", "CS-A1", "Tote", 12400, "None", "Conventional", "At Risk"],
        ["GJ-40", "Garlic Juice 40%", "GJ24091", "Garlic Juice", 600, "kg", "2025-12-05", "2026-12-30", "Released", "CS-A2", "Drum", 8500, "None", "Conventional", "Slow Moving"],
        ["GJ-45", "Garlic Juice 45%", "GJ45012", "Garlic Juice", 1000, "kg", "2025-10-20", "2026-09-10", "Released", "CS-B1", "Tote", 15000, "None", "Conventional", "At Risk"],
        ["OJ-65", "Onion Concentrate 65%", "OJ65021", "Onion Concentrate", 700, "kg", "2025-09-15", "2026-07-20", "Released", "CS-C1", "Tote", 9800, "None", "Conventional", "At Risk"],
        ["GJ-40", "Garlic Juice 40% QA Hold", "GJ99999", "Garlic Juice", 500, "kg", "2025-08-01", "2026-10-01", "Blocked", "CS-QA", "Tote", 6500, "None", "Conventional", "Blocked"],
    ], columns=[
        "Material_Code", "Material_Description", "Batch_Number", "Product_Family", "Available_Qty", "UOM",
        "Manufacturing_Date", "Expiry_Date", "Quality_Status", "Storage_Location", "Packaging_Format",
        "Inventory_Value", "Allergen_Status", "Claims_Certifications", "SLOB_Category"
    ])

    equiv = pd.DataFrame([
        ["GJ-40", "GJ-40", "Direct substitute", "No", "Yes", "No", "No", "Same material"],
        ["GJ-40", "GJ-45", "Can be blended", "Yes", "No", "Yes", "Yes", "Potential concentration adjustment required"],
        ["OJ-65", "OJ-65", "Direct substitute", "No", "Yes", "No", "No", "Same material"],
    ], columns=[
        "Required_Material_Code", "Alternative_Material_Code", "Equivalency_Type", "Can_Blend", "Can_Repack",
        "QA_Approval_Required", "Customer_Approval_Required", "Comments"
    ])

    restrictions = pd.DataFrame([
        ["CUST-001", "Example Customer", "GJ-40", 90, "Tote", "Conventional", "", "None", "No", "Standard customer"],
        ["CUST-002", "Strict Customer", "GJ-40", 180, "Drum", "Conventional", "", "None", "Yes", "Customer approval required for substitutions"],
    ], columns=[
        "Customer_Code", "Customer_Name", "Material_Code", "Minimum_Shelf_Life_Days", "Allowed_Packaging",
        "Allowed_Claims", "Disallowed_Claims", "Allergen_Restrictions", "Requires_Customer_Approval", "Special_Notes"
    ])
    return inventory, equiv, restrictions

def normalize(x):
    return "" if pd.isna(x) else str(x).strip().lower()

def calc_days(expiry):
    try:
        return (pd.to_datetime(expiry).date() - date.today()).days
    except Exception:
        return None

def risk_score(row):
    days = row.get("Days_to_Expiry", 9999)
    value = float(row.get("Inventory_Value", 0) or 0)
    qty = float(row.get("Available_Qty", 0) or 0)

    if days is None:
        base = 20
    elif days < 0:
        base = 100
    elif days <= 30:
        base = 90
    elif days <= 60:
        base = 75
    elif days <= 90:
        base = 60
    elif days <= 180:
        base = 35
    else:
        base = 15

    return round(base + min(value / 10000, 30) + min(qty / 1000, 10), 1)

def get_badge(level):
    if level == "Green":
        return '<span class="badge badge-green">GREEN — Use</span>'
    if level == "Yellow":
        return '<span class="badge badge-yellow">YELLOW — Review</span>'
    return '<span class="badge badge-red">RED — Blocked</span>'

def build_recommendations(order, inv, equiv, restrictions):
    inv = inv.copy()
    inv["Days_to_Expiry"] = inv["Expiry_Date"].apply(calc_days)
    inv["SLOB_Priority_Score"] = inv.apply(risk_score, axis=1)

    required = normalize(order["Required_Material_Code"])
    family = normalize(order["Product_Family"])
    packaging_req = normalize(order["Required_Packaging"])
    min_shelf = int(order["Minimum_Shelf_Life_Days"])
    order_qty = float(order["Order_Qty"])

    alt_map = {}
    if equiv is not None and not equiv.empty:
        subset = equiv[equiv["Required_Material_Code"].apply(normalize) == required]
        for _, r in subset.iterrows():
            alt_map[normalize(r["Alternative_Material_Code"])] = r.to_dict()

    rows = []
    for _, b in inv.iterrows():
        mat = normalize(b["Material_Code"])
        bfamily = normalize(b["Product_Family"])
        qstatus = normalize(b["Quality_Status"])
        bpack = normalize(b["Packaging_Format"])
        days = b["Days_to_Expiry"]
        qty = float(b["Available_Qty"])

        reasons, approvals, risks = [], [], []
        action = "Do not use"
        level = "Red"

        same = mat == required
        approved_alt = mat in alt_map
        same_family = family and family == bfamily

        if days is not None and days < 0:
            risks.append("Expired")
        if qstatus not in ["released", "approved", "qa released"]:
            risks.append(f"Quality status is {b['Quality_Status']}")
        if not same and not approved_alt and not same_family:
            risks.append("No material or family match")
        if qty <= 0:
            risks.append("No available quantity")

        if risks and ("Expired" in risks or "No material or family match" in risks or any("Quality status" in r for r in risks)):
            level = "Red"
            action = "Do not use"
            explanation = "Blocked because " + "; ".join(risks) + "."
        else:
            if same:
                reasons.append("same material code")
            elif approved_alt:
                reasons.append(f"approved alternative: {alt_map[mat].get('Equivalency_Type', '')}")
                if normalize(alt_map[mat].get("QA_Approval_Required")) == "yes":
                    approvals.append("QA")
                if normalize(alt_map[mat].get("Customer_Approval_Required")) == "yes":
                    approvals.append("Customer")
            elif same_family:
                reasons.append("same product family")
                approvals.append("QA")
                risks.append("not a direct material match")

            if days is not None and days < min_shelf:
                approvals.append("Customer / QA")
                risks.append("below minimum shelf life")
            else:
                reasons.append("meets shelf-life requirement")

            if packaging_req and packaging_req != bpack:
                approvals.append("Warehouse / Planning")
                risks.append("packaging mismatch")
                if approved_alt and normalize(alt_map[mat].get("Can_Repack")) == "yes":
                    action = "Review repack feasibility"
                else:
                    action = "Review packaging exception"
            else:
                reasons.append("packaging matches")

            coverage = min(qty, order_qty)
            if qty >= order_qty:
                reasons.append("can fully cover order")
            else:
                reasons.append("can partially cover order")
                risks.append("partial coverage only")

            if same and not approvals and not risks:
                level = "Green"
                action = "Allocate batch first"
            else:
                level = "Yellow"
                if action == "Do not use":
                    action = "Review and approve before allocation"

            explanation = (
                f"{level} recommendation. Batch {b['Batch_Number']} can cover {coverage:,.0f} {b['UOM']} "
                f"against order {order['Order_Number']}. Reasons: {', '.join(reasons)}."
            )
            if approvals:
                explanation += f" Approval needed: {', '.join(sorted(set(approvals)))}."
            if risks:
                explanation += f" Risks: {', '.join(sorted(set(risks)))}."

        coverage = min(qty, order_qty) if level in ["Green", "Yellow"] else 0
        avoided_value = round((coverage / qty) * float(b["Inventory_Value"]), 0) if qty > 0 and level in ["Green", "Yellow"] else 0

        rows.append({
            "Match": level,
            "Recommended Action": action,
            "Batch": b["Batch_Number"],
            "Material": b["Material_Code"],
            "Description": b["Material_Description"],
            "Available Qty": qty,
            "Coverage Qty": coverage,
            "UOM": b["UOM"],
            "Expiry": b["Expiry_Date"],
            "Days to Expiry": days,
            "Packaging": b["Packaging_Format"],
            "Quality": b["Quality_Status"],
            "Approval Needed": ", ".join(sorted(set(approvals))) if approvals else "None",
            "Risk": ", ".join(sorted(set(risks))) if risks else "Low",
            "Priority Score": b["SLOB_Priority_Score"],
            "Estimated Value Avoided": avoided_value,
            "AI Explanation": explanation,
            "Planner Comment": (
                f"{level} SLOB recommendation for {order['Order_Number']}: {action} using batch {b['Batch_Number']} "
                f"({b['Material_Code']}) covering {coverage:,.0f} {b['UOM']}. Expiry: {b['Expiry_Date']}."
            )
        })

    df = pd.DataFrame(rows)
    order_map = {"Green": 0, "Yellow": 1, "Red": 2}
    df["_order"] = df["Match"].map(order_map)
    return df.sort_values(["_order", "Days to Expiry", "Priority Score"], ascending=[True, True, False]).drop(columns="_order")

# -----------------------------
# Header
# -----------------------------

st.markdown("""
<div class="hero">
    <h1>SLOB Intelligence Copilot</h1>
    <p>Professional decision-support interface for planners and customer care to convert aging inventory into order fulfillment opportunities.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.markdown("## Data Control Center")
use_sample = st.sidebar.toggle("Use demo dataset", value=True)
uploaded_inv = st.sidebar.file_uploader("SLOB inventory CSV", type=["csv"])
uploaded_equiv = st.sidebar.file_uploader("Product equivalency CSV", type=["csv"])
uploaded_rules = st.sidebar.file_uploader("Customer restrictions CSV", type=["csv"])

sample_inv, sample_equiv, sample_restrictions = load_sample_data()

if use_sample:
    inv = sample_inv
    equiv = sample_equiv
    restrictions = sample_restrictions
else:
    inv = pd.read_csv(uploaded_inv) if uploaded_inv else pd.DataFrame()
    equiv = pd.read_csv(uploaded_equiv) if uploaded_equiv else pd.DataFrame()
    restrictions = pd.read_csv(uploaded_rules) if uploaded_rules else pd.DataFrame()

st.sidebar.divider()
st.sidebar.markdown("### Operating mode")
mode = st.sidebar.radio(
    "Select workflow",
    ["Single Order Copilot", "Inventory Control Tower", "Rule Library"],
    label_visibility="collapsed"
)

# -----------------------------
# Main tabs
# -----------------------------

if mode == "Single Order Copilot":
    st.markdown('<div class="section-header">Order Intake</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Enter the customer order information. The copilot will scan inventory and rank SLOB actions.</div>', unsafe_allow_html=True)

    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            order_number = st.text_input("Order Number", "SO-10045")
            customer_code = st.text_input("Customer Code", "CUST-001")
        with c2:
            customer_name = st.text_input("Customer Name", "Example Customer")
            required_material = st.text_input("Required Material Code", "GJ-40")
        with c3:
            product_family = st.text_input("Product Family", "Garlic Juice")
            order_qty = st.number_input("Order Quantity", min_value=0.0, value=1200.0, step=100.0)
        with c4:
            uom = st.text_input("UOM", "kg")
            min_shelf = st.number_input("Minimum Shelf Life Days", min_value=0, value=90, step=10)
            required_packaging = st.text_input("Required Packaging", "Tote")

    order = {
        "Order_Number": order_number,
        "Customer_Code": customer_code,
        "Customer_Name": customer_name,
        "Required_Material_Code": required_material,
        "Product_Family": product_family,
        "Order_Qty": order_qty,
        "UOM": uom,
        "Minimum_Shelf_Life_Days": min_shelf,
        "Required_Packaging": required_packaging
    }

    run = st.button("Run SLOB Optimization", type="primary", use_container_width=True)

    if run:
        if inv.empty:
            st.error("Upload SLOB inventory or activate demo dataset.")
        else:
            results = build_recommendations(order, inv, equiv, restrictions)
            good = results[results["Match"].isin(["Green", "Yellow"])]
            green = (results["Match"] == "Green").sum()
            yellow = (results["Match"] == "Yellow").sum()
            red = (results["Match"] == "Red").sum()
            coverage = good["Coverage Qty"].sum()
            value = good["Estimated Value Avoided"].sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.markdown(f'<div class="metric-card"><div class="metric-label">Green Matches</div><div class="metric-value">{green}</div><div class="metric-sub">Ready to allocate</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="metric-label">Yellow Opportunities</div><div class="metric-value">{yellow}</div><div class="metric-sub">Needs approval</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><div class="metric-label">Blocked</div><div class="metric-value">{red}</div><div class="metric-sub">Do not use</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="metric-card"><div class="metric-label">Potential Coverage</div><div class="metric-value">{coverage:,.0f}</div><div class="metric-sub">{uom}</div></div>', unsafe_allow_html=True)
            m5.markdown(f'<div class="metric-card"><div class="metric-label">Value Avoided</div><div class="metric-value">${value:,.0f}</div><div class="metric-sub">estimated</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Executive Recommendation</div>', unsafe_allow_html=True)
            best = good.head(1)
            if not best.empty:
                b = best.iloc[0]
                st.markdown(f"""
                <div class="card">
                    <div>{get_badge(b['Match'])}</div>
                    <div class="card-title" style="margin-top:12px;">{b['Recommended Action']} — Batch {b['Batch']}</div>
                    <div class="card-subtitle">{b['Material']} · {b['Description']} · Available {b['Available Qty']:,.0f} {b['UOM']} · Expires {b['Expiry']}</div>
                    <div class="action-box"><b>AI explanation:</b> {b['AI Explanation']}</div>
                    <div class="risk-box"><b>Risk / approval:</b> {b['Risk']} · Approval needed: {b['Approval Needed']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.text_area("Planner / Customer Care Comment", b["Planner Comment"], height=90)
            else:
                st.warning("No usable SLOB recommendation found for this order.")

            st.markdown('<div class="section-header">Ranked Recommendation Table</div>', unsafe_allow_html=True)
            st.dataframe(
                results[[
                    "Match", "Recommended Action", "Batch", "Material", "Available Qty", "Coverage Qty",
                    "Expiry", "Days to Expiry", "Packaging", "Quality", "Approval Needed",
                    "Risk", "Priority Score", "Estimated Value Avoided", "AI Explanation"
                ]],
                use_container_width=True,
                hide_index=True
            )

            csv = results.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Export Recommendations",
                data=csv,
                file_name=f"SLOB_recommendations_{order_number}.csv",
                mime="text/csv",
                use_container_width=True
            )

elif mode == "Inventory Control Tower":
    st.markdown('<div class="section-header">Inventory Control Tower</div>', unsafe_allow_html=True)
    if inv.empty:
        st.info("Upload inventory or use demo dataset.")
    else:
        inv2 = inv.copy()
        inv2["Days_to_Expiry"] = inv2["Expiry_Date"].apply(calc_days)
        inv2["Priority_Score"] = inv2.apply(risk_score, axis=1)

        total_value = inv2["Inventory_Value"].sum()
        at_risk_value = inv2[inv2["Days_to_Expiry"] <= 90]["Inventory_Value"].sum()
        released = (inv2["Quality_Status"].apply(normalize) == "released").sum()
        blocked = len(inv2) - released

        a, b, c, d = st.columns(4)
        a.markdown(f'<div class="metric-card"><div class="metric-label">Total SLOB Value</div><div class="metric-value">${total_value:,.0f}</div><div class="metric-sub">all visible batches</div></div>', unsafe_allow_html=True)
        b.markdown(f'<div class="metric-card"><div class="metric-label">90-Day Risk Value</div><div class="metric-value">${at_risk_value:,.0f}</div><div class="metric-sub">short shelf life</div></div>', unsafe_allow_html=True)
        c.markdown(f'<div class="metric-card"><div class="metric-label">Released Batches</div><div class="metric-value">{released}</div><div class="metric-sub">usable status</div></div>', unsafe_allow_html=True)
        d.markdown(f'<div class="metric-card"><div class="metric-label">Blocked / Review</div><div class="metric-value">{blocked}</div><div class="metric-sub">QA attention</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">Priority Batches</div>', unsafe_allow_html=True)
        st.dataframe(
            inv2.sort_values("Priority_Score", ascending=False),
            use_container_width=True,
            hide_index=True
        )

else:
    st.markdown('<div class="section-header">Rule Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Maintain equivalency and customer restriction rules. In production, this page would be permission-controlled.</div>', unsafe_allow_html=True)

    st.markdown("#### Product Equivalency Rules")
    st.dataframe(equiv, use_container_width=True, hide_index=True)

    st.markdown("#### Customer Restrictions")
    st.dataframe(restrictions, use_container_width=True, hide_index=True)

st.caption("Prototype version. For production use, connect to ERP inventory/order tables, Dataverse, and Azure OpenAI with Microsoft Entra ID authentication.")
