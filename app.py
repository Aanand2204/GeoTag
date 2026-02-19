import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from geopy.geocoders import Nominatim
import textwrap

# -------------------------------
# PAGE CONFIG & CSS
# -------------------------------
st.set_page_config(page_title="GeoTag Camera", layout="centered", initial_sidebar_state="collapsed")

# Snapchat-style / Modern Mobile CSS
st.markdown("""
    <style>
    /* Main Background */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Header Style */
    .stApp header {
        background-color: transparent;
    }
    
    /* Custom Card Style */
    .css-1r6slb0, .stVerticalBlock {
        gap: 1.5rem;
    }
    
    .snap-header {
        font-family: 'Avenir Next', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        color: #000;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .snap-subheader {
        color: #888;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Styled Radio / Tabs */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        background: #fff;
        padding: 5px;
        border-radius: 50px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Hide some Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Success/Info boxes rounded */
    .stAlert {
        border-radius: 15px;
        border: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Button Style */
    .stButton > button {
        border-radius: 25px;
        padding: 0.6rem 2rem;
        background-color: #FFFC00; /* Snapchat Yellow */
        color: #000;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 14px rgba(255, 252, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 252, 0, 0.6);
        background-color: #FFFC00;
        color: #000;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="snap-header">GeoTag Camera</div>', unsafe_allow_html=True)
st.markdown('<div class="snap-subheader">Capture moments with precise details</div>', unsafe_allow_html=True)

# Initialize geocoders and state
geolocator = Nominatim(user_agent="geotag_camera_app_v2")

if "latitude" not in st.session_state:
    st.session_state.latitude = "N/A"
if "longitude" not in st.session_state:
    st.session_state.longitude = "N/A"
if "address" not in st.session_state:
    st.session_state.address = "N/A"
if "local_time" not in st.session_state:
    st.session_state.local_time = "N/A"

# -------------------------------
# FETCH BROWSER DATA (TIME & LOC)
# -------------------------------
# 1. Fetch Local Time from Browser
browser_time_str = streamlit_js_eval(code='new Date().toLocaleString()', key='time_fetch')
if browser_time_str:
    st.session_state.local_time = browser_time_str

# 2. Fetch Location
loc = get_geolocation()

if loc and "coords" in loc:
    auto_lat = loc["coords"].get("latitude")
    auto_lon = loc["coords"].get("longitude")
    
    if st.session_state.latitude == "N/A" or st.session_state.latitude is None:
        st.session_state.latitude = auto_lat
        st.session_state.longitude = auto_lon
        
        try:
            location = geolocator.reverse(f"{auto_lat}, {auto_lon}")
            if location:
                st.session_state.address = location.address
        except Exception:
            pass

# -------------------------------
# LOCATION & TIME STATUS CARDS
# -------------------------------
col1, col2 = st.columns(2)
with col1:
    st.metric("🕒 Local Time", st.session_state.local_time.split(", ")[-1] if "," in st.session_state.local_time else st.session_state.local_time)
with col2:
    st.metric("📅 Date", st.session_state.local_time.split(", ")[0] if "," in st.session_state.local_time else "N/A")

st.info(f"📍 **Current Address:** {st.session_state.address}")

# -------------------------------
# SEARCH & CORRECTION
# -------------------------------
with st.expander("🔍 Incorrect location? Search here"):
    search_query = st.text_input("Enter location (e.g., 'SPPU, Pune')")
    if st.button("Update Location"):
        if search_query:
            try:
                res = geolocator.geocode(search_query)
                if res:
                    st.session_state.latitude = res.latitude
                    st.session_state.longitude = res.longitude
                    st.session_state.address = res.address
                    st.success(f"Updated to: {res.address}")
                    st.rerun()
                else:
                    st.error("Location not found.")
            except Exception as e:
                st.error(f"Error: {e}")

# -------------------------------
# PHOTO SOURCE SELECTION (MODERN TOGGLE)
# -------------------------------
st.markdown("### 📸 Take or Upload Photo")
photo_source = st.radio("", ["Camera", "Upload Image"], label_visibility="collapsed")

target_image = None

if photo_source == "Camera":
    camera_image = st.camera_input("Click a photo")
    if camera_image:
        target_image = camera_image
else:
    uploaded_image = st.file_uploader("Upload from gallery", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        target_image = uploaded_image

if target_image is not None:
    # Process Image
    base_image = Image.open(io.BytesIO(target_image.getvalue())).convert("RGBA")
    
    # Text Overlay Logic
    draw = ImageDraw.Draw(base_image)
    
    # Format text for overlay
    time_display = st.session_state.local_time
    wrapped_address = textwrap.fill(st.session_state.address, width=45)
    
    overlay_text = (
        f"Time: {time_display}\n"
        f"GPS: {st.session_state.latitude}, {st.session_state.longitude}\n"
        f"Loc: {wrapped_address}"
    )

    # Dynamic Background Rectangle (Snapchat-style bottom translucent bar)
    line_count = overlay_text.count('\n') + 1
    rect_h = 60 + (line_count * 35)
    
    # Semi-transparent black background for white text (Pro Look)
    draw.rectangle((0, base_image.height - rect_h, base_image.width, base_image.height), fill=(0, 0, 0, 160))
    
    # Using default font (can expand to custom .ttf later)
    draw.text((30, base_image.height - rect_h + 20), overlay_text, fill="white")

    # -------------------------------
    # LOGO & ACTION BAR
    # -------------------------------
    st.markdown("---")
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.markdown("#### 🎨 Brand Logo")
        logo_file = st.file_uploader("Optional Logo", type=["png", "jpg", "jpeg"], key="logo_up")
        if logo_file:
            logo = Image.open(logo_file).convert("RGBA")
            logo = logo.resize((150, 150))
            base_image.paste(logo, (base_image.width - 170, 30), logo)

    with col_r:
        # Final Download Button in the right column
        st.markdown("#### 🚀 Action")
        buf = io.BytesIO()
        base_image.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Photo",
            data=buf.getvalue(),
            file_name=f"GeoTag_{datetime.datetime.now().strftime('%H%M%S')}.png",
            mime="image/png"
        )

    # Preview
    st.markdown("### ✨ Preview")
    st.image(base_image, use_container_width=True)
