import streamlit as st
import cv2
import numpy as np
import json
from streamlit_image_coordinates import streamlit_image_coordinates

# Set up the page
st.set_page_config(layout="wide", page_title="Landmark Selector")
TARGET_POINTS = 16

# --- Initialize Session State ---
# Streamlit re-runs the whole script on every interaction.
# Session state keeps your variables alive between re-runs.
if "points" not in st.session_state:
    st.session_state.points = []
if "last_click" not in st.session_state:
    st.session_state.last_click = None

st.title(f"Mark Exactly {TARGET_POINTS} Landmarks")

# File uploader for the web interface
uploaded_file = st.file_uploader("Upload a high-res image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert uploaded file to an OpenCV image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # OpenCV uses BGR, but Streamlit expects RGB
    img_rgb = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)
    orig_h, orig_w = img_rgb.shape[:2]

    # Draw existing points on a copy of the image
    img_display = img_rgb.copy()
    for idx, (x, y) in enumerate(st.session_state.points):
        # Draw red circle and text (RGB format: 255, 0, 0 is Red)
        cv2.circle(img_display, (x, y), 6, (255, 0, 0), -1)
        cv2.putText(
            img_display, str(idx + 1), (x + 10, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA
        )

    # UI Layout: Image on the left, controls on the right
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**Points Selected:** {len(st.session_state.points)} / {TARGET_POINTS}")

        # Render the image and capture clicks
        # This component automatically scales the image to fit the column width
        # but returns coordinates mapped to the ORIGINAL image resolution!
        value = streamlit_image_coordinates(img_display, key="image_click")

        # Process the click
        if value is not None:
            point = (value["x"], value["y"])

            # Prevent double-registering the same click event
            if point != st.session_state.last_click:
                st.session_state.last_click = point

                if len(st.session_state.points) < TARGET_POINTS:
                    st.session_state.points.append(point)
                    st.rerun()  # Immediately refresh the UI to show the new dot
                else:
                    st.warning(f"Maximum of {TARGET_POINTS} points reached!")

    with col2:
        st.subheader("Controls")

        # Undo Button
        if st.button("Undo Last Point", use_container_width=True):
            if len(st.session_state.points) > 0:
                st.session_state.points.pop()
                st.session_state.last_click = None
                st.rerun()

        # Clear Button
        if st.button("Clear All Points", type="primary", use_container_width=True):
            st.session_state.points = []
            st.session_state.last_click = None
            st.rerun()

        st.divider()

        # Save Button (Only shows up when 16 points are selected)
        if len(st.session_state.points) == TARGET_POINTS:
            st.success("All 16 points mapped!")

            # Prepare JSON payload
            data = {
                "image": uploaded_file.name,
                "original_resolution": [orig_w, orig_h],
                "points": st.session_state.points
            }
            json_string = json.dumps(data, indent=4)

            # Native Streamlit download button
            st.download_button(
                label="Download Points JSON",
                data=json_string,
                file_name="../points.json",
                mime="application/json",
                type="primary",
                use_container_width=True
            )
else:
    st.info("Please upload an image to begin.")