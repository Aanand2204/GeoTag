import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import textwrap

# -------------------------------
# PAGE CONFIG & CSS
# -------------------------------
st.set_page_config(page_title="GeoTag Camera", layout="centered", initial_sidebar_state="collapsed")

# Snapchat-style / Modern Mobile CSS
st.markdown("""
    <style>
    .main { background-color: #f7f7f7; }
    .snap-header {
        font-family: 'Avenir Next', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800; color: #000; font-size: 2.5rem;
        text-align: center; margin-bottom: 0.5rem; letter-spacing: -1px;
    }
    .snap-subheader { color: #888; text-align: center; font-size: 1rem; margin-bottom: 2rem; }
    
    /* Styled Radio */
    div.row-widget.stRadio > div {
        flex-direction: row; justify-content: center;
        background: #fff; padding: 5px; border-radius: 50px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Places List Item Style */
    .place-item {
        background: white;
        padding: 12px 18px;
        border-radius: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #FFFC00;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .place-item:hover { transform: scale(1.02); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .place-name { font-weight: bold; font-size: 1.1rem; color: #000; margin: 0; }
    .place-address { font-size: 0.85rem; color: #666; margin: 2px 0; }
    .place-distance { font-size: 0.8rem; color: #FFFC00; font-weight: bold; background: #000; padding: 2px 8px; border-radius: 10px; display: inline-block; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Button Style */
    .stButton > button {
        border-radius: 25px; padding: 0.6rem 2rem;
        background-color: #FFFC00; color: #000; font-weight: bold;
        border: none; box-shadow: 0 4px 14px rgba(255, 252, 0, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="snap-header">GeoTag Camera</div>', unsafe_allow_html=True)
st.markdown('<div class="snap-subheader">Discover places and capture memories</div>', unsafe_allow_html=True)

# Initialize geocoders and state
geolocator = Nominatim(user_agent="geotag_camera_v3")

if "latitude" not in st.session_state: st.session_state.latitude = None
if "longitude" not in st.session_state: st.session_state.longitude = None
if "selected_venue" not in st.session_state: st.session_state.selected_venue = "Current Location"
if "full_address" not in st.session_state: st.session_state.full_address = "Detecting..."
if "local_time" not in st.session_state: st.session_state.local_time = "N/A"
if "search_results" not in st.session_state: st.session_state.search_results = []

# -------------------------------
# DATA FETCHING
# -------------------------------
# 1. Fetch Browser Local Time
t = streamlit_js_eval(code='new Date().toLocaleString()', key='time_v3')
if t: st.session_state.local_time = t

# 2. Fetch Location
loc = get_geolocation()
if loc and "coords" in loc:
    lat, lon = loc["coords"].get("latitude"), loc["coords"].get("longitude")
    if st.session_state.latitude is None:
        st.session_state.latitude, st.session_state.longitude = lat, lon
        try:
            rev_loc = geolocator.reverse(f"{lat}, {lon}")
            if rev_loc: st.session_state.full_address = rev_loc.address
        except: pass

# -------------------------------
# SEARCH & PLACES (SNAPCHAT STYLE)
# -------------------------------
st.markdown("### 🔍 Search Places")
query = st.text_input("", placeholder="Search for a venue, cafe, or park...", label_visibility="collapsed")

if st.button("Find Places"):
    if query:
        try:
            results = geolocator.geocode(query, exactly_one=False, limit=5)
            if results:
                st.session_state.search_results = results
            else:
                st.error("No places found.")
        except Exception as e:
            st.error(f"Search error: {e}")

# Display Places List
if st.session_state.search_results:
    st.markdown("#### Found Places")
    for place in st.session_state.search_results:
        # Calculate distance if we have current location
        dist_str = ""
        if st.session_state.latitude and st.session_state.longitude:
            d = geodesic((st.session_state.latitude, st.session_state.longitude), (place.latitude, place.longitude)).meters
            dist_str = f"{int(d)} m" if d < 1000 else f"{round(d/1000, 1)} km"

        with st.container():
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                # We try to extract a 'name' if available, otherwise use first part of address
                name = place.address.split(",")[0]
                addr = ", ".join(place.address.split(",")[1:3])
                st.markdown(f"""
                    <div class="place-item">
                        <p class="place-name">{name}</p>
                        <p class="place-address">{addr}</p>
                        <span class="place-distance">{dist_str}</span>
                    </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("Select", key=f"sel_{place.latitude}_{place.longitude}"):
                    st.session_state.selected_venue = name
                    st.session_state.full_address = place.address
                    st.session_state.latitude = place.latitude
                    st.session_state.longitude = place.longitude
                    st.success(f"Selected: {name}")
                    st.rerun()

# -------------------------------
# CURRENT SELECTION SUMMARY
# -------------------------------
st.markdown("---")
st.write(f"🌟 **Targeting:** {st.session_state.selected_venue}")
st.write(f"🕒 **Time:** {st.session_state.local_time}")

# -------------------------------
# PHOTO LOGIC
# -------------------------------
st.markdown("### 📸 Capture / Upload")
src = st.radio("", ["Camera", "Gallery"], label_visibility="collapsed")

img_input = None
if src == "Camera":
    img_input = st.camera_input("Smile!")
else:
    img_input = st.file_uploader("Choose a photo", type=["jpg", "png", "jpeg"])

if img_input:
    img = Image.open(io.BytesIO(img_input.getvalue())).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # Snapchat-style Text Overlay (Main Event)
    venue = st.session_state.selected_venue.upper()
    time_val = st.session_state.local_time
    gps_info = f"{st.session_state.latitude}, {st.session_state.longitude}"
    address_wrapped = textwrap.fill(st.session_state.full_address, width=50)

    overlay_text = (
        f"{venue}\n"
        f"--------------------------\n"
        f"{time_val}\n"
        f"GPS: {gps_info}\n"
        f"{address_wrapped}"
    )

    # Dynamic Height Calculation
    line_count = overlay_text.count('\n') + 1
    rect_h = 80 + (line_count * 35)
    
    # Translucent Background for readability
    draw.rectangle((0, img.height - rect_h, img.width, img.height), fill=(0, 0, 0, 180))
    
    # Font Style (Simple default but spaced)
    draw.text((40, img.height - rect_h + 30), overlay_text, fill="white")

    # Optional Logo
    # (Keeping the logo upload available)
    st.markdown("---")
    l_file = st.file_uploader("Add Logo (Optional)", type=["png", "jpg"])
    if l_file:
        logo = Image.open(l_file).convert("RGBA").resize((150, 150))
        img.paste(logo, (img.width - 180, 40), logo)

    # Preview & Download
    st.markdown("### ✨ Final Snap")
    st.image(img, use_container_width=True)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button("⬇️ Download Snap", buf.getvalue(), f"Snap_{datetime.datetime.now().strftime('%M%S')}.png", "image/png")
