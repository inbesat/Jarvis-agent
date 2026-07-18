"""
Jarvis Memory Server - Full Memory Backend
Run this to access your memory core at http://localhost:5050
Sections: Chat History, Notes, Future Ideas, Todo List, Tasks
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

DATA_DIR = Path("./jarvis_memory_data")
DATA_DIR.mkdir(exist_ok=True)

SECTIONS = {
    "chat_history": DATA_DIR / "chat_history.json",
    "notes": DATA_DIR / "notes.json",
    "future_ideas": DATA_DIR / "future_ideas.json",
    "todo_list": DATA_DIR / "todo_list.json",
    "tasks": DATA_DIR / "tasks.json",
}

def load_section(section):
    path = SECTIONS.get(section)
    if path and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_section(section, data):
    path = SECTIONS.get(section)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/")
def index():
    return send_from_directory(".", "jarvis_memory_ui.html")

# --- Chat History ---
@app.route("/api/chat_history", methods=["GET"])
def list_chat_history():
    return jsonify(load_section("chat_history"))

@app.route("/api/chat_history", methods=["POST"])
def add_chat_message():
    data = load_section("chat_history")
    msg = request.json or {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "role": msg.get("role", "user"),
        "content": msg.get("content", ""),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.append(entry)
    save_section("chat_history", data)
    return jsonify(entry)

@app.route("/api/chat_history/<item_id>", methods=["DELETE"])
def delete_chat_message(item_id):
    data = load_section("chat_history")
    data = [x for x in data if x.get("id") != item_id]
    save_section("chat_history", data)
    return jsonify({"ok": True})

@app.route("/api/chat_history/clear", methods=["POST"])
def clear_chat_history():
    save_section("chat_history", [])
    return jsonify({"ok": True})

# --- Notes ---
@app.route("/api/notes", methods=["GET"])
def list_notes():
    return jsonify(load_section("notes"))

@app.route("/api/notes", methods=["POST"])
def add_note():
    data = load_section("notes")
    note = request.json or {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "title": note.get("title", "Untitled Note"),
        "content": note.get("content", ""),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.append(entry)
    save_section("notes", data)
    return jsonify(entry)

@app.route("/api/notes/<item_id>", methods=["PUT"])
def update_note(item_id):
    data = load_section("notes")
    note = request.json or {}
    for x in data:
        if x.get("id") == item_id:
            x["title"] = note.get("title", x["title"])
            x["content"] = note.get("content", x["content"])
            x["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_section("notes", data)
            return jsonify(x)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/notes/<item_id>", methods=["DELETE"])
def delete_note(item_id):
    data = load_section("notes")
    data = [x for x in data if x.get("id") != item_id]
    save_section("notes", data)
    return jsonify({"ok": True})

# --- Future Ideas ---
@app.route("/api/future_ideas", methods=["GET"])
def list_future_ideas():
    return jsonify(load_section("future_ideas"))

@app.route("/api/future_ideas", methods=["POST"])
def add_future_idea():
    data = load_section("future_ideas")
    idea = request.json or {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "title": idea.get("title", "Untitled Idea"),
        "content": idea.get("content", ""),
        "priority": idea.get("priority", "medium"),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.append(entry)
    save_section("future_ideas", data)
    return jsonify(entry)

@app.route("/api/future_ideas/<item_id>", methods=["PUT"])
def update_future_idea(item_id):
    data = load_section("future_ideas")
    idea = request.json or {}
    for x in data:
        if x.get("id") == item_id:
            x["title"] = idea.get("title", x["title"])
            x["content"] = idea.get("content", x["content"])
            x["priority"] = idea.get("priority", x["priority"])
            save_section("future_ideas", data)
            return jsonify(x)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/future_ideas/<item_id>", methods=["DELETE"])
def delete_future_idea(item_id):
    data = load_section("future_ideas")
    data = [x for x in data if x.get("id") != item_id]
    save_section("future_ideas", data)
    return jsonify({"ok": True})

# --- Todo List ---
@app.route("/api/todo_list", methods=["GET"])
def list_todo():
    return jsonify(load_section("todo_list"))

@app.route("/api/todo_list", methods=["POST"])
def add_todo():
    data = load_section("todo_list")
    todo = request.json or {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "text": todo.get("text", ""),
        "status": todo.get("status", "pending"),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.append(entry)
    save_section("todo_list", data)
    return jsonify(entry)

@app.route("/api/todo_list/<item_id>", methods=["PUT"])
def update_todo(item_id):
    data = load_section("todo_list")
    todo = request.json or {}
    for x in data:
        if x.get("id") == item_id:
            x["text"] = todo.get("text", x["text"])
            x["status"] = todo.get("status", x.get("status", "pending"))
            save_section("todo_list", data)
            return jsonify(x)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/todo_list/<item_id>", methods=["DELETE"])
def delete_todo(item_id):
    data = load_section("todo_list")
    data = [x for x in data if x.get("id") != item_id]
    save_section("todo_list", data)
    return jsonify({"ok": True})

# --- Tasks ---
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    return jsonify(load_section("tasks"))

@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = load_section("tasks")
    task = request.json or {}
    entry = {
        "id": str(uuid.uuid4())[:8],
        "title": task.get("title", "Untitled Task"),
        "description": task.get("description", ""),
        "status": task.get("status", "pending"),
        "priority": task.get("priority", "medium"),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data.append(entry)
    save_section("tasks", data)
    return jsonify(entry)

@app.route("/api/tasks/<item_id>", methods=["PUT"])
def update_task(item_id):
    data = load_section("tasks")
    task = request.json or {}
    for x in data:
        if x.get("id") == item_id:
            x["title"] = task.get("title", x["title"])
            x["description"] = task.get("description", x["description"])
            x["status"] = task.get("status", x["status"])
            x["priority"] = task.get("priority", x["priority"])
            x["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_section("tasks", data)
            return jsonify(x)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/tasks/<item_id>", methods=["DELETE"])
def delete_task(item_id):
    data = load_section("tasks")
    data = [x for x in data if x.get("id") != item_id]
    save_section("tasks", data)
    return jsonify({"ok": True})

# --- Search across all sections ---
@app.route("/api/search", methods=["GET"])
def search_all():
    q = request.args.get("q", "").lower()
    results = {}
    for section_name in SECTIONS:
        items = load_section(section_name)
        matches = []
        for item in items:
            search_text = json.dumps(item).lower()
            if q in search_text:
                matches.append(item)
        if matches:
            results[section_name] = matches
    return jsonify(results)

# --- Import from old chat log ---
@app.route("/api/import_txt", methods=["POST"])
def import_txt():
    txt_path = Path("jarvis_chat_log.txt")
    if not txt_path.exists():
        return jsonify({"error": "jarvis_chat_log.txt not found"}), 404

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = load_section("chat_history")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    imported = 0
    for line in lines:
        line = line.strip()
        if line.startswith("User: "):
            data.append({"id": str(uuid.uuid4())[:8], "role": "user", "content": line[6:], "timestamp": now})
            imported += 1
        elif line.startswith("Jarvis: "):
            data.append({"id": str(uuid.uuid4())[:8], "role": "assistant", "content": line[8:], "timestamp": now})
            imported += 1
    save_section("chat_history", data)
    return jsonify({"ok": True, "imported": imported})

# --- Start the server ---
if __name__ == "__main__":
    print("=" * 60)
    print("  JARVIS MEMORY CORE SERVER")
    print("  Open http://localhost:5050 in your browser")
    print("  Sections: Chat History | Notes | Future Ideas | Todo | Tasks")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5050, debug=False)
