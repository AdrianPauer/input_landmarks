import streamlit as st
import cv2
import numpy as np
import json
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(layout="wide", page_title="Landmark Selector")
TARGET_POINTS = 16
MAX_DIM = 800  # Cap the display size to make the app fast

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

    # 2. Resize the image to make the web app fast
    if max(orig_h, orig_w) > MAX_DIM:
        scale_factor = MAX_DIM / float(max(orig_h, orig_w))
        disp_w = int(orig_w * scale_factor)
        disp_h = int(orig_h * scale_factor)
        img_display = cv2.resize(img_rgb, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
    else:
        scale_factor = 1.0
        img_display = img_rgb.copy()

    # 3. Draw existing points on the small display image
    for idx, (ox, oy) in enumerate(st.session_state.points):
        # Convert high-res saved coordinates down to display size
        dx = int(ox * scale_factor)
        dy = int(oy * scale_factor)

        cv2.circle(img_display, (dx, dy), 4, (255, 0, 0), -1)
        cv2.putText(
            img_display, str(idx + 1), (dx + 8, dy - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA
        )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**Points Selected:** {len(st.session_state.points)} / {TARGET_POINTS}")

        # 4. Render the fast, lightweight resized image
        value = streamlit_image_coordinates(img_display, key="image_click")

        if value is not None:
            # The click coordinates from the 800px image
            click_point = (value["x"], value["y"])

            if click_point != st.session_state.last_click:
                st.session_state.last_click = click_point

                # Convert the click back up to original high-res coordinates
                orig_x = int(value["x"] / scale_factor)
                orig_y = int(value["y"] / scale_factor)

                if len(st.session_state.points) < TARGET_POINTS:
                    st.session_state.points.append((orig_x, orig_y))
                    st.rerun()
                else:
                    st.warning(f"Maximum of {TARGET_POINTS} points reached!")

    with col2:
        st.subheader("Controls")

        if st.button("Undo Last Point", use_container_width=True):
            if len(st.session_state.points) > 0:
                st.session_state.points.pop()
                st.session_state.last_click = None
                st.rerun()

        if st.button("Clear All Points", type="primary", use_container_width=True):
            st.session_state.points = []
            st.session_state.last_click = None
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
else:
    st.info("Please upload an image to begin.")