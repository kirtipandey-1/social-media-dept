import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_pain_points_from_insights

st.title("😤 Comment Intelligence — Karen (Employee 7)")

if st.button("🔄 Run Karen Now (analyze latest comments)"):
    with st.spinner("Karen is reviewing comments..."):
        from db.sqlite_db import get_connection
        from mcp_servers.comments_server import analyze_comments
        conn = get_connection()
        unanalyzed = conn.execute(
            "SELECT DISTINCT post_url FROM comments WHERE analyzed_at IS NULL LIMIT 20"
        ).fetchall()
        urls = [row[0] for row in unanalyzed] or ["latest"]
        total = 0
        for url in urls:
            try:
                result = analyze_comments(url)
                total += result.get("analyzed", 0)
            except Exception as e:
                st.error(f"Error: {e}")
        st.success(f"Karen analyzed {total} comments.")
        st.cache_data.clear()

if st.button("🔍 Analyze New Comments"):
    st.info("Karen runs automatically at 3am. Ask Claude Code: 'analyze my latest comments'")

tab1, tab2 = st.tabs(["Pain Points", "Content Requests"])

with tab1:
    points = get_pain_points_from_insights(10)
    if points:
        for p in points:
            st.markdown(f"**{p['insight']}** — `{p['frequency']}` mentions")
            if p.get("example_comment"):
                st.caption(f'"{p["example_comment"]}"')
            st.markdown("---")
    else:
        st.info("No insights yet. Run research + comment analysis first.")

with tab2:
    from db.sqlite_db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT body FROM comments WHERE category='request' LIMIT 20"
    ).fetchall()
    if rows:
        for r in rows:
            st.markdown(f"- {r[0]}")
    else:
        st.info("No content requests captured yet.")
