import sys
import time
from globalhost import GlobalHostApp

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    is_streamlit_runtime = get_script_run_ctx() is not None
except:
    is_streamlit_runtime = False

if not is_streamlit_runtime:
    host = GlobalHostApp()
    if host.bg_launch("streamlit", __file__, port=8007):
        print(f"\nStreamlit Dashboard is live!")
        print(f"Public URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
    sys.exit(0)

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="GlobalHost Dashboard", layout="wide")

st.title("Streamlit Dashboard Demo")
st.write("A more complex Streamlit app with charts and data visualization.")

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)

col1, col2, col3 = st.columns(3)
col1.metric("Temperature", "70°F", "1.2°F")
col2.metric("Wind", "9 mph", "-8%")
col3.metric("Humidity", "86%", "4%")

st.subheader("Live Chart")
st.line_chart(chart_data)

st.subheader("Interactive Map")
map_data = pd.DataFrame(
    np.random.randn(100, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon']
)
st.map(map_data)
