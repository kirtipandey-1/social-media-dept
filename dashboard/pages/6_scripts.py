import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_scripts

st.title("📝 Scripts — Gollum (Employee 4)")
st.caption("My precious scripts... stored safely in the database.")

col1, col2 = st.columns([3,1])
with col1:
    pain_point = st.text_input("Pain point", placeholder="my mix sounds bad in the car")
with col2:
    duration = st.selectbox("Length (sec)", [30, 60, 90], index=1)

if st.button("✍️ Write Script", type="primary"):
    if not pain_point:
        st.warning("Enter a pain point.")
    else:
        with st.spinner("Gollum is scripting... my precious..."):
            from mcp_servers.content_server import generate_script
            try:
                script = generate_script(pain_point, duration)
                st.success("Script generated!")
                st.markdown(f"**🪝 HOOK:** {script['hook']}")
                st.markdown(f"**😤 PROBLEM:** {script['problem']}")
                st.markdown(f"**💡 INSIGHT:** {script['insight']}")
                st.markdown(f"**📣 CTA:** {script['cta']}")
                st.code(f"HOOK: {script['hook']}\n\nPROBLEM: {script['problem']}\n\nINSIGHT: {script['insight']}\n\nCTA: {script['cta']}")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.subheader("📚 Saved Scripts")
for s in get_scripts(10):
    with st.expander(s.get("hook","")[:80] + "..."):
        st.markdown(f"**Pain point:** {s['pain_point']}")
        st.code(f"HOOK: {s['hook']}\n\nPROBLEM: {s['problem']}\n\nINSIGHT: {s['insight']}\n\nCTA: {s['cta']}")
