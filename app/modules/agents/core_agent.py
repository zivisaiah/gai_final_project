"""
Core Agent Implementation
Phase 3.3: Complete multi-agent orchestration with Info Advisor integration
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
    INFO = "INFO"  # New: For job-related questions


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
    Core Agent for Phase 3.3: Complete multi-agent orchestration with Info Advisor.
    
    This agent orchestrates recruitment conversations, intelligently routing between:
    - Info Advisor: Job-related questions and information requests
    - Scheduling Advisor: Interview scheduling and time management
    - Exit Advisor: Conversation ending detection
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = None, vector_store_type: str = "local"):
        """Initialize the Core Agent with all advisors."""
        self.settings = get_settings()
        
        # Initialize OpenAI client with Core Agent specific model
        core_model = model_name or self.settings.get_core_agent_model()
        self.llm = self._create_safe_llm(
            model_name=core_model,
            api_key=openai_api_key or self.settings.OPENAI_API_KEY,
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
        
        # Initialize All Advisors
        self.exit_advisor = ExitAdvisor()
        self.scheduling_advisor = SchedulingAdvisor()
        self.info_advisor = InfoAdvisor(vector_store_type=vector_store_type)
        
        self.logger.info(f"Core Agent initialized with {vector_store_type} vector store for Info Advisor")
    
    def _create_safe_llm(self, model_name: str, api_key: str, temperature: float, max_tokens: int) -> ChatOpenAI:
        """Create ChatOpenAI instance with safe temperature handling"""
        try:
            # Try with the requested temperature first
            return ChatOpenAI(
                api_key=api_key,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            # If temperature is not supported, try with default temperature (1.0)
            if "temperature" in str(e).lower() and "unsupported" in str(e).lower():
                self.logger.warning(f"Model {model_name} doesn't support temperature {temperature}, using default temperature (1.0)")
                return ChatOpenAI(
                    api_key=api_key,
                    model=model_name,
                    temperature=1.0,
                    max_tokens=max_tokens
                )
            else:
                # Re-raise if it's a different error
                raise e
    
    def _setup_decision_chain(self):
        """Set up the LangChain decision-making chain."""
        # Enhanced system prompt with INFO routing capability
        enhanced_system_prompt = """You are a professional recruitment assistant for Python developer positions with multi-agent orchestration capabilities.

## Your Capabilities:
- Engage in professional, friendly conversation with candidates
- Gather candidate information (name, experience, availability)
- Route information requests to specialized advisors
- Determine when to CONTINUE, SCHEDULE, END, or request INFO

## Decision Framework & Response Format:
You must analyze the conversation and respond with a single, valid JSON object. The JSON object must have this exact structure:
{{
  "decision": "CONTINUE|SCHEDULE|END|INFO",
  "reasoning": "A brief explanation for your decision",
  "response": "The natural, conversational message to send to the candidate"
}}

### CONTINUE:
Choose when the conversation should proceed normally.
- Building rapport or gathering basic information
- Need more details from candidate
- General conversation flow

### SCHEDULE: 
Choose when ready to schedule an interview.
- Candidate has expressed clear interest and you have their basic info
- Candidate has indicated availability
- Natural scheduling moment reached

### END:
Choose when conversation should conclude.
- Candidate clearly states not interested
- Candidate found another job
- Natural conversation ending

### INFO:
Choose when candidate asks specific questions about:
- Job requirements, qualifications, technical skills needed
- Role responsibilities, duties, day-to-day work
- Company information, benefits, work environment
- Technical details about the position
- Any "what", "how", "why" questions about the job/role/company

## CRITICAL: JSON FORMAT ONLY
Your entire response must be only the JSON object. No additional text, explanations, or formatting outside the JSON structure.

## Tone & Style:
- Professional but warm and approachable
- Concise but informative
- Encouraging and positive"""
        
        # Create prompt template with proper context variables
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", enhanced_system_prompt),
            ("human", """Current User Message: {user_input}

Conversation Context:
{conversation_context}

Candidate Information Gathered:
{candidate_info}

