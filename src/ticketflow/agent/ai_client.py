from openai import OpenAI   
from ..config import config

class AIClient:

    def __init__(self):
        self.openrouter_client = OpenAI( 
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL
        )
        self.openai_client = OpenAI( 
            api_key=config.OPENAI_API_KEY,
        )
    @property    
    def can_use_openrouter(self):
        return config.OPENROUTER_API_KEY is not None
    @property
    def chat_client(self):
        return self.openrouter_client if config.OPENROUTER_API_KEY else self.openai_client

