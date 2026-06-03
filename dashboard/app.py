"""Streamlit dashboard — Social Media Department HQ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import streamlit as st

st.set_page_config(
    page_title="Social Media Dept",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🎵 Social Media Dept")
st.sidebar.markdown("**12 AI Employees • All Local • All Free**")
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Core Dept (1–8)**
1. 💪 Chad — Research
2. 🎣 Peter — Hooks
3. 🤓 McLovin — Analytics
4. 💍 Gollum — Content
5. 🧘 Keanu — Creative
6. 🎧 Drake — A&R Scout
7. 😤 Karen — Comments
8. 🎉 Borat — Radar

**Strategy (9–12)**
9. 🎸 Rick — Swipe File
10. ⚡ Speed — Opinion Miner
11. 📋 Dwight — Strategy
12. 🧙 Gandalf — Learning
""")
st.sidebar.markdown("---")
st.sidebar.caption("Runs at 3am • Telegram reports • LAN accessible")

st.title("🎵 Social Media Department — Executive HQ")
st.markdown("Use the sidebar to access each employee's intelligence. The homepage shows Dwight's Daily Brief.")
