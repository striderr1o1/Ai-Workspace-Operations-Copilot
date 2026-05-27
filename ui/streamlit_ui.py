import streamlit as st
import requests
import json

# Configure backend API URL
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Workspace Operations Copilot",
    page_icon="🤖",
    layout="wide"
)

st.title("AI Workspace Operations Copilot")
st.markdown("Multi-Agent Orchestration Interface")

# ---------------------------------------------------------
# Sidebar: Knowledge Base Ingestion
# ---------------------------------------------------------
with st.sidebar:
    st.header("Document Ingestion")
    st.markdown("Upload PDFs to Pinecone for the KB Agent.")
    
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    namespace = st.text_input("Pinecone Namespace", value="workspace-docs")
    
    if st.button("Ingest Document"):
        if uploaded_file and namespace:
            with st.spinner("Chunking and generating embeddings..."):
                # Prepare multipart form-data
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
                }
                data = {
                    "namespace_name": namespace
                }
                
                try:
                    response = requests.post(f"{API_BASE_URL}/ingestion", files=files, data=data)
                    if response.status_code == 200:
                        st.success(f"Successfully ingested into `{namespace}`!")
                    else:
                        st.error(f"Ingestion failed: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please provide both a PDF file and a namespace.")

# ---------------------------------------------------------
# Main Chat Interface: SSE Streaming
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Streaming Handler

if prompt := st.chat_input("Ask the orchestrator (e.g., 'What rooms are available today?'):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Use a status container to visualize the LangGraph node routing
        status_container = st.status("Agents orchestrating...", expanded=True)
        message_placeholder = st.empty()
        final_response = ""
        
        try:
            # 1. Update the endpoint to /query-agent
            # 2. Ensure the payload matches your 'inference' model ({"query": string})
            response = requests.post(
                f"{API_BASE_URL}/query-agent",
                json={"query": prompt},
                stream=True
            )
            response.raise_for_status()
            
            # Iterate over the SSE stream
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        
                        try:
                            # Parse your custom LangGraph JSON structure
                            chunk = json.loads(data_str)
                            event_type = chunk.get("event")
                            event_data = chunk.get("data")
                            
                            # Render UI updates based on which node is active
                            if event_type == "agent calls":
                                status_container.write(f"🧠 **Orchestrator** evaluating tools...")
                            
                            elif event_type == "knowledge base agent":
                                status_container.write("📚 **Knowledge Base Agent** searching Pinecone...")
                            
                            elif event_type == "booking agent":
                                status_container.write("📅 **Booking Agent** querying Supabase...")
                                
                            elif event_type == "final response":
                                # When the return_to_user_decision triggers, render the actual string
                                status_container.update(label="Orchestration Complete!", state="complete", expanded=False)
                                final_response = event_data
                                message_placeholder.markdown(final_response)
                                
                        except json.JSONDecodeError:
                            # Ignore incomplete chunks or malformed JSON
                            pass
                            
        except requests.exceptions.RequestException as e:
            status_container.update(label="Connection Failed", state="error")
            st.error(f"Backend communication error: {e}")

    if final_response:
        st.session_state.messages.append({"role": "assistant", "content": final_response})
