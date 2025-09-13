"""
Knowledge Base API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
import asyncio

from ticketflow.database.operations import KnowledgeBaseOperations
from ticketflow.database.operations.processing_tasks import ProcessingTaskOperations
from ticketflow.database.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseResponse
from ticketflow.api.dependencies import verify_db_connection
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)
from ticketflow.database.connection import db_manager
from ticketflow.utils.kb_processors import KnowledgeBaseProcessor
from ticketflow.utils.web_scraper import WebScraper
from ticketflow.utils.ai_metadata_generator import AIMetadataGenerator
router = APIRouter()

@router.post("/articles")
async def create_article(
    article_data: KnowledgeBaseCreateRequest,
    _: bool = Depends(verify_db_connection)
):
    """Create a new knowledge base article"""
    try:
        article = await KnowledgeBaseOperations.create_article(article_data.model_dump())
        article_data = KnowledgeBaseResponse.model_validate(article).model_dump()
        
        return success_response(
            data=article_data,
            message=ResponseMessages.KB_ARTICLE_CREATED
        )
    except Exception as e:
        return error_response(
            message="Failed to create knowledge base article",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.post("/upload")
async def upload_knowledge_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    _: bool = Depends(verify_db_connection)
):
    """Upload and process knowledge base files (markdown, txt, pdf)"""
    try:
        # Validate file type
        allowed_types = ['text/markdown', 'text/plain', 'application/pdf']
        allowed_extensions = ['.md', '.txt', '.pdf']
        
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        if file.content_type not in allowed_types and f'.{file_extension}' not in allowed_extensions:
            return error_response(
                message="Unsupported file type. Only markdown (.md), text (.txt), and PDF (.pdf) files are allowed.",
                error_code=ErrorCodes.BAD_REQUEST
            )
        
        # Read file content
        content = await file.read()
        
        # Create processing task
        task_info = ProcessingTaskOperations.create_task(
            task_type="file_upload",
            source_name=file.filename,
            user_metadata={"content_type": file.content_type, "category": category, "tags": tags, "author": author}
        )
        task_id = task_info["task_id"]
        
        # Process file in background
        background_tasks.add_task(
            _process_uploaded_file,
            task_id,
            file.filename,
            content,
            file.content_type,
            category,
            tags.split(',') if tags else None,
            author
        )
        
        return success_response(
            message="File uploaded successfully. Processing in background.",
            data={"filename": file.filename, "status": "processing", "task_id": task_id}
        )
        
    except Exception as e:
        return error_response(
            message="Failed to upload file",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.post("/url")
async def process_url_source(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    _: bool = Depends(verify_db_connection)
):
    """Process URL as knowledge base source with optional link following"""
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return error_response(
                message="Invalid URL format. URL must start with http:// or https://",
                error_code=ErrorCodes.BAD_REQUEST
            )
        

        
        # Create processing task
        task_info = ProcessingTaskOperations.create_task(
            task_type="url_scraping",
            source_name=url,
            user_metadata={"category": category, "tags": tags, "author": author}
        )
        task_id = task_info["task_id"]
        
        # Process URL in background
        background_tasks.add_task(
            _process_url_source,
            task_id,
            url,
            category,
            tags.split(',') if tags else None,
            author
        )
        
        return success_response(
            message="URL processing started. Content will be extracted and processed in background.",
            data={"url": url, "status": "processing", "task_id": task_id}
        )
        
    except Exception as e:
        return error_response(
            message="Failed to process URL",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/processing-status")
async def get_processing_status(
    task_id: Optional[str] = None,
    _: bool = Depends(verify_db_connection)
):
    """Get status of background processing tasks"""
    try:
        if task_id:
            # Get specific task status
            task_status = ProcessingTaskOperations.get_task_status(task_id)
            if not task_status:
                return error_response(
                    message="Task not found",
                    error_code=ErrorCodes.NOT_FOUND
                )
            return success_response(
                message="Task status retrieved",
                data=task_status
            )
        else:
            # Get recent tasks
            recent_tasks = ProcessingTaskOperations.get_recent_tasks(limit=20)
            return success_response(
                message="Processing status retrieved",
                data={
                    "recent_tasks": recent_tasks,
                    "total_tasks": len(recent_tasks)
                }
            )
    except Exception as e:
        return error_response(
            message="Failed to get processing status",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

async def _process_uploaded_file(
    task_id: str,
    filename: str,
    content: bytes,
    content_type: str,
    category: Optional[str],
    tags: Optional[List[str]],
    author: Optional[str]
):
    """Background task to process uploaded files"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Update task status to processing
        ProcessingTaskOperations.update_task_status(task_id, "processing", 10)
        
        processor = KnowledgeBaseProcessor()
        ai_generator = AIMetadataGenerator()
        
        # Process file content
        ProcessingTaskOperations.update_task_status(task_id, "processing", 30)
        processed_content = await processor.process_file_content(
            content, filename, content_type
        )
        
        # Generate AI metadata if not provided
        ProcessingTaskOperations.update_task_status(task_id, "processing", 60)
        if not all([category, author]) or not tags:
            ai_metadata = await ai_generator.generate_metadata(
                processed_content['title'],
                processed_content['content']
            )
            
            category = category or ai_metadata.get('category', 'general')
            author = author or ai_metadata.get('author', 'Unknown')
            tags = tags or ai_metadata.get('tags', [])
        
        # Create knowledge base article
        ProcessingTaskOperations.update_task_status(task_id, "processing", 90)
        article_data = {
            'title': processed_content['title'],
            'content': processed_content['content'],
            'summary': processed_content.get('summary', ''),
            'category': category,
            'tags': tags,
            'source_url': '',
            'source_type': 'file_upload',
            'author': author
        }
        
        article = await KnowledgeBaseOperations.create_article(article_data)
        
        # Mark task as completed
        ProcessingTaskOperations.update_task_status(
            task_id, "completed", 100,
            result_data={"article_id": article.id, "title": article.title}
        )
        
        logger.info(f"✅ Successfully processed file: {filename} -> Article ID: {article.id}")
        
    except Exception as e:
        ProcessingTaskOperations.update_task_status(
            task_id, "failed", 0, error_message=str(e)
        )
        logger.error(f"❌ Failed to process file {filename}: {e}")

