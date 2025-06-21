"""
Agent managers for AI-Powered CRM MVP
Handles connections to Vertex AI reasoning engines
"""

import os
import uuid
import json
import asyncio
import sys
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from dotenv import load_dotenv
from vertexai import agent_engines
from google.cloud import aiplatform

from backend.models import PipelinePayload, StageConfig, LeadData, BusinessData

# Add src to path for importing utility functions
sys.path.append('src')
from utils.utils import handle_upload_and_patch_state

# Load environment variables
load_dotenv()

class CRMAgentManager:
    """
    Manages connections to the CRM Stage Builder Agent
    Handles pipeline creation and business setup
    """
    
    def __init__(self):
        self.agent_id = os.getenv("CRM_STAGE_AGENT")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION")
        self.engine = None
        self.active_sessions = {}
        
        # Initialize AI Platform
        aiplatform.init(project=self.project_id, location=self.location)
        
        print(f"🤖 CRM Agent Manager initialized with agent: {self.agent_id}")
    
    def _get_engine(self):
        """Get the engine handle (lazy loading)"""
        if self.engine is None:
            self.engine = agent_engines.get(self.agent_id)
        return self.engine
    
    async def get_or_create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get existing session or create a new one"""
        if session_id and session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Create new session
        engine = self._get_engine()
        user_id = f"owner_{uuid.uuid4().hex[:8]}"
        
        session = engine.create_session(user_id=user_id)
        
        session_data = {
            "session_id": session["id"],
            "user_id": session["userId"],
            "engine": engine,
            "created_at": datetime.now().isoformat()
        }
        
        # Store session
        self.active_sessions[session["id"]] = session_data
        
        print(f"🆔 Created CRM session: {session['id']} for user: {user_id}")
        return session_data
    
    async def stream_query(self, session_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a query to the CRM agent"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        print(f"📤 Sending to CRM agent: {message[:100]}...")
        
        # Stream the response
        for event in engine.stream_query(
            user_id=session["user_id"],
            session_id=session_id,
            message=message
        ):
            yield event
    
    def combine_response_parts(self, response_parts: List[Dict[str, Any]]) -> str:
        """Combine response parts into a single text response"""
        text_parts = []
        
        for part in response_parts:
            if isinstance(part, dict):
                # Extract text from content
                content = part.get("content", {})
                if "parts" in content:
                    for part_item in content["parts"]:
                        if "text" in part_item:
                            text_parts.append(part_item["text"])
        
        return "\n".join(text_parts) if text_parts else "Response received"
    
    async def handle_file_upload(self, session_id: str, file_path: str, filename: str):
        """Handle file upload to the CRM agent session using the utility function"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        print(f"📁 Uploading file {filename} to CRM session {session_id}")
        
        try:
            # Use the utility function for file upload and RAG corpus integration
            await handle_upload_and_patch_state(
                self.agent_id,  # Pass the full agent ID
                file_path,
                user_id=session["user_id"],
                session_id=session_id
            )
            
            print(f"✅ File {filename} uploaded successfully to RAG corpus")
            
        except Exception as e:
            print(f"❌ File upload error: {str(e)}")
            raise
    
    async def is_pipeline_complete(self, session_id: str) -> bool:
        """Check if the pipeline creation is complete using the proper state path"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        try:
            # Get session state using the correct method
            remote_session_state = engine.get_session(
                user_id=session["user_id"],
                session_id=session_id
            )
            
            # Check pipeline completion status using the correct path
            is_complete = remote_session_state.get('state', {}).get('pipeline', {}).get('pipeline_completed', False)
            
            print(f"🔍 Pipeline completion status: {is_complete}")
            
            # Debug: Print top-level keys for troubleshooting
            state = remote_session_state.get('state', {})
            print(f"📋 Top-level keys in state: {list(state.keys())}")
            
            return bool(is_complete)
            
        except Exception as e:
            print(f"❌ Error checking pipeline status: {str(e)}")
            return False
    
    def extract_business_data(self, state: dict) -> dict:
        """Extract business data from state using the pattern from crm_agent_pipeline.py"""
        return {
            "biz_name": state.get("biz_name", ""),
            "biz_info": state.get("biz_info", ""),
            "goal": state.get("goal", ""),
            "business_id": state.get("business_id", ""),
        }
    
    def build_stages(self, state: dict) -> List[dict]:
        """Build stages list from state using the pattern from crm_agent_pipeline.py"""
        total = int(state.get("total_stages", 0))
        stages = []
        for i in range(1, total + 1):
            stages.append({
                "stage_name": state.get(f"stage_{i}_stage_name", ""),
                "stage_number": state.get(f"stage_{i}_stage_number", ""),
                "entry_condition": state.get(f"stage_{i}_entry_condition", ""),
                "prompt": state.get(f"stage_{i}_prompt", ""),
                "brief_stage_goal": state.get(f"stage_{i}_brief_stage_goal", ""),
                "fields": state.get(f"stage_{i}_fields", []),
                "user_tags": state.get(f"stage_{i}_user_tags", []),
            })
        return stages
    
    async def extract_pipeline_payload(self, session_id: str) -> Optional[PipelinePayload]:
        """Extract the complete pipeline payload from the session state"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        try:
            # Get session state
            remote_session_state = engine.get_session(
                user_id=session["user_id"],
                session_id=session_id
            )
            
            state = remote_session_state.get("state", {})
            
            # Extract business data using the helper function
            business_data = self.extract_business_data(state)
            
            # Build stages using the helper function
            stages_data = self.build_stages(state)
            
            if not stages_data:
                return None
            
            # Convert to StageConfig objects
            stages = []
            for stage_data in stages_data:
                stage = StageConfig(
                    stage_name=stage_data["stage_name"],
                    stage_number=stage_data.get("stage_number", 0),
                    entry_condition=stage_data["entry_condition"],
                    prompt=stage_data["prompt"],
                    brief_stage_goal=stage_data["brief_stage_goal"],
                    fields=stage_data["fields"],
                    user_tags=stage_data["user_tags"]
                )
                stages.append(stage)
            
            # Create pipeline payload
            pipeline_payload = PipelinePayload(
                business_id=business_data["business_id"] or str(uuid.uuid4()),
                biz_name=business_data["biz_name"],
                biz_info=business_data["biz_info"],
                goal=business_data["goal"],
                total_stages=len(stages),
                stages=stages,
                created_at=datetime.now().isoformat()
            )
            
            print(f"✅ Extracted pipeline with {len(stages)} stages for {business_data['biz_name']}")
            return pipeline_payload
            
        except Exception as e:
            print(f"❌ Error extracting pipeline payload: {str(e)}")
            return None
    
    async def cleanup_session(self, session_id: str):
        """Clean up a session"""
        if session_id in self.active_sessions:
            try:
                session = self.active_sessions[session_id]
                engine = session["engine"]
                engine.delete(force=True)
                print(f"🧹 Cleaned up CRM session: {session_id}")
            except Exception as e:
                print(f"⚠️  Session cleanup warning: {str(e)}")
            finally:
                del self.active_sessions[session_id]


