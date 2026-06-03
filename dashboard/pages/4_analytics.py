import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_post_performance

st.title("📊 Analytics — McLovin (Employee 3)")

st.info("💡 Sync analytics via dashboard buttons or ask Claude Code: 'sync my Instagram analytics'")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📱 Sync Instagram"):
        st.info("Use Claude Code: 'sync my Instagram Insights'")
with col2:
    if st.button("▶️ Sync YouTube"):
        st.info("Use Claude Code: 'sync my YouTube analytics'")
with col3:
    if st.button("👥 Sync Facebook"):
        st.info("Use Claude Code: 'sync my Facebook insights'")

perf = get_post_performance(20)
if perf:
    import pandas as pd
    df = pd.DataFrame(perf)
    st.subheader("Post Performance")
    st.dataframe(df[["posted_at","platform","views","likes","saves","comments"]], use_container_width=True)
    if "views" in df.columns and len(df) > 1:
        try:
            st.subheader("Views Over Time")
            chart_df = df.set_index("posted_at")["views"]
            st.line_chart(chart_df)
        except Exception:
            pass
else:
    st.info("No analytics data yet.")
