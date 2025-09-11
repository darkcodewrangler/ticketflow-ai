
from ...config import config
from pytidb.rerankers import Reranker

class OperationsUtils:
    @property
    def reranker():
        if config.JINA_API_KEY:
            return Reranker(
                model_name="jina_ai/jina-reranker-v2-base-multilingual",
                api_key=config.JINA_API_KEY

            )
        else:
            return None
__all__=[
    "OperationsUtils"

]

