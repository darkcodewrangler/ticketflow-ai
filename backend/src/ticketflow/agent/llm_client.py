"""
LLM Client for TicketFlow AI Agent
Handles communication with language models for analysis and decision making
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional


from ticketflow.agent.ai_client import AIClient

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for LLM interactions using Jina AI or other providers
    Handles analysis, decision making, and text generation
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.chat_client = self.ai_client.chat_client
        self.model ='openai/gpt-4o' if self.ai_client.can_use_openrouter else 'gpt-4o'
        self.response_format = {"type": "json_object"}
        
    async def analyze_ticket_patterns(self, ticket_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patterns in ticket and similar cases
        """
        prompt = self._build_pattern_analysis_prompt(ticket_context)
        
        try:
            response = await self._make_llm_request(prompt, max_tokens=500)
            return self._parse_json_response(response, "pattern_analysis")
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return self._fallback_pattern_analysis(ticket_context)
    
    async def analyze_root_cause(self, ticket_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine root cause of the issue
        """
        prompt = self._build_root_cause_prompt(ticket_context)
        
        try:
            response = await self._make_llm_request(prompt, max_tokens=300)
            return self._parse_json_response(response, "root_cause")
        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}")
            return self._fallback_root_cause_analysis(ticket_context)
    
    async def generate_solution(self, ticket_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solution recommendations
        """
        prompt = self._build_solution_prompt(ticket_context)
        
        try:
            response = await self._make_llm_request(prompt, max_tokens=600)
            return self._parse_json_response(response, "solution")
        except Exception as e:
            logger.error(f"Solution generation failed: {e}")
            return self._fallback_solution(ticket_context)
    
    async def assess_confidence(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess confidence in the analysis and solution
        """
        prompt = self._build_confidence_prompt(analysis_results)
        
        try:
            response = await self._make_llm_request(prompt, max_tokens=200)
            return self._parse_json_response(response, "confidence")
        except Exception as e:
            logger.error(f"Confidence assessment failed: {e}")
            return self._fallback_confidence_assessment()
    
    def _build_pattern_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for pattern analysis"""
        ticket = context["ticket"]
        similar_cases = context.get("similar_cases", [])[:3]
        
        similar_cases_text = ""
        if similar_cases:
            for i, case in enumerate(similar_cases, 1):
                similar_cases_text += f"Case {i}: {case['title']} -> {case['resolution'][:100]}...\n"
        
        return f"""
        Analyze this support ticket and identify patterns from similar resolved cases.
        
        CURRENT TICKET:
        Title: {ticket['title']}
        Description: {ticket['description']}
        Category: {ticket['category']}
        Priority: {ticket['priority']}
        
        SIMILAR RESOLVED CASES:
        {similar_cases_text if similar_cases_text else "No similar cases found"}
        
        Analyze and respond in JSON format:
        {{
            "patterns_identified": ["list", "of", "patterns"],
            "common_issues": ["issue1", "issue2"],
            "resolution_patterns": ["pattern1", "pattern2"],
            "confidence": 0.85
        }}
        """
    
    
    def _build_root_cause_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for root cause analysis"""
        ticket = context["ticket"]
        kb_articles = context.get("kb_articles", [])[:2]
        
        kb_context = ""
        if kb_articles:
            for article in kb_articles:
                kb_context += f"- {article['title']}: {article['summary'][:100]}...\n"
        
        return f"""
        Determine the root cause of this support issue using available knowledge.
        
        TICKET:
        Title: {ticket['title']}
        Description: {ticket['description']}
        Category: {ticket['category']}
        
        KNOWLEDGE BASE CONTEXT:
        {kb_context if kb_context else "No relevant articles found"}
        
        Analyze and respond in JSON format:
        {{
            "primary_cause": "most likely root cause",
            "secondary_causes": ["cause1", "cause2"],
            "confidence": 0.80,
            "evidence": ["evidence1", "evidence2"],
            "category": "technical|user_error|system_issue"
        }}
        """
    
    def _build_solution_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for solution generation"""
        ticket = context["ticket"]
        similar_cases = context.get("similar_cases", [])[:2]
        kb_articles = context.get("kb_articles", [])[:2]
        
        solutions_context = ""
        if similar_cases:
            solutions_context += "SUCCESSFUL RESOLUTIONS:\n"
            for case in similar_cases:
                solutions_context += f"- {case['resolution'][:150]}...\n"
        
        if kb_articles:
            solutions_context += "\nKNOWLEDGE BASE SOLUTIONS:\n"
            for article in kb_articles:
                solutions_context += f"- {article['title']}: {article['content'][:200]}...\n"
        
        return f"""
        Generate solution recommendations for this support ticket.
        
        TICKET:
        Title: {ticket['title']}
        Description: {ticket['description']}
        Priority: {ticket['priority']}
        
        {solutions_context}
        
        Provide solution in JSON format:
        {{
            "recommended_solution": "detailed step-by-step solution",
            "alternative_solutions": ["solution1", "solution2"],
            "urgency_level": "low|medium|high|critical",
            "estimated_resolution_time": "time estimate",
            "confidence": 0.90
        }}
        """
    
    def _build_confidence_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Build prompt for confidence assessment"""
        return f"""
        Assess the confidence level of this analysis based on available evidence.
        
        ANALYSIS RESULTS:
        Pattern Analysis: {analysis_results.get('patterns', {})}
        Root Cause: {analysis_results.get('root_cause', {})}
        Solution: {analysis_results.get('solution', {})}
        
        Evaluate and respond in JSON format:
        {{
            "overall_confidence": 0.85,
            "confidence_factors": {{
                "pattern_clarity": 0.90,
                "evidence_strength": 0.80,
                "solution_viability": 0.85
            }},
            "risk_assessment": "low|medium|high",
            "recommendation": "auto_resolve|escalate_with_context|manual_review"
        }}
        """
    
    async def _make_llm_request(self, prompt: str, max_tokens: int = 500) -> str:
        """Make request to LLM API"""
        if not self.chat_client:
            raise Exception("No LLM API key configured")
        completion= self.chat_client.chat.completions.create(
            extra_headers={
    "HTTP-Referer": "https://ticketflow.ai", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "TicketFlow AI", # Optional. Site title for rankings on openrouter.ai.
  },
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an AI assistant specializing in technical support analysis. Always respond with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=self.response_format,
            max_tokens=max_tokens,
            temperature=0.3
        )

        if completion.choices[0].message.content:
            return completion.choices[0].message.content
        elif completion.choices[0].message.refusal:
            raise Exception(f"LLM API error: {completion.choices[0].message.refusal}")    
        else:
            raise Exception(f"LLM API error: {completion.choices[0].message.refusal}")
    
    def _parse_json_response(self, response: str, response_type: str) -> Dict[str, Any]:
        """Parse JSON response with fallback"""
        try:
            # Try to parse as JSON
            parsed = json.loads(response.strip())
            return parsed
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback based on response type
            logger.warning(f"Failed to parse LLM JSON response for {response_type}")
            return self._get_fallback_response(response_type)
    
    def _get_fallback_response(self, response_type: str) -> Dict[str, Any]:
        """Get fallback response when parsing fails"""
        fallbacks = {
            "pattern_analysis": {
                "patterns_identified": ["general_support_issue"],
                "common_issues": ["user_configuration"],
                "resolution_patterns": ["standard_troubleshooting"],
                "confidence": 0.5
            },
            "root_cause": {
                "primary_cause": "requires_further_investigation",
                "secondary_causes": ["user_error", "system_issue"],
                "confidence": 0.4,
                "evidence": ["insufficient_data"],
                "category": "system_issue"
            },
            "solution": {
                "recommended_solution": "Please contact support for personalized assistance",
                "alternative_solutions": ["Check documentation", "Restart service"],
                "urgency_level": "medium",
                "estimated_resolution_time": "2-4 hours",
                "confidence": 0.3
            },
            "confidence": {
                "overall_confidence": 0.4,
                "confidence_factors": {
                    "pattern_clarity": 0.4,
                    "evidence_strength": 0.4,
                    "solution_viability": 0.4
                },
                "risk_assessment": "high",
                "recommendation": "manual_review"
            }
        }
        return fallbacks.get(response_type, {"error": "unknown_response_type"})
    
    # Fallback methods for when LLM is unavailable
    def _fallback_pattern_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern analysis"""
        ticket = context["ticket"]
        category = ticket["category"]
        
        patterns = {
            "account": ["authentication", "access_control"],
            "billing": ["payment_processing", "subscription"],
            "technical": ["integration", "configuration"]
        }.get(category, ["general_support"])
        
        return {
            "patterns_identified": patterns,
            "common_issues": [f"{category}_related"],
            "resolution_patterns": ["standard_procedure"],
            "confidence": 0.6
        }
    
    def _fallback_root_cause_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback root cause analysis"""
        ticket = context["ticket"]
        
        return {
            "primary_cause": f"{ticket['category']}_issue",
            "secondary_causes": ["configuration", "user_error"],
            "confidence": 0.5,
            "evidence": ["ticket_category", "description_keywords"],
            "category": "system_issue"
        }
    
    def _fallback_solution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback solution generation"""
        return {
            "recommended_solution": "Standard troubleshooting procedure recommended",
            "alternative_solutions": ["Contact support", "Check documentation"],
            "urgency_level": "medium",
            "estimated_resolution_time": "1-2 hours",
            "confidence": 0.4
        }
    
    def _fallback_confidence_assessment(self) -> Dict[str, Any]:
        """Fallback confidence assessment"""
        return {
            "overall_confidence": 0.4,
            "confidence_factors": {
                "pattern_clarity": 0.4,
                "evidence_strength": 0.4,
                "solution_viability": 0.4
            },
            "risk_assessment": "medium",
            "recommendation": "escalate_with_context"
        }