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
from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision


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
        
    async def add_message(self, role: str, content: str, agent: 'CoreAgent', timestamp: datetime = None):
        """Add a message and update state using LLM-based analysis."""
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now()
        }
        self.messages.append(message)
        
        # New: Use LLM-based extraction for all user messages for consistency
        if role == "user":
            try:
                # Use the agent's LLM extraction method
                extracted_info = await agent.extract_candidate_info_llm(self)
                
                # Update candidate_info with new, non-empty values
                for key, value in extracted_info.items():
                    if value not in [None, "unknown", ""]:
                        self.candidate_info[key] = value
                
                agent.logger.info(f"Updated candidate info via LLM: {self.candidate_info}")

            except Exception as e:
                agent.logger.error(f"Error during LLM info extraction in ConversationState: {e}")

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
        
        # Create candidate info extraction chain
        self._setup_candidate_info_chain()
        
        # Initialize Advisors
        self.exit_advisor = ExitAdvisor()
        self.scheduling_advisor = SchedulingAdvisor()
    
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
    
    def _setup_candidate_info_chain(self):
        """Set up the LangChain candidate information extraction chain."""
        # Create prompt template for candidate info extraction
        self.candidate_info_prompt = ChatPromptTemplate.from_messages([
            ("human", "{extraction_prompt}")
        ])
        
        # Create the extraction chain
        self.candidate_info_chain = self.candidate_info_prompt | self.llm
    
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
            await conversation.add_message("user", user_message, agent=self)
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
                await conversation.add_message("assistant", response, agent=self)
                conversation.add_decision(decision, reasoning, response)
                self.memory.chat_memory.add_ai_message(response)
                self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
                return response, decision, reasoning
            
            # --- Otherwise, continue with normal decision logic ---
            decision, reasoning, response = await self._make_decision(user_message, conversation)

            await conversation.add_message("assistant", response, agent=self)
            conversation.add_decision(decision, reasoning, response)
            self.memory.chat_memory.add_ai_message(response)
            self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
            return response, decision, reasoning
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return "I apologize, but I'm having technical difficulties. Could you please try again?", AgentDecision.CONTINUE, f"Error occurred: {e}"

    # Optionally, keep the sync process_message for backward compatibility
    def process_message(self, user_message: str, conversation_id: str = None) -> Tuple[str, AgentDecision, str]:
        import asyncio
        return asyncio.run(self.process_message_async(user_message, conversation_id))
    
    async def _make_decision(
        self,
        user_message: str,
        conversation: ConversationState
    ) -> Tuple[AgentDecision, str, str]:
        """
        Make a decision, and if scheduling, proactively fetch and format time slots.
        """
        try:
            # Prepare input for the LangChain chain
            chain_input = {
                "user_input": user_message,
                "candidate_info": conversation.candidate_info,
                "conversation_context": self.prompts.format_conversation_context(conversation.messages)
            }
            
            # Get response from LangChain
            response = await self.decision_chain.ainvoke(chain_input)
            response_text = response.content
            
            # Parse the response to extract decision, reasoning, and the initial agent response
            decision, reasoning, agent_response = self._parse_agent_response(response_text)
            
            # Validate decision based on conversation context
            decision = self._validate_decision(decision, conversation)
            
            # --- Proactive Scheduling Logic ---
            if decision == AgentDecision.SCHEDULE:
                self.logger.info("Decision is SCHEDULE. Consulting SchedulingAdvisor for available slots.")
                
                # Use the entire conversation history for context
                full_history = conversation.messages
                # Corrected method call and arguments
                (
                    schedule_decision,
                    schedule_reasoning,
                    available_slots,
                    _
                ) = self.scheduling_advisor.make_scheduling_decision(
                    candidate_info=conversation.candidate_info,
                    conversation_messages=[{"role": m["role"], "content": m["content"]} for m in full_history],
                    latest_message=user_message
                )

                # Handle different scheduling advisor decisions
                if schedule_decision == SchedulingDecision.CONFIRM_SLOT:
                    # User is confirming a previously offered slot - don't offer more slots
                    self.logger.info("SchedulingAdvisor detected slot confirmation. Not offering additional slots.")
                    return decision, f"Slot confirmation detected. Advisor reason: {schedule_reasoning}", agent_response
                
                elif schedule_decision == SchedulingDecision.SCHEDULE and available_slots:
                    # We have slots, so let's format them proactively.
                    slot_text = "\n".join([f"- {datetime.fromisoformat(slot['datetime']).strftime('%A, %B %d at %I:%M %p')}" for slot in available_slots])
                    # The 'agent_response' from the LLM is a pre-confirmation. We append the slots to it.
                    proactive_response = f"{agent_response}\n\nI found a few available time slots for you:\n{slot_text}\n\nPlease let me know which one works best for you."
                    final_reasoning = f"Proactively providing schedule options. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, proactive_response
                else:
                    # Advisor decided not to schedule or found no slots.
                    # Use the original LLM response, which should be a commitment to find slots.
                    final_reasoning = f"Scheduling decision made, but no slots available yet. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, agent_response

            # For CONTINUE or END, return the original parsed response
            return decision, reasoning, agent_response
            
        except Exception as e:
            self.logger.error(f"Critical error in decision making: {e}", exc_info=True)
            # Re-raise the exception to be caught by the main handler.
            # This ensures we don't silently fail and can see the root cause.
            raise

    def _parse_agent_response(self, response_text: str) -> Tuple[AgentDecision, str, str]:
        """Parse the LLM's JSON response to extract decision, reasoning, and response."""
        try:
            # The LLM is now instructed to only return JSON, but might wrap it in markdown.
            response_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            
            # Find the JSON object boundaries to handle potential leading/trailing text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                self.logger.error(f"No JSON object found in LLM response: {response_text}")
                raise ValueError("Response does not contain a valid JSON object.")

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            # Extract data from JSON
            decision_str = data.get("decision", "CONTINUE").upper()
            reasoning = data.get("reasoning", "No reasoning provided.")
            agent_response = data.get("response", "I'm not sure how to respond to that, could you rephrase?")

            # Convert decision string to Enum
            decision = AgentDecision[decision_str]
            
            return decision, reasoning, agent_response

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Critical error parsing LLM JSON response: {e}. Raw response: {response_text}")
            # Re-raise to be caught by the main error handler. We no longer use a fallback.
            raise ValueError(f"Could not parse decision from LLM response: {response_text}") from e
    
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
    
    async def extract_candidate_info_llm(self, conversation: ConversationState) -> Dict:
        """
        Extract candidate information using LLM analysis (new unified approach).
        
        This method demonstrates the proper LLM-based approach that should replace
        the keyword-based extraction for architectural consistency.
        """
        try:
            # Generate extraction prompt
            extraction_prompt = self.prompts.get_candidate_info_extraction_prompt(conversation.messages)
            
            # Get LLM analysis
            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": extraction_prompt})
            response_text = response.content.strip()
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            extracted_data = json.loads(response_text)
            
            # Convert to compatible format
            candidate_info = {
                "name": extracted_data.get("name"),
                "experience": "mentioned" if extracted_data.get("experience", {}).get("has_python") else "unknown",
                "current_status": extracted_data.get("current_status"),
                "interest_level": extracted_data.get("interest_level", "unknown"),
                "availability_mentioned": extracted_data.get("availability_mentioned", False)
            }
            
            self.logger.info(f"LLM-extracted candidate info: {candidate_info}")
            return candidate_info
            
        except Exception as e:
            self.logger.error(f"Error in LLM candidate info extraction: {e}")
            # Fallback to keyword method for resilience, though it's deprecated
            return Phase1Prompts.extract_candidate_info(conversation.messages)

    def start_conversation(self, conversation_id: str = None) -> Tuple[str, ConversationState]:
        """Start a new conversation with initial greeting."""
        conversation = self.get_or_create_conversation(conversation_id)
        
        greeting = self.prompts.get_template("greeting")
        # For the initial message, we don't need async complexity
        message = {
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now()
        }
        conversation.messages.append(message)
        
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