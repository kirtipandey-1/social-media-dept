import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_latest_daily_brief

st.title("📋 Strategy — Dwight (Employee 11)")
st.caption("Bears. Beets. Social Media Department.")

if st.button("⚡ Generate Daily Brief", type="primary"):
    with st.spinner("Dwight is compiling..."):
        try:
            from mcp_servers.strategy_server import generate_daily_brief
            brief = generate_daily_brief()
            st.cache_data.clear()
            st.success("Brief generated!")
        except ImportError:
            from mcp_servers.reports_server import generate_daily_report
            brief = generate_daily_report()
            st.cache_data.clear()
            st.success("Report generated (strategy_server coming soon)!")

st.markdown("---")
brief = get_latest_daily_brief()
if brief:
    st.caption(f"Generated: {brief['created_at']}")
    st.markdown(brief["body_md"])
else:
    report = st.empty()
    from dashboard.db_helpers import get_latest_report
    r = get_latest_report("daily")
    if r:
        st.caption(f"Latest daily report: {r['created_at']}")
        st.markdown(r["body_md"])
    else:
        st.info("No brief yet. Click Generate.")
