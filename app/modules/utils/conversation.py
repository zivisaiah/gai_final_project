"""
Conversation Utilities
Session state management, message history, and conversation persistence
"""

import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import logging


class ConversationSession:
    """Manages individual conversation sessions with persistence."""
    
    def __init__(self, session_id: str = None, timeout_minutes: int = 30):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.timeout_minutes = timeout_minutes
        self.metadata = {}
        self.is_active = True
        
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(minutes=self.timeout_minutes)
        return datetime.now() > expiry_time
    
    def get_duration_minutes(self) -> float:
        """Get session duration in minutes."""
        return (datetime.now() - self.created_at).total_seconds() / 60
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "timeout_minutes": self.timeout_minutes,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "duration_minutes": self.get_duration_minutes()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationSession':
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            timeout_minutes=data["timeout_minutes"]
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.metadata = data.get("metadata", {})
        session.is_active = data.get("is_active", True)
        return session


class ConversationManager:
    """
    Manages multiple conversation sessions with persistence and cleanup.
    Handles session lifecycle, state persistence, and memory management.
    """
    
    def __init__(self, storage_dir: str = None, auto_cleanup: bool = True):
        self.storage_dir = Path(storage_dir) if storage_dir else Path("data/conversations")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, ConversationSession] = {}
        self.auto_cleanup = auto_cleanup
        self.logger = logging.getLogger(__name__)
        
        # Load existing sessions
        self._load_sessions()
        
        # Clean up expired sessions
        if self.auto_cleanup:
            self._cleanup_expired_sessions()
    
    def create_session(self, session_id: str = None, **metadata) -> ConversationSession:
        """Create a new conversation session."""
        session = ConversationSession(session_id)
        session.metadata.update(metadata)
        
        self.sessions[session.session_id] = session
        self._save_session(session)
        
        self.logger.info(f"Created new session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an existing session by ID."""
        session = self.sessions.get(session_id)
        
        if session and session.is_expired():
            self.logger.info(f"Session {session_id} has expired")
            self.end_session(session_id)
            return None
        
        if session:
            session.update_activity()
            self._save_session(session)
        
        return session
    
    def get_or_create_session(self, session_id: str = None, **metadata) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(session_id, **metadata)
    
    def end_session(self, session_id: str):
        """End a conversation session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            self._save_session(session)
            del self.sessions[session_id]
            
            self.logger.info(f"Ended session: {session_id}")
    
    def list_active_sessions(self) -> List[ConversationSession]:
        """Get list of all active sessions."""
        return [session for session in self.sessions.values() if session.is_active]
    
    def get_session_stats(self) -> Dict:
        """Get statistics about sessions."""
        active_sessions = self.list_active_sessions()
        
        total_duration = sum(session.get_duration_minutes() for session in active_sessions)
        avg_duration = total_duration / len(active_sessions) if active_sessions else 0
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "average_duration_minutes": avg_duration,
            "total_duration_minutes": total_duration
        }
    
    def _save_session(self, session: ConversationSession):
        """Save session to persistent storage."""
        try:
            session_file = self.storage_dir / f"{session.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving session {session.session_id}: {e}")
    
    def _load_sessions(self):
        """Load sessions from persistent storage."""
        try:
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session = ConversationSession.from_dict(session_data)
                    if not session.is_expired() and session.is_active:
                        self.sessions[session.session_id] = session
                        self.logger.debug(f"Loaded session: {session.session_id}")
                    else:
                        # Remove expired session file
                        session_file.unlink()
                        
                except Exception as e:
                    self.logger.error(f"Error loading session from {session_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error loading sessions: {e}")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            self.end_session(session_id)
            
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class MessageHistory:
    """
    Manages conversation message history with efficient storage and retrieval.
    Supports pagination, filtering, and export functionality.
    """
    
    def __init__(self, conversation_id: str, storage_dir: str = None):
        self.conversation_id = conversation_id
        self.storage_dir = Path(storage_dir) if storage_dir else Path("data/messages")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.messages: List[Dict] = []
        self.message_file = self.storage_dir / f"{conversation_id}_messages.json"
        
        # Load existing messages
        self._load_messages()
    
    def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Dict = None,
        timestamp: datetime = None
    ):
        """Add a message to the history."""
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self._save_messages()
    
    def get_messages(
        self, 
        limit: int = None, 
        offset: int = 0,
        role_filter: str = None
    ) -> List[Dict]:
        """Get messages with optional filtering and pagination."""
        filtered_messages = self.messages
        
        # Filter by role if specified
        if role_filter:
            filtered_messages = [msg for msg in filtered_messages if msg["role"] == role_filter]
        
        # Apply pagination
        if limit:
            return filtered_messages[offset:offset + limit]
        else:
            return filtered_messages[offset:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []
    
    def get_message_count(self, role_filter: str = None) -> int:
        """Get total message count, optionally filtered by role."""
        if role_filter:
            return len([msg for msg in self.messages if msg["role"] == role_filter])
        return len(self.messages)
    
    def search_messages(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search messages by content."""
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for message in self.messages:
            content = message["content"]
            if not case_sensitive:
                content = content.lower()
            
            if query in content:
                results.append(message)
        
        return results
    
    def export_messages(self, format: str = "json") -> str:
        """Export messages in specified format."""
        if format.lower() == "json":
            return json.dumps(self.messages, indent=2)
        elif format.lower() == "txt":
            lines = []
            for msg in self.messages:
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] {msg['role'].title()}: {msg['content']}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages = []
        self._save_messages()
    
    def _load_messages(self):
        """Load messages from persistent storage."""
        try:
            if self.message_file.exists():
                with open(self.message_file, 'r') as f:
                    self.messages = json.load(f)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error loading messages: {e}")
            self.messages = []
    
    def _save_messages(self):
        """Save messages to persistent storage."""
        try:
            with open(self.message_file, 'w') as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error saving messages: {e}")


