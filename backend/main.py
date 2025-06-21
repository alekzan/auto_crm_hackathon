#!/usr/bin/env python3
"""
AI-Powered CRM MVP - FastAPI Backend
Main application entry point
"""

import os
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.agents import CRMAgentManager, OmniAgentManager
from backend.models import (
    ChatMessage, 
    ChatResponse, 
    PipelinePayload, 
    LeadData,
    BusinessData
)
from backend.state_manager import StateManager
from backend.websocket_manager import WebSocketManager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered CRM MVP",
    description="One-night MVP with two Vertex AI agents working together",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
crm_agent = CRMAgentManager()
omni_agent = OmniAgentManager()
state_manager = StateManager()
websocket_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Initialize application state on startup"""
    print("🚀 Starting AI-Powered CRM MVP Backend...")
    
    # Load persisted state if it exists
    await state_manager.load_state()
    
    print("✅ Backend initialized successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Save state on shutdown"""
    print("💾 Saving application state...")
    await state_manager.save_state()
    print("👋 Backend shutting down...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI-Powered CRM MVP Backend", 
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

# Owner Chat Endpoints (Phase 1)
@app.post("/owner/chat")
async def owner_chat(message: ChatMessage) -> ChatResponse:
    """
    Owner chat endpoint - handles conversation with CRM Stage Builder Agent
    Supports text messages and file uploads to build custom sales pipeline
    """
    try:
        print(f"📨 Owner chat message: {message.content[:100]}...")
        
        # Get or create CRM session
        session = await crm_agent.get_or_create_session(message.session_id)
        
        # Handle file uploads if present
        if message.files:
            for file_info in message.files:
                await crm_agent.handle_file_upload(
                    session["session_id"], 
                    file_info["path"], 
                    file_info["name"]
                )
        
        # Send message to CRM agent and stream response
        response_parts = []
        async for event in crm_agent.stream_query(
            session["session_id"], 
            message.content
        ):
            response_parts.append(event)
        
        # Combine response parts
        full_response = crm_agent.combine_response_parts(response_parts)
        
        # Check if pipeline is complete and extract payload
        is_complete = await crm_agent.is_pipeline_complete(session["session_id"])
        pipeline_payload = None
        
        # Always try to extract pipeline payload for debugging
        try:
            pipeline_payload = await crm_agent.extract_pipeline_payload(session["session_id"])
            print(f"🔧 Pipeline payload extracted: {pipeline_payload is not None}")
        except Exception as e:
            print(f"⚠️ Pipeline extraction error: {str(e)}")
        
        if is_complete and pipeline_payload:
            # Broadcast pipeline update via WebSocket
            await websocket_manager.broadcast_pipeline_update(pipeline_payload)
        
        # Store conversation in state
        await state_manager.add_owner_message(message.content, full_response)
        
        return ChatResponse(
            response=full_response,
            session_id=session["session_id"],
            pipeline_complete=is_complete,
            pipeline_payload=pipeline_payload.model_dump() if pipeline_payload else None,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Owner chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/owner/upload")
async def upload_file(file: UploadFile = File(...), session_id: Optional[str] = None):
    """
    Handle file uploads for the owner chat
    Supports PDF, DOCX, CSV files for pipeline creation
    """
    try:
        # Validate file type
        allowed_types = ['.pdf', '.docx', '.csv']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not supported. Allowed: {allowed_types}"
            )
        
        # Save file temporarily
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = f"{upload_dir}/{uuid.uuid4().hex}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"📁 File uploaded: {file.filename} -> {file_path}")
        
        return {
            "filename": file.filename,
            "path": file_path,
            "size": len(content),
            "type": file_ext
        }
        
    except Exception as e:
        print(f"❌ File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# State Management Endpoints
@app.get("/state/pipeline")
async def get_pipeline_state():
    """Get current pipeline state"""
    return await state_manager.get_pipeline_state()

@app.get("/state/leads")
async def get_leads():
    """Get all leads data"""
    return await state_manager.get_leads()

@app.get("/state/business")
async def get_business_data():
    """Get business configuration data"""
    return await state_manager.get_business_data()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for real-time updates"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Echo back for now (can be extended for bidirectional communication)
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        print(f"🔌 WebSocket disconnected: {client_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 