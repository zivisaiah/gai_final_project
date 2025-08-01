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

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, trim_messages
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
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
        
    def _detect_form_mode(self) -> bool:
        """
        Detect if we're operating in form-based mode (structured data exists) 
        vs conversation-based mode (extract everything from conversation).
        """
        # Check for indicators that structured form data was provided
        form_indicators = {
            "position": bool(self.candidate_info.get("position")),  # Specific position selected
            "email": bool(self.candidate_info.get("email")),         # Email address provided
            "phone": bool(self.candidate_info.get("phone")),         # Phone number provided
            "structured_experience": bool(self.candidate_info.get("experience") and 
                                        self.candidate_info.get("experience") not in ["unknown", "mentioned"]),  # Structured experience data
            "current_status": bool(self.candidate_info.get("current_status")),  # Job status provided
        }
        
        # Count how many form indicators are present
        active_indicators = [key for key, value in form_indicators.items() if value]
        is_form_mode = len(active_indicators) >= 2  # At least 2 form indicators suggests form submission
        
        return is_form_mode
    
    def _has_substantial_conversation_data(self) -> bool:
        """Check if we have substantial conversation-based information."""
        user_messages = [m for m in self.messages if m.get("role") == "user"]
        
        # Look for substantial conversation content
        total_content_length = sum(len(m.get("content", "")) for m in user_messages)
        meaningful_messages = [m for m in user_messages if len(m.get("content", "").strip()) > 10]
        
        return len(meaningful_messages) >= 1 and total_content_length > 20

    def _get_better_tone(self, tone1: str, tone2: str) -> str:
        """Return the more positive tone between two options."""
        tone_hierarchy = {"negative": 0, "neutral": 1, "positive": 2}
        score1 = tone_hierarchy.get(tone1.lower(), 1)
        score2 = tone_hierarchy.get(tone2.lower(), 1)
        return tone1 if score1 >= score2 else tone2
    
    def _get_better_engagement(self, eng1: str, eng2: str) -> str:
        """Return the higher engagement level between two options."""
        engagement_hierarchy = {"low": 0, "medium": 1, "high": 2}
        score1 = engagement_hierarchy.get(eng1.lower(), 0)
        score2 = engagement_hierarchy.get(eng2.lower(), 0)
        return eng1 if score1 >= score2 else eng2
    
    def _get_better_quality(self, qual1: str, qual2: str) -> str:
        """Return the better communication quality between two options."""
        quality_hierarchy = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
        score1 = quality_hierarchy.get(qual1.lower(), 0)
        score2 = quality_hierarchy.get(qual2.lower(), 0)
        return qual1 if score1 >= score2 else qual2

    def _is_form_based_candidate(self) -> bool:
        """Check if this candidate came through form submission."""
        return self._detect_form_mode()
        
    async def add_message(self, role: str, content: str, agent: 'CoreAgent', timestamp: datetime = None):
        """Add a message and update state using appropriate extraction mode."""
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now()
        }
        self.messages.append(message)
        
        # Only process user messages for extraction
        if role == "user":
            try:
                # Log current state before processing
                existing_data_count = len([v for v in self.candidate_info.values() if v not in [None, "", {}, [], "unknown"]])
                agent.logger.info(f"PRE-EXTRACTION: {existing_data_count} existing data fields: {list(self.candidate_info.keys())}")
                
                # Determine operation mode
                is_form_mode = self._detect_form_mode()
                has_conversation_data = self._has_substantial_conversation_data()
                
                # Enhanced logging for mode detection
                form_indicators = {
                    "position": bool(self.candidate_info.get("position")),
                    "email": bool(self.candidate_info.get("email")),
                    "phone": bool(self.candidate_info.get("phone")),
                    "structured_experience": bool(self.candidate_info.get("experience") and 
                                                self.candidate_info.get("experience") not in ["unknown", "mentioned"]),
                    "current_status": bool(self.candidate_info.get("current_status")),
                }
                active_indicators = [key for key, value in form_indicators.items() if value]
                agent.logger.info(f"MODE DETECTION: Form indicators: {form_indicators}, Active: {active_indicators}")
                
                if is_form_mode:
                    # FORM-BASED MODE: Preserve existing structured data, fill only gaps
                    agent.logger.info(f"[LOCK] FORM-BASED MODE: Preserving {existing_data_count} existing fields, filling gaps only")
                    agent.logger.info(f"[LOCK] EXISTING DATA TO PRESERVE: {self.candidate_info}")
                    await self._handle_form_based_extraction(agent)
                elif has_conversation_data:
                    # CONVERSATION-BASED MODE: Full LLM extraction from conversation
                    agent.logger.info(f"[CHAT] CONVERSATION-BASED MODE: Full LLM extraction (existing data: {existing_data_count} fields)")
                    if existing_data_count > 0:
                        agent.logger.warning(f"[!]  CONVERSATION MODE WITH EXISTING DATA: {self.candidate_info}")
                    await self._handle_conversation_based_extraction(agent)
                else:
                    # MINIMAL DATA MODE: Basic extraction for very limited conversation
                    agent.logger.info(f"🔹 MINIMAL DATA MODE: Basic extraction (existing data: {existing_data_count} fields)")
                    await self._handle_minimal_extraction(agent)
                
                # Log what changed
                final_data_count = len([v for v in self.candidate_info.values() if v not in [None, "", {}, [], "unknown"]])
                agent.logger.info(f"POST-EXTRACTION: {final_data_count} total fields (was {existing_data_count})")
                agent.logger.info(f"FINAL CANDIDATE INFO: {self.candidate_info}")

            except Exception as e:
                agent.logger.error(f"Error during candidate info extraction: {e}")

    async def _handle_form_based_extraction(self, agent: 'CoreAgent'):
        """Handle form-based mode: preserve existing data, use LLM to fill gaps only."""
        agent.logger.info("[LOCK] FORM-BASED EXTRACTION: Analyzing what needs to be filled")
        
        # Create backup of original data
        original_data = self.candidate_info.copy()
        
        # Identify what information is missing from the form
        missing_fields = []
        if not self.candidate_info.get("name"):
            missing_fields.append("name")
        if not self.candidate_info.get("experience") or self.candidate_info.get("experience") in ["unknown", "mentioned"]:
            missing_fields.append("experience")
        if not self.candidate_info.get("availability_mentioned"):
            missing_fields.append("availability")
        if not self.candidate_info.get("interest_level") or self.candidate_info.get("interest_level") == "unknown":
            missing_fields.append("interest_level")
        
        agent.logger.info(f"[SEARCH] MISSING FIELDS IDENTIFIED: {missing_fields}")
        agent.logger.info(f"[LOCK] PRESERVED FORM DATA: {original_data}")
        
        if not missing_fields:
            # No missing fields, set HIGH engagement for form-submitted candidates
            agent.logger.info("[OK] NO MISSING FIELDS: Setting HIGH engagement for form-submitted candidate")
            self.candidate_info["conversation_sentiment"] = {
                "overall_tone": "positive", 
                "engagement_level": "high",      # [OK] HIGH - they filled out the form!
                "communication_quality": "excellent"  # [OK] EXCELLENT - structured data provided
            }
            return
        
        # Use targeted LLM extraction to fill only missing fields
        agent.logger.info(f"[BOT] CALLING TARGETED LLM for fields: {missing_fields}")
        extracted_info = await agent.extract_missing_info_llm(self, missing_fields)
        agent.logger.info(f"[BOT] LLM EXTRACTED: {extracted_info}")
        
        # Carefully merge only the missing information, preserving all form data
        changes_made = []
        for field in missing_fields:
            if field in extracted_info and extracted_info[field] not in [None, "unknown", ""]:
                if field == "experience":
                    # For experience, only update if we have something better than current
                    current_exp = self.candidate_info.get("experience")
                    new_exp = extracted_info[field]
                    if not current_exp or current_exp in ["unknown", "mentioned"]:
                        agent.logger.info(f"[MEMO] UPDATING EXPERIENCE: '{current_exp}' → '{new_exp}'")
                        self.candidate_info[field] = new_exp
                        changes_made.append(f"experience: {new_exp}")
                    else:
                        agent.logger.info(f"[LOCK] PRESERVING EXPERIENCE: '{current_exp}' (ignoring extracted: '{new_exp}')")
                else:
                    # Only update if current value is missing/empty
                    current_val = self.candidate_info.get(field)
                    if not current_val or current_val in [None, "unknown", ""]:
                        agent.logger.info(f"[MEMO] UPDATING {field}: '{current_val}' → '{extracted_info[field]}'")
                        self.candidate_info[field] = extracted_info[field]
                        changes_made.append(f"{field}: {extracted_info[field]}")
                    else:
                        agent.logger.info(f"[LOCK] PRESERVING {field}: '{current_val}' (ignoring extracted: '{extracted_info[field]}')")
        
        # Always update conversation sentiment - smart logic for form vs conversation users
        if "conversation_sentiment" in extracted_info:
            llm_sentiment = extracted_info["conversation_sentiment"]
            
            # For form-submitted candidates, ensure minimum high engagement but allow improvements
            if self._is_form_based_candidate():
                base_form_sentiment = {
                    "overall_tone": "positive",
                    "engagement_level": "high", 
                    "communication_quality": "excellent"
                }
                
                # Take the BETTER of form baseline vs current conversation assessment
                final_sentiment = {
                    "overall_tone": self._get_better_tone(base_form_sentiment["overall_tone"], llm_sentiment.get("overall_tone", "neutral")),
                    "engagement_level": self._get_better_engagement(base_form_sentiment["engagement_level"], llm_sentiment.get("engagement_level", "low")),
                    "communication_quality": self._get_better_quality(base_form_sentiment["communication_quality"], llm_sentiment.get("communication_quality", "poor"))
                }
                
                self.candidate_info["conversation_sentiment"] = final_sentiment
                changes_made.append("conversation_sentiment (smart-form)")
                agent.logger.info(f"[OK] SMART FORM SENTIMENT: Base={base_form_sentiment}, LLM={llm_sentiment}, Final={final_sentiment}")
            else:
                # Non-form users: use LLM assessment directly
                self.candidate_info["conversation_sentiment"] = llm_sentiment
                changes_made.append("conversation_sentiment (llm-direct)")
                agent.logger.info(f"[OK] LLM SENTIMENT: {llm_sentiment}")
        
        agent.logger.info(f"[OK] FORM-BASED EXTRACTION COMPLETE: Changes made: {changes_made if changes_made else 'None (all data preserved)'}")
        
        # Verify no critical form data was lost (but allow sentiment to evolve)
        for key, original_value in original_data.items():
            if original_value not in [None, "", {}, [], "unknown"]:
                # Skip conversation_sentiment - it should be allowed to evolve during conversation
                if key == "conversation_sentiment":
                    agent.logger.debug(f"[OK] SENTIMENT EVOLUTION ALLOWED: {key} can change during conversation")
                    continue
                    
                current_value = self.candidate_info.get(key)
                if current_value != original_value:
                    agent.logger.error(f"[ALERT] FORM DATA LOST! Field '{key}': '{original_value}' became '{current_value}'")
                    # Restore the original value
                    self.candidate_info[key] = original_value
                    agent.logger.info(f"[WRENCH] RESTORED: '{key}' back to '{original_value}'")
                else:
                    agent.logger.debug(f"[OK] PRESERVED: {key} = {original_value}")
    
    async def _handle_conversation_based_extraction(self, agent: 'CoreAgent'):
        """Handle full conversation-based extraction when no structured form data exists."""
        agent.logger.info("[CHAT] CONVERSATION-BASED EXTRACTION: Full LLM analysis of conversation context")
        
        # Get comprehensive extraction from LLM
        extracted_info = await agent.extract_candidate_info_llm(self)
        agent.logger.info(f"[BOT] LLM COMPREHENSIVE EXTRACTION: {extracted_info}")
        
        # Use the enhanced merging strategy from the original implementation
        agent.logger.info(f"[SEARCH] PRE-MERGE CANDIDATE INFO: {self.candidate_info}")
        
        for key, value in extracted_info.items():
            if value not in [None, "unknown", "", {}, []]:
                existing_value = self.candidate_info.get(key)
                agent.logger.info(f"[MEMO] MERGING FIELD '{key}': existing='{existing_value}' → new='{value}'")
                
                # Special handling for different data types
                if key == "experience":
                    # Preserve specific experience over generic, but allow upgrades
                    if not existing_value or existing_value in ["unknown", "mentioned"]:
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPDATED EXPERIENCE: '{existing_value}' -> '{value}'")
                    elif (isinstance(value, str) and isinstance(existing_value, str) and 
                          "year" in value.lower() and "year" not in existing_value.lower()):
                        # Prioritize experience with year information
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPGRADED EXPERIENCE (year info): '{existing_value}' -> '{value}'")
                    elif (isinstance(value, str) and isinstance(existing_value, str) and 
                          len(value) > len(existing_value) and 
                          existing_value in ["unknown", "mentioned"]):
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPGRADED EXPERIENCE (more detailed): '{existing_value}' -> '{value}'")
                    else:
                        agent.logger.info(f"[LOCK] PRESERVED EXPERIENCE: '{existing_value}' (ignored: '{value}')")
                        
                elif key == "qualification_assessment":
                    # Always update qualification assessment as it's comprehensive
                    if isinstance(value, dict) and value:
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPDATED QUALIFICATION ASSESSMENT: {value}")
                        
                elif key in ["experience_details", "extraction_metadata"]:
                    # Always update these comprehensive analysis fields
                    if isinstance(value, dict) and value:
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPDATED {key}: {value}")
                        
                elif key == "conversation_sentiment":
                    # Special handling for conversation sentiment - preserve high engagement for form users
                    if isinstance(value, dict) and value:
                        # Check if this appears to be form-based data (has structured info)
                        has_structured_data = (
                            self.candidate_info.get("email") and 
                            self.candidate_info.get("phone") and
                            self.candidate_info.get("experience") not in [None, "unknown", "mentioned"]
                        )
                        
                        if has_structured_data:
                            # Override with high engagement for form users
                            optimized_sentiment = {
                                "overall_tone": "positive",
                                "engagement_level": "high",
                                "communication_quality": "excellent"
                            }
                            self.candidate_info[key] = optimized_sentiment
                            agent.logger.info(f"[OK] FORM-OPTIMIZED CONVERSATION SENTIMENT: {optimized_sentiment}")
                        else:
                            # Use LLM sentiment for pure conversation users
                            self.candidate_info[key] = value
                            agent.logger.info(f"[OK] UPDATED CONVERSATION SENTIMENT: {value}")
                        
                elif key in ["name", "email", "phone", "interest_level", "current_status", 
                           "availability_mentioned", "availability_details", "position_interest"]:
                    # Update basic fields if they don't exist or are generic
                    if not existing_value or existing_value in [None, "unknown", ""]:
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPDATED BASIC FIELD '{key}': '{existing_value}' -> '{value}'")
                    else:
                        agent.logger.info(f"[LOCK] PRESERVED BASIC FIELD '{key}': '{existing_value}' (ignored: '{value}')")
                        
                else:
                    # For any other fields, update if current is None/empty
                    if not existing_value:
                        self.candidate_info[key] = value
                        agent.logger.info(f"[OK] UPDATED OTHER FIELD '{key}': '{existing_value}' -> '{value}'")
            else:
                agent.logger.info(f"⏭️  SKIPPED FIELD '{key}': value is None/empty/unknown ({value})")
        
        agent.logger.info(f"[SEARCH] POST-MERGE CANDIDATE INFO: {self.candidate_info}")
        agent.logger.info("[OK] CONVERSATION-BASED EXTRACTION COMPLETE")

    async def _handle_minimal_extraction(self, agent: 'CoreAgent'):
        """Handle minimal data mode: very basic extraction for short interactions."""
        # For very short interactions, just extract basics without complex analysis
        latest_message = self.messages[-1].get("content", "") if self.messages else ""
        
        # Simple name detection
        if not self.candidate_info.get("name"):
            if any(phrase in latest_message.lower() for phrase in ["my name is", "i'm", "i am", "call me"]):
                # Use simple LLM extraction just for name
                simple_extraction = await agent.extract_simple_info_llm(self, ["name"])
                if simple_extraction.get("name"):
                    self.candidate_info["name"] = simple_extraction["name"]
        
        # Update basic sentiment
        self.candidate_info["conversation_sentiment"] = {
            "overall_tone": "neutral",
            "engagement_level": "low" if len(latest_message) < 20 else "medium", 
            "communication_quality": "fair"
        }

    def add_decision(self, decision: AgentDecision, reasoning: str, response: str):
        """Track agent decisions for analysis."""
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
        
        # Initialize modernized conversation memory using InMemoryChatMessageHistory
        # This replaces the deprecated ConversationBufferWindowMemory
        self.chat_history = InMemoryChatMessageHistory()
        self.max_history_length = self.settings.MAX_CONVERSATION_HISTORY
        
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
        """
        Get qualification assessment from enhanced LLM extraction with complete data protection.
        
        This method safely extracts qualification assessment while preserving all existing form data.
        Uses backup/restore mechanism to prevent any data loss during LLM operations.
        """
        candidate_info = conversation.candidate_info
        
        # Check if we already have a qualification assessment from LLM extraction
        if "qualification_assessment" in candidate_info and candidate_info["qualification_assessment"]:
            existing_assessment = candidate_info["qualification_assessment"]
            
            # Validate assessment completeness
            if (existing_assessment.get("qualification_status", "unknown") != "unknown" and
                existing_assessment.get("assessment_confidence", 0) > 0.3):
                
                self.logger.info(f"Using existing qualification assessment: {existing_assessment}")
                return existing_assessment
        
        # If no valid assessment exists, trigger protected LLM extraction
        self.logger.info("No valid qualification assessment found, triggering protected LLM extraction")
        
        # CRITICAL: Backup all form data before any LLM operation
        original_candidate_info = conversation.candidate_info.copy()
        self.logger.info(f"[LOCK] BACKING UP candidate data: {original_candidate_info}")
        
        try:
            # Extract qualification assessment using safe LLM method
            enhanced_info = await self.extract_qualification_assessment_llm(conversation)
            
            # SELECTIVE UPDATE: Only add qualification assessment, preserve everything else
            if "qualification_assessment" in enhanced_info and enhanced_info["qualification_assessment"]:
                conversation.candidate_info["qualification_assessment"] = enhanced_info["qualification_assessment"]
                assessment = enhanced_info["qualification_assessment"]
                
                self.logger.info(f"[OK] SAFE ASSESSMENT UPDATE: Added qualification only")
                self.logger.info(f"Enhanced qualification assessment: {assessment}")
                return assessment
            else:
                raise ValueError("No valid qualification assessment in LLM response")
            
        except Exception as e:
            # RESTORE original data completely if anything goes wrong
            conversation.candidate_info.clear()
            conversation.candidate_info.update(original_candidate_info)
            self.logger.error(f"[WRENCH] RESTORED original candidate data after assessment error: {e}")
            
            # Return safe fallback assessment
            fallback_assessment = self._create_safe_fallback_assessment(str(e))
            conversation.candidate_info["qualification_assessment"] = fallback_assessment
            return fallback_assessment

    def _create_safe_fallback_assessment(self, error_msg: str = "Assessment unavailable") -> Dict[str, Any]:
        """Create a safe fallback qualification assessment."""
        return {
            "meets_requirements": False,
            "experience_gap": 3,
            "qualification_status": "unknown",
            "assessment_confidence": 0.0,
            "key_concerns": [f"Assessment error: {error_msg}"],
            "strengths": [],
            "should_continue": True,
            "assessment_reason": f"Unable to assess qualifications: {error_msg}"
        }

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
            # Add user message to chat history
            self.chat_history.add_user_message(user_message)
            
            # Trim messages to maintain window size
            messages = self.chat_history.messages
            if len(messages) > self.max_history_length * 2:  # Each turn has 2 messages (user + assistant)
                trimmed_messages = trim_messages(
                    messages,
                    max_tokens=self.max_history_length * 2,
                    strategy="last",
                    token_counter=len  # Simple message count instead of token count
                )
                self.chat_history.clear()
                for msg in trimmed_messages:
                    self.chat_history.add_message(msg)

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
                self.chat_history.add_ai_message(response)
                self.logger.info(f"Decision: {decision.value}, Reasoning: {reasoning}")
                return response, decision, reasoning
            
            # --- Otherwise, continue with normal decision logic ---
            decision, reasoning, response = await self._make_decision(user_message, conversation)

            await conversation.add_message("assistant", response, agent=self)
            conversation.add_decision(decision, reasoning, response)
            self.chat_history.add_ai_message(response)
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
            
            # CRITICAL: Don't make qualification assumptions on null/unknown data
            # Only be proactive about qualifications when we have actual experience information
            candidate_experience = conversation.candidate_info.get("experience")
            has_concrete_experience = (candidate_experience and 
                                     candidate_experience not in [None, "unknown", "mentioned", ""])
            
            # If candidate is underqualified AND we have concrete experience data, be proactive
            if (qualification_status == "underqualified" and 
                has_concrete_experience and  # Must have actual experience info, not null/unknown
                experience_gap >= 1 and  # 1+ year gap is significant for junior-mid level positions
                len(conversation.messages) <= 4 and  # Early in conversation
                not any("qualification" in msg.get("content", "").lower() or 
                       "experience" in msg.get("content", "").lower() or
                       "requirement" in msg.get("content", "").lower() 
                       for msg in conversation.messages[-3:] if msg.get("role") == "assistant")):
                
                self.logger.info(f"Proactively addressing qualification mismatch: {experience_gap} year gap")
                
                # Calculate actual years from concrete experience data (not assumptions)
                experience_details = conversation.candidate_info.get("experience_details", {})
                years_numeric = experience_details.get("years_numeric")
                
                if years_numeric is not None:
                    actual_years = years_numeric
                else:
                    # Try to parse from experience string
                    import re
                    years_match = re.search(r'(\d+)', str(candidate_experience))
                    actual_years = int(years_match.group(1)) if years_match else "unclear"
                
                # Get candidate name safely (handle null values)
                candidate_name = conversation.candidate_info.get('name')
                name_greeting = f"Hi {candidate_name}! " if candidate_name and candidate_name != "unknown" else "Hi! "
                
                proactive_response = f"""{name_greeting}I appreciate your interest in our Python Developer position. 

I want to be upfront with you - this role requires at least 3 years of Python development experience, and I see from your profile that you have {actual_years} years of experience. While there is an experience gap, I'd love to understand more about your background.

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
                    # User is confirming a previously offered slot - trigger actual booking
                    self.logger.info("SchedulingAdvisor detected slot confirmation. Triggering booking process.")
                    
                    # Try to match the user's confirmation to a specific slot
                    booking_result = await self._handle_slot_confirmation(
                        conversation, user_message, available_slots
                    )
                    
                    if booking_result.get('success'):
                        # Successful booking - return confirmation message
                        confirmation_msg = booking_result.get('confirmation_message', 
                                                            'Your interview has been scheduled successfully!')
                        return decision, f"Slot confirmed and booked. {schedule_reasoning}", confirmation_msg
                    else:
                        # Booking failed - ask for clarification
                        error_msg = f"I'd like to confirm your interview slot, but I need to clarify the specific time. {booking_result.get('error', 'Please let me know which specific date and time works for you.')}"
                        return AgentDecision.CONTINUE, f"Slot confirmation failed: {booking_result.get('error', 'unclear slot')}", error_msg
                
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

    async def _handle_slot_confirmation(
        self,
        conversation: ConversationState,
        user_message: str,
        available_slots: List[Dict]
    ) -> Dict:
        """
        Handle when user confirms a specific slot and trigger actual booking.
        
        Args:
            conversation: Current conversation state
            user_message: User's confirmation message (e.g., "9am is great")
            available_slots: List of available slots to match against
            
        Returns:
            Dict with booking result and confirmation details
        """
        try:
            # Extract time reference from user message
            import re
            from datetime import datetime, time, date, timedelta
            
            # Look for time patterns in user message
            time_patterns = [
                r'(\d{1,2})\s*am',
                r'(\d{1,2})\s*pm', 
                r'(\d{1,2}):(\d{2})\s*(am|pm)',
                r'(\d{1,2})\s*o\'?clock'
            ]
            
            matched_time = None
            for pattern in time_patterns:
                match = re.search(pattern, user_message.lower())
                if match:
                    if len(match.groups()) == 1:
                        # Simple hour format (e.g., "9am")
                        hour = int(match.group(1))
                        if 'pm' in user_message.lower() and hour != 12:
                            hour += 12
                        elif 'am' in user_message.lower() and hour == 12:
                            hour = 0
                        matched_time = time(hour, 0)
                    elif len(match.groups()) == 3:
                        # Hour:minute format (e.g., "9:30am")
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        if match.group(3).lower() == 'pm' and hour != 12:
                            hour += 12
                        elif match.group(3).lower() == 'am' and hour == 12:
                            hour = 0
                        matched_time = time(hour, minute)
                    break
            
            if not matched_time:
                return {
                    'success': False,
                    'error': 'Could not identify specific time from your message'
                }
            
            # Find matching slot
            best_match = None
            min_time_diff = float('inf')
            
            for slot in available_slots:
                slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                slot_time = slot_dt.time()
                
                # Calculate time difference in minutes
                slot_minutes = slot_time.hour * 60 + slot_time.minute
                matched_minutes = matched_time.hour * 60 + matched_time.minute
                time_diff = abs(slot_minutes - matched_minutes)
                
                # Consider it a match if within 30 minutes
                if time_diff <= 30 and time_diff < min_time_diff:
                    best_match = slot
                    min_time_diff = time_diff
            
            if not best_match:
                return {
                    'success': False,
                    'error': f'No available slots found near {matched_time.strftime("%I:%M %p")}'
                }
            
            # Book the appointment using SchedulingAdvisor
            candidate_info = conversation.candidate_info
            slot_datetime = datetime.fromisoformat(best_match['datetime'].replace('Z', '+00:00'))
            recruiter_id = best_match.get('recruiter_id', 1)
            slot_id = best_match.get('id')
            
            booking_result = self.scheduling_advisor.book_appointment(
                candidate_info,
                slot_datetime,
                recruiter_id,
                45,  # 45 minutes duration
                slot_id
            )
            
            if booking_result['success']:
                self.logger.info(f"Successfully booked appointment {booking_result.get('appointment_id')}")
                
                # Update conversation state to mark as completed
                conversation.candidate_info['appointment_booked'] = True
                conversation.candidate_info['appointment_details'] = {
                    'datetime': slot_datetime.strftime("%A, %B %d, %Y at %I:%M %p"),
                    'recruiter': booking_result.get('recruiter', {}).get('name', 'Our recruiter'),
                    'appointment_id': booking_result.get('appointment_id')
                }
                
                return {
                    'success': True,
                    'confirmation_message': booking_result.get('confirmation_message', ''),
                    'appointment_details': conversation.candidate_info['appointment_details']
                }
            else:
                return {
                    'success': False,
                    'error': booking_result.get('error', 'Unknown booking error')
                }
                
        except Exception as e:
            self.logger.error(f"Error handling slot confirmation: {e}")
            return {
                'success': False,
                'error': f'Booking system error: {str(e)}'
            }

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
    
    async def extract_missing_info_llm(self, conversation: ConversationState, missing_fields: List[str]) -> Dict:
        """
        Extract only specific missing information fields using targeted LLM analysis.
        Used in form-based mode to preserve existing structured data.
        """
        import json
        import re
        
        # Define regex pattern at method level to avoid f-string conflicts
        json_pattern = r'\{.*\}'
        
        try:
            # Create targeted extraction prompt for missing fields only
            fields_description = {
                "name": "candidate's name from introductions or mentions",
                "experience": "Python development experience (years, level, technologies)",
                "availability": "scheduling availability, time preferences, or readiness to interview",
                "interest_level": "level of interest in the position (high/medium/low)"
            }
            
            missing_descriptions = [f"- {field}: {fields_description.get(field, field)}" for field in missing_fields]
            
            # Format existing form data as clean JSON (not markdown)
            existing_data_json = json.dumps({
                key: value for key, value in conversation.candidate_info.items()
                if value not in [None, "", {}, [], "unknown"]
            }, indent=2)
            
            conversation_json = json.dumps([
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation.messages[-5:]  # Recent messages for context
            ], indent=2)
            
            targeted_prompt = f"""You are extracting ONLY specific missing information from a conversation to supplement existing form data.

