import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import streamlit as st

st.title("🪝 Hooks — Peter (Employee 2)")

col1, col2 = st.columns([3,1])
with col1:
    topic = st.text_input("Topic", placeholder="e.g. 808 bass, mixing tips, beat drop")
with col2:
    count = st.slider("Count", 5, 50, 25)

if st.button("⚡ Generate Hooks", type="primary"):
    if not topic:
        st.warning("Enter a topic first.")
    else:
        with st.spinner(f"Peter generating {count} hooks about '{topic}'..."):
            from mcp_servers.hooks_server import generate_hooks
            try:
                hooks = generate_hooks(topic, count)
                st.success(f"Generated {len(hooks)} hooks!")
                for h in hooks:
                    c1, c2 = st.columns([5,1])
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
