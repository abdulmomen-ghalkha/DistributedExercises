# Distributed Systems Exercise 1: Microservices (2026)

## 🎯 Learning Objectives

By completing this exercise, you will understand:
- The difference between **monolithic** and **microservices** architecture
- How services communicate over HTTP
- The role of an **API Gateway**

---

## 📐 Architecture Overview

### Part A: Monolithic Architecture

```
┌─────────────────────────────────────────┐
│              Client                     │
└─────────────────┬───────────────────────┘
                  │ HTTP Request
                  ▼
┌─────────────────────────────────────────┐
│           MONOLITH (Port 5000)          │
│  ┌───────────┐       ┌──────────────┐   │
│  │   /add    │       │  /multiply   │   │
│  └───────────┘       └──────────────┘   │
│              ┌──────────┐               │
│              │ /health  │               │
│              └──────────┘               │
└─────────────────────────────────────────┘
```

**One application handles everything.**

---

### Part B: Microservices Architecture

```
                    ┌─────────────────┐
                    │     Client      │
                    └────────┬────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │   API GATEWAY         │
                 │   (Port 8000)         │
                 │   FastAPI             │
                 └───────┬───────┬───────┘
                         │       │
            ┌────────────┘       └────────────┐
            ▼                                 ▼
┌───────────────────────┐       ┌───────────────────────┐
│   ADD SERVICE         │       │   MULTIPLY SERVICE    │
│   (Port 5001)         │       │   (Port 5002)         │
│   Flask               │       │   Flask               │
│                       │       │                       │
│   POST /add           │       │   POST /multiply      │
│   GET  /health        │       │   GET  /health        │
└───────────────────────┘       └───────────────────────┘
```

**Each service does one thing well.**

---

## 📁 Project Structure

```
student-starter/
├── src/
│   ├── monolith/
│   │   └── app.py          ← Complete this first
│   └── microservices/
│       ├── add_service/
│       │   └── app.py      ← Handles only addition
│       ├── multiply_service/
│       │   └── app.py      ← Handles only multiplication
│       └── gateway/
│           └── app.py      ← Routes requests to services
├── requirements.txt
└── README.md
```

---

## ✅ Tasks

| # | File | Port | What to implement |
|---|------|------|-------------------|
| 1 | `src/monolith/app.py` | 5000 | `/add`, `/multiply`, `/health` |
| 2 | `src/microservices/add_service/app.py` | 5001 | `/add`, `/health` |
| 3 | `src/microservices/multiply_service/app.py` | 5002 | `/multiply`, `/health` |
| 4 | `src/microservices/gateway/app.py` | 8000 | Routes + aggregated `/health` |

---

## 🛠️ Environment Setup

### Prerequisites

