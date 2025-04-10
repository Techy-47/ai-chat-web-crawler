import streamlit as st
from dotenv import load_dotenv
import os
import base64
import datetime
import time
from src.crawler import AsyncWebCrawler, URLValidator
from src.chat import ChatAPI, ChatManager
from src.file_processor import FileProcessor
import json
import asyncio

# Load environment variables and configure Python to not create __pycache__ files
load_dotenv()
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SESSION_TIMEOUT = 3600  # 1 hour

# Initialize Streamlit page configuration
st.set_page_config(
    page_title="AI Chat & Web Crawler",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS styles
st.markdown("""
<style>
    /* Base styles */
    :root {
        --sidebar-width: 300px;
        --content-padding: 1rem;
    }
    
    /* Responsive container widths */
    @media (max-width: 640px) {
        .block-container {
            padding-top: 3rem !important;  /* Increased padding for mobile */
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        .stChatFloatingInputContainer {
            padding: 0.5rem !important;
        }
    }
    
    /* Chat container */
    .stChatFloatingInputContainer {
        padding: 10px;
        background-color: rgba(240, 242, 246, 0.05);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        margin: 0 auto;
        max-width: 1200px;
    }
    
    /* Message containers */
    .stChatMessage {
        background-color: rgba(240, 242, 246, 0.1) !important;
        border-radius: 15px !important;
        padding: clamp(0.5rem, 2vw, 1rem) !important;
        margin: 0.75rem 0 !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        padding: clamp(0.5rem, 2vw, 1rem) !important;
    }
    
    /* Improve text readability */
    div[data-testid="stMarkdownContainer"] > p {
        font-size: clamp(14px, 1.5vw, 16px) !important;
        line-height: 1.6 !important;
    }
    
    /* Style the chat input */
    .stChatInputContainer {
        padding-bottom: clamp(10px, 2vw, 20px) !important;
        padding-top: clamp(5px, 1vw, 10px) !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
    
    /* Title container styling */
    .title-container {
        margin-top: 4rem;  /* Increased margin for better spacing */
        margin-bottom: 1rem;
        text-align: center;
        padding-top: 2rem;  /* Added padding at the top */
    }
    
    /* Main title styling */
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        padding-top: 2rem !important;  /* Increased padding */
    }
    
    /* Welcome container adjustments */
    .welcome-container {
        text-align: center;
        padding: clamp(1.5rem, 3vw, 2.5rem);  /* Increased padding */
        max-width: 800px;
        margin: 1rem auto 2rem auto;  /* Adjusted margins */
    }
    
    .welcome-container h3 {
        font-size: clamp(1.5rem, 3vw, 2rem);
        margin-bottom: 0.75rem;
    }
    
    .welcome-container p {
        font-size: clamp(1rem, 2vw, 1.1rem);
        color: var(--text-color);
        opacity: 0.8;
    }
    
    /* Developer Mode Styling */
    .dev-info {
        border: 1px solid #f0ad4e;
        border-radius: 5px;
        background-color: rgba(240, 173, 78, 0.1);
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9rem !important;
        overflow-x: auto;
    }
    
    .dev-info pre {
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .dev-info-title {
        color: #f0ad4e;
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
    }
    
    .dev-info-title button {
        background: none;
        border: none;
        color: #f0ad4e;
        cursor: pointer;
        font-size: 0.8rem;
    }
    
    /* Adjust top spacing for mobile */
    @media (max-width: 640px) {
        .title-container {
            margin-top: 3rem;  /* Adjusted for mobile */
            padding-top: 1.5rem;  /* Adjusted for mobile */
        }
        
        .main-title {
            font-size: 2rem !important;
            padding-top: 1.5rem !important;  /* Adjusted for mobile */
        }
        
        .welcome-container {
            padding: 1rem;  /* Adjusted padding for mobile */
            margin-top: 1.5rem;  /* Added top margin for mobile */
        }
    }
    
    /* Responsive buttons */
    .stButton > button {
        padding: clamp(0.5rem, 1vw, 1rem) clamp(1rem, 2vw, 2rem) !important;
        font-size: clamp(0.875rem, 1.5vw, 1rem) !important;
    }
    
    /* Add some animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stChatMessage {
        animation: fadeIn 0.3s ease-out forwards;
    }
    
    /* Improve form field readability */
    .stTextInput > div > div > input {
        font-size: clamp(14px, 1.5vw, 16px) !important;
    }
    
    /* Make selectbox more mobile-friendly */
    .stSelectbox > div > div > select {
        font-size: clamp(14px, 1.5vw, 16px) !important;
        padding: clamp(0.25rem, 1vw, 0.5rem) !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "crawled_data" not in st.session_state:
    st.session_state.crawled_data = []
if "last_activity" not in st.session_state:
    st.session_state.last_activity = datetime.datetime.now().timestamp()
if "debug_info" not in st.session_state:
    st.session_state.debug_info = []
if "chat_manager_cleared" not in st.session_state:
    st.session_state.chat_manager_cleared = False

def check_session_timeout() -> bool:
    """Check if the session has timed out"""
    current_time = datetime.datetime.now().timestamp()
    if current_time - st.session_state.last_activity > SESSION_TIMEOUT:
        st.session_state.messages = []
        st.session_state.crawled_data = []
        st.session_state.last_activity = current_time
        st.session_state.chat_manager_cleared = True
        return True
    st.session_state.last_activity = current_time
    return False

def generate_download_link(content: str, filename: str, display_text: str) -> str:
    """Generate a download link for file content"""
    b64 = base64.b64encode(content.encode()).decode()
    ext = filename.split('.')[-1]
    mime_type = "application/json" if ext == "json" else "text/plain"
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{display_text}</a>'

def format_context_window(tokens: int) -> str:
    """Format context window size in a readable way"""
    if tokens >= 1000000:
        return f"{tokens/1000000:.1f}M tokens"
    elif tokens >= 1000:
        return f"{tokens/1000:.0f}K tokens"
    return f"{tokens} tokens"

def is_free_model(model: dict) -> bool:
    """Check if a model is free based on its ID"""
    return model.get('id', '').endswith(':free')

def format_model_name(model: dict) -> str:
    """Format model name for display"""
    try:
        model_name = model.get('id', '').split('/')[-1].replace(':free', '')
        return f"{model_name} 🆓"
    except Exception:
        return model.get('id', 'Unknown Model')

def add_debug_info(title: str, content: any, type_info: str = "info"):
    """Add debug information to the session state"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if isinstance(content, dict) or isinstance(content, list):
        formatted_content = json.dumps(content, indent=2)
    else:
        formatted_content = str(content)
    
    st.session_state.debug_info.append({
        "timestamp": timestamp,
        "title": title,
        "content": formatted_content,
        "type": type_info
    })

def clear_debug_info():
    """Clear debug information from the session state"""
    st.session_state.debug_info = []

def prepare_crawled_content() -> str:
    """Prepare crawled content for inclusion in the system prompt"""
    if not st.session_state.crawled_data:
        return ""
    
    content_parts = []
    total_chars = 0
    max_chars = 10000  # Limit total context to prevent token overflow
    
    content_parts.append("\n\n### REFERENCE CONTENT ###\n")
    content_parts.append("Use the following information to answer the user's questions:\n\n")
    
    for idx, item in enumerate(st.session_state.crawled_data):
        title = item.get('title', f"Document {idx+1}")
        url = item.get('url', 'No URL')
        content = item.get('content', '')
        
        # Calculate how many characters we can include from this document
        remaining_chars = max_chars - total_chars
        if remaining_chars <= 0:
            break
            
        # Truncate the content if needed
        excerpt = content[:min(len(content), remaining_chars)]
        total_chars += len(excerpt) + 100  # Add buffer for the formatting
        
        content_parts.append(f"--- {title} ---\n")
        if url != "uploaded_file":
            content_parts.append(f"Source: {url}\n")
        content_parts.append(f"{excerpt}\n\n")
    
    if total_chars >= max_chars:
        content_parts.append("(Note: Some content was truncated due to length limits)\n")
        
    return "".join(content_parts)

# Initialize API and managers
def get_api_and_managers(api_key: str):
    """Initialize API and managers without caching"""
    chat_api = ChatAPI(OPENROUTER_BASE_URL, api_key)
    chat_manager = ChatManager(chat_api)
    file_processor = FileProcessor()
    return chat_api, chat_manager, file_processor

# Sidebar configuration
with st.sidebar:
    st.title("🔑 Configuration")
    
    # API Key input
    saved_api_key = st.session_state.get('api_key', '')
    api_key_input = st.text_input(
        "Enter your OpenRouter API Key",
        value=saved_api_key,
        type="password",
        key="api_key_input",
        help="Get your API key from https://openrouter.ai/keys"
    )
    
    if st.button("🔑 Save API Key", key="enter_api_key", use_container_width=True):
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.sidebar.success("✅ API Key saved")
        else:
            st.sidebar.error("⚠️ Please enter an API key!")
    
    # Model selection
    api_key = st.session_state.get('api_key', '')
    if api_key:
        chat_api, _, _ = get_api_and_managers(api_key)
        models_data = chat_api.fetch_models()
        
        if "error" not in models_data:
            free_models = [model for model in models_data['data'] if is_free_model(model)]
            if free_models:
                model_options = {format_model_name(model): model['id'] for model in free_models}
                st.info("ℹ️ All shown models are completely FREE to use!")
                selected_model = st.selectbox(
                    "Select Free AI Model",
                    options=list(model_options.keys()),
                    key="selected_model"
                )
                
                if selected_model:
                    st.session_state.current_model = model_options[selected_model]
                    selected_model_data = next(
                        (model for model in free_models if model['id'] == st.session_state.current_model),
                        None
                    )
                    
                    if selected_model_data:
                        st.markdown("### Model Information")
                        st.markdown("#### Context Window")
                        context_window = format_context_window(selected_model_data.get('context_length', 0))
                        st.info(f"📝 {context_window}")
                        
                        if selected_model_data.get('description'):
                            st.markdown("#### Description")
                            st.info(f"ℹ️ {selected_model_data['description']}")
            else:
                st.warning("😔 No free models available at the moment. Please try again later.")
        else:
            st.error(f"❌ Error: {models_data['error']}")

# Settings section
st.sidebar.markdown("---")
st.sidebar.title("⚙️ Settings")

developer_mode = st.sidebar.checkbox(
    "Developer Mode",
    value=st.session_state.get("developer_mode", False),
    help="Show detailed error information and API interactions for debugging"
)
st.session_state.developer_mode = developer_mode

if developer_mode:
    if st.sidebar.button("🗑️ Clear Debug Info", key="clear_debug", use_container_width=True):
        clear_debug_info()
        st.rerun()

system_prompt = st.sidebar.text_area(
    "System Prompt (Optional)",
    value=st.session_state.get("system_prompt", "You are a helpful AI assistant."),
    help="Instructions for the AI model on how to behave"
)
st.session_state.system_prompt = system_prompt

temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.1,
    max_value=1.0,
    value=0.7,
    step=0.1,
    help="Higher values produce more creative responses, lower values are more deterministic"
)

max_tokens = st.sidebar.slider(
    "Max Response Length",
    min_value=500,
    max_value=4000,
    value=2000,
    step=500,
    help="Maximum number of tokens (words) in the response"
)

# Web crawler section
st.sidebar.markdown("---")
st.sidebar.title("🌐 Web Crawler")

url_input = st.sidebar.text_input("Enter URL to crawl", key="url_input")
depth = st.sidebar.slider("Crawling Depth", min_value=1, max_value=5, value=2)
st.sidebar.caption("How deep to explore website links")
max_pages = st.sidebar.slider("Maximum Pages", min_value=1, max_value=100, value=50)
st.sidebar.caption("Maximum number of pages to process")

if st.sidebar.button("Start Crawling", key="crawl_button", use_container_width=True):
    if not url_input:
        st.sidebar.warning("⚠️ Please enter a URL to crawl")
    else:
        if not url_input.startswith(('http://', 'https://')):
            url_input = 'https://' + url_input
        
        is_valid, message = URLValidator.validate(url_input)
        if not is_valid:
            st.sidebar.error(f"❌ {message}")
        else:
            if depth > 3 and max_pages > 50:
                st.sidebar.warning("⚠️ High depth and page count may take a long time to process")
            
            with st.spinner(f"Crawling {url_input}..."):
                try:
                    if st.session_state.developer_mode:
                        add_debug_info("Crawler Configuration", {
                            "url": url_input,
                            "depth": depth,
                            "max_pages": max_pages
                        })
                    
                    crawler = AsyncWebCrawler(max_depth=depth, max_pages=max_pages)
                    with st.status("🌐 Crawling website...", expanded=True) as status:
                        status.write("🔍 Starting crawler...")
                        results = asyncio.run(crawler.crawl(url_input, status))
                    
                    if not results:
                        st.sidebar.warning("⚠️ No content found on this website.")
                    else:
                        st.session_state.crawled_data = [
                            {
                                'url': result.url,
                                'title': result.title,
                                'content': result.content,
                                'status_code': result.status_code
                            } for result in results
                        ]
                        st.sidebar.success(f"✅ Found {len(results)} pages")
                        
                        if st.session_state.developer_mode:
                            add_debug_info("Crawl Results Summary", {
                                "pages_found": len(results),
                                "urls": [result.url for result in results],
                                "total_content_size": sum(len(result.content) for result in results)
                            })
                        
                        # Display results
                        st.subheader("📄 Crawled Pages")
                        for result in st.session_state.crawled_data:
                            with st.expander(f"📄 {result['title'][:50]}..."):
                                st.write(f"URL: {result['url']}")
                                st.write(f"Content Length: {len(result['content'])} characters")
                                st.write("First 200 characters of content:")
                                st.text(result['content'][:200] + "...")

                        if st.session_state.crawled_data:
                            st.info("💡 You can now ask questions about the crawled content!")
                except Exception as e:
                    st.sidebar.error(f"❌ Crawling error: {str(e)}")
                    if st.session_state.developer_mode:
                        add_debug_info("Crawler Error", str(e), "error")
                        st.sidebar.code(str(e))

# File upload section
st.sidebar.markdown("---")
st.sidebar.title("📄 Document Upload")
uploaded_file = st.sidebar.file_uploader("Upload a text document", type=["txt", "md", "pdf"])

if uploaded_file is not None:
    _, _, file_processor = get_api_and_managers(st.session_state.get('api_key', ''))
    try:
        if st.session_state.developer_mode:
            add_debug_info("File Upload", {
                "filename": uploaded_file.name,
                "type": uploaded_file.type,
                "size": uploaded_file.size
            })
            
        if uploaded_file.name.endswith('.pdf'):
            text_content, error = file_processor.process_pdf(uploaded_file)
        else:
            text_content, error = file_processor.process_text_file(uploaded_file)
            
        if error:
            st.sidebar.error(f"❌ {error}")
            if st.session_state.developer_mode:
                add_debug_info("File Processing Error", error, "error")
        elif text_content:
            st.session_state.crawled_data.append({
                'url': "uploaded_file",
                'title': uploaded_file.name,
                'content': text_content[:1000000]  # Limit to ~1MB
            })
            st.sidebar.success(f"✅ Successfully processed: {uploaded_file.name}")
            st.sidebar.info("💡 You can now ask questions about the uploaded document!")
            
            if st.session_state.developer_mode:
                add_debug_info("File Processing Success", {
                    "filename": uploaded_file.name,
                    "content_length": len(text_content),
                    "truncated": len(text_content) > 1000000
                })
    except Exception as e:
        st.sidebar.error(f"❌ Error processing file: {str(e)}")
        if st.session_state.developer_mode:
            add_debug_info("File Processing Exception", str(e), "error")
            st.sidebar.code(str(e))

# Main chat interface
st.markdown("""
<div class="title-container">
    <h1 class="main-title">💬 AI Chat</h1>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="welcome-container">
        <h3>Welcome to AI Chat! 🚀</h3>
        <p>Chat with powerful AI models - completely free!</p>
    </div>
    """, unsafe_allow_html=True)

# Display status indicator for crawled data
if st.session_state.crawled_data:
    data_count = len(st.session_state.crawled_data)
    if data_count == 1:
        st.success(f"✅ 1 document loaded and ready for questions")
    else:
        st.success(f"✅ {data_count} documents loaded and ready for questions")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Display developer info if developer mode is enabled
if st.session_state.developer_mode and st.session_state.debug_info:
    st.markdown("## 🛠️ Developer Information")
    for idx, debug_item in enumerate(st.session_state.debug_info):
        with st.expander(f"[{debug_item['timestamp']}] {debug_item['title']}"):
            st.code(debug_item["content"], language="json")

# Chat input and response handling
if prompt := st.chat_input("What would you like to know?", key="chat_input"):
    if check_session_timeout():
        st.warning("⚠️ Your session has timed out. Starting a new session.")
        time.sleep(2)
        st.rerun()
        
    if not st.session_state.get('api_key'):
        st.error("⚠️ Please enter your OpenRouter API key in the sidebar first!")
    elif "current_model" not in st.session_state:
        st.error("⚠️ Please select a model from the sidebar first!")
    else:
        # Skip empty prompts
        if not prompt.strip():
            st.error("⚠️ Cannot send an empty message.")
        else:
            # Get API and chat manager 
            chat_api, chat_manager, _ = get_api_and_managers(st.session_state.api_key)
            
            # Add user message to session state messages
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # If chat history was cleared, also clear the chat manager's messages
            if st.session_state.chat_manager_cleared:
                chat_manager.clear_history()
                st.session_state.chat_manager_cleared = False
                # Add the current message to the chat manager since it's been cleared
                chat_manager.add_message("user", prompt)
            else:
                # Synchronize chat manager with session state if needed
                if len(chat_manager.messages) != len(st.session_state.messages) - 1:  # -1 because we just added a message
                    chat_manager.messages = st.session_state.messages[:-1].copy()
                    chat_manager.add_message("user", prompt)
                else:
                    # Just add the new message to chat manager
                    chat_manager.add_message("user", prompt)
                    
            try:
                # Display the user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    with st.status("🤔 Thinking...", expanded=True) as status:
                        # Add system prompt if provided, and include crawled content
                        base_system_prompt = st.session_state.system_prompt
                        crawled_content = prepare_crawled_content()
                        
                        # Create the enhanced system prompt with crawled content
                        enhanced_system_prompt = base_system_prompt
                        if crawled_content:
                            enhanced_system_prompt = f"{base_system_prompt}\n{crawled_content}"
                            if st.session_state.developer_mode:
                                add_debug_info("Enhanced System Prompt", {
                                    "base_prompt": base_system_prompt,
                                    "added_content_length": len(crawled_content),
                                    "total_length": len(enhanced_system_prompt)
                                })
                        
                        # Prepare messages for sending to API
                        messages_to_send = chat_manager.get_messages().copy()
                        
                        # Debug: Check messages exist
                        if st.session_state.developer_mode:
                            add_debug_info("Chat Manager Messages Count", {
                                "count": len(chat_manager.messages),
                                "messages": [{"role": msg["role"], "content_preview": msg["content"][:30] + "..."} 
                                            for msg in chat_manager.messages]
                            })
                        
                        # Make sure we have messages to send - this should not happen now
                        if not messages_to_send or len(messages_to_send) == 0:
                            message_placeholder.error("❌ Error: No messages to send to the API.")
                            if st.session_state.developer_mode:
                                add_debug_info("Message Error", "No messages to send to the API", "error") 
                            st.session_state.messages.pop()
                        else:
                            # Insert system prompt at the beginning if it exists
                            if enhanced_system_prompt:
                                messages_to_send.insert(0, {
                                    "role": "system",
                                    "content": enhanced_system_prompt
                                })
                            
                            # Log request details in developer mode
                            if st.session_state.developer_mode:
                                request_payload = {
                                    "model": st.session_state.current_model,
                                    "temperature": temperature,
                                    "max_tokens": max_tokens,
                                    "stream": True,
                                    "message_count": len(messages_to_send),
                                    "includes_crawled_data": bool(crawled_content),
                                    "system_prompt_length": len(enhanced_system_prompt) if enhanced_system_prompt else 0
                                }
                                add_debug_info("API Request", request_payload)
                                
                                # Also log actual messages being sent in debug mode
                                if messages_to_send:
                                    message_summary = []
                                    for msg in messages_to_send:
                                        # Truncate long content for readability
                                        content = msg.get('content', '')
                                        if len(content) > 500:
                                            content = content[:500] + "... [truncated]"
                                        message_summary.append({
                                            "role": msg.get('role'),
                                            "content_length": len(msg.get('content', '')),
                                            "content_preview": content
                                        })
                                    add_debug_info("Messages Being Sent", message_summary)
                            
                            # Make the actual request
                            response = chat_api.make_request(
                                messages=messages_to_send,
                                model=st.session_state.current_model,
                                temperature=temperature,
                                max_tokens=max_tokens
                            )
                            
                            # Log response metadata in developer mode
                            if st.session_state.developer_mode:
                                response_meta = {
                                    "status_code": response.status_code,
                                    "headers": dict(response.headers),
                                    "elapsed": str(response.elapsed)
                                }
                                add_debug_info("API Response Metadata", response_meta)
                            
                            if response.status_code == 200:
                                status.update(label="💭 Generating response...")
                                
                                # Process the streaming response
                                token_count = 0
                                start_time = time.time()
                                
                                for content in chat_api.process_stream(response):
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                                    token_count += 1
                                    
                                    # Update developer stats periodically
                                    if st.session_state.developer_mode and token_count % 10 == 0:
                                        elapsed = time.time() - start_time
                                        tokens_per_second = token_count / elapsed if elapsed > 0 else 0
                                        status.write(f"📊 Received {token_count} tokens at {tokens_per_second:.1f} tokens/sec")
                                
                                message_placeholder.markdown(full_response)
                                status.update(label="✨ Done!", state="complete")
                                
                                # Log final response stats in developer mode
                                if st.session_state.developer_mode:
                                    final_elapsed = time.time() - start_time
                                    final_tokens_per_second = token_count / final_elapsed if final_elapsed > 0 else 0
                                    
                                    add_debug_info("Generation Stats", {
                                        "total_tokens": token_count,
                                        "generation_time": f"{final_elapsed:.2f} seconds",
                                        "tokens_per_second": f"{final_tokens_per_second:.1f}",
                                        "response_size": f"{len(full_response)} characters"
                                    })
                                
                                # Only add to history if we actually got a response
                                if full_response:
                                    chat_manager.add_message("assistant", full_response)
                                    st.session_state.messages = chat_manager.get_messages().copy()
                                else:
                                    message_placeholder.error("❌ Received empty response from API.")
                                    st.session_state.messages.pop()
                                
                            elif response.status_code == 401:
                                message_placeholder.error("❌ Authentication error: Invalid API key.")
                                if st.session_state.developer_mode:
                                    add_debug_info("API Error", "Authentication error: Invalid API key", "error")
                                st.session_state.messages.pop()
                            elif response.status_code == 400:
                                # Handle 400 Bad Request errors specifically
                                error_text = response.text
                                try:
                                    error_json = response.json()
                                    if "error" in error_json and "message" in error_json["error"]:
                                        error_text = error_json["error"]["message"]
                                except:
                                    pass
                                
                                message_placeholder.error(f"❌ Bad Request: {error_text}")
                                if st.session_state.developer_mode:
                                    add_debug_info("API Error", f"Bad Request: {error_text}", "error")
                                st.session_state.messages.pop()
                            else:
                                message_placeholder.error(f"❌ Error: {response.text}")
                                if st.session_state.developer_mode:
                                    add_debug_info("API Error", response.text, "error")
                                st.session_state.messages.pop()
                        
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.session_state.developer_mode:
                    add_debug_info("Exception", str(e), "error")
                    import traceback
                    add_debug_info("Exception Traceback", traceback.format_exc(), "error")
                if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

# Clear and export buttons
st.sidebar.markdown("---")
if st.session_state.crawled_data:
    if st.sidebar.button("🗑️ Clear Crawled Data", key="clear_data", use_container_width=True):
        st.session_state.crawled_data = []
        st.rerun()

    st.sidebar.markdown("""
    ### How to Use Crawled Data
    1. After crawling a website, the content is stored automatically
    2. Simply ask questions in the chat like:
        - "What is this website about?"
        - "Summarize the main topics"
        - "What did you find about [specific topic]?"
    3. The AI will use the crawled content to answer your questions
    """)

if st.session_state.messages:
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat History", key="clear_chat", use_container_width=True):
        st.session_state.messages = []
        
        # Mark that chat history was cleared so we can clear the ChatManager too
        st.session_state.chat_manager_cleared = True
        
        if st.session_state.developer_mode:
            add_debug_info("Chat History", "Chat history cleared", "info")
            
        st.rerun()

    st.sidebar.markdown("### 💾 Export Chat History")
    
    # JSON export
    json_data = json.dumps(st.session_state.messages, indent=2)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"chat_session_{timestamp}.json"
    json_link = generate_download_link(json_data, json_filename, "Download as JSON")
    st.sidebar.markdown(json_link, unsafe_allow_html=True)
    
    # Text export
    text_content = f"Chat Session\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "AI"
        text_content += f"{role}: {msg['content']}\n\n"
    
    text_filename = f"chat_session_{timestamp}.txt"
    text_link = generate_download_link(text_content, text_filename, "Download as Text")
    st.sidebar.markdown(text_link, unsafe_allow_html=True)

# Export debug info (only shown in developer mode)
if st.session_state.developer_mode and st.session_state.debug_info:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Export Debug Info")
    
    debug_json = json.dumps(st.session_state.debug_info, indent=2)
    debug_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_filename = f"debug_info_{debug_timestamp}.json"
    debug_link = generate_download_link(debug_json, debug_filename, "Download Debug Log")
    st.sidebar.markdown(debug_link, unsafe_allow_html=True)
