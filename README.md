# 🌟 AI Chat & Web Crawler

A powerful AI chat platform with integrated web crawling and document processing capabilities. This interactive application allows you to chat with various AI models, crawl websites for information, upload documents, and ask questions about everything you gather.

## ✨ Features

### 🤖 AI Chat
- 💬 User-friendly chat interface with streaming responses
- 🆓 Access to free AI models through OpenRouter API
- 🌡️ Adjustable response parameters (temperature, max tokens)
- 📝 Custom system prompts to guide AI behavior
- 💾 Export chat history in JSON or text format

### 🕷️ Web Crawler
- 🔍 Crawl websites and extract meaningful content
- 🔄 Adjustable crawling depth and page limits
- 🔒 Security features to prevent unsafe URL crawling
- 📊 Progress tracking during crawling operations

### 📄 Document Processing
- 📁 Support for PDF, text, and markdown files
- 🧠 Extract and process content for AI context
- ⚡ Efficient handling of large documents with progress bars
- ✂️ Automatic content truncation for oversized files

### 🛠️ Developer Tools
- 🐞 Developer mode for debugging API interactions
- 📊 Response timing and token metrics
- 💻 Detailed error information and troubleshooting
- 📋 Export debug logs for analysis

## 🚀 Getting Started

### Prerequisites