EXISTING_FORM_DATA_JSON:
{existing_data_json}

CONVERSATION_HISTORY_JSON:
{conversation_json}

EXTRACTION_TASK_MISSING_FIELDS_ONLY:
The candidate has already provided structured form data above. Extract ONLY the following missing information from the conversation:
{chr(10).join(missing_descriptions)}

CRITICAL_INSTRUCTIONS:
- DO NOT extract or suggest information that already exists in the form data
- Only extract information for the specific missing fields requested
- If information already exists in form data, leave it as null in your response
- Do not duplicate or override existing form information
- Respond with ONLY valid JSON, no markdown formatting

REQUIRED_JSON_RESPONSE_FORMAT:
{{
  "name": "candidate name or null if not found/already in form",
  "experience": "specific experience details or null if not mentioned/already in form",
  "availability": true/false if availability is mentioned in conversation,
  "interest_level": "high/medium/low/unknown based on conversation engagement",
  "conversation_sentiment": {{
    "overall_tone": "positive/neutral/negative",
    "engagement_level": "high/medium/low",
    "communication_quality": "excellent/good/fair/poor"
  }}
}}

Extract only what is clearly mentioned in the conversation and NOT already in the form data. JSON_RESPONSE_ONLY:"""

            # Get LLM response
            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": targeted_prompt})
            response_text = response.content.strip()
            
            # Parse JSON response
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            extracted_data = json.loads(response_text)
            
            # Map availability field
            if "availability" in extracted_data:
                extracted_data["availability_mentioned"] = extracted_data.pop("availability")
            
            self.logger.info(f"Targeted extraction for missing fields {missing_fields}: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error in targeted missing info extraction: {e}")
            return {
                "conversation_sentiment": {
                    "overall_tone": "neutral",
                    "engagement_level": "medium",
                    "communication_quality": "good"
                }
            }

    async def extract_simple_info_llm(self, conversation: ConversationState, fields: List[str]) -> Dict:
        """
        Extract very basic information using simple LLM analysis.
        Used in minimal data mode for short interactions.
        """
        import json
        import re
        
        # Define regex pattern at method level to avoid f-string conflicts
        json_pattern = r'\{.*\}'
        
        try:
            latest_message = conversation.messages[-1].get("content", "") if conversation.messages else ""
            
            simple_prompt = f"""Extract basic information from this message:

