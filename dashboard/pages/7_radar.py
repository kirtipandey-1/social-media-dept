import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_top_opportunities

st.title("🎉 Opportunity Radar — Borat (Employee 8)")
st.caption("VERY NICE! These are today's opportunities!")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔍 Scan Opportunities"):
        with st.spinner("VERY NICE! Borat is scanning..."):
            from mcp_servers.radar_server import scan_opportunities
            try:
                r = scan_opportunities()
                st.success(f"Found {r['opportunities_found']} new from {r['trends_checked']} trends!")
                st.cache_data.clear()
            except Exception as e:
                st.error(str(e))
with col2:
    topic_q = st.text_input("Score a topic", placeholder="lo-fi hip hop beats")

if topic_q and st.button("Rate It"):
    from mcp_servers.radar_server import score_topic
    score = score_topic(topic_q)
    delta = "🔥 Hot" if score >= 75 else "📉 Low" if score < 40 else "🟡 Medium"
    st.metric("Relevance Score", f"{score}/100", delta=delta)

opps = get_top_opportunities(10)
if opps:
    import pandas as pd
    st.dataframe(pd.DataFrame(opps)[["title","score","type","notes"]], use_container_width=True)
else:
    st.info("No opportunities yet. Click Scan!")
