"""
Exit Advisor Agent for Phase 2 - Conversation Termination Detection

This module implements an intelligent agent that determines when recruitment
conversations should naturally end based on candidate responses and engagement patterns.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config.phase1_settings import get_settings


class ExitDecision(BaseModel):
    """Model for exit advisor's decision"""
    should_exit: bool
    confidence: float
    reason: str
    farewell_message: Optional[str] = None


class ExitAdvisor:
    """Exit Advisor for intelligent conversation termination detection with qualification assessment"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.3,
        memory: Optional[any] = None  # Keep for compatibility but not used
    ):
        """Initialize the Exit Advisor with LLM capabilities"""
        self.settings = get_settings()
        
        # Use provided model or get from settings
        self.model_name = model_name or self.settings.get_exit_advisor_model()
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = self._create_safe_llm(self.model_name, self.temperature)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Exit Advisor initialized with model: {self.model_name}")
    
    def _create_safe_llm(self, model_name: str, temperature: float) -> ChatOpenAI:
        """Create ChatOpenAI instance with safe temperature handling"""
        try:
            # Try with the requested temperature first
            return ChatOpenAI(
                api_key=self.settings.OPENAI_API_KEY,
                model=model_name,
                temperature=temperature
            )
        except Exception as e:
            # If temperature is not supported, try with default temperature (1.0)
            if "temperature" in str(e).lower() and "unsupported" in str(e).lower():
                self.logger.warning(f"Model {model_name} doesn't support temperature {temperature}, using default temperature (1.0)")
                return ChatOpenAI(
                    model_name=model_name,
                    temperature=1.0
                )
            else:
                # Re-raise if it's a different error
                raise e

    def _create_exit_analysis_prompt(self, current_message: str, conversation_history: List[Dict[str, str]], candidate_info: Dict[str, Any] = None) -> str:
        """Create a comprehensive prompt for LLM-based exit analysis including qualification assessment"""
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{'Assistant' if msg.get('role') == 'assistant' else 'User'}: {msg.get('content', '')}"
                for msg in conversation_history[-8:]  # Last 8 messages for context
            ])
        
        # Format candidate information with qualification assessment
        candidate_text = ""
        if candidate_info:
            qualification_assessment = candidate_info.get('qualification_assessment', {})
            candidate_text = f"""
**CANDIDATE PROFILE:**
- Name: {candidate_info.get('name', 'Not provided')}
- Experience: {candidate_info.get('experience', 'Not provided')}
- Interest Level: {candidate_info.get('interest_level', 'Not provided')}
- Current Status: {candidate_info.get('current_status', 'Not provided')}
- **QUALIFICATION STATUS**: {qualification_assessment.get('qualification_status', 'unknown')}
- **EXPERIENCE GAP**: {qualification_assessment.get('experience_gap', 0)} years
- **MEETS REQUIREMENTS**: {qualification_assessment.get('meets_requirements', False)}
"""

        prompt = f"""You are an Expert Exit Detection Agent for a recruitment conversation system.

**CRITICAL INSTRUCTION: You must always respond in English only. Never use any other language.**

Your task is to analyze whether a recruitment conversation should END or CONTINUE based on the user's latest message, conversation context, and candidate qualifications.

**CONVERSATION CONTEXT:**
{history_text}
{candidate_text}
**LATEST USER MESSAGE:**
{current_message}

**ANALYSIS GUIDELINES:**

DO **END** the conversation when you detect:

**1. EXPLICIT DISINTEREST:**
- User explicitly states they're not interested, have found another job, or want to pass
- Polite decline or says "no thank you"
- Explicit goodbye or indicates they need to leave

**2. QUALIFICATION MISMATCH (CRITICAL):**
- Candidate has less experience than required (e.g., 1-2 years vs 3+ years required) 
- Candidate lacks fundamental skills for the position
- Candidate's background doesn't align with job requirements
- After providing honest feedback about qualification gaps, candidate doesn't show additional relevant experience
- **DECISIVE RULE**: If candidate has 1+ year gap in required experience AND no compensating factors mentioned, END conversation

**3. CONVERSATION COMPLETION:**
- User confirms their needs are fully met and they're ready to conclude
- Task completion or natural conversation end

**4. TOPIC DIVERGENCE:**
- User shifts to completely unrelated topics unrelated to job/career

DO **CONTINUE** the conversation when you detect:
1. **Interest Signals**: User expresses interest, curiosity, or engagement
2. **Information Sharing**: User shares background, experience, skills, or qualifications
3. **Questions**: User asks about the role, company, process, or next steps
4. **Availability**: User mentions their schedule, availability, or readiness to proceed
5. **Engagement**: User is actively participating in job-related discussion
6. **Scheduling Intent**: User shows willingness to schedule or move forward
7. **Qualification Clarification**: User provides additional experience that might bridge qualification gaps

