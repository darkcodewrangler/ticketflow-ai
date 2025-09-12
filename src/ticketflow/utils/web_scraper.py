"""Web Scraper for Knowledge Base
Extracts content from web pages with robots.txt compliance and rate limiting
"""

import asyncio
import aiohttp
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraper with robots.txt compliance and rate limiting"""
    
    def __init__(self, rate_limit_delay: float = 1.0, user_agent: str = "TicketFlow-AI/1.0"):
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        self.last_request_time = {}
        self.robots_cache = {}
        self.session = None
    
    async def scrape_url(
        self, 
        url: str, 
        follow_links: bool = True, 
        max_depth: int = 3
    ) -> List[Dict[str, str]]:
        """Scrape content from URL with optional link following"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': self.user_agent}
        ) as session:
            self.session = session
            
            visited_urls = set()
            results = []
            
            # Start with the main URL
            await self._scrape_page_recursive(
                url, visited_urls, results, 0, max_depth, follow_links
            )
            
            return results
    
    async def _scrape_page_recursive(
        self,
        url: str,
        visited_urls: Set[str],
        results: List[Dict],
        current_depth: int,
        max_depth: int,
        follow_links: bool
    ):
        """Recursively scrape pages"""
        if current_depth > max_depth or url in visited_urls:
            return
        
        # Check robots.txt
        if not await self._can_fetch(url):
            logger.warning(f"Robots.txt disallows fetching {url}")
            return
        
        # Rate limiting
        await self._rate_limit(url)
        
        try:
            # Fetch page content
            page_data = await self._fetch_page_content(url)
            if page_data:
                visited_urls.add(url)
                results.append(page_data)
                
                # Follow links if enabled and not at max depth
                if follow_links and current_depth < max_depth:
                    links = self._extract_links(page_data['raw_html'], url)
                    
                    # Process links concurrently but with rate limiting
                    for link in links[:10]:  # Limit to 10 links per page
                        await self._scrape_page_recursive(
                            link, visited_urls, results, 
                            current_depth + 1, max_depth, follow_links
                        )
        
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
    
    async def _fetch_page_content(self, url: str) -> Optional[Dict[str, str]]:
        """Fetch and parse page content"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    logger.warning(f"Non-HTML content type for {url}: {content_type}")
                    return None
                
                html_content = await response.text()
                return self._parse_html_content(html_content, url)
        
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _parse_html_content(self, html: str, url: str) -> Dict[str, str]:
        """Parse HTML content and extract meaningful text"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else urlparse(url).path.split('/')[-1]
        
        # Extract main content
        content = self._extract_main_content(soup)
        
        # Generate summary from first paragraph or first 200 chars
        summary = self._generate_summary(content)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'summary': summary,
            'raw_html': html
        }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from parsed HTML"""
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '#main-content', '.post-content',
            '.entry-content', '.article-content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text and clean it
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up the text
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Filter out very short lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _generate_summary(self, content: str) -> str:
        """Generate a summary from content"""
        # Take first few sentences or first 200 characters
        sentences = re.split(r'[.!?]+', content)
        
        summary = ""
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if sentence:
                summary += sentence + ". "
                if len(summary) > 200:
                    break
        
        return summary.strip()[:200] + "..." if len(summary) > 200 else summary.strip()
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract internal links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Only include links from the same domain
            if urlparse(absolute_url).netloc == base_domain:
                # Filter out common non-content links
                if not any(skip in absolute_url.lower() for skip in [
                    'javascript:', 'mailto:', '#', '.pdf', '.jpg', '.png', 
                    '.gif', '.css', '.js', 'login', 'register', 'admin'
                ]):
                    links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    async def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check cache first
            if base_url in self.robots_cache:
                rp = self.robots_cache[base_url]
            else:
                # Fetch and parse robots.txt
                robots_url = urljoin(base_url, '/robots.txt')
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                try:
                    async with self.session.get(robots_url) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            # Parse robots.txt content
                            rp.read()
                        else:
                            # If no robots.txt, assume we can fetch
                            return True
                except:
                    # If can't fetch robots.txt, assume we can fetch
                    return True
                
                self.robots_cache[base_url] = rp
            
            return rp.can_fetch(self.user_agent, url)
        
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if there's an error
    
    async def _rate_limit(self, url: str):
        """Implement rate limiting per domain"""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()