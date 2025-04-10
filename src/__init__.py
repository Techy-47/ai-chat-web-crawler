"""
AI Chat & Web Crawler Application
--------------------------------

This package contains the core modules for the AI chat and web crawler application:

- chat: Handles API communication and chat management
- crawler: Implements async web crawling functionality
- file_processor: Handles document processing and text extraction
"""

from .chat import ChatAPI, ChatManager
from .crawler import AsyncWebCrawler, URLValidator, CrawlResult
from .file_processor import FileProcessor

__version__ = "1.0.0"
__all__ = [
    'ChatAPI',
    'ChatManager',
    'AsyncWebCrawler',
    'URLValidator',
    'CrawlResult',
    'FileProcessor'
]