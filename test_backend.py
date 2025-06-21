#!/usr/bin/env python3
"""
Test script for AI-Powered CRM MVP Backend
Phase 1: Test owner chat functionality
"""

import sys
import os
import asyncio
import uuid
from datetime import datetime

# Add backend to path
sys.path.append('.')

async def test_imports():
    """Test that all our modules import correctly"""
    print("🧪 Testing imports...")
    
    try:
        from backend.models import ChatMessage, ChatResponse, PipelinePayload
        print("✅ Models imported successfully")
        
        from backend.agents import CRMAgentManager, OmniAgentManager
        print("✅ Agents imported successfully")
        
        from backend.state_manager import StateManager
        print("✅ State manager imported successfully")
        
        from backend.websocket_manager import WebSocketManager
        print("✅ WebSocket manager imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

async def test_state_manager():
    """Test state manager functionality"""
    print("\n🧪 Testing State Manager...")
    
    try:
        from backend.state_manager import StateManager
        from backend.models import BusinessData, LeadData
        
        # Create state manager
        state_manager = StateManager("test_state.json")
        
        # Test business data
        business_data = BusinessData(
            biz_name="Test Company",
            biz_info="A test company for CRM",
            goal="Test goal",
            business_id=str(uuid.uuid4())
        )
        
        await state_manager.update_business_data(business_data)
        retrieved_data = await state_manager.get_business_data()
        
        assert retrieved_data.biz_name == "Test Company"
        print("✅ Business data storage works")
        
        # Test lead data
        lead_data = LeadData(
            name="Test Lead",
            type="Customer",
            company="Lead Company",
            email="test@example.com",
            stage=1,
            session_id=str(uuid.uuid4())
        )
        
        await state_manager.add_lead(lead_data)
        leads = await state_manager.get_leads()
        
        assert len(leads) == 1
        assert leads[0].name == "Test Lead"
        print("✅ Lead data storage works")
        
        # Clean up test file
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")
        
        return True
        
    except Exception as e:
        print(f"❌ State manager error: {str(e)}")
        return False

async def test_models():
    """Test Pydantic models"""
    print("\n🧪 Testing Models...")
    
    try:
        from backend.models import ChatMessage, ChatResponse, PipelinePayload, StageConfig
        
        # Test ChatMessage
        message = ChatMessage(
            content="Hello, can you help me create a pipeline?",
            session_id=str(uuid.uuid4())
        )
        
        assert message.content == "Hello, can you help me create a pipeline?"
        print("✅ ChatMessage model works")
        
        # Test ChatResponse
        response = ChatResponse(
            response="I can help you create a pipeline!",
            session_id=message.session_id,
            pipeline_complete=False,
            timestamp=datetime.now().isoformat()
        )
        
        assert response.pipeline_complete is False
        print("✅ ChatResponse model works")
        
        # Test PipelinePayload
        stage = StageConfig(
            stage_name="Lead Qualification",
            stage_number=1,
            entry_condition="New lead enters system",
            prompt="Qualify the lead",
            brief_stage_goal="Determine if lead is qualified",
            fields=["name", "email", "company"],
            user_tags=["new", "unqualified"]
        )
        
        pipeline = PipelinePayload(
            biz_name="Test Business",
            biz_info="A test business",
            goal="Generate leads",
            business_id=str(uuid.uuid4()),
            total_stages=1,
            stages=[stage]
        )
        
        assert pipeline.total_stages == 1
        assert len(pipeline.stages) == 1
        print("✅ PipelinePayload model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Models error: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 AI-Powered CRM MVP - Backend Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_models,
        test_state_manager
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # Summary
    print("\n📊 Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Backend is ready for Phase 1.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 