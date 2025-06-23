# AI Powered Auto-CRM

This is a fully AI-powered CRM system that builds itself and runs automatically using multi-agent workflows. It was created for the Google ADK Hackathon to show how complex business tools can be automated using AI.

### ✨ Live Demo

**Try it here:** [https://auto-crm-ai-49793268080.us-central1.run.app](https://auto-crm-ai-49793268080.us-central1.run.app)
**Watch the video demo:** [https://youtu.be/zmA\_eOgJ8O4](https://youtu.be/zmA_eOgJ8O4)

---

### 🚀 What it does

* One AI agent talks to the business owner, collects business info, and builds a full CRM pipeline with stages.
* Another AI agent talks to leads and moves them through the pipeline automatically.
* Business owners can upload a PDF that is used by the AI to answer questions from customers.
* The pipeline is fully dynamic and updates in real time.

---

### 🧩 Tech Stack

* **Frontend:** React + Vite
* **Backend:** FastAPI
* **Agents:** Google Vertex AI Reasoning Engines + Google ADK
* **Cloud:** Google Cloud Storage + Vertex AI + RAG Corpus
* **Libs:** google-cloud-aiplatform, google-adk, pydantic, python-dotenv, google-genai

---

### 🧰 Main Features

* AI builds and runs the entire CRM system
* Chat interface for business setup and lead interaction
* Automatic lead qualification and movement across pipeline
* Real-time Kanban board and database updates
* Persistent sessions and secure state management

---

### 🔧 How it works

* The CRM Agent builds the structure based on a conversation with the business owner.
* A RAG corpus is created from the uploaded file.
* The Omni Agent uses that data to chat with leads and move them through the funnel.
* Everything is dynamic and handled by just two AI agents.

---

### ✅ Why it's unique

Most CRMs need forms and setup. This one builds itself from a conversation. One agent creates the system, the other runs it. It’s ideal for small businesses that want automation without the complexity.

---

### 🔄 Next Steps

* Add lead import and export features
* Integrate with tools like HubSpot or Salesforce
* Add analytics to track performance
* Let the AI edit the pipeline on user request
* Add tools like web search and code execution for more advanced needs

---

Made with love, AI, and late nights by [@alekzan](https://github.com/alekzan)
