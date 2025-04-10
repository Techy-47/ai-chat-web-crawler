from typing import List, Dict, Any, Optional, Generator, Tuple, AsyncGenerator
import requests
import json
import sseclient
import time
from collections import deque
from threading import Lock
import functools
import random
import streamlit as st

class RateLimiter:
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.timestamps: deque = deque(maxlen=max_requests)
        self.lock = Lock()

    def check_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        with self.lock:
            while self.timestamps and self.timestamps[0] < current_time - self.time_window:
                self.timestamps.popleft()
            
            if len(self.timestamps) >= self.max_requests:
                return False
            
            self.timestamps.append(current_time)
            return True

class ChatAPI:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = RateLimiter()
        self.chat_endpoint = f"{base_url}/chat/completions"
        self.models_endpoint = f"{base_url}/models"

    @staticmethod
    def retry_with_backoff(max_retries: int = 3, initial_backoff: int = 1, max_backoff: int = 10):
        """Retry decorator with exponential backoff"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                retries = 0
                backoff = initial_backoff
                
                while retries <= max_retries:
                    try:
                        return func(*args, **kwargs)
                    except (requests.exceptions.Timeout, 
                            requests.exceptions.ConnectionError) as e:
                        retries += 1
                        if retries > max_retries:
                            raise e
                        
                        jitter = random.uniform(0, 0.3) * backoff
                        sleep_time = backoff + jitter
                        time.sleep(sleep_time)
                        backoff = min(backoff * 2, max_backoff)
            return wrapper
        return decorator

    def get_headers(self, stream: bool = False) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "localhost:8501",
            "X-Title": "Free AI Chat App"
        }
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    @retry_with_backoff()
    def fetch_models(self) -> Dict[str, Any]:
        """Fetch available models from the API"""
        try:
            if not self.rate_limiter.check_limit():
                return {"error": "Rate limit exceeded"}

            response = requests.get(
                self.models_endpoint,
                headers=self.get_headers(),
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def process_stream(self, response: requests.Response) -> Generator[str, None, None]:
        """Process streaming response from the API"""
        try:
            client = sseclient.SSEClient(response)
            full_response = ""
            
            for event in client.events():
                if event.data == "[DONE]":
                    break
                    
                try:
                    data = json.loads(event.data)
                    if data.get('choices') and len(data['choices']) > 0:
                        content = data['choices'][0].get('delta', {}).get('content', '')
                        if content:
                            full_response += content
                            yield content
                    if data.get('error'):
                        error_message = data.get('error', {}).get('message', 'Unknown error occurred')
                        yield f"\n\nError from API: {error_message}"
                        break
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    yield f"\n\nError processing response: {str(e)}"
                    break
            
            if not full_response:
                yield "I apologize, but I couldn't generate a response. Please try again."
        except Exception as e:
            yield f"\n\nConnection error: {str(e)}"

    @retry_with_backoff()
    def make_request(self, 
                    messages: List[Dict[str, str]], 
                    model: str,
                    temperature: float = 0.7,
                    max_tokens: int = 2000) -> requests.Response:
        """Make a request to the chat API"""
        if not self.rate_limiter.check_limit():
            raise Exception("Rate limit exceeded. Please wait a moment before trying again.")
        
        # Validate messages - if messages is empty, raise exception
        if not messages or len(messages) == 0:
            raise Exception("Cannot send empty messages to the API")
            
        payload = {
            "messages": messages,
            "model": model,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        return requests.post(
            self.chat_endpoint,
            headers=self.get_headers(stream=True),
            json=payload,
            stream=True,
            timeout=60
        )

class ChatManager:
    def __init__(self, api: ChatAPI):
        self.api = api
        self.messages: List[Dict[str, str]] = []
        self.max_history = 100
        self.memory_limit = 1024 * 1024  # 1MB

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history with memory management"""
        self.messages.append({"role": role, "content": content})
        self._manage_chat_history()

    def _manage_chat_history(self) -> None:
        """Manage chat history size and memory usage"""
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        total_size = sum(len(str(m)) for m in self.messages)
        while total_size > self.memory_limit and self.messages:
            removed_message = self.messages.pop(0)
            total_size -= len(str(removed_message))

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the chat history"""
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear the chat history"""
        self.messages.clear()

    async def process_message(self, 
                            prompt: str, 
                            model: str,
                            temperature: float = 0.7,
                            max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        """Process a new message and get the response"""
        # Validate prompt is not empty
        if not prompt or prompt.strip() == "":
            yield "Error: Cannot send an empty message."
            return
            
        self.add_message("user", prompt)
        
        try:
            response = self.api.make_request(
                messages=self.messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.status_code == 200:
                full_response = ""
                for content in self.api.process_stream(response):
                    full_response += content
                    yield content
                
                # Add assistant's response to history
                self.add_message("assistant", full_response)
            else:
                error_msg = f"Error: {response.text}"
                yield error_msg
                # Remove the user message if there was an error
                self.messages.pop()
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield error_msg
            # Remove the user message if there was an error
            self.messages.pop()