Message: "{latest_message}"

Extract only what is explicitly mentioned:
- name: person's name if mentioned
- basic_info: any other basic information

Respond with JSON:
{{
  "name": "name or null",
  "basic_info": "any other info or null"
}}"""

            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": simple_prompt})
            response_text = response.content.strip()
            
            # Parse JSON
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            extracted_data = json.loads(response_text)
            
            self.logger.info(f"Simple extraction: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error in simple info extraction: {e}")
            return {}

    async def extract_qualification_assessment_llm(self, conversation: ConversationState) -> Dict:
        """
        Safe qualification assessment extraction using JSON-first approach.
        
        This method extracts ONLY qualification assessment without touching any existing data.
        Uses JSON formatting to prevent markdown contamination issues.
        """
        try:
            import json
            
            # Format existing candidate data as clean JSON (not markdown)
            existing_data_json = json.dumps({
                key: value for key, value in conversation.candidate_info.items()
                if value not in [None, "", {}, [], "unknown"]
            }, indent=2)
            
            # Format conversation history as JSON
            conversation_json = json.dumps([
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation.messages[-5:]  # Last 5 messages for context
            ], indent=2)
            
            # Create JSON-first qualification assessment prompt
            assessment_prompt = f"""You are a qualification assessment specialist. Extract qualification assessment ONLY.