class ConversationContext:
    """
    Provides conversation context and state management for agents.
    Integrates session management, message history, and candidate tracking.
    """
    
    def __init__(self, conversation_id: str = None, storage_dir: str = None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        
        # Initialize components
        self.session_manager = ConversationManager(storage_dir)
        self.message_history = MessageHistory(self.conversation_id, storage_dir)
        
        # Create or get session
        self.session = self.session_manager.get_or_create_session(
            self.conversation_id,
            conversation_id=self.conversation_id
        )
        
        # Context tracking
        self.context_data = {}
        self.candidate_info = {}
        
    def add_user_message(self, content: str, metadata: Dict = None):
        """Add a user message to the conversation."""
        self.message_history.add_message("user", content, metadata)
        self.session.update_activity()
    
    def add_assistant_message(self, content: str, metadata: Dict = None):
        """Add an assistant message to the conversation."""
        self.message_history.add_message("assistant", content, metadata)
        self.session.update_activity()
    
    def get_conversation_context(self, message_limit: int = 5) -> Dict:
        """Get current conversation context for agent processing."""
        recent_messages = self.message_history.get_recent_messages(message_limit)
        
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session.session_id,
            "recent_messages": recent_messages,
            "message_count": self.message_history.get_message_count(),
            "session_duration": self.session.get_duration_minutes(),
            "candidate_info": self.candidate_info,
            "context_data": self.context_data
        }
    
    def update_candidate_info(self, info: Dict):
        """Update candidate information."""
        self.candidate_info.update(info)
        self.session.metadata["candidate_info"] = self.candidate_info
    
    def set_context_data(self, key: str, value: Any):
        """Set context data for the conversation."""
        self.context_data[key] = value
        self.session.metadata["context_data"] = self.context_data
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """Get context data from the conversation."""
        return self.context_data.get(key, default)
    
    def export_conversation(self) -> Dict:
        """Export complete conversation data."""
        return {
            "conversation_id": self.conversation_id,
            "session": self.session.to_dict(),
            "messages": self.message_history.messages,
            "candidate_info": self.candidate_info,
            "context_data": self.context_data,
            "summary": {
                "total_messages": self.message_history.get_message_count(),
                "user_messages": self.message_history.get_message_count("user"),
                "assistant_messages": self.message_history.get_message_count("assistant"),
                "duration_minutes": self.session.get_duration_minutes()
            }
        }
    
    def end_conversation(self):
        """End the conversation and clean up resources."""
        self.session_manager.end_session(self.session.session_id) 