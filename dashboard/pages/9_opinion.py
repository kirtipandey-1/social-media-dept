import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_opinion_topics

st.title("⚡ Opinion Miner — Speed (Employee 10)")
st.caption("YO YO YO! These are today's HOTTEST takes and questions!")

col1, col2 = st.columns(2)
with col1:
    if st.button("💥 Generate 25 Hot Questions", type="primary"):
        st.info("Speed server not yet built (coming soon). Topics below are from Reddit research.")
with col2:
    if st.button("🌶️ Generate Hot Takes"):
        st.info("Speed server coming soon!")

st.markdown("---")
st.subheader("📋 Opinion Topics")
topics = get_opinion_topics(20)
if topics:
    for t in topics:
        badge = "🔥" if t.get("relevance_score", 0) > 0.7 else "💬"
        st.markdown(f"{badge} **{t['topic']}** — _{t['type']}_ (r/{t.get('source','?')})")
else:
    from dashboard.db_helpers import get_recent_reddit
    st.subheader("Reddit Pain Points (Speed's raw material)")
    posts = get_recent_reddit(15)
    for p in posts:
        st.markdown(f"- **r/{p['subreddit']}**: {p['title']}")
