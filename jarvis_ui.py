import tkinter as tk
import threading
import numpy as np
import sounddevice as sd
import time
from datetime import datetime
import subprocess
import shutil
# speech_recognition is an optional dependency; import dynamically to avoid hard failure
try:
    import importlib
    sr = importlib.import_module("speech_recognition")
except ImportError:  # pragma: no cover - optional dependency for environments without it
    sr = None
import requests
try:
    import edge_tts
except ImportError:  # pragma: no cover - optional dependency
    edge_tts = None
import asyncio
import pygame
import os
import math
import random
import keyboard  
import re
import base64
import io
import json
import pyautogui
from pywinauto import Desktop
from PIL import ImageGrab
from groq import Groq
from ddgs import DDGS
from huggingface_hub import HfApi
from serpapi import GoogleSearch  
import chromadb 
import webbrowser
import urllib.parse
try:
    import keyboard
except ImportError:  # pragma: no cover - optional dependency
    keyboard = None
from sentence_transformers import SentenceTransformer
from pathlib import Path
from openai import OpenAI

env_file = Path(".") / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip() # This prevents hidden space formatting errors
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# --- 2. GLOBAL CLIENT INITIALIZATION (MUST BE HERE) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
    print("[ WARNING ] GROQ_API_KEY not set. Groq will be unavailable.")
    groq_client = None
else:
    groq_client = Groq(api_key=GROQ_API_KEY)

GROQ_API_KEY_BACKUP = os.getenv("GROQ_API_KEY_BACKUP")
if GROQ_API_KEY_BACKUP and GROQ_API_KEY_BACKUP != "YOUR_BACKUP_GROQ_KEY_HERE":
    groq_client_backup = Groq(api_key=GROQ_API_KEY_BACKUP)
else:
    groq_client_backup = None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_API_KEY, 
    timeout=15.0
) if OPENROUTER_API_KEY else None

OPENROUTER_API_KEY_BACKUP = os.getenv("OPENROUTER_API_KEY_BACKUP")
if OPENROUTER_API_KEY_BACKUP and OPENROUTER_API_KEY_BACKUP != "YOUR_BACKUP_OPENROUTER_KEY_HERE":
    openrouter_client_backup = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY_BACKUP,
        timeout=15.0
    )
else:
    openrouter_client_backup = None

# --- 4. OTHER GLOBAL VARS & CONFIG ---
ANYTHING_API_KEY = os.getenv("ANYTHING_API_KEY")
WORKSPACE_SLUG = os.getenv("WORKSPACE_SLUG", "jarvis")
ANYTHING_API_URL = f"http://localhost:3001/api/v1/workspace/{WORKSPACE_SLUG}/chat"

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
# (Initialize other keys here using os.getenv as well)
HF_TOKEN = os.getenv("HF_TOKEN")
api = HfApi(token=HF_TOKEN)

# --- GLOBAL AUDIO METRICS ---
CURRENT_AUDIO_AMPLITUDE = 0.0

# Now start your function definitions below...
pyautogui.FAILSAFE = True
if pygame is not None:
    try:
        pygame.mixer.init()
    except ImportError as e:
        print(f"[ SYSTEM WARNING ] pygame.mixer failed to initialize: {e}")

async def speak_async_segment(text_chunk, app_instance):
    """Generates and plays small localized voice segments on the fly."""
    audio_file = "jarvis_stream_segment.mp3"
    try:
        communicate = edge_tts.Communicate(text_chunk, "en-GB-ThomasNeural")
        await communicate.save(audio_file)
        
        if pygame is None:
            print("[ TTS STREAM ] pygame not available; skipping playback.")
        else:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
        
        if pygame is not None:
            while pygame.mixer.music.get_busy():
                if app_instance and hasattr(app_instance, 'stop_playback') and app_instance.stop_playback.is_set():
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.05)
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
        if os.path.exists(audio_file):
            os.remove(audio_file)
    except Exception as e:
        print("[ TTS STREAM FAILED ] Segment dropout: " + str(e))

LOG_FILE = "jarvis_chat_log.txt"
MEMORY_API = "http://localhost:5050/api"

def save_to_memory(user_text, ai_text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"User: {user_text}\n")
        f.write(f"Jarvis: {ai_text}\n\n")
    try:
        requests.post(f"{MEMORY_API}/chat_history", json={"role": "user", "content": user_text}, timeout=2)
        requests.post(f"{MEMORY_API}/chat_history", json={"role": "assistant", "content": ai_text}, timeout=2)
    except Exception:
        pass

def get_recent_memory():
    if not os.path.exists(LOG_FILE):
        return "No previous memory."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-20:])

def check_internet():
    try:
        requests.get("http://www.duckduckgo.com", timeout=2)
        return True
    except:
        return False

# --- EMBEDDED CHROMADB LOCAL RAG ---
CHROMA_DIR = "./jarvis_embedded_rag"
embedding_model = None

def get_local_embedding(text):
    global embedding_model
    if embedding_model is None:
        print("[ SYSTEM ] Loading local sentence-transformer array handles...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model.encode(text).tolist()

def get_embedded_rag_context(question):
    if not os.path.exists(CHROMA_DIR):
        return "Local RAG directory context path empty."
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_or_create_collection(name="user_knowledge")
        query_vector = get_local_embedding(question)
        results = collection.query(query_embeddings=[query_vector], n_results=3)
        documents = results.get('documents', [[]])[0]
        if documents:
            context_str = "LOCAL EMBEDDED MATERIAL ACCESS CODES:\n"
            for doc in documents: context_str += f"- {doc}\n"
            return context_str + "\n"
    except Exception as e:
        print(f"[ SYSTEM ERROR ] Embedded Local RAG access failure: {e}")
    return ""

def ask_serpapi(query):
    if SERPAPI_API_KEY == "YOUR_SERPAPI_KEY_HERE":
        return "SerpApi lookup keys not deployed."
    try:
        print(f"[ Tool ] Dispatching SerpApi Engine for: '{query}'")
        params = {"q": query, "hl": "en", "gl": "us", "api_key": SERPAPI_API_KEY}
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "answer_box" in results and "answer" in results["answer_box"]: return f"Direct Answer: {results['answer_box']['answer']}"
        elif "answer_box" in results and "snippet" in results["answer_box"]: return f"Direct Answer: {results['answer_box']['snippet']}"
            
        snippets = []
        if "organic_results" in results:
            for res in results["organic_results"][:3]: snippets.append(f"- {res.get('title')}: {res.get('snippet')}")
        if snippets: return "\n".join(snippets)
        return "No explicit search answers scraped."
    except Exception as e:
        return f"SerpApi cluster runtime interaction issue: {e}"    

def query_notion_notebook(query):
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {"filter": {"or": [{"property": "Name", "title": {"contains": query}}]}}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"NOTION WORKSPACE DATA: Found {len(data['results'])} notes related to '{query}'."
        return "Notion integration failed to retrieve workspace data."
    except Exception as e:
        return f"Notion API error: {e}"

def capture_screen():
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        screenshot.thumbnail((1280, 1280))
        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=75)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception:
        try:
            screenshot = ImageGrab.grab()
            screenshot.thumbnail((1024, 1024))
            buffered = io.BytesIO()
            screenshot.save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str
        except Exception as e:
            print(f"[ SYSTEM ERROR ] Failed to capture screen: {e}")
            return None

def get_accessibility_tree():
    try:
        windows = Desktop(backend="uia").windows()
        tree_data = []
        for win in windows[:8]:
            title = win.window_text()
            if title:
                tree_data.append(f"Window: '{title}'")
                children = win.descendants(control_type="Button") + win.descendants(control_type="Edit") + win.descendants(control_type="Text") + win.descendants(control_type="Hyperlink") + win.descendants(control_type="ListItem")
                for child in children[:20]:
                    text = child.window_text()
                    if text and len(text.strip()) > 0:
                        tree_data.append(f"  - [{child.element_info.control_type}] Name: '{text[:80]}'")
        return "\n".join(tree_data)
    except Exception as e:
        return f"Accessibility Tree scan failed: {e}"

def ask_agent_model(system_prompt, user_content):
    """
    Universal agent engine with smart model fallback.
    When images are present, tries vision models first.
    Falls back to backup keys when primary keys fail.
    Falls back to next model on any error or invalid JSON.
    """
    has_image = isinstance(user_content, list) and len(user_content) > 1
    text_only = user_content[0]["text"] if isinstance(user_content, list) else user_content

    if has_image:
        provider_chain = [
            ("openrouter", "google/gemini-2.5-flash", "Gemini 2.5 Flash (Vision)"),
            ("openrouter", "qwen/qwen-2.5-vl-72b-instruct", "Qwen 2.5 Vision 72B"),
            ("openrouter_backup", "google/gemini-2.5-flash", "Gemini 2.5 Flash (Backup Key)"),
            ("openrouter_backup", "qwen/qwen-2.5-vl-72b-instruct", "Qwen Vision (Backup Key)"),
            ("openrouter", "meta-llama/llama-3.3-70b-instruct", "Llama 3.3 (Text-only)"),
            ("groq", "llama-3.3-70b-versatile", "Groq Llama 3.3 (Text-only)"),
            ("groq_backup", "llama-3.3-70b-versatile", "Groq Llama 3.3 (Backup Key)"),
        ]
    else:
        provider_chain = [
            ("groq", "llama-3.3-70b-versatile", "Groq Llama 3.3 (Primary)"),
            ("groq_backup", "llama-3.3-70b-versatile", "Groq Llama 3.3 (Backup Key)"),
            ("openrouter", "google/gemini-2.5-flash", "Gemini 2.5 Flash"),
            ("openrouter_backup", "google/gemini-2.5-flash", "Gemini (Backup Key)"),
            ("openrouter", "meta-llama/llama-3.3-70b-instruct", "Llama 3.3"),
        ]

    for client_type, model_id, provider_name in provider_chain:
        try:
            print("[ MODEL ] Trying: " + provider_name)

            if client_type in ("groq", "groq_backup"):
                client = groq_client if client_type == "groq" else groq_client_backup
                if client is None:
                    print("[ MODEL ] " + provider_name + " not available (no key), skipping...")
                    continue
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text_only}
                    ],
                    max_tokens=400,
                    response_format={"type": "json_object"}
                )
                result = response.choices[0].message.content

            elif client_type in ("openrouter", "openrouter_backup"):
                client = openrouter_client if client_type == "openrouter" else openrouter_client_backup
                if client is None:
                    print("[ MODEL ] " + provider_name + " not available (no key), skipping...")
                    continue
                messages_payload = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                response = client.chat.completions.create(
                    model=model_id,
                    messages=messages_payload,
                    max_tokens=400,
                    response_format={"type": "json_object"}
                )
                result = response.choices[0].message.content

            try:
                parsed = json.loads(result)
                if "action" in parsed:
                    print("[ MODEL ] Success via " + provider_name + " -> action: " + parsed["action"])
                    return result
                else:
                    print("[ MODEL ] " + provider_name + " returned JSON without 'action' field, trying next...")
                    continue
            except json.JSONDecodeError:
                print("[ MODEL ] " + provider_name + " returned invalid JSON, trying next...")
                continue

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                print("[ ERROR ] Auth failed for " + provider_name + ". Check API key.")
            elif "429" in error_msg or "rate_limit" in error_msg or "insufficient_quota" in error_msg:
                print("[ WARNING ] " + provider_name + " quota exhausted. Switching...")
            elif "404" in error_msg:
                print("[ WARNING ] " + provider_name + " endpoint not found. Switching...")
            else:
                print("[ WARNING ] " + provider_name + " error: " + str(e)[:200] + ". Switching...")
            continue

    print("[ FATAL ] All API models exhausted.")
    return json.dumps({"action": "done", "message": "All API models failed."})

