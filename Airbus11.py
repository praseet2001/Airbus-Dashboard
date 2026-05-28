import pandas as pd
import streamlit as st
import plotly.express as px

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Airbus Multi-Program Dashboard", layout="wide")

# =================================================
# HEADER
# =================================================
st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #0B1F3A, #1B3B6F);
        padding: 22px 30px;
        border-radius: 12px;
        margin-top: -25px;
        margin-bottom: 6px;
    ">
        <div style="text-align:center;">
            <h2 style="color:white; margin-bottom:6px;">
                ✈️ Airbus Automation Tools Lifecycle Dashboard
            </h2>
            <p style="color:#D1D5DB; font-size:14px;">
                Lifecycle-based tracking of automation tools across categories and operational status.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =================================================
# LOAD DATA
# =================================================
@st.cache_data
def load_data():
    df = pd.read_excel("AirbusTools11.xlsx")
    df.columns = df.columns.str.strip()
    df.fillna("Unknown", inplace=True)
    return df

df = load_data()

# =================================================
# ✅ PROGRAM PROCESSING
# =================================================
df["Program List"] = df["Program"].astype(str).apply(
    lambda x: [p.strip() for p in x.split(",") if p.strip()]
)

df["Program Count"] = df["Program List"].apply(len)

def reuse_category(x):
    if x == 1:
        return "Single Program"
    elif x <= 3:
        return "Shared Tools (A320+A350)"
    else:
        return "Enterprise Tools (A320+A350+A330+A380)"

df["Reuse Category"] = df["Program Count"].apply(reuse_category)

df_exploded = df.explode("Program List")

# =================================================
# ✅ FILTER SETUP
# =================================================
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = 0

all_programs = sorted(df_exploded["Program List"].dropna().unique())
all_bf = sorted(df_exploded["Business Function"].dropna().unique())
all_tool_type = sorted(df_exploded["BOT/COT/DOT"].dropna().unique())

# =================================================
# ✅ FILTER UI
# =================================================
st.markdown("<div style='height:5px;'></div>", unsafe_allow_html=True)