**QUALIFICATION ASSESSMENT PRIORITY:**
- **CRITICAL DECISION RULE**: If candidate has 1+ year experience gap AND no compensating factors → END immediately
- If candidate clearly doesn't meet minimum requirements (e.g., 2 years experience for 3+ year position), strongly lean toward END
- If candidate shows additional relevant experience, projects, or skills that might compensate, CONTINUE
- Consider the overall conversation flow - has qualification mismatch been addressed?
- **CRITICAL**: After honest qualification feedback is provided, if candidate doesn't demonstrate additional relevant experience, END conversation
- **DECISIVE APPROACH**: Don't prolong conversations with underqualified candidates unless they show strong compensating factors
- **NEW RULE**: For candidates with 2 years experience vs 3+ required, END unless they mention specific projects, bootcamps, or additional skills

**RESPONSE FORMAT:**
You must respond with a valid JSON object:
{{
    "should_exit": boolean,
    "confidence": float (0.0-1.0),
    "reason": "Detailed explanation of your decision including qualification assessment if relevant",
    "farewell_message": "Appropriate goodbye message if should_exit is true, null otherwise"
}}

**QUALIFICATION-BASED EXIT EXAMPLES:**
- Candidate has 1 year experience, job requires 3+ years, no additional compensating skills → should_exit: true
- Candidate has 2 years experience, job requires 3+ years, no additional compensating skills → should_exit: true  
- Candidate has 1-2 years experience but mentions relevant projects/bootcamp/certifications → should_exit: false
- Candidate asks about requirements after learning they don't meet them → should_exit: false (still engaged)
- Candidate says "I'm available" but has qualification gap and no compensating factors → should_exit: true

Analyze the conversation carefully and make your decision based on the overall context, user intent, AND qualification fit."""

        return prompt

    async def analyze_conversation(
        self,
        current_message: str,
        conversation_history: List[Dict[str, str]],
        candidate_info: Dict[str, Any] = None
    ) -> ExitDecision:
        """Analyze the conversation and determine if it should end using LLM analysis with qualification assessment
        
        Args:
            current_message: The latest message from the user
            conversation_history: List of previous messages in the conversation
            candidate_info: Information about the candidate for qualification assessment
            
        Returns:
            ExitDecision object containing the decision and reasoning
        """
        try:
            # Create comprehensive analysis prompt with qualification assessment
            analysis_prompt = self._create_exit_analysis_prompt(current_message, conversation_history, candidate_info)
            
            # Get LLM analysis
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the JSON response
            try:
                # Clean up the response (remove markdown formatting if present)
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                decision_data = json.loads(response_text)
                
                # Create the exit decision
                decision = ExitDecision(
                    should_exit=decision_data["should_exit"],
                    confidence=decision_data["confidence"],
                    reason=decision_data["reason"],
                    farewell_message=decision_data.get("farewell_message")
                )
                
                self.logger.info(f"Exit analysis: should_exit={decision.should_exit}, confidence={decision.confidence:.2f}, reason={decision.reason}")
                return decision
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Failed to parse LLM response as JSON: {e}. Response: {response_text}")
                
                # Fallback: analyze the response text for decision
                response_lower = response_text.lower()
                
                # Look for explicit decision indicators in the response
                if "should_exit\": true" in response_lower or "should end" in response_lower:
                    should_exit = True
                    confidence = 0.6
                    reason = "LLM indicated conversation should end (fallback parsing)"
                else:
                    should_exit = False
                    confidence = 0.4
                    reason = "LLM response unclear, defaulting to continue (fallback parsing)"
                
                return ExitDecision(
                    should_exit=should_exit,
                    confidence=confidence,
                    reason=reason,
                    farewell_message="Thank you for your time! Feel free to reach out if you have any questions." if should_exit else None
                )
            
        except Exception as e:
            self.logger.error(f"Error in exit analysis: {e}")
            
            # Safe fallback: default to continue conversation
            return ExitDecision(
                should_exit=False,
                confidence=0.2,
                reason=f"Error in analysis, defaulting to continue: {str(e)}",
                farewell_message=None
            )

    def get_farewell_message(self, context: Dict[str, Any]) -> str:
        """Generate an appropriate farewell message based on context
        
        Args:
            context: Dictionary containing conversation context
            
        Returns:
            A personalized farewell message
        """
        # Simple fallback farewell messages
        if context.get("scheduling_completed"):
            return "Great! Your interview has been scheduled. We look forward to meeting you. If you need to make any changes, please let us know. Have a wonderful day!"
        elif context.get("information_provided"):
            return "I'm glad I could provide the information you needed. If you have any more questions, don't hesitate to ask. Have a great day!"
        elif context.get("needs_consideration"):
            return "Thank you for your interest. Take your time to consider the opportunity. When you're ready to proceed, we'll be here. Have a great day!"
        else:
            return "Thank you for your time! If you need anything else, feel free to reach out. Have a great day!" 