# Replace your current execute_hybrid_action and get_ai_response functions with this perfect block

def execute_hybrid_action(task, initial_base64_image):
    print("[ AGENT ] Initiating Universal Autonomous Loop for: " + task)
    action_history = []
    scroll_count = 0
    max_scrolls = 5
    opened_apps = set()

    system_prompt = "You are Jarvis, an AI desktop agent. TASK: " + task + """

OUTPUT: EXACTLY ONE raw JSON object. Nothing else. No markdown. No explanation.

ACTIONS (use ONLY these):
{"action":"open_app","app_name":"name"}
{"action":"click","x":123,"y":456}
{"action":"type","text":"hello"}
{"action":"press_key","key":"enter"}
{"action":"hotkey","keys":["ctrl","f"]}
{"action":"scroll","amount":-500}
{"action":"click_link","text":"link text"}
{"action":"open_url","url":"https://..."}
{"action":"wait","seconds":2}
{"action":"done","message":"what was accomplished"}

RULES (violation = failure):
1. Execute the MINIMUM actions needed. Do exactly what was asked. Nothing more.
2. After opening an app, NEVER open it again. The app is already open.
3. After typing text, output "done". Do NOT type more unless the task explicitly says so.
4. For websites: ALWAYS use Chrome (already open or use ctrl+l). Never open a new browser.
5. NEVER click random buttons, open random tabs, or explore the screen.
6. NEVER close anything (no ctrl+w, no alt+f4, no escape unless dismissing a popup).
7. NEVER guess coordinates. Use accessibility tree element names or click_link.
8. After the LAST action of the task, ALWAYS output done immediately.
9. If the task is "open X and do Y", the actions are: open X -> wait -> do Y -> done.
10. For messages: type text THEN press enter THEN done.

CRITICAL - YOUTUBE SEARCH + CLICK LATEST VIDEO:
To search and open the latest video on YouTube:
Step 1: {"action":"open_url","url":"https://youtube.com/results?search_query=QUERY"}
Step 2: {"action":"wait","seconds":3}
Step 3: {"action":"click_link","text":"first video title from search results"}
Step 4: {"action":"done","message":"Opened latest video for QUERY"}
The accessibility tree will show video titles after search loads. Click the FIRST video result.

CRITICAL - HOW TO SEND MESSAGES (Instagram/Telegram/WhatsApp):
1. The chat list is in the LEFT SIDEBAR. Use the accessibility tree to find the person's name.
2. {"action":"click_link","text":"PersonName"} to open their chat.
3. {"action":"wait","seconds":2} for chat to load.
4. Find the MESSAGE INPUT field - it is at the BOTTOM of the screen. Use accessibility tree to find the textbox/input field at the bottom.
5. {"action":"type","text":"your message"}
6. {"action":"press_key","key":"enter"}
7. {"action":"done","message":"Sent message to PersonName"}

CRITICAL - SCREEN UNDERSTANDING (VISION):
When the user asks "what's on screen" or "describe the screen":
You CAN see the screenshot. Look at the image carefully.
Describe what you see: apps open, text visible, videos, websites, buttons, menus.
Be specific - mention actual text, titles, colors, layout you observe.
If the task asks you to describe the screen, output: {"action":"done","message":"<detailed description of what you see>"}

WEBSITE KNOWLEDGE:
- YOUTUBE: Left sidebar: Home, Shorts, Subscriptions, Library. Search bar top. Videos show as thumbnails with titles. Click the FIRST video thumbnail after searching.
- INSTAGRAM: Left sidebar has chat list. Click a person's name. Message input at BOTTOM. Press enter to send.
- TELEGRAM: Left sidebar has chat list. Click a person's name. Message input at BOTTOM. Press enter to send.
- WHATSAPP WEB: Left sidebar has chat list. Click a person's name. Message input at BOTTOM. Press enter to send.
- NOTEPAD: Full text area. Just type after opening.
- VS CODE: ctrl+shift+p for command palette. File explorer on left.
- CHROME: ctrl+l = address bar. Type URL. Enter.

EXAMPLES:
Task: "open notepad and write hello world"
Step 1: {"action":"open_app","app_name":"notepad"}
Step 2: {"action":"wait","seconds":3}
Step 3: {"action":"type","text":"hello world"}
Step 4: {"action":"done","message":"Written hello world in Notepad"}

Task: "search youtube for mrbeast and open the latest video"
Step 1: {"action":"open_url","url":"https://youtube.com/results?search_query=mrbeast+latest+video"}
Step 2: {"action":"wait","seconds":3}
Step 3: {"action":"click_link","text":"MrBeast"}
Step 4: {"action":"done","message":"Opened MrBeast latest video on YouTube"}

Task: "open instagram and message hi to John"
Step 1: {"action":"open_app","app_name":"instagram"}
Step 2: {"action":"wait","seconds":5}
Step 3: {"action":"click_link","text":"John"}
Step 4: {"action":"wait","seconds":2}
Step 5: {"action":"type","text":"hi"}
Step 6: {"action":"press_key","key":"enter"}
Step 7: {"action":"done","message":"Sent hi to John on Instagram"}

Task: "scroll down"
Step 1: {"action":"scroll","amount":-500}
Step 2: {"action":"done","message":"Scrolled down"}

Task: "what's on my screen"
Step 1: Look at the screenshot image provided.
Step 2: {"action":"done","message":"<describe everything you see on screen>"}

Output ONLY one raw JSON. If the task is complete, output done NOW."""

    for step_num in range(25):
        if keyboard.is_pressed('alt+i') or keyboard.is_pressed('alt+q'):
            print("\n[ SYSTEM ] Emergency Stop Triggered! Halting Jarvis.")
            return "Task manually interrupted by user."

        print("\n[ AGENT STEP " + str(step_num + 1) + " ] Scanning environment...")

        try:
            ui_tree = get_accessibility_tree()
            current_image = capture_screen() or initial_base64_image

            user_content = [
                {"type": "text", "text": "Task: " + task + "\nAccessibility Tree:\n" + ui_tree + "\nHistory: " + str(action_history) + "\nScroll count: " + str(scroll_count) + "/" + str(max_scrolls) + "\n\nWhat is the next action? If the task goal is visually met, output 'done'."},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + current_image}}
            ]

            response_text = ask_agent_model(system_prompt, user_content)
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            command = json.loads(clean_json)

            action = command.get("action")
            step_num_display = step_num + 1
            print("[ STEP " + str(step_num_display) + "/25 ] Action: " + str(action) + " | " + str({k: v for k, v in command.items() if k != "action"}))

            action_history.append(command)

            # If model outputs "done" but somehow continues, force return
            if len(action_history) > 1 and action_history[-2].get("action") == "done":
                print("[ AGENT ] Model continued after done. Forcing stop.")
                return "Task successfully completed."

            # --- STUCK DETECTION ---
            if len(action_history) >= 3:
                last_three = action_history[-3:]

                # Detect repeated identical actions (same action + same params)
                if all(a == last_three[0] for a in last_three):
                    print("[ WARNING ] Same action repeated 3 times. Model may be stuck.")
                    # For open_app, don't skip - it might be retrying a different app
                    if action != "open_app":
                        continue

                # Detect coordinate loops
                coords = [a.get("x") for a in last_three if a.get("action") == "click" and a.get("x") is not None]
                if len(coords) == 3 and coords[0] == coords[1] == coords[2]:
                    print("[ WARNING ] Stuck clicking same coordinates!")
                    continue

                # Detect scroll loops
                if all(a.get("action") == "scroll" for a in last_three):
                    scroll_count += 1
                    if scroll_count >= max_scrolls:
                        print("[ FAIL ] Scrolled " + str(max_scrolls) + " times. Target not found.")
                        return "Task failed. Could not locate the target item on screen."
                    continue

            # --- ACTION FAILURE TRACKING (only for stuck detection, not success) ---
            # We track repeated identical actions to detect loops, not count successes

            # --- ACTION EXECUTION ---
            if action == "open_app":
                app_name = command.get("app_name", "")
                if app_name.lower() in opened_apps:
                    print("[ AGENT ] App '" + app_name + "' already opened. Skipping.")
                else:
                    pyautogui.press('escape')
                    time.sleep(0.3)
                    pyautogui.press('escape')
                    time.sleep(0.2)
                    pyautogui.press('win')
                    time.sleep(1.0)
                    pyautogui.write(app_name, interval=0.03)
                    time.sleep(1.0)
                    pyautogui.press('enter')
                    time.sleep(3.0)
                    opened_apps.add(app_name.lower())
                    print("[ AGENT ] Opened app: " + app_name)

            elif action == "click":
                x, y = command.get("x"), command.get("y")
                if x is not None and y is not None:
                    pyautogui.click(int(x), int(y))
                else:
                    target = command.get("target") or command.get("target_name")
                    if target:
                        try:
                            Desktop(backend="uia").window(title=target, control_type="Button", top_level_only=False).click_input()
                        except Exception:
                            pass
                time.sleep(1.0)

            elif action == "click_link":
                link_text = command.get("text", "")
                print("[ AGENT ] Looking for link: '" + link_text + "'")
                try:
                    windows = Desktop(backend="uia").windows()
                    clicked = False
                    for win in windows:
                        if clicked:
                            break
                        children = win.descendants()
                        for child in children:
                            if link_text.lower() in child.window_text().lower():
                                child.click_input()
                                print("[ AGENT ] Clicked link: '" + child.window_text() + "'")
                                clicked = True
                                time.sleep(1.0)
                                break
                    if not clicked:
                        print("[ AGENT ] click_link: element not found, using ctrl+f fallback.")
                        pyautogui.hotkey('ctrl', 'f')
                        time.sleep(0.5)
                        pyautogui.write(link_text, interval=0.02)
                        time.sleep(0.5)
                        pyautogui.press('escape')
                except Exception as e:
                    print("[ AGENT ] click_link fallback: " + str(e))
                    pyautogui.hotkey('ctrl', 'f')
                    time.sleep(0.5)
                    pyautogui.write(link_text, interval=0.02)
                    time.sleep(0.5)
                    pyautogui.press('escape')
                time.sleep(1.0)

            elif action == "type":
                text_to_type = command.get("text", "")
                if text_to_type:
                    # Click center of screen first to ensure focus is on the right window
                    sw, sh = pyautogui.size()
                    pyautogui.click(sw // 2, sh // 2)
                    time.sleep(0.3)
                    pyautogui.write(text_to_type, interval=0.03)
                time.sleep(0.5)

            elif action in ["press", "press_key"]:
                pyautogui.press(command.get("key", ""))
                time.sleep(0.5)

            elif action == "hotkey":
                keys = command.get("keys", [])
                if keys:
                    pyautogui.hotkey(*keys)
                time.sleep(0.5)

            elif action == "scroll":
                amount = command.get("amount", -500)
                sw, sh = pyautogui.size()
                pyautogui.click(sw // 2, sh // 2)
                time.sleep(0.3)
                pyautogui.scroll(int(amount))
                time.sleep(1.5)

            elif action == "open_url":
                url = command.get("url", "")
                if url:
                    # Always try to activate Chrome first
                    try:
                        chrome = Desktop(backend="uia").window(title_re=".*Chrome.*", control_type="Window")
                        if chrome.exists():
                            chrome.set_focus()
                            time.sleep(0.5)
                    except Exception:
                        pass
                    pyautogui.hotkey('ctrl', 'l')
                    time.sleep(0.5)
                    pyautogui.write(url, interval=0.01)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    time.sleep(2.0)

            elif action == "find_text":
                find_text = command.get("text", "")
                if find_text:
                    pyautogui.hotkey('ctrl', 'f')
                    time.sleep(0.5)
                    pyautogui.write(find_text, interval=0.02)
                    time.sleep(0.5)
                    pyautogui.press('escape')

            elif action == "wait":
                wait_secs = command.get("seconds", 2)
                time.sleep(int(wait_secs))

            elif action == "escape":
                pyautogui.press('escape')
                time.sleep(0.5)

            elif action == "alt_tab":
                pyautogui.hotkey('alt', 'tab')
                time.sleep(1.0)

            elif action == "done":
                msg = command.get("message", "Task complete")
                print("[ AGENT ] Done: " + msg)
                return "Task completed: " + msg

            elif action == "fatal_error":
                return "Task failed. All API models were rejected."

            time.sleep(0.5)

        except json.JSONDecodeError:
            print("[ AGENT ] Invalid JSON from model: " + str(response_text)[:200])
            time.sleep(1)
        except Exception as e:
            print("[ AGENT FALLBACK ] Error: " + str(e))
            time.sleep(1)

    return "Agent reached maximum allowed steps (25) and halted."


def read_local_file(file_path):
    """Safely reads the contents of a local file for the AI to analyze."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        else:
            return f"Error: Could not find file at {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"

def get_active_vscode_file():
    """Try to detect the currently active file in VS Code via accessibility tree."""
    try:
        windows = Desktop(backend="uia").windows()
        for win in windows:
            title = win.window_text()
            if title and ("visual studio code" in title.lower() or "vscode" in title.lower()):
                # Extract filename from title like "filename.py - project - VS Code"
                parts = title.split(" - ")
                if parts:
                    filename = parts[0].strip()
                    # Search common project directories for this file
                    search_dirs = [
                        Path.home() / "Documents",
                        Path.home() / "Desktop",
                        Path.home() / "Projects",
                        Path.home() / "Code",
                    ]
                    for sd in search_dirs:
                        if sd.exists():
                            for found in sd.rglob(filename):
                                if found.is_file() and found.suffix in ['.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.jsx', '.tsx']:
                                    return str(found)
    except Exception as e:
        print(f"[ CODE GURU ] Could not detect active VS Code file: {e}")
    return None

def get_clipboard_text():
    """Read text from Windows clipboard."""
    try:
        result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True, timeout=3)
        return result.stdout.strip()
    except Exception:
        return None

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_tasks.json")

def save_note(text):
    """Save a note to the chat log AND the memory server notes section."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chat_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_chat_log.txt")
    with open(chat_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] NOTE: {text}\n")
    try:
        requests.post(f"{MEMORY_API}/notes", json={"title": text[:60], "content": text}, timeout=2)
    except Exception:
        pass
    return 'Noted. Saved: "' + text + '"'

def get_notes():
    """Read back recent notes from chat log."""
    chat_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_chat_log.txt")
    if not os.path.exists(chat_log):
        return "No notes saved yet."
    with open(chat_log, "r", encoding="utf-8") as f:
        lines = f.readlines()
    notes = [l.strip() for l in lines if "NOTE:" in l]
    if not notes:
        return "No notes saved yet."
    recent = notes[-20:]
    return "Your recent notes:\n" + "\n".join(recent)

def _load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

def add_task(text):
    """Add a task to the persistent task list."""
    tasks = _load_tasks()
    tasks.append({"task": text, "done": False, "created": datetime.now().strftime("%Y-%m-%d %H:%M")})
    _save_tasks(tasks)
    return f"Task added: \"{text}\". You now have {len([t for t in tasks if not t['done']])} pending tasks."

def list_tasks():
    """List all pending tasks."""
    tasks = _load_tasks()
    pending = [t for t in tasks if not t["done"]]
    if not pending:
        return "No pending tasks. You're all caught up."
    task_list = "\n".join(f"  {i+1}. {t['task']}" for i, t in enumerate(pending))
    return f"You have {len(pending)} pending tasks:\n{task_list}"

def complete_task(text):
    """Mark a task as done by partial text match."""
    tasks = _load_tasks()
    text_lower = text.lower()
    for t in tasks:
        if not t["done"] and text_lower in t["task"].lower():
            t["done"] = True
            _save_tasks(tasks)
            remaining = len([x for x in tasks if not x["done"]])
            return f"Done: \"{t['task']}\". {remaining} tasks remaining."
    return f"Couldn't find a task matching \"{text}\"."

def set_timer(minutes, label="Timer"):
    """Start a background timer that announces when done."""
    def _timer_thread():
        time.sleep(minutes * 60)
        try:
            import asyncio as _aio
            loop = _aio.new_event_loop()
            _aio.set_event_loop(loop)
            loop.run_until_complete(speak_async_segment(f"Time's up! {label} finished.", None))
            loop.close()
        except Exception:
            pass
    t = threading.Thread(target=_timer_thread, daemon=True)
    t.start()
    return f"Timer set for {minutes} minutes. I'll let you know when it's done."

# --- CLIPBOARD AWARENESS ---
def get_clipboard():
    """Read current clipboard content."""
    try:
        import subprocess
        result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True, timeout=5)
        text = result.stdout.strip()
        if text:
            return f"Clipboard contains: \"{text}\""
        return "Clipboard is empty."
    except Exception as e:
        return f"Could not read clipboard: {e}"

