import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import io
import re

class PDFService:
    def __init__(self):
        pass

    async def extract_text_from_pdf(self, file_path: str) -> Dict[str, any]:
        """Extract text content from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get basic info
                num_pages = len(pdf_reader.pages)
                text_content = []
                page_texts = {}
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            # Clean up the text
                            cleaned_text = self._clean_text(page_text)
                            text_content.append(cleaned_text)
                            page_texts[page_num] = cleaned_text
                    except Exception as e:
                        print(f"Error extracting text from page {page_num}: {e}")
                        page_texts[page_num] = ""
                
                # Combine all text
                full_text = "\n\n".join(text_content)
                
                # Get metadata
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    }
                
                return {
                    'success': True,
                    'text': full_text,
                    'page_count': num_pages,
                    'page_texts': page_texts,
                    'metadata': metadata,
                    'word_count': len(full_text.split()) if full_text else 0,
                    'character_count': len(full_text) if full_text else 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract text from PDF: {str(e)}",
                'text': '',
                'page_count': 0,
                'page_texts': {},
                'metadata': {}
            }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Fix common OCR issues
        text = text.replace('�', '')  # Remove replacement characters
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple line breaks to double
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text

    async def get_pdf_info(self, file_path: str) -> Dict[str, any]:
        """Get basic PDF information without full text extraction"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                num_pages = len(pdf_reader.pages)
                
                # Get metadata
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    }
                
                # Check if PDF is encrypted
                is_encrypted = pdf_reader.is_encrypted
                
                return {
                    'success': True,
                    'page_count': num_pages,
                    'metadata': metadata,
                    'is_encrypted': is_encrypted,
                    'file_size': Path(file_path).stat().st_size
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get PDF info: {str(e)}"
            }

    async def extract_text_from_page(self, file_path: str, page_number: int) -> Dict[str, any]:
        """Extract text from a specific page"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_number < 1 or page_number > len(pdf_reader.pages):
                    return {
                        'success': False,
                        'error': f"Page {page_number} does not exist. PDF has {len(pdf_reader.pages)} pages."
                    }
                
                page = pdf_reader.pages[page_number - 1]  # Convert to 0-based index
                page_text = page.extract_text()
                cleaned_text = self._clean_text(page_text)
                
                return {
                    'success': True,
                    'text': cleaned_text,
                    'page_number': page_number,
                    'word_count': len(cleaned_text.split()) if cleaned_text else 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract text from page {page_number}: {str(e)}"
            }

    async def search_text_in_pdf(self, file_path: str, query: str) -> List[Dict[str, any]]:
        """Search for text within PDF and return matches with page numbers"""
        try:
            results = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        cleaned_text = self._clean_text(page_text)
                        
                        # Case-insensitive search
                        if query.lower() in cleaned_text.lower():
                            # Find all occurrences in the page
                            text_lower = cleaned_text.lower()
                            query_lower = query.lower()
                            
                            start = 0
                            while True:
                                pos = text_lower.find(query_lower, start)
                                if pos == -1:
                                    break
                                
                                # Extract context around the match
                                context_start = max(0, pos - 100)
                                context_end = min(len(cleaned_text), pos + len(query) + 100)
                                context = cleaned_text[context_start:context_end]
                                
                                results.append({
                                    'page_number': page_num,
                                    'position': pos,
                                    'context': context,
                                    'match': cleaned_text[pos:pos + len(query)]
                                })
                                
                                start = pos + 1
                                
                    except Exception as e:
                        print(f"Error searching page {page_num}: {e}")
                        continue
            
            return results
            
        except Exception as e:
            print(f"Error searching PDF: {e}")
            return []

    async def validate_pdf(self, file_path: str) -> Dict[str, any]:
        """Validate PDF file integrity and readability"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Basic validation
                num_pages = len(pdf_reader.pages)
                
                if num_pages == 0:
                    return {
                        'valid': False,
                        'error': 'PDF has no pages'
                    }
                
                # Check if we can read at least the first page
                try:
                    first_page = pdf_reader.pages[0]
                    first_page.extract_text()
                except Exception as e:
                    return {
                        'valid': False,
                        'error': f'Cannot read PDF content: {str(e)}'
                    }
                
                # Check if encrypted and needs password
                is_encrypted = pdf_reader.is_encrypted
                
                return {
                    'valid': True,
                    'page_count': num_pages,
                    'is_encrypted': is_encrypted,
                    'readable': True
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid PDF file: {str(e)}'
            }

    def get_text_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, any]]:
        """Split text into chunks for processing"""
        if not text:
            return []
        
        chunks = []
        words = text.split()
        
        if len(words) <= chunk_size:
            return [{
                'text': text,
                'chunk_index': 0,
                'word_count': len(words),
                'start_word': 0,
                'end_word': len(words)
            }]
        
        start = 0
        chunk_index = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'chunk_index': chunk_index,
                'word_count': len(chunk_words),
                'start_word': start,
                'end_word': end
            })
            
            # Move start position with overlap
            start = end - overlap if end < len(words) else end
            chunk_index += 1
        
        return chunks
