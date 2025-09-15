import logging
from typing import Any, Dict, List

from ticketflow.database.connection import db_manager
from ticketflow.database.models import KnowledgeBaseArticle
from ticketflow.database.operations.utils import   reranker
from ticketflow.utils.helpers import get_isoformat, get_value
logger = logging.getLogger(__name__)
class KnowledgeBaseOperations:
    """
    Knowledge base operations with PyTiDB AI features
    """

    @staticmethod
    def create_article(article_data: Dict[str, Any]) -> KnowledgeBaseArticle:
        """Create KB article - PyTiDB auto-generates embeddings!"""
        try:
            article = KnowledgeBaseArticle(
                title=get_value(article_data, "title", ""),
                content=get_value(article_data, "content", ""),
                summary=get_value(article_data, "summary", ""),
                category=get_value(article_data, "category", "general"),
                tags=get_value(article_data, "tags", []),
                source_url=get_value(article_data, "source_url", ""),
                source_type=get_value(article_data, "source_type", "manual"),
                author=get_value(article_data, "author", "")
            )
            
            # PyTiDB automatically generates embeddings for title, content, and summary!
            result = db_manager.kb_articles.insert(article)
            # Handle case where insert returns a list
            created_article = result[0] if isinstance(result, list) else result
            
            logger.info(f"📚 Created KB article {created_article.id} with auto-embeddings")
            return created_article
            
        except Exception as e:
            logger.error(f"❌ Failed to create KB article: {e}")
            raise

    @staticmethod
    def search_articles(query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """
        Search knowledge base using PyTiDB's intelligent search
        """
        try:
            filters = {}
            if category:
                filters["category"] = category
            
            # PyTiDB's built-in hybrid search on KB articles
            searchQuery = db_manager.kb_articles.search(
                query,
                search_type='hybrid'      
            ).vector_column('content_vector').text_column('title').limit(limit).filter(filters)
            if reranker is not None:
                searchQuery = searchQuery.rerank(reranker,'title').distance_range(0.7)


            results=searchQuery.to_list()

            # Convert to our format - handle both objects and dicts
            articles = []
            for result in results:
                # Handle both object attributes and dictionary keys
                
                content = get_value(result, 'content', '')
                if len(content) > 300:
                    content = content[:300] + "..."
                
                # Calculate helpfulness score if it's not available
                helpful_votes = get_value(result, 'helpful_votes', 0)
                unhelpful_votes = get_value(result, 'unhelpful_votes', 0)
                total_votes = helpful_votes + unhelpful_votes
                helpfulness_score = (helpful_votes / total_votes) if total_votes > 0 else 0.0
                
                articles.append({
                    "article_id": get_value(result, 'id'),
                    "title": get_value(result, 'title', ''),
                    "content": content,
                    "summary": get_value(result, 'summary', ''),
                    "category": get_value(result, 'category', ''),
                    "tags": get_value(result, 'tags', []),
                    "source_url": get_value(result, 'source_url', ''),
                    "author": get_value(result, 'author', ''),
                    "helpfulness_score": helpfulness_score,
                    "distance": get_value(result, '_distance', 0.0),
                    "similarity_score": get_value(result, '_score', 0.0),
                    "usage_count": get_value(result, 'usage_in_resolutions', 0)
                })
            
            logger.info(f"📖 Found {len(articles)} relevant articles for: '{query[:50]}...'")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Failed to search articles: {e}")
            return []

    @staticmethod
    def get_articles_by_category(category: str, limit: int = 20) -> List[KnowledgeBaseArticle]:

        """Get articles by category"""
        try:
            return db_manager.kb_articles.query(
                filters={"category": category},
                limit=limit,
                order_by={"created_at":"desc"}
            ).to_list()
        except Exception as e:
            logger.error(f"❌ Failed to get articles by category: {e}")
            return []

    @staticmethod
    def update_article_usage(article_id: int, was_helpful: bool = True):

        """Track article usage and helpfulness"""
        try:
            # Get current article
            articles = db_manager.kb_articles.query(filters={"id": article_id}, limit=1).to_list()
            if not articles:
                return
            
            article = articles[0]
            # Handle the case where attributes might be dict keys instead of attributes
            usage_count = get_value(article, 'usage_in_resolutions', 0) 
            view_count = get_value(article, 'view_count', 0) 
            helpful_votes = get_value(article, 'helpful_votes', 0) 
            unhelpful_votes = get_value(article, 'unhelpful_votes', 0) 
            
            # Update usage stats
            updates = {
                "usage_in_resolutions": usage_count + 1,
                "view_count": view_count + 1,
                "last_accessed": get_isoformat()
            }
            
            if was_helpful:
                updates["helpful_votes"] = helpful_votes + 1
            else:
                updates["unhelpful_votes"] = unhelpful_votes + 1
            
            db_manager.kb_articles.update(
                filters={"id": article_id},
                values=updates
            )
            
            logger.info(f"📊 Updated usage stats for article {article_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update article usage: {e}")


__all__ = [
    "KnowledgeBaseOperations"
]