def set_clipboard(text):
    """Set clipboard content."""
    try:
        import subprocess
        subprocess.run(['powershell', '-command', f'Set-Clipboard -Value "{text}"'], timeout=5)
        return f"Clipboard set to: \"{text}\""
    except Exception as e:
        return f"Could not set clipboard: {e}"

# --- FILE OPERATIONS ---
def create_file(file_path, content=""):
    """Create a file with optional content."""
    try:
        expanded = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(expanded), exist_ok=True)
        with open(expanded, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created file: {expanded}" + (f" with {len(content)} characters." if content else " (empty).")
    except Exception as e:
        return f"Error creating file: {e}"

def write_to_file(file_path, content):
    """Append content to a file."""
    try:
        expanded = os.path.expanduser(file_path)
        with open(expanded, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to {expanded}."
    except Exception as e:
        return f"Error writing to file: {e}"

def read_file_content(file_path):
    """Read and return file contents."""
    try:
        expanded = os.path.expanduser(file_path)
        with open(expanded, "r", encoding="utf-8") as f:
            content = f.read()
        return f"File {os.path.basename(expanded)} ({len(content)} chars):\n{content[:2000]}"
    except Exception as e:
        return f"Error reading file: {e}"

# --- SCHEDULED REMINDERS ---
SCHEDULED_REMINDERS = []

def set_scheduled_reminder(time_str, message):
    """Set a reminder at a specific time (e.g., '9:00 AM', '14:30')."""
    try:
        now = datetime.now()
        target = datetime.strptime(time_str.strip(), "%I:%M %p")
        target = target.replace(year=now.year, month=now.month, day=now.day)
        if target <= now:
            target = target.replace(day=now.day + 1)
        delay = (target - now).total_seconds()
        if delay <= 0:
            return "That time has already passed today."
        def _remind():
            time.sleep(delay)
            try:
                import asyncio as _aio
                loop = _aio.new_event_loop()
                _aio.set_event_loop(loop)
                loop.run_until_complete(speak_async_segment(f"Reminder: {message}", None))
                loop.close()
            except Exception:
                pass
            if message in SCHEDULED_REMINDERS:
                SCHEDULED_REMINDERS.remove(message)
        t = threading.Thread(target=_remind, daemon=True)
        t.start()
        SCHEDULED_REMINDERS.append(message)
        return f"Reminder set for {time_str}: \"{message}\""
    except ValueError:
        return "Could not understand the time. Use format like '9:00 AM' or '14:30'."

def list_scheduled_reminders():
    """List all active scheduled reminders."""
    if not SCHEDULED_REMINDERS:
        return "No scheduled reminders."
    return "Active reminders:\n" + "\n".join(f"  - {r}" for r in SCHEDULED_REMINDERS)

# --- APP-SPECIFIC HOTKEYS ---
APP_HOTKEYS = {
    "spotify": {"play_pause": "play/pause media", "next": "next track", "prev": "previous track", "volume_up": "volume up", "volume_down": "volume down"},
    "youtube": {"play_pause": "play/pause media", "next": "next track", "fullscreen": "f"},
    "vlc": {"play_pause": "play/pause media", "next": "next track", "prev": "previous track", "fullscreen": "f"},
    "chrome": {"new_tab": "ctrl+t", "close_tab": "ctrl+w", "reopen_tab": "ctrl+shift+t", "refresh": "f5", "devtools": "f12"},
    "vscode": {"command_palette": "ctrl+shift+p", "quick_open": "ctrl+p", "terminal": "ctrl+`", "save": "ctrl+s"},
}

def handle_media_key(action):
    """Handle media key actions (play/pause, next, prev, volume)."""
    media_map = {
        "play_pause": "playpause",
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack",
        "prev": "prevtrack",
        "volume_up": "volumeup",
        "volume_down": "volumedown",
        "mute": "volumemute",
        "stop": "stop",
    }
    key = media_map.get(action.lower().replace(" ", "_"))
    if key:
        pyautogui.press(key)
        return f"Media action: {action}"
    return f"Unknown media action: {action}. Available: play, pause, next, previous, volume_up, volume_down, mute"

# --- PLUGIN SYSTEM ---
PLUGIN_DIR = "./jarvis_plugins"

def load_plugins():
    """Load all .py plugins from the plugins directory."""
    plugins = {}
    plugin_path = Path(PLUGIN_DIR)
    if not plugin_path.exists():
        plugin_path.mkdir(exist_ok=True)
        return plugins
    for py_file in plugin_path.glob("*.py"):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(py_file.stem, str(py_file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "PLUGIN_NAME") and hasattr(module, "run"):
                plugins[module.PLUGIN_NAME] = module
                print(f"[ PLUGIN ] Loaded: {module.PLUGIN_NAME}")
        except Exception as e:
            print(f"[ PLUGIN ] Failed to load {py_file.name}: {e}")
    return plugins

def run_plugin(plugin_name, args=""):
    """Run a loaded plugin by name."""
    plugins = load_plugins()
    if plugin_name in plugins:
        try:
            result = plugins[plugin_name].run(args)
            return str(result)
        except Exception as e:
            return f"Plugin '{plugin_name}' error: {e}"
    available = ", ".join(plugins.keys()) if plugins else "None installed"
    return f"Plugin '{plugin_name}' not found. Available: {available}"

def list_plugins():
    """List all installed plugins."""
    plugins = load_plugins()
    if not plugins:
        return "No plugins installed. Place .py files in jarvis_plugins/ folder with PLUGIN_NAME and run() function."
    return "Installed plugins:\n" + "\n".join(f"  - {name}" for name in plugins.keys())

# --- SCREENSHOT OCR (text extraction) ---
def extract_text_from_screen():
    """Capture screen and extract text using vision model."""
    image = capture_screen()
    if not image:
        return "Could not capture screen."
    system_prompt = "Extract ALL visible text from this screenshot. Return the text exactly as it appears, preserving layout. No commentary."
    content = [
        {"type": "text", "text": system_prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image}}
    ]
    try:
        for client_type, model_id, name in [
            ("openrouter", "google/gemini-2.5-flash", "Gemini"),
            ("openrouter_backup", "google/gemini-2.5-flash", "Gemini Backup"),
        ]:
            client = openrouter_client if client_type == "openrouter" else openrouter_client_backup
            if client is None:
                continue
            try:
                response = client.chat.completions.create(model=model_id, messages=[{"role": "user", "content": content}], max_tokens=1000)
                return response.choices[0].message.content
            except Exception:
                continue
    except Exception as e:
        return f"OCR extraction failed: {e}"
    return "Could not extract text. No vision models available."

# --- BACKGROUND TASK SYSTEM ---
BACKGROUND_TASKS = {}

def start_background_task(task_name, func, *args):
    """Run a task in the background."""
    def _wrapper():
        try:
            result = func(*args)
            BACKGROUND_TASKS[task_name] = {"status": "completed", "result": str(result)[:200]}
        except Exception as e:
            BACKGROUND_TASKS[task_name] = {"status": "failed", "error": str(e)[:200]}
    thread = threading.Thread(target=_wrapper, daemon=True)
    thread.start()
    BACKGROUND_TASKS[task_name] = {"status": "running", "thread": thread}
    return f"Background task '{task_name}' started."

def get_background_tasks():
    """List all background tasks and their status."""
    if not BACKGROUND_TASKS:
        return "No background tasks."
    lines = []
    for name, info in BACKGROUND_TASKS.items():
        status = info.get("status", "unknown")
        if status == "completed":
            lines.append(f"  [DONE] {name}: {info.get('result', '')[:100]}")
        elif status == "failed":
            lines.append(f"  [FAIL] {name}: {info.get('error', '')[:100]}")
        else:
            lines.append(f"  [RUNNING] {name}")
    return "Background tasks:\n" + "\n".join(lines)

def code_guru_analyze(file_path=None, question=""):
    """Phase 1: Code Guru - Read file directly, analyze with Groq, return fix."""
    if not file_path:
        file_path = get_active_vscode_file()
    if not file_path:
        return None, "Could not detect the active file. Say 'analyze' followed by a file path, or open a file in VS Code first."

    file_content = read_local_file(file_path)
    if file_content.startswith("Error"):
        return None, file_content

    filename = os.path.basename(file_path)
    print(f"[ CODE GURU ] Analyzing {filename} ({len(file_content)} chars)")

    system_prompt = """You are a Senior Software Engineer and Code Guru. Analyze the provided code file and:
1. Identify any bugs, syntax errors, or logic issues
2. Explain each issue clearly
3. Provide the EXACT fixed code for each issue
4. If no bugs found, suggest improvements

Be concise. Use this format:
BUG: [description]
FIX: [exact code to replace]
EXPLANATION: [why this fixes it]"""

    user_content = f"File: {filename}\nPath: {file_path}\n\nCode:\n```\n{file_content[:8000]}\n```\n\nUser question: {question or 'Find and fix any bugs in this code.'}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1500
        )
        analysis = clean_ai_text(response.choices[0].message.content)
        return analysis, file_path
    except Exception as e:
        return None, f"Groq analysis failed: {e}"

def architect_build(prompt):
    """Phase 2: Architect - Hand off to opencode CLI for app generation."""
    opencode_path = shutil.which("opencode")
    if not opencode_path:
        # Try common npm global paths
        npm_paths = [
            os.path.expandvars(r"%APPDATA%\npm\opencode.CMD"),
            os.path.expandvars(r"%APPDATA%\npm\opencode"),
        ]
        for p in npm_paths:
            if os.path.exists(p):
                opencode_path = p
                break

    if not opencode_path:
        return "opencode CLI not found. Install it with: npm install -g opencode"

    print(f"[ ARCHITECT ] Handing off to opencode: {prompt}")
    try:
        # Run opencode in background with the user's prompt
        subprocess.Popen(
            [opencode_path, prompt],
            cwd=str(Path.home() / "Documents"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        return f"Architect engaged. opencode is building: {prompt}. I'll let you know when it's ready."
    except Exception as e:
        return f"Failed to launch Architect: {e}"    
       
def get_location():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=2)
        if res.status_code == 200:
            return res.json().get("city", "New Delhi")
    except:
        pass
    return "New Delhi"

def get_news(topic="technology"):
    if NEWSDATA_API_KEY == "YOUR_NEWSDATA_API_KEY_HERE":
        return "News API identification key token is missing from configuration blocks."
        
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={topic}&language=en"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            articles = res.json().get('results', [])[:3] 
            if not articles:
                return f"No recent news context matrices found referencing provided topic query filter matching: {topic}."
                
            news_str = "LIVE NEWS HEADLINES:\n"
            for a in articles:
                title = a.get('title', 'Unknown Headline Title Context')
                news_str += f"- {title}\n"
            return news_str
        else:
            return f"News aggregation framework returned structural fault error status execution flag code: {res.status_code}."
    except Exception as e:
        return f"News stream interface encountered runtime transmission level fault: {e}"

def get_nasa_data(query_type="apod"):
    try:
        if query_type == "apod":
            url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                return f"NASA Picture of the Day Info: Title: {data.get('title')}. Explanation: {data.get('explanation')}"
    except Exception as e:
        print(f"NASA transaction level monitoring array fault: {e}")
    return "NASA database lookup failed completely during transmission phase execution."

def get_country_info(country_name):
    if REST_COUNTRIES_API_KEY == "YOUR_REST_COUNTRIES_API_KEY_HERE":
        url = f"https://restcountries.com/v3.1/name/{country_name}?fullText=true"
        headers = {}
    else:
        url = f"https://api.restcountries.com/countries/v5/name/{country_name}"
        headers = {"Authorization": f"Bearer {REST_COUNTRIES_API_KEY}"}
        
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()[0]
            capital = data.get('capital', ['N/A'])[0]
            population = data.get('population', 'N/A')
            region = data.get('region', 'N/A')
            return f"REST Countries Profile for {country_name}: Capital: {capital}, Population: {population}, Region: {region}."
    except Exception as e:
        print(f"Demographic processing node error: {e}")
    return f"Could not map country context configuration profile parameters correctly for tracking keyword: {country_name}."

def get_joke():
    try:
        res = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=3)
        if res.status_code == 200:
            data = res.json()
            return f"JOKE: {data['setup']} ... {data['punchline']}"
    except Exception as e:
        print(f"Humor data generation pipeline intercept fault: {e}")
    return "Why did the system throw an error? Because it couldn't connect to the funny database frame server."

def get_rag_context(question):
    headers = {
        "Authorization": f"Bearer {ANYTHING_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "message": question,
        "mode": "query" 
    }
    try:
        response = requests.post(ANYTHING_API_URL, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            text = response.json().get('textResponse', '')
            if text and len(text) > 15 and "sorry" not in text.lower() and "cannot find" not in text.lower():
                return f"LOCAL WORKSPACE DOCUMENTS:\n{text}\n\n"
    except Exception:
        pass
    return ""

def sync_memory_to_anythingllm(user_text, ai_text):
    # Add this line to the top of the function
    global ANYTHING_API_KEY 
    
    headers = {
        "Authorization": f"Bearer {os.getenv('ANYTHING_API_KEY')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    sync_msg = f"LOG ENTRY. User said: '{user_text}'. Jarvis replied: '{ai_text}'. Acknowledge and store."
    data = {
        "message": sync_msg,
        "mode": "chat" 
    }
    try:
        requests.post(ANYTHING_API_URL, headers=headers, json=data, timeout=3)
    except Exception:
        pass

def ask_anythingllm(question):
    headers = {
        "Authorization": f"Bearer {ANYTHING_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "message": question,
        "mode": "chat" 
    }
    try:
        response = requests.post(ANYTHING_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('textResponse', "I'm sorry, my local brain returned an empty response.")
        else:
            return f"Error code structural feedback trace matching index: {response.status_code}"
    except Exception as e:
        return f"Local network array execution processing error trace mapping stack trace log matching: {e}"

def clean_ai_text(text):
    if not text: return "Error generating response processing stream metrics."
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def fast_web_navigator(command):
    """Instantly opens websites or performs web searches using Chrome Browser if available."""
    command = command.lower()
    
    # Define standard Windows paths for Chrome Browser
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if chrome_path:
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        browser = webbrowser.get('chrome')
    else:
        browser = webbrowser
    
    # --- GLOBAL INSTANT WEBSITE INTERCEPTS ---
    if "chatgpt" in command or "chat gpt" in command:
        url = "https://chatgpt.com"
        browser.open_new_tab(url)
        return f"Instantly opened ChatGPT: {url}"
        
    elif "notion" in command and "use my workspace" not in command:
        url = "https://www.notion.so"
        browser.open_new_tab(url)
        return f"Instantly opened Notion Web: {url}"

    elif "instagram" in command:
        target = command.replace("jarvis", "").replace("open", "").replace("instagram", "").strip()
        url = f"https://www.instagram.com/{target.replace(' ', '')}" if target else "https://www.instagram.com"
        browser.open_new_tab(url)
        return f"Instantly opened Instagram: {url}"

    elif "whatsapp" in command:
        browser.open_new_tab("https://web.whatsapp.com")
        return "Instantly opened WhatsApp Web: https://web.whatsapp.com"

    elif "telegram" in command:
        browser.open_new_tab("https://web.telegram.org")
        return "Instantly opened Telegram Web: https://web.telegram.org"

    elif "discord" in command:
        browser.open_new_tab("https://discord.com/app")
        return "Instantly opened Discord: https://discord.com/app"

    elif "spotify" in command:
        browser.open_new_tab("https://open.spotify.com")
        return "Instantly opened Spotify: https://open.spotify.com"

    elif "netflix" in command:
        browser.open_new_tab("https://www.netflix.com")
        return "Instantly opened Netflix: https://www.netflix.com"

    # --- UNIVERSAL DOMAIN INTERCEPTOR ---
    elif any(ext in command for ext in [".com", ".org", ".net", ".in", ".io", ".co"]):
        words = command.split()
        for word in words:
            if "." in word:
                # Clean up the URL and launch
                clean_url = word.replace("jarvis", "").replace("open", "").strip()
                url = f"https://{clean_url}" if not clean_url.startswith("http") else clean_url
                browser.open_new_tab(url)
                return f"Instantly routed to domain: {url}"    

    # 1. Direct site navigation
    elif "youtube" in command and "search" not in command:
        target = command.replace("jarvis", "").replace("open", "").replace("youtube", "").replace("channel", "").strip()
        url = f"https://www.youtube.com/@{target.replace(' ', '')}" if target else "https://www.youtube.com"
        browser.open_new_tab(url)
        return f"Instantly opened YouTube: {url}"
        
    elif "github" in command:
        target = command.replace("jarvis", "").replace("open", "").replace("github", "").strip()
        url = f"https://github.com/{target.replace(' ', '')}" if target else "https://github.com"
        browser.open_new_tab(url)
        return f"Instantly opened GitHub: {url}"
        
    # 2. Instant Google/YouTube Searching
    elif "search" in command:
        query = command.replace("jarvis", "").replace("search", "").replace("for", "").strip()
        if "on youtube" in query or "youtube" in query:
            query = query.replace("on youtube", "").replace("youtube", "").strip()
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        browser.open_new_tab(url)
        return f"Instantly searched the web for: {query}"
        
    return None

def fast_math_calculator(command):
    """Safely and instantly evaluates spoken math equations."""
    # Strip out conversational words
    clean_expr = command.lower().replace("jarvis", "").replace("calculate", "").replace("what is", "").replace("x", "*").replace("times", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-").strip()
    
    # Allow only safe math characters
    if re.match(r'^[\d\+\-\*\/\(\)\.\s]+$', clean_expr):
        try:
            result = eval(clean_expr)
            return f"The answer is {result}"
        except Exception:
            return None
    return None

def get_ai_response(question, base64_image=None):
    is_online = check_internet()
    recent_memory = get_recent_memory()
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    q_lower = question.lower()

    # --- NON-AGENTIC KEYWORDS: These NEVER trigger the vision loop ---
    non_agentic = ["weather", "temperature", "rain", "forecast", "news", "headlines",
                   "joke", "laugh", "calculate", "math", "nasa", "country", "brief me",
                   "who", "what is", "score"]
    is_pure_question = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in non_agentic)

    # --- Check if user wants to SEARCH through Google (not open a site) ---
    search_via_google = False
    search_query = None
    for prep in ["through", "via", "on", "using"]:
        pattern = f"{prep} google"
        if pattern in q_lower:
            search_via_google = True
            # Extract the part before "through google" as the search query
            idx = q_lower.find(pattern)
            search_query = question[:idx].strip()
            # Clean up common prefixes
            for cleanup in ["open", "search", "jarvis", "please", "can you"]:
                search_query = search_query.replace(cleanup, "").strip()
            break

    agentic_keywords = ["click", "type", "open", "navigate", "go to", "write", "chrome", "browser", "youtube", "google", "scroll", "link"]
    # Remove "google" from agentic if it's part of "through google" search intent
    effective_agentic = [k for k in agentic_keywords if not (search_via_google and k == "google")]
    is_agentic_task = any(word in q_lower for word in effective_agentic) and not is_pure_question and not search_via_google

    if is_online:
        extra_context = ""

        # --- DAILY EXECUTIVE BRIEFING ---
        if any(w in q_lower for w in ["brief me", "daily briefing", "morning update"]):
            current_loc = get_location()
            weather = ask_serpapi(f"current weather forecast {current_loc} temperature humidity chance of rain")
            news = get_news("technology")
            recent = get_recent_memory()
            today = datetime.now().strftime("%A, %B %d, %Y")
            extra_context = f"""DAILY BRIEFING DATA for {today}:
WEATHER: {weather}
TOP NEWS: {recent}
RECENT CONVERSATIONS & TASKS:
{recent}
Generate a concise executive morning briefing. Cover: 1) Weather summary 2) Top 3 news headlines 3) Any pending tasks or reminders from recent conversations. Be direct and professional. No markdown."""
            is_agentic_task = False
            use_agent_loop = False

        # --- WEATHER: Always answer directly, NEVER open Chrome ---
        elif any(w in q_lower for w in ["weather", "temperature", "rain", "forecast"]):
            extracted_city = None
            words = question.strip().split()
            if "at" in words: extracted_city = words[words.index("at") + 1]
            elif "in" in words: extracted_city = words[words.index("in") + 1]
            city = extracted_city if extracted_city else get_location()
            hour = datetime.now().hour
            if hour < 6: time_of_day = "night"
            elif hour < 12: time_of_day = "morning"
            elif hour < 17: time_of_day = "afternoon"
            elif hour < 20: time_of_day = "evening"
            else: time_of_day = "night"
            weather_data = ask_serpapi(f"current weather in {city} right now {time_of_day} temperature feels like humidity wind chance of rain")
            extra_context += f"LIVE WEATHER DATA FOR {city} (current {time_of_day}):\n{weather_data}\n\n"
            use_agent_loop = False
            is_agentic_task = False

        # --- SEARCH THROUGH GOOGLE (e.g., "open instagram through google") ---
        elif search_via_google and search_query:
            print(f"[ FAST LANE ] Search-through-Google detected: {search_query}")
            url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            chrome_paths = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
            browser_obj = webbrowser
            for cp in chrome_paths:
                if os.path.exists(cp):
                    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(cp))
                    browser_obj = webbrowser.get('chrome')
                    break
            browser_obj.open_new_tab(url)
            return f"Instantly searched Google for: {search_query}"

        if "access" in q_lower:
            extra_context += get_embedded_rag_context(question)

        search_triggers = ["search", "who", "what is", "latest", "current", "fifa", "score"]
        if any(word in q_lower for word in search_triggers) and not is_agentic_task:
            extra_context += ask_serpapi(question) + "\n\n"

        if any(w in q_lower for w in ["news", "headlines", "update me on"]) and "access" not in q_lower:
            topic = "technology"
            words = q_lower.split()
            if "on" in words:
                try: topic = words[words.index("on") + 1]
                except: pass
            extra_context += get_news(topic) + "\n\n"

        if "nasa" in q_lower: extra_context += get_nasa_data("apod") + "\n\n"
        if "country profile" in q_lower:
            words = q_lower.split()
            extra_context += get_country_info(words[-1]) + "\n\n"
        if any(w in q_lower for w in ["joke", "laugh"]):
            extra_context += get_joke() + "\n\n"

        if "use my workspace" in q_lower or "notion" in q_lower:
            extra_context += query_notion_notebook(question) + "\n\n"

        # --- CODE GURU: Read file directly, analyze, return fix ---
        if any(w in q_lower for w in ["review my code", "debug this", "analyze this", "fix my code", "check my code", "what's wrong with", "find bug"]):
            # Try to extract a file path from the command
            file_path = None
            for word in question.split():
                if os.path.exists(word):
                    file_path = word
                    break
                if word.endswith(('.py', '.js', '.ts', '.html', '.css', '.json')):
                    # Try common locations
                    for base in [Path.home() / "Documents", Path.home() / "Desktop", Path.home() / "Projects"]:
                        candidate = base / word
                        if candidate.exists():
                            file_path = str(candidate)
                            break
            analysis, result_path = code_guru_analyze(file_path, question)
            if analysis:
                return analysis
            else:
                return result_path  # Error message

        # --- ARCHITECT: Hand off to opencode for app generation ---
        if any(w in q_lower for w in ["code an app", "build me", "create a project", "make me a", "generate a", "write me a", "code me a", "build a"]):
            if any(w in q_lower for w in ["app", "project", "website", "page", "tool", "script", "program", "bot", "api", "frontend", "backend", "full stack"]):
                # Extract the build prompt (everything after the trigger phrase)
                build_prompt = question
                for trigger in ["code an app", "build me", "create a project", "make me a", "generate a", "write me a", "code me a", "build a"]:
                    if trigger in q_lower:
                        idx = q_lower.find(trigger)
                        build_prompt = question[idx + len(trigger):].strip()
                        break
                if build_prompt:
                    result = architect_build(build_prompt)
                    return result

        # --- REMEMBER / SAVE NOTE ---
        if any(w in q_lower for w in ["remember this", "save note", "take a note", "note down", "make a note"]):
            note_text = question
            for cleanup in ["remember this", "save note", "take a note", "note down", "make a note", "jarvis", "please"]:
                note_text = note_text.replace(cleanup, "").strip()
            if note_text:
                return save_note(note_text)
            return "What should I note down?"

        # --- READ NOTES ---
        if any(w in q_lower for w in ["show notes", "read notes", "my notes", "what did i note"]):
            return get_notes()

        # --- ADD TASK ---
        if any(w in q_lower for w in ["add task", "new task", "todo", "i need to", "i have to"]) or ("remind me to" in q_lower and "remind me at" not in q_lower):
            task_text = question
            for cleanup in ["add task", "new task", "todo", "i need to", "i have to", "remind me to", "jarvis", "please"]:
                task_text = task_text.replace(cleanup, "").strip()
            if task_text:
                return add_task(task_text)
            return "What task should I add?"

        # --- LIST TASKS ---
        if any(w in q_lower for w in ["my tasks", "show tasks", "what do i have", "pending tasks", "list tasks"]):
            return list_tasks()

        # --- COMPLETE TASK ---
        if any(w in q_lower for w in ["done with", "completed", "finished", "cross off", "remove task"]):
            task_text = question
            for cleanup in ["done with", "completed", "finished", "cross off", "remove task", "jarvis", "please", "i'm", "i am"]:
                task_text = task_text.replace(cleanup, "").strip()
            if task_text:
                return complete_task(task_text)
            return "Which task did you complete?"

        # --- TIMER ---
        if "timer" in q_lower or "alarm" in q_lower or "remind me in" in q_lower:
            import re as _re
            match = _re.search(r'(\d+)\s*(min|minute|hour|sec|second)', q_lower)
            if match:
                val = int(match.group(1))
                unit = match.group(2)
                if "hour" in unit:
                    minutes = val * 60
                elif "sec" in unit:
                    minutes = val / 60
                else:
                    minutes = val
                return set_timer(minutes)
            return "How long should I set the timer for? Say something like 'timer 5 minutes'."

        # --- TIME / DATE ---
        if any(w in q_lower for w in ["what time", "current time", "what's the time", "tell me the time", "what is the time"]):
            return f"It's {datetime.now().strftime('%I:%M %p')} right now."

        if any(w in q_lower for w in ["what date", "what day", "today's date", "what's the date", "what is the date"]):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

        # --- HELP / CAPABILITIES ---
        if any(w in q_lower for w in ["what can you do", "your capabilities", "help me", "what are your features", "how can you help"]):
            return (
                "Here's what I can do:\n\n"
                "VOICE & CHAT: Talk to me naturally. I understand commands and questions.\n\n"
                "WEB: Open any website - say 'open YouTube', 'open Instagram', 'open GitHub'. "
                "Search Google - say 'search through Google for X'.\n\n"
                "VISION & CONTROL: I can see your screen and click, type, scroll, navigate. "
                "Say 'click the 2nd video', 'scroll down', 'type hello in the chat'.\n\n"
                "WEATHER & NEWS: Say 'weather in Delhi' or 'news headlines'. "
                "Say 'brief me' for a full morning briefing.\n\n"
                "MATH: Say 'calculate 15 times 3 plus 2'.\n\n"
                "CODE: Say 'analyze this code' or 'debug my code' to review files. "
                "Say 'build me a weather app' to generate projects with opencode.\n\n"
                "NOTES & TASKS: Say 'remember this X' to save notes. "
                "Say 'add task X' to manage your to-do list.\n\n"
                "TIMER: Say 'timer 5 minutes' and I'll alert you when it's done.\n\n"
                "SCHEDULED REMINDERS: Say 'remind me at 9 AM to check emails'.\n\n"
                "CLIPBOARD: Say 'what's in my clipboard' or 'copy X to clipboard'.\n\n"
                "FILE OPERATIONS: Say 'create a file called main.py' or 'write hello to notes.txt'.\n\n"
                "MEDIA CONTROL: Say 'play', 'pause', 'next song', 'previous song', 'mute'.\n\n"
                "SCREEN OCR: Say 'extract text from screen' to read all text on screen.\n\n"
                "PLUGINS: Say 'list plugins' to see installed plugins.\n\n"
                "BACKGROUND TASKS: Say 'run task in background' for parallel execution.\n\n"
                "FUN: Ask for jokes, NASA picture of the day, or country profiles.\n\n"
                "Say 'Alt+Space' to wake me up anytime."
            )

        # --- CLIPBOARD ---
        if any(w in q_lower for w in ["clipboard", "what's in my clipboard", "what is in my clipboard", "read clipboard", "paste clipboard"]):
            if any(w in q_lower for w in ["set", "copy", "put", "write"]):
                clip_text = question
                for cleanup in ["copy", "set", "put", "write", "to clipboard", "into clipboard", "jarvis", "please"]:
                    clip_text = clip_text.replace(cleanup, "").strip()
                if clip_text:
                    return set_clipboard(clip_text)
                return "What should I copy to clipboard?"
            return get_clipboard()

        # --- FILE OPERATIONS ---
        if any(w in q_lower for w in ["create a file", "create file", "new file", "make a file", "write to file", "write in file", "save to file", "read file"]):
            if "read file" in q_lower:
                file_path = question
                for cleanup in ["read file", "read", "open", "jarvis", "please", "the"]:
                    file_path = file_path.replace(cleanup, "").strip()
                if file_path:
                    return read_file_content(file_path)
                return "Which file should I read?"
            file_path = None
            content = None
            for prefix in ["create a file called", "create file", "new file called", "make a file called", "create"]:
                if prefix in q_lower:
                    idx = q_lower.find(prefix)
                    rest = question[idx + len(prefix):].strip()
                    parts = rest.split(" with ", 1)
                    if len(parts) == 2:
                        file_path = parts[0].strip().strip('"').strip("'")
                        content = parts[1].strip()
                    else:
                        file_path = rest.strip().strip('"').strip("'")
                    break
            if "write" in q_lower and ("to file" in q_lower or "in file" in q_lower or "save" in q_lower):
                for prefix in ["write", "save"]:
                    if prefix in q_lower:
                        idx = q_lower.find(prefix)
                        rest = question[idx + len(prefix):].strip()
                        parts = rest.split(" to ", 1) if " to " in rest else rest.split(" in ", 1)
                        if len(parts) == 2:
                            content = parts[0].strip().strip('"').strip("'")
                            file_path = parts[1].strip().strip('"').strip("'")
                        break
            if file_path:
                if content:
                    return create_file(file_path, content)
                return create_file(file_path)
            return "What should I name the file? Say 'create a file called main.py with hello world'"

        # --- SCHEDULED REMINDERS ---
        if any(w in q_lower for w in ["remind me at", "set reminder", "schedule reminder", "reminder at"]):
            if "list" in q_lower or "show" in q_lower:
                return list_scheduled_reminders()
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', question)
            if time_match:
                time_str = time_match.group(1)
                msg = question[time_match.end():].strip()
                for cleanup in ["to", "about", "that", "jarvis", "please"]:
                    msg = msg.replace(cleanup, "").strip()
                if msg:
                    return set_scheduled_reminder(time_str, msg)
                return "What should I remind you about?"
            return "What time? Say 'remind me at 9:00 AM to check emails'"

        # --- MEDIA / APP HOTKEYS ---
        if any(w in q_lower for w in ["next song", "next track", "previous song", "previous track", "mute", "unmute", "volume up", "volume down"]):
            if any(w in q_lower for w in ["next song", "next track"]):
                return handle_media_key("next")
            elif any(w in q_lower for w in ["previous song", "previous track"]):
                return handle_media_key("previous")
            elif "mute" in q_lower or "unmute" in q_lower:
                return handle_media_key("mute")
            elif "volume up" in q_lower:
                return handle_media_key("volume_up")
            elif "volume down" in q_lower:
                return handle_media_key("volume_down")
        if q_lower.strip() in ["play", "pause", "resume"]:
            return handle_media_key("play_pause")

        # --- SCREEN OCR ---
        if any(w in q_lower for w in ["extract text from screen", "read screen text", "ocr screen", "what text is on screen", "read text on screen"]):
            return extract_text_from_screen()

        # --- PLUGINS ---
        if any(w in q_lower for w in ["list plugins", "show plugins", "what plugins", "available plugins"]):
            return list_plugins()
        if "run plugin" in q_lower or "use plugin" in q_lower:
            plugin_name = question
            for cleanup in ["run plugin", "use plugin", "run", "use", "jarvis", "please"]:
                plugin_name = plugin_name.replace(cleanup, "").strip()
            if plugin_name:
                return run_plugin(plugin_name, question)
            return "Which plugin should I run?"

        # --- BACKGROUND TASKS ---
        if any(w in q_lower for w in ["background tasks", "show tasks running", "what's running", "list background"]):
            return get_background_tasks()

        coding_triggers = ["code", "analyze", "script", "complex", "debug", "write program", "vscode", "notepad"]
        vision_triggers = ["what's on screen", "what is on screen", "describe the screen", "what do you see", "what can you see", "look at my screen", "tell me about the video", "tell me about the screen"]
        use_agent_loop = is_agentic_task or any(w in q_lower for w in coding_triggers) or any(w in q_lower for w in vision_triggers)

        # --- FAST LANE: MATH ---
        if any(w in q_lower for w in ["calculate", "+", "-", "*", "/"]) or ("what is" in q_lower and re.search(r'\d', q_lower)):
            math_result = fast_math_calculator(question)
            if math_result:
                save_to_memory(question, math_result)
                return math_result

        # --- FAST LANE: WEB NAVIGATION (only for simple "open site" commands) ---
        simple_sites = ["youtube", "google", "github", "instagram", "chatgpt", "chat gpt", "whatsapp", "telegram", "discord", "spotify", "netflix"]
        has_site = any(site in q_lower for site in simple_sites)
        has_domain = any(ext in q_lower for ext in [".com", ".org", ".net", ".in", ".io", ".co"])
        is_search_cmd = "search" in q_lower and (has_site or has_domain)
        if any(w in q_lower for w in ["open", "search"]) and (has_site or has_domain):
            words_after_site = q_lower
            for site in simple_sites:
                words_after_site = words_after_site.replace(site, "")
            words_after_site = words_after_site.replace("open", "").replace("search", "").replace("jarvis", "").strip()
            is_simple_open = has_domain or is_search_cmd or (has_site and len(words_after_site.split()) <= 2)
            if is_simple_open:
                web_result = fast_web_navigator(question)
                if web_result:
                    save_to_memory(question, web_result)
                    return web_result

        # --- FAST LANE: YOUTUBE VIDEO SEARCH ---
        if "video" in q_lower and any(w in q_lower for w in ["open", "play", "watch", "show"]):
            query = q_lower
            for cleanup in ["jarvis", "open", "play", "watch", "show", "the", "latest", "a", "an", "video", "on youtube"]:
                query = query.replace(cleanup, " ")
            query = " ".join(query.split()).strip()
            if query:
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                try:
                    chrome_paths_yt = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
                    browser_yt = webbrowser
                    for cp in chrome_paths_yt:
                        if os.path.exists(cp):
                            webbrowser.register('chrome_yt', None, webbrowser.BackgroundBrowser(cp))
                            browser_yt = webbrowser.get('chrome_yt')
                            break
                    browser_yt.open_new_tab(url)
                except Exception:
                    webbrowser.open_new_tab(url)
                return f"Instantly searched YouTube for: {query}"

        # --- SLOW VISION LOOP ---
        if use_agent_loop:
            print("[ SYSTEM: ONLINE ] Routing to Universal Action Model Loop...")
            active_image = base64_image if base64_image else capture_screen()
            ai_text = execute_hybrid_action(question, active_image)
            save_to_memory(question, ai_text)
            return ai_text

        elif groq_client is not None or groq_client_backup is not None:
            selected_model = "llama-3.3-70b-versatile"
            user_content = "Memory:\n" + recent_memory + "\n\n" + extra_context + "User Command: " + question
            system_prompt = "You are Jarvis, a highly capable AI assistant. Date: " + current_time + ". IMPORTANT: If CONTEXT or LIVE WEB SEARCH RESULTS are provided, you MUST use them to answer. Do not tell the user to check a website. Extract the exact answer from the context. Be concise and direct. Do not use asterisks or markdown formatting in your response."
            ai_text = None

            for fallback_client in [groq_client, groq_client_backup, openrouter_client, openrouter_client_backup]:
                if fallback_client is None:
                    continue
                try:
                    response = fallback_client.chat.completions.create(model=selected_model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}], max_tokens=300)
                    ai_text = clean_ai_text(response.choices[0].message.content)
                    break
                except Exception as e:
                    print("[ API FALLBACK ] " + str(e)[:100] + " - trying next...")
                    continue

            if ai_text is None:
                ai_text = "I'm sorry, all my API connections failed. Please check your API keys and internet connection."
        else:
            ai_text = "Error: No API keys configured."
    else:
        ai_text = ask_anythingllm(question)

    save_to_memory(question, ai_text)
    threading.Thread(target=sync_memory_to_anythingllm, args=(question, ai_text), daemon=True).start()
    return ai_text

def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return "#%02x%02x%02x" % (r, g, b)


def hex_to_rgb(hex_color):
    return (int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16))