Analyze this context and respond with the JSON decision format only.""")
        ])
        
        # Create the chain
        self.decision_chain = self.decision_prompt | self.llm
    
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
            
            # --- NEW: Info Advisor Logic ---
            if decision == AgentDecision.INFO:
                self.logger.info("Decision is INFO. Consulting Info Advisor for job-related answer.")
                
                try:
                    # Get conversation history for context
                    full_history = [{"role": m["role"], "content": m["content"]} for m in conversation.messages]
                    
                    # Ask Info Advisor for job-related information
                    info_response: InfoResponse = await self.info_advisor.answer_question(
                        question=user_message,
                        conversation_history=full_history
                    )
                    
                    # Return Info Advisor's response
                    final_reasoning = f"Info request handled. Question type: {info_response.question_type}, Confidence: {info_response.confidence:.2f}, Has context: {info_response.has_context}"
                    return decision, final_reasoning, info_response.answer
                    
                except Exception as e:
                    self.logger.error(f"Error consulting Info Advisor: {e}")
                    # Fallback to continue response
                    fallback_response = "I'd be happy to help with information about this position. Could you please rephrase your question or be more specific about what you'd like to know?"
                    return AgentDecision.CONTINUE, f"Info Advisor error, fallback response: {str(e)}", fallback_response
            
            # --- Proactive Scheduling Logic ---
            elif decision == AgentDecision.SCHEDULE:
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
                    # We have slots - let the UI handle displaying them as buttons
                    # Don't include slot text in the response since they'll be shown as clickable buttons
                    final_reasoning = f"Proactively providing schedule options. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, agent_response
                
                elif schedule_decision == SchedulingDecision.SCHEDULE and not available_slots:
                    # High intent but no matching slots - ask for flexibility
                    flexibility_response = await self._handle_no_slots_available(
                        conversation, user_message, schedule_reasoning
                    )
                    final_reasoning = f"No slots match preferences, asking for flexibility. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, flexibility_response
                
                else:
                    # Low scheduling intent - OVERRIDE response to avoid scheduling promises
                    # The original agent_response may contain scheduling promises, so we need to provide
                    # a response that continues the conversation without making empty promises
                    override_response = await self._generate_continue_response(conversation, user_message, schedule_reasoning)
                    final_reasoning = f"Low scheduling intent, continuing conversation. Advisor reason: {schedule_reasoning}"
                    return AgentDecision.CONTINUE, final_reasoning, override_response

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
        
        # Check if we have enough information for scheduling
        has_name = bool(candidate_info.get("name"))
        has_experience = bool(candidate_info.get("experience") and 
                            candidate_info.get("experience") not in ["unknown", ""])
        has_availability = bool(candidate_info.get("availability_mentioned"))
        has_interest = candidate_info.get("interest_level") in ["high", "medium"]
        
        self.logger.info(f"Validation check - Name: {has_name}, Experience: {has_experience}, "
                        f"Availability: {has_availability}, Interest: {has_interest}")
        self.logger.info(f"Candidate info: {candidate_info}")
        
        # Override to SCHEDULE if we have enough information and availability
        if (decision == AgentDecision.CONTINUE and 
            has_name and has_experience and has_availability and has_interest):
            
            self.logger.info("Overriding CONTINUE to SCHEDULE based on sufficient candidate information")
            return AgentDecision.SCHEDULE
        
        # Don't override SCHEDULE decisions - let them proceed
        # The SchedulingAdvisor will make the final determination
        
        return decision
    
    async def _handle_no_slots_available(
        self,
        conversation: ConversationState,
        user_message: str,
        schedule_reasoning: str
    ) -> str:
        """
        Handle the case when no slots match user preferences.
        Try to offer alternatives or gracefully end conversation.
        """
        try:
            # Check how many times we've asked for flexibility
            flexibility_attempts = sum(
                1 for msg in conversation.messages[-10:]  # Last 10 messages
                if msg.get("role") == "assistant" and 
                ("flexibility" in msg.get("content", "").lower() or 
                 "alternative" in msg.get("content", "").lower())
            )
            
            if flexibility_attempts == 0:
                # First attempt - ask for flexibility
                return await self._ask_for_flexibility(conversation, schedule_reasoning)
            
            elif flexibility_attempts == 1:
                # Second attempt - offer specific alternatives
                return await self._offer_alternatives(conversation, schedule_reasoning)
            
            else:
                # Third attempt - trigger exit conversation
                return await self._trigger_scheduling_exit(conversation, schedule_reasoning)
                
        except Exception as e:
            self.logger.error(f"Error handling no slots available: {e}")
            return "I apologize, but I'm having trouble finding suitable interview slots at the moment. Could you please let me know your preferred days and times? This will help me suggest the best available options for you."
    
    async def _ask_for_flexibility(self, conversation: ConversationState, schedule_reasoning: str) -> str:
        """Ask user for flexibility in their time preferences."""
        return f"""I understand you prefer meeting after 4 PM, but unfortunately we don't have any available slots that match that time preference.

