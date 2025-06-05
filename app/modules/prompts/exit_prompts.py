"""Exit Advisor prompts and examples for conversation end detection."""

from typing import List, Dict
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# System prompt for exit detection
EXIT_SYSTEM_PROMPT = """You are an Exit Advisor agent specialized in detecting when a conversation should end.
Your role is to analyze conversation context and determine if the user wants to end the conversation or if it has naturally concluded.

Key Responsibilities:
1. Detect explicit exit requests (e.g., "goodbye", "thank you", "that's all")
2. Identify implicit exit signals (e.g., user satisfaction, task completion)
3. Generate appropriate farewell messages
4. Provide confidence scores for exit decisions

IMPORTANT:
- Do NOT end the conversation if the user is describing their experience, education, skills, or background. This is usually a sign of engagement and interest.
- Only end the conversation if the user clearly expresses disinterest, says they want to stop, or gives an explicit exit signal.
- If in doubt, prefer to continue the conversation.

Consider the following factors:
- Current conversation context and flow
- User's explicit and implicit intentions
- Whether all necessary information has been exchanged
- Whether the user's needs have been met
- Natural conversation patterns and social cues

Your response should be structured as follows:
{
    "should_exit": boolean,
    "confidence": float (0-1),
    "reason": string,
    "farewell_message": string (if should_exit is true)
}"""

# Few-shot examples for exit detection
EXIT_EXAMPLES = [
    {
        "input": "Thank you for your help, I think I have all the information I need.",
        "output": {
            "should_exit": True,
            "confidence": 0.95,
            "reason": "User explicitly indicates satisfaction and completion",
            "farewell_message": "You're welcome! I'm glad I could help. If you have any more questions in the future, feel free to reach out. Have a great day!"
        }
    },
    {
        "input": "I need to think about this and get back to you later.",
        "output": {
            "should_exit": True,
            "confidence": 0.9,
            "reason": "User indicates need for time to consider and will return later",
            "farewell_message": "Of course! Take your time to think it over. When you're ready to continue, just let me know. Have a great day!"
        }
    },
    {
        "input": "What are the next steps in the interview process?",
        "output": {
            "should_exit": False,
            "confidence": 0.95,
            "reason": "User is actively seeking more information about the process",
            "farewell_message": None
        }
    },
    {
        "input": "Goodbye, thanks for your time!",
        "output": {
            "should_exit": True,
            "confidence": 0.99,
            "reason": "Explicit exit request with gratitude",
            "farewell_message": "Thank you for your time! It was a pleasure assisting you. If you need anything else, don't hesitate to reach out. Have a wonderful day!"
        }
    },
    {
        "input": "I am a student who has just completed a certificate in deep-level Python development training.",
        "output": {
            "should_exit": False,
            "confidence": 0.98,
            "reason": "User is describing their background and is likely interested in continuing the conversation.",
            "farewell_message": None
        }
    },
    {
        "input": "I have 3 years of experience in backend development and recently finished my degree in computer science.",
        "output": {
            "should_exit": False,
            "confidence": 0.98,
            "reason": "User is describing their experience and education, indicating engagement.",
            "farewell_message": None
        }
    },
    {
        "input": "I recently completed a bootcamp in software engineering and am eager to apply my skills.",
        "output": {
            "should_exit": False,
            "confidence": 0.98,
            "reason": "User is sharing recent education and motivation, not an exit signal.",
            "farewell_message": None
        }
    },
    {
        "input": "I'll pass on this opportunity",
        "output": {
            "should_exit": True,
            "confidence": 0.95,
            "reason": "User explicitly declines the opportunity",
            "farewell_message": "Thank you for letting me know. If you change your mind or are interested in future opportunities, please feel free to reach out. We wish you all the best in your current endeavors. Have a great day!"
        }
    },
    {
        "input": "I will pass on this opportunity",
        "output": {
            "should_exit": True,
            "confidence": 0.95,
            "reason": "User explicitly declines the opportunity",
            "farewell_message": "Thank you for letting me know. If you change your mind or are interested in future opportunities, please feel free to reach out. We wish you all the best in your current endeavors. Have a great day!"
        }
    },
    {
        "input": "I'm more interested in Java development role rather than python",
        "output": {
            "should_exit": True,
            "confidence": 0.95,
            "reason": "User indicates preference for a different technology/role, not interested in Python position",
            "farewell_message": "Thank you for letting me know! Unfortunately, my focus is on the Python developer position, but I wish you the best in finding a Java development role that suits your interests and skills. If you have any other questions, feel free to ask."
        }
    },
    {
        "input": "I'm not interested in this position",
        "output": {
            "should_exit": True,
            "confidence": 0.95,
            "reason": "User explicitly states lack of interest in the position",
            "farewell_message": "Thank you for letting me know. If you change your mind or are interested in future opportunities, please feel free to reach out. We wish you all the best in your current endeavors. Have a great day!"
        }
    }
]

# Template for exit detection
EXIT_DETECTION_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content=EXIT_SYSTEM_PROMPT),
    *[HumanMessage(content=example["input"]) for example in EXIT_EXAMPLES],
    *[AIMessage(content=str(example["output"])) for example in EXIT_EXAMPLES],
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    HumanMessage(content="{input}")
])

# Farewell message templates
FAREWELL_TEMPLATES = {
    "standard": "Thank you for your time! If you need anything else, feel free to reach out. Have a great day!",
    "scheduling_complete": "Great! Your interview has been scheduled. We look forward to meeting you. If you need to make any changes, please let us know. Have a wonderful day!",
    "information_provided": "I'm glad I could provide the information you needed. If you have any more questions, don't hesitate to ask. Have a great day!",
    "consideration": "Thank you for your interest. Take your time to consider the opportunity. When you're ready to proceed, we'll be here. Have a great day!",
    "technical_issue": "I apologize for any technical difficulties. Please try again later or contact our support team. Have a great day!"
}

def get_farewell_template(context: Dict) -> str:
    """Get appropriate farewell template based on conversation context."""
    if context.get("scheduling_completed"):
        return FAREWELL_TEMPLATES["scheduling_complete"]
    elif context.get("information_provided"):
        return FAREWELL_TEMPLATES["information_provided"]
    elif context.get("needs_consideration"):
        return FAREWELL_TEMPLATES["consideration"]
    elif context.get("technical_issue"):
        return FAREWELL_TEMPLATES["technical_issue"]
    return FAREWELL_TEMPLATES["standard"]

# Exit detection confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "high_confidence": 0.9,  # Very likely to be an exit
    "medium_confidence": 0.7,  # Probably an exit
    "low_confidence": 0.5,  # Might be an exit
}

# Exit signal patterns
EXIT_SIGNALS = {
    "explicit": [
        "goodbye", "bye", "thank you", "thanks", "that's all",
        "that's it", "I'm done", "finished", "complete",
        "no more questions", "nothing else", "pass on this",
        "not interested", "decline", "no thank you", "more interested in",
        "prefer", "focused on", "looking for something else"
    ],
    "implicit": [
        "I'll think about it", "get back to you",
        "consider it", "let you know", "check and return",
        "look into it", "review the information"
    ]
} 