Before starting, ensure you have installed:
- **Python 3.9+** — [Download here](https://www.python.org/downloads/)
- **A code editor** — We recommend [VS Code](https://code.visualstudio.com/)
- **A terminal** — Command Prompt (Windows), Terminal (Mac/Linux)

To verify Python is installed:
```bash
python --version
# or on some systems:
python3 --version
```

---

## 🐍 Creating Virtual Environments

A virtual environment keeps your project dependencies isolated. Choose **one** method below.

### Option A: Using venv (Built into Python)

```bash
# Navigate to the project folder
cd student-starter

# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

You'll see `(venv)` in your terminal when activated.

To deactivate later:
```bash
deactivate
```

---

### Option B: Using Conda

If you have [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed:

```bash
# Create environment with Python 3.11
conda create --name dist-sys python=3.11

# Activate it
conda activate dist-sys
```

To deactivate later:
```bash
conda deactivate
```

---

## 📦 Installing Dependencies

### Using requirements.txt

First, create a `requirements.txt` file in your project root with:

```
flask==3.0.0
fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0
```

Then install all dependencies:

```bash
# Make sure your virtual environment is activated!
pip install -r requirements.txt
```

### Manual Installation (Alternative)

```bash
pip install flask fastapi uvicorn httpx
```

### Verify Installation

```bash
pip list
```

You should see flask, fastapi, uvicorn, and httpx in the list.

---

## 🏗️ Implementing the Monolith

Open `src/monolith/app.py` and complete the TODOs.

### Step 1: Implement `/add`

```python
@app.route('/add', methods=['POST'])
def add():
    data = request.get_json()      # Parse JSON from request body
    a = data['a']                   # Extract value 'a'
    b = data['b']                   # Extract value 'b'
    result = a + b                  # Perform addition
    return jsonify({
        "operation": "add",
        "a": a,
        "b": b,
        "result": result
    })
```

### Step 2: Implement `/multiply`

Follow the same pattern as `/add`, but use multiplication (`a * b`).

### Step 3: Implement `/health`

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "monolith"
    })
```

---

## 🔧 Implementing the Microservices

### Add Service (`src/microservices/add_service/app.py`)

Similar to the monolith's `/add`, but include `"service": "add_service"` in the response:

```python
@app.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    a, b = data['a'], data['b']
    return jsonify({
        "operation": "add",
        "a": a,
        "b": b,
        "result": a + b,
        "service": "add_service"    # Identifies which service handled it
    })
```

### Multiply Service (`src/microservices/multiply_service/app.py`)

Same pattern, but for multiplication.

### API Gateway (`src/microservices/gateway/app.py`)

The gateway forwards requests to the appropriate service:

```python
@app.post("/add")
async def add(req: CalcRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADD_SERVICE_URL}/add",
            json={"a": req.a, "b": req.b}
        )
        return response.json()
```

For the `/health` endpoint, check both services:

```python
@app.get("/health")
async def health():
    async with httpx.AsyncClient() as client:
        try:
            add_resp = await client.get(f"{ADD_SERVICE_URL}/health")
            add_status = add_resp.json().get("status", "unknown")
        except:
            add_status = "unreachable"
        
        try:
            mult_resp = await client.get(f"{MULTIPLY_SERVICE_URL}/health")
            mult_status = mult_resp.json().get("status", "unknown")
        except:
            mult_status = "unreachable"
    
    return {
        "gateway": "healthy",
        "add_service": add_status,
        "multiply_service": mult_status
    }
```

---

## 🚀 Running the Application

### Running the Monolith

```bash
# From project root, with virtual environment activated
python src/monolith/app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Running the Microservices

You need **3 separate terminal windows**, each with the virtual environment activated.

**Terminal 1 — Add Service:**
```bash
cd student-starter
source venv/bin/activate    # or: venv\Scripts\activate on Windows
python src/microservices/add_service/app.py
```

**Terminal 2 — Multiply Service:**
```bash
cd student-starter
source venv/bin/activate
python src/microservices/multiply_service/app.py
```

**Terminal 3 — API Gateway:**
```bash
cd student-starter
source venv/bin/activate
python src/microservices/gateway/app.py
```

---

## 🧪 Testing Your Implementation

### Testing the Monolith

Open a new terminal and run:

```bash
# Test addition
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{"a": 5, "b": 3}'
```

**Expected response:**
```json
{"operation": "add", "a": 5, "b": 3, "result": 8}
```

```bash
# Test multiplication
curl -X POST http://localhost:5000/multiply \
  -H "Content-Type: application/json" \
  -d '{"a": 4, "b": 7}'
```

**Expected response:**
```json
{"operation": "multiply", "a": 4, "b": 7, "result": 28}
```

```bash
# Test health
curl http://localhost:5000/health
```

**Expected response:**
```json
{"status": "healthy", "service": "monolith"}
```

### Testing the Microservices (via Gateway)

```bash
# Test addition through gateway
curl -X POST http://localhost:8000/add \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 5}'
```

**Expected response:**
```json
{"operation": "add", "a": 10, "b": 5, "result": 15, "service": "add_service"}
```

```bash
# Test health (shows all services)
curl http://localhost:8000/health
```

**Expected response:**
```json
{"gateway": "healthy", "add_service": "healthy", "multiply_service": "healthy"}
```

### Using PowerShell (Windows)

If `curl` doesn't work, use:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/add" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"a": 5, "b": 3}'
```

---

## ❓ Troubleshooting FAQs

### "command not found: python"

**Problem:** Python is not in your PATH.

**Solution:**
- Try `python3` instead of `python`
- Reinstall Python and check "Add to PATH" during installation
- On Windows, try: `py -3` instead

---

### "ModuleNotFoundError: No module named 'flask'"

**Problem:** Dependencies not installed or virtual environment not activated.

**Solution:**
```bash
# Make sure venv is activated (you should see (venv) in terminal)
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows

# Then install dependencies
pip install -r requirements.txt
```

---

### "Address already in use" / "Port 5000 is in use"

**Problem:** Another process is using the port.

**Solution:**
```bash
# Find what's using port 5000:
# Mac/Linux:
lsof -i :5000

# Windows:
netstat -ano | findstr :5000

# Kill the process or use a different port in your code
```

---

### "Connection refused" when testing

**Problem:** The service isn't running.

**Solution:**
- Check the terminal running the service for errors
- Make sure you're using the correct port
- Ensure the service started successfully (look for "Running on..." message)

---

### Gateway returns "unreachable" for services

**Problem:** Add or Multiply service isn't running.

**Solution:**
- Start all three services (add, multiply, gateway)
- Check each service is running on the correct port:
  - Add Service: 5001
  - Multiply Service: 5002
  - Gateway: 8000

---

### "curl: command not found" (Windows)

**Solution:** Use one of these alternatives:

1. **Use PowerShell's Invoke-RestMethod** (see Testing section above)

2. **Install curl via chocolatey:**
   ```bash
   choco install curl
   ```

3. **Use the built-in curl in Git Bash**

---

### JSON parsing error

**Problem:** Malformed JSON in your request.

**Solution:**
- Use double quotes for JSON keys and string values: `{"a": 5, "b": 3}`
- Don't use single quotes: `{'a': 5}` ← This is invalid JSON
- Check for missing commas or brackets

---

## 💡 Quick Reference

| Endpoint | Method | Request Body | Port (Monolith) | Port (Gateway) |
|----------|--------|--------------|-----------------|----------------|
| `/add` | POST | `{"a": num, "b": num}` | 5000 | 8000 |
| `/multiply` | POST | `{"a": num, "b": num}` | 5000 | 8000 |
| `/health` | GET | None | 5000 | 8000 |

---

## 🤔 Reflection Questions

After completing the exercise, consider:

1. What happens if the add_service goes down in the microservices version?
2. How would you add a new `/subtract` operation to each architecture?
3. Which architecture is easier to scale? Why?
4. What are the trade-offs between monolithic and microservices architectures?

---

*Good luck! 🍀*