st.markdown("""
<style>
div[data-baseweb="select"] span {
    font-size: 16px !important;
}
span[data-baseweb="tag"] {
    background-color: #191970 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 4px 10px !important;
}
span[data-baseweb="tag"]:hover {
    background-color: #0B1F3A !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("#### 🔎 Filters")

# ✅ NOW ONLY 4 COLUMNS
c1, c2, c3, c4 = st.columns([1.3, 2.0, 0.8, 0.2])

program_filter = c1.multiselect(
    "Aircraft Program",
    all_programs,
    default=all_programs,
    key=f"prog_{st.session_state.reset_trigger}"
)

business_function = c2.multiselect(
    "Business Function",
    all_bf,
    default=all_bf,
    key=f"bf_{st.session_state.reset_trigger}"
)

tool_type_filter = c3.multiselect(
    "Tool Classification",
    all_tool_type,
    default=all_tool_type,
    key=f"type_{st.session_state.reset_trigger}"
)

# ✅ RESET BUTTON
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹Reset"):
        st.session_state.reset_trigger += 1
        st.rerun()

st.markdown("<hr style='margin-top:6px; margin-bottom:8px;'>", unsafe_allow_html=True)

# =================================================
# ✅ APPLY FILTERS (NO GOVERNANCE NOW ✅)
# =================================================
filtered_df = df_exploded[
    (df_exploded["Program List"].isin(program_filter)) &
    (df_exploded["Business Function"].isin(business_function)) &
    (df_exploded["BOT/COT/DOT"].isin(tool_type_filter))
]

filtered_df = filtered_df.drop_duplicates(subset=["Name"])

# =================================================
# ✅ EMPTY CHECK
# =================================================
if filtered_df.empty:
    st.warning("No tools match the selected filters.")
    st.stop()

# =================================================
# ✅ KPIs
# =================================================
total_tools = filtered_df["Name"].nunique()

single_tools = filtered_df[filtered_df["Program Count"] == 1]["Name"].nunique()
shared_tools = filtered_df[
    (filtered_df["Program Count"] > 1) & (filtered_df["Program Count"] <= 3)
]["Name"].nunique()
enterprise_tools = filtered_df[filtered_df["Program Count"] > 3]["Name"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Tools", total_tools)
k2.metric("Single Program", single_tools)
k3.metric("Shared Tools", shared_tools)
k4.metric("Enterprise Tools", enterprise_tools)

# =================================================
# ✅ DONUT CHARTS
# =================================================
# d1, d2 = st.columns(2)

# ✅ FIXED PROGRAM DISTRIBUTION (IMPORTANT 🔥)

program_df = df_exploded[
    (df_exploded["Program List"].isin(program_filter)) &
    (df_exploded["Business Function"].isin(business_function)) &
    (df_exploded["BOT/COT/DOT"].isin(tool_type_filter))
]

program_counts = program_df["Program List"].value_counts().reset_index()
program_counts.columns = ["Program", "Count"]


fig_program = px.pie(
    program_counts,
    names="Program",
    values="Count",
    hole=0.65,
    # color_discrete_sequence=[
    #     "#2F4F5F",  # darkest → highest value
    #     "#4A6C82",
    #     "#5B8BB0",
    #     "#5499C7",
    #     "#5DADE2"   # lightest → smallest
    # ]
    color_discrete_sequence=px.colors.sequential.Blues_r
)

fig_program.update_layout(
    title="📊 Tools Distribution by Aircraft Program",
    annotations=[dict(
        text=f"{len(filtered_df)}<br>TOOLS",
        x=0.5, y=0.5,
        showarrow=False,
        font_size=22
    )],
    height=470
)

# REUSE DISTRIBUTION
reuse_counts = filtered_df["Reuse Category"].value_counts().reset_index()
reuse_counts.columns = ["Reuse", "Count"]

fig_reuse = px.pie(
    reuse_counts,
    names="Reuse",
    values="Count",
    hole=0.65,
    color="Reuse",
    color_discrete_map={
        "Single Program": "#E39014",
        "Shared Tools": "#F2C614",
        "Enterprise Tools": "#12F516"
    }
)

fig_reuse.update_layout(
    title="🔁 Tool Reusability Across Programs",
    annotations=[dict(
        text=f"{len(filtered_df)}<br>TOOLS",
        x=0.5, y=0.5,
        showarrow=False,
        font_size=22
    )],
    height=470
)

# =================================================
# ✅ NEW LAYOUT (BIG DONUT + TOOL PANEL + REUSE BELOW)
# =================================================

# ✅ MAIN ROW
left, right = st.columns([2, 1])   # 🔥 LEFT BIG, RIGHT SMALL

# -----------------------------
# ✅ LEFT → BIG PROGRAM DONUT
# -----------------------------
with left:
    st.markdown("### 🌍 Aircraft Program Distribution")

    fig_program.update_layout(height=520)

    st.plotly_chart(fig_program, use_container_width=True)


# -----------------------------
# ✅ RIGHT → TOOL DETAILS PANEL
# -----------------------------
with right:

    st.markdown("### 🔍 Tool Details")

    selected_tool = st.selectbox(
        "Select Tool",
        sorted(filtered_df["Name"].unique()),
        key="tool_selector"
    )

    tool = filtered_df[filtered_df["Name"] == selected_tool].iloc[0]

    # ✅ TITLE
    st.markdown(f"### 🔷 {tool['Name']}")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ✅ DETAILS (MATCH OLD STYLE)
    st.markdown(f"**Name:** {tool['Name']}")
    st.markdown(f"**Business Function:** {tool['Business Function']}")
    st.markdown(f"**Tool Category:** {tool['BOT/COT/DOT']}")
    st.markdown(f"**Programs:** {tool['Program']}")

    # ✅ ADD THIS ONLY IF COLUMN EXISTS (SAFE)
    if "Business Owner Name" in tool:
        st.markdown(f"**Business Owner:** {tool['Business Owner Name']}")

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    if st.button("📄 View Full Tool Information", key="view_tool_details"):
            st.session_state["show_tool_dialog"] = True

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


if st.session_state.get("show_tool_dialog", False):

    @st.dialog("View Full Tool Information")
    def tool_details_dialog():

        # ✅ TOOL DETAILS
        st.markdown(f"### {tool['Name']}")
        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        st.markdown(f"**Business Function:** {tool['Business Function']}")
        st.markdown(f"**Tool Category:** {tool['BOT/COT/DOT']}")
        st.markdown(f"**Business Owner:** {tool.get('Business Owner Name','-')}")

        # ✅ SAFE (because Governance may not exist in new file)
        if "Governance Group" in tool:
            st.markdown(f"**Governance Group:** {tool['Governance Group']}")

        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        st.markdown(tool.get("Description", "No description available."))

        # =================================================
        # ✅ PROGRESS RING
        # =================================================
        c1, c2 = st.columns([3, 1])

        with c1:
            st.markdown("#### 🔄 Tool Progress")

        with c2:
            progress = int(tool.get("Completion (%)", 0))

            if progress >= 85:
                ring_color = "#28B463"
            elif progress >= 60:
                ring_color = "#F4D03F"
            else:
                ring_color = "#E74C3C"

            st.markdown(
                f"""
                <div style="width:80px;height:80px;border-radius:50%;
                    background:conic-gradient({ring_color} {progress * 3.6}deg, #E5EAF3 0deg);
                    display:flex;align-items:center;justify-content:center;">
                    
                    <div style="width:55px;height:55px;background:white;
                        border-radius:50%;display:flex;align-items:center;
                        justify-content:center;font-weight:bold;">
                        {progress}%
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        # =================================================
        # ✅ LIFECYCLE BAR
        # =================================================
        phases = ["Planning", "Development", "Execution", "Testing", "Decision"]

        phase_html = "".join([f"<div class='phase'>{p}</div>" for p in phases])

        st.markdown(
            f"""
            <style>
            .life {{
                background:#fff;
                padding:15px;
                border-radius:10px;
            }}

            .bar {{
                height:18px;
                background:#E5EAF3;
                border-radius:20px;
                margin:12px 0;
            }}

            .prog {{
                height:100%;
                width:{progress}%;
                background:{ring_color};
                border-radius:20px;
            }}

            .grid {{
                display:grid;
                grid-template-columns:repeat(5,1fr);
                text-align:center;
                font-size:12px;
            }}

            .phase:before {{
                content:"";
                display:block;
                height:15px;
                width:2px;
                background:#111;
                margin:0 auto 4px;
            }}
            </style>

            <div class="life">
                <div class="bar">
                    <div class="prog"></div>
                </div>
                <div class="grid">
                    {phase_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ✅ CLOSE BUTTON
        if st.button("Close"):
            st.session_state["show_tool_dialog"] = False
            st.rerun()

    tool_details_dialog()
# =================================================
# ✅ SECOND ROW → REUSE DONUT
# =================================================

st.markdown("### 🔁 Tool Reusability Across Programs")

fig_reuse.update_layout(height=420)

st.plotly_chart(fig_reuse, use_container_width=True)

# =================================================
# ✅ DISPLAY
# =================================================
# d1.plotly_chart(fig_program, use_container_width=True)
# d2.plotly_chart(fig_reuse, use_container_width=True)
