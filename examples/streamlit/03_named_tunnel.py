import os
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

    # PRO TIP: You can paste the ENTIRE manual command from Cloudflare here!
    # Example: "cloudflared tunnel run --token eyJhIjoi..."
    # The code will automatically extract just the token for you.
    token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "cloudflared tunnel run --token YOUR_TOKEN_HERE")

    if host.bg_launch("streamlit", __file__, port=8006, token=token):
        print(f"\nStreamlit is live on your custom domain!")
        print(f"URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
    sys.exit(0)

# Below this is the actual Streamlit app
import streamlit as st

st.set_page_config(page_title="GlobalHost Named Tunnel", layout="centered")

st.title("Streamlit Named Tunnel Demo")
st.write("This app is exposed via a permanent Cloudflare Named Tunnel.")
st.success("Your custom domain is now reliably mapped to this local server!")

if st.button("Check Connection"):
    st.balloons()
    st.write("Connection stable!")
