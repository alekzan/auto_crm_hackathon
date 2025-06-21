# AI‑Powered CRM – One‑Night MVP PRD

## 1. Purpose

Deliver a single‑night proof of concept that demonstrates two Vertex AI agents working together inside a small, modern web app.

The web app is divided into four key sections:

1. A chat interface for the business owner to interact with the CRM Stage Builder Agent.
2. A Kanban board generated from the pipeline structure.
3. A lead table that reflects user data captured by the Omni Stage Agent.
4. A chat interface for leads to interact with the Omni Stage Agent.

Deliver a single‑night proof of concept that demonstrates two Vertex AI agents working together inside a small, modern web app.

- **CRM Stage Builder Agent** – lets the business owner design a custom sales pipeline.
- **Omni Stage Agent** – chats with each lead, gathers data, and advances the lead through pipeline stages.

## 2. MVP Scope (Tonight)

The MVP covers functionality across the four main sections of the app:

1. **Owner Chat with CRM Agent**
   - Owner can upload reference files (PDF, DOCX, CSV).
   - Agent returns `pipeline_payload` JSON.
2. **Kanban View**
   - Columns: `stage_name` from the payload.
   - Card contents: lead identifier plus `user_tags`.
3. **Lead Chat with Omni Agent**
   - Each message updates the lead’s state.
   - Stage transitions move the corresponding card in the Kanban.
4. **Lead Table**
   - Columns: `Name, Type, Company, Website, Phone, Email, Address, Requirements, Notes, Stage`.
   - Populated directly from the Omni Agent’s state object.
5. **Persist in Memory**
   - Use in‑memory Python dicts; dump to JSON file on app shutdown for quick restart.

*No multi‑tenant auth, analytics or heavy persistence in this MVP.*

## 3. Tech Stack

### Required Python Packages

```
google-cloud-aiplatform[adk,agent_engines]==1.97.0
google-adk==1.3.0
pydantic==2.11.4
google-api-python-client==2.172.0
google-genai==1.20.0
python-dotenv
```

Recommended stack: | Layer | Choice | Reason | | Frontend | **React + Vite + Tailwind** | Modern look, quick scaffold, flexible components | | Backend | **FastAPI** | Lightweight Python server to call Vertex AI agents and expose REST/WebSocket endpoints | | Realtime updates | **WebSockets via FastAPI** | Push state changes to React without polling | | LLM connectivity | `vertexai` SDK (sync) | Simplest stable path tonight | | Temporary storage | Python dicts → JSON dump | Zero external setup; quick reload |

## 4. Environment Variables

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=hackathon-adk
GOOGLE_CLOUD_LOCATION=us-central1
STAGING_BUCKET=gs://adk_hackathon_bucket

# Main agents
CRM_STAGE_AGENT=projects/49793268080/locations/us-central1/reasoningEngines/7234302725649858560
OMNI_STAGE_AGENT=projects/49793268080/locations/us-central1/reasoningEngines/3944423197855711232

# For optional RAG corpus tasks
PROJECT_ID=49793268080

GOOGLE_APPLICATION_CREDENTIALS=<path-to-service-account.json>
```

## 5. Phases & Success Criteria

| Phase                       | Target Outcome                           | Key Tasks                                                                                                          | Acceptance                                                  |
| --------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| **0. Setup**                | Local hello‑world call to CRM Agent      | \* Load env vars \* Authenticate service account \* Call `stream_query` once                                       | JSON response appears in console                            |
| **1. Owner Chat UI**        | Owner can chat & send files to CRM Agent | \* FastAPI endpoint `/owner/chat` \* File upload handling \* Proxy messages to agent                               | Endpoint returns full `pipeline_payload`                    |
| **2. Kanban Generator**     | Visual pipeline based on payload         | \* Parse `stage_name`, `brief_stage_goal`, `user_tags` \* React Kanban component renders columns dynamically       | Board loads with correct columns                            |
| **3. Lead Chat UI**         | End‑user chat powered by Omni Agent      | \* FastAPI endpoint `/lead/chat` \* React chat widget \* Maintain session ids                                      | Replies flow in UI                                          |
| **4. Live Sync**            | Kanban & Lead Table auto‑update          | \* WebSocket channel broadcasts state deltas \* React listeners move cards, update rows                            | Drag‑free update within <1 s                                |
| **5. Persistence & Export** | State survives restart and is shareable  | \* Dump dicts to `state.json` every 30 s \* Endpoint `/export/prd` uploads this PRD MD to `crm_prd_exports` bucket | JSON reloaded correctly after restart & file appears in GCS |

