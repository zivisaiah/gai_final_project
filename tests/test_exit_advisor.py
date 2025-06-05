"""Tests for the Exit Advisor agent."""

import pytest
from typing import List, Dict
from app.modules.agents.exit_advisor import ExitAdvisor, ExitDecision
from app.modules.prompts.exit_prompts import EXIT_SIGNALS

@pytest.fixture
def exit_advisor():
    """Create an Exit Advisor instance for testing."""
    return ExitAdvisor(temperature=0.1)

@pytest.fixture
def sample_conversation_history():
    """Create a sample conversation history for testing."""
    return [
        {"role": "user", "content": "Hello, I'm interested in the Python developer position."},
        {"role": "assistant", "content": "Welcome! I'd be happy to help you with the application process."},
        {"role": "user", "content": "What are the requirements for the position?"},
        {"role": "assistant", "content": "The position requires Python experience, knowledge of web frameworks, and database skills."}
    ]

@pytest.mark.asyncio
async def test_explicit_exit_detection(exit_advisor):
    """Test detection of explicit exit signals."""
    message = "Thank you for your help, goodbye!"
    decision = await exit_advisor.analyze_conversation(message, [])
    
    assert decision.should_exit is True
    assert decision.confidence >= 0.9
    assert "goodbye" in decision.reason.lower()
    assert decision.farewell_message is not None

@pytest.mark.asyncio
async def test_implicit_exit_detection(exit_advisor):
    """Test detection of implicit exit signals."""
    message = "I'll think about it and get back to you later."
    decision = await exit_advisor.analyze_conversation(message, [])
    
    assert decision.should_exit is True
    assert decision.confidence >= 0.7
    assert "think" in decision.reason.lower()
    assert decision.farewell_message is not None

@pytest.mark.asyncio
async def test_continuation_detection(exit_advisor):
    """Test detection of conversation continuation."""
    message = "What are the next steps in the interview process?"
    decision = await exit_advisor.analyze_conversation(message, [])
    
    assert decision.should_exit is False
    assert decision.confidence >= 0.7
    assert decision.farewell_message is None

@pytest.mark.asyncio
async def test_task_completion_detection(exit_advisor, sample_conversation_history):
    """Test detection of task completion as exit signal."""
    message = "Great, I've scheduled the interview for next week. That's all I needed!"
    decision = await exit_advisor.analyze_conversation(message, sample_conversation_history)
    
    assert decision.should_exit is True
    assert decision.confidence >= 0.8
    assert any(word in decision.reason.lower() for word in ["complete", "scheduled", "finished"])
    assert "scheduled" in decision.farewell_message.lower()

@pytest.mark.asyncio
async def test_satisfaction_detection(exit_advisor, sample_conversation_history):
    """Test detection of user satisfaction as exit signal."""
    message = "Thank you, that's exactly the information I needed!"
    decision = await exit_advisor.analyze_conversation(message, sample_conversation_history)
    
    assert decision.should_exit is True
    assert decision.confidence >= 0.8
    assert "satisfaction" in decision.reason.lower() or "complete" in decision.reason.lower()
    assert decision.farewell_message is not None

@pytest.mark.asyncio
async def test_technical_issue_detection(exit_advisor):
    """Test detection of technical issues as exit signal."""
    message = "I'm having some technical issues with the chat. I'll try again later."
    decision = await exit_advisor.analyze_conversation(message, [])
    
    assert decision.should_exit is True
    assert decision.confidence >= 0.7
    assert "technical" in decision.reason.lower() or "issue" in decision.reason.lower()
    assert "technical" in decision.farewell_message.lower()

def test_explicit_exit_signals(exit_advisor):
    """Test explicit exit signal detection function."""
    for signal in EXIT_SIGNALS["explicit"]:
        result = exit_advisor._check_explicit_exit(f"Some text {signal} more text")
        assert result["has_explicit_exit"] is True
        assert signal in result["found_signals"]
        assert result["confidence"] == 0.9

def test_implicit_exit_signals(exit_advisor):
    """Test implicit exit signal detection function."""
    for signal in EXIT_SIGNALS["implicit"]:
        result = exit_advisor._check_implicit_exit(f"Some text {signal} more text")
        assert result["has_implicit_exit"] is True
        assert signal in result["found_signals"]
        assert result["confidence"] == 0.7

def test_conversation_context_analysis(exit_advisor, sample_conversation_history):
    """Test conversation context analysis."""
    # Test task completion
    message = "I've completed the scheduling process"
    result = exit_advisor._analyze_conversation_context(message, sample_conversation_history)
    assert result["has_task_completion"] is True
    assert result["confidence"] == 0.8
    
    # Test satisfaction
    message = "Thank you, that's perfect!"
    result = exit_advisor._analyze_conversation_context(message, sample_conversation_history)
    assert result["has_satisfaction"] is True
    assert result["confidence"] == 0.8
    
    # Test neutral message
    message = "What's the next step?"
    result = exit_advisor._analyze_conversation_context(message, sample_conversation_history)
    assert result["has_task_completion"] is False
    assert result["has_satisfaction"] is False
    assert result["confidence"] == 0.0

def test_farewell_message_generation(exit_advisor):
    """Test farewell message generation for different contexts."""
    # Test scheduling completion
    message = exit_advisor.get_farewell_message({"scheduling_completed": True})
    assert "scheduled" in message.lower()
    
    # Test information provided
    message = exit_advisor.get_farewell_message({"information_provided": True})
    assert "information" in message.lower()
    
    # Test needs consideration
    message = exit_advisor.get_farewell_message({"needs_consideration": True})
    assert "consider" in message.lower() or "think" in message.lower()
    
    # Test technical issue
    message = exit_advisor.get_farewell_message({"technical_issue": True})
    assert "technical" in message.lower() or "difficulties" in message.lower()
    
    # Test standard farewell
    message = exit_advisor.get_farewell_message({})
    assert "thank you" in message.lower()
    assert "day" in message.lower() 