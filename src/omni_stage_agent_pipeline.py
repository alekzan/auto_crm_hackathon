# src/omni_stage_agent_pipeline.py

from dotenv import load_dotenv
import os
import uuid
from vertexai import agent_engines
from crm_agent_pipeline import extract_user_data  # importa la función del CRM pipeline

load_dotenv()

#— Carga de ID desde .env
OMNI_STAGE_AGENT = os.getenv("OMNI_STAGE_AGENT")

def get_engine(agent_id: str):
    """Devuelve el objeto Engine para el reasoningEngine dado."""
    return agent_engines.get(agent_id)

def start_omni_session(initial_state: dict = None) -> dict:
    """
    Crea una nueva sesión en el Omni Stage Agent.
    Si se le pasa initial_state, la usa para arrancar en esa etapa.
    """
    engine = get_engine(OMNI_STAGE_AGENT)
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    if initial_state:
        session = engine.create_session(user_id=user_id, state=initial_state)
    else:
        session = engine.create_session(user_id=user_id)
    return {"engine": engine, **session}

def stream_query(engine, user_id: str, session_id: str, message: str):
    """Yields los eventos de respuesta del Omni Stage Agent."""
    for event in engine.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message
    ):
        yield event

def get_state(engine, user_id: str, session_id: str) -> dict:
    """Recupera el state completo de la sesión Omni."""
    sess = engine.get_session(user_id=user_id, session_id=session_id)
    return sess.get("state", {})


def extract_user_data(state: dict) -> dict:
    """Extrae los campos dinámicos para el user DB."""
    return {
        "user_name":    state.get("Name", ""),
        "user_tag":     state.get("Type", ""),
        "company":      state.get("Company", ""),
        "website":      state.get("Website", ""),
        "phone":        state.get("Phone", ""),
        "email":        state.get("Email", ""),
        "address":      state.get("Address", ""),
        "requirements": state.get("Requirements", ""),
        "notes":        state.get("Notes", ""),
        "stage":        state.get("current_stage", 1.0),
    }