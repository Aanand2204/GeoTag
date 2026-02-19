import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
import textwrap

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="GeoTag Logo Camera App", layout="centered")

st.title("📸 GeoTag Camera with Logo")

# Initialize geocoder
geolocator = Nominatim(user_agent="geotag_camera_app")

# Session state for location
if "latitude" not in st.session_state:
    st.session_state.latitude = "N/A"
if "longitude" not in st.session_state:
    st.session_state.longitude = "N/A"
if "address" not in st.session_state:
    st.session_state.address = "N/A"

# -------------------------------
# GET LOCATION (AUTO)
# -------------------------------
st.subheader("📍 Location Information")

# Inform user about security requirements for geolocation
st.info("💡 **Tip:** Geolocation requires a secure context (localhost or HTTPS). If you don't see a prompt, check your browser's site settings.")

# Use the built-in get_geolocation function
loc = get_geolocation()

if loc and "coords" in loc:
    auto_lat = loc["coords"].get("latitude")
    auto_lon = loc["coords"].get("longitude")
    
    # Only update if it's the first time or auto-detect is requested
    if st.session_state.latitude == "N/A":
        st.session_state.latitude = auto_lat
        st.session_state.longitude = auto_lon
        
        # Reverse Geocode
        try:
            location = geolocator.reverse(f"{auto_lat}, {auto_lon}")
            if location:
                st.session_state.address = location.address
        except Exception as e:
            st.error(f"Error fetching address: {e}")

# -------------------------------
# MANUAL LOCATION SEARCH
# -------------------------------
st.markdown("---")
st.subheader("🔍 Search & Correct Location")
search_query = st.text_input("If address is wrong, search here (e.g., 'SPPU, Pune')")

if st.button("Search and Update"):
    if search_query:
        try:
            location = geolocator.geocode(search_query)
            if location:
                st.session_state.latitude = location.latitude
                st.session_state.longitude = location.longitude
                st.session_state.address = location.address
                st.success(f"Location updated to: {location.address}")
            else:
                st.error("Location not found. Please be more specific.")
        except Exception as e:
            st.error(f"Search error: {e}")
    else:
        st.warning("Please enter a location to search.")

# Display current location status
st.write(f"**Current Latitude:** {st.session_state.latitude}")
st.write(f"**Current Longitude:** {st.session_state.longitude}")
st.write(f"**Current Address:** {st.session_state.address}")

# -------------------------------
# PHOTO SOURCE SELECTION
# -------------------------------
st.markdown("---")
st.subheader("🖼️ Select Photo Source")
photo_source = st.radio("How would you like to provide the photo?", ["Camera", "Upload Photo"])

target_image = None

if photo_source == "Camera":
    camera_image = st.camera_input("Click a photo")
    if camera_image:
        target_image = camera_image
else:
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        target_image = uploaded_image

if target_image is not None:
    # Convert image
    image_bytes = target_image.getvalue()
    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # Get date & time
    now = datetime.datetime.now()
    date_str = now.strftime("%d %b %Y")
    time_str = now.strftime("%I:%M %p")

    # -------------------------------
    # DRAW TEXT ON IMAGE
    # -------------------------------
    draw = ImageDraw.Draw(base_image)
    
    # Wrap address text if it's too long
    # We estimate width based on image size (approx 40-50 chars for standard mobile aspect)
    wrapped_address = textwrap.fill(st.session_state.address, width=50)

    text = (
        f"Date: {date_str}   Time: {time_str}\n"
        f"Lat: {st.session_state.latitude}, Lon: {st.session_state.longitude}\n"
        f"Address: {wrapped_address}"
    )

    # Calculate text position (bottom left overlay)
    # Adjust height based on wrapped text lines
    line_count = text.count('\n') + 1
    rect_height = 40 + (line_count * 30) 
    
    draw.rectangle((0, base_image.height - rect_height, base_image.width, base_image.height), fill=(255, 255, 255, 180))
    draw.text((20, base_image.height - rect_height + 20), text, fill="black")

    st.subheader("📍 Geo Information Summary")
    st.text(text)

    # -------------------------------
    # LOGO UPLOAD
    # -------------------------------
    st.subheader("🎨 Add Logo")
    logo_file = st.file_uploader("Upload logo (PNG preferred)", type=["png", "jpg", "jpeg"], key="logo_uploader")

    if logo_file is not None:
        logo = Image.open(logo_file).convert("RGBA")

        # Resize logo
        logo_size = (150, 150)
        logo = logo.resize(logo_size)
        
        img_w, img_h = base_image.size
        logo_x = img_w - logo_size[0] - 20
        logo_y = 20

        base_image.paste(logo, (logo_x, logo_y), logo)

    # -------------------------------
    # PREVIEW & DOWNLOAD
    # -------------------------------
    st.subheader("✅ Final Result")
    st.image(base_image, use_container_width=True)

    # Save to buffer for download
    buf = io.BytesIO()
    base_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="⬇ Download Final Image",
        data=byte_im,
        file_name="geotag_image.png",
        mime="image/png"
    )
