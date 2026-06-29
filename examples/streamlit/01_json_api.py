import sys
import time
from globalhost import GlobalHostApp

# Check if we're running under Streamlit's runtime
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    is_streamlit_runtime = get_script_run_ctx() is not None
except:
    is_streamlit_runtime = False

if not is_streamlit_runtime:
    # Running directly with python3 - launch the tunnel
    host = GlobalHostApp()
    if host.bg_launch("streamlit", __file__, port=8006):
        print(f"\nStreamlit is live in the background!")
        print(f"Public URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
    sys.exit(0)

# Below this is the actual Streamlit app
import streamlit as st

st.set_page_config(page_title="GlobalHost Streamlit", layout="centered")

st.title("Streamlit JSON API Demo")
st.write("This is a simple Streamlit app exposed via Cloudflare Tunnel.")

if st.button("Get JSON Data"):
    st.json({
        "status": "success",
        "message": "Streamlit endpoint is live!",
        "timestamp": time.time()
    })

st.write("---")
st.write("Click the button above to fetch JSON data.")
