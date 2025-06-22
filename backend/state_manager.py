"""
State manager for AI-Powered CRM MVP
Handles in-memory state and JSON file persistence
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.models import (
    ApplicationState, 
    BusinessData, 
    PipelinePayload, 
    LeadData, 
    KanbanBoard,
    KanbanColumn,
    KanbanCard
)

class StateManager:
    """
    Manages application state in memory with JSON file persistence
    """
    
    def __init__(self, state_file: str = "state.json"):
        self.state_file = state_file
        self.state = ApplicationState()
        self._save_task = None
        
        print(f"📊 State Manager initialized with file: {state_file}")
    
    async def load_state(self):
        """Load state from JSON file if it exists"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Convert dict back to ApplicationState
                self.state = ApplicationState(**data)
                
                print(f"📥 Loaded state from {self.state_file}")
                print(f"   - Business: {self.state.business_data.biz_name}")
                print(f"   - Leads: {len(self.state.leads)}")
                print(f"   - Active sessions: {len(self.state.active_sessions)}")
                
            else:
                print(f"📄 No existing state file found, starting fresh")
                
        except Exception as e:
            print(f"❌ Error loading state: {str(e)}")
            self.state = ApplicationState()  # Start fresh if load fails
    
    async def save_state(self):
        """Save current state to JSON file"""
        try:
            # Update last_updated timestamp
            self.state.last_updated = datetime.now().isoformat()
            
            # Convert to dict and save
            state_dict = self.state.model_dump()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            print(f"💾 State saved to {self.state_file}")
            
        except Exception as e:
            print(f"❌ Error saving state: {str(e)}")
    
    def start_auto_save(self, interval: int = 30):
        """Start auto-save task that runs every interval seconds"""
        if self._save_task is None:
            self._save_task = asyncio.create_task(self._auto_save_loop(interval))
            print(f"⏰ Auto-save started (every {interval}s)")
    
    async def _auto_save_loop(self, interval: int):
        """Auto-save loop"""
        while True:
            await asyncio.sleep(interval)
            await self.save_state()
    
    def stop_auto_save(self):
        """Stop auto-save task"""
        if self._save_task:
            self._save_task.cancel()
            self._save_task = None
            print("⏰ Auto-save stopped")
    
    # Business Data Methods
    async def update_business_data(self, business_data: BusinessData):
        """Update business configuration"""
        self.state.business_data = business_data
        print(f"🏢 Updated business data: {business_data.biz_name}")
    
    async def get_business_data(self) -> BusinessData:
        """Get current business data"""
        return self.state.business_data
    
    # Pipeline Methods
    async def update_pipeline(self, pipeline: PipelinePayload):
        """Update pipeline configuration"""
        self.state.pipeline_payload = pipeline
        
        # Update business data from pipeline
        self.state.business_data.biz_name = pipeline.biz_name
        self.state.business_data.biz_info = pipeline.biz_info
        self.state.business_data.goal = pipeline.goal
        self.state.business_data.business_id = pipeline.business_id
        
        # Rebuild Kanban board
        await self._rebuild_kanban_board()
        
        print(f"📋 Updated pipeline: {pipeline.biz_name} ({pipeline.total_stages} stages)")
    
    async def get_pipeline_state(self) -> Optional[PipelinePayload]:
        """Get current pipeline configuration"""
        return self.state.pipeline_payload
    
    # Lead Methods
    async def add_lead(self, lead: LeadData):
        """Add a new lead"""
        # Check if lead already exists (by session_id)
        existing_lead = next(
            (l for l in self.state.leads if l.session_id == lead.session_id), 
            None
        )
        
        if existing_lead:
            # Update existing lead
            existing_lead.name = lead.name
            existing_lead.type = lead.type
            existing_lead.company = lead.company
            existing_lead.website = lead.website
            existing_lead.phone = lead.phone
            existing_lead.email = lead.email
            existing_lead.address = lead.address
            existing_lead.requirements = lead.requirements
            existing_lead.notes = lead.notes
            existing_lead.stage = lead.stage
            existing_lead.user_tags = lead.user_tags
            existing_lead.updated_at = datetime.now().isoformat()
            
            print(f"📝 Updated lead: {lead.name} (Stage {lead.stage})")
        else:
            # Add new lead
            self.state.leads.append(lead)
            print(f"➕ Added new lead: {lead.name} (Stage {lead.stage})")
        
        # Update Kanban board
        await self._update_kanban_card(lead)
    
    async def get_leads(self) -> List[LeadData]:
        """Get all leads"""
        return self.state.leads
    
    async def get_lead_by_session(self, session_id: str) -> Optional[LeadData]:
        """Get lead by session ID"""
        return next(
            (lead for lead in self.state.leads if lead.session_id == session_id), 
            None
        )
    
    async def move_lead_to_stage(self, session_id: str, new_stage: int):
        """Move a lead to a different stage"""
        lead = await self.get_lead_by_session(session_id)
        if lead:
            old_stage = lead.stage
            lead.stage = new_stage
            lead.updated_at = datetime.now().isoformat()
            
            print(f"🔄 Moved lead {lead.name} from stage {old_stage} to {new_stage}")
            
            # Update Kanban board
            await self._update_kanban_card(lead)
    
    # Conversation Methods
    async def add_owner_message(self, message: str, response: str):
        """Add owner conversation"""
        self.state.owner_conversations.append({
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"💬 Added owner conversation (total: {len(self.state.owner_conversations)})")
    
    async def add_lead_message(self, session_id: str, message: str, response: str):
        """Add lead conversation"""
        if session_id not in self.state.lead_conversations:
            self.state.lead_conversations[session_id] = []
        
        self.state.lead_conversations[session_id].append({
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"💬 Added lead conversation for {session_id}")
    
    # Kanban Board Methods
    async def get_kanban_board(self) -> KanbanBoard:
        """Get current Kanban board"""
        return self.state.kanban_board
    
    async def _rebuild_kanban_board(self):
        """Rebuild the entire Kanban board from pipeline and leads"""
        if not self.state.pipeline_payload:
            return
        
        # Create columns from pipeline stages
        columns = []
        for stage in self.state.pipeline_payload.stages:
            column = KanbanColumn(
                stage_number=stage.stage_number,
                stage_name=stage.stage_name,
                brief_stage_goal=stage.brief_stage_goal,
                cards=[]
            )
            columns.append(column)
        
        # Add leads to appropriate columns
        for lead in self.state.leads:
            card = KanbanCard(
                id=lead.session_id,
                lead_name=lead.name or f"Lead {lead.session_id[:8]}",
                lead_type=lead.type,
                user_tags=lead.user_tags,
                stage=lead.stage,
                updated_at=lead.updated_at
            )
            
            # Add card to appropriate column
            for column in columns:
                if column.stage_number == lead.stage:
                    column.cards.append(card)
                    break
        
        # Update board
        self.state.kanban_board = KanbanBoard(
            business_name=self.state.business_data.biz_name,
            columns=columns,
            total_leads=len(self.state.leads),
            updated_at=datetime.now().isoformat()
        )
        
        print(f"🗂️  Rebuilt Kanban board with {len(columns)} columns and {len(self.state.leads)} leads")
    
    async def _update_kanban_card(self, lead: LeadData):
        """Update a specific card in the Kanban board"""
        if not self.state.pipeline_payload:
            return
        
        # Find and update/create the card
        card_updated = False
        
        for column in self.state.kanban_board.columns:
            # Remove card from wrong column
            column.cards = [c for c in column.cards if c.id != lead.session_id]
            
            # Add card to correct column
            if column.stage_number == lead.stage:
                card = KanbanCard(
                    id=lead.session_id,
                    lead_name=lead.name or f"Lead {lead.session_id[:8]}",
                    lead_type=lead.type,
                    user_tags=lead.user_tags,
                    stage=lead.stage,
                    updated_at=lead.updated_at
                )
                column.cards.append(card)
                card_updated = True
        
        if card_updated:
            self.state.kanban_board.total_leads = len(self.state.leads)
            self.state.kanban_board.updated_at = datetime.now().isoformat()
            print(f"🗂️  Updated Kanban card for {lead.name}")
    
    # Session Management
    async def add_active_session(self, session_id: str, session_data: Dict[str, Any]):
        """Add an active session"""
        self.state.active_sessions[session_id] = session_data
    
    async def remove_active_session(self, session_id: str):
        """Remove an active session"""
        if session_id in self.state.active_sessions:
            del self.state.active_sessions[session_id]
            print(f"🗑️  Removed session: {session_id}")
    
    async def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions"""
        return self.state.active_sessions

    def save_session_state(self, session_state: Dict[str, Any]) -> None:
        """Save complete session state for ready state preparation"""
        self.state.session_state = session_state
        # Create a task to save state asynchronously without blocking
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                asyncio.create_task(self.save_state())
            else:
                # If no loop is running, run the coroutine
                asyncio.run(self.save_state())
        except RuntimeError:
            # Fallback: just update the state without saving to file immediately
            # The state will be saved on the next auto-save or shutdown
            pass
        print("Session state saved")

    def get_session_state(self) -> Dict[str, Any]:
        """Get the complete session state"""
        return self.state.session_state 