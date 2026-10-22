# JARVIS Nexus 🤖

**Your Personal AI Action Assistant**

JARVIS Nexus is a local AI assistant that combines a web dashboard, a locally running language model, and a Model Context Protocol (MCP) server to help users manage tasks and reminders through natural-language interactions.

## Features

- **AI Chat:** Interact with JARVIS through a web-based dashboard.
- **Task Management:** Create, list, and complete tasks.
- **Reminders:** Create and view reminders.
- **Local AI:** Uses Ollama with the `qwen2.5:7b` model.
- **MCP Integration:** Connects the assistant to task and reminder tools.
- **Local Data Storage:** Stores tasks and reminders in JSON files.

## Technology Stack

- Python
- FastAPI
- Ollama
- Qwen 2.5 (7B)
- Model Context Protocol (MCP)
- HTML, CSS, and JavaScript
- JSON

## Prerequisites

Before running JARVIS Nexus, install:

- Python 3.11 or a compatible Python version supported by the dependencies.
- [Ollama](https://ollama.com/)
- Git (optional, for cloning the repository)

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Jarvis-Nexus
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the repository URL after publishing the project.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Download the AI model

```powershell
ollama pull qwen2.5:7b
```

Ensure Ollama is running before starting the application.

## Running JARVIS Nexus

Open separate terminals in the project directory.

### Terminal 1: Start the MCP server

Activate the virtual environment, then run:

```powershell
python mcp_server.py
```

### Terminal 2: Start the FastAPI application

Activate the virtual environment, then run:

```powershell
python -m uvicorn main:app --reload --port 8000
```

Open the dashboard in your browser:

http://127.0.0.1:8000

The MCP server is configured to use port `8001`, and the Ollama API is configured at `http://127.0.0.1:11434`.

## Data Storage

Task and reminder information is stored locally in:

- `data/tasks.json`
- `data/reminders.json`

These files are excluded from the Git repository to avoid publishing personal data. The application creates the data directory when needed.

## Project Structure

```text
Jarvis-Nexus/
├── frontend/
├── data/                 # Local task and reminder data
├── main.py               # FastAPI application and AI integration
├── mcp_server.py         # MCP tools and JSON storage
├── test_mcp.py           # MCP integration test
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md
```

## Notes

- JARVIS Nexus is designed to run locally on the user's computer.
- The Qwen model must be downloaded through Ollama before AI chat can work.
- Keep the MCP server and FastAPI application running while using the dashboard.
- Do not commit personal data, credentials, or secret environment files.

## Future Improvements

- Voice interaction
- More system automation tools
- Improved error handling
- Expanded task and reminder workflows

---

Built as an AI assistant project for the Amazon Developer Hackathon.