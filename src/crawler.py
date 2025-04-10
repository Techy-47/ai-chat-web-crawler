from typing import List, Dict, Optional, Any
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from dataclasses import dataclass
import streamlit as st

@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    status_code: int

class URLValidator:
    @staticmethod
    def validate(url: str) -> tuple[bool, str]:
        """Enhanced URL validation with security checks"""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False, "Invalid URL format"
            
            if result.scheme not in ['http', 'https']:
                return False, "Only HTTP(S) protocols are allowed"
            
            netloc = result.netloc.lower()
            if any(x in netloc for x in ['localhost', '127.0.0.1', '0.0.0.0']):
                return False, "Local addresses are not allowed"
                
            url_pattern = re.compile(
                r'^https?:\/\/'
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
                r'localhost|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                r'(?::\d+)?'
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                return False, "URL format is invalid"
                
            return True, "URL is valid"
        except Exception as e:
            return False, f"URL validation error: {str(e)}"

class AsyncWebCrawler:
    def __init__(self, max_depth: int = 2, max_pages: int = 50, chunk_size: int = 20):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.chunk_size = chunk_size
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
        self.visited: set[str] = set()
        self.results: List[CrawlResult] = []
        self.processed = 0
        self.queue: List[Dict[str, Any]] = []  # URL queue with depth information

    async def crawl_page(self, url: str, session: aiohttp.ClientSession, timeout: int = 30) -> Dict[str, Any]:
        """Crawl a single page asynchronously"""
        try:
            async with session.get(url, headers={'User-Agent': self.user_agent}, timeout=timeout) as response:
                return {
                    'status_code': response.status,
                    'content': await response.text() if response.status == 200 else None
                }
        except Exception as e:
            return {'status_code': 0, 'error': str(e), 'content': None}

    def update_progress(self, progress_bar: Any, status: Any) -> None:
        """Update the progress bar and status message"""
        self.processed += 1
        progress = min(1.0, self.processed / self.max_pages)
        progress_bar.progress(progress)
        status.write(f"Processed {self.processed}/{self.max_pages} pages. Found {len(self.results)} pages with content.")
        if progress >= 1.0:
            time.sleep(0.5)
            progress_bar.empty()

    async def process_page(self, url: str, depth: int, session: aiohttp.ClientSession, 
                         progress_bar: Any, status: Any) -> List:
        """Process a single page and return any new URLs found"""
        if url in self.visited or len(self.results) >= self.max_pages:
            return []
            
        self.visited.add(url)
        status.write(f"Processing: {url} (depth: {depth})")
        
        response_data = await self.crawl_page(url, session)
        new_urls = []
        
        if response_data['status_code'] == 200 and response_data['content']:
            soup = BeautifulSoup(response_data['content'], 'html.parser')
            content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section'])
            content = ' '.join([elem.get_text().strip() for elem in content_elements])
            title = soup.title.string if soup.title else url.split('/')[-1]
            
            if content.strip():
                self.results.append(CrawlResult(
                    url=url,
                    title=title,
                    content=content[:500000],  # Limit content size
                    status_code=response_data['status_code']
                ))
                
                # Update progress after processing each page with content
                self.update_progress(progress_bar, status)
            
            # If we haven't reached max depth and still need more pages, collect links
            if depth < self.max_depth and len(self.results) < self.max_pages:
                links = soup.find_all('a', href=True)
                base_domain = urlparse(url).netloc
                for link in links:
                    full_url = urljoin(url, link['href'])
                    # Only follow links within the same domain
                    if urlparse(full_url).netloc == base_domain and full_url not in self.visited:
                        new_urls.append((full_url, depth + 1))
                        
        return new_urls

    async def breadth_first_crawl(self, start_url: str, session: aiohttp.ClientSession, 
                                progress_bar: Any, status: Any) -> None:
        """Crawl the website using a breadth-first approach"""
        # Initialize queue with the starting URL at depth 0
        queue = [(start_url, 0)]
        
        while queue and len(self.results) < self.max_pages:
            # Process a batch of URLs concurrently
            batch = queue[:self.chunk_size]
            queue = queue[self.chunk_size:]
            
            tasks = [self.process_page(url, depth, session, progress_bar, status) 
                    for url, depth in batch]
            results = await asyncio.gather(*tasks)
            
            # Add newly discovered URLs to the queue
            for new_urls in results:
                for url_info in new_urls:
                    url, depth = url_info
                    if url not in self.visited and depth <= self.max_depth:
                        queue.append((url, depth))
                        
            # Sort queue so we process lower depths first (breadth-first)
            queue.sort(key=lambda x: x[1])
            
            # Avoid processing too many URLs
            if len(queue) > self.max_pages * 2:
                queue = queue[:self.max_pages * 2]

    async def crawl(self, url: str, status: Any) -> List[CrawlResult]:
        """Main crawl method"""
        is_valid, message = URLValidator.validate(url)
        if not is_valid:
            st.error(f"❌ {message}")
            return []
        
        try:
            progress_bar = st.progress(0.0)
            self.processed = 0
            self.visited.clear()
            self.results.clear()

            async with aiohttp.ClientSession() as session:
                status.write(f"🔍 Starting crawl of: {url}")
                await self.breadth_first_crawl(url, session, progress_bar, status)
                
                status.write(f"✅ Crawling complete. Found {len(self.results)} pages with content.")
                status.write(f"📊 Total processed pages: {self.processed}, visited URLs: {len(self.visited)}")

            return self.results

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return []
        finally:
            if 'progress_bar' in locals():
                progress_bar.empty()

def crawl_website(url: str, max_depth: int = 2, max_pages: int = 50, status: Any = None) -> List[CrawlResult]:
    """Synchronous wrapper for the async crawler"""
    crawler = AsyncWebCrawler(max_depth=max_depth, max_pages=max_pages)
    return asyncio.run(crawler.crawl(url, status))