import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st
from dashboard.db_helpers import get_suggested_topics

st.title("🪝 Hooks — Peter (Employee 2)")

# Suggested topics from research
try:
    suggestions = get_suggested_topics(limit=8)
except Exception:
    suggestions = []
selected_suggestion = None
if suggestions:
    st.markdown("**💡 Suggested topics from Chad's research:**")
    cols = st.columns(min(len(suggestions), 4))
    for i, sug in enumerate(suggestions[:8]):
        with cols[i % 4]:
            if st.button(sug[:35], key=f"sug_{i}", use_container_width=True):
                selected_suggestion = sug

col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("Topic",
                          value=selected_suggestion if selected_suggestion else "",
                          placeholder="e.g. 808 bass, mixing tips, beat drop")
with col2:
    count = st.slider("Count", 5, 50, 25)

import os as _os
_is_cloud = _os.environ.get("HOME", "").startswith("/home/")
if _is_cloud:
    st.info("⚠️ Hook generation requires Ollama on your Mac. Browse saved hooks below.")

if not _is_cloud and st.button("⚡ Generate Hooks", type="primary"):
    if not topic:
        st.warning("Enter a topic first.")
    else:
        with st.spinner(f"Peter generating {count} hooks about '{topic}'..."):
            from mcp_servers.hooks_server import generate_hooks
            try:
                hooks = generate_hooks(topic, count)
                st.success(f"Generated {len(hooks)} hooks!")
                for h in hooks:
                    c1, c2 = st.columns([5, 1])
                    c1.write(h)
                    if c2.button("📋", key=f"cp_{h[:15]}"):
                        st.code(h)
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.subheader("🔍 Search Hook Database")
query = st.text_input("Search hooks", placeholder="mixing bass, hook ideas...")
if query:
    from mcp_servers.hooks_server import search_hooks_fn
    results = search_hooks_fn(query, limit=10)
    for r in results:
        st.markdown(f"- **{r['document']}** _{r['metadata'].get('category','')}_")

st.markdown("---")
st.subheader("📊 Hook Clusters")
if st.button("Analyze Patterns"):
    from mcp_servers.hooks_server import cluster_hooks
    st.markdown(cluster_hooks())
