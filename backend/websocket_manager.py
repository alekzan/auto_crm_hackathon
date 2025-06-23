"""
WebSocket manager for AI-Powered CRM MVP
Handles real-time updates and connections
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from backend.models import WebSocketMessage, PipelinePayload, LeadData, KanbanBoard

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts real-time updates
    """
    
    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, WebSocket] = {}
        
        print("🔌 WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        print(f"🔗 WebSocket connected: {client_id} (total: {len(self.active_connections)})")
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connection_established",
            "message": "WebSocket connection established",
            "client_id": client_id
        })
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔗 WebSocket disconnected: {client_id} (remaining: {len(self.active_connections)})")
    
    async def send_to_client(self, client_id: str, data: Dict[str, Any]):
        """Send data to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                
                # Create WebSocket message
                message = WebSocketMessage(
                    type=data.get("type", "message"),
                    data=data
                )
                
                # Send as JSON
                await websocket.send_text(message.model_dump_json())
                
            except WebSocketDisconnect:
                # Connection was closed, remove it
                self.disconnect(client_id)
            except Exception as e:
                print(f"❌ Error sending to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, data: Dict[str, Any], exclude: Optional[List[str]] = None):
        """Broadcast data to all connected clients"""
        if not self.active_connections:
            return
        
        exclude = exclude or []
        
        # Create WebSocket message
        message = WebSocketMessage(
            type=data.get("type", "broadcast"),
            data=data
        )
        
        message_json = message.model_dump_json()
        disconnected_clients = []
        
        # Send to all clients except excluded ones
        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await websocket.send_text(message_json)
                except WebSocketDisconnect:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    print(f"❌ Error broadcasting to {client_id}: {str(e)}")
                    disconnected_clients.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        if disconnected_clients:
            print(f"🧹 Cleaned up {len(disconnected_clients)} disconnected clients")
    
    # Specific broadcast methods for different update types
    
    async def broadcast_pipeline_update(self, pipeline: PipelinePayload):
        """Broadcast pipeline update to all clients"""
        await self.broadcast({
            "type": "pipeline_updated",
            "pipeline": pipeline.model_dump(),
            "message": f"Pipeline updated: {pipeline.biz_name} ({pipeline.total_stages} stages)"
        })
        
        print(f"📡 Broadcasted pipeline update: {pipeline.biz_name}")
    
    async def broadcast_lead_update(self, lead: LeadData):
        """Broadcast lead update to all clients"""
        await self.broadcast({
            "type": "lead_updated",
            "lead": lead.model_dump(),
            "message": f"Lead updated: {lead.name} (Stage {lead.stage})"
        })
        
        print(f"📡 Broadcasted lead update: {lead.name}")
    
    async def broadcast_state_reset(self):
        """Broadcast state reset to all clients"""
        await self.broadcast({
            "type": "state_reset",
            "message": "Application state has been reset",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"📡 Broadcasted state reset to all clients")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_connected_clients(self) -> List[str]:
        """Get list of connected client IDs"""
        return list(self.active_connections.keys())
