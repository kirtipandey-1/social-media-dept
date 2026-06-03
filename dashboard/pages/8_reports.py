import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_latest_report

st.title("📋 Reports — McLovin (Employee 3)")

def report_tab(rtype: str):
    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"⚡ Generate {rtype.title()}"):
            from mcp_servers import reports_server
            with st.spinner("Generating..."):
                fn = getattr(reports_server, f"generate_{rtype}_report")
                fn()
                st.cache_data.clear()
                st.success("Done!")
    with c2:
        if st.button(f"📱 Send to Telegram", key=f"tg_{rtype}"):
            from workers.notifier import TelegramNotifier
            with st.spinner("Sending..."):
                try:
                    TelegramNotifier(rtype).execute()
                    st.success("Sent!")
                except Exception as e:
                    st.error(str(e))
    report = get_latest_report(rtype)
    if report:
        st.caption(f"Generated: {report['created_at']}")
        st.markdown(report["body_md"])
    else:
        st.info(f"No {rtype} report yet.")

t1, t2, t3 = st.tabs(["Daily", "Weekly", "Monthly"])
with t1: report_tab("daily")
with t2: report_tab("weekly")
with t3: report_tab("monthly")
