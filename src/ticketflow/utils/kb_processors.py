"""Knowledge Base File Processors
Handles processing of different file types for knowledge base ingestion
"""

import io
import re
from typing import Dict, Any, List
import logging
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)

class KnowledgeBaseProcessor:
    """Processes different file types for knowledge base ingestion"""
    
    def __init__(self):
        self.supported_types = {
            'text/markdown': self._process_markdown,
            'text/plain': self._process_text,
            'application/pdf': self._process_pdf
        }
    
    async def process_file_content(
        self, 
        content: bytes, 
        filename: str, 
        content_type: str
    ) -> Dict[str, Any]:
        """Process file content based on type"""
        try:
            # Get processor for content type
            processor = self.supported_types.get(content_type)
            if not processor:
                # Fallback to extension-based detection
                extension = filename.lower().split('.')[-1] if '.' in filename else ''
                if extension == 'md':
                    processor = self._process_markdown
                elif extension == 'txt':
                    processor = self._process_text
                elif extension == 'pdf':
                    processor = self._process_pdf
                else:
                    processor = self._process_text  # Default fallback
            
            # Handle PDF files differently (binary content)
            if processor == self._process_pdf:
                return await processor(content, filename)
            else:
                # Decode content for text-based files
                text_content = content.decode('utf-8')
                return await processor(text_content, filename)
            
        except UnicodeDecodeError:
            logger.error(f"Failed to decode file {filename} as UTF-8")
            raise ValueError("File must be UTF-8 encoded")
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")
            raise
    
    async def _process_markdown(self, content: str, filename: str) -> Dict[str, Any]:
        """Process markdown files"""
        lines = content.split('\n')
        
        # Extract title from first heading or filename
        title = self._extract_title_from_filename(filename)
        summary = ""
        
        # Look for first H1 heading
        for line in lines:
            if line.strip().startswith('# '):
                title = line.strip()[2:].strip()
                break
        
        # Generate summary from first paragraph or first few lines
        content_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        if content_lines:
            summary = ' '.join(content_lines[:3])[:200] + '...' if len(' '.join(content_lines[:3])) > 200 else ' '.join(content_lines[:3])
        
        # Clean content for better processing
        cleaned_content = self._clean_markdown_content(content)
        
        return {
            'title': title,
            'content': cleaned_content,
            'summary': summary,
            'format': 'markdown'
        }
    
    async def _process_text(self, content: str, filename: str) -> Dict[str, Any]:
        """Process plain text files"""
        lines = content.split('\n')
        
        # Extract title from filename or first line
        title = self._extract_title_from_filename(filename)
        
        # Check if first line could be a title
        if lines and len(lines[0].strip()) < 100 and not lines[0].strip().endswith('.'):
            title = lines[0].strip()
            content = '\n'.join(lines[1:]).strip()
        
        # Generate summary from first few lines
        content_lines = [line.strip() for line in lines if line.strip()]
        summary = ' '.join(content_lines[:3])[:200] + '...' if len(' '.join(content_lines[:3])) > 200 else ' '.join(content_lines[:3])
        
        return {
            'title': title,
            'content': content,
            'summary': summary,
            'format': 'text'
        }
    
    async def _process_pdf(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Process PDF files"""
        try:
            if PyPDF2 is None:
                raise ValueError("PyPDF2 library is not installed. Please install it to process PDF files.")
            
            # Create PDF reader from bytes
            pdf_stream = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            if len(pdf_reader.pages) == 0:
                raise ValueError("PDF file has no pages")
            
            # Extract text from all pages
            text_content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            if not text_content.strip():
                raise ValueError("No readable text found in PDF")
            
            # Extract title from filename
            title = self._extract_title_from_filename(filename)
            
            # Clean and format content
            formatted_content = self._clean_pdf_content(text_content)
            
            # Generate summary
            word_count = len(formatted_content.split())
            summary = f"PDF document with {len(pdf_reader.pages)} pages and approximately {word_count} words"
            
            return {
                'title': title,
                'content': formatted_content,
                'summary': summary,
                'format': 'pdf'
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF file {filename}: {e}")
            raise ValueError(f"Invalid PDF format: {e}")
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """Extract a clean title from filename"""
        # Remove extension
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Replace underscores and hyphens with spaces
        name = re.sub(r'[_-]', ' ', name)
        
        # Capitalize words
        return ' '.join(word.capitalize() for word in name.split())
    
    def _clean_markdown_content(self, content: str) -> str:
        """Clean markdown content for better processing"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Keep markdown formatting but clean up
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Keep the line but strip trailing whitespace
            cleaned_lines.append(line.rstrip())
        
        return '\n'.join(cleaned_lines).strip()
    
    def _clean_pdf_content(self, content: str) -> str:
        """Clean and format PDF content for better processing"""
        if not content.strip():
            return "Empty PDF content"
        
        # Remove excessive whitespace and normalize line breaks
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Split into lines and clean each line
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace from each line
            line = line.strip()
            
            # Skip very short lines that are likely formatting artifacts
            if len(line) < 2 and not line.isdigit():
                continue
                
            # Keep the line
            cleaned_lines.append(line)
        
        # Join lines back together
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Remove page separators if they're too frequent
        cleaned_content = re.sub(r'\n--- Page \d+ ---\n', '\n\n', cleaned_content)
        
        # Final cleanup
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip()