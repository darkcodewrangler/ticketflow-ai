
from datetime import datetime
import json
import time
from typing import  Dict
import asyncio
import logging
from src.ticketflow.vector_search_engine import VectorSearchEngine
from openai import OpenAI
from .external_tools_manager import ExternalToolsManager
from .ticket import Ticket
from .workflow import AgentState, WorkflowStep
from .config import config

class SmartTicketFlowAgent:
    def __init__(self):
        self.vector_search = VectorSearchEngine()
        self.llm_model='openai/gpt-4'
        self.llm_client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL
        )
        self.external_tools = ExternalToolsManager()
        self.logger = logging.getLogger(__name__)
        
    async def process_ticket(self, ticket: Ticket) -> AgentResult:
        """Main agent workflow - this is your money shot for the demo"""
        
        state = AgentState(ticket=ticket, step_history=[])
        
        try:
            # Step 1: Ingest & Index the new ticket
            state = await self._step_ingest(state)
            await self._broadcast_step_update(state, "Indexing new ticket...")
            
            # Step 2: Search for similar cases and KB articles
            state = await self._step_search(state)
            await self._broadcast_step_update(state, f"Found {len(state.similar_cases)} similar cases")
            
            # Step 3: LLM Analysis Chain
            state = await self._step_analyze(state)
            await self._broadcast_step_update(state, f"Analysis complete (confidence: {state.confidence_score:.0%})")
            
            # Step 4: Decision Making
            state = await self._step_decide(state)
            await self._broadcast_step_update(state, f"Recommended {len(state.recommended_actions)} actions")
            
            # Step 5: Execute External Actions
            state = await self._step_execute(state)
            await self._broadcast_step_update(state, "Actions executed successfully")
            
            # Step 6: Finalize Resolution
            result = await self._step_finalize(state)
            await self._broadcast_step_update(state, "Ticket processing complete")
            
            return result
            
        except Exception as e:
            await self._handle_workflow_error(state, e)
            raise

    async def _step_ingest(self, state: AgentState) -> AgentState:
        """Step 1: Process and index the incoming ticket"""
        state.current_step = WorkflowStep.INGEST
        start_time = time.time()
        
        # Generate embedding for the ticket
        ticket_embedding = await self.vector_search.generate_embedding(
            f"{state.ticket.title} {state.ticket.description}"
        )
        
        # Store in TiDB with vector
        await self._store_ticket_with_vector(state.ticket, ticket_embedding)
        
        # Extract metadata and classify
        metadata = await self._extract_ticket_metadata(state.ticket)
        state.ticket.metadata = metadata
        
        # Log the step
        state.step_history.append({
            "step": "ingest",
            "duration_ms": (time.time() - start_time) * 1000,
            "data": {"embedding_dimensions": len(ticket_embedding), "metadata": metadata}
        })
        
        return state
    
    async def _step_search(self, state: AgentState) -> AgentState:
        """Step 2: Find similar cases and relevant KB articles"""
        state.current_step = WorkflowStep.SEARCH
        start_time = time.time()
        
        # Parallel search for efficiency
        similar_cases_task = self.vector_search.contextual_search(
            state.ticket, 
            context={"user_history": await self._get_user_history(state.ticket.user_id)}
        )
        
        kb_articles_task = self.vector_search.hybrid_search(
            f"{state.ticket.title} {state.ticket.description}",
            search_type="knowledge_base"
        )
        
        # Execute searches in parallel
        state.similar_cases, kb_results = await asyncio.gather(
            similar_cases_task, 
            kb_articles_task
        )
        
        state.kb_articles = [self._convert_to_kb_article(result) for result in kb_results]
        
        # Log the step
        state.step_history.append({
            "step": "search",
            "duration_ms": (time.time() - start_time) * 1000,
            "data": {
                "similar_cases_found": len(state.similar_cases),
                "kb_articles_found": len(state.kb_articles),
                "avg_similarity_score": np.mean([case.similarity for case in state.similar_cases])
            }
        })
        
        return state
    
    async def _step_analyze(self, state: AgentState) -> AgentState:
        """Step 3: Chain multiple LLM calls for deep analysis"""
        state.current_step = WorkflowStep.ANALYZE
        start_time = time.time()
        
        # Multi-step LLM analysis chain
        
        # Analysis 1: Pattern Recognition
        pattern_analysis = await self._llm_analyze_patterns(state)
        
        # Analysis 2: Root Cause Analysis  
        root_cause_analysis = await self._llm_root_cause_analysis(state, pattern_analysis)
        
        # Analysis 3: Solution Synthesis
        solution_analysis = await self._llm_solution_synthesis(state, pattern_analysis, root_cause_analysis)
        
        # Analysis 4: Confidence Assessment
        confidence_analysis = await self._llm_confidence_assessment(state, solution_analysis)
        
        # Combine all analyses
        state.analysis = {
            "patterns": pattern_analysis,
            "root_cause": root_cause_analysis, 
            "solution": solution_analysis,
            "confidence": confidence_analysis
        }
        
        state.confidence_score = confidence_analysis.get("overall_confidence", 0.0)
        
        # Log the step
        state.step_history.append({
            "step": "analyze", 
            "duration_ms": (time.time() - start_time) * 1000,
            "data": {
                "confidence_score": state.confidence_score,
                "analysis_chain_length": 4,
                "pattern_matches": len(pattern_analysis.get("matches", []))
            }
        })
        
        return state

    async def _llm_analyze_patterns(self, state: AgentState) -> Dict:
        """First LLM call: Identify patterns in similar cases"""
        
        similar_cases_text = "\n\n".join([
            f"Case {i+1}:\nIssue: {case.description}\nResolution: {case.resolution}\nOutcome: {case.outcome}"
            for i, case in enumerate(state.similar_cases[:5])
        ])
        
        prompt = f"""
        Analyze the following support ticket and similar resolved cases to identify patterns:
        
        NEW TICKET:
        Title: {state.ticket.title}
        Description: {state.ticket.description}
        Category: {state.ticket.category}
        Priority: {state.ticket.priority}
        
        SIMILAR RESOLVED CASES:
        {similar_cases_text}
        
        Please analyze:
        1. What common patterns do you see across the similar cases?
        2. What are the typical root causes for this type of issue?
        3. What resolution approaches have been most successful?
        4. Are there any red flags or escalation indicators?
        
        Respond in JSON format with your analysis.
        """
        
        response = await self.llm_client.chat_completion(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.content)

    async def _step_decide(self, state: AgentState) -> AgentState:
        """Step 4: Decide on specific actions to take"""
        state.current_step = WorkflowStep.DECIDE
        start_time = time.time()
        
        # Use analysis to determine actions
        decision_prompt = f"""
        Based on the analysis, decide what actions to take for this ticket:
        
        ANALYSIS SUMMARY:
        Confidence Score: {state.confidence_score:.0%}
        Root Cause: {state.analysis['root_cause'].get('likely_cause')}
        Recommended Solution: {state.analysis['solution'].get('recommended_approach')}
        
        AVAILABLE ACTIONS:
        1. auto_resolve - Automatically resolve with suggested solution
        2. escalate_to_human - Escalate to human agent
        3. request_more_info - Ask customer for additional details
        4. schedule_followup - Schedule a follow-up check
        5. notify_team - Notify relevant team (engineering, sales, etc.)
        6. update_kb - Update knowledge base with new information
        
        Return a JSON array of actions to take, with parameters for each action.
        Only auto-resolve if confidence > 85%.
        """
        
        decision_response = await self.llm_client.chat_completion(
            model=self.llm_model,
            messages=[{"role": "user", "content": decision_prompt}],
            response_format={"type": "json_object"}
        )
        
        state.recommended_actions = json.loads(decision_response.content).get("actions", [])
        
        # Log the step
        state.step_history.append({
            "step": "decide",
            "duration_ms": (time.time() - start_time) * 1000,
            "data": {
                "actions_recommended": len(state.recommended_actions),
                "decision_factors": {
                    "confidence_score": state.confidence_score,
                    "similar_cases_count": len(state.similar_cases),
                    "kb_articles_found": len(state.kb_articles)
                }
            }
        })
        
        return state

    async def _step_execute(self, state: AgentState) -> AgentState:
        """Step 5: Execute the decided actions using external tools"""
        state.current_step = WorkflowStep.EXECUTE
        start_time = time.time()
        
        execution_results = []
        
        for action in state.recommended_actions:
            try:
                result = await self._execute_single_action(action, state)
                execution_results.append({
                    "action": action["type"],
                    "status": "success",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                execution_results.append({
                    "action": action["type"], 
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        state.execution_results = execution_results
        
        # Log the step
        state.step_history.append({
            "step": "execute",
            "duration_ms": (time.time() - start_time) * 1000,
            "data": {
                "actions_executed": len(execution_results),
                "success_count": len([r for r in execution_results if r["status"] == "success"]),
                "failed_count": len([r for r in execution_results if r["status"] == "failed"])
            }
        })
        
        return state
    
    async def _execute_single_action(self, action: Dict, state: AgentState) -> Dict:
        """Execute a single action using appropriate external tool"""
        
        action_type = action["type"]
        
        if action_type == "auto_resolve":
            return await self.external_tools.resolve_ticket(
                ticket_id=state.ticket.id,
                resolution=action["parameters"]["resolution"],
                confidence=state.confidence_score
            )
            
        elif action_type == "escalate_to_human":
            return await self.external_tools.escalate_ticket(
                ticket_id=state.ticket.id,
                reason=action["parameters"]["reason"],
                assigned_agent=action["parameters"].get("agent")
            )
            
        elif action_type == "notify_team":
            return await self.external_tools.send_notification(
                team=action["parameters"]["team"],
                message=action["parameters"]["message"],
                ticket_id=state.ticket.id
            )
            
        # TODO: Add more action types as needed
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _broadcast_step_update(self, state: AgentState, message: str):
        """Send real-time updates to frontend via WebSocket"""
        await self.websocket_manager.broadcast({
            "type": "agent_step_update",
            "ticket_id": state.ticket.id,
            "current_step": state.current_step.value,
            "message": message,
            "confidence_score": state.confidence_score,
            "timestamp": datetime.utcnow().isoformat()
        })
