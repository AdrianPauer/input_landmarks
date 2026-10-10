import streamlit as st
import cv2
import numpy as np
import json
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(layout="wide", page_title="Landmark Selector")
TARGET_POINTS = 16
MAX_DIM = 800

if "points" not in st.session_state:
    st.session_state.points = []
if "last_click" not in st.session_state:
    st.session_state.last_click = None

st.title(f"Mark Exactly {TARGET_POINTS} Landmarks")

uploaded_file = st.file_uploader("Upload a high-res image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Load the original image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)
    orig_h, orig_w = img_rgb.shape[:2]

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Navigation")
        # 2. Add Zoom and Pan Sliders
        zoom_level = st.slider("Zoom Level", min_value=1.0, max_value=10.0, value=1.0, step=0.5)

        # Pan sliders (0 to 100% of the image)
        pan_x_pct = st.slider("Pan X (Horizontal)", 0, 100, 50)
        pan_y_pct = st.slider("Pan Y (Vertical)", 0, 100, 50)

        st.divider()
        st.subheader("Controls")

        if st.button("Undo Last Point", use_container_width=True):
            if len(st.session_state.points) > 0:
                st.session_state.points.pop()
                st.rerun()

        if st.button("Clear All Points", type="primary", use_container_width=True):
            st.session_state.points = []
            st.rerun()

        st.divider()

        # Save Button
        if len(st.session_state.points) == TARGET_POINTS:
            st.success("All 16 points mapped!")
            data = {
                "image": uploaded_file.name,
                "original_resolution": [orig_w, orig_h],
                "points": st.session_state.points
            }
            st.download_button(
                label="Download Points JSON",
                data=json.dumps(data, indent=4),
                file_name="points.json",
                mime="application/json",
                type="primary",
                use_container_width=True
            )

    with col1:
        st.write(f"**Points Selected:** {len(st.session_state.points)} / {TARGET_POINTS}")

        # 3. Calculate cropping based on sliders
        crop_w = orig_w / zoom_level
        crop_h = orig_h / zoom_level

        center_x = orig_w * (pan_x_pct / 100.0)
        center_y = orig_h * (pan_y_pct / 100.0)

        # Clamp bounds so we don't look outside the image
        center_x = max(crop_w / 2, min(center_x, orig_w - crop_w / 2))
        center_y = max(crop_h / 2, min(center_y, orig_h - crop_h / 2))

        x1 = int(center_x - crop_w / 2)
        y1 = int(center_y - crop_h / 2)
        x2 = int(x1 + crop_w)
        y2 = int(y1 + crop_h)

        # 4. Crop and resize for display
        crop_img = img_rgb[y1:y2, x1:x2].copy()

        # Scale to max dimension
        if max(crop_h, crop_w) > MAX_DIM:
            scale_factor = MAX_DIM / float(max(crop_h, crop_w))
            disp_w = int(crop_w * scale_factor)
            disp_h = int(crop_h * scale_factor)
            img_display = cv2.resize(crop_img, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
        else:
            scale_factor = 1.0
            disp_w, disp_h = int(crop_w), int(crop_h)
            img_display = crop_img.copy()

        # 5. Draw existing points that are currently visible
        for idx, (ox, oy) in enumerate(st.session_state.points):
            if x1 <= ox < x2 and y1 <= oy < y2:
                # Map original coordinates to the display crop
                dx = int((ox - x1) * scale_factor)
                dy = int((oy - y1) * scale_factor)

                cv2.circle(img_display, (dx, dy), 4, (255, 0, 0), -1)
                cv2.putText(
                    img_display, str(idx + 1), (dx + 8, dy - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA
                )

        # 6. Render the interactive image
        value = streamlit_image_coordinates(img_display, key="image_click")

        if value is not None:
            click_point = (value["x"], value["y"])

            if click_point != st.session_state.last_click:
                st.session_state.last_click = click_point

                # 7. Convert click from cropped display back to full high-res image
                orig_x = int(x1 + (value["x"] / scale_factor))
                orig_y = int(y1 + (value["y"] / scale_factor))

                if len(st.session_state.points) < TARGET_POINTS:
                    st.session_state.points.append((orig_x, orig_y))
                    st.rerun()
                else:
                    st.warning(f"Maximum of {TARGET_POINTS} points reached!")
else:
    st.info("Please upload an image to begin.")