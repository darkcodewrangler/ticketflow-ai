
from ticketflow.config import config
from pytidb.rerankers import Reranker
from typing import Optional

reranker: Optional[Reranker] = None

if config.JINA_API_KEY:
    reranker=Reranker(  
    model_name="jina_ai/jina-reranker-v2-base-multilingual",
    api_key=config.JINA_API_KEY
    )
else:
    reranker=None
    print("JINA_API_KEY not found, reranking disabled")