class OmniAgentManager:
    """
    Manages connections to the Omni Stage Agent
    Handles lead interactions and progression through pipeline stages
    """
    
    def __init__(self):
        self.agent_id = os.getenv("OMNI_STAGE_AGENT")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION")
        self.engine = None
        self.active_sessions = {}
        
        # Initialize AI Platform
        aiplatform.init(project=self.project_id, location=self.location)
        
        print(f"🤖 Omni Agent Manager initialized with agent: {self.agent_id}")
    
    def _get_engine(self):
        """Get the engine handle (lazy loading)"""
        if self.engine is None:
            self.engine = agent_engines.get(self.agent_id)
        return self.engine
    
    async def create_lead_session(self, pipeline_payload: PipelinePayload, lead_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session for a lead with the pipeline state"""
        engine = self._get_engine()
        user_id = f"lead_{uuid.uuid4().hex[:8]}"
        
        # Prepare ready state from pipeline
        try:
            # Import the utility function from src/utils/utils.py
            import sys
            sys.path.append('../src')
            from utils.utils import build_ready_state
            
            # Convert pipeline to state format
            state = self._pipeline_to_state(pipeline_payload)
            ready_state = await build_ready_state(session_state=state, current_stage=1)
            
            session = engine.create_session(user_id=user_id, state=ready_state)
            
        except ImportError:
            # Fallback if utility not available
            session = engine.create_session(user_id=user_id)
        
        session_data = {
            "session_id": session["id"],
            "user_id": session["userId"],
            "engine": engine,
            "lead_id": lead_id or user_id,
            "current_stage": 1,
            "created_at": datetime.now().isoformat()
        }
        
        # Store session
        self.active_sessions[session["id"]] = session_data
        
        print(f"🆔 Created Omni session: {session['id']} for lead: {user_id}")
        return session_data
    
    def _pipeline_to_state(self, pipeline: PipelinePayload) -> Dict[str, Any]:
        """Convert PipelinePayload to state format expected by Omni agent"""
        state = {
            "biz_name": pipeline.biz_name,
            "biz_info": pipeline.biz_info,
            "goal": pipeline.goal,
            "business_id": pipeline.business_id,
            "total_stages": pipeline.total_stages,
            "pipeline_completed": pipeline.pipeline_completed,
            "current_stage": 1
        }
        
        # Add stage definitions
        for stage in pipeline.stages:
            prefix = f"stage_{stage.stage_number}_"
            state[f"{prefix}stage_name"] = stage.stage_name
            state[f"{prefix}stage_number"] = stage.stage_number
            state[f"{prefix}entry_condition"] = stage.entry_condition
            state[f"{prefix}prompt"] = stage.prompt
            state[f"{prefix}brief_stage_goal"] = stage.brief_stage_goal
            state[f"{prefix}fields"] = stage.fields
            state[f"{prefix}user_tags"] = stage.user_tags
        
        return state
    
    async def stream_query(self, session_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a query to the Omni agent"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        print(f"📤 Sending to Omni agent: {message[:100]}...")
        
        # Stream the response
        for event in engine.stream_query(
            user_id=session["user_id"],
            session_id=session_id,
            message=message
        ):
            yield event
    
    async def get_lead_data(self, session_id: str) -> Optional[LeadData]:
        """Extract current lead data from session state"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        try:
            # Get session state
            current_session = engine.get_session(
                user_id=session["user_id"],
                session_id=session_id
            )
            
            state = current_session.get("state", {})
            
            # Extract lead data
            lead_data = LeadData(
                name=state.get("Name", ""),
                type=state.get("Type", ""),
                company=state.get("Company", ""),
                website=state.get("Website", ""),
                phone=state.get("Phone", ""),
                email=state.get("Email", ""),
                address=state.get("Address", ""),
                requirements=state.get("Requirements", ""),
                notes=state.get("Notes", ""),
                stage=int(state.get("current_stage", 1)),
                session_id=session_id,
                updated_at=datetime.now().isoformat()
            )
            
            return lead_data
            
        except Exception as e:
            print(f"❌ Error extracting lead data: {str(e)}")
            return None
    
    async def cleanup_session(self, session_id: str):
        """Clean up a session"""
        if session_id in self.active_sessions:
            try:
                session = self.active_sessions[session_id]
                engine = session["engine"]
                engine.delete(force=True)
                print(f"🧹 Cleaned up Omni session: {session_id}")
            except Exception as e:
                print(f"⚠️  Session cleanup warning: {str(e)}")
            finally:
                del self.active_sessions[session_id] 