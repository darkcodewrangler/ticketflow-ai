"""
Core AI Agent for TicketFlow - Multi-step intelligent processing
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..database import (
    db_manager, 
    TicketOperations, 
    KnowledgeBaseOperations,
    WorkflowOperations,
    Ticket,
    TicketStatus,
    Priority
)
from .llm_client import LLMClient
from ..external_tools_manager import ExternalToolsManager

logger = logging.getLogger(__name__)

class AgentStep(str, Enum):
    INGEST = "ingest"
    SEARCH_SIMILAR = "search_similar"
    SEARCH_KB = "search_kb"
    ANALYZE = "analyze"
    DECIDE = "decide"
    EXECUTE = "execute"
    FINALIZE = "finalize"

@dataclass
class AgentConfig:
    """Configuration for the AI agent"""
    confidence_threshold: float = 0.85  # Minimum confidence for auto-resolution
    max_similar_tickets: int = 10
    max_kb_articles: int = 5
    enable_auto_resolution: bool = True
    enable_escalation: bool = True
    max_processing_time_ms: int = 30000

class TicketFlowAgent:
    """
    Multi-step AI Agent for intelligent ticket processing
    
    Workflow:
    1. Ingest - Receive and index ticket
    2. Search Similar - Find related resolved cases
    3. Search KB - Find relevant knowledge base articles
    4. Analyze - LLM analysis of context and patterns
    5. Decide - Choose appropriate actions
    6. Execute - Perform selected actions
    7. Finalize - Complete workflow and update metrics
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.llm_client = LLMClient()
        self.external_tools = ExternalToolsManager()
        
    async def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main agent workflow - processes a ticket from start to finish
        
        Args:
            ticket_data: Dictionary containing ticket information
            
        Returns:
            Dictionary with processing results and workflow details
        """
        workflow_start = time.time()
        workflow_id = None
        
        try:
            # Step 1: Ingest ticket
            step_result = await self._step_ingest(ticket_data)
            ticket = step_result["ticket"]
            workflow_id = step_result["workflow_id"]
            
            # Step 2: Search for similar resolved tickets
            similar_cases = await self._step_search_similar(workflow_id, ticket)
            
            # Step 3: Search knowledge base
            kb_articles = await self._step_search_kb(workflow_id, ticket)
            
            # Step 4: LLM analysis
            analysis = await self._step_analyze(workflow_id, ticket, similar_cases, kb_articles)
            
            # Step 5: Decision making
            decisions = await self._step_decide(workflow_id, ticket, analysis)
            
            # Step 6: Execute actions
            execution_results = await self._step_execute(workflow_id, ticket, decisions)
            
            # Step 7: Finalize workflow
            final_result = await self._step_finalize(
                workflow_id, ticket, analysis, execution_results, workflow_start
            )
            
            return {
                "success": True,
                "ticket_id": ticket.id,
                "workflow_id": workflow_id,
                "final_status": final_result["status"],
                "confidence": final_result["confidence"],
                "resolution": final_result.get("resolution"),
                "processing_time_ms": final_result["total_duration_ms"],
                "actions_taken": execution_results
            }
            
        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            
            if workflow_id:
                # Log error in workflow
                await self._log_workflow_error(workflow_id, str(e))
            
            return {
                "success": False,
                "error": str(e),
                "ticket_id": ticket_data.get("title", "Unknown"),
                "workflow_id": workflow_id
            }
    
    async def _step_ingest(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Ingest and index the ticket"""
        step_start = time.time()
        
        # Create ticket (PyTiDB auto-generates embeddings)
        ticket = TicketOperations.create_ticket(ticket_data)
        
        # Create workflow tracking
        initial_step = {
            "step": AgentStep.INGEST.value,
            "status": "completed",
            "message": f"Ticket created with auto-embeddings",
            "data": {
                "ticket_id": ticket.id,
                "title": ticket.title[:50] + "...",
                "category": ticket.category,
                "priority": ticket.priority
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        workflow = WorkflowOperations.create_workflow(ticket.id, [initial_step])
        
        logger.info(f"Agent ingested ticket {ticket.id}")
        
        return {
            "ticket": ticket,
            "workflow_id": workflow.id
        }
    
    async def _step_search_similar(self, workflow_id: int, ticket: Ticket) -> List[Dict]:
        """Step 2: Search for similar resolved tickets"""
        step_start = time.time()
        
        # Use PyTiDB's intelligent search
        search_query = f"{ticket.title} {ticket.description}"
        similar_tickets = TicketOperations.find_similar_tickets(
            search_query, 
            limit=self.config.max_similar_tickets,
            include_filters={"status": TicketStatus.RESOLVED.value}
        )
        
        # Log workflow step
        step_data = {
            "step": AgentStep.SEARCH_SIMILAR.value,
            "status": "completed",
            "message": f"Found {len(similar_tickets)} similar resolved tickets",
            "data": {
                "similar_tickets_count": len(similar_tickets),
                "avg_similarity": sum(t["similarity_score"] for t in similar_tickets) / len(similar_tickets) if similar_tickets else 0,
                "top_similarities": [t["similarity_score"] for t in similar_tickets[:3]]
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent found {len(similar_tickets)} similar tickets for {ticket.id}")
        return similar_tickets
    
    async def _step_search_kb(self, workflow_id: int, ticket: Ticket) -> List[Dict]:
        """Step 3: Search knowledge base articles"""
        step_start = time.time()
        
        # Search KB articles using PyTiDB's hybrid search
        search_query = f"{ticket.title} {ticket.description}"
        kb_articles = KnowledgeBaseOperations.search_articles(
            search_query,
            category=ticket.category,  # Category-specific search
            limit=self.config.max_kb_articles
        )
        
        # Log workflow step
        step_data = {
            "step": AgentStep.SEARCH_KB.value,
            "status": "completed",
            "message": f"Found {len(kb_articles)} relevant KB articles",
            "data": {
                "kb_articles_count": len(kb_articles),
                "avg_relevance": sum(a["similarity_score"] for a in kb_articles) / len(kb_articles) if kb_articles else 0,
                "articles": [{"id": a["article_id"], "title": a["title"][:50]} for a in kb_articles[:3]]
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent found {len(kb_articles)} KB articles for {ticket.id}")
        return kb_articles
    
    async def _step_analyze(self, workflow_id: int, ticket: Ticket, 
                           similar_cases: List[Dict], kb_articles: List[Dict]) -> Dict[str, Any]:
        """Step 4: LLM analysis of ticket context"""
        step_start = time.time()
        
        # Prepare context for LLM analysis
        context = self._prepare_analysis_context(ticket, similar_cases, kb_articles)
        
        # LLM analysis chain
        analysis_tasks = [
            self._analyze_patterns(context),
            self._analyze_root_cause(context),
            self._analyze_solution_options(context),
            self._assess_confidence(context)
        ]
        
        # Execute analysis chain
        pattern_analysis, root_cause, solutions, confidence = await asyncio.gather(*analysis_tasks)
        
        # Combine analysis results
        combined_analysis = {
            "patterns": pattern_analysis,
            "root_cause": root_cause,
            "solutions": solutions,
            "confidence_assessment": confidence,
            "overall_confidence": confidence.get("confidence_score", 0.0)
        }
        
        # Log workflow step
        step_data = {
            "step": AgentStep.ANALYZE.value,
            "status": "completed",
            "message": f"LLM analysis complete (confidence: {combined_analysis['overall_confidence']:.2f})",
            "data": {
                "confidence_score": combined_analysis["overall_confidence"],
                "root_cause": root_cause.get("primary_cause", "Unknown"),
                "solution_count": len(solutions.get("options", [])),
                "analysis_chain_length": len(analysis_tasks)
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent analyzed ticket {ticket.id} (confidence: {combined_analysis['overall_confidence']:.2f})")
        return combined_analysis
    
    async def _step_decide(self, workflow_id: int, ticket: Ticket, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Decision making based on analysis"""
        step_start = time.time()
        
        confidence = analysis["overall_confidence"]
        
        # Decision logic based on confidence and configuration
        if confidence >= self.config.confidence_threshold and self.config.enable_auto_resolution:
            decision = "auto_resolve"
            reasoning = f"High confidence ({confidence:.2f}) warrants automatic resolution"
        elif confidence >= 0.6:
            decision = "escalate_with_context"
            reasoning = f"Medium confidence ({confidence:.2f}) - escalate with analysis context"
        else:
            decision = "escalate_for_review"
            reasoning = f"Low confidence ({confidence:.2f}) - requires human review"
        
        # Prepare action plan
        actions = self._prepare_action_plan(decision, analysis, ticket)
        
        decisions = {
            "primary_decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "actions": actions
        }
        
        # Log workflow step
        step_data = {
            "step": AgentStep.DECIDE.value,
            "status": "completed",
            "message": f"Decision: {decision} ({reasoning})",
            "data": {
                "decision": decision,
                "confidence": confidence,
                "actions_count": len(actions),
                "reasoning": reasoning
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent decided '{decision}' for ticket {ticket.id}")
        return decisions
    
    async def _step_execute(self, workflow_id: int, ticket: Ticket, decisions: Dict[str, Any]) -> List[Dict]:
        """Step 6: Execute decided actions"""
        step_start = time.time()
        
        execution_results = []
        
        for action in decisions["actions"]:
            try:
                result = await self._execute_single_action(action, ticket, decisions)
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
                logger.error(f"Action {action['type']} failed for ticket {ticket.id}: {e}")
        
        # Log workflow step
        step_data = {
            "step": AgentStep.EXECUTE.value,
            "status": "completed",
            "message": f"Executed {len(execution_results)} actions",
            "data": {
                "actions_executed": len(execution_results),
                "success_count": len([r for r in execution_results if r["status"] == "success"]),
                "actions": [r["action"] for r in execution_results]
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent executed {len(execution_results)} actions for ticket {ticket.id}")
        return execution_results
    
    async def _step_finalize(self, workflow_id: int, ticket: Ticket, analysis: Dict[str, Any],
                           execution_results: List[Dict], workflow_start: float) -> Dict[str, Any]:
        """Step 7: Finalize workflow and update metrics"""
        step_start = time.time()
        
        total_duration = int((time.time() - workflow_start) * 1000)
        
        # Determine final status based on execution results
        successful_actions = [r for r in execution_results if r["status"] == "success"]
        
        if any(r["action"] == "resolve_ticket" for r in successful_actions):
            final_status = TicketStatus.RESOLVED.value
        elif any(r["action"] == "escalate_ticket" for r in successful_actions):
            final_status = TicketStatus.ESCALATED.value
        else:
            final_status = TicketStatus.PROCESSING.value
        
        # Update workflow completion
        WorkflowOperations.complete_workflow(
            workflow_id,
            final_confidence=analysis["overall_confidence"],
            total_duration_ms=total_duration
        )
        
        # Log final step
        step_data = {
            "step": AgentStep.FINALIZE.value,
            "status": "completed",
            "message": f"Workflow completed - final status: {final_status}",
            "data": {
                "final_status": final_status,
                "total_duration_ms": total_duration,
                "confidence": analysis["overall_confidence"],
                "successful_actions": len(successful_actions)
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent finalized ticket {ticket.id} - status: {final_status}")
        
        return {
            "status": final_status,
            "confidence": analysis["overall_confidence"],
            "total_duration_ms": total_duration,
            "resolution": execution_results
        }
    
    def _prepare_analysis_context(self, ticket: Ticket, similar_cases: List[Dict], 
                                kb_articles: List[Dict]) -> Dict[str, Any]:
        """Prepare context for LLM analysis"""
        return {
            "ticket": {
                "title": ticket.title,
                "description": ticket.description,
                "category": ticket.category,
                "priority": ticket.priority,
                "user_type": ticket.user_type
            },
            "similar_cases": similar_cases[:5],  # Top 5 most similar
            "kb_articles": kb_articles[:3],      # Top 3 most relevant
            "context_stats": {
                "similar_cases_count": len(similar_cases),
                "kb_articles_count": len(kb_articles),
                "avg_similarity": sum(t["similarity_score"] for t in similar_cases) / len(similar_cases) if similar_cases else 0
            }
        }
    
    def _prepare_action_plan(self, decision: str, analysis: Dict[str, Any], ticket: Ticket) -> List[Dict]:
        """Prepare list of actions based on decision"""
        actions = []
        
        if decision == "auto_resolve":
            # Automatic resolution actions
            resolution_text = analysis["solutions"].get("recommended_solution", "Resolution determined by AI analysis")
            
            actions.extend([
                {
                    "type": "resolve_ticket",
                    "parameters": {
                        "resolution": resolution_text,
                        "confidence": analysis["overall_confidence"]
                    }
                },
                {
                    "type": "notify_user",
                    "parameters": {
                        "message": "Your ticket has been resolved automatically",
                        "resolution": resolution_text
                    }
                },
                {
                    "type": "update_kb_usage",
                    "parameters": {
                        "articles_used": [a["article_id"] for a in analysis.get("kb_articles", [])]
                    }
                }
            ])
            
        elif decision == "escalate_with_context":
            # Escalation with context
            actions.extend([
                {
                    "type": "escalate_ticket",
                    "parameters": {
                        "reason": "Medium confidence - requires human review",
                        "context": analysis,
                        "suggested_priority": "high" if ticket.priority == Priority.URGENT.value else "medium"
                    }
                },
                {
                    "type": "notify_team",
                    "parameters": {
                        "team": "support",
                        "message": f"Ticket escalated with AI analysis context",
                        "context_summary": analysis["root_cause"].get("summary", "")
                    }
                }
            ])
            
        else:  # escalate_for_review
            actions.extend([
                {
                    "type": "escalate_ticket",
                    "parameters": {
                        "reason": "Low confidence - requires manual review",
                        "priority": "high"
                    }
                },
                {
                    "type": "notify_team",
                    "parameters": {
                        "team": "senior_support",
                        "message": f"Complex ticket requires senior review"
                    }
                }
            ])
        
        return actions
    
    async def _execute_single_action(self, action: Dict, ticket: Ticket, context: Dict) -> Dict:
        """Execute a single action"""
        action_type = action["type"]
        params = action["parameters"]
        
        if action_type == "resolve_ticket":
            return await self._resolve_ticket_action(ticket.id, params)
        elif action_type == "escalate_ticket":
            return await self._escalate_ticket_action(ticket.id, params)
        elif action_type == "notify_user":
            return await self._notify_user_action(ticket, params)
        elif action_type == "notify_team":
            return await self._notify_team_action(ticket, params)
        elif action_type == "update_kb_usage":
            return await self._update_kb_usage_action(params)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _resolve_ticket_action(self, ticket_id: int, params: Dict) -> Dict:
        """Resolve ticket action"""
        resolved_ticket = TicketOperations.resolve_ticket(
            ticket_id,
            resolution=params["resolution"],
            resolved_by="ticketflow_agent",
            confidence=params.get("confidence", 0.0)
        )
        
        return {
            "ticket_id": ticket_id,
            "status": "resolved",
            "resolution": params["resolution"]
        }
    
    async def _escalate_ticket_action(self, ticket_id: int, params: Dict) -> Dict:
        """Escalate ticket action"""
        updates = {
            "status": TicketStatus.ESCALATED.value,
            "ticket_metadata": {
                "escalation_reason": params["reason"],
                "escalation_context": params.get("context", {}),
                "escalated_by": "ticketflow_agent",
                "escalated_at": datetime.utcnow().isoformat()
            }
        }
        
        TicketOperations.update_ticket(ticket_id, updates)
        
        return {
            "ticket_id": ticket_id,
            "status": "escalated",
            "reason": params["reason"]
        }
    
    async def _notify_user_action(self, ticket: Ticket, params: Dict) -> Dict:
        """Notify user action"""
        # In a real implementation, this would send email/SMS
        return {
            "notification_type": "user",
            "recipient": ticket.user_email,
            "message": params["message"],
            "status": "sent"
        }
    
    async def _notify_team_action(self, ticket: Ticket, params: Dict) -> Dict:
        """Notify team action"""
        # In a real implementation, this would send Slack/email to team
        return {
            "notification_type": "team",
            "team": params["team"],
            "message": params["message"],
            "ticket_id": ticket.id,
            "status": "sent"
        }
    
    async def _update_kb_usage_action(self, params: Dict) -> Dict:
        """Update KB article usage statistics"""
        updated_articles = []
        for article_id in params.get("articles_used", []):
            KnowledgeBaseOperations.update_article_usage(article_id, was_helpful=True)
            updated_articles.append(article_id)
        
        return {
            "articles_updated": updated_articles,
            "status": "completed"
        }
    
    # LLM Analysis Methods (simplified versions)
    async def _analyze_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in similar cases"""
        prompt = f"""
        Analyze patterns in these similar support cases:
        
        Current Issue: {context['ticket']['title']} - {context['ticket']['description']}
        
        Similar Resolved Cases: {context['similar_cases'][:3]}
        
        Identify common patterns, root causes, and successful resolution approaches.
        Return JSON with: patterns_found, common_causes, success_patterns
        """
        
        # Simulate LLM call - in reality would call actual LLM
        return {
            "patterns_found": ["authentication_issue", "email_delivery"],
            "common_causes": ["spam_filter", "expired_tokens"],
            "success_patterns": ["whitelist_domain", "token_refresh"]
        }
    
    async def _analyze_root_cause(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze root cause"""
        return {
            "primary_cause": "email_delivery_issue",
            "confidence": 0.85,
            "supporting_evidence": ["similar_cases", "kb_articles"]
        }
    
    async def _analyze_solution_options(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze solution options"""
        return {
            "recommended_solution": "Check spam folder and whitelist our domain",
            "alternative_solutions": ["Manual password reset", "Account verification"],
            "confidence": 0.88
        }
    
    async def _assess_confidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall confidence"""
        return {
            "confidence_score": 0.87,
            "factors": {
                "similar_cases_quality": 0.9,
                "kb_coverage": 0.8,
                "pattern_clarity": 0.9
            }
        }
    
    async def _log_workflow_error(self, workflow_id: int, error_message: str):
        """Log workflow error"""
        step_data = {
            "step": "error",
            "status": "failed",
            "message": f"Workflow failed: {error_message}",
            "error": error_message
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)