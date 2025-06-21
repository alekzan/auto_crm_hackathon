#!/usr/bin/env python3
"""
Setup test for AI-Powered CRM MVP
Phase 0: Verify connection to Vertex AI agents
"""

import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'GOOGLE_GENAI_USE_VERTEXAI', 
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_CLOUD_LOCATION',
        'CRM_STAGE_AGENT',
        'OMNI_STAGE_AGENT'
    ]
    
    print("🔍 Checking environment variables...")
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def test_crm_agent_connection():
    """Test basic connection to CRM Stage Builder Agent"""
    try:
        # Import after env vars are loaded
        from google.cloud import aiplatform
        from google.adk.client import ADKClient
        
        print("\n🤖 Testing CRM Stage Builder Agent connection...")
        
        # Initialize the client
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION')
        crm_agent_id = os.getenv('CRM_STAGE_AGENT')
        
        # Initialize AI Platform
        aiplatform.init(project=project_id, location=location)
        
        # Create ADK client
        client = ADKClient()
        
        # Test message
        test_message = "Hello! Can you help me create a simple 3-stage sales pipeline?"
        
        print(f"📤 Sending test message: {test_message}")
        
        # Call the agent
        response = client.stream_query(
            reasoning_engine=crm_agent_id,
            query=test_message
        )
        
        print("📥 Agent response:")
        full_response = ""
        for chunk in response:
            content = chunk.text if hasattr(chunk, 'text') else str(chunk)
            print(content, end='', flush=True)
            full_response += content
        
        print(f"\n\n✅ CRM Agent connection successful!")
        print(f"📊 Response length: {len(full_response)} characters")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRM Agent connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main setup test function"""
    print("🚀 AI-Powered CRM MVP - Setup Test")
    print("=" * 50)
    
    # Test environment
    if not test_environment():
        print("\n💡 Create a .env file with the required variables and try again.")
        return False
    
    # Test agent connection
    if not test_crm_agent_connection():
        print("\n💡 Check your Google Cloud credentials and agent configuration.")
        return False
    
    print("\n🎉 Setup test completed successfully!")
    print("Ready to proceed with Phase 1: Owner Chat UI")
    return True

if __name__ == "__main__":
    main() 