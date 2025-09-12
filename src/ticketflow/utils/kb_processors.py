"""Knowledge Base File Processors
Handles processing of different file types for knowledge base ingestion
"""

import csv
import io
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseProcessor:
    """Processes different file types for knowledge base ingestion"""
    
    def __init__(self):
        self.supported_types = {
            'text/markdown': self._process_markdown,
            'text/plain': self._process_text,
            'text/csv': self._process_csv,
            'application/csv': self._process_csv
        }
    
    async def process_file_content(
        self, 
        content: bytes, 
        filename: str, 
        content_type: str
    ) -> Dict[str, Any]:
        """Process file content based on type"""
        try:
            # Decode content
            text_content = content.decode('utf-8')
            
            # Get processor for content type
            processor = self.supported_types.get(content_type)
            if not processor:
                # Fallback to extension-based detection
                extension = filename.lower().split('.')[-1] if '.' in filename else ''
                if extension == 'md':
                    processor = self._process_markdown
                elif extension == 'txt':
                    processor = self._process_text
                elif extension == 'csv':
                    processor = self._process_csv
                else:
                    processor = self._process_text  # Default fallback
            
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
    
    async def _process_csv(self, content: str, filename: str) -> Dict[str, Any]:
        """Process CSV files"""
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            rows = list(csv_reader)
            
            if not rows:
                raise ValueError("CSV file is empty")
            
            # Extract title from filename
            title = self._extract_title_from_filename(filename)
            
            # Convert CSV to readable format
            formatted_content = self._format_csv_content(rows, csv_reader.fieldnames)
            
            # Generate summary
            summary = f"CSV data with {len(rows)} rows and {len(csv_reader.fieldnames)} columns: {', '.join(csv_reader.fieldnames[:5])}"
            if len(csv_reader.fieldnames) > 5:
                summary += "..."
            
            return {
                'title': title,
                'content': formatted_content,
                'summary': summary,
                'format': 'csv'
            }
            
        except Exception as e:
            logger.error(f"Failed to process CSV file {filename}: {e}")
            raise ValueError(f"Invalid CSV format: {e}")
    
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
    
    def _format_csv_content(self, rows: List[Dict], fieldnames: List[str]) -> str:
        """Format CSV data into readable text"""
        if not rows or not fieldnames:
            return "Empty CSV data"
        
        # Create a formatted representation
        content_parts = []
        content_parts.append(f"CSV Data Summary:")
        content_parts.append(f"Columns: {', '.join(fieldnames)}")
        content_parts.append(f"Total Rows: {len(rows)}")
        content_parts.append("\nData Preview:")
        
        # Show first few rows in a readable format
        for i, row in enumerate(rows[:10]):  # Show first 10 rows
            content_parts.append(f"\nRow {i+1}:")
            for field in fieldnames:
                value = row.get(field, '')
                if value:
                    content_parts.append(f"  {field}: {value}")
        
        if len(rows) > 10:
            content_parts.append(f"\n... and {len(rows) - 10} more rows")
        
        # Add searchable content by concatenating all values
        content_parts.append("\nFull Data for Search:")
        all_values = []
        for row in rows:
            for field in fieldnames:
                value = str(row.get(field, '')).strip()
                if value:
                    all_values.append(f"{field}: {value}")
        
        content_parts.append(' | '.join(all_values))
        
        return '\n'.join(content_parts)