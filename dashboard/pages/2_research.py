import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_competitor_posts, get_recent_reddit, get_recent_trends

st.title("🔍 Research — Chad (Employee 1)")

if st.button("🔄 Run Research Now"):
    with st.spinner("Chad is scraping... (may take 2-3 mins)"):
        from workers.research_scraper import ResearchScraper
        try:
            result = ResearchScraper().execute()
            st.success(f"Done: {result}")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Error: {e}")

tab1, tab2, tab3 = st.tabs(["Competitor Feed", "Reddit Intel", "Trends"])

with tab1:
    posts = get_competitor_posts(30)
    if posts:
        for p in posts:
            label = f"@{p['handle']} — {p['views'] or 0:,} views"
            with st.expander(label):
                col_img, col_text = st.columns([1, 2])
                with col_img:
                    if p.get("thumbnail_url"):
                        st.image(p["thumbnail_url"], use_container_width=True)
                    else:
                        st.caption("No thumbnail")
                with col_text:
                    st.write(p.get("caption", "")[:300])
                    if p.get("ai_analysis"):
                        st.markdown("**🤖 Why it's working:**")
                        st.info(p["ai_analysis"])
                    st.caption(f"Scraped: {p.get('scraped_at','')}")
    else:
        st.info("No competitor data yet. Click 'Run Research Now'.")

with tab2:
    posts = get_recent_reddit(30)
    if posts:
        for p in posts:
            upvotes = p.get('upvotes', 0)
            badge = "🔥" if upvotes > 500 else ("⬆️" if upvotes > 100 else "")
            st.markdown(f"**r/{p['subreddit']}** {badge} · **{upvotes:,} upvotes**")
            st.write(p["title"])
            if p.get("url"):
                st.caption(p["url"])
            st.markdown("---")
    else:
        st.info("No Reddit data yet. Click 'Run Research Now'.")

with tab3:
    trends = get_recent_trends(20)
    if trends:
        import pandas as pd
        st.dataframe(pd.DataFrame(trends), use_container_width=True)
    else:
        st.info("No trends detected yet.")