Before you begin, make sure you have:
- 💻 Python 3.8 or higher installed
- 🔑 OpenRouter API key (get it from [OpenRouter](https://openrouter.ai/keys))
- 📦 pip package manager

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/Techy-47/ai-chat-web-crawler.git
   cd ai-chat-web-crawler
   ```

2. **Create a virtual environment**
   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate on Windows
   .\venv\Scripts\activate

   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the web interface**  
   Open your browser and navigate to http://localhost:8501

## 🎮 User Guide

### 🔑 Setting Up
1. Enter your OpenRouter API key in the sidebar configuration section
2. Select a free AI model from the dropdown menu
3. Optionally adjust system prompt, temperature, and response length

### 💬 Chatting with AI
1. Type your message in the chat input at the bottom
2. Watch as the AI generates a streaming response
3. Continue the conversation as long as you like
4. Clear chat history anytime using the button in the sidebar

### 🕸️ Crawling Websites
1. Go to the Web Crawler section in the sidebar
2. Enter a valid URL (e.g., "https://example.com")
3. Adjust crawling depth and maximum pages if needed
4. Click "Start Crawling" and watch the progress
5. Once complete, review the crawled content in expandable sections
6. Now you can ask the AI questions about the crawled content!

### 📑 Processing Documents
1. Navigate to the Document Upload section in the sidebar
2. Upload a PDF, text file, or markdown document
3. Wait for processing to complete
4. Ask questions about the document in the chat

### 🔧 Advanced Features
1. Enable Developer Mode in settings to see detailed API interactions
2. Adjust temperature for more creative (higher) or deterministic (lower) responses
3. Export your chat history as JSON or plain text
4. Download debug logs when troubleshooting issues

## 📚 Understanding Key Parameters

### System Prompt
This is your instruction set for the AI. Customize it to get responses in specific formats, tones, or with particular expertise.

### Temperature Setting
- 🧊 Low temperature (0.1-0.3): More predictable, factual responses
- 🌡️ Medium temperature (0.4-0.7): Balanced creativity and accuracy
- 🔥 High temperature (0.8-1.0): More creative, varied responses

### Max Response Length
Controls the maximum length of the AI's response in tokens (roughly words). Higher values allow for more detailed responses but may take longer to generate.

## 🔍 Tips for Best Results

- 📏 Start with specific URLs rather than very general domains
- 📉 For large websites, use lower depth values (1-2) to avoid long processing times
- 🔄 Clear crawled data when switching to a different topic
- 📝 For lengthy documents, consider splitting them into smaller files
- 🔍 Ask specific questions about content rather than vague queries
- 💡 Try different AI models for different types of questions

## 🛑 Troubleshooting

- **API Key Issues**: Make sure your OpenRouter API key is valid and has sufficient credits
- **Slow Crawling**: Reduce depth and maximum pages for faster results
- **PDF Processing Errors**: Some PDFs with complex formatting or security features may not process correctly
- **Response Generation Failures**: Try adjusting your prompt or switching models
- **Rate Limiting**: If you encounter rate limit errors, wait a few minutes before trying again

## 🧠 Technical Architecture

This application is built with:
- 🐍 Python for backend processing
- 🔄 Streamlit for the interactive web interface
- 🌐 aiohttp for asynchronous web requests
- 📄 PyPDF2 for PDF processing
- 🧩 BeautifulSoup for HTML parsing
- 🔄 SSE for streaming responses

### System Architecture

```
┌─────────────────┐     ┌───────────────┐     ┌─────────────────┐
│                 │     │               │     │                 │
│   Streamlit UI  │◄───►│  Application  │◄───►│  External APIs  │
│                 │     │    Logic      │     │                 │
└─────────────────┘     └───────────────┘     └─────────────────┘
                              ▲
                              │
                              ▼
                        ┌───────────────┐
                        │               │
                        │    Modules    │
                        │               │
                        └───────────────┘
                              ▲
                              │
                              ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│             │     │                 │     │                 │
│  File       │     │  Web Crawler    │     │  Chat           │
│  Processor  │     │                 │     │  Manager        │
│             │     │                 │     │                 │
└─────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Components:

1. **ChatAPI (`src/chat.py`)**: 
   - Handles all communication with the OpenRouter API
   - Implements token rate limiting (60 requests per minute)
   - Provides exponential backoff retry mechanism for API failures
   - Processes server-sent events (SSE) for streaming responses
   - Connection timeout handling and error recovery

2. **ChatManager (`src/chat.py`)**:
   - Manages conversation history with memory limitations
   - Maintains chat context within token limits
   - Implements a sliding window approach for long conversations
   - Handles message formatting and role assignment

3. **AsyncWebCrawler (`src/crawler.py`)**:
   - Uses asynchronous I/O for efficient parallel web requests
   - Implements breadth-first crawling algorithm
   - Follows same-domain policy for security
   - Contains rate limiting to prevent overloading target websites
   - Extracts useful content using BeautifulSoup selectors
   - Throttles requests with configurable chunk sizes

4. **URLValidator (`src/crawler.py`)**:
   - Validates URLs for security and format
   - Prevents access to localhost and internal networks
   - Enforces HTTPS/HTTP protocols only
   - Uses regex pattern matching for URL validation

5. **FileProcessor (`src/file_processor.py`)**:
   - Handles extraction of text from multiple document formats
   - Implements streaming for large PDF processing
   - Uses multiple encoding detection for text files
   - Contains size limits and pagination limits for resource management

### Data Flow

1. **User Input → Processing → AI Response**:
   ```
   User Input → ChatManager → Message Formatting → API Request → 
   Streaming Response → Content Display → History Update
   ```

2. **Web Crawling Pipeline**:
   ```
   URL Input → Validation → Async Requests → HTML Parsing → 
   Content Extraction → Storage → Context Formation
   ```

3. **Document Processing**:
   ```
   File Upload → Format Detection → Content Extraction → 
   Text Processing → Storage → Context Formation
   ```

### Implementation Details

#### Rate Limiting Implementation
```python
class RateLimiter:
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.timestamps: deque = deque(maxlen=max_requests)
        self.lock = Lock()
```
The rate limiter uses a thread-safe sliding window approach to track API calls within a time period, preventing API quota exhaustion.

#### Async Crawling with Concurrency Control
```python
async def breadth_first_crawl(self, start_url: str, session: aiohttp.ClientSession, 
                            progress_bar: Any, status: Any) -> None:
    queue = [(start_url, 0)]
    
    while queue and len(self.results) < self.max_pages:
        batch = queue[:self.chunk_size]
        queue = queue[self.chunk_size:]
        
        tasks = [self.process_page(url, depth, session, progress_bar, status) 
                for url, depth in batch]
        results = await asyncio.gather(*tasks)
```
The crawler processes URLs in batches for optimal parallelism while maintaining control over system resources.

#### SSE Streaming Response Handling
```python
def process_stream(self, response: requests.Response) -> Generator[str, None, None]:
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        if event.data == "[DONE]":
            break
            
        data = json.loads(event.data)
        if data.get('choices') and len(data['choices']) > 0:
            content = data['choices'][0].get('delta', {}).get('content', '')
            if content:
                yield content
```
Streaming responses are handled incrementally, providing real-time feedback while efficiently processing data chunks.

### Memory Management

1. **Chat History Memory Management**:
   - Implements token counting and truncation
   - Uses a sliding window approach to maintain recent context
   - Automatically removes oldest messages when memory limit reached

2. **Crawled Content Management**:
   - Content is stored with metadata for efficient retrieval
   - Large content is automatically truncated before storage
   - Chunk-based processing prevents memory spikes

3. **Streaming Response Handling**:
   - Incrementally processes and displays responses
   - Avoids loading full response into memory at once
   - Uses generators for memory-efficient streaming

### Security Considerations

1. **URL Validation and Sanitization**:
   - Prevents server-side request forgery (SSRF)
   - Blocks access to internal networks and localhost
   - Enforces protocol restrictions (HTTP/HTTPS only)
   - Uses regex pattern matching for validation

2. **API Key Management**:
   - Keys are stored only in session state
   - No persistent storage of credentials
   - Keys are transmitted only through encrypted channels

3. **Content Sanitization**:
   - HTML content is safely parsed and stripped
   - Document size limits prevent DOS attacks
   - Input validation on all user inputs

### Performance Optimizations

1. **Asynchronous Web Crawling**:
   - Parallel request processing improves crawling speed
   - Connection pooling reduces overhead
   - Configurable concurrency limits prevent resource exhaustion

2. **Lazy Loading and Pagination**:
   - Large documents are processed in chunks
   - Progress tracking for long-running operations
   - Cancellation support for ongoing operations

3. **Caching Mechanisms**:
   - Model data is cached to reduce API calls
   - Session state preserves user context
   - Metadata is separated from content for efficient handling

### API Integration

The application uses OpenRouter's API with the following endpoints:

1. **Models Endpoint**: `/api/v1/models`
   - Retrieves available models with metadata
   - Filters for free tier models
   - Extracts context window sizes and capabilities

2. **Chat Completions Endpoint**: `/api/v1/chat/completions`
   - Streaming mode enabled for real-time responses
   - Supports temperature and token length parameters
   - System prompts for context control
   - Message history formatting for conversation context

### Error Handling

1. **Graceful Degradation**:
   - API unavailability is handled with clear user messaging
   - Network timeouts implement exponential backoff
   - Invalid responses trigger friendly error messages

2. **Comprehensive Error Capture**:
   - Developer mode exposes detailed error information
   - Error logs can be exported for debugging
   - Structured error responses for systematic troubleshooting

## 🔒 Privacy & Security

- Your API key is stored only in your session and never persisted
- Crawled data is temporary and exists only during your session
- URL validation prevents crawling of local or potentially harmful addresses
- File size limits prevent processing of excessively large documents

## 📝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created with ❤️ using Python and Streamlit
