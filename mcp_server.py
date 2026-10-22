import json
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP


# Create the JARVIS Nexus MCP server.
mcp = FastMCP(
    "JARVIS Nexus",
    host="127.0.0.1",
    port=8001
)

# Store application data inside the project folder.
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TASKS_FILE = DATA_DIR / "tasks.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"


def load_data(file_path):
    """Load saved information from a JSON file."""
    if not file_path.exists():
        return []

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_data(file_path, data):
    """Save information to a JSON file."""
    file_path.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


@mcp.tool()
def add_task(title: str) -> dict:
    """Create and save a new task."""

    title = title.strip()

    if not title:
        return {"success": False, "message": "Task cannot be empty."}

    tasks = load_data(TASKS_FILE)

    task = {
        "id": max((item["id"] for item in tasks), default=0) + 1,
        "title": title,
        "completed": False,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    tasks.append(task)
    save_data(TASKS_FILE, tasks)

    return {
        "success": True,
        "message": "Task created successfully.",
        "task": task
    }


@mcp.tool()
def list_tasks() -> dict:
    """Return all saved tasks."""

    return {
        "success": True,
        "tasks": load_data(TASKS_FILE)
    }


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Mark a task as completed using its ID."""

    tasks = load_data(TASKS_FILE)

    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            save_data(TASKS_FILE, tasks)

            return {
                "success": True,
                "message": "Task marked as completed.",
                "task": task
            }

    return {
        "success": False,
        "message": f"No task found with ID {task_id}."
    }


@mcp.tool()
def add_reminder(title: str, reminder_time: str) -> dict:
    """
    Save a reminder.

    reminder_time must use ISO format, for example:
    2026-10-22T09:00:00
    """

    title = title.strip()

    if not title:
        return {
            "success": False,
            "message": "Reminder title cannot be empty."
        }

    try:
        parsed_time = datetime.fromisoformat(reminder_time)
    except ValueError:
        return {
            "success": False,
            "message": "Use a valid ISO date and time."
        }

    reminders = load_data(REMINDERS_FILE)

    reminder = {
        "id": max(
            (item["id"] for item in reminders),
            default=0
        ) + 1,
        "title": title,
        "reminder_time": parsed_time.isoformat(timespec="seconds"),
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    reminders.append(reminder)
    save_data(REMINDERS_FILE, reminders)

    return {
        "success": True,
        "message": "Reminder saved successfully.",
        "reminder": reminder
    }


@mcp.tool()
def list_reminders() -> dict:
    """Return all saved reminders."""

    return {
        "success": True,
        "reminders": load_data(REMINDERS_FILE)
    }


if __name__ == "__main__":
    print("Starting JARVIS Nexus MCP server...")
    print("Local MCP endpoint: http://127.0.0.1:8001/mcp")

    mcp.run(transport="streamable-http")