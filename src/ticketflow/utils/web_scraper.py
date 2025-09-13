"""Web Scraper for Knowledge Base
Extracts content from web pages using Jina AI Reader API"""


import aiohttp
from typing import List, Dict, Optional
import logging
from ticketflow.config import config
logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraper using Jina AI Reader API"""
    
    def __init__(self, jina_api_key: Optional[str] = None):
        self.jina_api_key = config.JINA_API_KEY
        self.base_url = "https://r.jina.ai/"
        self.session = None
    
    async def scrape_url(self, url: str) -> List[Dict[str, str]]:
        """Scrape content from URL using Jina AI Reader API"""
        try:
            # Prepare headers for Jina AI Reader API
            headers = {
                'Accept': 'application/json',
                'X-Retain-Images': 'none',
                'X-With-Links-Summary': 'true'
            }
            
            # Add API key if available
            if self.jina_api_key:
                headers['Authorization'] = f'Bearer {self.jina_api_key}'
            
            # Construct Jina AI Reader URL
            jina_url = f"{self.base_url}{url}"
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Jina AI Reader API returned status {response.status} for {url}")
                        return []
                    
                    data = await response.json()
                    
                    # Extract content from Jina AI response
                    if 'data' in data:
                        result = self._parse_jina_response(data['data'], url)
                        return [result] if result else []
                    else:
                        logger.error(f"Unexpected response format from Jina AI Reader API for {url}")
                        return []
                        
        except Exception as e:
             logger.error(f"Failed to scrape {url} using Jina AI Reader: {e}")
             return []
    
    def _parse_jina_response(self, jina_data: Dict, original_url: str) -> Optional[Dict[str, str]]:
        """Parse Jina AI Reader API response into our expected format"""
        try:
            # Extract basic information
            title = jina_data.get('title', '')
            content = jina_data.get('content', '')
            description = jina_data.get('description', '')
            
            # Generate summary from description or first part of content
            summary = description if description else self._generate_summary(content)
            
            # Extract links if available
            links = jina_data.get('links', {})
            
            return {
                'url': original_url,
                'title': title,
                'content': content,
                'summary': summary,
                'links': links,
                'raw_html': ''  # Jina AI doesn't provide raw HTML
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Jina AI response for {original_url}: {e}")
            return None
    
    def _generate_summary(self, content: str) -> str:
        """Generate a summary from content"""
        if not content:
            return ""
        
        # Take first 200 characters or first sentence, whichever is shorter
        sentences = content.split('. ')
        if sentences and len(sentences[0]) <= 200:
            return sentences[0] + '.'
        else:
            return content[:200] + "..." if len(content) > 200 else content