def _process_url_source(
    task_id: str,
    url: str,
    category: Optional[str],
    tags: Optional[List[str]],
    author: Optional[str]
):
    """Background task to process URL sources"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Update task status to processing
        ProcessingTaskOperations.update_task_status(task_id, "processing", 10)
        
        scraper = WebScraper()
        processor = KnowledgeBaseProcessor()
        ai_generator = AIMetadataGenerator()
        
        # Scrape content from URL
        ProcessingTaskOperations.update_task_status(task_id, "processing", 30)
        scraped_pages = asyncio.run(scraper.scrape_url(url))
        print(f"{scraped_pages}")
        articles_created = []
        total_pages = len(scraped_pages)
        
        # Process each scraped page
        for i, page_data in enumerate(scraped_pages):
            # Update progress
            progress = 30 + int((i / total_pages) * 60)
            ProcessingTaskOperations.update_task_status(task_id, "processing", progress)
            
            # Generate AI metadata if not provided
            if not all([category, author]) or not tags:
                ai_metadata = asyncio.run( ai_generator.generate_metadata(
                    page_data['title'],
                    page_data['content']
                ))
                
                page_category = category or ai_metadata.get('category', 'web_content')
                page_author = author or ai_metadata.get('author', 'Web Source')
                page_tags = tags or ai_metadata.get('tags', [])
            else:
                page_category = category
                page_author = author
                page_tags = tags
            
            # Create knowledge base article
            article_data = {
                'title': page_data['title'],
                'content': page_data['content'],
                'summary': page_data.get('summary', ''),
                'category': page_category,
                'tags': page_tags,
                'source_url': page_data['url'],
                'source_type': 'web_scraping',
                'author': page_author
            }
            
            article = asyncio.run( KnowledgeBaseOperations.create_article(article_data))
            articles_created.append({
                'id': article.id,
                'title': article.title,
                'url': page_data['url']
            })
        
        # Mark task as completed
        ProcessingTaskOperations.update_task_status(
            task_id, "completed", 100,
            result_data={
                "articles_created": len(articles_created),
                "articles": articles_created,
                "source_url": url
            }
        )
        
        logger.info(f"✅ Successfully processed URL: {url} -> {len(articles_created)} articles created")
        
    except Exception as e:
        ProcessingTaskOperations.update_task_status(
            task_id, "failed", 0, error_message=str(e)
        )
        logger.error(f"❌ Failed to process URL {url}: {e}")
    except Exception as e:
        return error_response(
            message="Failed to create knowledge base article",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/articles")
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get knowledge base articles"""
    try:
        if category:
            articles = await KnowledgeBaseOperations.get_articles_by_category(category, int(limit))
        else:
            
            articles = db_manager.kb_articles.query(
                limit=int(limit),
                order_by={"created_at": "desc"}
            ).to_list()
        
        article_list = [KnowledgeBaseResponse.model_validate(article).model_dump() for article in articles]
        return success_response(
            data=article_list,
            message=ResponseMessages.RETRIEVED,
            count=len(article_list),
            metadata={"filtered_by_category": category is not None, "category_filter": category}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve knowledge base articles",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get a specific knowledge base article"""
    try:
      
        articles = db_manager.kb_articles.query(filters={"id": int(article_id)}, limit=1).to_list()
        
        if not articles:
            return error_response(
                message=ResponseMessages.KB_ARTICLE_NOT_FOUND,
                error="Knowledge base article not found",
                error_code=ErrorCodes.KB_ARTICLE_NOT_FOUND
            )
        
        article_data = KnowledgeBaseResponse.model_validate(articles[0]).model_dump()
        return success_response(
            data=article_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"article_id": article_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve knowledge base article",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/search")
async def search_articles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    _: bool = Depends(verify_db_connection)
):
    """Search knowledge base articles using vector similarity"""
    try:
        if not query.strip():
            return error_response(
                message="Search query cannot be empty",
                error="Query parameter is required and cannot be empty",
                error_code=ErrorCodes.BAD_REQUEST
            )
        
        results = await KnowledgeBaseOperations.search_articles(query, category, int(limit))
        
        return success_response(
            data=results,
            message="Knowledge base search completed successfully",
            count=len(results),
            metadata={"query": query, "category_filter": category, "search_limit": limit}
        )
    except Exception as e:
        return error_response(
            message="Knowledge base search failed",
            error=str(e),
            error_code=ErrorCodes.KB_SEARCH_FAILED
        )
