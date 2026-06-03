import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.title("🧙 Taste & Performance — Gandalf (Employee 12)")
st.caption("You shall not drop a bad hook.")

tab1, tab2, tab3 = st.tabs(["Analytics Chart", "Swipe Patterns", "Hook Performance"])

with tab1:
    if st.button("🔄 Regenerate Master Analytics Graphic"):
        with st.spinner("Gandalf is weaving the analytics..."):
            try:
                from dashboard.utils.charts import generate_global_analytics_graphic
                fig = generate_global_analytics_graphic()
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Chart error: {e}")
    else:
        try:
            from dashboard.utils.charts import generate_global_analytics_graphic
            fig = generate_global_analytics_graphic()
            st.pyplot(fig)
        except Exception as e:
            st.info("No analytics data yet. Sync from Instagram/YouTube first.")

with tab2:
    from dashboard.db_helpers import get_swipe_file
    swipes = get_swipe_file(50)
    if swipes:
        formats = {}
        for s in swipes:
            f = s.get("content_format","unknown")
            formats[f] = formats.get(f,0) + 1
        import pandas as pd
        st.subheader("Content Format Breakdown")
        st.bar_chart(pd.Series(formats))
    else:
        st.info("Swipe file empty — Rick needs to run first.")

with tab3:
    from db.sqlite_db import get_connection
    conn = get_connection()
    rows = conn.execute("""
    SELECT hook_text, platform, views, saves, engagement_rate
    FROM hook_performance ORDER BY views DESC LIMIT 10
    """).fetchall()
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows, columns=["Hook","Platform","Views","Saves","Engagement"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hook performance data yet.")
