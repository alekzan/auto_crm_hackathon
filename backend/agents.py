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


from .models import PipelinePayload, StageConfig, LeadData, BusinessData

# build_ready_state will be imported conditionally when needed

# Import handle_upload_and_patch_state from utils
def _import_handle_upload_and_patch_state():
    """Import handle_upload_and_patch_state from utils"""
    try:
        import importlib.util
        utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'utils.py')
        spec = importlib.util.spec_from_file_location("utils", utils_path)
        utils_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils_module)
        return utils_module.handle_upload_and_patch_state
    except Exception as e:
        print(f"❌ Error importing handle_upload_and_patch_state: {str(e)}")
        raise

handle_upload_and_patch_state = _import_handle_upload_and_patch_state()

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
        """Check if the pipeline creation is complete using multiple indicators"""
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
            
            state = remote_session_state.get('state', {})
            return await self.is_pipeline_complete_from_state(state)
            
        except Exception as e:
            print(f"❌ Error checking pipeline status: {str(e)}")
            return False
    
    async def is_pipeline_complete_from_state(self, state: dict) -> bool:
        """Check if the pipeline creation is complete using session state directly"""
        try:
            print(f"📋 Checking pipeline completion. Top-level keys: {list(state.keys())}")
            
            # Check multiple indicators for completion (per user's explanation)
            is_complete = False
            
            # 1. Check if pipeline.pipeline_completed is True
            if 'pipeline' in state and isinstance(state['pipeline'], dict):
                pipeline_completed = state['pipeline'].get('pipeline_completed', False)
                print(f"🔍 pipeline.pipeline_completed: {pipeline_completed}")
                if pipeline_completed:
                    is_complete = True
            
            # 2. Check if stages exist in pipeline.stage_design_results.stages
            if 'pipeline' in state and 'stage_design_results' in state['pipeline']:
                stages = state['pipeline']['stage_design_results'].get('stages', [])
                print(f"🔍 Found {len(stages)} stages in stage_design_results")
                if len(stages) >= 3:  # User specified 3-4 stages
                    # Check if at least the first stage has a goal
                    if stages and stages[0].get('brief_stage_goal'):
                        print(f"🔍 First stage has goal: {stages[0]['brief_stage_goal'][:50]}...")
                        is_complete = True
            
            # 3. Check if we have flattened stage data directly in state
            stage_count = 0
            for i in range(1, 10):  # Check up to 9 stages
                if f'stage_{i}_stage_name' in state:
                    stage_count = i
            
            if stage_count >= 3:
                print(f"🔍 Found {stage_count} flattened stages in state")
                is_complete = True
            
            print(f"🔍 Final pipeline completion status: {is_complete}")
            return bool(is_complete)
            
        except Exception as e:
            print(f"❌ Error checking pipeline status from state: {str(e)}")
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
        """Extract the complete pipeline payload from the session state using build_ready_state"""
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

            raw_state = remote_session_state.get("state", {})
            return await self.extract_pipeline_payload_from_state(raw_state)
            
        except Exception as e:
            print(f"❌ Error extracting pipeline payload: {str(e)}")
            return None

    async def extract_pipeline_payload_from_state(self, raw_state: dict) -> Optional[PipelinePayload]:
        """Extract the complete pipeline payload from session state directly"""
        try:
            print(f"🔧 Extracting pipeline from raw state with keys: {list(raw_state.keys())}")
            
            # Import build_ready_state conditionally
            try:
                import sys
                import os
                import importlib.util
                
                # Direct import from utils.py file
                utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'utils.py')
                spec = importlib.util.spec_from_file_location("utils", utils_path)
                utils_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(utils_module)
                build_ready_state = utils_module.build_ready_state
                
                print("✅ Successfully imported build_ready_state")
            except Exception as e:
                print(f"⚠️ Could not import build_ready_state: {str(e)}")
                return None
            
            # Use build_ready_state to properly flatten the state
            ready_state = await build_ready_state(raw_state, current_stage=1)
            print(f"✅ Built ready state with {ready_state.get('total_stages', 0)} stages")
            
            # Validate we have at least 3 stages as required by user
            total_stages = ready_state.get('total_stages', 0)
            if total_stages < 3 or total_stages > 4:
                print(f"⚠️ Pipeline has {total_stages} stages, expected 3-4. Adjusting...")
                # If we have stages but wrong count, try to extract what we can
                if total_stages == 0:
                    return None
            
            # Extract business data from ready state
            business_data = {
                "biz_name": ready_state.get("biz_name", ""),
                "biz_info": ready_state.get("biz_info", ""),
                "goal": ready_state.get("goal", ""),
                "business_id": ready_state.get("business_id", str(uuid.uuid4())),
            }
            
            # Build stages from flattened ready state
            stages = []
            for i in range(1, total_stages + 1):
                stage_data = {
                    "stage_name": ready_state.get(f"stage_{i}_stage_name", f"Stage {i}"),
                    "stage_number": i,
                    "entry_condition": ready_state.get(f"stage_{i}_entry_condition", ""),
                    "prompt": ready_state.get(f"stage_{i}_prompt", ""),
                    "brief_stage_goal": ready_state.get(f"stage_{i}_brief_stage_goal", ""),
                    "fields": ready_state.get(f"stage_{i}_fields", []),
                    "user_tags": ready_state.get(f"stage_{i}_user_tags", []),
                }
                
                # Convert to StageConfig object
                stage = StageConfig(
                    stage_name=stage_data["stage_name"],
                    stage_number=stage_data["stage_number"],
                    entry_condition=stage_data["entry_condition"],
                    prompt=stage_data["prompt"],
                    brief_stage_goal=stage_data["brief_stage_goal"],
                    fields=stage_data["fields"],
                    user_tags=stage_data["user_tags"]
                )
                stages.append(stage)
                print(f"📋 Built stage {i}: {stage_data['stage_name']}")
            
            if not stages:
                print("❌ No stages found in ready state")
                return None
            
            # Create pipeline payload
            pipeline_payload = PipelinePayload(
                business_id=business_data["business_id"],
                biz_name=business_data["biz_name"],
                biz_info=business_data["biz_info"],
                goal=business_data["goal"],
                total_stages=total_stages,
                stages=stages,
                pipeline_completed=True,
                created_at=datetime.now().isoformat()
            )
            
            print(f"✅ Extracted pipeline: {business_data['biz_name']} with {total_stages} stages")
            return pipeline_payload
            
        except Exception as e:
            print(f"❌ Error extracting pipeline payload from state: {str(e)}")
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
    Handles lead conversations and state tracking
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
    
    async def create_lead_session(self, ready_state: Dict[str, Any], lead_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new lead session with the ready state from CRM pipeline"""
        engine = self._get_engine()
        user_id = f"lead_{uuid.uuid4().hex[:8]}" if not lead_id else lead_id
        
        print(f"🚀 Creating Omni session with ready state for lead: {user_id}")
        
        # Create session with the ready state
        session = engine.create_session(user_id=user_id, state=ready_state)
        
        session_data = {
            "session_id": session["id"],
            "user_id": session["userId"],
            "engine": engine,
            "ready_state": ready_state,
            "created_at": datetime.now().isoformat(),
            "last_state_update": datetime.now().isoformat()
        }
        
        # Store session
        self.active_sessions[session["id"]] = session_data
        
        print(f"✅ Created Omni session: {session['id']} for lead: {user_id}")
        print(f"📊 Initial state keys: {len(ready_state)} keys")
        
        return session_data
    
    async def stream_query(self, session_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a query to the Omni agent and track state changes"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        print(f"📤 Sending to Omni agent: {message[:100]}...")
        
        # Track state changes
        state_changes = []
        
        # Stream the response
        for event in engine.stream_query(
            user_id=session["user_id"],
            session_id=session_id,
            message=message
        ):
            # Check for tool usage in events
            if isinstance(event, dict):
                # Look for tool usage indicators
                if self._is_state_change_event(event):
                    state_changes.append(event)
                    print(f"🔧 Detected state change event: {event.get('type', 'unknown')}")
            
            yield event
        
        # Update our local tracking if state changes occurred
        if state_changes:
            await self._handle_state_changes(session_id, state_changes)
    
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
    
    def _is_state_change_event(self, event: Dict[str, Any]) -> bool:
        """Check if an event indicates a state change from internal tools"""
        # Convert event to string for pattern matching
        event_str = str(event).lower()
        
        # Look for tool usage patterns
        tool_indicators = [
            "update_record_tool",
            "move_stage_tool", 
            "success message",
            "updated",
            "moved to stage",
            "stage transition",
            "information saved",
            "record updated"
        ]
        
        # Check if any tool indicators are present
        for indicator in tool_indicators:
            if indicator in event_str:
                print(f"🔧 State change detected: '{indicator}' found in event")
                return True
        
        # Also check the content structure more thoroughly
        content = event.get("content", {})
        if isinstance(content, dict):
            parts = content.get("parts", [])
            for part in parts:
                if isinstance(part, dict):
                    text = part.get("text", "").lower()
                    for indicator in tool_indicators:
                        if indicator in text:
                            print(f"🔧 State change detected in text: '{indicator}'")
                            return True
        
        return False
    
    async def _handle_state_changes(self, session_id: str, state_changes: List[Dict[str, Any]]):
        """Handle state changes from Omni agent internal tools"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        try:
            # Get the updated state from the agent
            remote_session = engine.get_session(
                user_id=session["user_id"],
                session_id=session_id
            )
            
            updated_state = remote_session.get("state", {})
            
            # Extract lead data from the updated state
            lead_data = self._extract_lead_data(updated_state, session_id)
            
            print(f"📊 State updated for lead: {lead_data.get('name', 'Unknown')}")
            print(f"🎯 Current stage: {lead_data.get('stage', 1)}")
            
            # Update our session tracking
            session["last_state_update"] = datetime.now().isoformat()
            
            # Return the updated lead data for the caller to handle
            return lead_data
            
        except Exception as e:
            print(f"❌ Error handling state changes: {str(e)}")
            return None
    
    def _extract_lead_data(self, state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract lead data from Omni agent state using the pattern from omni_stage_agent_pipeline.py"""
        return {
            "session_id": session_id,
            "name": state.get("Name", ""),
            "type": state.get("Type", ""),
            "company": state.get("Company", ""),
            "website": state.get("Website", ""),
            "phone": state.get("Phone", ""),
            "email": state.get("Email", ""),
            "address": state.get("Address", ""),
            "requirements": state.get("Requirements", ""),
            "notes": state.get("Notes", ""),
            "stage": int(state.get("current_stage", 1)),
            "user_tags": state.get("current_stage_user_tags", []),
            "updated_at": datetime.now().isoformat()
        }
    
    async def get_lead_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current lead data from the Omni agent state"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        engine = session["engine"]
        
        try:
            # Get current state from agent
            remote_session = engine.get_session(
                user_id=session["user_id"],
                session_id=session_id
            )
            
            current_state = remote_session.get("state", {})
            
            # Extract and return lead data
            return self._extract_lead_data(current_state, session_id)
            
        except Exception as e:
            print(f"❌ Error getting lead data: {str(e)}")
            return None
    
    async def cleanup_session(self, session_id: str):
        """Clean up a lead session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            print(f"🗑️ Cleaned up Omni session: {session_id}") 