CRITICAL INSTRUCTIONS:
- Analyze candidate against Python Developer position requirements
- Minimum requirement: 3+ years Python development experience
- Respond with ONLY valid JSON, NO markdown formatting
- Do not include any explanatory text or headers
- **CRITICAL**: If there's insufficient experience data, use "unknown" status, NOT negative assumptions

EXISTING_CANDIDATE_DATA:
{existing_data_json}

RECENT_CONVERSATION:
{conversation_json}

ASSESSMENT_TASK:
Evaluate if candidate meets "3+ years Python development experience" requirement based on existing data and conversation.

**IMPORTANT NULL/EMPTY DATA HANDLING**:
- If candidate data is empty/null (like just "hi" message) → qualification_status: "unknown" 
- If no concrete experience mentioned → experience_gap: 0 and qualification_status: "unknown"
- If conversation is minimal (greetings only) → assessment_confidence: 0.0
- DO NOT assume "0 years experience" from null/empty data
- Only assess when you have actual experience information to evaluate

REQUIRED_JSON_RESPONSE_FORMAT:
{{
  "qualification_assessment": {{
    "meets_requirements": false for unknown status,
    "experience_gap": 0 if unknown, actual gap if known,
    "qualification_status": "qualified/underqualified/overqualified/unknown",
    "assessment_confidence": 0.0 for unknown, 0.1-1.0 for actual assessments,
    "key_concerns": ["Insufficient information to assess qualifications"] for unknown,
    "strengths": ["Expressed interest in position"] for unknown or actual strengths,
    "assessment_reason": "Need more information about experience and qualifications" for unknown
  }}
}}