def rgb_to_hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))


STATE_PALETTES = {
    "idle":      {"primary": "#1565C0", "secondary": "#0D47A1", "core": "#82B1FF", "accent": "#002171", "outer": "#B71C1C", "speed": 0.3, "amp": 2},
    "listening": {"primary": "#1565C0", "secondary": "#0D47A1", "core": "#82B1FF", "accent": "#002171", "outer": "#D32F2F", "speed": 1.8, "amp": 18},
    "thinking":  {"primary": "#FFD600", "secondary": "#F57F17", "core": "#FFFFFF", "accent": "#3E2700", "outer": "#FF6F00", "speed": 4.0, "amp": 6},
    "speaking":  {"primary": "#E65100", "secondary": "#BF360C", "core": "#FFAB91", "accent": "#3E0000", "outer": "#FF1744", "speed": 1.2, "amp": 30},
    "done":      {"primary": "#2E7D32", "secondary": "#1B5E20", "core": "#FFD600", "accent": "#003300", "outer": "#00E676", "speed": 0.5, "amp": 4},
}


class JarvisHUD:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = 480
        win_h = 360
        pos_x = (screen_w - win_w) // 2
        pos_y = 10
        self.root.geometry(str(win_w) + "x" + str(win_h) + "+" + str(pos_x) + "+" + str(pos_y))
        self.root.configure(bg='black')
        self.root.wm_attributes("-transparentcolor", "black")

        self.canvas = tk.Canvas(root, width=220, height=260, bg='black', highlightthickness=0)
        self.canvas.pack()

        self.title_label = tk.Label(root, text="J.A.R.V.I.S.", font=("Segoe UI", 12, "bold"),
                                     fg="#1565C0", bg="black", justify="center")
        self.title_label.pack(pady=(6, 0))

        self.status_label = tk.Label(root, text="J.A.R.V.I.S. // STANDBY",
                                      font=("Consolas", 9), fg="#1565C0", bg="black",
                                      justify="center", wraplength=460)
        self.status_label.pack(pady=(0, 2))

        self.subtitle_label = tk.Label(root, text="", font=("Segoe UI", 11),
                                        fg="#FFFFFF", bg="black", justify="center", wraplength=460)
        self.subtitle_label.pack(pady=(4, 10), side=tk.BOTTOM)

        self.num_bars = 60
        self.bar_heights = [2] * self.num_bars
        self.bar_targets = [2] * self.num_bars
        self.rotation_angle = 0
        self.wave_offset = 0

        self.particles = []
        for _ in range(18):
            angle = random.uniform(0, 360)
            radius = random.uniform(35, 85)
            speed = random.uniform(0.15, 0.5)
            size = random.uniform(0.8, 2.2)
            self.particles.append([angle, radius, speed, size])

        self.pulse_waves = []

        self.current_state = "idle"
        self.mode = "hidden"

        palette = STATE_PALETTES["idle"]
        self.cur_colors = {k: hex_to_rgb(palette[k]) for k in ("primary", "secondary", "core", "accent", "outer")}
        self.tgt_colors = dict(self.cur_colors)
        self.cur_speed = palette["speed"]
        self.tgt_speed = palette["speed"]
        self.cur_amp = palette["amp"]
        self.tgt_amp = palette["amp"]
        self.last_frame_time = time.time()

        self.mic_lock = threading.Lock()
        self.stop_playback = threading.Event()
        self.current_screen = None

        self.update_wave()
        keyboard.add_hotkey('alt+space', self.trigger_wake)
        keyboard.add_hotkey('alt+s', self.force_stop)
        keyboard.add_hotkey('alt+q', lambda: os._exit(0))

        self.root.withdraw()

        threading.Thread(target=self.start_amplitude_listener, daemon=True).start()
        threading.Thread(target=self.continuous_listen_loop, daemon=True).start()
        print("Jarvis is running silently in the background. Say 'Hey Jarvis' to wake.")

    def start_amplitude_listener(self):
        global CURRENT_AUDIO_AMPLITUDE
        def audio_callback(indata, frames, time, status):
            global CURRENT_AUDIO_AMPLITUDE
            if self.current_state == "speaking":
                volume_norm = np.linalg.norm(indata) * 10
                CURRENT_AUDIO_AMPLITUDE = min(volume_norm, 40.0)
            else:
                CURRENT_AUDIO_AMPLITUDE = 0.0

        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000):
                while True:
                    time.sleep(0.1)
        except Exception as e:
            print("[ SYSTEM ] Audio monitoring stream failed to initialize: " + str(e))

    def update_subtitle(self, text):
        if text:
            self.subtitle_label.config(text=text)
        else:
            self.subtitle_label.config(text="")

    def update_status(self, state, text, color):
        self.current_state = state
        self.status_label.config(text=text, fg=color)
        palette = STATE_PALETTES.get(state, STATE_PALETTES["idle"])
        self.tgt_colors = {k: hex_to_rgb(palette[k]) for k in ("primary", "secondary", "core", "accent", "outer")}
        self.tgt_speed = palette["speed"]
        self.tgt_amp = palette["amp"]
        state_colors = {
            "idle": "#1565C0",
            "listening": "#1565C0",
            "thinking": "#F57F17",
            "speaking": "#E65100",
            "done": "#2E7D32"
        }
        self.title_label.config(fg=state_colors.get(state, "#1565C0"))

    def trigger_wake(self):
        if self.mode == "hidden":
            self.mode = "active"
            self.root.deiconify()
            self.update_status("listening", "AWAITING COMMAND", "#1565C0")
            self.root.after(0, lambda: self.update_subtitle("Say your command..."))
            self.current_screen = capture_screen()
            print("[ SYSTEM ] Screen captured. Vision ready.")

    def trigger_sleep(self):
        self.mode = "hidden"
        self.current_screen = None
        self.root.withdraw()

    def force_stop(self):
        print("[ SYSTEM ] Emergency stop triggered.")
        self.stop_playback.set()

    def safe_listen(self, recognizer, timeout, phrase_time_limit):
        try:
            with self.mic_lock:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    recognizer.pause_threshold = 4.0
                    audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=25)
            return recognizer.recognize_google(audio).lower()
        except:
            return None

    def continuous_listen_loop(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        self.is_processing = False
        self.last_command_time = 0

        def callback(recognizer, audio):
            if self.mode == "hidden" or self.is_processing:
                return

            try:
                self.root.after(0, lambda: self.update_subtitle("Listening..."))
                text = recognizer.recognize_google(audio).lower()
                self.root.after(0, lambda: self.update_subtitle(text))

                if any(w in text for w in ["close", "done", "hide", "sleep"]):
                    self.root.after(0, self.trigger_sleep)
                else:
                    self.is_processing = True
                    self.root.after(0, lambda: self.update_status("listening", "WAITING...", "#1565C0"))
                    self.root.after(0, lambda: self.update_subtitle('"' + text + '" — executing in 3s...'))
                    # Wait 3 seconds before executing to confirm no more speech
                    import time
                    time.sleep(3)
                    self.root.after(0, lambda: self.process_command(text))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.update_subtitle("..."))
            except Exception as e:
                pass

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            recognizer.pause_threshold = 3.0

        recognizer.listen_in_background(microphone, callback)
        print("Jarvis is now streaming audio to HUD subtitles (3-Second Silence Delay Active).")

    def process_command(self, text):
        print("[ ROUTING ] Command: " + text)
        self.root.after(0, lambda: self.update_status("thinking", "PROCESSING...", "#FFD600"))
        self.root.after(0, lambda: self.update_subtitle(text))

        non_agentic = ["weather", "temperature", "rain", "forecast", "news", "headlines",
                       "joke", "laugh", "calculate", "math", "nasa", "country", "brief me",
                       "who", "what is", "score", "remember", "note down",
                       "timer", "alarm", "time is", "date", "help me", "capabilities"]
        is_pure_question = any(re.search(r'\b' + re.escape(w) + r'\b', text.lower()) for w in non_agentic)

        agentic_keywords = ["click", "type", "open", "navigate", "go to", "write", "chrome",
                            "browser", "youtube", "google", "scroll", "link", "chat", "message",
                            "dm", "send"]
        is_agentic = any(word in text.lower() for word in agentic_keywords) and not is_pure_question

        try:
            if is_agentic:
                response = get_ai_response(text, self.current_screen)
                is_agent_done = (response.startswith("Task completed:") or
                                 response == "Task manually interrupted by user.")
                is_agent_failed = (response.startswith("Task failed") or
                                   response.startswith("Agent reached") or
                                   response.startswith("Fatal error"))
                is_fast_lane = (response.startswith("Instantly opened") or
                                response.startswith("Instantly searched") or
                                response.startswith("Instantly routed") or
                                response.startswith("AFK Protocol") or
                                response.startswith("The answer is"))

                if is_agent_done:
                    completion_msg = response.replace("Task completed: ", "")
                    self.root.after(0, lambda: self.update_subtitle(completion_msg))
                    self.root.after(0, lambda: self.update_status("done", "TASK COMPLETE", "#2E7D32"))
                    self.speak_and_monitor(completion_msg)
                    self.root.after(0, lambda: self.update_status("idle", "J.A.R.V.I.S. // STANDBY", "#1B5E20"))
                    self.current_screen = capture_screen()
                    self.is_processing = False
                    return

                if is_fast_lane or is_agent_failed:
                    self.root.after(0, lambda: self.update_subtitle(response))
                    self.root.after(0, lambda: self.update_status("done", "DONE", "#2979FF"))
                    self.speak_and_monitor(response)
                    self.root.after(0, lambda: self.update_status("idle", "J.A.R.V.I.S. // STANDBY", "#1B5E20"))
                    self.current_screen = capture_screen()
                    self.is_processing = False
                    return

                self.root.after(0, lambda: self.update_status("speaking", "SPEAKING // SAY STOP", "#FF6D00"))
                self.root.after(0, lambda: self.update_subtitle(response))
                self.speak_and_monitor(response)
                self.root.after(0, lambda: self.update_status("idle", "J.A.R.V.I.S. // STANDBY", "#1B5E20"))
                self.current_screen = capture_screen()
                self.is_processing = False
                return

            response = get_ai_response(text, self.current_screen)
            print("[ ROUTING ] Response: " + str(response)[:120])

            self.root.after(0, lambda: self.update_status("speaking", "SPEAKING // SAY STOP", "#FF6D00"))
            self.root.after(0, lambda: self.update_subtitle(response))
            self.speak_and_monitor(response)
            self.root.after(0, lambda: self.update_status("idle", "J.A.R.V.I.S. // STANDBY", "#1B5E20"))
            self.current_screen = capture_screen()
            self.is_processing = False

        except Exception as e:
            print("[ ROUTING ERROR ] " + str(e))
            self.root.after(0, lambda: self.update_subtitle("Sorry, an error occurred."))
            self.root.after(0, lambda: self.update_status("idle", "J.A.R.V.I.S. // STANDBY", "#1B5E20"))
            self.is_processing = False

    def speak_and_monitor(self, text):
        audio_file = "jarvis_response.mp3"
        clean_text = text.replace('*', '').replace('#', '')

        try:
            async def generate_audio():
                communicate = edge_tts.Communicate(clean_text, "en-GB-ThomasNeural")
                await communicate.save(audio_file)
            asyncio.run(generate_audio())

            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()

            self.stop_playback.clear()
            threading.Thread(target=self.stop_monitor_loop, daemon=True).start()

            while pygame.mixer.music.get_busy():
                if self.stop_playback.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)

            self.stop_playback.set()
            pygame.mixer.music.unload()
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            print("Voice Error: " + str(e))

    def stop_monitor_loop(self):
        recognizer = sr.Recognizer()
        stop_words = ["stop", "quiet", "cancel", "shut up"]
        while not self.stop_playback.is_set() and pygame.mixer.music.get_busy():
            text = self.safe_listen(recognizer, timeout=1, phrase_time_limit=1.5)
            if text and any(w in text for w in stop_words):
                print("[ SYSTEM ] Playback interrupted by voice command.")
                self.stop_playback.set()
                break

    def update_wave(self):
        if self.mode == "hidden":
            self.root.after(100, self.update_wave)
            return

        now = time.time()
        dt = min(now - self.last_frame_time, 0.05)
        self.last_frame_time = now

        lerp_rate = 1.0 - math.pow(0.001, dt)
        for k in ("primary", "secondary", "core", "accent", "outer"):
            cr, cg, cb = self.cur_colors[k]
            tr, tg, tb = self.tgt_colors[k]
            self.cur_colors[k] = (cr + (tr - cr) * lerp_rate, cg + (tg - cg) * lerp_rate, cb + (tb - cb) * lerp_rate)
        self.cur_speed += (self.tgt_speed - self.cur_speed) * lerp_rate
        self.cur_amp += (self.tgt_amp - self.cur_amp) * lerp_rate

        primary = rgb_to_hex(*self.cur_colors["primary"])
        secondary = rgb_to_hex(*self.cur_colors["secondary"])
        core = rgb_to_hex(*self.cur_colors["core"])
        accent = rgb_to_hex(*self.cur_colors["accent"])
        outer = rgb_to_hex(*self.cur_colors["outer"])
        speed = self.cur_speed
        amp = self.cur_amp

        self.canvas.delete("wave")

        width = 220
        height = 260
        center_x = width / 2
        center_y = 115

        # LAYER 0: Outer tick marks (clock face)
        tick_r_outer = 98
        tick_r_inner = 92
        for i in range(60):
            a = (i / 60) * 360 + self.rotation_angle * 0.1
            rad = math.radians(a)
            is_major = (i % 5 == 0)
            r_in = tick_r_inner if is_major else tick_r_inner + 2
            r_out = tick_r_outer if is_major else tick_r_outer - 3
            x1 = center_x + math.cos(rad) * r_in
            y1 = center_y + math.sin(rad) * r_in
            x2 = center_x + math.cos(rad) * r_out
            y2 = center_y + math.sin(rad) * r_out
            w = 2 if is_major else 1
            self.canvas.create_line(x1, y1, x2, y2, fill=outer if is_major else accent, width=w, tags="wave")

        # LAYER 1: Outer ring - dashed circle, rotating slowly
        outer_r = 85
        num_outer = 36
        for i in range(num_outer):
            if i % 2 == 0:
                continue
            a1 = (i / num_outer) * 360 + self.rotation_angle * 0.3
            a2 = a1 + (360 / num_outer) * 0.5
            rad1 = math.radians(a1)
            rad2 = math.radians(a2)
            x1 = center_x + math.cos(rad1) * outer_r
            y1 = center_y + math.sin(rad1) * outer_r
            x2 = center_x + math.cos(rad2) * outer_r
            y2 = center_y + math.sin(rad2) * outer_r
            self.canvas.create_line(x1, y1, x2, y2, fill=outer, width=1, tags="wave")

        # LAYER 2: Middle ring - 12 segments, counter-rotating
        mid_r = 68
        num_segments = 12
        for i in range(num_segments):
            a1 = (i / num_segments) * 360 - self.rotation_angle * 0.6
            a2 = a1 + (360 / num_segments) * 0.55
            rad1 = math.radians(a1)
            rad2 = math.radians(a2)
            x1 = center_x + math.cos(rad1) * mid_r
            y1 = center_y + math.sin(rad1) * mid_r
            x2 = center_x + math.cos(rad2) * mid_r
            y2 = center_y + math.sin(rad2) * mid_r
            self.canvas.create_line(x1, y1, x2, y2, fill=secondary, width=2, tags="wave")

        # LAYER 3: Inner ring - rotating thin circle
        inner_r = 52
        a_start = self.rotation_angle * 0.15
        self.canvas.create_arc(center_x - inner_r, center_y - inner_r,
                               center_x + inner_r, center_y + inner_r,
                               start=a_start, extent=180, outline=secondary, width=1, style="arc", tags="wave")
        self.canvas.create_arc(center_x - inner_r, center_y - inner_r,
                               center_x + inner_r, center_y + inner_r,
                               start=a_start + 180, extent=180, outline=accent, width=1, style="arc", tags="wave")

        # LAYER 4: Decorative data ring (static thin circle)
        data_r = 78
        self.canvas.create_oval(center_x - data_r, center_y - data_r,
                                center_x + data_r, center_y + data_r,
                                outline=accent, width=1, dash=(2, 4), tags="wave")

        # LAYER 5: 12 spoke lines from center outward
        spoke_inner = 22
        spoke_outer = 50
        for i in range(12):
            spoke_angle = math.radians(self.rotation_angle + i * 30)
            sx1 = center_x + math.cos(spoke_angle) * spoke_inner
            sy1 = center_y + math.sin(spoke_angle) * spoke_inner
            sx2 = center_x + math.cos(spoke_angle) * spoke_outer
            sy2 = center_y + math.sin(spoke_angle) * spoke_outer
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill=accent, width=1, tags="wave")

        # LAYER 6: 60 audio-reactive bars around the core
        base_radius = 28
        for i in range(self.num_bars):
            angle = (i / self.num_bars) * 360
            rad = math.radians(angle)

            if self.current_state in ["listening", "speaking"]:
                bar_offset = math.sin(self.wave_offset * 3 + i * 0.5) * 0.3 + 0.7
                self.bar_targets[i] = 2 + CURRENT_AUDIO_AMPLITUDE * bar_offset * (amp / 40.0)
            else:
                self.bar_targets[i] = 2 + math.sin(self.wave_offset + i * 0.4) * amp

            self.bar_heights[i] += (self.bar_targets[i] - self.bar_heights[i]) * 0.35
            h = self.bar_heights[i]

            x_inner = center_x + math.cos(rad) * base_radius
            y_inner = center_y + math.sin(rad) * base_radius
            x_outer = center_x + math.cos(rad) * (base_radius + h)
            y_outer = center_y + math.sin(rad) * (base_radius + h)

            self.canvas.create_line(x_inner, y_inner, x_outer, y_outer, fill=primary, width=1, tags="wave")

        # LAYER 7: 18 floating particles
        for p in self.particles:
            p[0] += p[2] * speed * 0.3
            if p[0] > 360:
                p[0] -= 360
            px = center_x + math.cos(math.radians(p[0])) * p[1]
            py = center_y + math.sin(math.radians(p[0])) * p[1]
            flicker = 0.5 + math.sin(self.wave_offset * 3 + p[0]) * 0.5
            ps = p[3] * flicker
            self.canvas.create_oval(px - ps, py - ps, px + ps, py + ps,
                                    fill=core, outline="", tags="wave")

        # LAYER 8: Pulse waves (listening, speaking, done)
        if self.current_state in ["listening", "speaking", "done"]:
            if random.random() < 0.08:
                self.pulse_waves.append([0])
        for pw in self.pulse_waves[:]:
            pw[0] += 1.2
            if pw[0] > 95:
                self.pulse_waves.remove(pw)
                continue
            pr = pw[0]
            fade = max(0.0, 1.0 - pr / 95)
            fade_sq = fade * fade
            r = int(self.cur_colors["secondary"][0] * fade_sq + self.cur_colors["accent"][0] * (1 - fade_sq))
            g = int(self.cur_colors["secondary"][1] * fade_sq + self.cur_colors["accent"][1] * (1 - fade_sq))
            b = int(self.cur_colors["secondary"][2] * fade_sq + self.cur_colors["accent"][2] * (1 - fade_sq))
            pw_color = rgb_to_hex(r, g, b)
            self.canvas.create_oval(center_x - pr, center_y - pr, center_x + pr, center_y + pr,
                                    outline=pw_color, width=1, tags="wave")

        # LAYER 9: Arc reactor core - filled circle with glow effect
        core_pulse = 15 + math.sin(self.wave_offset * 2.5) * 3
        if self.current_state in ["listening", "speaking"]:
            core_pulse += CURRENT_AUDIO_AMPLITUDE * 0.15

        # Outer glow layers (more for richer effect)
        for g in range(4):
            gr = core_pulse + 5 + g * 5
            glow_alpha = 0.6 - g * 0.15
            r = int(self.cur_colors["accent"][0] * glow_alpha)
            gc = int(self.cur_colors["accent"][1] * glow_alpha)
            b = int(self.cur_colors["accent"][2] * glow_alpha)
            glow_color = rgb_to_hex(r, gc, b)
            self.canvas.create_oval(center_x - gr, center_y - gr,
                                    center_x + gr, center_y + gr,
                                    outline=glow_color, width=1, tags="wave")

        # Core fill
        self.canvas.create_oval(center_x - core_pulse, center_y - core_pulse,
                                center_x + core_pulse, center_y + core_pulse,
                                fill=accent, outline=secondary, width=2, tags="wave")

        # Bright center dot
        dot_r = 6 + math.sin(self.wave_offset * 3) * 2
        self.canvas.create_oval(center_x - dot_r, center_y - dot_r,
                                center_x + dot_r, center_y + dot_r,
                                fill=core, outline="", tags="wave")

        # Inner bright ring
        self.canvas.create_oval(center_x - core_pulse + 4, center_y - core_pulse + 4,
                                center_x + core_pulse - 4, center_y + core_pulse - 4,
                                outline=core, width=1, tags="wave")

        # LAYER 10: Corner HUD decorations (static frame)
        frame_margin = 8
        frame_len = 18
        # Top-left
        self.canvas.create_line(frame_margin, frame_margin, frame_margin + frame_len, frame_margin, fill=outer, width=1, tags="wave")
        self.canvas.create_line(frame_margin, frame_margin, frame_margin, frame_margin + frame_len, fill=outer, width=1, tags="wave")
        # Top-right
        self.canvas.create_line(width - frame_margin, frame_margin, width - frame_margin - frame_len, frame_margin, fill=outer, width=1, tags="wave")
        self.canvas.create_line(width - frame_margin, frame_margin, width - frame_margin, frame_margin + frame_len, fill=outer, width=1, tags="wave")
        # Bottom-left
        self.canvas.create_line(frame_margin, height - frame_margin - 20, frame_margin + frame_len, height - frame_margin - 20, fill=outer, width=1, tags="wave")
        # Bottom-right
        self.canvas.create_line(width - frame_margin, height - frame_margin - 20, width - frame_margin - frame_len, height - frame_margin - 20, fill=outer, width=1, tags="wave")

        # LAYER 11: Small data readout text
        data_text = "SYS:NOMINAL"
        if self.current_state == "listening":
            data_text = "MIC:ACTIVE"
        elif self.current_state == "thinking":
            data_text = "PROC:BUSY"
        elif self.current_state == "speaking":
            data_text = "TTS:OUTPUT"
        elif self.current_state == "done":
            data_text = "TASK:DONE"
        self.canvas.create_text(width - 12, height - 24, text=data_text, anchor="e",
                                fill=accent, font=("Consolas", 6), tags="wave")

        # LAYER 12: J.A.R.V.I.S. text at center bottom
        self.canvas.create_text(center_x, height - 12, text="J.A.R.V.I.S.", anchor="center",
                                fill=secondary, font=("Consolas", 7, "bold"), tags="wave")

        self.rotation_angle += speed
        self.wave_offset += 0.15

        self.root.after(30, self.update_wave)


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisHUD(root) 
    root.mainloop()