Would you be flexible with your timing? We have several slots available during business hours (9 AM - 4:30 PM) on weekdays. 

Could any of these alternative times work for you:
• **Morning slots**: 9:00 AM - 12:00 PM
• **Afternoon slots**: 1:00 PM - 4:30 PM

Please let me know if any of these times could work, or if you have other preferences!"""

    async def _offer_alternatives(self, conversation: ConversationState, schedule_reasoning: str) -> str:
        """Offer specific alternative times from available slots."""
        try:
            # Get next 3 available slots regardless of time preference
            from datetime import date, timedelta
            today = date.today()
            end_date = today + timedelta(days=14)
            
            available_slots = self.scheduling_advisor.sql_manager.get_available_slots(
                start_date=today,
                end_date=end_date,
                available_only=True
            )[:3]  # Take first 3 available
            
            if available_slots:
                slots_text = "\n".join([
                    f"• **{slot.slot_date.strftime('%A, %B %d')}** at **{slot.start_time.strftime('%I:%M %p')}**"
                    for slot in available_slots
                ])
                
                return f"""I've checked our calendar again and here are the nearest available slots:

{slots_text}

These are the only times our interviewers have available in the next two weeks. Would any of these work for you, or would you prefer to wait for later availability?

If none of these times work, we may need to explore other options or schedule for a later date."""
            else:
                return "Unfortunately, we don't have any available interview slots in the next two weeks. Would you like me to check for later dates or explore other scheduling options?"
                
        except Exception as e:
            self.logger.error(f"Error offering alternatives: {e}")
            return "I'm having trouble accessing our calendar at the moment. Could you please share your preferred days and times for an interview? I'll do my best to find a slot that works for your schedule."

    async def _generate_continue_response(
        self,
        conversation: ConversationState,
        user_message: str,
        schedule_reasoning: str
    ) -> str:
        """
        Generate a continuation response that doesn't make scheduling promises.
        Used when CoreAgent wants to SCHEDULE but SchedulingAdvisor says NOT_SCHEDULE.
        """
        candidate_info = conversation.candidate_info
        
        # Check if we have basic candidate info
        has_name = candidate_info.get("name")
        has_experience = candidate_info.get("experience") == "mentioned"
        has_interest = candidate_info.get("interest_level") == "high"
        
        # If we have name and interest but lack scheduling intent, ask for availability
        if has_name and has_interest:
            return f"""That's great to hear, {has_name}! Your background sounds like it could be a good fit for our Python developer position.

To move forward, I'd like to understand your availability better. Are you generally available during business hours (9 AM - 5 PM) on weekdays? Or do you have specific time preferences for a brief interview call?

This will help me check what slots might work best for both of us."""
        
        # If we have interest but no name, gather basic info first
        elif has_interest and not has_name:
            return """That's wonderful to hear about your interest and experience! 

Before we discuss next steps, could you share your name? And are you currently available for interviews, or do you have any specific timing preferences I should know about?"""
        
        # If we have name but need to gauge interest level
        elif has_name and not has_interest:
            return f"""Thanks for sharing that information, {has_name}! 

I'd love to learn more about what you're looking for in your next role. What aspects of Python development are you most passionate about? And are you actively looking for new opportunities right now?"""
        
        # Default: gather basic information
        else:
            return """Thanks for sharing your background! Your Python experience sounds interesting.

To better understand if this might be a good fit, could you tell me:
1. Your name
2. Whether you're currently looking for new opportunities
3. What your general availability looks like for a brief discussion about the role

This will help me determine the best next steps for us."""

    async def _trigger_scheduling_exit(self, conversation: ConversationState, schedule_reasoning: str) -> str:
        """Trigger exit conversation when scheduling repeatedly fails."""
        self.logger.info("Triggering exit conversation due to repeated scheduling failures")
        
        # Update conversation state to indicate scheduling failure
        conversation.candidate_info["scheduling_failed"] = True
        
        return """I understand this timing isn't working out. Unfortunately, we haven't been able to find a mutually convenient time for the interview.

I appreciate your interest in our Python developer position. If your schedule becomes more flexible in the future or if you'd like to explore other options, please feel free to reach out to us again.

Thank you for your time, and I wish you the best in your job search!"""
    
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
            # Return default values instead of falling back to deprecated keyword method
            return {
                "name": None,
                "experience": "unknown",
                "current_status": None,
                "interest_level": "unknown",
                "availability_mentioned": False
            }

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