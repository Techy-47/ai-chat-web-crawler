from typing import Tuple, Optional, BinaryIO
import streamlit as st
from PyPDF2 import PdfReader
import time

class FileProcessor:
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):  # 10MB default
        self.max_file_size = max_file_size

    def process_pdf(self, file: BinaryIO, max_pages: int = 100) -> Tuple[Optional[str], Optional[str]]:
        """Process PDF with enhanced error handling and size limits"""
        try:
            content = []
            total_size = 0
            
            pdf_reader = PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            if total_pages > max_pages:
                return None, f"PDF has too many pages ({total_pages}). Maximum is {max_pages}."
                
            progress_bar = st.sidebar.progress(0)
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    content.append(text)
                    
                    total_size += len(text.encode('utf-8'))
                    if total_size > self.max_file_size:
                        return None, "PDF content exceeds size limit"
                        
                    progress_bar.progress((i + 1) / total_pages)
                    
                except Exception as e:
                    st.warning(f"Warning: Could not process page {i+1}: {str(e)}")
                    continue
                    
            progress_bar.empty()
            return "\n\n".join(content), None
            
        except Exception as e:
            return None, f"Error processing PDF: {str(e)}"
        finally:
            if 'progress_bar' in locals():
                progress_bar.empty()

    def process_text_file(self, file: BinaryIO) -> Tuple[Optional[str], Optional[str]]:
        """Process text files with size limits and encoding detection"""
        try:
            file_content = file.read()
            if len(file_content) > self.max_file_size:
                return None, f"File too large. Maximum size is {self.max_file_size / (1024 * 1024):.1f}MB"
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    text_content = file_content.decode(encoding)
                    return text_content, None
                except UnicodeDecodeError:
                    continue
                    
            return None, "Could not decode file. Please ensure it's a valid text document."
            
        except Exception as e:
            return None, f"Error processing text file: {str(e)}"