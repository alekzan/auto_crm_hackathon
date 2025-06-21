#!/usr/bin/env python3
"""
Setup test for AI-Powered CRM MVP - Fixed Version
Phase 0: Verify connection to Vertex AI agents using the correct vertexai.agent_engines approach
"""

import os
from dotenv import load_dotenv
import uuid

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
    """Test basic connection to CRM Stage Builder Agent using correct vertexai approach"""
    try:
        # Import the correct vertexai module
        from vertexai import agent_engines
        from google.cloud import aiplatform
        
        print("\n🤖 Testing CRM Stage Builder Agent connection...")
        
        # Initialize AI Platform
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION')
        aiplatform.init(project=project_id, location=location)
        
        # Get the CRM agent ID
        crm_stage_agent = os.getenv('CRM_STAGE_AGENT')
        
        # Get a handle to the existing engine
        print(f"📡 Getting engine handle for: {crm_stage_agent}")
        remote_app = agent_engines.get(crm_stage_agent)
        
        # Create a new session
        u_id = f"u_{uuid.uuid4().hex[:8]}"
        print(f"🆔 Creating session with user ID: {u_id}")
        
        remote_session = remote_app.create_session(user_id=u_id)
        print(f"✅ Session created: {remote_session['id']}")
        
        # Test message
        test_message = "Hello! Can you help me create a simple 3-stage sales pipeline?"
        print(f"📤 Sending test message: {test_message}")
        
        # Stream the response
        print("📥 Agent response:")
        full_response = ""
        for event in remote_app.stream_query(
            user_id=remote_session["userId"],
            session_id=remote_session["id"],
            message=test_message,
        ):
            # Print each event as it comes
            event_text = str(event)
            print(event_text)
            full_response += event_text
        
        print(f"\n✅ CRM Agent connection successful!")
        print(f"📊 Total response length: {len(full_response)} characters")
        
        # Cleanup - delete the session
        try:
            remote_app.delete(force=True)
            print("🧹 Session cleaned up")
        except Exception as cleanup_err:
            print(f"⚠️  Cleanup warning (non-critical): {cleanup_err}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRM Agent connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main setup test function"""
    print("🚀 AI-Powered CRM MVP - Setup Test (Fixed)")
    print("=" * 55)
    
    # Test environment
    if not test_environment():
        print("\n💡 Create a .env file with the required variables and try again.")
        return False
    
    # Test agent connection
    if not test_crm_agent_connection():
        print("\n💡 Check your Google Cloud credentials and agent configuration.")
        return False
    
    print("\n🎉 Setup test completed successfully!")
    print("✨ Ready to proceed with Phase 1: Owner Chat UI")
    return True

if __name__ == "__main__":
    main() 