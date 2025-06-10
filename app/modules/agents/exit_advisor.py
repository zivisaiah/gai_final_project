from typing import Dict, List, Optional, Tuple, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        from langchain.chat_models import ChatOpenAI

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older langchain versions
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.schema import SystemMessage, HumanMessage, AIMessage

from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from pydantic import BaseModel
import json
import re

from ..prompts.exit_prompts import (
    EXIT_DETECTION_TEMPLATE,
    get_farewell_template,
    CONFIDENCE_THRESHOLDS,
    EXIT_SIGNALS
)

class ExitDecision(BaseModel):
    """Model for exit advisor's decision"""
    should_exit: bool
    confidence: float
    reason: str
    farewell_message: Optional[str] = None

class ExitAdvisor:
    """Agent responsible for detecting conversation end scenarios"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        memory: Optional[ConversationBufferMemory] = None
    ):
        """Initialize the Exit Advisor agent
        
        Args:
            model_name: The OpenAI model to use
            temperature: Model temperature (lower for more consistent decisions)
            memory: Optional conversation memory
        """
        # Import settings here to avoid circular imports
        from config.phase1_settings import settings
        
        # Use configuration-based model selection if not explicitly provided
        if model_name is None:
            model_name = settings.get_exit_advisor_model()
            
        self.model_name = model_name
        self.is_fine_tuned = model_name.startswith("ft:") if model_name else False
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            return_messages=True
        )
        
        # Store conversation history for tool access
        self.current_conversation_history = []
        
        # Initialize tools for exit detection
        self.tools = self._create_tools()
        
        # Initialize the agent
        self._initialize_agent()

    def _create_tools(self) -> List[Tool]:
        """Create tools for exit detection"""
        return [
            Tool(
                name="check_explicit_exit",
                func=self._check_explicit_exit,
                description="Check if the message contains explicit exit signals"
            ),
            Tool(
                name="check_implicit_exit",
                func=self._check_implicit_exit,
                description="Check if the message contains implicit exit signals"
            ),
            Tool(
                name="analyze_conversation_context",
                func=self._analyze_conversation_context_wrapper,
                description="Analyze the conversation context for exit signals"
            )
        ]

    def _check_explicit_exit(self, message: str) -> Dict[str, Any]:
        """Check for explicit exit signals in the message"""
        message_lower = message.lower()
        found_signals = [
            signal for signal in EXIT_SIGNALS["explicit"]
            if signal in message_lower
        ]
        return {
            "has_explicit_exit": len(found_signals) > 0,
            "found_signals": found_signals,
            "confidence": 0.9 if found_signals else 0.0
        }

    def _check_implicit_exit(self, message: str) -> Dict[str, Any]:
        """Check for implicit exit signals in the message"""
        message_lower = message.lower()
        found_signals = [
            signal for signal in EXIT_SIGNALS["implicit"]
            if signal in message_lower
        ]
        return {
            "has_implicit_exit": len(found_signals) > 0,
            "found_signals": found_signals,
            "confidence": 0.7 if found_signals else 0.0
        }

    def _analyze_conversation_context(
        self,
        current_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze the conversation context for exit signals"""
        # Check if the conversation has reached a natural conclusion
        last_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        # Check for task completion signals
        task_completion_phrases = [
            "scheduled", "booked", "confirmed", "completed",
            "finished", "done", "got what I needed"
        ]
        
        has_task_completion = any(
            phrase in current_message.lower()
            for phrase in task_completion_phrases
        )
        
        # Check for satisfaction signals
        satisfaction_phrases = [
            "thank you", "thanks", "great", "perfect",
            "excellent", "that's what I needed"
        ]
        
        has_satisfaction = any(
            phrase in current_message.lower()
            for phrase in satisfaction_phrases
        )
        
        # Check for scheduling failure patterns
        scheduling_failure_indicators = self._detect_scheduling_failure(conversation_history)
        
        # Calculate overall confidence
        confidence = 0.0
        if has_task_completion or has_satisfaction:
            confidence = 0.8
        elif scheduling_failure_indicators["has_failure"]:
            confidence = scheduling_failure_indicators["confidence"]
        
        return {
            "has_task_completion": has_task_completion,
            "has_satisfaction": has_satisfaction,
            "has_scheduling_failure": scheduling_failure_indicators["has_failure"],
            "scheduling_failure_reason": scheduling_failure_indicators["reason"],
            "confidence": confidence,
            "context_length": len(conversation_history)
        }
    
    def _detect_scheduling_failure(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Detect if scheduling has repeatedly failed"""
        
        # Look for patterns indicating scheduling difficulties
        assistant_messages = [
            msg["content"].lower() for msg in conversation_history[-10:]  # Last 10 messages
            if msg.get("role") == "assistant"
        ]
        
        # Count flexibility requests
        flexibility_requests = sum(
            1 for msg in assistant_messages
            if any(phrase in msg for phrase in [
                "flexibility", "alternative", "different time", 
                "business hours", "available slots", "timing"
            ])
        )
        
        # Count promises without delivery
        promises = sum(
            1 for msg in assistant_messages
            if any(phrase in msg for phrase in [
                "i'll find", "let me check", "i'll look", 
                "get back to you", "check our calendar"
            ])
        )
        
        # Check for repeated scheduling attempts
        scheduling_attempts = sum(
            1 for msg in assistant_messages
            if any(phrase in msg for phrase in [
                "schedule", "interview", "appointment", "slots", "available"
            ])
        )
        
        # Determine if there's a scheduling failure pattern
        has_failure = False
        reason = ""
        confidence = 0.0
        
        if flexibility_requests >= 2:
            has_failure = True
            reason = "Multiple flexibility requests without successful scheduling"
            confidence = 0.85
        elif promises >= 3 and scheduling_attempts >= 3:
            has_failure = True
            reason = "Repeated promises without delivering concrete options"
            confidence = 0.75
        elif len(conversation_history) >= 8 and scheduling_attempts >= 4:
            has_failure = True
            reason = "Extended conversation without successful scheduling resolution"
            confidence = 0.7
        
        return {
            "has_failure": has_failure,
            "reason": reason,
            "confidence": confidence,
            "flexibility_requests": flexibility_requests,
            "promises": promises,
            "scheduling_attempts": scheduling_attempts
        }

    def _analyze_conversation_context_wrapper(self, current_message: str) -> Dict[str, Any]:
        """Wrapper function for the _analyze_conversation_context method to work with LangChain tools"""
        return self._analyze_conversation_context(current_message, self.current_conversation_history)

    def _initialize_agent(self):
        """Initialize the LangChain agent with prompts and tools"""
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            prompt=EXIT_DETECTION_TEMPLATE,
            tools=self.tools
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            output_key="output"
        )

    async def analyze_conversation(
        self,
        current_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> ExitDecision:
        """Analyze the conversation and determine if it should end
        
        Args:
            current_message: The latest message from the user
            conversation_history: List of previous messages in the conversation
            
        Returns:
            ExitDecision object containing the decision and reasoning
        """
        # Store conversation history for tool access
        self.current_conversation_history = conversation_history
        
        # Prepare conversation context
        context = {
            "current_message": current_message,
            "conversation_history": conversation_history
        }
        
        # Run the agent to analyze the conversation
        result = await self.agent_executor.ainvoke({
            "input": current_message,
            "chat_history": conversation_history,
            "agent_scratchpad": []
        })
        
        try:
            # Parse the agent's response
            decision_data = json.loads(result["output"])
            
            # Create the exit decision
            decision = ExitDecision(
                should_exit=decision_data["should_exit"],
                confidence=decision_data["confidence"],
                reason=decision_data["reason"],
                farewell_message=decision_data.get("farewell_message")
            )
            
            # If we should exit but no farewell message was provided,
            # generate one based on context
            if decision.should_exit and not decision.farewell_message:
                decision.farewell_message = get_farewell_template({
                    "scheduling_completed": "scheduled" in current_message.lower(),
                    "information_provided": "information" in current_message.lower(),
                    "needs_consideration": any(phrase in current_message.lower() 
                                            for phrase in ["think", "consider", "review"]),
                    "technical_issue": any(phrase in current_message.lower() 
                                         for phrase in ["error", "issue", "problem"])
                })
            
            return decision
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to basic exit detection if parsing fails
            explicit_check = self._check_explicit_exit(current_message)
            implicit_check = self._check_implicit_exit(current_message)
            
            should_exit = explicit_check["has_explicit_exit"] or implicit_check["has_implicit_exit"]
            confidence = max(
                explicit_check["confidence"],
                implicit_check["confidence"]
            )
            
            return ExitDecision(
                should_exit=should_exit,
                confidence=confidence,
                reason="Fallback detection based on explicit/implicit signals",
                farewell_message=get_farewell_template({}) if should_exit else None
            )

    def get_farewell_message(self, context: Dict[str, Any]) -> str:
        """Generate an appropriate farewell message based on context
        
        Args:
            context: Dictionary containing conversation context
            
        Returns:
            A personalized farewell message
        """
        return get_farewell_template(context) 