**EXAMPLE FOR MINIMAL DATA (like "hi" message)**:
{{
  "qualification_assessment": {{
    "meets_requirements": false,
    "experience_gap": 0,
    "qualification_status": "unknown",
    "assessment_confidence": 0.0,
    "key_concerns": ["Insufficient information to assess qualifications"],
    "strengths": ["Expressed initial interest in position"],
    "assessment_reason": "Need more information about experience and qualifications"
  }}
}}

JSON_RESPONSE_ONLY:"""

            # Get LLM response
            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": assessment_prompt})
            response_text = response.content.strip()
            
            self.logger.debug(f"Raw qualification assessment response: {response_text}")
            
            # Enhanced JSON parsing
            import re
            
            # Remove any potential markdown formatting
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Find JSON object in response
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            # Parse JSON
            assessment_data = json.loads(response_text)
            
            # Validate response structure
            if "qualification_assessment" in assessment_data:
                assessment = assessment_data["qualification_assessment"]
                
                # Add calculated fields for backward compatibility
                assessment["should_continue"] = not assessment.get("meets_requirements", True)
                
                self.logger.info(f"[OK] QUALIFICATION ASSESSMENT EXTRACTED: {assessment}")
                return {"qualification_assessment": assessment}
            else:
                raise ValueError("No qualification_assessment key in LLM response")
            
        except Exception as e:
            self.logger.error(f"Error in JSON-first qualification assessment: {e}")
            self.logger.error(f"Raw response: {response_text if 'response_text' in locals() else 'N/A'}")
            
            # Return empty dict - calling method will handle fallback
            return {}

    async def extract_candidate_info_llm(self, conversation: ConversationState) -> Dict:
        """
        Enhanced contextual candidate information extraction using LLM analysis.
        
        This method uses the full conversation context to synthesize comprehensive
        candidate information, including automatic qualification assessment.
        """
        import json
        import re
        
        # Define regex pattern at method level to avoid f-string conflicts
        json_pattern = r'\{.*\}'
        
        try:
            # Check if we have existing form data to preserve
            has_existing_data = bool(conversation.candidate_info and 
                                   any(v not in [None, "", {}, [], "unknown"] 
                                       for v in conversation.candidate_info.values()))
            
            if has_existing_data:
                # Create context-aware prompt using JSON formatting (not markdown)
                existing_data_json = json.dumps({
                    key: value for key, value in conversation.candidate_info.items()
                    if value not in [None, "", {}, [], "unknown"]
                }, indent=2)
                
                conversation_json = json.dumps([
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation.messages[-8:]  # Last 8 messages for context
                ], indent=2)
                
                extraction_prompt = f"""You are analyzing a conversation to extract comprehensive candidate information. 
