import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_post_performance

st.title("📊 Analytics — McLovin (Employee 3)")

tab_sync, tab_view = st.tabs(["📥 Sync Data", "📊 Performance"])

with tab_sync:
    st.markdown("""
**How to sync:** Open Instagram/YouTube/Facebook Insights, copy the stats text, paste below.
    """)
    platform = st.selectbox("Platform", ["instagram", "youtube", "facebook"])
    post_url = st.text_input("Post URL (optional)", placeholder="https://instagram.com/p/...")
    raw_text = st.text_area("Paste insights text here", height=150,
                            placeholder="Views 12,345\nLikes 890\nSaves 234\nComments 56")
    if st.button("💾 Save to Database", type="primary"):
        if raw_text.strip():
            from workers.analytics_ingest import parse_insights_text
            from db.duckdb_db import get_connection as dq, init_schema, upsert_post_performance
            metrics = parse_insights_text(raw_text)
            conn = dq()
            init_schema(conn)
            record = {
                "post_url": post_url.strip() or f"manual_{platform}_{metrics.get('views',0)}",
                "platform": platform,
                **metrics,
            }
            upsert_post_performance(conn, record)
            st.success(
                f"Saved! Views: {metrics.get('views',0):,} · "
                f"Likes: {metrics.get('likes',0):,} · "
                f"Saves: {metrics.get('saves',0):,}"
            )
            st.cache_data.clear()
        else:
            st.warning("Paste some insights text first.")

with tab_view:
    perf = get_post_performance(20)
    if perf:
        import pandas as pd
        df = pd.DataFrame(perf)
        st.subheader("Post Performance")
        display_cols = [c for c in ["posted_at","platform","views","likes","saves","comments"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        if "views" in df.columns and len(df) > 1:
            try:
                st.subheader("Views Over Time")
                chart_df = df.set_index("posted_at")["views"]
                st.line_chart(chart_df)
            except Exception:
                pass
    else:
        st.info("No analytics data yet. Use the Sync tab to add data.")
