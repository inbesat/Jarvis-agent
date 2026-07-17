# JARVIS — Local-First Agentic AI Desktop Assistant

A voice-controlled AI desktop assistant that sees your screen, controls your mouse/keyboard, answers questions, and maintains chat memory — all through a transparent Iron Man arc-reactor HUD overlay.

---

## Quick Start (5 Minutes)

### Step 1: Install Anaconda or Miniconda

Download and install **Miniconda** (lighter) or **Anaconda** (full):
- Miniconda: https://docs.anaconda.com/miniconda/
- Anaconda: https://www.anaconda.com/download

Verify installation:
```bash
conda --version
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Jarvis.git
cd Jarvis
```

### Step 3: Create the Conda Environment

```bash
conda create -n jarvis-env python=3.14 -y
```

### Step 4: Activate the Environment

```bash
conda activate jarvis-env
```

> **Important:** You must run this command every time you open a new terminal before starting Jarvis.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure API Keys

```bash
copy .env.example .env
```

Open `.env` in any text editor and fill in your API keys. At minimum, you need:

| Key | Where to Get | Free? |
|-----|-------------|-------|
| `GROQ_API_KEY` | https://console.groq.com | Yes |
| `OPENROUTER_API_KEY` | https://openrouter.ai | Yes |

See the [API Keys](#api-keys) section for all available keys and what they do.

### Step 7: Run Jarvis

```bash
python jarvis_ui.py
```

Or use the Windows batch file (auto-activates conda environment):
```
double-click start_jarvis.bat
```

### Step 8: Activate the HUD

- Press **Alt+Space** to show the HUD
- Say a command (e.g., "What's the weather in Delhi?")
- Press **Alt+Q** to quit

---

## Table of Contents

- [Quick Start](#quick-start-5-minutes)
- [What Jarvis Is](#what-jarvis-is)
- [Requirements](#requirements)
- [Installation](#installation-detailed)
- [Running](#running)
- [Architecture](#architecture)
- [Core Systems](#core-systems)
- [Voice Commands](#voice-commands)
- [Agent Loop Actions](#agent-loop-actions)
- [Memory System](#memory-system)
- [Plugin System](#plugin-system)
- [API Keys](#api-keys)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Test Checklist](#test-checklist)
- [File Structure](#file-structure)
- [Known Limitations](#known-limitations)

---

## What Jarvis Is

Jarvis is a **Local-First Agentic AI** desktop assistant built in Python. It combines voice recognition, screen vision, desktop automation, and conversational AI into a single desktop app with an Iron Man-style HUD overlay.

**Core capabilities:**
- **Voice control** — speak commands, Jarvis executes them on your desktop
- **Screen vision** — captures screenshots, reads text, describes what's on screen
- **Desktop control** — opens apps, clicks buttons, types text, scrolls, navigates
- **Conversational AI** — answers questions, searches the web, tells jokes
- **Memory** — remembers notes, tasks, reminders across sessions
- **Code analysis** — reads your code files, finds bugs, suggests fixes
- **Code generation** — launches opencode CLI to build full projects from voice commands

---

## Requirements

- **OS:** Windows 10/11
- **Python:** 3.10+ (developed on 3.14)
- **Conda:** Anaconda or Miniconda (recommended for environment management)
- **Browser:** Google Chrome (forced for all web operations)
- **Audio:** Working microphone and speakers
- **Internet:** Required for voice recognition, TTS, web search, AI models

### Python Dependencies (requirements.txt)

All dependencies are listed in `requirements.txt`:

| Package | Purpose |
|---------|---------|
| `edge-tts` | Microsoft Edge text-to-speech |
| `pygame` | Audio playback for TTS |
| `SpeechRecognition` | Voice recognition (Google) |
| `pyautogui` | Mouse/keyboard automation |
| `pywinauto` | Windows UIA accessibility tree |
| `pyperclip` | Clipboard operations |
| `psutil` | System monitoring (CPU, RAM) |
| `requests` | HTTP requests for APIs |
| `python-dotenv` | Load API keys from .env |
| `groq` | Groq API client (fast inference) |
| `flask` | Memory server (optional) |

Install all at once:
```bash
pip install -r requirements.txt
```

---

## Installation (Detailed)

### Option A: Using Anaconda/Miniconda (Recommended)

This is the recommended method because conda isolates dependencies and avoids conflicts.

**1. Install Miniconda or Anaconda:**
- Miniconda (lightweight, ~80MB): https://docs.anaconda.com/miniconda/
- Anaconda (full suite, ~3GB): https://www.anaconda.com/download

**2. Open Anaconda Prompt** (search "Anaconda Prompt" in Start Menu)

**3. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/Jarvis.git
cd Jarvis
```

**4. Create a conda environment with Python 3.14:**
```bash
conda create -n jarvis-env python=3.14 -y
```

**5. Activate the environment:**
```bash
conda activate jarvis-env
```

> **Important:** You must run `conda activate jarvis-env` every time you open a new terminal before starting Jarvis.

**6. Install all dependencies:**
```bash
pip install -r requirements.txt
```

**7. Configure API keys:**
```bash
copy .env.example .env
```

Open `.env` in a text editor and fill in your API keys. See the [API Keys](#api-keys) section.

**8. Run Jarvis:**
```bash
python jarvis_ui.py
```

### Option B: Using Python Directly (Without Conda)

If you prefer not to use conda:

**1. Install Python 3.10+ from:**
- https://www.python.org/downloads/
- **Check "Add Python to PATH"** during installation

**2. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/Jarvis.git
cd Jarvis
```

**3. (Recommended) Create a virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

**4. Install dependencies:**
```bash
pip install -r requirements.txt
```

**5. Configure API keys:**
```bash
copy .env.example .env
```

Edit `.env` with your API keys. See [API Keys](#api-keys).

**6. Run Jarvis:**
```bash
python jarvis_ui.py
```

### Option C: Using the Windows Batch File (Easiest)

If you already have conda set up, just double-click `start_jarvis.bat`:

```
start_jarvis.bat
```

**What it does:**
1. Checks if conda is installed
2. Activates the `jarvis-env` environment automatically
3. Checks if `.env` exists (creates from template if missing)
4. Checks if Chrome is installed
5. Runs `python jarvis_ui.py`

**If conda is not found:**
- Install Miniconda/Anaconda first
- Then run: `conda create -n jarvis-env python=3.14 -y`
- Then double-click `start_jarvis.bat` again

---

## Running

### Start Jarvis (Main App)

**Method 1: Direct Python**
```bash
conda activate jarvis-env
python jarvis_ui.py
```

**Method 2: Double-click start_jarvis.bat**
- Auto-activates conda environment
- Checks for .env and Chrome
- Runs Jarvis

**Method 3: From any terminal**
```bash
python jarvis_ui.py
```

**What you'll see:**
- HUD appears hidden (green arc reactor in standby)
- Press **Alt+Space** to activate and speak
- Press **Alt+Q** to force quit

### Start Memory Server (Optional)
```bash
python jarvis_memory_server.py
```
- Opens at `http://localhost:5050`
- 5 sections: Chat History, Notes, Future Ideas, Todo List, Tasks
- Jarvis saves conversations and notes here automatically

### Windows Batch File (start_jarvis.bat)

The `start_jarvis.bat` file provides a one-click launcher:

**What it checks:**
1. Is conda installed? → Error if not
2. Can it activate `jarvis-env`? → Error if environment missing
3. Does `.env` exist? → Creates from template if missing
4. Is Chrome installed? → Warning if not found
5. Runs `python jarvis_ui.py`

**If environment is missing:**
```bash
conda create -n jarvis-env python=3.14 -y
conda activate jarvis-env
pip install -r requirements.txt
```

---

## Architecture

```
jarvis_ui.py              Main app (HUD + routing + agent loop + all features)
jarvis_memory_server.py   Flask REST API for memory (port 5050)
jarvis_memory_ui.html     Cyberpunk frontend for memory server
jarvis_tasks.json         Persistent todo list (JSON)
jarvis_chat_log.txt       Flat text chat log + notes
.env                      API keys configuration (DO NOT commit to git)
.env.example              Template for API keys (safe to commit)
requirements.txt          Python dependencies
start_jarvis.bat          Windows one-click launcher
jarvis_plugins/           Plugin directory (.py scripts)
```

---

## Core Systems

### 1. Voice Recognition
- Continuous background listening via Google Speech Recognition
- 3-second silence delay before executing (confirms you're done speaking)
- Wake via **Alt+Space** hotkey
- Sleep/hide via voice ("close", "done", "hide", "sleep")
- Stop TTS via voice ("stop", "quiet", "cancel", "shut up")
- Command blocked while Jarvis is already processing (`is_processing` flag)

### 2. Text-to-Speech
- Microsoft Edge TTS (`en-GB-ThomasNeural` voice)
- pygame audio playback
- Voice interrupt support (say "stop" while speaking)
- Audio-reactive HUD bars during speech

### 3. HUD Display
- Transparent tkinter window, always on top, borderless
- 480x360px centered at top of screen
- 9-layer arc-reactor animation at 30fps
- 5 distinct state colors:
  - **Idle** — Dark green (`#1B5E20`), slow pulse
  - **Listening** — Blue (`#1565C0`), medium animation
  - **Thinking** — Gold (`#FFD600`), fast spin
  - **Speaking** — Orange (`#E65100`), audio-reactive bars
  - **Done** — Green (`#2E7D32`), pulse then back to idle
- Subtitle displays all text (commands + responses)

### 4. Agent Loop (Vision + Desktop Control)
- 25-step autonomous loop
- Captures screen (base64 JPEG) + accessibility tree (Windows UIA)
- Sends to vision models with fallback chain
- Executes actions: open_app, click, type, press_key, hotkey, scroll, click_link, open_url, wait, done
- **Stuck detection:** repeated actions, coordinate loops, scroll limits
- **Repeat prevention:** `opened_apps` set prevents opening same app twice
- **Emergency stop:** **Alt+I** or **Alt+Q**

### 5. API Fallback Chain
- Primary Groq → Backup Groq → Primary OpenRouter → Backup OpenRouter
- 7 models tried for vision: Gemini Flash → Qwen VL → Gemini backup → Qwen backup → Llama text → Groq text → Groq backup
- 4 models tried for text: Groq → Groq backup → OpenRouter → OpenRouter backup

### 6. Memory System
- `jarvis_chat_log.txt` — conversation persistence
- Memory server (`localhost:5050`) — chat history, notes, future ideas, todo list, tasks
- ChromaDB + sentence-transformers — local vector embeddings
- `jarvis_tasks.json` — persistent todo list
- Notes saved to both chat log AND memory server for proactive recall

### 7. Web Integration
- Chrome browser (forced for all web operations)
- SerpAPI — Google search results
- NewsData.io — news headlines
- NASA API — picture of the day
- REST Countries API — country profiles
- Joke API — random jokes

### 8. Code Analysis
- **Code Guru:** Reads files, analyzes with Groq, finds bugs, provides fixes
- **Architect:** Launches opencode CLI to generate full applications
- VS Code integration (detects active file via window title)

### 9. Plugin System
- Drop `.py` files in `jarvis_plugins/` folder
- Plugin needs `PLUGIN_NAME = "name"` and `def run(args)`
- Sample included: `system_info.py` (shows CPU, RAM, disk)

### 10. Background Tasks
- Run functions in daemon threads
- Track status (running/completed/failed)
- Non-blocking parallel execution

---

## Voice Commands

### Agentic Commands (go to agent vision loop)

| Command | What Happens |
|---------|-------------|
| "Open Notepad" | Opens Notepad via Start Menu |
| "Open Notepad and write hello world" | Opens → waits → types → done |
| "Open Chrome and go to YouTube" | Opens Chrome → navigates |
| "Open Instagram and message hi to John" | Opens → finds chat → types → sends |
| "Search YouTube for MrBeast latest video" | Opens YouTube search → clicks first video |
| "Click the sign in button" | Finds button in accessibility tree → clicks |
| "Scroll down" | Scrolls page down |
| "Type hello in the chat" | Clicks focus → types text |
| "What's on my screen" | Captures screenshot → describes what it sees |
| "Describe the screen" | Same — vision description |
| "Open Spotify and play my playlist" | Opens Spotify app |

### Non-Agent Fast Lanes (instant, no vision loop)

| Command | What Happens |
|---------|-------------|
| "What is 2 + 2" | Math calculator → "The answer is 4" |
| "Calculate 15 times 3 plus 2" | Math calculator → "The answer is 47" |
| "Open YouTube" | Opens YouTube in Chrome instantly |
| "Open Instagram" | Opens Instagram in Chrome instantly |
| "Open ChatGPT" | Opens ChatGPT in Chrome instantly |
| "Open GitHub" | Opens GitHub in Chrome instantly |
| "Open WhatsApp" | Opens WhatsApp Web in Chrome instantly |
| "Open Telegram" | Opens Telegram Web in Chrome instantly |
| "Open Discord" | Opens Discord in Chrome instantly |
| "Open Spotify" | Opens Spotify Web in Chrome instantly |
| "Open Netflix" | Opens Netflix in Chrome instantly |
| "Open Notion" | Opens Notion in Chrome instantly |
| "Search YouTube for cats" | YouTube search in Chrome |
| "Open xyz.com" | Opens any domain in Chrome |
| "Open Instagram through Google" | Google search for Instagram |

### Non-Agentic Commands (no vision, direct API)

| Command | What Happens |
|---------|-------------|
| "What's the weather in Delhi" | SerpAPI weather + time-of-day context |
| "Weather at night" | Says "night" not "sunny" |
| "News headlines" | NewsData.io top 3 headlines |
| "News on technology" | Topic-specific news |
| "Brief me" / "Daily briefing" | Full executive briefing (weather + news + tasks) |
| "Tell me a joke" | Random joke from API |
| "Who is Elon Musk" | Web search → speaks answer |
| "What is quantum computing" | Web search → speaks answer |
| "NASA picture of the day" | NASA APOD data |
| "Country profile of Japan" | REST Countries API data |
| "What time is it" | Current time (no API) |
| "What's the date today" | Current date (no API) |

### Notes & Tasks

| Command | What Happens |
|---------|-------------|
| "Remember this buy groceries" | Saves note to chat log + memory server |
| "Save note call mom at 5pm" | Same — saves note |
| "Show notes" / "My notes" | Reads back recent notes |
| "Add task finish homework" | Adds to `jarvis_tasks.json` |
| "I need to buy milk" | Same — adds task |
| "My tasks" / "Show tasks" | Lists pending tasks |
| "Done with homework" / "Finished homework" | Marks task complete |

### Timer & Reminders

| Command | What Happens |
|---------|-------------|
| "Timer 5 minutes" | Background timer → speaks "Time's up!" |
| "Alarm 30 minutes" | Same |
| "Remind me in 2 hours" | Same |
| "Remind me at 9:00 AM to check emails" | Scheduled reminder at exact time |
| "List reminders" | Shows all active scheduled reminders |

### Clipboard

| Command | What Happens |
|---------|-------------|
| "What's in my clipboard" | Reads clipboard via PowerShell |
| "Read clipboard" | Same |
| "Copy hello world to clipboard" | Sets clipboard content |
| "Set clipboard to my email" | Same |

### File Operations

| Command | What Happens |
|---------|-------------|
| "Create a file called main.py with hello world" | Creates file with content |
| "Create file notes.txt" | Creates empty file |
| "Write hello to notes.txt" | Appends content to file |
| "Read file main.py" | Reads and displays file content |

### Media Control

| Command | What Happens |
|---------|-------------|
| "Play" / "Pause" / "Resume" | Toggle media playback |
| "Next song" / "Next track" | Skip to next |
| "Previous song" / "Previous track" | Go back |
| "Mute" / "Unmute" | Toggle mute |
| "Volume up" | Increase volume |
| "Volume down" | Decrease volume |

### Screen OCR

| Command | What Happens |
|---------|-------------|
| "Extract text from screen" | Vision model reads all text from screenshot |
| "Read screen text" | Same |
| "What text is on screen" | Same |

> **Note:** OCR uses the vision model (Gemini Flash) rather than Tesseract because screen UIs have complex backgrounds, icons, and buttons that Tesseract cannot handle well. Vision models understand context and layout.

### Code Analysis

| Command | What Happens |
|---------|-------------|
| "Analyze this code" | Reads VS Code active file → analyzes |
| "Debug my code" | Same |
| "Review my code" | Same |
| "Fix my code" | Same |
| "What's wrong with main.py" | Reads specified file → analyzes |

### Code Generation

| Command | What Happens |
|---------|-------------|
| "Build me a weather app" | Launches opencode CLI → generates full project |
| "Create a project website" | Same |
| "Generate a chatbot" | Same |
| "Code me a calculator" | Same |

### Plugins

| Command | What Happens |
|---------|-------------|
| "List plugins" | Shows installed plugins |
| "Run plugin system_info" | Executes plugin |
| "Use plugin weather" | Same |

### Background Tasks

| Command | What Happens |
|---------|-------------|
| "Show background tasks" | Lists running/completed/failed tasks |

### System

| Command | What Happens |
|---------|-------------|
| "Help me" / "What can you do" | Full capabilities list |
| "Close" / "Hide" / "Sleep" | Hides HUD |

---

## Agent Loop Actions

| Action | Description |
|--------|-------------|
| `open_app` | Start Menu → type name → Enter → wait 3s |
| `click` | pyautogui.click(x,y) or pywinauto click by name |
| `click_link` | Find UI element by text → click it |
| `type` | Click center for focus → pyautogui.write() |
| `press_key` | Single key press |
| `hotkey` | Key combination (e.g., ctrl+l) |
| `scroll` | Scroll by pixel amount |
| `open_url` | Focus Chrome → ctrl+l → type URL → enter |
| `find_text` | ctrl+f → type search text → escape |
| `wait` | Sleep for N seconds |
| `escape` | Press escape key |
| `alt_tab` | Alt+Tab window switch |
| `done` | Return completion message → end loop |
| `fatal_error` | Return failure → end loop |

---

## Memory System

### Memory Server (`jarvis_memory_server.py`)

Flask REST API running on `http://localhost:5050`.

**5 sections with full CRUD:**

| Section | Purpose | Endpoints |
|---------|---------|-----------|
| `chat_history` | All conversations | GET, POST, DELETE |
| `notes` | Saved notes | GET, POST, PUT, DELETE, search |
| `future_ideas` | Ideas to revisit | GET, POST, PUT, DELETE |
| `todo_list` | Pending items | GET, POST, PUT, DELETE |
| `tasks` | Projects with status/priority | GET, POST, PUT, DELETE |

**Additional endpoints:**
- `GET /search?q=query` — search across all sections
- `POST /import-log` — import from `jarvis_chat_log.txt`

### Memory UI (`jarvis_memory_ui.html`)

Cyberpunk-themed frontend:
- Left nav with section tabs + item counts
- Chat bubbles for conversations
- Card layouts for notes and ideas
- Todo checkboxes with priority badges
- Add/edit/delete modals for all sections
- Import button to migrate from txt log

### Storage Layers

| Layer | File/URL | Purpose |
|-------|----------|---------|
| Chat log | `jarvis_chat_log.txt` | Flat text conversation history |
| Tasks | `jarvis_tasks.json` | Persistent JSON todo list |
| Memory server | `localhost:5050` | Structured CRUD storage |
| ChromaDB | `./chroma_db/` | Local vector embeddings |

---

## Plugin System

### Creating a Plugin

Create a `.py` file in `jarvis_plugins/`:

```python
PLUGIN_NAME = "my_plugin"

def run(args):
    # args is a string of additional instructions
    return f"Plugin executed with args: {args}"
```

### Using Plugins

| Command | What Happens |
|---------|-------------|
| "List plugins" | Shows all installed plugins |
| "Run plugin my_plugin" | Executes the plugin |
| "Use plugin my_plugin" | Same |

### Sample Plugin

`system_info.py` — shows CPU, RAM, and disk usage:
```bash
python jarvis_ui.py
# Then say: "Run plugin system_info"
```

---

## API Keys

### Setup

```bash
copy .env.example .env
```

Open `.env` in any text editor and fill in your API keys.

### Required Keys

These are the minimum keys needed for Jarvis to work:

```env
# Groq — Fast AI inference (required)
# Get at: https://console.groq.com
# Free tier: 30 requests/minute
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenRouter — Backup AI inference + vision models (required)
# Get at: https://openrouter.ai
# Free tier: Limited credits
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Optional Keys (Recommended)

These add more features and reliability:

```env
# Backup Groq key — used when primary fails
GROQ_API_KEY_BACKUP=

# Backup OpenRouter key — used when primary fails
OPENROUTER_API_KEY_BACKUP=

# SerpAPI — Google search results (100 free searches/month)
# Get at: https://serpapi.com
SERPAPI_API_KEY=

# NewsData.io — News headlines (200 free credits/day)
# Get at: https://newsdata.io
NEWSDATA_API_KEY=

# OpenWeather — Weather data (1000 free calls/day)
# Get at: https://openweathermap.org
OPENWEATHER_API_KEY=

# NASA — Picture of the day (1000 free requests/hour)
# Get at: https://api.nasa.gov
NASA_API_KEY=DEMO_KEY
```

### Optional Keys (Advanced)

These are for specific integrations:

```env
# REST Countries — Country profiles (unlimited free)
# Get at: https://restcountries.com
REST_COUNTRIES_API_KEY=

# Notion — Save notes to Notion
# Get at: https://notion.so/my-integrations
NOTION_TOKEN=
NOTION_DATABASE_ID=

# AnythingLLM — Local RAG (run at localhost:3001)
ANYTHING_API_KEY=
WORKSPACE_SLUG=jarvis
ANYTHING_API_URL=http://localhost:3001/api/v1/workspace/jarvis/chat

# HuggingFace — Local embeddings
HF_TOKEN=
```

### Where to Get Keys

| Service | URL | Free Tier | What It Does |
|---------|-----|-----------|--------------|
| **Groq** | https://console.groq.com | Yes (30 req/min) | AI inference, chat, code analysis |
| **OpenRouter** | https://openrouter.ai | Yes (limited) | Backup AI + vision models |
| **SerpAPI** | https://serpapi.com | 100 searches/month | Google search results |
| **NewsData** | https://newsdata.io | 200 credits/day | News headlines |
| **OpenWeather** | https://openweathermap.org | 1000 calls/day | Weather data |
| **NASA** | https://api.nasa.gov | 1000 req/hour | Picture of the day |
| **REST Countries** | https://restcountries.com | Unlimited | Country profiles |
| **Notion** | https://notion.so/my-integrations | Yes | Save notes to Notion |

### .env.example Reference

The `.env.example` file contains all possible keys with descriptions. It is safe to commit to git. The actual `.env` file contains your real keys and should **never** be committed (it's in `.gitignore`).

```bash
# View the template
cat .env.example

# Copy to .env
copy .env.example .env

# Edit with your keys
notepad .env
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Alt+Space** | Wake HUD / Activate listening |
| **Alt+S** | Emergency stop TTS |
| **Alt+I** | Emergency stop agent loop |
| **Alt+Q** | Force quit Jarvis |

---

## Test Checklist

### A. HUD & Wake Tests

| # | Test | Expected |
|---|------|----------|
| A1 | Start Jarvis | Window hidden, green arc reactor in standby |
| A2 | Press Alt+Space | HUD appears, shows "AWAITING COMMAND" in blue |
| A3 | Say "close" | HUD disappears |
| A4 | Press Alt+S during TTS | Playback stops immediately |
| A5 | Press Alt+Q | Force quit |
| A6 | State: idle | Green arc reactor, slow pulse |
| A7 | State: listening | Blue arc reactor, medium animation |
| A8 | State: thinking | Gold arc reactor, fast spin |
| A9 | State: speaking | Orange arc reactor, audio-reactive bars |
| A10 | State: done | Green pulse, then back to idle |

### B. Voice Recognition Tests

| # | Test | Expected |
|---|------|----------|
| B1 | Say command, wait 3s silence | Command executes after delay |
| B2 | Say command, keep talking | HUD shows "WAITING..." during 3s delay |
| B3 | Say command while agent running | Command blocked (is_processing) |
| B4 | Say garbage words | Shows "...", no crash |
| B5 | Say "stop" during TTS | Playback interrupted |
| B6 | Say "close" | HUD hides |
| B7 | Say command twice quickly | Second command blocked |

### C. Routing Tests — Non-Agentic

| # | Command | Expected |
|---|---------|----------|
| C1 | "What is the time?" | Speaks time, no agent loop |
| C2 | "What's the date today?" | Speaks date |
| C3 | "What is 2 plus 2?" | "The answer is 4" |
| C4 | "Calculate 15 times 3 plus 2" | "The answer is 47" |
| C5 | "Tell me a joke" | Speaks joke |
| C6 | "Weather in Delhi" | Speaks weather with time-of-day |
| C7 | "Weather at night" | Says "night" not "sunny" |
| C8 | "News headlines" | Speaks top 3 headlines |
| C9 | "News on technology" | Topic-specific news |
| C10 | "Brief me" | Full executive briefing |
| C11 | "Who is Elon Musk?" | Web search answer |
| C12 | "What is Python?" | Web search answer |
| C13 | "NASA picture of the day" | NASA APOD data |
| C14 | "Country profile of Japan" | Country info |
| C15 | "Help me" | Lists all capabilities |

### D. Routing Tests — Web Navigation

| # | Command | Expected |
|---|---------|----------|
| D1 | "Open YouTube" | YouTube in Chrome instantly |
| D2 | "Open Instagram" | Instagram in Chrome |
| D3 | "Open ChatGPT" | ChatGPT in Chrome |
| D4 | "Open GitHub" | GitHub in Chrome |
| D5 | "Open WhatsApp" | WhatsApp Web in Chrome |
| D6 | "Open Telegram" | Telegram Web in Chrome |
| D7 | "Open Discord" | Discord in Chrome |
| D8 | "Open Spotify" | Spotify Web in Chrome |
| D9 | "Open Netflix" | Netflix in Chrome |
| D10 | "Open Notion" | Notion in Chrome |
| D11 | "Open xyz.com" | Opens domain in Chrome |
| D12 | "Search YouTube for cats" | YouTube search in Chrome |
| D13 | "Open Instagram through Google" | Google search |

### E. Routing Tests — Notes & Tasks

| # | Command | Expected |
|---|---------|----------|
| E1 | "Remember this buy milk" | Saves note, speaks confirmation |
| E2 | "Save note call mom" | Saves note |
| E3 | "Show notes" | Reads back recent notes |
| E4 | "Add task finish homework" | Adds task, speaks count |
| E5 | "I need to buy groceries" | Adds task |
| E6 | "My tasks" | Lists pending tasks |
| E7 | "Done with homework" | Marks task complete |
| E8 | "Finished buying milk" | Marks task complete |
| E9 | Notes saved to memory server | Check localhost:5050 → Notes section |

### F. Routing Tests — Timer & Reminders

| # | Command | Expected |
|---|---------|----------|
| F1 | "Timer 5 minutes" | Sets timer, speaks "Time's up!" after |
| F2 | "Alarm 30 minutes" | Same |
| F3 | "Remind me in 2 hours" | Same |
| F4 | "Remind me at 9:00 AM to check emails" | Scheduled at exact time |
| F5 | "List reminders" | Shows active reminders |

### G. Routing Tests — Clipboard & Files

| # | Command | Expected |
|---|---------|----------|
| G1 | "What's in my clipboard" | Reads clipboard content |
| G2 | "Copy hello to clipboard" | Sets clipboard |
| G3 | "Create a file called test.py with print hello" | Creates file with content |
| G4 | "Write data to notes.txt" | Appends to file |
| G5 | "Read file test.py" | Reads and speaks content |

### H. Routing Tests — Media & OCR

| # | Command | Expected |
|---|---------|----------|
| H1 | "Play" | Toggles media play/pause |
| H2 | "Pause" | Same |
| H3 | "Next song" | Skips track |
| H4 | "Previous song" | Goes back |
| H5 | "Mute" | Toggles mute |
| H6 | "Volume up" | Increases volume |
| H7 | "Volume down" | Decreases volume |
| H8 | "Extract text from screen" | Vision model reads all text |
| H9 | "Read screen text" | Same |

### I. Routing Tests — Code & Plugins

| # | Command | Expected |
|---|---------|----------|
| I1 | "Analyze this code" | Reads VS Code file → speaks analysis |
| I2 | "Debug my code" | Same |
| I3 | "Build me a weather app" | Launches opencode CLI |
| I4 | "List plugins" | Shows installed plugins |
| I5 | "Run plugin system_info" | Runs plugin → speaks result |

### J. Agent Loop Tests

| # | Command | Expected |
|---|---------|----------|
| J1 | "Open Notepad" | Opens once, says "Task completed: Opened app" |
| J2 | "Open Notepad and write hello world" | Opens → waits → types → done |
| J3 | "Open Chrome and go to YouTube" | Opens Chrome → navigates to YouTube |
| J4 | "Click on sign in" | Finds button in accessibility tree → clicks |
| J5 | "Scroll down" | Scrolls down → done immediately |
| J6 | "Open Notepad and write hello" then "Open Notepad and write world" | Second command does NOT re-open Notepad |
| J7 | "Open Instagram and message hi to John" | Opens → finds chat → types → enter → done |
| J8 | "Search YouTube for MrBeast" | Opens YouTube search → clicks first video |
| J9 | "What's on my screen" | Describes what it sees |
| J10 | "Open Calculator" | Opens calculator → done |
| J11 | Say command while agent running | Blocked (is_processing flag) |

### K. Agent Safety Tests

| # | Test | Expected |
|---|------|----------|
| K1 | Press Alt+I during agent loop | Emergency stop, returns "Task manually interrupted" |
| K2 | Agent tries to open same app twice | Skipped (opened_apps set) |
| K3 | Agent clicks same spot 3 times | Stuck detection kicks in |
| K4 | Agent scrolls 5 times without finding | Fails with "Could not locate target" |
| K5 | Agent outputs "done" then continues | Forced stop |

### L. API Fallback Tests

| # | Test | Expected |
|---|------|----------|
| L1 | Primary Groq fails | Falls back to backup Groq key |
| L2 | Both Groq keys fail | Falls back to OpenRouter |
| L3 | All 4 API keys fail | Shows "all my API connections failed" |
| L4 | OpenRouter vision model fails | Tries next vision model |
| L5 | No internet | Graceful error, no crash |

### M. Memory System Tests

| # | Test | Expected |
|---|------|----------|
| M1 | Say any command | Saved to `jarvis_chat_log.txt` |
| M2 | Say any command | Saved to memory server chat_history |
| M3 | "Remember this X" | Saved to notes section in memory server |
| M4 | Memory server running | Open localhost:5050 → 5 sections visible |
| M5 | Chat History tab | Shows all conversations |
| M6 | Notes tab | Shows saved notes |
| M7 | Future Ideas tab | Can add/edit/delete ideas |
| M8 | Todo List tab | Can toggle done, edit, delete |
| M9 | Tasks tab | Can set status and priority |
| M10 | Import Log button | Imports jarvis_chat_log.txt |

### N. Subtitle Display Tests

| # | Test | Expected |
|---|------|----------|
| N1 | Say a long command | Full text shown in subtitle |
| N2 | Response spoken | Full response text shown |
| N3 | Agent running | Command text shown during processing |
| N4 | Task completes | Completion message shown |
| N5 | Error occurs | Error message shown |

### O. Edge Case Tests

| # | Test | Expected |
|---|------|----------|
| O1 | No internet | Graceful error, no crash |
| O2 | Memory server not running | Commands still work (just no server save) |
| O3 | Chrome not installed | Falls back to system browser |
| O4 | Groq API key invalid | Falls through to next model |
| O5 | Unknown voice command | Routes to Groq for answer |
| O6 | Very long command | Full text in subtitle, processes correctly |
| O7 | "Open the latest MrBeast video" | Routes to agent (not non-agentic) |
| O8 | Say command during TTS | Blocked while speaking |
| O9 | Multiple rapid commands | Only first executes, rest blocked |
| O10 | Agent reaches 25 steps | Stops with "maximum allowed steps" message |

---

## File Structure

```
Jarvis/
├── jarvis_ui.py                  Main app (HUD + routing + agent loop)
├── jarvis_memory_server.py       Flask REST API for memory (port 5050)
├── jarvis_memory_ui.html         Cyberpunk frontend for memory server
├── jarvis_tasks.json             Persistent todo list (JSON)
├── jarvis_chat_log.txt           Flat text chat log + notes
├── .env                          API keys configuration (DO NOT commit)
├── .env.example                  Template for API keys (safe to commit)
├── requirements.txt              Python dependencies
├── start_jarvis.bat              Windows one-click launcher
├── README.md                     This file
└── jarvis_plugins/
    ├── __init__.py
    └── system_info.py            Sample plugin (CPU/RAM/disk)
```

> **Note:** `.env` contains your API keys and should never be committed to git. The `.gitignore` file should include `.env`.

---

## Known Limitations

1. **Windows only** — Uses Windows UIA (pywinauto), Start Menu, and PowerShell
2. **Chrome required** — Forced browser for all web operations
3. **Internet required** — Voice recognition, TTS, web search, AI models all need internet
4. **Screen OCR** — Uses vision model, not Tesseract (see note in Screen OCR section)
5. **No face recognition** — Requires dlib (not installed)
6. **No email integration** — Requires MCP server setup
7. **No Telegram integration** — Requires bot token + MCP
8. **No voice cloning** — Uses fixed Microsoft Edge TTS voice
9. **Python 3.14 f-string restriction** — No backslash escapes in f-strings

---

## Future Features

- [ ] Email integration via MCP server
- [ ] Telegram bot integration
- [ ] Voice cloning
- [ ] Face recognition (requires dlib)
- [ ] Multi-language support
- [ ] Custom wake word
- [ ] Scheduled tasks (cron-like)
- [ ] Home automation integration
- [ ] Spotify playlist control
- [ ] Calendar integration

---

## License

Personal project — not open source.

---

**Built with Python, Groq, OpenRouter, Edge TTS, and a lot of arc-reactor energy.**
