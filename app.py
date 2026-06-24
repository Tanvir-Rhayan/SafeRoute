import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.dhaka_zones import DHAKA_ZONES, SAFE_PLACES_24_7
from utils.safety_score import get_safety_color, get_safety_label, get_zone_safety
from utils.map_render import (create_base_map, add_routes_to_map,
    add_origin_dest_markers, add_safe_places, add_zone_circles,
    create_heatmap, add_legend)
from utils.routing import geocode_location, get_routes
from utils.search import search_places, get_place_coords, get_nearby_open_places

st.set_page_config(page_title="SafeRoute Dhaka", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="collapsed")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

for k, v in {
    "route_result": None, "night_mode": False,
    "show_sos": False, "origin_coords": None, "dest_coords": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div class="tl">
    <span class="logo-icon">🛡️</span>
    <span class="logo-name">SafeRoute</span>
    <span class="logo-badge">Dhaka</span>
  </div>
  <div class="tr">
    <span class="tagline">Navigate safely · Women first</span>
  </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️  Navigate", "🌡️  City Safety", "ℹ️  About"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — NAVIGATE
# ══════════════════════════════════════════════════════════════
with tab1:
    left, right = st.columns([1, 3], gap="medium")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Plan your route</div>', unsafe_allow_html=True)

        # Origin
        origin_query = st.text_input("From",
            placeholder="Type to search — Dhanmondi, Gulshan...",
            key="origin_q")
        origin_final = origin_query
        if origin_query and len(origin_query) >= 2:
            sugg = search_places(origin_query)
            if sugg:
                choice = st.selectbox("", [""] + sugg,
                    key="origin_sel", label_visibility="collapsed")
                if choice:
                    origin_final = choice

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # Destination
        dest_query = st.text_input("To",
            placeholder="Type to search — Uttara, Banani...",
            key="dest_q")
        dest_final = dest_query
        if dest_query and len(dest_query) >= 2:
            sugg = search_places(dest_query)
            if sugg:
                choice = st.selectbox("", [""] + sugg,
                    key="dest_sel", label_visibility="collapsed")
                if choice:
                    dest_final = choice

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        hour = st.slider("Departure time", 0, 23, 14, format="%d:00")

        if   5  <= hour <= 11: tag, tc = "🌅 Morning",            "#f5a623"
        elif 12 <= hour <= 17: tag, tc = "☀️ Afternoon",          "#00c96e"
        elif 18 <= hour <= 20: tag, tc = "🌆 Evening",            "#f5a623"
        else:                  tag, tc = "🌙 Night — be cautious","#e63946"
        st.markdown(
            f'<span class="chip" style="color:{tc};border-color:{tc}">{tag}</span>',
            unsafe_allow_html=True)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: show_safe  = st.checkbox("Safe places",  value=True)
        with c2: show_zones = st.checkbox("Safety zones", value=False)
        night = st.toggle("🌙 Dark map", value=st.session_state.night_mode)
        st.session_state.night_mode = night

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        find = st.button("Find Safe Route →", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # SOS
        st.markdown('<div class="sos-wrap">', unsafe_allow_html=True)
        sos = st.button("🚨  SOS — Share My Location",
                        use_container_width=True, key="sos")
        st.markdown('</div>', unsafe_allow_html=True)
        if sos:
            st.session_state.show_sos = not st.session_state.show_sos
        if st.session_state.show_sos:
            loc = "https://maps.google.com/?q=23.7808,90.4152"
            wa  = f"https://wa.me/?text=🚨 I need help! My location: {loc}"
            st.markdown(f"""
            <div class="sos-box">
              <div class="sos-head">🚨 Emergency Mode</div>
              <div class="sos-body">Share your location instantly.</div>
              <a href="{wa}" target="_blank" class="wa-btn">📱 Send via WhatsApp</a>
            </div>""", unsafe_allow_html=True)
            if st.button("Dismiss", key="dis"):
                st.session_state.show_sos = False

        # Nearby open places
        if st.session_state.origin_coords:
            nearby = get_nearby_open_places(
                st.session_state.origin_coords[0],
                st.session_state.origin_coords[1], hour)
            if nearby:
                st.markdown('<div class="nearby-card">', unsafe_allow_html=True)
                st.markdown('<div class="nearby-title">📍 Open nearby</div>',
                            unsafe_allow_html=True)
                for p in nearby[:5]:
                    icon = ("🏥" if "hospital" in p["type"] else
                            "🚔" if "police"   in p["type"] else
                            "🕌" if "mosque"   in p["type"] else
                            "🏪" if "shop"     in p["type"] else "📍")
                    oh = p["opening_hours"] if p["opening_hours"] not in ["nan",""] else "Open"
                    st.markdown(
                        f'<div class="nearby-row">'
                        f'<span class="ni">{icon}</span>'
                        f'<span class="nn">{p["name"]}</span>'
                        f'<span class="no">{oh}</span>'
                        f'</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # Route results
        if st.session_state.route_result and \
           "error" not in st.session_state.route_result:
            r   = st.session_state.route_result
            f_r = r["fastest"]
            s_r = r["safest"]
            sc  = s_r["safety_score"]
            col = get_safety_color(sc)
            lbl = get_safety_label(sc)
            diff = max(0, s_r['travel_time_min'] - f_r['travel_time_min'])

            st.markdown(f"""
            <div class="result-card">
              <div class="result-head">Route Results</div>
              <div class="rrow"><span class="rl">🛡️ Safety score</span>
                <span class="rv" style="color:{col}">{sc}/100 — {lbl}</span></div>
              <div class="rrow"><span class="rl">🟢 Safest</span>
                <span class="rv">{s_r['travel_time_min']} min · {s_r['distance_km']} km</span></div>
              <div class="rrow"><span class="rl">🔵 Fastest</span>
                <span class="rv">{f_r['travel_time_min']} min · {f_r['distance_km']} km</span></div>
              <div class="rrow"><span class="rl">⏱️ Extra for safety</span>
                <span class="rv">+{diff:.1f} min</span></div>
            </div>""", unsafe_allow_html=True)

            if   sc < 40: st.markdown('<div class="alert red">⚠️ High risk — consider travelling with someone.</div>', unsafe_allow_html=True)
            elif sc < 65: st.markdown('<div class="alert yellow">🟡 Moderate — stay alert, keep phone charged.</div>', unsafe_allow_html=True)
            else:         st.markdown('<div class="alert green">✅ Safe route — stay aware of surroundings.</div>', unsafe_allow_html=True)

    # ── MAP ───────────────────────────────────────────────────────────────────
    with right:
        if find:
            if not origin_final or not dest_final:
                st.error("Please enter both From and To locations.")
            else:
                with st.spinner("Finding your safest route..."):
                    oc = get_place_coords(origin_final) or geocode_location(origin_final)
                    dc = get_place_coords(dest_final)   or geocode_location(dest_final)
                    if oc is None:
                        st.error(f"Could not find: **{origin_final}**")
                    elif dc is None:
                        st.error(f"Could not find: **{dest_final}**")
                    else:
                        st.session_state.origin_coords = oc
                        st.session_state.dest_coords   = dc
                        result = get_routes(oc, dc, hour)
                        st.session_state.route_result  = result
                        if "error" in result:
                            st.error(f"Routing failed: {result['error']}")

        m = create_base_map(night_mode=st.session_state.night_mode)
        if show_zones: m = add_zone_circles(m, hour)
        if show_safe:  m = add_safe_places(m, hour)
        if st.session_state.route_result and \
           "error" not in st.session_state.route_result:
            r = st.session_state.route_result
            m = add_routes_to_map(m, r["fastest"], r["safest"])
            if st.session_state.origin_coords and st.session_state.dest_coords:
                m = add_origin_dest_markers(m,
                    st.session_state.origin_coords,
                    st.session_state.dest_coords,
                    origin_final, dest_final)
        m = add_legend(m)
        st_folium(m, width=None, height=650, returned_objects=[])

# ══════════════════════════════════════════════════════════════
# TAB 2 — CITY SAFETY
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="sec-title">🌡️ Dhaka City Safety Map</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="sec-sub">Red = danger · Green = safe · Drag slider to see safety by hour</p>',
                unsafe_allow_html=True)
    hh = st.slider("Hour of day", 0, 23, 22, format="%d:00", key="hh")
    st_folium(create_heatmap(hh), width=None, height=580, returned_objects=[])

# ══════════════════════════════════════════════════════════════
# TAB 3 — ABOUT
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="about">
      <div class="stat-box">
        <span class="stat-n">80%</span>
        <span class="stat-t">of women in Dhaka have experienced public harassment
        <br><small>— Bangladesh National Women Lawyers Association</small></span>
      </div>
      <h3>What SafeRoute does</h3>
      <p>SafeRoute uses machine learning to score road safety in Dhaka by time,
      lighting, crowd density, and proximity to hospitals and police —
      then finds the <b>safest path</b>, not just the fastest.</p>
      <h3>Features</h3>
      <ul>
        <li>🗺️ 24,000+ real Dhaka locations — shops, mosques, hospitals, schools</li>
        <li>🤖 ML safety scoring with Random Forest model</li>
        <li>⏰ Time-aware — safety shifts by hour</li>
        <li>📍 Live nearby open places with real opening hours</li>
        <li>🚨 One-tap SOS WhatsApp location sharing</li>
        <li>🌙 Day and night map modes</li>
      </ul>
      <h3>Stack</h3>
      <p>Python · Streamlit · Folium · OSMnx · NetworkX · XGBoost · scikit-learn</p>
      <div class="about-foot">Built for ML Hackathon 2026 · Dhaka, Bangladesh</div>
    </div>
    """, unsafe_allow_html=True)