CRITICAL: The candidate has ALREADY provided information via form submission. You must PRESERVE all existing data and ENHANCE it with conversation details.

EXISTING_CANDIDATE_DATA_JSON:
{existing_data_json}

CONVERSATION_HISTORY_JSON:
{conversation_json}

ENHANCED_EXTRACTION_TASK:
- PRESERVE all existing form data exactly as provided above
- ENHANCE the profile with additional details from the conversation
- FILL any missing fields from conversation context
- DO NOT override or change existing form data
- SUPPLEMENT the information, don't replace it
- Respond with ONLY valid JSON, no markdown formatting

Use the enhanced extraction format but maintain all existing data integrity. Respond with valid JSON only."""
            else:
                # Standard extraction prompt for pure conversation mode
                extraction_prompt = self.prompts.get_candidate_info_extraction_prompt(conversation.messages)
            
            # Get LLM analysis with full context
            response = await self.candidate_info_chain.ainvoke({"extraction_prompt": extraction_prompt})
            response_text = response.content.strip()
            
            self.logger.debug(f"Raw LLM extraction response: {response_text}")
            
            # Parse JSON response with enhanced error handling
            # Clean and extract JSON from response
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            extracted_data = json.loads(response_text)
            
            # Enhanced data processing with comprehensive mapping
            # CRITICAL FIX: Handle both string and dict formats for experience/qualification data
            raw_experience = extracted_data.get("experience", {})
            raw_qualification = extracted_data.get("qualification_assessment", {})
            
            # Convert experience data to dict format if it's a string
            if isinstance(raw_experience, str):
                experience_data = {
                    "years": raw_experience if raw_experience not in ["unknown", ""] else None,
                    "level": None,
                    "years_numeric": self._extract_years_from_string(raw_experience),
                    "technologies": ["python"] if raw_experience and "python" in raw_experience.lower() else [],
                    "has_python": raw_experience and "python" in raw_experience.lower(),
                    "python_details": None,
                    "career_level": "unknown"
                }
            else:
                experience_data = raw_experience or {}
            
            # Convert qualification data to dict format if needed
            if isinstance(raw_qualification, dict):
                qualification_data = raw_qualification
            else:
                qualification_data = {}
            
            # Convert to enhanced candidate_info format with backward compatibility
            candidate_info = {
                # Basic information
                "name": extracted_data.get("name"),
                "email": extracted_data.get("email"), 
                "phone": extracted_data.get("phone"),
                "current_status": extracted_data.get("current_status"),
                "interest_level": extracted_data.get("interest_level", "unknown"),
                "availability_mentioned": extracted_data.get("availability_mentioned", False),
                "availability_details": extracted_data.get("availability_details"),
                "position_interest": extracted_data.get("position_interest"),
                
                # Enhanced experience information
                "experience": self._format_experience_field(experience_data),
                "experience_details": {
                    "level": experience_data.get("level"),
                    "years": experience_data.get("years"),
                    "years_numeric": experience_data.get("years_numeric"),
                    "technologies": experience_data.get("technologies", []),
                    "has_python": experience_data.get("has_python", False),
                    "python_details": experience_data.get("python_details"),
                    "career_level": experience_data.get("career_level", "unknown")
                },
                
                # Integrated qualification assessment
                "qualification_assessment": {
                    "meets_requirements": qualification_data.get("meets_requirements", False),
                    "experience_gap": qualification_data.get("experience_gap_years", 0),
                    "qualification_status": qualification_data.get("qualification_status", "unknown"),
                    "assessment_confidence": qualification_data.get("assessment_confidence", 0.0),
                    "key_concerns": qualification_data.get("key_concerns", []),
                    "strengths": qualification_data.get("strengths", []),
                    "should_continue": not qualification_data.get("meets_requirements", True),  # Continue if underqualified
                    "assessment_reason": self._generate_assessment_reason(qualification_data, experience_data)
                },
                
                # Conversation context
                "conversation_sentiment": extracted_data.get("conversation_sentiment", {}),
                "extraction_metadata": extracted_data.get("extraction_metadata", {})
            }
            
            self.logger.info(f"Enhanced LLM-extracted candidate info: {candidate_info}")
            self.logger.info(f"Qualification assessment: {candidate_info['qualification_assessment']}")
            
            return candidate_info
            
        except Exception as e:
            self.logger.error(f"Error in enhanced LLM candidate info extraction: {e}")
            self.logger.error(f"Raw response that caused error: {response_text if 'response_text' in locals() else 'N/A'}")
            
            # Return enhanced default structure
            return {
                "name": None,
                "experience": "unknown",
                "current_status": None,
                "interest_level": "unknown", 
                "availability_mentioned": False,
                "email": None,
                "phone": None,
                "experience_details": {
                    "level": None,
                    "years": None,
                    "years_numeric": None,
                    "technologies": [],
                    "has_python": False,
                    "python_details": None,
                    "career_level": "unknown"
                },
                "qualification_assessment": {
                    "meets_requirements": False,
                    "experience_gap": 3,
                    "qualification_status": "unknown",
                    "assessment_confidence": 0.0,
                    "key_concerns": ["Unable to assess qualifications due to extraction error"],
                    "strengths": [],
                    "should_continue": True,
                    "assessment_reason": f"Assessment error: {str(e)}"
                },
                "conversation_sentiment": {},
                "extraction_metadata": {"error": str(e)}
            }
    
    def _format_experience_field(self, experience_data: Dict) -> str:
        """Format experience data for backward compatibility with existing code."""
        if not experience_data:
            return "unknown"
        
        # Preserve specific experience details
        years = experience_data.get("years")
        level = (experience_data.get("level") or "").lower()
        has_python = experience_data.get("has_python", False)
        
        if years and has_python:
            return f"{years} Python"
        elif years and "python" in level:
            return f"{years} Python"
        elif years:
            return f"{years} years"
        elif has_python:
            return "mentioned Python"
        elif level and level != "null":
            return "mentioned"
        else:
            return "unknown"
    
    def _generate_assessment_reason(self, qualification_data: Dict, experience_data: Dict) -> str:
        """Generate human-readable assessment reason with proper null handling."""
        status = qualification_data.get("qualification_status", "unknown")
        gap = qualification_data.get("experience_gap_years", 0)
        years_numeric = experience_data.get("years_numeric")
        
        # Handle null values safely
        if gap is None:
            gap = 0
        if years_numeric is None:
            years_numeric = 0
        
        if status == "underqualified" and gap > 0 and years_numeric > 0:
            return f"Candidate has {years_numeric} years experience, needs 3+ years (gap: {gap} years)"
        elif status == "qualified":
            return f"Candidate meets experience requirements"
        elif status == "overqualified":
            return f"Candidate exceeds experience requirements"
        elif status == "unknown":
            return f"Need more information about experience and qualifications"
        else:
            return f"Assessment status: {status}"

    def _extract_years_from_string(self, experience_str: str) -> Optional[int]:
        """Extract numeric years from experience string (e.g., '1 years' -> 1)."""
        if not experience_str or experience_str in ["unknown", ""]:
            return None
        
        import re
        # Look for patterns like "1 years", "3+ years", "5 year", etc.
        match = re.search(r'(\d+)', experience_str)
        if match:
            return int(match.group(1))
        return None

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
        self.chat_history.add_ai_message(greeting)
        
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
        self.chat_history.clear()
    
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