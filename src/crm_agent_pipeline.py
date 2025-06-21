# src/crm_agent_pipeline.py

from dotenv import load_dotenv
import os
import uuid
from vertexai import agent_engines
from utils.utils import (
    handle_upload_and_patch_state,
    build_ready_state,
)

load_dotenv()

#— Carga de IDs desde .env
CRM_STAGE_AGENT  = os.getenv("CRM_STAGE_AGENT")
OMNI_STAGE_AGENT = os.getenv("OMNI_STAGE_AGENT")

def get_engine(agent_id: str):
    """Returns the Engine object for the given reasoningEngine."""
    return agent_engines.get(agent_id)

def start_crm_session() -> dict:
    """Creates a new session in the CRM Stage Agent."""
    engine = get_engine(CRM_STAGE_AGENT)
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    session = engine.create_session(user_id=user_id)
    return {"engine": engine, **session}

def stream_query(engine, user_id: str, session_id: str, message: str):
    """Yields the agent's response events."""
    for event in engine.stream_query(
        user_id=user_id, 
        session_id=session_id, 
        message=message
    ):
        yield event

async def upload_and_patch(engine, user_id: str, session_id: str, local_file: str):
    """Uploads a file to the bucket and patches the state."""
    return await handle_upload_and_patch_state(
        engine,
        local_file,
        user_id=user_id,
        session_id=session_id,
    )
    
def get_state(engine, user_id: str, session_id: str) -> dict:
    """Retrieves the complete session state."""
    sess = engine.get_session(user_id=user_id, session_id=session_id)
    return sess.get("state", {})

def is_pipeline_complete(engine, user_id: str, session_id: str) -> bool:
    """
    Queries the session and returns True if the pipeline is complete.
    - engine: the Engine object (not its name).
    - user_id, session_id: session identifiers.
    """
    sess = engine.get_session(user_id=user_id, session_id=session_id)
    state = sess.get("state", {})
    # El path pipeline → pipeline_completed puede variar; ajusta si es distinto
    return bool(state.get("pipeline", {}).get("pipeline_completed", False))

async def prepare_ready_state(engine, user_id: str, session_id: str, current_stage: int = 1) -> dict:
    """
    Retrieves the latest CRM session state and builds the ready_state
    to pass to the Omni Stage Agent.
    """
    # 1) traemos la sesión completa
    remote_session = engine.get_session(user_id=user_id, session_id=session_id)
    state = remote_session.get("state", {})

    # 2) construimos el ready_state (pasa current_stage=1 si siempre inicias en la etapa 1)
    ready_state = await build_ready_state(session_state=state, current_stage=current_stage)
    return ready_state

def extract_business_data(state: dict) -> dict:
    """Extracts the static business context fields."""
    return {
        "biz_name":    state.get("biz_name", ""),
        "biz_info":    state.get("biz_info", ""),
        "goal":        state.get("goal", ""),
        "business_id": state.get("business_id", ""),
    }

def build_stages(state: dict) -> list[dict]:
    """Builds the list of stages based on total_stages."""
    total = int(state.get("total_stages", 0))
    stages = []
    for i in range(1, total+1):
        stages.append({
            "stage_name":       state.get(f"stage_{i}_stage_name", ""),
            "stage_number":     state.get(f"stage_{i}_stage_number", ""),
            "entry_condition":  state.get(f"stage_{i}_entry_condition", ""),
            "prompt":           state.get(f"stage_{i}_prompt", ""),
            "brief_stage_goal": state.get(f"stage_{i}_brief_stage_goal", ""),
            "fields":           state.get(f"stage_{i}_fields", []),
            "user_tags":        state.get(f"stage_{i}_user_tags", []),
        })
    return stages
