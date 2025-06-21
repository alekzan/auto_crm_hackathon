# UTILS
# Upload the artifact to Google Cloud Storage
# Create a new RAG Corpus for a business owner
# Add a PDF file to the owner's RAG Corpus
from dotenv import load_dotenv
import os, uuid, time
from google.adk.events import Event, EventActions
from google.cloud import storage
from pathlib import Path
from mimetypes import guess_type
from typing import Tuple, Dict, Any, List
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag import TransformationConfig, ChunkingConfig
from google.adk.sessions import VertexAiSessionService



load_dotenv()  # Esto busca el .env en el root del proyecto

# Ahora la variable de entorno ya está disponible para Google Cloud
print("Credenciales:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

from google.cloud import storage

client = storage.Client()
bucket_name = "adk_hackathon_bucket"
gcs_folder = "crm_demo"
bucket = client.bucket(bucket_name)
print(f"✅ Conectado al bucket: {bucket.name}")

# Upload a file to Google Cloud Storage
def upload_to_gcs(local_path: str, bucket_name: str = bucket_name, folder: str = gcs_folder) -> Tuple[str, str]:
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    file_path = Path(local_path)
    filename = file_path.name

    destination_path = f"{folder}/{filename}"
    blob = bucket.blob(destination_path)
    blob.upload_from_filename(str(file_path))

    gcs_uri = f"gs://{bucket_name}/{destination_path}"
    print(f"✅ Subido: {file_path} → {gcs_uri}")
    return filename, gcs_uri

# Create a new RAG Corpus for a business owner
def create_corpus_for_new_owner(project_id: str, location: str, owner_display_name: str) -> str:
    """
    Creates a new, dedicated RAG Corpus for a business owner.
    Returns: The full resource name of the new corpus.
    """
    vertexai.init(project=project_id, location=location)
    
    print(f"Creating new RAG Corpus for {owner_display_name}...")
    corpus = rag.create_corpus(display_name=f"Corpus for {owner_display_name}")
    
    print(f"Successfully created corpus: {corpus.name}")
    return corpus.name # This is the ID you will save, e.g., "projects/..."

# Add a PDF file to the owner's RAG Corpus
def add_pdf_to_owner_corpus(project_id: str, location: str, owner_corpus_id: str, gcs_pdf_path: str):
    """
    Ingests a PDF from GCS into a specific owner's RAG Corpus.
    """
    vertexai.init(project=project_id, location=location)

    # These are the correct arguments based on your screenshot.
    response = rag.import_files(
        corpus_name=owner_corpus_id,
        paths=[gcs_pdf_path],
        # You can optionally include chunking configuration here if needed
        transformation_config=TransformationConfig(
            chunking_config=ChunkingConfig(
            chunk_size=512,  # Adjust chunk size as needed
            chunk_overlap=64,
        ),
                                                       )
    )
    print(f"Started import of {gcs_pdf_path} into corpus {owner_corpus_id}. Response: {response}")

# Update the session state with a new event
async def handle_upload_and_patch_state(
    crm_engine_app:str,
    local_file: str,
    user_id: str,
    session_id: str
):
    # 1) Detect MIME type
    mime_type, _ = guess_type(local_file)
    mime_type = mime_type or "application/octet-stream"
    
    # 2) Upload to GCS
    filename, gcs_uri = upload_to_gcs(local_file)
    
    # 3) Create (or reuse) a RAG corpus for this owner
    corpus_name = create_corpus_for_new_owner(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        owner_display_name=user_id
    )
    
    # 4) Ingest into that corpus
    add_pdf_to_owner_corpus(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        owner_corpus_id=corpus_name,
        gcs_pdf_path=gcs_uri
    )
    
    # 5) Initialize the SessionService with constants
    session_svc = VertexAiSessionService(
        project="49793268080",
        location="us-central1",
    )
    
    # 6) Use the constant app_name
    #crm_engine_app
    
    # 7) Fetch the live session
    session = await session_svc.get_session(
        app_name=crm_engine_app,
        user_id=user_id,
        session_id=session_id,
    )
    
    # 8) Build the state delta with both uploaded_docs and rag_corpus
    current_uploads = session.state.get("uploaded_docs", [])
    new_upload_entry = {"filename": filename, "gcs_uri": gcs_uri}
    
    delta = {
        "uploaded_docs": current_uploads + [new_upload_entry],
        "rag_corpus": corpus_name
    }
    
    # 9) Create and append the event
    evt = Event(
        invocation_id=str(uuid.uuid4()),
        author="system",
        timestamp=time.time(),
        actions=EventActions(state_delta=delta),
    )
    
    await session_svc.append_event(session=session, event=evt)
    print(f"✅ Session {session_id} patched with uploads & rag_corpus")


async def build_ready_state(
    session_state: Dict[str, Any], # Ahora acepta el estado directamente
    current_stage: int = 1
) -> Dict[str, Any]:
    """
    Recibe el estado completo de una sesión existente (ej. intake session)
    y lo transforma en un diccionario plano listo para inyectar en una nueva sesión.
    """

    st = session_state
    ready: Dict[str, Any] = {}

    # 1) Siempre incluye estos cuatro, con valores predeterminados si faltan
    ready["intake_completed"]    = st.get("intake_completed", False)
    ready["uploaded_docs"]       = st.get("uploaded_docs", [])
    ready["rag_corpus"]          = st.get("rag_corpus", "")
    ready["pipeline_completed"]  = st.get("pipeline_completed", False)

    # 2) Extrae business/biz_info/goal/kb_files desde el nivel superior o intake_data
    for k in ("business_id", "biz_name", "biz_info", "goal", "kb_files"):
        if k in st:
            ready[k] = st[k]
        elif "intake_data" in st and k in st["intake_data"]:
            ready[k] = st["intake_data"][k]
        elif "pipeline" in st \
             and "intake_data" in st["pipeline"] \
             and k in st["pipeline"]["intake_data"]:
            ready[k] = st["pipeline"]["intake_data"][k]
        else:
            ready[k] = [] if k == "kb_files" else ""

    # 3) Aplanar cada etapa del pipeline
    stages: List[Dict[str, Any]] = []
    if "pipeline" in st and "stage_design_results" in st["pipeline"] and "stages" in st["pipeline"]["stage_design_results"]:
        stages = st["pipeline"]["stage_design_results"]["stages"]
    
    ready["total_stages"] = len(stages)
    for stage in stages:
        n = stage.get("stage_number") # Get the stage number, potentially a float like 1.0

        # Convert 'n' to an integer for the key, if it's a float like X.0
        # This part ensures the key for the flattened state is always an integer.
        key_n = n # Default to n
        if isinstance(n, float) and n.is_integer():
            key_n = int(n)
        elif n is None:
            print(f"Advertencia: Etapa sin 'stage_number' válido o faltante: {stage}")
            continue # Skip this stage if no valid number for key

        for field, value in stage.items():
            # --- CAMBIO CLAVE AQUÍ: Ajustar el valor antes de asignarlo si es stage_number ---
            if field == "stage_number":
                # If the value is a float like X.0, convert it to int X
                if isinstance(value, float) and value.is_integer():
                    ready[f"stage_{key_n}_{field}"] = int(value)
                else:
                    ready[f"stage_{key_n}_{field}"] = value # Keep as is if not X.0 float
            else:
                ready[f"stage_{key_n}_{field}"] = value
    
    # 4) Construir contexto de "current stage"
    if stages and 0 < current_stage <= len(stages):
        cs = stages[current_stage - 1] 
        kb_list = ready.get("kb_files", []) 

        # Ensure current_stage_number is also an integer if it came as float
        current_stage_num_value = cs.get("stage_number")
        if isinstance(current_stage_num_value, float) and current_stage_num_value.is_integer():
            current_stage_num_value = int(current_stage_num_value)

        ready.update({
            "current_stage":   current_stage,
            "current_artifacts": ", ".join(kb_list),
            "current_stage_name":       cs.get("stage_name", ""),
            "current_stage_brief_goal": cs.get("brief_stage_goal", ""),
            "current_stage_prompt":     cs.get("prompt", ""),
            "current_stage_fields":     cs.get("fields", {}),
            "current_stage_user_tags":  cs.get("user_tags", []),
            # Ensure stage_number in this combined string is also int
            "all_stages_names_and_descriptions_and_entry_conditions":
                "\n\n".join(
                    f"{int(s.get('stage_number')) if isinstance(s.get('stage_number'), float) and s.get('stage_number').is_integer() else s.get('stage_number', '')}. {s.get('stage_name', '')}: {s.get('brief_stage_goal', '')}\nEntry: {s.get('entry_condition', '')}"
                    for s in stages
                ),
        })
        # Add the converted current_stage_number to ready if needed (it's already in ready[f"stage_{key_n}_{field}"])
        # ready["current_stage_number_value"] = current_stage_num_value # You could add this if you need it separately
    else:
        ready.update({
            "current_stage":   current_stage,
            "current_artifacts": "",
            "current_stage_name":       "",
            "current_stage_brief_goal": "",
            "current_stage_prompt":     "",
            "current_stage_fields":     {},
            "current_stage_user_tags":  [],
            "all_stages_names_and_descriptions_and_entry_conditions": "",
        })

    return ready