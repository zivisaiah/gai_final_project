"""Info Advisor prompts and templates for job-related Q&A using RAG."""

from typing import List, Dict, Any
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older langchain versions
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.schema import SystemMessage, HumanMessage, AIMessage

# System prompt for information advisor
INFO_SYSTEM_PROMPT = """You are an Information Advisor agent specialized in answering job-related questions using company information.
Your role is to provide accurate, helpful, and contextually relevant information about the Python Developer position.

Key Responsibilities:
1. Answer questions about job requirements, responsibilities, and qualifications
2. Provide information about company culture, benefits, and work environment
3. Clarify technical requirements and expectations
4. Use retrieved context to provide accurate information
5. Maintain a professional but friendly conversational tone

IMPORTANT GUIDELINES:
- ONLY use information from the provided context/documents
- If you don't have information about something, say so clearly
- Be concise but comprehensive in your responses
- Reference specific job requirements when relevant
- Encourage follow-up questions if needed
- Stay focused on the Python Developer position

CONTEXT INTEGRATION:
- You will receive relevant document excerpts as context
- Use this context to answer questions accurately
- Don't make up information not in the context
- If context doesn't fully answer the question, acknowledge limitations

Your response should be natural conversational text that:
- Directly addresses the user's question
- Incorporates relevant information from the context
- Maintains professional but approachable tone
- Encourages continued engagement when appropriate"""

# Few-shot examples for information responses
INFO_EXAMPLES = [
    {
        "input": "What programming languages are required for this position?",
        "context": "The position requires strong proficiency in Python, with experience in frameworks like Django or Flask. Knowledge of JavaScript, HTML, and CSS is also valuable.",
        "output": "For this Python Developer position, you'll need strong proficiency in Python as the primary requirement. Experience with Python frameworks like Django or Flask is essential. Additionally, knowledge of web technologies including JavaScript, HTML, and CSS would be valuable for this role. The focus is definitely on Python development, but having that additional web development knowledge will make you a stronger candidate."
    },
    {
        "input": "What are the main responsibilities of this role?",
        "context": "Key responsibilities include developing and maintaining Python applications, collaborating with cross-functional teams, writing clean and efficient code, conducting code reviews, and contributing to system architecture decisions.",
        "output": "The main responsibilities for this Python Developer role include several key areas: You'll be developing and maintaining Python applications, which is the core of the position. You'll collaborate with cross-functional teams, so teamwork and communication skills are important. Writing clean, efficient code is a priority, and you'll participate in code reviews to maintain code quality. You'll also have the opportunity to contribute to system architecture decisions, which means your input on technical direction will be valued."
    },
    {
        "input": "What experience level is required?",
        "context": "We're looking for candidates with 2-5 years of experience in Python development, with demonstrated experience in building web applications and working with databases.",
        "output": "This position is looking for candidates with 2-5 years of experience in Python development. The key requirement is demonstrated experience building web applications and working with databases. So if you're a mid-level developer with solid Python experience and have worked on web projects involving database integration, you'd be a good fit for this role."
    },
    {
        "input": "Do you offer remote work options?",
        "context": "",
        "output": "I don't have specific information about remote work options in the job description I have access to. This is definitely an important question, and I'd recommend asking about the company's remote work policy and flexibility during your interview process. Many companies today offer hybrid or remote options, but I want to make sure you get accurate information directly from the hiring team."
    }
]

# Template for information Q&A with RAG
INFO_RAG_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content=INFO_SYSTEM_PROMPT),
    HumanMessage(content="Context from job documents:\n{context}\n\nQuestion: {question}"),
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    HumanMessage(content="Please provide a helpful answer based on the context and your knowledge of the position.")
])

# Template for when no context is available
INFO_NO_CONTEXT_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are an Information Advisor for a Python Developer position. 
    A user has asked a question, but no relevant context was found in the job documents.
    
    Provide a helpful response that:
    1. Acknowledges you don't have specific information about their question
    2. Suggests they ask during the interview process
    3. Maintains a helpful and professional tone
    4. Encourages them to continue asking other questions you might be able to help with"""),
    HumanMessage(content="Question: {question}"),
    HumanMessage(content="Please provide a helpful response explaining that you don't have specific information about this topic.")
])

# Question classification patterns
QUESTION_PATTERNS = {
    "technical_requirements": [
        "programming language", "technology", "framework", "tool", "stack",
        "python", "django", "flask", "database", "sql", "api", "git"
    ],
    "job_responsibilities": [
        "responsibilities", "duties", "tasks", "day to day", "work on",
        "projects", "role", "position", "job", "do in this role"
    ],
    "qualifications": [
        "experience", "qualification", "requirement", "skill", "background",
        "education", "degree", "certification", "years", "level"
    ],
    "company_culture": [
        "culture", "environment", "team", "workplace", "company", "benefits",
        "remote", "office", "flexible", "work life balance"
    ],
    "career_growth": [
        "growth", "advancement", "career", "promotion", "development",
        "learning", "training", "mentorship", "future"
    ],
    "compensation": [
        "salary", "compensation", "benefits", "vacation", "insurance",
        "equity", "bonus", "pay", "package"
    ]
}

def classify_question(question: str) -> str:
    """Classify the type of question being asked."""
    question_lower = question.lower()
    
    for category, keywords in QUESTION_PATTERNS.items():
        if any(keyword in question_lower for keyword in keywords):
            return category
    
    return "general"

def get_search_keywords(question: str) -> List[str]:
    """Extract relevant keywords for vector search from the question."""
    # Simple keyword extraction - can be enhanced with NLP
    question_lower = question.lower()
    
    # Technical keywords
    tech_keywords = [
        "python", "django", "flask", "javascript", "html", "css", "sql",
        "database", "api", "framework", "git", "testing", "deployment"
    ]
    
    # Job-related keywords
    job_keywords = [
        "experience", "responsibility", "requirement", "qualification",
        "skill", "education", "team", "project", "development"
    ]
    
    found_keywords = []
    for keyword in tech_keywords + job_keywords:
        if keyword in question_lower:
            found_keywords.append(keyword)
    
    # Always include the original question for semantic search
    found_keywords.append(question_lower)
    
    return found_keywords if found_keywords else [question_lower]

# Response templates for different scenarios
RESPONSE_TEMPLATES = {
    "context_available": """Based on the job information I have, {response}

Feel free to ask me any other questions about the position!""",
    
    "partial_context": """From what I can see in the job description, {response}

However, I don't have complete information about this topic. I'd recommend asking for more details during your interview to get the full picture.

Is there anything else about the position I can help clarify?""",
    
    "no_context": """I don't have specific information about {topic} in the job description I have access to. This is definitely something worth discussing during the interview process to get accurate and up-to-date information.

I can help answer questions about the technical requirements, job responsibilities, and qualifications that are outlined in the position description. Is there anything else you'd like to know about those areas?""",
    
    "general_encouragement": """That's a great question! While I can provide information about the Python Developer position based on the job description, some details are best discussed directly with the hiring team during the interview process.

I'm here to help with any questions about the role requirements, responsibilities, or technical aspects. What else would you like to know?"""
}

def format_response(response: str, context_quality: str = "context_available", **kwargs) -> str:
    """Format the response based on context quality and additional parameters."""
    template = RESPONSE_TEMPLATES.get(context_quality, RESPONSE_TEMPLATES["general_encouragement"])
    
    try:
        return template.format(response=response, **kwargs)
    except KeyError:
        # If formatting fails, return the response as is
        return response 