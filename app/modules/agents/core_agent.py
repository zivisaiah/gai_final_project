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
                
                # CRITICAL FIX: Only update with LLM data if it's more specific than existing data
                for key, value in extracted_info.items():
                    if value not in [None, "unknown", ""]:
                        existing_value = self.candidate_info.get(key)
                        
                        # Preserve detailed existing information over generic LLM extractions
                        if key == "experience":
                            # Don't overwrite specific experience (e.g., "2 years Python") with generic "mentioned"
                            if existing_value and existing_value not in ["unknown", "mentioned"] and value == "mentioned":
                                continue  # Keep existing detailed experience
                        
                        # For other fields, only update if we don't have existing data or new data is more specific
                        if not existing_value or existing_value in [None, "unknown", ""]:
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
    
    async def _assess_candidate_qualifications(self, conversation: ConversationState) -> Dict[str, Any]:
        """Continuously assess candidate qualifications against job requirements"""
        candidate_info = conversation.candidate_info
        
        # Extract experience information (handle None values)
        experience_value = candidate_info.get("experience", "")
        experience_str = (experience_value or "").lower()
        
        # Job requirements (these could be loaded from configuration)
        min_experience_years = 3  # Minimum 3 years Python experience required
        
        assessment = {
            "meets_requirements": False,
            "experience_gap": 0,
            "qualification_status": "unknown",
            "should_continue": True,
            "assessment_reason": ""
        }
        
        try:
            # Parse experience years from candidate info
            if "years" in experience_str or "year" in experience_str:
                # Extract number from experience string (e.g., "1 years Python" -> 1)
                import re
                years_match = re.search(r'(\d+)\s*years?', experience_str)
                if years_match:
                    candidate_years = int(years_match.group(1))
                    assessment["experience_gap"] = min_experience_years - candidate_years
                    
                    if candidate_years >= min_experience_years:
                        assessment["meets_requirements"] = True
                        assessment["qualification_status"] = "qualified"
                        assessment["should_continue"] = True
                        assessment["assessment_reason"] = f"Candidate has {candidate_years} years experience, meets {min_experience_years}+ requirement"
                    else:
                        assessment["meets_requirements"] = False
                        assessment["qualification_status"] = "underqualified"
                        # Don't immediately end - let conversation flow naturally
                        # Exit Advisor will make the final decision based on candidate response
                        assessment["should_continue"] = True
                        assessment["assessment_reason"] = f"Candidate has {candidate_years} years experience, needs {min_experience_years}+ years (gap: {assessment['experience_gap']} years)"
                else:
                    assessment["qualification_status"] = "unclear"
                    assessment["should_continue"] = True
                    assessment["assessment_reason"] = "Experience format unclear, needs clarification"
            else:
                assessment["qualification_status"] = "unknown"
                assessment["should_continue"] = True
                assessment["assessment_reason"] = "No experience information provided yet"
                
        except Exception as e:
            self.logger.error(f"Error assessing qualifications: {e}")
            assessment["qualification_status"] = "error"
            assessment["should_continue"] = True
            assessment["assessment_reason"] = f"Assessment error: {str(e)}"
        
        # Store assessment in candidate info for Exit Advisor to use
        candidate_info["qualification_assessment"] = assessment
        
        self.logger.info(f"Qualification assessment: {assessment}")
        return assessment

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

            # --- NEW: Continuous Qualification Assessment ---
            qualification_assessment = await self._assess_candidate_qualifications(conversation)
            
            # --- NEW: Consult ExitAdvisor first (with qualification assessment) ---
            exit_decision: ExitDecision = await self.exit_advisor.analyze_conversation(
                current_message=user_message,
                conversation_history=[{"role": m["role"], "content": m["content"]} for m in conversation.messages],
                candidate_info=conversation.candidate_info
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
            # Check for significant qualification mismatch early in conversation
            qualification_assessment = conversation.candidate_info.get("qualification_assessment", {})
            qualification_status = qualification_assessment.get("qualification_status")
            experience_gap = qualification_assessment.get("experience_gap", 0)
            
            # If candidate is underqualified and conversation is still early, be proactive
            if (qualification_status == "underqualified" and 
                experience_gap >= 1 and  # 1+ year gap is significant for junior-mid level positions
                len(conversation.messages) <= 4 and  # Early in conversation
                not any("qualification" in msg.get("content", "").lower() or 
                       "experience" in msg.get("content", "").lower() or
                       "requirement" in msg.get("content", "").lower() 
                       for msg in conversation.messages[-3:] if msg.get("role") == "assistant")):  # Haven't discussed qualifications yet
                
                self.logger.info(f"Proactively addressing qualification mismatch: {experience_gap} year gap")
                
                # Provide honest but encouraging qualification feedback
                candidate_years = qualification_assessment.get("experience_gap", 0) + 3 - qualification_assessment.get("experience_gap", 0)
                # Calculate actual years from the gap
                actual_years = 3 - experience_gap
                
                proactive_response = f"""Hi {conversation.candidate_info.get('name', '')}! I appreciate your interest in our Python Developer position. 

I want to be upfront with you - this role requires at least 3 years of Python development experience, and I see you have {actual_years} years of experience. While there is an experience gap, I'd love to understand more about your background.

Do you have any additional experience through personal projects, bootcamps, or other programming languages that might be relevant? Sometimes candidates have stronger skills than their formal work experience might suggest.

What specific Python projects or technologies have you worked with in your {actual_years} years of experience?"""
                
                return AgentDecision.CONTINUE, "Proactively addressing qualification gap while remaining encouraging", proactive_response
            
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
                    
                    # Ask Info Advisor for job-related information (with candidate info for qualification assessment)
                    info_response: InfoResponse = await self.info_advisor.answer_question(
                        question=user_message,
                        conversation_history=full_history,
                        candidate_info=conversation.candidate_info
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
                    # We have slots - store them in conversation state for UI to access
                    conversation.candidate_info['available_slots'] = available_slots
                    
                    # Create a response that includes the slots in text form as backup
                    # The UI will display them as buttons, but this provides fallback text
                    try:
                        slots_text = "\n".join([
                            f"• **{datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00')).strftime('%A, %B %d at %I:%M %p')}** with {slot.get('recruiter', 'our team')}"
                            for slot in available_slots[:3]  # Show max 3 slots
                        ])
                        
                        enhanced_response = f"{agent_response}\n\nHere are the available time slots:\n\n{slots_text}\n\nPlease let me know which time works best for you!"
                    except Exception as e:
                        self.logger.error(f"Error formatting slots for response: {e}")
                        enhanced_response = f"{agent_response}\n\nI have {len(available_slots)} available time slots for you to choose from. Please let me know which time works best for you!"
                    
                    final_reasoning = f"Proactively providing schedule options. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, enhanced_response
                
                elif schedule_decision == SchedulingDecision.SCHEDULE and not available_slots:
                    # High intent but no matching slots - ask for flexibility
                    flexibility_response = await self._handle_no_slots_available(
                        conversation, user_message, schedule_reasoning
                    )
                    final_reasoning = f"No slots match preferences, asking for flexibility. Advisor reason: {schedule_reasoning}"
                    return decision, final_reasoning, flexibility_response
                
                elif schedule_decision == SchedulingDecision.NOT_SCHEDULE:
                    # Check if this is due to no available slots vs low intent
                    if "no available slots" in schedule_reasoning.lower() or "no slots" in schedule_reasoning.lower():
                        # High intent but no matching slots - be transparent about it
                        flexibility_response = await self._handle_no_slots_available(
                            conversation, user_message, schedule_reasoning
                        )
                        final_reasoning = f"No slots match preferences, asking for flexibility. Advisor reason: {schedule_reasoning}"
                        return decision, final_reasoning, flexibility_response
                    else:
                        # Low scheduling intent - OVERRIDE response to avoid scheduling promises
                        override_response = await self._generate_continue_response(conversation, user_message, schedule_reasoning)
                        final_reasoning = f"Low scheduling intent, continuing conversation. Advisor reason: {schedule_reasoning}"
                        return AgentDecision.CONTINUE, final_reasoning, override_response
                
                else:
                    # Fallback for any other cases
                    override_response = await self._generate_continue_response(conversation, user_message, schedule_reasoning)
                    final_reasoning = f"Unhandled scheduling case, continuing conversation. Advisor reason: {schedule_reasoning}"
                    return AgentDecision.CONTINUE, final_reasoning, override_response

            # NEW: Handle contact information requests
            if decision == AgentDecision.CONTINUE and conversation.candidate_info.get("needs_contact_info"):
                # Clear the flag and generate contact info request
                conversation.candidate_info["needs_contact_info"] = False
                contact_request_response = await self._generate_contact_info_request(conversation, user_message)
                final_reasoning = "Requesting contact information before scheduling interview"
                return decision, final_reasoning, contact_request_response
            
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
        
        # NEW: Contact information validation for actual scheduling
        has_email = bool(candidate_info.get("email"))
        has_phone = bool(candidate_info.get("phone"))
        has_contact_info = has_email or has_phone  # At least one contact method required
        
        self.logger.info(f"Validation check - Name: {has_name}, Experience: {has_experience}, "
                        f"Availability: {has_availability}, Interest: {has_interest}")
        self.logger.info(f"Contact validation - Email: {has_email}, Phone: {has_phone}, HasContact: {has_contact_info}")
        self.logger.info(f"Candidate info: {candidate_info}")
        
        # Override to SCHEDULE if we have enough information and availability
        if (decision == AgentDecision.CONTINUE and 
            has_name and has_experience and has_availability and has_interest):
            
            self.logger.info("Overriding CONTINUE to SCHEDULE based on sufficient candidate information")
            return AgentDecision.SCHEDULE
        
        # NEW: Block SCHEDULE decisions if missing contact information
        if decision == AgentDecision.SCHEDULE and not has_contact_info:
            self.logger.info("Blocking SCHEDULE decision - missing contact information (email or phone)")
            # Store the need for contact info in conversation state for response generation
            conversation.candidate_info["needs_contact_info"] = True
            return AgentDecision.CONTINUE
        
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
        
        # Extract the user's stated preference from the last few messages
        user_preference = "your preferred time"
        for msg in conversation.messages[-3:]:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                if "between" in content and ("pm" in content or "am" in content):
                    user_preference = f"the time you mentioned ({msg.get('content', '')})"
                    break
        
        return f"""I appreciate you sharing your availability! Unfortunately, we don't currently have any interview slots available during {user_preference}.

Would you be flexible with your timing? We have several slots available during business hours on weekdays:

• **Morning slots**: 9:00 AM - 12:00 PM
• **Early afternoon slots**: 1:00 PM - 3:00 PM

Would any of these alternative times work for your schedule? If not, I can also check for availability in the following weeks.

Please let me know what might work best for you!"""

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
    
    async def _generate_contact_info_request(self, conversation: ConversationState, user_message: str) -> str:
        """Generate a request for contact information before scheduling."""
        candidate_info = conversation.candidate_info
        name = candidate_info.get("name", "")
        
        # Check what contact info we already have
        has_email = bool(candidate_info.get("email"))
        has_phone = bool(candidate_info.get("phone"))
        
        if name:
            if not has_email and not has_phone:
                # Need both email and phone
                return f"""Great to hear you're interested in scheduling an interview, {name}! Before I can set up a meeting time and send you confirmation details, I'll need to get your contact information.

Could you please provide:
• **Email address** - for sending interview confirmations and details
• **Phone number** - as a backup contact method

Once I have your contact information, I'll be able to show you available time slots and confirm your interview!"""
            
            elif not has_email:
                # Need email only
                return f"""Perfect, {name}! I'm ready to schedule your interview. To send you the confirmation details and interview information, I'll need your email address.

Could you please share your email with me? Once I have that, I can show you the available time slots!"""
            
            elif not has_phone:
                # Need phone only (rare case, but handle it)
                return f"""Excellent, {name}! Before I schedule your interview, could you also provide your phone number? This gives us a backup way to reach you if needed.

Once I have your phone number, I'll show you the available interview time slots!"""
        else:
            # No name, need everything
            return """I'd be happy to help you schedule an interview! Before I can set up a meeting time, I'll need to get some basic contact information.

Could you please provide:
• **Your name**
• **Email address** - for sending interview confirmations  
• **Phone number** - as a backup contact method

Once I have your contact details, I'll be able to show you available time slots and confirm your interview!"""
    
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
                "availability_mentioned": extracted_data.get("availability_mentioned", False),
                "email": extracted_data.get("email"),
                "phone": extracted_data.get("phone")
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
                "availability_mentioned": False,
                "email": None,
                "phone": None
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