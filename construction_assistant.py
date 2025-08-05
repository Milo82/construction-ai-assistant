import streamlit as st
import openai
from datetime import datetime
import PyPDF2
import io

# Page config
st.set_page_config(
    page_title="Construction Assistant", 
    page_icon="🏗️",
    layout="wide"
)

# Title and description
st.title("🏗️ Construction Consulting Assistant")
st.markdown("Upload your project documents and ask specific questions")

# Sidebar for API key and file upload
with st.sidebar:
    st.header("Setup")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password")
    
    if api_key:
        openai.api_key = api_key
    
    st.markdown("---")
    
    # File upload
    st.header("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload project documents", 
        accept_multiple_files=True,
        type=['txt', 'pdf', 'md']
    )
    
    # Document processing
    documents_text = ""
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} files uploaded")
        
        for file in uploaded_files:
            try:
                if file.type == "application/pdf":
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                    file_text = ""
                    for page in pdf_reader.pages:
                        file_text += page.extract_text() + "\n"
                    documents_text += f"\n\n--- {file.name} ---\n{file_text}"
                    
                elif file.type == "text/plain":
                    file_text = file.read().decode('utf-8')
                    documents_text += f"\n\n--- {file.name} ---\n{file_text}"
                    
            except Exception as e:
                st.error(f"Error reading {file.name}: {str(e)}")
        
        # Store in session state
        st.session_state.documents = documents_text
        st.session_state.doc_count = len(uploaded_files)

# Main interface
if not api_key:
    st.warning("⚠️ Please enter your OpenAI API key in the sidebar")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your construction projects..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Get context from documents
                context = ""
                if hasattr(st.session_state, 'documents'):
                    context = st.session_state.documents
                    context_info = f"Based on {st.session_state.doc_count} uploaded documents"
                else:
                    context = "No documents uploaded yet."
                    context_info = "No documents available"
                
                messages = [
                    {"role": "system", "content": "You are a construction consulting assistant. Answer based on uploaded documents when available, citing specific files. Provide practical construction advice."},
                    {"role": "user", "content": f"Documents:\n{context}\n\nQuestion: {prompt}"}
                ]
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800
                )
                
                answer = response.choices[0].message.content
                st.markdown(answer)
                
                # Show cost
                usage = response.usage
                cost = (usage.prompt_tokens * 0.00015 + usage.completion_tokens * 0.0006) / 1000
                st.info(f"💰 Cost: ${cost:.4f} | 📄 {context_info}")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tips
if not hasattr(st.session_state, 'documents'):
    st.markdown("### 💡 Try uploading a PDF or text file first!")
