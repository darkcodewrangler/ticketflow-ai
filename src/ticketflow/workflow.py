
## Agent Workflow Logic

### **Multi-Step Agent Architecture**


from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from src.ticketflow.vector_search_engine import VectorSearchEngine
from openai import  OpenAIClient
from src.ticketflow.external_tools_manager import ExternalToolsManager
from src.ticketflow.ticket import Ticket, SimilarCase, KBArticle

class WorkflowStep(Enum):
    INGEST = "ingest"
    SEARCH = "search" 
    ANALYZE = "analyze"
    DECIDE = "decide"
    EXECUTE = "execute"
    FINALIZE = "finalize"

@dataclass
class AgentState:
    ticket: Ticket
    similar_cases: List[SimilarCase] = None
    kb_articles: List[KBArticle] = None
    analysis: Dict[str, Any] = None
    confidence_score: float = 0.0
    recommended_actions: List[Dict] = None
    execution_results: List[Dict] = None
    current_step: WorkflowStep = WorkflowStep.INGEST
    step_history: List[Dict] = None



