from pdb import run
import pandas as pd
import streamlit as st
import plotly.express as px

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Airbus Tool Dashboard",
    layout="wide"
)

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
                ✈️ A220 Automation Tools Lifecycle Dashboard
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
# COLOR MAP
# =================================================
COLOR_MAP = {
    "Airbus Canada": "#191970",
    "COT + QChecker": "#b3cde0",
    "Non‑Engineering Tools": "#FFD700",
    "Evaluation": "#FF9912"
}
# =================================================
# LOAD DATA
# =================================================
@st.cache_data
# def load_data():
#     df = pd.read_excel("AirbusTools.xlsx")
#     df.columns = df.columns.str.strip()
#     df.fillna("Unknown", inplace=True)
#     return df

# df = load_data()
# =================================================
# LOAD DATA FROM GOOGLE SHEETS (LIVE)
# =================================================
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/11Dt4ScH0Qe2TUX4HInjwZxQzcoAb1elNNRSSZgsIzqA/export?format=csv"
    
    df = pd.read_csv(url)

    # CLEAN HEADERS
    df.columns = df.columns.str.strip()

    # ✅ FIX TYPES
    text_cols = [
        "Name",
        "Description",
        "Tool Type",
        "BOT Source File Format",
        "Business Function",
        "Business Owner Name",
        "Status"
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    if "Completion (%)" in df.columns:
        df["Completion (%)"] = pd.to_numeric(df["Completion (%)"], errors="coerce")
        df["Completion (%)"] = df["Completion (%)"].fillna(0)

    return df

df = load_data()

import numpy as np

countries = ["France", "Germany", "India", "Canada", "USA", "UK"]

df["Location"] = np.random.choice(countries, size=len(df))

# =================================================
# GOVERNANCE CLASSIFICATION
# =================================================
def classify_governance(row):
    owner = row["Business Owner Name"].strip().lower()
    category = row["BOT/COT/DOT"].strip().upper()
    name = str(row.get("Name", "")).lower()

    if owner == "airbus canada":
        return "Airbus Canada"
    if owner == "tbc":
        return "Non‑Engineering Tools"
    if category == "COT" or "qchecker" in name or "q-checker" in name:
        return "COT + QChecker"
    return "Evaluation"

df["Governance Group"] = df.apply(classify_governance, axis=1)
# =================================================
# FILTERS (BOT/COT/DOT REMOVED)
# =================================================
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = 0

all_bf = sorted(df["Business Function"].unique())
all_gov = sorted(df["Governance Group"].unique())
all_tool_types = sorted(df["BOT/COT/DOT"].unique())

st.markdown("<div style='height:5px;'></div>", unsafe_allow_html=True)
st.markdown("""
<style>

/* ✅ Multiselect text */
div[data-baseweb="select"] span {
    font-size: 16px !important;
}

/* ✅ FORCE pill background change */
span[data-baseweb="tag"] {
    background-color: #191970 !important;  /* Dark Blue */
    color: white !important;
    border-radius: 8px !important;
    padding: 4px 10px !important;
}

/* ✅ Inner label text */
span[data-baseweb="tag"] span {
    color: white !important;
}

/* ✅ Cross icon */
span[data-baseweb="tag"] svg {
    fill: white !important;
}

/* ✅ Hover effect */
span[data-baseweb="tag"]:hover {
    background-color: #0B1F3A !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("#### 🔎 Filters")

# c1, c2, c3 = st.columns([1.5, 1.5, 0.4])
c1, c2, c3, c4 = st.columns([1.0, 1.7, 0.8, 0.4])

business_function = c1.multiselect(
    "Business Function",
    all_bf,
    default=all_bf,
    key=f"bf_{st.session_state.reset_trigger}"
)

default_gov = st.session_state.get("frozen_governance", all_gov)

governance_filter = c2.multiselect(
    "Category",
    all_gov,
    default=default_gov,
    key=f"gov_{st.session_state.reset_trigger}"
)

tool_type_filter = c3.multiselect(
    "BOT/COT/DOT",
    all_tool_types,
    default=all_tool_types,
    key=f"tool_{st.session_state.reset_trigger}"
)

with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Reset"):
        st.session_state.reset_trigger += 1
        st.session_state.pop("frozen_governance", None)
        st.rerun()

st.markdown(
    "<hr style='margin-top:6px; margin-bottom:8px;'>",
    unsafe_allow_html=True
)
# =================================================
# APPLY FILTERS (UPDATED)
# =================================================
selection = st.session_state.get("gov_donut", {}).get("selection", {})

if selection and "points" in selection and len(selection["points"]) > 0:
    selected_gov = selection["points"][0]["label"]

    if st.session_state.get("frozen_governance") != [selected_gov]:
        st.session_state["frozen_governance"] = [selected_gov]
        st.session_state.reset_trigger += 1
        st.rerun()

# filtered_df = df[
#     (df["Business Function"].isin(business_function)) &
#     (df["Governance Group"].isin(governance_filter))
# ]

filtered_df = df[
    (df["Business Function"].isin(business_function)) &
    (df["Governance Group"].isin(governance_filter)) &
    (df["BOT/COT/DOT"].isin(tool_type_filter))
]

if filtered_df.empty:
    st.warning("No tools match the selected filters.")
    st.stop()
# =================================================
# ENGINEERING TOOLS BREAKDOWN
# =================================================
st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
st.markdown("### 🛠 Engineering Tools Breakdown")

engineering_df = filtered_df[
    filtered_df["Business Function"].isin(["Design", "Manufacturing", "Tooling"])
]

k1, k2, k3 = st.columns(3)
k1.metric("Design", (engineering_df["Business Function"] == "Design").sum())
k2.metric("Manufacturing", (engineering_df["Business Function"] == "Manufacturing").sum())
k3.metric("Tooling", (engineering_df["Business Function"] == "Tooling").sum())

st.markdown(
    "<hr style='margin-top:1px; margin-bottom:1px;'>",
    unsafe_allow_html=True
)
# =================================================
# DONUT + TOOL DETAILS
# =================================================
left, right = st.columns([2, 1])

with left:
    st.markdown("<div style='margin-top:-8px'></div>", unsafe_allow_html=True)
    st.markdown("### 🟢 Tool Portfolio Overview")

    gov_counts = (
        filtered_df["Governance Group"]
        .value_counts()
        .reindex(COLOR_MAP.keys(), fill_value=0)
        .reset_index()
    )
    gov_counts.columns = ["Governance Group", "Count"]

    fig = px.pie(
        gov_counts,
        names="Governance Group",
        values="Count",
        hole=0.65,
        color="Governance Group",
        color_discrete_map=COLOR_MAP,
        hover_data=["Count"]
    )
    
    fig.update_traces(
    hovertemplate=
        "<b>%{label}</b><br><br>" +
        "Total Tools: %{value}<br>" +
        "Contribution: %{percent}<br>" +
        "<extra></extra>"
)
    
    # ✅ Highlight selected slice
    fig.update_traces(
        pull=[
            0.08 if gov == st.session_state.get("frozen_governance", [None])[0] else 0
            for gov in gov_counts["Governance Group"]
        ]
    )

    fig.update_layout(
        annotations=[dict(
            text=f"{len(filtered_df)}<br>TOOLS",
            x=0.5,
            y=0.5,
            font_size=28,
            showarrow=False
        )],
        height=480,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="#2F2F2F",   # dark background
            font_size=13,
            font_color="white",
            bordercolor="gray"
        )
    )       

    # ✅ VERY IMPORTANT: render with selection enabled
    st.plotly_chart(
        fig,
        use_container_width=True,
        key="gov_donut",
        on_select="rerun"
    )
with right:

        st.markdown('<div class="right-bg">', unsafe_allow_html=True)

        st.markdown('<div class="inner-box">', unsafe_allow_html=True)

        st.markdown("### 🔍 Tool Details")

        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

        selected_tool = st.selectbox(
            "Select Tool",
            sorted(filtered_df["Name"].unique()),
            key="tool_selector"
        )

        tool = filtered_df[filtered_df["Name"] == selected_tool].iloc[0]

        st.markdown(f"### 🔷 {tool['Name']}")

        st.markdown(f"**Name:** {tool['Name']}")
        st.markdown(f"**Business Function:** {tool['Business Function']}")
        st.markdown(f"**Tool Category:** {tool['BOT/COT/DOT']}")
        st.markdown(f"**Business Owner:** {tool['Business Owner Name']}")
        st.markdown(f"**Governance Group:** {tool['Governance Group']}")

        st.divider()

        if tool["Governance Group"] == "Airbus Canada":
            st.success("✅ Delivered & Operational")
        elif tool["Governance Group"] == "COT + QChecker":
            st.warning("🟣 Licensed / Platform Tool")
        elif tool["Governance Group"] == "Non‑Engineering Tools":
            st.info("⚪ Non‑Engineering Tool")
        else:
            st.warning("🟡 Under Evaluation")

        if st.button("📄 View Full Tool Information", key="view_tool_details"):
            st.session_state["show_tool_dialog"] = True

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =================================================
if st.session_state.get("show_tool_dialog", False):

    @st.dialog("View Full Tool Information")
    def tool_details_dialog():

        # ✅ TOOL DETAILS
        st.markdown(f"### {tool['Name']}")
        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        st.markdown(f"**Business Function:** {tool['Business Function']}")
        st.markdown(f"**Tool Category:** {tool['BOT/COT/DOT']}")
        st.markdown(f"**Business Owner:** {tool['Business Owner Name']}")
        st.markdown(f"**Governance Group:** {tool['Governance Group']}")

        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        # ✅ REMOVE GAP BEFORE DESCRIPTION
        st.markdown("<div style='margin-top:-8px'></div>", unsafe_allow_html=True)
        st.markdown(tool.get("Description", "No additional description available."))

        # ✅ MOVE LIFECYCLE UP

        # ✅ CREATE LEFT (label) + RIGHT (circle)
        c1, c2 = st.columns([3, 1])

        with c1:
            st.markdown(
                "<h4 style='margin-bottom:4px;'>🔄 Tool Progress</h4>",
                unsafe_allow_html=True
            )

        with c2:
            progress = int(tool["Completion (%)"])

            if progress >= 85:
                ring_color = "#28B463"
            elif progress >= 60:
                ring_color = "#F4D03F"
            else:
                ring_color = "#E74C3C"

            st.markdown(
                f"""
                <style>
                .mini-sphere {{
                    width:80px;
                    height:80px;
                    border-radius:50%;
                    background:
                        conic-gradient(
                            {ring_color} {progress * 3.6}deg,
                            #E5EAF3 {progress * 3.6}deg
                        );
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    margin-top:-10px;
                }}

                .mini-inner {{
                    width:55px;
                    height:55px;
                    background:white;
                    border-radius:60%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:14px;
                    font-weight:600;
                    color:#333;
                }}
                </style>

                <div style="display:flex; justify-content:flex-end,padding-right:50px;">
                    <div class="mini-sphere">
                        <div class="mini-inner">
                            {progress}%
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        governance = tool["Governance Group"]

        if governance == "Airbus Canada":
            phases = ["Requirement", "Design", "Development", "Testing", "Monitoring"]

        elif governance == "COT + QChecker":
            phases = ["Identification", "Assessment", "License", "Decision", "Monitoring"]

        elif governance == "Non‑Engineering Tools":
            phases = ["Requirement", "Design", "Build", "Validation", "Release"]

        else:
            phases = ["Requirement", "Planning", "Development", "Testing", "Decision"]

# ✅ UI ONLY (NO PROGRESS, NO COLOR LOGIC)
        phase_html = "".join([f"<div class='phase'>{p}</div>" for p in phases])

        st.markdown(
            f"""
            <style>
              .life {{
                  background:#fff;
                  padding:18px;
                  border-radius:12px;
              }}

              .bar {{
                height:20px;
          background:#E5EAF3;
          border-radius:20px;
          margin:14px 0;
          position:relative;
      }}

      /* ✅ Static green fill (like screenshot feel) */
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
          font-size:13px;
      }}

      .phase:before {{
          content:"";
          display:block;
          height:20px;
          width:2px;
          background:#111;
          margin:0 auto 6px;
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
        if st.button("Close Popup"):
            st.session_state["show_tool_dialog"] = False
            st.rerun()

    tool_details_dialog()

# =================================================
# CATEGORY COMPLETION CALCULATION
# =================================================
category_progress = (
    df.groupby(["Governance Group", "Status"])
    .size()
    .unstack(fill_value=0)
)

# Ensure column exists
if "Completed" not in category_progress.columns:
    category_progress["Completed"] = 0  

# Total tools
category_progress["Total"] = category_progress.sum(axis=1)

# % completion
category_progress["Percent"] = (
    category_progress["Completed"] / category_progress["Total"] * 100
).round(0)
# =================================================
# CATEGORY COMPLETION SUMMARY (4 DONUT CHARTS)
# =================================================
st.markdown("### 📊 Category Completion Overview")

cat_cols = st.columns(4)
categories = ["Airbus Canada", "COT + QChecker", "Non‑Engineering Tools", "Evaluation"]

for i, cat in enumerate(categories):
    with cat_cols[i]:

        if cat in category_progress.index:
            data = category_progress.loc[cat]
            completed = int(data["Completed"])
            total = int(data["Total"])
            percent = int(data["Percent"])
        else:
            completed, total, percent = 0, 0, 0

        remaining = total - completed

        fig_small = px.pie(
            values=[completed, remaining],
            names=["Completed", "Remaining"],
            hole=0.78
        )

        fig_small.update_traces(
            textinfo="none",
            marker=dict(
                colors=[COLOR_MAP[cat], "#E5E7EB"],
                line=dict(color="white", width=2)
            )
        )

        fig_small.update_layout(
            annotations=[
                dict(
                    text=f"<b>{percent}%</b>",
                    x=0.5,
                    y=0.55,
                    font_size=20,
                    showarrow=False
                ),
                dict(
                    text=f"{cat}",
                    x=0.5,
                    y=0.40,
                    font_size=15,
                    showarrow=False
                )
            ],
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=10),
            height=220
        )

        st.plotly_chart(fig_small, use_container_width=True)
        # st.caption(f"{completed} of {total} completed")
# =================================================
# LIFECYCLE
# st.markdown("#### 🌍 Tool Distribution")
left_map, right_heat = st.columns([1.2, 2])

# with left_map:

#     # st.markdown("#### 🌍 Tool Distribution")

#     location_df = (
#         filtered_df.groupby("Location")
#         .size()
#         .reset_index(name="Count")
#     )

#     fig_map = px.choropleth(
#         location_df,
#         locations="Location",
#         locationmode="country names",
#         color="Count",
#         color_continuous_scale="Blues"
#     )

#     fig_map.update_layout(
#         height=520,
#         margin=dict(l=0, r=0, t=10, b=0)
#     )

#     st.plotly_chart(fig_map, use_container_width=True)


with left_map:

    st.markdown("#### 🌍 Tool Distribution")

    location_df = (
        filtered_df.groupby("Location")
        .size()
        .reset_index(name="Count")
    )

    fig_map = px.choropleth(
        location_df,
        locations="Location",
        locationmode="country names",
        color="Count",
        color_continuous_scale=[
            "#D6E4F0",
            "#8FB3D9",
            "#3E79B8",
            "#1B3B6F"
        ]
    )

    # ✅ CLEAN GEO (NO WEIRD BOX / NO CLUTTER)
    fig_map.update_geos(
        showcountries=True,
        countrycolor="#d9d9d9",
        showcoastlines=True,
        showframe=False,
        bgcolor="white",
        projection_type="natural earth"
    )

    # ✅ REMOVE UGLY COLOR BAR (KEY FIX)
    fig_map.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=520
    )

    # ✅ SIMPLE HOVER
    fig_map.update_traces(
        hovertemplate="<b>%{location}</b><br>Tools: %{z}<extra></extra>"
    )

    st.plotly_chart(fig_map, use_container_width=True)


import numpy as np

with right_heat:

# ✅ Sort tools (highest completion first)
        tools = filtered_df.sort_values(by="Completion (%)", ascending=False).reset_index(drop=True)

        # ✅ Grid size
        n = 10  # 10x10

        # ✅ Ensure exactly 100 rows (safe padding)
        if len(tools) < n * n:
            pad_rows = n * n - len(tools)
            pad_df = pd.DataFrame({
                "Name": [""] * pad_rows,
                "Completion (%)": [0] * pad_rows
            })
            tools = pd.concat([tools[["Name", "Completion (%)"]], pad_df], ignore_index=True)
        else:
            tools = tools[["Name", "Completion (%)"]].head(n * n)

        # ✅ Create matrix
        matrix = tools["Completion (%)"].to_numpy().reshape(n, n)

        # ✅ Labels
        labels = (
            tools["Name"]
            .astype(str)
            .apply(lambda x: x[:6])
            .to_numpy()
            .reshape(n, n)
        )

        # ✅ Percent (for annotation)
        percent = tools["Completion (%)"].to_numpy().reshape(n, n)

        # ✅ Plot
        import numpy as np

        # ✅ Create matrix
        matrix = tools["Completion (%)"].to_numpy().reshape(n, n)

        # ✅ Define bins
        bins = [0, 30, 50, 70, 85, 95, 100, 101]

        # ✅ Digitize values
        digitized = np.digitize(matrix, bins)

        # ✅ Exact step colors (your theme)
        colorscale = [
            [0.0, "#FFE5E5"], [0.14, "#FFE5E5"],   # 0–30
            [0.14, "#faf069"], [0.28, "#faf069"], # 30–50
            [0.28, "#fff33b"], [0.42, "#fcf261"], # 50–70
            [0.42, "#fdc70c"], [0.57, "#fdc70c"], # 70–85
            [0.57, "#f3903f"], [0.71, "#f3903f"], # 85–95
            [0.71, "#ed683c"], [0.95, "#ed683c"], # 95–98
            [0.95, "#e93e3a"], [1.0, "#e93a3a"]   # 98–100 (darkest)
        ]

        # ✅ Plot
        fig = px.imshow(
            digitized,
            color_continuous_scale=colorscale,
            aspect="equal"
        )

        # ✅ Remove axes
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        # ✅ Add annotations (original values)
        annotations = []
        for i in range(n):
            for j in range(n):
                name = labels[i][j]
                val = matrix[i][j]

                annotations.append(
                    dict(
                        x=j,
                        y=i,
                        text=f"{name}<br>{int(val)}%",
                        showarrow=False,
                        font=dict(size=9, color="black")
                    )
                )

        fig.update_layout(
            height=520,
            margin=dict(l=5, r=5, t=30, b=5),
            annotations=annotations,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig, use_container_width=True)
st.divider()
progress = int(tool["Completion (%)"])

# # ✅ Keep phases same (recommended)
phases = ["Planning", "Development", "Execution", "Testing", "Decision"]

phase_html = "".join([f"<div class='phase'>{p}</div>" for p in phases])

# st.markdown(
#     f"""
#     <style>
#       .life {{background:#fff;padding:24px;border-radius:16px}}
#       .bar {{height:30px;background:#E5EAF3;border-radius:20px;margin:12px 0}}
#       .prog {{height:100%;width:{progress}%;background:#6FCF6A;border-radius:20px}}
#       .grid {{display:grid;grid-template-columns:repeat(5,1fr);text-align:center}}
#       .phase:before {{content:"";display:block;height:24px;width:2px;background:#111;margin:0 auto 6px}}
#     </style>

#     <div class="life">
#       <b>🔄 Tool Lifecycle Progress</b>
#       <div class="bar"><div class="prog"></div></div>
#       <div class="grid">{phase_html}</div>
#     </div>
#     """,
#     unsafe_allow_html=True
# )
# =================================================
# TABLE
# =================================================
# st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 📋 Enterprise Tool Register (Filtered View)")
st.dataframe(filtered_df, height=420)
