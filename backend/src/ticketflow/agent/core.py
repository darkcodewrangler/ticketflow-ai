"""
Core AI Agent for TicketFlow - Multi-step intelligent processing
"""

import asyncio
import time
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from ticketflow.database.models import WorkflowStatus
from ticketflow.database.schemas import TicketResponse

from ticketflow.database import (
    db_manager, 
    TicketOperations, 
    KnowledgeBaseOperations,
    WorkflowOperations,
    TicketStatus,
    Priority
)
from ticketflow.utils.helpers import get_isoformat, get_value
from .llm_client import LLMClient
from ticketflow.external_tools_manager import ExternalToolsManager
from ticketflow.api.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class AgentStep(str, Enum):
    INGEST = "ingest"
    SEARCH_SIMILAR = "search_similar"
    SEARCH_KB = "search_kb"
    ANALYZE = "analyze"
    DECIDE = "decide"
    EXECUTE = "execute"
    VERIFY = "verify"
    FINALIZE = "finalize"

class ResolutionType(str, Enum):
    AUTOMATED = "automated"
    ESCALATED = "escalated"
    MANUAL = "manual"
    PARTIAL = "partial"

class ResolutionOutcome(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_VERIFICATION = "needs_verification"
    ESCALATED = "escalated"


@dataclass
class LearningMetrics:
    """Metrics for tracking agent learning and performance"""
    total_tickets_processed: int = 0
    successful_resolutions: int = 0
    escalations: int = 0
    verification_failures: int = 0
    average_confidence: float = 0.0
    feedback_count: int = 0
    positive_feedback: int = 0
    resolution_patterns: Dict[str, int] = None
    common_failures: Dict[str, int] = None
    
    def __post_init__(self):
        if self.resolution_patterns is None:
            self.resolution_patterns = {}
        if self.common_failures is None:
            self.common_failures = {}


@dataclass
class AgentConfig:
    """Configuration for the AI agent"""
    confidence_threshold: float = 0.85  # Minimum confidence for auto-resolution
    max_similar_tickets: int = 10
    max_kb_articles: int = 5
    enable_auto_resolution: bool = True
    enable_escalation: bool = True
    max_processing_time_ms: int = 30000
    # Verification settings
    enable_verification: bool = True
    verification_threshold: float = 0.9  # Higher threshold for verification
    max_verification_attempts: int = 3
    require_human_verification: bool = False

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
    7. Verify - Verify resolution effectiveness
    8. Finalize - Complete workflow and update metrics
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.llm_client = LLMClient()
        self.external_tools = ExternalToolsManager()
        self.learning_metrics = self._load_learning_data()
        
    def _load_learning_data(self) -> LearningMetrics:
        """Load learning metrics from persistent storage"""
        try:
            learning_file = os.path.join(os.path.dirname(__file__), "learning_data.json")
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    data = json.load(f)
                    return LearningMetrics(**data)
        except Exception as e:
            logger.warning(f"Could not load learning data: {e}")
        return LearningMetrics()
    
    def _save_learning_data(self):
        """Save learning metrics to persistent storage"""
        try:
            learning_file = os.path.join(os.path.dirname(__file__), "learning_data.json")
            with open(learning_file, 'w') as f:
                json.dump(asdict(self.learning_metrics), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save learning data: {e}")
        
    def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
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
            step_result = self._step_ingest(ticket_data)
            ticket = step_result["ticket"]
            workflow_id = step_result["workflow_id"]
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.INGEST.value, "Ticket ingested", {
                        "title": get_value(ticket, 'title'),
                        "category": get_value(ticket, 'category'),
                        "priority": get_value(ticket, 'priority')
                    }
                ))
            except Exception:
                pass
            
            # Step 2: Search for similar resolved tickets
            similar_cases = self._step_search_similar(workflow_id, ticket)
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.SEARCH_SIMILAR.value, f"Found {len(similar_cases)} similar tickets", {
                        "count": len(similar_cases)
                    }
                ))
            except Exception:
                pass
            
            # Step 3: Search knowledge base
            kb_articles = self._step_search_kb(workflow_id, ticket)
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.SEARCH_KB.value, f"Found {len(kb_articles)} KB articles", {
                        "count": len(kb_articles)
                    }
                ))
            except Exception:
                pass
            
            # Step 4: LLM analysis
            analysis = self._step_analyze(workflow_id, ticket, similar_cases, kb_articles)
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.ANALYZE.value, "Analysis complete", {
                        "confidence": analysis.get("overall_confidence")
                    }
                ))
            except Exception:
                pass
            
            # Step 5: Decision making
            decisions = self._step_decide(workflow_id, ticket, analysis)
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.DECIDE.value, f"Decision: {decisions.get('primary_decision')}", {
                        "actions_count": len(decisions.get("actions", [])),
                        "confidence": decisions.get("confidence")
                    }
                ))
            except Exception:
                pass
            
            # Step 6: Execute actions
            execution_results = self._step_execute(workflow_id, ticket, decisions)
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, 'id'), AgentStep.EXECUTE.value, f"Executed {len(execution_results)} actions", {
                        "actions": [r.get("action") for r in execution_results]
                    }
                ))
            except Exception:
                pass
            
            # Step 7: Finalize workflow
            final_result = self._step_finalize(
                workflow_id, ticket, analysis, execution_results, workflow_start
            )
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    ticket.get('id'), AgentStep.FINALIZE.value, "Workflow completed", {
                        "status": final_result.get("status"),
                        "confidence": final_result.get("confidence"),
                        "duration_ms": final_result.get("total_duration_ms")
                    }
                ))
            except Exception:
                pass
            
            return {
                "success": True,
                "ticket_id": get_value(ticket, 'id'),
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
                self._log_workflow_error(workflow_id, str(e))
            try:
                asyncio.run(websocket_manager.send_agent_update(
                    get_value(ticket, "id"), "error", "Agent processing failed", {"error": str(e)}
                ))
            except Exception:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "ticket_id": ticket_data.get("title", "Unknown"),
                "workflow_id": workflow_id
            }
    
    def process_existing_ticket(self, ticket_id: int, workflow_id: int) -> Dict[str, Any]:
        """
        Process an existing ticket that's already in the database
        
        Args:
            ticket_id: ID of the existing ticket
            workflow_id: ID of the workflow tracking this processing
            
        Returns:
            Dictionary with processing results and workflow details
        """
        workflow_start = time.time()
        
        try:
            # Get the existing ticket from database
            tickets = db_manager.tickets.query(filters={"id": int(ticket_id)}, limit=1).to_pydantic()
            
            if not tickets:
                raise ValueError(f"Ticket {ticket_id} not found")

            ticket = TicketResponse.model_validate(tickets[0]).model_dump()
            
            # Step 1: Log that we're processing existing ticket
            step_data = {
                "step": AgentStep.INGEST.value,
                "status": "completed",
                "message": f"Processing existing ticket {ticket_id}",
                "data": {
                    "ticket_id": get_value(ticket, "id"),
                    "title": get_value(ticket, "title")[:50] + "...",
                    "category": get_value(ticket, "category"),
                    "priority": get_value(ticket, "priority")
                },
                "duration_ms": 0
            }
            WorkflowOperations.update_workflow_step(workflow_id, step_data)
            
            # Continue with normal processing steps
            similar_cases = self._step_search_similar(workflow_id, ticket)
            kb_articles = self._step_search_kb(workflow_id, ticket)
            analysis = self._step_analyze(workflow_id, ticket, similar_cases, kb_articles)
            decisions = self._step_decide(workflow_id, ticket, analysis)
            execution_results = self._step_execute(workflow_id, ticket, decisions)
            
            # Verification step
            verification_result = None
            if self.config.enable_verification:
                verification_result = self._step_verify(workflow_id, ticket, analysis, execution_results)
            
            # Finalize
            final_result = self._step_finalize(
                workflow_id, ticket, analysis, execution_results, workflow_start, verification_result
            )
            
            return {
                "success": True,
                "ticket_id": ticket.get('id'),
                "workflow_id": workflow_id,
                "final_status": final_result["status"],
                "confidence": final_result["confidence"],
                "resolution": final_result.get("resolution"),
                "processing_time_ms": final_result["total_duration_ms"],
                "actions_taken": execution_results
            }
            
        except Exception as e:
            logger.error(f"Processing existing ticket failed: {e}")
            
            if workflow_id:
                self._log_workflow_error(workflow_id, str(e))
            
            return {
                "success": False,
                "error": str(e),
                "ticket_id": ticket_id,
                "workflow_id": workflow_id
            }
    
    def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback to improve agent performance"""
        try:
            workflow_id = feedback_data.get("workflow_id")
            resolution_effective = feedback_data.get("resolution_effective", False)
            resolution_rating = feedback_data.get("resolution_rating", 3)
            feedback_text = feedback_data.get("feedback_text", "")
            
            # Update learning metrics
            self.learning_metrics.feedback_count += 1
            if resolution_effective and resolution_rating >= 4:
                self.learning_metrics.positive_feedback += 1
            
            # Extract patterns from feedback
            if feedback_text:
                # Simple pattern extraction - in production, use more sophisticated NLP
                if "slow" in feedback_text.lower():
                    self.learning_metrics.common_failures["slow_response"] = \
                        self.learning_metrics.common_failures.get("slow_response", 0) + 1
                elif "wrong" in feedback_text.lower() or "incorrect" in feedback_text.lower():
                    self.learning_metrics.common_failures["incorrect_solution"] = \
                        self.learning_metrics.common_failures.get("incorrect_solution", 0) + 1
                elif "helpful" in feedback_text.lower() or "good" in feedback_text.lower():
                    self.learning_metrics.resolution_patterns["positive_resolution"] = \
                        self.learning_metrics.resolution_patterns.get("positive_resolution", 0) + 1
            
            # Save updated metrics
            self._save_learning_data()
            
            logger.info(f"Processed feedback for workflow {workflow_id}: effective={resolution_effective}, rating={resolution_rating}")
            
            return {
                "success": True,
                "learning_updated": True,
                "metrics": {
                    "total_feedback": self.learning_metrics.feedback_count,
                    "positive_feedback": self.learning_metrics.positive_feedback,
                    "feedback_ratio": self.learning_metrics.positive_feedback / max(1, self.learning_metrics.feedback_count)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return {
                "success": False,
                "error": str(e),
                "learning_updated": False
            }

    def _step_ingest(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
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
                "ticket_id": get_value(ticket, 'id'),
                "title": get_value(ticket, 'title')[:50] + "...",
                "category": get_value(ticket, 'category'),
                "priority": get_value(ticket, 'priority')
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        workflow =  WorkflowOperations.create_workflow(ticket.id, [initial_step])
        
        logger.info(f"Agent ingested ticket {ticket.id}")
        
        # Convert ticket to dict for consistent handling throughout the workflow
        ticket_dict = TicketResponse.model_validate(ticket).model_dump()
        
        return {
            "ticket": ticket_dict,
            "workflow_id": workflow.id
        }
    
    def _step_search_similar(self, workflow_id: int, ticket: dict) -> List[Dict]:
        """Step 2: Search for similar resolved tickets"""
        step_start = time.time()
        
        # Use intelligent search
        similar_tickets = TicketOperations.find_similar_to_ticket(ticket=ticket,
            limit=self.config.max_similar_tickets,
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
        
        logger.info(f"Agent found {len(similar_tickets)} similar tickets for {ticket.get("id")}")
        return similar_tickets
    
    def _step_search_kb(self, workflow_id: int, ticket: dict) -> List[Dict]:
        """Step 3: Search knowledge base articles"""
        step_start = time.time()
        
        # Search KB articles using PyTiDB's hybrid search
        search_query = f"{get_value(ticket,"title",'')} {get_value(ticket,"description",'')}"
        kb_articles = KnowledgeBaseOperations.search_articles(
            search_query,
            category=get_value(ticket,"category",None),  # Category-specific search
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
        
        logger.info(f"Agent found {len(kb_articles)} KB articles for {ticket.get('id')}")
        return kb_articles
    
    def _step_analyze(self, workflow_id: int, ticket: dict, 
                           similar_cases: List[Dict], kb_articles: List[Dict]) -> Dict[str, Any]:
        """Step 4: LLM analysis of ticket context"""
        step_start = time.time()
        
        # Prepare context for LLM analysis
        context = self._prepare_analysis_context(ticket, similar_cases, kb_articles)
        
        # LLM analysis chain
        pattern_analysis = self._analyze_patterns(context)
        root_cause = self._analyze_root_cause(context)
        solutions = self._analyze_solution_options(context)
        confidence = self._assess_confidence(context)

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
                "analysis_chain_length": 4
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent analyzed ticket {ticket.get('id')} (confidence: {combined_analysis['overall_confidence']:.2f})")
        return combined_analysis
    
    def _step_decide(self, workflow_id: int, ticket: dict, analysis: Dict[str, Any]) -> Dict[str, Any]:
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
        
        logger.info(f"Agent decided '{decision}' for ticket {ticket.get('id')}")
        return decisions
    
    def _step_execute(self, workflow_id: int, ticket: Dict, decisions: Dict[str, Any]) -> List[Dict]:
        """Step 6: Execute decided actions"""
        step_start = time.time()
        
        execution_results = []
        
        for action in decisions["actions"]:
            try:
                result = self._execute_single_action(action, ticket, decisions)
                execution_results.append({
                    "action": action["type"],
                    "status": "success",
                    "result": result,
                    "timestamp": get_isoformat()
                })
            except Exception as e:
                execution_results.append({
                    "action": action["type"],
                    "status": "failed", 
                    "error": str(e),
                    "timestamp": get_isoformat()
                })
                logger.error(f"Action {action['type']} failed for ticket {ticket.get('id')}: {e}")
        
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
        
        logger.info(f"Agent executed {len(execution_results)} actions for ticket {ticket.get('id')}")
        return execution_results
    
    def _step_verify(self, workflow_id: int, ticket: Dict, analysis: Dict[str, Any], execution_results: List[Dict]) -> Dict[str, Any]:
        """Step 7: Verify resolution effectiveness and determine if escalation is needed"""
        step_start = time.time()
        
        # Check if any resolution actions were taken
        resolution_actions = [r for r in execution_results if r["action"] == "resolve_ticket" and r["status"] == "success"]
        
        if not resolution_actions:
            # No resolution to verify
            verification_result = {
                "outcome": ResolutionOutcome.SUCCESS.value,
                "confidence": analysis["overall_confidence"],
                "needs_escalation": False,
                "verification_notes": "No resolution actions to verify"
            }
        else:
            # Perform verification checks
            confidence = analysis["overall_confidence"]
            needs_escalation = self._should_escalate(ticket, analysis, execution_results)
            
            # Determine verification outcome
            if needs_escalation:
                outcome = ResolutionOutcome.ESCALATED.value
            elif confidence >= self.config.verification_threshold:
                outcome = ResolutionOutcome.SUCCESS.value
            elif confidence >= self.config.confidence_threshold:
                outcome = ResolutionOutcome.NEEDS_VERIFICATION.value
            else:
                outcome = ResolutionOutcome.FAILED.value
                needs_escalation = True
            
            verification_result = {
                "outcome": outcome,
                "confidence": confidence,
                "needs_escalation": needs_escalation,
                "verification_notes": f"Confidence: {confidence:.2f}, Threshold: {self.config.verification_threshold}"
            }
        
        # Log verification step
        step_data = {
            "step": AgentStep.VERIFY.value,
            "status": "completed",
            "message": f"Verification complete: {verification_result['outcome']}",
            "data": {
                "outcome": verification_result["outcome"],
                "confidence": verification_result["confidence"],
                "needs_escalation": verification_result["needs_escalation"],
                "resolution_actions_count": len(resolution_actions)
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent verification for ticket {ticket.get('id')}: {verification_result['outcome']}")
        return verification_result
    
    def _should_escalate(self, ticket: Dict, analysis: Dict[str, Any], execution_results: List[Dict]) -> bool:
        """Determine if ticket should be escalated based on various factors"""
        
        # Check confidence threshold
        if analysis["overall_confidence"] < self.config.confidence_threshold:
            return True
        
        # Check for high priority tickets with low confidence
        if ticket.get("priority") == Priority.HIGH.value and analysis["overall_confidence"] < 0.9:
            return True
        
        # Check for failed execution results
        failed_actions = [r for r in execution_results if r["status"] == "failed"]
        if len(failed_actions) > len(execution_results) / 2:  # More than half failed
            return True
        
        # Check for complex issues (multiple similar tickets with different solutions)
        similar_solutions = analysis.get("solution_analysis", {}).get("similar_solutions", [])
        if len(similar_solutions) > 3:  # Too many different approaches found
            return True
        
        return False
    
    def _step_finalize(self, workflow_id: int, ticket: Dict, analysis: Dict[str, Any], execution_results: List[Dict], workflow_start: float, verification_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Step 8: Finalize workflow and update metrics"""
        step_start = time.time()
        
        total_duration = int((time.time() - workflow_start) * 1000)
        
        # Determine final status based on execution results and verification
        successful_actions = [r for r in execution_results if r["status"] == "success"]
        
        # Consider verification result in final status determination
        if verification_result and verification_result.get("needs_escalation"):
            final_status = TicketStatus.ESCALATED.value
        elif any(r["action"] == "resolve_ticket" for r in successful_actions):
            # Check if verification passed for resolution
            if verification_result and verification_result.get("outcome") == ResolutionOutcome.FAILED.value:
                final_status = TicketStatus.PROCESSING.value  # Keep processing if verification failed
            else:
                final_status = TicketStatus.RESOLVED.value
        elif any(r["action"] == "escalate_ticket" for r in successful_actions):
            final_status = TicketStatus.ESCALATED.value
        else:
            final_status = TicketStatus.PROCESSING.value
        
        # Use verification confidence if available, otherwise use analysis confidence
        final_confidence = verification_result.get("confidence", analysis["overall_confidence"]) if verification_result else analysis["overall_confidence"]
        
        # Update learning metrics
        self.learning_metrics.total_tickets_processed += 1
        if final_status == TicketStatus.RESOLVED.value:
            self.learning_metrics.successful_resolutions += 1
        elif final_status == TicketStatus.ESCALATED.value:
            self.learning_metrics.escalations += 1
        if verification_result and verification_result.get("outcome") == ResolutionOutcome.FAILED.value:
            self.learning_metrics.verification_failures += 1
        
        # Update average confidence (running average)
        total_processed = self.learning_metrics.total_tickets_processed
        self.learning_metrics.average_confidence = (
            (self.learning_metrics.average_confidence * (total_processed - 1) + final_confidence) / total_processed
        )
        
        # Save learning data
        self._save_learning_data()
        
        # Update workflow completion
        WorkflowOperations.complete_workflow(
            workflow_id,
            final_confidence=final_confidence,
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
                "confidence": final_confidence,
                "successful_actions": len(successful_actions),
                "verification_outcome": verification_result.get("outcome") if verification_result else None
            },
            "duration_ms": int((time.time() - step_start) * 1000)
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)
        
        logger.info(f"Agent finalized ticket {ticket.get('id')} - status: {final_status}")
        
        return {
            "status": final_status,
            "confidence": analysis["overall_confidence"],
            "total_duration_ms": total_duration,
            "resolution": execution_results
        }
    
    def _prepare_analysis_context(self, ticket: dict, similar_cases: List[Dict], 
                                kb_articles: List[Dict]) -> Dict[str, Any]:
        """Prepare context for LLM analysis"""
        return {
            "ticket": {
                "title": ticket.get("title"),
                "description": ticket.get("description"),
                "category": ticket.get("category"),
                "priority": ticket.get("priority"),
                "user_type": ticket.get("user_type")
            },
            "similar_cases": similar_cases[:5],  # Top 5 most similar
            "kb_articles": kb_articles[:3],      # Top 3 most relevant
            "context_stats": {
                "similar_cases_count": len(similar_cases),
                "kb_articles_count": len(kb_articles),
                "avg_similarity": sum(t["similarity_score"] for t in similar_cases) / len(similar_cases) if similar_cases else 0
            }
        }
    
    def _prepare_action_plan(self, decision: str, analysis: Dict[str, Any], ticket: Dict) -> List[Dict]:
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
                        "suggested_priority": "high" if ticket.get("priority") == Priority.URGENT.value else "medium"
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
    
    def _execute_single_action(self, action: Dict, ticket: Dict, context: Dict) -> Dict:
        """Execute a single action"""
        action_type = action["type"]
        params = action["parameters"]
        
        if action_type == "resolve_ticket":
            return self._resolve_ticket_action(ticket.get("id"), params)
        elif action_type == "escalate_ticket":
            return self._escalate_ticket_action(ticket.get("id"), params)
        elif action_type == "notify_user":
            return self._notify_user_action(ticket, params)
        elif action_type == "notify_team":
            return self._notify_team_action(ticket, params)
        elif action_type == "update_kb_usage":
            return self._update_kb_usage_action(params)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _resolve_ticket_action(self, ticket_id: int, params: Dict) -> Dict:
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
    
    def _escalate_ticket_action(self, ticket_id: int, params: Dict) -> Dict:
        """Escalate ticket action"""
        updates = {
            "status": TicketStatus.ESCALATED.value,
            "ticket_metadata": {
                "escalation_reason": params["reason"],
                "escalation_context": params.get("context", {}),
                "escalated_by": "ticketflow_agent",
                "escalated_at": get_isoformat()
            }
        }
        
        TicketOperations.update_ticket(ticket_id, updates)

        
        return {
            "ticket_id": ticket_id,
            "status": "escalated",
            "reason": params["reason"]
        }
    
    def _notify_user_action(self, ticket: Dict, params: Dict) -> Dict:
        """Notify user action using Resend"""
        try:
            # Create HTML email template
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">TicketFlow AI Update</h2>
                <p>Hello,</p>
                <p>{params["message"]}</p>
                <p><strong>Ticket ID:</strong> {ticket.get("id")}</p>
                <p><strong>Subject:</strong> {ticket.get("title")}</p>
                {f'<p><strong>Resolution:</strong> {params.get("resolution", "")}</p>' if params.get("resolution") else ""}
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">.
                    This is an automated message from TicketFlow AI. 
                    If you have any questions, please contact our support team.
                </p>
            </body>
            </html>
            """
            # user_email=ticket.get("user_email")
            # TODO: Replace this email with actual user email
            user_email="luckyvictory54@gmail.com"

            # Send email using external tools manager
            result = self.external_tools.send_email_notification(
                recipient=user_email,
                subject=f"Ticket #{ticket.get("id")} Update - {ticket.get("title")}",
                body=params["message"],
                html_body=html_body
            )
            
            return {
                "notification_type": "user",
                "recipient": user_email,
                "message": params["message"],
                "status": result.get("status", "failed"),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"User notification failed: {e}")
            return {
                "notification_type": "user",
                "recipient": user_email  ,
                "message": params["message"],
                "status": "failed",
                "error": str(e)
            }
    
    def _notify_team_action(self, ticket: Dict, params: Dict) -> Dict:
        """Notify team action using Slack and email"""
        try:
            # Send Slack notification
            slack_result =asyncio.run(self.external_tools.send_slack_notification(
                channel=f"#{params['team']}",
                message=f"🚨 {params['message']}\nTicket: #{ticket.get("id")} - {ticket.get("title")}",
                ticket_id=ticket.get('id')
            ))
            
            # Send email to team (using a team email address)
            email_result = self.external_tools.send_email_notification(
              
                subject=f"Ticket #{ticket.get("id")} Escalated - {ticket.get("title")   }",
                content=f"""
                {params['message']}
                
                Ticket Details:
                - ID: {ticket.get("id")}
                - Title: {ticket.get("title")}
                - Category: {ticket.get("category")}
                - Priority: {ticket.get("priority") }
                - User: {ticket.get("user_email")}
                
                Please review and take appropriate action.
                """
            )
            
            return {
                "notification_type": "team",
                "team": params["team"],
                "message": params["message"],
                "ticket_id": ticket.get("id"),
                "slack_status": slack_result.get("status", "failed"),
                "email_status": email_result.get("status", "failed"),
                "slack_message_id": slack_result.get("message_id"),
                "email_message_id": email_result.get("message_id")
            }
            
        except Exception as e:
            logger.error(f"Team notification failed: {e}")
            return {
                "notification_type": "team",
                "team": params["team"],
                "message": params["message"],
                "ticket_id": ticket.get("id"),
                "status": "failed",
                "error": str(e)
            }
    
    def _update_kb_usage_action(self, params: Dict) -> Dict:
        """Update KB article usage statistics"""
        updated_articles = []
        for article_id in params.get("articles_used", []):
            KnowledgeBaseOperations.update_article_usage(article_id, was_helpful=True)
            updated_articles.append(article_id)
        
        return {
            "articles_updated": updated_articles,
            "status": "completed"
        }
    
    # LLM Analysis Methods implementations
    def _analyze_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in similar cases using LLM"""
        try:
            return self.llm_client.analyze_ticket_patterns(context)
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            # Fallback to basic analysis
            return {
                "patterns_found": ["general_issue"],
                "common_causes": ["unknown"],
                "success_patterns": ["manual_review"]
            }
    
    def _analyze_root_cause(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze root cause using LLM"""
        try:
            return self.llm_client.analyze_root_cause(context)
        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}")
            # Fallback to basic analysis
            return {
                "primary_cause": "unknown_issue",
                "confidence": 0.5,
                "supporting_evidence": ["limited_context"]
            }
    
    def _analyze_solution_options(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze solution options using LLM"""
        try:
            return self.llm_client.generate_solution(context)
        except Exception as e:
            logger.error(f"Solution analysis failed: {e}")
            # Fallback to basic analysis
            return {
                "recommended_solution": "Please contact support for assistance",
                "alternative_solutions": ["Manual review required"],
                "confidence": 0.5
            }
    
    def _assess_confidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall confidence using LLM"""
        try:
            # Combine all analysis results for confidence assessment
            analysis_results = {
                "patterns": context.get("patterns", {}),
                "root_cause": context.get("root_cause", {}),
                "solutions": context.get("solutions", {}),
                "similar_cases_count": len(context.get("similar_cases", [])),
                "kb_articles_count": len(context.get("kb_articles", []))
            }
            return self.llm_client.assess_confidence(analysis_results)
        except Exception as e:
            logger.error(f"Confidence assessment failed: {e}")
            # Fallback to basic confidence calculation
            similar_cases_count = len(context.get("similar_cases", []))
            kb_articles_count = len(context.get("kb_articles", []))
            
            # Simple confidence calculation based on available data
            confidence = min(0.9, 0.3 + (similar_cases_count * 0.1) + (kb_articles_count * 0.05))
            
            return {
                "confidence_score": confidence,
                "factors": {
                    "similar_cases_quality": min(0.9, similar_cases_count * 0.2),
                    "kb_coverage": min(0.9, kb_articles_count * 0.3),
                    "pattern_clarity": 0.5
                }
            }
    
    def _log_workflow_error(self, workflow_id: int, error_message: str):
        """Log workflow error"""
        step_data = {
            "step": "error",
            "status":WorkflowStatus.FAILED.value,
            "message": f"Workflow failed: {error_message}",
            "error": error_message
        }
        
        WorkflowOperations.update_workflow_step(workflow_id, step_data)