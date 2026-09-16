import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

st.set_page_config(
page_title="Geo Regreen Environmental Intelligence",
page_icon="🌍",
layout="wide",
)

st.markdown(
"<h1>🌍 Geo Regreen Environmental Intelligence</h1>",
unsafe_allow_html=True,
)
st.markdown(
"Satellite Earth Observation → Geospatial Analytics → Environmental Risk Signals"
)

st.info(
"Prototype demonstration: environmental indicators shown here are "
"demonstration data, not live operational telemetry."
)

st.sidebar.header("Analysis Controls")

regions = {
"Gauteng Test Area": (-26.2708, 28.1123),
"Sedibeng Test Area": (-26.6500, 28.0000),
"Tshwane Test Area": (-25.7479, 28.2293),
"Eastern Cape Test Area": (-33.0153, 27.9116),
}

selected_region = st.sidebar.selectbox(
"Area of Interest", list(regions.keys())
)

modules = [
"Vegetation Condition",
"Moisture Stress",
"Flood / Waterlogging Risk",
"Heat / Evaporation Risk",
"Change Detection",
]

analysis_module = st.sidebar.selectbox(
"Environmental Intelligence Module", modules
)

baseline_days = st.sidebar.selectbox(
"Comparison Window", [7, 14, 21, 30], index=1
)

region_seed = list(regions.keys()).index(selected_region) + 1
module_seed = modules.index(analysis_module) + 1
rng = np.random.default_rng(region_seed * 17 + module_seed * 31 + baseline_days)

current_index = round(float(rng.uniform(0.42, 0.82)), 2)
previous_index = round(
min(0.90, current_index + float(rng.uniform(0.08, 0.22))), 2
)
change_pct = round(
((current_index - previous_index) / previous_index) * 100, 1
)
affected_area = round(float(rng.uniform(8, 42)), 1)

if change_pct <= -15:
    status = "HIGH"
    status_text = "Field verification recommended"
    status_icon = "🔴"
elif change_pct <= -7:
    status = "WATCH"
    status_text = "Monitor closely"
    status_icon = "🟡"
else:
    status = "STABLE"
    status_text = "No immediate intervention indicated"
    status_icon = "🟢"

lat, lon = regions[selected_region]

m = folium.Map(
location=[lat, lon],
zoom_start=9,
tiles="OpenStreetMap",
)

offset = 0.045
polygon = [
[lat - offset, lon - offset],
[lat - offset, lon + offset],
[lat + offset, lon + offset],
[lat + offset, lon - offset],
]

folium.Polygon(
locations=polygon,
color="#15803d",
weight=2,
fill=True,
fill_opacity=0.12,
popup=f"{selected_region} — Prototype Area of Interest",
).add_to(m)

folium.Marker(
[lat, lon],
tooltip=selected_region,
popup=(
f"<b>Geo Regreen prototype</b><br>"
f"Module: {analysis_module}<br>"
f"Status: {status}"
),
).add_to(m)

col_map, col_summary = st.columns([2.2, 1])

with col_map:
    st.subheader("Spatial Intelligence")
    st_folium(m, width=None, height=500, returned_objects=[])

with col_summary:
    st.subheader("Risk Signal")

st.metric("Current Environmental Index", f"{current_index:.2f}")
st.metric(
f"Change vs {baseline_days}-day baseline",
f"{change_pct:+.1f}%"
)
st.metric("Area flagged", f"{affected_area:.1f} km²")

st.warning(f"{status_icon} **{status} — {status_text}**")

st.divider()
st.subheader("Environmental Intelligence Summary")

summaries = {
"Vegetation Condition": (
"The prototype indicates a vegetation-condition change relative "
"to the selected baseline. This can help prioritise field "
"verification for possible crop or ecosystem stress."
),
"Moisture Stress": (
"The prototype indicates a moisture-related change signal that "
"could support prioritisation of field visits and investigation "
"of possible water stress."
),
"Flood / Waterlogging Risk": (
"The prototype highlights an area for investigation of possible "
"surface-water accumulation or waterlogging."
),
"Heat / Evaporation Risk": (
"The prototype highlights an area where heat-related environmental "
"stress may warrant additional monitoring or field verification."
),
"Change Detection": (
"The change-detection view compares observations over time to "
"identify areas where environmental conditions have changed."
),
}

st.write(summaries[analysis_module])

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 1. Detect")
    st.write("Identify environmental change across large geographic areas.")

with c2:
    st.markdown("### 2. Prioritise")
    st.write(
    "Rank locations so limited field capacity can focus on higher-risk areas."
    )

with c3:
    st.markdown("### 3. Verify")
    st.write(
    "Provide a clear field-verification signal for operational teams."
    )

st.divider()
st.subheader("Environmental Change Over Time")

dates = pd.date_range(
end=pd.Timestamp.today().normalize(),
periods=8,
freq="7D",
)

values = np.linspace(
previous_index,
current_index,
len(dates)
) + rng.normal(0, 0.012, len(dates))

timeseries = pd.DataFrame(
{"Environmental Index": np.round(values, 3)},
index=dates,
)

st.line_chart(timeseries)

st.caption(
"Prototype time series for interface demonstration. Production deployment "
"will replace demonstration values with Earth Observation-derived observations."
)

st.divider()
st.subheader("Geo Regreen Intelligence Pipeline")

pipeline = st.columns(5)

steps = [
("🛰️", "Earth Observation", "Satellite imagery and environmental data"),
("⚙️", "Processing", "Geospatial and time-series analysis"),
("🧠", "AI / ML", "Anomaly and risk modelling"),
("🚨", "Risk Signals", "Alerts and prioritisation"),
("📊", "Delivery", "Dashboard, API and reports"),
]

for column, (icon, title, description) in zip(pipeline, steps):
    with column:
        st.markdown(f"### {icon} {title}")
        st.caption(description)

st.divider()
st.caption(
"Geo Regreen MVP — Environmental intelligence prototype. "
"Demonstration interface; not a live operational monitoring system."
)