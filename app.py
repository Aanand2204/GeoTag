import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from streamlit_js_eval import get_geolocation

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="GeoTag Logo Camera App", layout="centered")

st.title("📸 GeoTag Camera with Logo")

# -------------------------------
# GET LOCATION
# -------------------------------
st.subheader("📍 Location Information")

# Inform user about security requirements for geolocation
st.info("💡 **Tip:** Geolocation requires a secure context. Ensure you are accessing this app via **localhost** or **HTTPS**. If you don't see a prompt, check your browser's site settings.")

# Use the built-in get_geolocation function which is more reliable
loc = get_geolocation()

latitude = "N/A"
longitude = "N/A"

if loc:
    if "coords" in loc:
        latitude = loc["coords"].get("latitude", "N/A")
        longitude = loc["coords"].get("longitude", "N/A")
        st.success(f"Location fetched: {latitude}, {longitude}")
    elif "error" in loc:
        st.error(f"Location error: {loc['error'].get('message', 'Unknown error')}")
        st.warning("Please ensure location is enabled in your browser settings.")
else:
    st.warning("Waiting for location access... Please allow access if prompted by your browser.")

# -------------------------------
# PHOTO SOURCE SELECTION
# -------------------------------
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

    text = (
        f"Date: {date_str}\n"
        f"Time: {time_str}\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}"
    )

    # Calculate text position (bottom left overlay)
    rect_height = 150
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
