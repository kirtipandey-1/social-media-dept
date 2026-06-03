import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_top_opportunities, get_latest_daily_brief, get_latest_report, get_recent_trends, get_employee_activity

st.title("🏠 Daily HQ — Dwight's Executive Brief")

col1, col2, col3, col4 = st.columns(4)
opps = get_top_opportunities(3)
trends = get_recent_trends(5)
activity = get_employee_activity(5)
with col1: st.metric("🎯 Active Opportunities", len(opps))
with col2: st.metric("📈 Trends Detected", len(trends))
with col3:
    brief = get_latest_daily_brief()
    st.metric("📋 Last Brief", brief["created_at"][:10] if brief else "None")
with col4: st.metric("🤖 Recent Actions", len(activity))

st.markdown("---")

col_a, col_b = st.columns([2,1])
with col_a:
    st.subheader("📋 Dwight's Daily Brief")
    brief = get_latest_daily_brief()
    if brief:
        st.caption(f"Generated: {brief['created_at']}")
        st.markdown(brief["body_md"])
    else:
        report = get_latest_report("daily")
        if report:
            st.caption(f"McLovin's report (no Dwight brief yet): {report['created_at']}")
            st.markdown(report["body_md"])
        else:
            st.info("No brief yet. Run the pipeline or go to Reports and click Generate.")
            if st.button("⚡ Run Pipeline Now", type="primary"):
                with st.spinner("Running full pipeline..."):
                    from orchestrator import run_pipeline
                    try:
                        run_pipeline(send_telegram=False)
                        st.cache_data.clear()
                        st.success("Pipeline complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

with col_b:
    st.subheader("🔥 Top Opportunities")
    if opps:
        for o in opps:
            st.markdown(f"**{o['title']}** — `{o['score']}`")
    else:
        st.info("No opportunities yet.")
    st.subheader("🤖 Activity Log")
    for a in activity[:5]:
        st.caption(f"**{a['employee']}** → {a['action']}")
