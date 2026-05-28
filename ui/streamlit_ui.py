import streamlit as st
import requests
import json
import time

# Configure backend API URL
API_BASE_URL = "http://localhost:8000"

# --- 1. Page Configuration & Aesthetic Theming ---
st.set_page_config(
    page_title="Ops Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection for a sleek, startup-style theme (Navy, Gold, Purple accents)
st.markdown("""
<style>
    /* Main background & font adjustments */
    .stApp {
        background-color: #0B132B;
        color: #E0E1DD;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling with gradient */
    h1 {
        background: -webkit-linear-gradient(45deg, #FFD700, #9D4EDD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1C2541;
        border-right: 1px solid #3A506B;
    }
    
    /* Input field styling */
    .stTextInput input, .stFileUploader > div {
        background-color: #0B132B !important;
        border: 1px solid #3A506B !important;
        color: white !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #9D4EDD;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #7B2CBF;
        border-color: #FFD700;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }
    
    /* Chat message containers */
    [data-testid="stChatMessage"] {
        background-color: rgba(28, 37, 65, 0.6);
        border-radius: 10px;
        border: 1px solid rgba(58, 80, 107, 0.4);
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# --- 2. Header Section ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Workspace Ops Copilot")
    st.markdown("*Multi-Agent Orchestration Engine*")
with col2:
    st.metric(label="System Status", value="Online", delta="Connected", delta_color="normal")
st.divider()

# --- 3. Sidebar: Knowledge Base Ingestion ---
with st.sidebar:
    st.subheader("📚 Knowledge Base")
    st.caption("Ingest documents to Pinecone")
    
    uploaded_file = st.file_uploader("Select PDF", type=["pdf"], label_visibility="collapsed")
    namespace = st.text_input("Namespace", value="workspace-docs")
    
    if st.button("Ingest to Vector Store", use_container_width=True):
        if uploaded_file and namespace:
            # Using a progress bar for a better aesthetic feel
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Chunking document...")
            progress_bar.progress(30)
            
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            data = {"namespace_name": namespace}
            
            status_text.text("Generating embeddings & Upserting...")
            progress_bar.progress(60)
            
            try:
                response = requests.post(f"{API_BASE_URL}/ingestion", files=files, data=data)
                progress_bar.progress(100)
                if response.status_code == 200:
                    status_text.empty()
                    st.success(f"✓ Ingested into `{namespace}`")
                else:
                    status_text.empty()
                    st.error(f"Failed: {response.text}")
            except Exception as e:
                status_text.empty()
                st.error(f"Error: {e}")
            
            time.sleep(2)
            progress_bar.empty()
        else:
            st.warning("Provide a PDF and namespace.")

    st.divider()
    st.markdown("<small>Built with LangGraph & FastAPI</small>", unsafe_allow_html=True)

# --- 4. Main Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Streaming Handler
if prompt := st.chat_input("Command the orchestrator..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # A more stylized status container
        status_container = st.status("Initializing routing protocol...", expanded=True)
        message_placeholder = st.empty()
        final_response = ""
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/query-agent",
                json={"query": prompt},
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        
                        try:
                            chunk = json.loads(data_str)
                            event_type = chunk.get("event")
                            event_data = chunk.get("data")
                            
                            if event_type == "agent calls":
                                # Added simulated delay for visual impact if processing is too fast
                                time.sleep(0.2)
                                status_container.write("⚙️ **Orchestrator**: Evaluating intent & selecting tools...")
                            
                            elif event_type == "knowledge base agent":
                                status_container.write("🔍 **KB Agent**: Querying Pinecone vector store...")
                            
                            elif event_type == "booking agent":
                                status_container.write("⚡ **Booking Agent**: Executing Supabase transaction...")
                                
                            elif event_type == "final response":
                                status_container.update(label="✓ Orchestration Complete", state="complete", expanded=False)
                                final_response = event_data
                                # Basic typing animation effect for the final output
                                displayed_text = ""
                                for char in final_response:
                                    displayed_text += char
                                    message_placeholder.markdown(displayed_text + "▌")
                                    time.sleep(0.01) # fast typing effect
                                message_placeholder.markdown(final_response)
                                
                        except json.JSONDecodeError:
                            pass
                            
        except requests.exceptions.RequestException as e:
            status_container.update(label="System Offline", state="error")
            st.error(f"Backend communication error: {e}")

    if final_response:
        st.session_state.messages.append({"role": "assistant", "content": final_response})
