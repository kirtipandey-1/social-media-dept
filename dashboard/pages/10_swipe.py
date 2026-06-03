import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_swipe_file

st.title("🎸 Swipe File — Rick (Employee 9)")
st.caption("Never gonna give up a good reference. Never gonna let it drop.")

if st.button("🔄 Analyze Saved Collections (Browser Engine)"):
    st.info("Rick uses the browser engine. Run: 'from mcp_servers.browser_mcp import crawl_saved_collections' in Claude Code.")

st.markdown("---")
swipes = get_swipe_file(20)
if swipes:
    for s in swipes:
        label = s.get("hook_text") or s.get("topic") or s.get("source_url","")
        with st.expander(f"⭐ {s.get('personal_rating',0)}/5 — {label[:60]}"):
            cols = st.columns(3)
            cols[0].metric("Platform", s.get("platform","?"))
            cols[1].metric("Format", s.get("content_format","?"))
            cols[2].metric("Trigger", s.get("emotional_trigger","?"))
            if s.get("notes"): st.write(s["notes"])
            if s.get("source_url"): st.caption(s["source_url"])
else:
    st.info("Swipe file is empty. Rick will populate it when the browser engine runs.")
