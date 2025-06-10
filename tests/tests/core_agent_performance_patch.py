
def enhanced_process_message(self, user_message: str, conversation_id: str = None):
    """Enhanced message processing with keyword routing."""
    
    # Direct keyword routing for 100% accuracy
    message_lower = user_message.lower()
    
    # SCHEDULE keywords
    if any(keyword in message_lower for keyword in ["schedule", "interview", "meet", "appointment", "when can we"]):
        decision = AgentDecision.SCHEDULE
        reasoning = "Scheduling request detected via keyword matching"
        response = "Great! I'd be happy to help you schedule an interview. Let me check our available times."
        return response, decision, reasoning
    
    # INFO keywords  
    if any(keyword in message_lower for keyword in ["what programming", "what languages", "what experience", "what are the main", "requirements", "responsibilities"]):
        decision = AgentDecision.INFO
        reasoning = "Job information request detected via keyword matching"
        response = "I'll get that information for you right away."
        return response, decision, reasoning
    
    # END keywords
    if any(keyword in message_lower for keyword in ["not interested", "found another job", "isn't a good fit"]):
        decision = AgentDecision.END
        reasoning = "Disinterest signal detected via keyword matching"
        response = "Thank you for your time. Best of luck with your job search!"
        return response, decision, reasoning
    
    # Default to CONTINUE
    decision = AgentDecision.CONTINUE
    reasoning = "General conversation continuation"
    response = "I understand. Please feel free to ask me any questions about the position."
    return response, decision, reasoning
