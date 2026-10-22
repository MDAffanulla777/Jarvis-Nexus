import json
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from mcp_server import (
    add_task,
    list_tasks,
    complete_task,
    add_reminder,
    list_reminders,
)


# ============================================
# JARVIS NEXUS APPLICATION
# ============================================

app = FastAPI(
    title="JARVIS Nexus",
    description="Your Personal AI Action Assistant",
    version="1.0.0",
)

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"

FRONTEND_DIR.mkdir(exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"
MCP_URL = "http://127.0.0.1:8001/mcp"


# ============================================
# REQUEST MODELS
# ============================================

class TaskRequest(BaseModel):
    title: str


class ChatRequest(BaseModel):
    message: str


class CompleteTaskRequest(BaseModel):
    task_id: int


class ReminderRequest(BaseModel):
    title: str
    reminder_time: str


# ============================================
# DASHBOARD
# ============================================

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "success": True,
        "application": "JARVIS Nexus",
        "status": "online",
    }


# ============================================
# TASK API
# ============================================

@app.get("/api/tasks")
def get_tasks():
    return list_tasks()


@app.post("/api/tasks")
def create_task(request: TaskRequest):
    return add_task(request.title)


@app.post("/api/tasks/complete")
def finish_task(request: CompleteTaskRequest):
    return complete_task(request.task_id)


# ============================================
# REMINDER API
# ============================================

@app.get("/api/reminders")
def get_reminders():
    return list_reminders()


@app.post("/api/reminders")
def create_reminder(request: ReminderRequest):
    return add_reminder(
        request.title,
        request.reminder_time,
    )


# ============================================
# CONVERT MCP TOOLS FOR OLLAMA
# ============================================

def convert_mcp_tools(mcp_tools):
    """
    Convert MCP tool definitions into Ollama's
    function-calling format.
    """

    ollama_tools = []

    for tool in mcp_tools:
        ollama_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or tool.name,
                "parameters": tool.inputSchema,
            },
        })

    return ollama_tools


# ============================================
# READ MCP TOOL RESULTS
# ============================================

def read_tool_result(result):
    """Convert MCP results into text for the AI."""

    parts = []

    for item in result.content:
        if hasattr(item, "text"):
            parts.append(item.text)

    output = "\n".join(parts)

    if result.isError:
        return json.dumps({
            "success": False,
            "error": output or "MCP tool execution failed.",
        })

    return output or json.dumps({
        "success": True,
        "message": "Tool executed successfully.",
    })


# ============================================
# JARVIS AI CHAT WITH MCP TOOL CALLING
# ============================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        return {
            "success": False,
            "response": "Please enter a message.",
        }

    messages = [
        {
            "role": "system",
            "content": (
                "You are JARVIS Nexus, a helpful personal AI "
                "assistant built for productivity and the "
                "Amazon Developer Hackathon. "
                "You have access to MCP tools for tasks and reminders. "
                "When the user requests an action supported by a tool, "
                "call the appropriate tool instead of merely describing "
                "what you would do. "
                "For requests to list tasks or reminders, use the "
                "corresponding list tool. "
                "Use complete_task only when you know the correct task ID. "
                "For reminders, obtain a specific date and time if it is "
                "missing. Use ISO date-time format such as "
                "2026-10-25T09:00:00. "
                "Never claim an action succeeded unless the tool result "
                "confirms success. If a tool fails, explain the failure. "
                "Answer clearly and concisely."
            ),
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:

            # Connect to the MCP server.
            async with streamablehttp_client(MCP_URL) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(
                    read_stream,
                    write_stream,
                ) as session:

                    await session.initialize()

                    # Discover available MCP tools.
                    tool_result = await session.list_tools()

                    ollama_tools = convert_mcp_tools(
                        tool_result.tools
                    )

                    # Allow the AI to use tools and then explain
                    # the actual results to the user.
                    for _ in range(5):

                        payload = {
                            "model": OLLAMA_MODEL,
                            "messages": messages,
                            "stream": False,
                        }

                        if ollama_tools:
                            payload["tools"] = ollama_tools

                        response = await client.post(
                            OLLAMA_URL,
                            json=payload,
                        )
                        print("OLLAMA STATUS:", response.status_code)
                        print("OLLAMA RESPONSE:", response.text)
                        response.raise_for_status()

                        data = response.json()
                        assistant_message = data["message"]

                        # Save the assistant response in the
                        # conversation before processing tool calls.
                        messages.append(assistant_message)

                        tool_calls = assistant_message.get(
                            "tool_calls",
                            [],
                        )

                        # If there are no tool calls, the AI
                        # has finished answering the user.
                        if not tool_calls:
                            return {
                                "success": True,
                                "response": assistant_message.get(
                                    "content",
                                    "I'm here, sir.",
                                ),
                            }

                        # Execute every requested MCP tool.
                        for tool_call in tool_calls:

                            function = tool_call.get(
                                "function",
                                {},
                            )

                            tool_name = function.get("name")
                            arguments = function.get("arguments", {})

                            if isinstance(arguments, str):
                                arguments = json.loads(arguments)

                            available_tools = {
                                tool.name for tool in tool_result.tools
                            }

                            if tool_name not in available_tools:
                                tool_output = json.dumps({
                                    "success": False,
                                    "error": (
                                        "Requested tool is unavailable: "
                                        + str(tool_name)
                                    ),
                                })
                            else:
                                try:
                                    result = await session.call_tool(
                                        tool_name,
                                        arguments=arguments,
                                    )

                                    tool_output = read_tool_result(
                                        result
                                    )

                                except Exception as tool_error:
                                    tool_output = json.dumps({
                                        "success": False,
                                        "error": str(tool_error),
                                    })

                            # Give the actual tool result back
                            # to Ollama so it can explain it.
                            messages.append({
                                "role": "tool",
                                "tool_name": tool_name or "unknown",
                                "content": tool_output,
                            })

                    return {
                        "success": False,
                        "response": (
                            "I reached the tool-call limit. "
                            "Please try a simpler request."
                        ),
                    }

    except httpx.TimeoutException:
        return {
            "success": False,
            "response": (
                "The AI took too long to respond. "
                "Please try again."
            ),
        }

    except httpx.HTTPError as error:
        print("HTTP error:", repr(error))

        return {
            "success": False,
            "response": (
                "Could not connect to the AI service. "
                "Check that Ollama is running."
            ),
        }

    except Exception as error:
        print("JARVIS MCP error:", repr(error))

        return {
            "success": False,
            "response": (
                "I encountered a problem connecting to my tools. "
                "Please check that the MCP server is running."
            ),
        }