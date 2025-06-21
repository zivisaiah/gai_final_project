from typing import Dict, List, Optional, Tuple, Any
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        from langchain.chat_models import ChatOpenAI

try:
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older langchain versions
    from langchain.schema import SystemMessage, HumanMessage, AIMessage

from pydantic import BaseModel
import json
import logging

class ExitDecision(BaseModel):
    """Model for exit advisor's decision"""
    should_exit: bool
    confidence: float
    reason: str
    farewell_message: Optional[str] = None

class ExitAdvisor:
    """Agent responsible for detecting conversation end scenarios using pure LLM analysis"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.3,
        memory: Optional[any] = None  # Keep for compatibility but not used
    ):
        """Initialize the Exit Advisor agent
        
        Args:
            model_name: The OpenAI model to use
            temperature: Model temperature (lower for more consistent decisions)
            memory: Optional conversation memory (kept for compatibility)
        """
        # Import settings here to avoid circular imports
        from config.phase1_settings import settings
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Use configuration-based model selection if not explicitly provided
        if model_name is None:
            model_name = settings.get_exit_advisor_model()
            
        self.model_name = model_name
        self.is_fine_tuned = model_name.startswith("ft:") if model_name else False
        
        # Initialize ChatOpenAI with safe temperature handling
        self.llm = self._create_safe_llm(model_name, temperature)
        
        self.logger.info(f"Exit Advisor initialized with model: {model_name}")

    def _create_safe_llm(self, model_name: str, temperature: float) -> ChatOpenAI:
        """Create ChatOpenAI instance with safe temperature handling"""
        try:
            # Try with the requested temperature first
            return ChatOpenAI(
                model_name=model_name,
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

    def _create_exit_analysis_prompt(self, current_message: str, conversation_history: List[Dict[str, str]]) -> str:
        """Create a comprehensive prompt for LLM-based exit analysis"""
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{'Assistant' if msg.get('role') == 'assistant' else 'User'}: {msg.get('content', '')}"
                for msg in conversation_history[-8:]  # Last 8 messages for context
            ])
        
        prompt = f"""You are an Expert Exit Detection Agent for a recruitment conversation system.

**CRITICAL INSTRUCTION: You must always respond in English only. Never use any other language.**

Your task is to analyze whether a recruitment conversation should END or CONTINUE based on the user's latest message and conversation context.

**CONVERSATION CONTEXT:**
{history_text}

**LATEST USER MESSAGE:**
{current_message}

**ANALYSIS GUIDELINES:**

DO **END** the conversation when you detect:
1. **Clear Disinterest**: User explicitly states they're not interested, have found another job, or want to pass
2. **Polite Decline**: User politely declines or says "no thank you"
3. **Task Completion**: User confirms their needs are fully met and they're ready to conclude
4. **Explicit Goodbye**: User says goodbye, thanks for time, or indicates they need to leave
5. **Topic Change**: User shifts to completely unrelated topics unrelated to job/career

DO **CONTINUE** the conversation when you detect:
1. **Interest Signals**: User expresses interest, curiosity, or engagement ("interested", "sounds good", "tell me more")
2. **Information Sharing**: User shares background, experience, skills, or qualifications
3. **Questions**: User asks about the role, company, process, or next steps
4. **Availability**: User mentions their schedule, availability, or readiness to proceed
5. **Engagement**: User is actively participating in job-related discussion
6. **Scheduling Intent**: User shows willingness to schedule or move forward
7. **Neutral Responses**: Simple acknowledgments or unclear intent

**IMPORTANT CONTEXT UNDERSTANDING:**
- "Thanks" + Interest Signal = CONTINUE (e.g., "Thanks, I'm very interested")
- "Thanks" + Goodbye Signal = END (e.g., "Thanks, that's all I need")
- Questions about role/process = CONTINUE
- Expressing qualifications/experience = CONTINUE
- Simple greetings or acknowledgments = CONTINUE

**RESPONSE FORMAT:**
You must respond with a valid JSON object:
{{
    "should_exit": boolean,
    "confidence": float (0.0-1.0),
    "reason": "Detailed explanation of your decision",
    "farewell_message": "Appropriate goodbye message if should_exit is true, null otherwise"
}}

**EXAMPLES:**
- "Thanks, I'm very interested!" → should_exit: false (interest expressed)
- "Thanks, but I'm not looking right now" → should_exit: true (clear decline)
- "What are the requirements?" → should_exit: false (seeking information)
- "I have 5 years Python experience" → should_exit: false (sharing qualifications)
- "I need to think about it and get back to you" → should_exit: true (postponing decision)

Analyze the conversation carefully and make your decision based on the overall context and user intent."""

        return prompt

    async def analyze_conversation(
        self,
        current_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> ExitDecision:
        """Analyze the conversation and determine if it should end using pure LLM analysis
        
        Args:
            current_message: The latest message from the user
            conversation_history: List of previous messages in the conversation
            
        Returns:
            ExitDecision object containing the decision and reasoning
        """
        try:
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_exit_analysis_prompt(current_message, conversation_history)
            
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