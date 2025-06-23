"""
Agent managers for AI-Powered CRM MVP
Handles connections to Vertex AI reasoning engines
"""

import os
import uuid
import asyncio
from typing import Dict, List, Optional, Any

from google.cloud import aiplatform
from vertexai import agent_engines

from backend.models import LeadData
from backend.state_manager import StateManager


class CRMAgentManager:
    """Manages interactions with the CRM Stage Builder Agent."""

    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION")
        self.agent_id = "crm-stage-builder-agent"
        self.engine = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        aiplatform.init(project=self.project_id, location=self.location)
        print("✅ AI Platform initialized for CRM Agent")

    def _get_engine(self):
        """Initializes and returns the agent engine."""
        if self.engine is None:
            print(f"🤖 Getting CRM Agent engine for: {self.agent_id}")
            self.engine = agent_engines.get(self.agent_id)
        return self.engine

    async def get_or_create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Gets an existing session or creates a new one."""
        engine = self._get_engine()
        
        if session_id and session_id in self.active_sessions:
            return self.active_sessions[session_id]

        user_id = f"crm_user_{uuid.uuid4().hex[:8]}"
        new_session = engine.create_session(user_id=user_id)
        
        session_data = {
            "session_id": new_session.id,
            "user_id": user_id,
            "engine": engine,
        }
        self.active_sessions[new_session.id] = session_data
        print(f"✅ Created CRM Agent session: {new_session.id}")
        return session_data

    async def stream_query(self, session_id: str, message: str):
        """Streams a query to the CRM agent."""
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")
        
        session_data = self.active_sessions[session_id]
        engine = session_data["engine"]
        
        async for event in engine.stream_query(
            user_id=session_data["user_id"],
            session_id=session_id,
            message=message
        ):
            yield event

    def combine_response_parts(self, response_parts: List[Dict[str, Any]]) -> str:
        """Combine response parts into a single text response"""
        text_parts = []
        for part in response_parts:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        return "\n".join(text_parts) if text_parts else "Response received"

    async def reset_session(self):
        """Resets all active sessions."""
        self.active_sessions = {}
        print("🔄 All CRM Agent sessions have been reset.")


class OmniAgentManager:
    """Manages interactions with the Omni Stage Agent."""
    
    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION")
        self.agent_id = "omni-stage-agent"
        self.engine = None
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        aiplatform.init(project=self.project_id, location=self.location)
        print("✅ Omni Agent Manager initialized.")

    def _get_engine(self):
        """Initializes and returns the agent engine."""
        if self.engine is None:
            print(f"🤖 Getting Omni Agent engine for: {self.agent_id}")
            self.engine = agent_engines.get(self.agent_id)
        return self.engine

    async def create_lead_session(self, lead_id: Optional[str] = None) -> Dict[str, Any]:
        """Creates or retrieves a session for the Omni Agent."""
        session_id = lead_id or f"lead_{uuid.uuid4().hex[:12]}"
        
        if session_id in self.user_sessions:
            return self.user_sessions[session_id]

        # Check if pipeline is available before creating session
        state_manager = StateManager()
        pipeline = await state_manager.get_pipeline_state()
        
        if not pipeline:
            raise Exception("No active CRM pipeline found. Please create a pipeline with the CRM Agent first.")

        engine = self._get_engine()
        user_id = f"lead_{uuid.uuid4().hex[:8]}"
        new_session = engine.create_session(user_id=user_id)
        
        session_data = {
            "session_id": new_session.id,
            "user_id": user_id,
            "engine": engine,
        }
        self.user_sessions[new_session.id] = session_data
        print(f"✅ Created Omni Agent session: {new_session.id}")
        return session_data

    async def query(self, session_id: str, prompt: str):
        """Sends a query to the Omni Agent for a specific session."""
        if session_id not in self.user_sessions:
            raise Exception(f"Session not found for ID: {session_id}")
            
        session_data = self.user_sessions[session_id]
        engine = session_data["engine"]
        
        response_text = ""
        async for event in engine.stream_query(
            user_id=session_data["user_id"],
            session_id=session_id,
            message=prompt
        ):
            if "text" in event:
                response_text += event["text"]
        
        # For now, return simple lead data - this can be enhanced later
        updated_lead_data = {"session_id": session_id, "stage": 1}

        return response_text, updated_lead_data

    async def reset_all_sessions(self):
        """Resets all active sessions in the manager."""
        self.user_sessions = {}
        self.engine = None
        print("🔄 All Omni Agent sessions have been reset.") 