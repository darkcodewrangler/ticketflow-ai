"""AI Metadata Generator for Knowledge Base
Generates author, summary, category, and tags using AI
"""

import json
import logging
from typing import Dict, List, Optional

from ticketflow.agent.ai_client import AIClient

logger = logging.getLogger(__name__)

class AIMetadataGenerator:
    """Generates metadata for knowledge base articles using AI"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.chat_client = self.ai_client.chat_client
        self.model = 'openai/gpt-4o' if self.ai_client.can_use_openrouter else 'gpt-4o'
    
    async def generate_metadata(
        self, 
        title: str, 
        content: str, 
        existing_categories: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """Generate comprehensive metadata for content"""
        try:
            # Truncate content if too long to avoid token limits
            truncated_content = content[:2000] + "..." if len(content) > 2000 else content
            
            prompt = self._build_metadata_prompt(title, truncated_content, existing_categories)
            
            response = await self._make_llm_request(prompt)
            metadata = self._parse_metadata_response(response)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            return self._fallback_metadata(title, content)
    
    def _build_metadata_prompt(
        self, 
        title: str, 
        content: str, 
        existing_categories: Optional[List[str]] = None
    ) -> str:
        """Build prompt for metadata generation"""
        
        categories_hint = ""
        if existing_categories:
            categories_hint = f"\nExisting categories in the system: {', '.join(existing_categories[:10])}"
            categories_hint += "\nPrefer using existing categories when appropriate, but create new ones if needed."
        
        return f"""
Analyze the following content and generate metadata for a knowledge base article.

TITLE: {title}

CONTENT:
{content}
{categories_hint}

Generate the following metadata in JSON format:
1. **author**: Identify or infer the likely author/source (e.g., "Technical Documentation Team", "Support Team", "Web Source", specific person if mentioned)
2. **summary**: Create a concise 1-2 sentence summary (max 150 characters)
3. **category**: Assign to the most appropriate category (e.g., "technical", "troubleshooting", "how-to", "policy", "faq", "product-info")
4. **tags**: Generate 3-5 relevant tags for searchability

Consider the content type, technical level, and purpose when generating metadata.

Respond with valid JSON only:
{{
    "author": "string",
    "summary": "string", 
    "category": "string",
    "tags": ["tag1", "tag2", "tag3"]
}}
"""
    
    async def _make_llm_request(self, prompt: str) -> str:
        """Make request to LLM"""
        try:
            response = await self.chat_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst. Generate accurate metadata for knowledge base articles. Always respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    def _parse_metadata_response(self, response: str) -> Dict[str, any]:
        """Parse and validate LLM response"""
        try:
            metadata = json.loads(response)
            
            # Validate and clean the response
            cleaned_metadata = {
                'author': self._clean_author(metadata.get('author', 'Unknown')),
                'summary': self._clean_summary(metadata.get('summary', '')),
                'category': self._clean_category(metadata.get('category', 'general')),
                'tags': self._clean_tags(metadata.get('tags', []))
            }
            
            return cleaned_metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError("Invalid JSON response from AI")
    
    def _clean_author(self, author: str) -> str:
        """Clean and validate author field"""
        if not author or not isinstance(author, str):
            return "Unknown"
        
        author = author.strip()[:100]  # Limit length
        
        # If it looks like a generic response, make it more specific
        if author.lower() in ['unknown', 'not specified', 'n/a', 'none']:
            return "Content Author"
        
        return author
    
    def _clean_summary(self, summary: str) -> str:
        """Clean and validate summary field"""
        if not summary or not isinstance(summary, str):
            return "Knowledge base article"
        
        summary = summary.strip()
        
        # Ensure it's not too long
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        # Ensure it ends with proper punctuation
        if summary and not summary.endswith(('.', '!', '?')):
            summary += "."
        
        return summary
    
    def _clean_category(self, category: str) -> str:
        """Clean and validate category field"""
        if not category or not isinstance(category, str):
            return "general"
        
        category = category.strip().lower()
        
        # Map common variations to standard categories
        category_mapping = {
            'tech': 'technical',
            'howto': 'how-to',
            'how_to': 'how-to',
            'trouble': 'troubleshooting',
            'debug': 'troubleshooting',
            'faq': 'faq',
            'faqs': 'faq',
            'product': 'product-info',
            'documentation': 'technical',
            'docs': 'technical',
            'guide': 'how-to',
            'tutorial': 'how-to'
        }
        
        return category_mapping.get(category, category)
    
    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Clean and validate tags field"""
        if not tags or not isinstance(tags, list):
            return []
        
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                # Clean the tag
                clean_tag = tag.strip().lower()
                clean_tag = clean_tag.replace(' ', '-')  # Replace spaces with hyphens
                clean_tag = ''.join(c for c in clean_tag if c.isalnum() or c in '-_')  # Keep only alphanumeric and hyphens/underscores
                
                if clean_tag and len(clean_tag) > 1 and clean_tag not in cleaned_tags:
                    cleaned_tags.append(clean_tag)
        
        # Limit to 5 tags
        return cleaned_tags[:5]
    
    def _fallback_metadata(self, title: str, content: str) -> Dict[str, any]:
        """Generate fallback metadata when AI fails"""
        # Simple heuristic-based metadata generation
        
        # Determine category based on keywords
        content_lower = (title + " " + content).lower()
        
        if any(word in content_lower for word in ['error', 'fix', 'problem', 'issue', 'troubleshoot']):
            category = 'troubleshooting'
        elif any(word in content_lower for word in ['how to', 'guide', 'tutorial', 'step']):
            category = 'how-to'
        elif any(word in content_lower for word in ['api', 'code', 'technical', 'development']):
            category = 'technical'
        elif any(word in content_lower for word in ['policy', 'rule', 'guideline']):
            category = 'policy'
        elif any(word in content_lower for word in ['faq', 'question', 'answer']):
            category = 'faq'
        else:
            category = 'general'
        
        # Generate simple tags based on common words
        words = content_lower.split()
        common_tech_words = [
            'api', 'database', 'server', 'client', 'user', 'system', 'configuration',
            'installation', 'setup', 'troubleshooting', 'guide', 'tutorial'
        ]
        
        tags = [word for word in common_tech_words if word in words][:3]
        if not tags:
            tags = ['knowledge-base']
        
        # Generate summary from first sentence or first 100 chars
        sentences = content.split('. ')
        summary = sentences[0][:100] + "..." if len(sentences[0]) > 100 else sentences[0]
        if not summary.endswith('.'):
            summary += "."
        
        return {
            'author': 'Content Team',
            'summary': summary,
            'category': category,
            'tags': tags
        }