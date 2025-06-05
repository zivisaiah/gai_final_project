"""
Core Agent Implementation
Phase 1: Conversation orchestration and decision making (Continue vs Schedule)
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.modules.prompts.phase1_prompts import Phase1Prompts
from config.phase1_settings import get_settings
from app.modules.agents.exit_advisor import ExitAdvisor, ExitDecision


class AgentDecision(Enum):
    """Possible agent decisions."""
    CONTINUE = "CONTINUE"
    SCHEDULE = "SCHEDULE"
    END = "END"


class ConversationState:
    """Manages conversation state and context."""
    
    def __init__(self, conversation_id: str = None):
        self.conversation_id = conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.messages: List[Dict] = []
        self.candidate_info: Dict = {}
        self.decision_history: List[Dict] = []
        self.created_at = datetime.now()
        self.last_decision = None
        self.last_reasoning = None
        
    def add_message(self, role: str, content: str, timestamp: datetime = None):
        """Add a message to the conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now()
        }
        self.messages.append(message)
        
        # Update candidate info if this is a user message
        if role == "user":
            self.candidate_info = Phase1Prompts.extract_candidate_info(self.messages)
    
    def add_decision(self, decision: AgentDecision, reasoning: str, response: str):
        """Record a decision made by the agent."""
        decision_record = {
            "decision": decision.value,
            "reasoning": reasoning,
            "response": response,
            "timestamp": datetime.now(),
            "candidate_info_at_decision": self.candidate_info.copy()
        }
        self.decision_history.append(decision_record)
        self.last_decision = decision
        self.last_reasoning = reasoning
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of the conversation state."""
        return {
            "conversation_id": self.conversation_id,
            "message_count": len(self.messages),
            "candidate_info": self.candidate_info,
            "last_decision": self.last_decision.value if self.last_decision else None,
            "created_at": self.created_at.isoformat(),
            "duration_minutes": (datetime.now() - self.created_at).total_seconds() / 60
        }


class CoreAgent:
    """
    Core Agent for Phase 1: Handles conversation flow and makes Continue vs Schedule decisions.
    
    This agent orchestrates recruitment conversations, gathering candidate information
    and determining when to transition from conversation to interview scheduling.
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = None):
        """Initialize the Core Agent with LangChain components."""
        self.settings = get_settings()
        
        # Initialize OpenAI client with Core Agent specific model
        core_model = model_name or self.settings.get_core_agent_model()
        self.llm = ChatOpenAI(
            api_key=openai_api_key or self.settings.OPENAI_API_KEY,
            model=core_model,
            temperature=self.settings.OPENAI_TEMPERATURE,
            max_tokens=self.settings.OPENAI_MAX_TOKENS
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferWindowMemory(
            k=self.settings.MAX_CONVERSATION_HISTORY,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Conversation state tracking
        self.conversations: Dict[str, ConversationState] = {}
        
        # Initialize prompts
        self.prompts = Phase1Prompts()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create the decision chain
        self._setup_decision_chain()
        
        # Initialize ExitAdvisor with model configuration
        self.exit_advisor = ExitAdvisor()
    
    def _setup_decision_chain(self):
        """Set up the LangChain decision-making chain."""
        # Create prompt template
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompts.get_core_agent_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_input}")
        ])
        
        # Create the chain
        self.decision_chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self.memory.chat_memory.messages
            )
            | self.decision_prompt
            | self.llm
        )
    
    def get_or_create_conversation(self, conversation_id: str = None) -> ConversationState:
        """Get existing conversation or create a new one."""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # Create new conversation
        new_conv = ConversationState(conversation_id)
        self.conversations[new_conv.conversation_id] = new_conv
        return new_conv
    
    async def process_message_async(
        self, 
        user_message: str, 
        conversation_id: str = None
    ) -> Tuple[str, AgentDecision, str]:
        """
        Async version: Process a user message and return agent response, decision, and reasoning.
        """
        try:
            conversation = self.get_or_create_conversation(conversation_id)
            conversation.add_message("user", user_message)
            self.memory.chat_memory.add_user_message(user_message)
            # --- NEW: Consult ExitAdvisor first ---
            exit_decision: ExitDecision = await self.exit_advisor.analyze_conversation(
                current_message=user_message,
                conversation_history=[{"role": m["role"], "content": m["content"]} for m in conversation.messages]
            )
            if exit_decision.should_exit and exit_decision.confidence >= 0.7:
                response = exit_decision.farewell_message or "Thank you for your time."
                decision = AgentDecision.END
                reasoning = exit_decision.reason
                conversation.add_message("assistant", response)
                conversation.add_decision(decision, reasoning, response)
                self.memory.chat_memory.add_ai_message(response)
                self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
                return response, decision, reasoning
            # --- Otherwise, continue with normal decision logic ---
            decision, reasoning, response = self._make_decision(user_message, conversation)
            conversation.add_message("assistant", response)
            conversation.add_decision(decision, reasoning, response)
            self.memory.chat_memory.add_ai_message(response)
            self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
            return response, decision, reasoning
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return "I apologize, but I'm having technical difficulties. Could you please try again?", AgentDecision.CONTINUE, "Error occurred"

    # Optionally, keep the sync process_message for backward compatibility
    def process_message(self, user_message: str, conversation_id: str = None) -> Tuple[str, AgentDecision, str]:
        import asyncio
        return asyncio.run(self.process_message_async(user_message, conversation_id))
    
    def _make_decision(
        self, 
        user_message: str, 
        conversation: ConversationState
    ) -> Tuple[AgentDecision, str, str]:
        """
        Make a decision about whether to continue or schedule based on conversation context.
        
        Args:
            user_message: Latest user message
            conversation: Current conversation state
            
        Returns:
            Tuple of (decision, reasoning, response)
        """
        try:
            # Prepare input for the LangChain chain
            chain_input = {
                "user_input": user_message,
                "candidate_info": conversation.candidate_info,
                "conversation_context": self.prompts.format_conversation_context(conversation.messages)
            }
            
            # Get response from LangChain
            response = self.decision_chain.invoke(chain_input)
            response_text = response.content
            
            # Parse the response to extract decision, reasoning, and agent response
            decision, reasoning, agent_response = self._parse_agent_response(response_text)
            
            # Validate decision based on conversation context
            decision = self._validate_decision(decision, conversation)
            
            return decision, reasoning, agent_response
            
        except Exception as e:
            self.logger.error(f"Error in decision making: {e}")
            # Fallback to rule-based decision
            return self._fallback_decision(user_message, conversation)
    
    def _parse_agent_response(self, response_text: str) -> Tuple[AgentDecision, str, str]:
        """Parse the LLM response to extract decision, reasoning, and response."""
        try:
            # Look for structured response format
            decision_match = re.search(r'DECISION:\s*(CONTINUE|SCHEDULE)', response_text, re.IGNORECASE)
            reasoning_match = re.search(r'REASONING:\s*(.+?)(?=RESPONSE:|$)', response_text, re.DOTALL)
            response_match = re.search(r'RESPONSE:\s*(.+)', response_text, re.DOTALL)
            
            if decision_match and reasoning_match and response_match:
                decision = AgentDecision(decision_match.group(1).upper())
                reasoning = reasoning_match.group(1).strip()
                agent_response = response_match.group(1).strip()
                
                return decision, reasoning, agent_response
            
            # If structured format not found, try to infer from content
            if any(keyword in response_text.lower() for keyword in ['schedule', 'interview', 'calendar', 'appointment']):
                decision = AgentDecision.SCHEDULE
                reasoning = "Response indicates scheduling intent"
            else:
                decision = AgentDecision.CONTINUE
                reasoning = "Continuing conversation to gather more information"
            
            # Use entire response as agent response if not structured
            agent_response = response_text.strip()
            
            return decision, reasoning, agent_response
            
        except Exception as e:
            self.logger.error(f"Error parsing agent response: {e}")
            return AgentDecision.CONTINUE, "Error parsing response", response_text
    
    def _validate_decision(self, decision: AgentDecision, conversation: ConversationState) -> AgentDecision:
        """Validate and potentially override the decision based on conversation state."""
        candidate_info = conversation.candidate_info
        
        # Override to SCHEDULE if all conditions are met
        if (decision == AgentDecision.CONTINUE and 
            candidate_info.get("name") and 
            candidate_info.get("experience") == "mentioned" and
            candidate_info.get("interest_level") == "high" and
            candidate_info.get("availability_mentioned")):
            
            self.logger.info("Overriding CONTINUE to SCHEDULE based on conversation state")
            return AgentDecision.SCHEDULE
        
        # Override to CONTINUE if we don't have enough information yet
        if (decision == AgentDecision.SCHEDULE and 
            not candidate_info.get("name") and
            candidate_info.get("interest_level") != "high"):
            
            self.logger.info("Overriding SCHEDULE to CONTINUE - need more information")
            return AgentDecision.CONTINUE
        
        return decision
    
    def _fallback_decision(
        self, 
        user_message: str, 
        conversation: ConversationState
    ) -> Tuple[AgentDecision, str, str]:
        """Fallback rule-based decision making if LLM fails."""
        candidate_info = conversation.candidate_info
        user_lower = user_message.lower()
        
        # Clear scheduling intent
        if any(word in user_lower for word in ['schedule', 'interview', 'when can', 'available']):
            if candidate_info.get("interest_level") == "high":
                return (
                    AgentDecision.SCHEDULE,
                    "User expressed scheduling intent and shows interest",
                    "Great! Let me check our available interview slots for you."
                )
        
        # Clear disinterest
        if any(phrase in user_lower for phrase in ['not interested', 'no thanks', 'have a job']):
            return (
                AgentDecision.CONTINUE,
                "User may not be interested, continuing to confirm",
                "I understand. Thank you for your time, and feel free to reach out if your situation changes."
            )
        
        # Information gathering phase
        if not candidate_info.get("name") or candidate_info.get("experience") != "mentioned":
            return (
                AgentDecision.CONTINUE,
                "Still gathering basic candidate information",
                "Could you tell me a bit more about your Python experience and background?"
            )
        
        # Default to continue
        return (
            AgentDecision.CONTINUE,
            "Continuing conversation to build rapport",
            "That's great to hear! What aspects of Python development interest you most?"
        )
    
    def start_conversation(self, conversation_id: str = None) -> Tuple[str, ConversationState]:
        """Start a new conversation with initial greeting."""
        conversation = self.get_or_create_conversation(conversation_id)
        
        greeting = self.prompts.get_template("greeting")
        conversation.add_message("assistant", greeting)
        
        # Add to LangChain memory
        self.memory.chat_memory.add_ai_message(greeting)
        
        return greeting, conversation
    
    def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Get the current state of a conversation."""
        return self.conversations.get(conversation_id)
    
    def get_candidate_info(self, conversation_id: str) -> Dict:
        """Get extracted candidate information from a conversation."""
        conversation = self.conversations.get(conversation_id)
        return conversation.candidate_info if conversation else {}
    
    def export_conversation(self, conversation_id: str) -> Dict:
        """Export conversation data for analysis or storage."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}
        
        return {
            "conversation_id": conversation.conversation_id,
            "messages": conversation.messages,
            "candidate_info": conversation.candidate_info,
            "decision_history": conversation.decision_history,
            "summary": conversation.get_conversation_summary()
        }
    
    def clear_conversation(self, conversation_id: str):
        """Clear a conversation from memory."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        self.memory.clear()
    
    def get_statistics(self) -> Dict:
        """Get usage statistics for the agent."""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv.messages) for conv in self.conversations.values())
        
        decision_counts = {"CONTINUE": 0, "SCHEDULE": 0}
        for conv in self.conversations.values():
            for decision in conv.decision_history:
                decision_counts[decision["decision"]] += 1
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "decision_counts": decision_counts,
            "average_messages_per_conversation": total_messages / max(total_conversations, 1)
        } 