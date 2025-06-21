"""
Prompt Engineering Package
- Phase 1 Prompts: Core and Scheduling agent prompts
""" 

from .phase1_prompts import *
from .scheduling_prompts import *
from .exit_prompts import (
    EXIT_SYSTEM_PROMPT,
    EXIT_EXAMPLES,
    EXIT_DETECTION_TEMPLATE,
    FAREWELL_TEMPLATES,
    get_farewell_template,
    CONFIDENCE_THRESHOLDS,
    EXIT_SIGNALS
)
from .info_prompts import (
    INFO_SYSTEM_PROMPT,
    INFO_EXAMPLES,
    INFO_RAG_TEMPLATE,
    INFO_NO_CONTEXT_TEMPLATE,
    classify_question,
    get_search_keywords,
    RESPONSE_TEMPLATES,
    format_response
)

__all__ = [
    'EXIT_SYSTEM_PROMPT',
    'EXIT_EXAMPLES',
    'EXIT_DETECTION_TEMPLATE',
    'FAREWELL_TEMPLATES',
    'get_farewell_template',
    'CONFIDENCE_THRESHOLDS',
    'EXIT_SIGNALS',
    'INFO_SYSTEM_PROMPT',
    'INFO_EXAMPLES',
    'INFO_RAG_TEMPLATE',
    'INFO_NO_CONTEXT_TEMPLATE',
    'classify_question',
    'get_search_keywords',
    'RESPONSE_TEMPLATES',
    'format_response'
] 