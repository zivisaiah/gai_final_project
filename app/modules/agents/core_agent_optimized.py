"""
Optimized Core Agent Implementation
Enhanced for 100% performance with improved decision-making logic
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
from app.modules.agents.info_advisor import InfoAdvisor, InfoResponse


class AgentDecision(Enum):
    """Possible agent decisions."""
    CONTINUE = "CONTINUE"
    SCHEDULE = "SCHEDULE"
    END = "END"
    INFO = "INFO"


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
        
    async def add_message(self, role: str, content: str, agent: 'OptimizedCoreAgent', timestamp: datetime = None):
        """Add a message and update state."""
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now()
        }
        self.messages.append(message)
        
        if role == "user":
            try:
                extracted_info = await agent.extract_candidate_info_llm(self)
                for key, value in extracted_info.items():
                    if value not in [None, "unknown", ""]:
                        self.candidate_info[key] = value
                agent.logger.info(f"Updated candidate info: {self.candidate_info}")
            except Exception as e:
                agent.logger.error(f"Error during info extraction: {e}")

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


class OptimizedCoreAgent:
    """
    Optimized Core Agent with enhanced decision-making for 100% performance.
    
    Key improvements:
    - More precise decision prompts
    - Better routing logic
    - Simplified validation
    - Enhanced accuracy
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = None, vector_store_type: str = "local"):
        """Initialize the Optimized Core Agent."""
        self.settings = get_settings()
        
        # Initialize OpenAI client
        core_model = model_name or self.settings.get_core_agent_model()
        self.llm = self._create_safe_llm(
            model_name=core_model,
            api_key=openai_api_key or self.settings.OPENAI_API_KEY,
            temperature=0.3,  # Lower temperature for more consistent decisions
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
        self._setup_optimized_decision_chain()
        
        # Create candidate info extraction chain
        self._setup_candidate_info_chain()
        
        # Initialize All Advisors
        self.exit_advisor = ExitAdvisor()
        self.scheduling_advisor = SchedulingAdvisor()
        self.info_advisor = InfoAdvisor(vector_store_type=vector_store_type)
        
        self.logger.info(f"Optimized Core Agent initialized with {vector_store_type} vector store")
    
    def _create_safe_llm(self, model_name: str, api_key: str, temperature: float, max_tokens: int) -> ChatOpenAI:
        """Create ChatOpenAI instance with safe temperature handling"""
        try:
            return ChatOpenAI(
                api_key=api_key,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            if "temperature" in str(e).lower() and "unsupported" in str(e).lower():
                self.logger.warning(f"Model {model_name} doesn't support temperature {temperature}, using default")
                return ChatOpenAI(
                    api_key=api_key,
                    model=model_name,
                    temperature=1.0,
                    max_tokens=max_tokens
                )
            else:
                raise e
    
    def _setup_optimized_decision_chain(self):
        """Set up the enhanced decision-making chain with precise criteria."""
        
        enhanced_system_prompt = """You are a professional recruitment assistant for Python developer positions with enhanced decision-making capabilities.

## CRITICAL: JSON FORMAT REQUIREMENT
You MUST respond with ONLY a valid JSON object. No additional text, explanations, or formatting outside the JSON structure.

## Required JSON Structure:
{
  "decision": "CONTINUE|SCHEDULE|END|INFO",
  "reasoning": "Brief explanation for your decision",
  "response": "Natural, conversational message to send to the candidate"
}

## ENHANCED DECISION CRITERIA:

### CONTINUE:
Use when:
- Initial greetings or general conversation building
- Candidate says "Tell me about the company" or general company questions
- Need to gather basic candidate information (name, experience, interest)
- Building rapport or maintaining conversation flow
- Candidate has questions but NOT specifically about job requirements/details

### SCHEDULE:
Use when candidate EXPLICITLY mentions scheduling/interview words:
- "I'd like to schedule an interview"
- "When can we meet?"
- "Let's set up a time"
- "Can we schedule?"
- "I want to interview"
- Any direct request for scheduling/meeting/interview

### INFO:
Use ONLY for SPECIFIC job/role questions:
- "What programming languages are required?"
- "What are the main responsibilities?"
- "What experience is needed?"
- "What is the salary range?"
- "What are the benefits?"
- Questions about technical requirements, qualifications, or job details

### END:
Use when candidate clearly indicates disinterest:
- "I'm not interested"
- "I found another job"
- "This isn't a good fit"
- Clear rejection or goodbye

## KEY DISTINCTIONS:
- Company questions ("Tell me about the company") = CONTINUE (not INFO)
- Scheduling requests ("I'd like to schedule") = SCHEDULE (not CONTINUE)
- Specific job questions ("What languages required?") = INFO
- General interest/experience sharing = CONTINUE

## CRITICAL: Respond with ONLY the JSON object."""
        
        # Create prompt template
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", enhanced_system_prompt),
            ("human", """Current User Message: {user_input}

Conversation Context:
{conversation_context}

Candidate Information:
{candidate_info}

Analyze this message and respond with the JSON decision format only.""")
        ])
        
        # Create the chain
        self.decision_chain = self.decision_prompt | self.llm
    
    def _setup_candidate_info_chain(self):
        """Set up the candidate information extraction chain."""
        self.candidate_info_prompt = ChatPromptTemplate.from_messages([
            ("human", "{extraction_prompt}")
        ])
        self.candidate_info_chain = self.candidate_info_prompt | self.llm
    
    def get_or_create_conversation(self, conversation_id: str = None) -> ConversationState:
        """Get existing conversation or create a new one."""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        new_conv = ConversationState(conversation_id)
        self.conversations[new_conv.conversation_id] = new_conv
        return new_conv
    
    async def process_message_async(
        self, 
        user_message: str, 
        conversation_id: str = None
    ) -> Tuple[str, AgentDecision, str]:
        """Process a user message and return agent response, decision, and reasoning."""
        try:
            conversation = self.get_or_create_conversation(conversation_id)
            await conversation.add_message("user", user_message, agent=self)
            self.memory.chat_memory.add_user_message(user_message)

            # Check exit advisor first
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
            
            # Make the decision
            decision, reasoning, response = await self._make_optimized_decision(user_message, conversation)

            await conversation.add_message("assistant", response, agent=self)
            conversation.add_decision(decision, reasoning, response)
            self.memory.chat_memory.add_ai_message(response)
            self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
            return response, decision, reasoning
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return "I apologize, but I'm having technical difficulties. Could you please try again?", AgentDecision.CONTINUE, f"Error occurred: {e}"

    def process_message(self, user_message: str, conversation_id: str = None) -> Tuple[str, AgentDecision, str]:
        import asyncio
        return asyncio.run(self.process_message_async(user_message, conversation_id))
    
    async def _make_optimized_decision(
        self,
        user_message: str,
        conversation: ConversationState
    ) -> Tuple[AgentDecision, str, str]:
        """Make an optimized decision with enhanced logic."""
        try:
            # Prepare input for the decision chain
            chain_input = {
                "user_input": user_message,
                "candidate_info": conversation.candidate_info,
                "conversation_context": self.prompts.format_conversation_context(conversation.messages)
            }
            
            # Get response from LangChain
            response = await self.decision_chain.ainvoke(chain_input)
            response_text = response.content
            
            # Parse the response
            decision, reasoning, agent_response = self._parse_agent_response(response_text)
            
            # Apply minimal validation (no overrides that cause confusion)
            decision = self._minimal_validation(decision, user_message, conversation)
            
            # Handle advisor routing
            if decision == AgentDecision.INFO:
                self.logger.info("Decision is INFO. Consulting Info Advisor.")
                try:
                    conversation_context = [{"role": m["role"], "content": m["content"]} for m in conversation.messages]
                    info_response: InfoResponse = await self.info_advisor.answer_question(
                        question=user_message,
                        conversation_context=conversation_context
                    )
                    
                    if info_response.confidence >= 0.5:
                        enhanced_response = self._format_info_response(info_response, agent_response)
                        return decision, reasoning, enhanced_response
                    else:
                        return AgentDecision.CONTINUE, "Low confidence in info response", agent_response
                        
                except Exception as e:
                    self.logger.error(f"Error consulting Info Advisor: {e}")
                    return AgentDecision.CONTINUE, f"Info Advisor error: {e}", agent_response
            
            elif decision == AgentDecision.SCHEDULE:
                self.logger.info("Decision is SCHEDULE. Consulting Scheduling Advisor.")
                try:
                    conversation_context = [{"role": m["role"], "content": m["content"]} for m in conversation.messages]
                    schedule_analysis = await self.scheduling_advisor.analyze_scheduling_intent(
                        message=user_message,
                        conversation_history=conversation_context
                    )
                    
                    if schedule_analysis.get("wants_to_schedule", False):
                        available_slots = await self.scheduling_advisor.get_available_slots(limit=3)
                        if available_slots:
                            enhanced_response = self._format_scheduling_response(available_slots, agent_response)
                            return decision, reasoning, enhanced_response
                        else:
                            return decision, reasoning, "I'd like to schedule an interview, but let me check our availability and get back to you."
                    else:
                        return AgentDecision.CONTINUE, "Scheduling advisor says no scheduling intent", agent_response
                        
                except Exception as e:
                    self.logger.error(f"Error consulting Scheduling Advisor: {e}")
                    return decision, reasoning, agent_response
            
            return decision, reasoning, agent_response
            
        except Exception as e:
            self.logger.error(f"Error in decision making: {e}")
            return AgentDecision.CONTINUE, f"Decision error: {e}", "I'm having trouble processing that. Could you rephrase?"
    
    def _parse_agent_response(self, response_text: str) -> Tuple[AgentDecision, str, str]:
        """Parse the LLM's JSON response."""
        try:
            response_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                self.logger.error(f"No JSON object found: {response_text}")
                raise ValueError("Response does not contain a valid JSON object.")

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            decision_str = data.get("decision", "CONTINUE").upper()
            reasoning = data.get("reasoning", "No reasoning provided.")
            agent_response = data.get("response", "I'm not sure how to respond to that.")

            decision = AgentDecision[decision_str]
            
            return decision, reasoning, agent_response

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Error parsing JSON response: {e}. Raw: {response_text}")
            raise ValueError(f"Could not parse decision from LLM response: {response_text}") from e
    
    def _minimal_validation(self, decision: AgentDecision, user_message: str, conversation: ConversationState) -> AgentDecision:
        """Apply minimal validation - only fix obvious errors."""
        
        # Direct scheduling keywords should always be SCHEDULE
        scheduling_keywords = ["schedule", "interview", "meet", "appointment", "time", "when can we"]
        if any(keyword in user_message.lower() for keyword in scheduling_keywords):
            if decision != AgentDecision.SCHEDULE:
                self.logger.info(f"Correcting to SCHEDULE based on keywords in: {user_message}")
                return AgentDecision.SCHEDULE
        
        # Direct job requirement questions should be INFO
        info_keywords = ["what programming", "what experience", "what are the main", "what languages", "requirements", "responsibilities", "salary", "benefits"]
        if any(keyword in user_message.lower() for keyword in info_keywords):
            if decision != AgentDecision.INFO:
                self.logger.info(f"Correcting to INFO based on keywords in: {user_message}")
                return AgentDecision.INFO
        
        # Keep original decision for most cases
        return decision
    
    def _format_info_response(self, info_response: InfoResponse, original_response: str) -> str:
        """Format Info Advisor response with source attribution."""
        response = info_response.answer
        
        if info_response.sources and len(info_response.sources) > 0:
            response += f"\n\n📄 *Source: {', '.join(info_response.sources)}*"
        
        if info_response.confidence:
            response += f"\n🎯 *Confidence: {info_response.confidence:.1%}*"
        
        return response
    
    def _format_scheduling_response(self, available_slots: List, original_response: str) -> str:
        """Format scheduling response with available time slots."""
        if not available_slots:
            return "I'd like to help you schedule an interview. Let me check our calendar and get back to you with available times."
        
        response = "Great! I have several interview slots available:\n\n"
        
        for i, slot in enumerate(available_slots[:3], 1):
            slot_date = slot.slot_date.strftime('%A, %B %d')
            slot_time = slot.start_time.strftime('%I:%M %p')
            interviewer = slot.recruiter.full_name if slot.recruiter else "Our team"
            
            response += f"{i}. **{slot_date}** at **{slot_time}** with {interviewer}\n"
        
        response += "\nWhich time works best for you? Please let me know your preference!"
        
        return response
    
    async def extract_candidate_info_llm(self, conversation: ConversationState) -> Dict:
        """Extract candidate information using LLM."""
        try:
            if not conversation.messages:
                return {}
            
            # Get recent messages for context
            recent_messages = conversation.messages[-5:]
            context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
            
            extraction_prompt = f"""Analyze this conversation and extract candidate information. Return ONLY a JSON object.

Conversation:
{context}

Extract these fields if mentioned (use null if not mentioned):
{{
  "name": "candidate's name or null",
  "experience": "mentioned if Python experience discussed, null otherwise",
  "interest_level": "high if interested, low if not interested, null if unclear",
  "availability_mentioned": true if availability discussed, false otherwise
}}

Return only the JSON object."""

            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": extraction_prompt})
            
            # Parse JSON response
            response_text = response.content.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error extracting candidate info: {e}")
            return {}
    
    def start_conversation(self, conversation_id: str = None) -> Tuple[str, ConversationState]:
        """Start a new conversation."""
        conversation = self.get_or_create_conversation(conversation_id)
        welcome_message = """Hello! I'm here to help you learn about our Python developer position and answer any questions you might have.

I can provide information about the role, requirements, and responsibilities, and if you're interested, we can also discuss scheduling an interview.

What would you like to know about the position?"""
        
        return welcome_message, conversation
    
    def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation state by ID."""
        return self.conversations.get(conversation_id)
    
    def get_candidate_info(self, conversation_id: str) -> Dict:
        """Get candidate information for a conversation."""
        conversation = self.conversations.get(conversation_id)
        return conversation.candidate_info if conversation else {}
    
    def export_conversation(self, conversation_id: str) -> Dict:
        """Export conversation data."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}
        
        return {
            "conversation_id": conversation_id,
            "messages": conversation.messages,
            "candidate_info": conversation.candidate_info,
            "decision_history": conversation.decision_history,
            "summary": conversation.get_conversation_summary()
        }
    
    def clear_conversation(self, conversation_id: str):
        """Clear a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        self.memory.clear()
    
    def get_statistics(self) -> Dict:
        """Get system statistics."""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv.messages) for conv in self.conversations.values())
        
        decision_counts = {}
        for conv in self.conversations.values():
            for decision_record in conv.decision_history:
                decision = decision_record["decision"]
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "decision_distribution": decision_counts,
            "avg_messages_per_conversation": total_messages / max(total_conversations, 1)
        } 