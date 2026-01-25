# Part 3: Stateful vs Stateless Servers

## Overview

This part compares **stateless** and **stateful** server architectures through hands-on examples.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    STATELESS vs STATEFUL SERVERS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────┐    ┌─────────────────────────────────┐
    │        STATELESS SERVER         │    │         STATEFUL SERVER         │
    │                                 │    │                                 │
    │  "Who are you?                  │    │  "Welcome back!                 │
    │   I just met you!"              │    │   I remember you."              │
    │                                 │    │                                 │
    │   ┌───┐                         │    │   ┌───┐                         │
    │   │   │  No memory              │    │   │ M │  Stores sessions        │
    │   │   │  between requests       │    │   │ E │  Tracks history         │
    │   │   │                         │    │   │ M │  Remembers results      │
    │   └───┘                         │    │   └───┘                         │
    │                                 │    │                                 │
    └─────────────────────────────────┘    └─────────────────────────────────┘
```

---

## Key Question from Lecture

> "HTTP is stateless. Can web servers be stateful?"

**Answer:** Yes! Using cookies, sessions, URL rewriting, or server-side state.

---

## Stateless Server

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATELESS SERVER FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client                              Server                                │
│   ──────                              ──────                                │
│      │                                   │                                  │
│      │─── Request(add, 10, 5) ─────────►│                                  │
│      │                                   │ Calculate: 10 + 5 = 15          │
│      │◄── Response(15) ─────────────────│                                  │
│      │                                   │ *FORGETS EVERYTHING*            │
│      │                                   │                                  │
│      │─── Request(multiply, 15, 2) ────►│                                  │
│      │              ▲                    │ Calculate: 15 × 2 = 30          │
│      │              │                    │                                  │
│      │    Client sends 15!              │                                  │
│      │    (server forgot it)            │                                  │
│      │                                   │                                  │
│      │◄── Response(30) ─────────────────│                                  │
│      │                                   │ *FORGETS EVERYTHING*            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

RULES:
  ✗ Never keep info about client after request
  ✗ Don't record file open status
  ✗ Don't track clients
  ✗ Don't remember previous requests
```

---

## Stateful Server

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATEFUL SERVER FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client                              Server                                │
│   ──────                              ──────                                │
│      │                                   │                                  │
│      │─── Request(add, 10, 5) ─────────►│                                  │
│      │                                   │ Calculate: 10 + 5 = 15          │
│      │                                   │ STORE: last_result = 15         │
│      │                                   │ STORE: history.append(...)      │
│      │◄── Response(15) ─────────────────│                                  │
│      │                                   │                                  │
│      │─── Request(use_last * 2) ───────►│                                  │
│      │                                   │ RECALL: last_result = 15        │
│      │    Client just says "use_last"   │ Calculate: 15 × 2 = 30          │
│      │    (no need to send 15!)         │ STORE: last_result = 30         │
│      │                                   │                                  │
│      │◄── Response(30) ─────────────────│                                  │
│                                                                             │
│   FEATURES:                                                                 │
│     ✓ Keeps track of client sessions                                       │
│     ✓ Can prefetch data                                                    │
│     ✓ Can provide undo/history                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Comparison Table

```
┌───────────────────────┬─────────────────────────┬─────────────────────────┐
│       Aspect          │       STATELESS         │        STATEFUL         │
├───────────────────────┼─────────────────────────┼─────────────────────────┤
│                       │                         │                         │
│  Crash recovery       │  ✓ Easy                 │  ✗ Hard                 │
│                       │    (no state to lose)   │    (state lost)         │
│                       │                         │                         │
│  Scalability          │  ✓ Easy                 │  ✗ Hard                 │
│                       │    (any server works)   │    (session affinity)   │
│                       │                         │                         │
│  Data sent            │  ✗ More                 │  ✓ Less                 │
│                       │    (full context each)  │    (server remembers)   │
│                       │                         │                         │
│  Features             │  ✗ Basic               │  ✓ Rich                 │
│                       │    (no history/undo)    │    (undo, history)      │
│                       │                         │                         │
│  Complexity           │  ✓ Simple              │  ✗ Complex              │
│                       │    (no state mgmt)      │    (sessions, locks)    │
│                       │                         │                         │
└───────────────────────┴─────────────────────────┴─────────────────────────┘
```

---

## Scaling Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STATELESS SCALING (Easy!)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        Load Balancer                                        │
│                             │                                               │
│              ┌──────────────┼──────────────┐                               │
│              ▼              ▼              ▼                               │
│         ┌────────┐    ┌────────┐    ┌────────┐                            │
│         │Server 1│    │Server 2│    │Server 3│                            │
│         └────────┘    └────────┘    └────────┘                            │
│                                                                             │
│   Any server can handle any request!                                       │
│   • Round-robin load balancing works                                       │
│   • Servers are interchangeable                                            │
│   • Easy to add/remove servers                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    STATEFUL SCALING (Hard!)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    Load Balancer (sticky sessions)                          │
│                             │                                               │
│              ┌──────────────┼──────────────┐                               │
│              ▼              ▼              ▼                               │
│         ┌────────┐    ┌────────┐    ┌────────┐                            │
│         │Server 1│    │Server 2│    │Server 3│                            │
│         │        │    │        │    │        │                            │
│         │SessionA│    │SessionB│    │SessionC│                            │
│         │SessionD│    │SessionE│    │SessionF│                            │
│         └────────┘    └────────┘    └────────┘                            │
│              ▲                           ▲                                 │
│              │                           │                                 │
│         User A must          If Server 3 crashes,                         │
│         always go to         Sessions C & F are LOST!                     │
│         Server 1                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Running the Demo

### Quick Start
```bash
# Run the comparison (starts both servers automatically)
python client.py
```

### Run Servers Separately
```bash
# Terminal 1: Start stateless server
python stateless_server.py

# Terminal 2: Start stateful server
python stateful_server.py

# Terminal 3: Run client
python client.py
```

---

## Demo Output Explained

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEMO: Same Calculation                              │
│                    Task: ((10 + 5) × 2) - 3 = 27                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   STATELESS:                        STATEFUL:                              │
│   ──────────                        ─────────                              │
│                                                                             │
│   send(add, 10, 5) → 15            start_session → abc123                 │
│   client stores 15                  send(calculate, 10, 5) → 15            │
│                                     server stores 15                        │
│   send(multiply, 15, 2) → 30                                               │
│   client stores 30                  send(use_last, 2, multiply) → 30       │
│                                     server stores 30                        │
│   send(subtract, 30, 3) → 27                                               │
│                                     send(use_last, 3, subtract) → 27       │
│                                                                             │
│   Data sent: 6 numbers              Data sent: 4 numbers                   │
│   (10,5,15,2,30,3)                  (10,5,2,3)                             │
│                                                                             │
│   Features: NONE                    Features: history, undo, stats         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Real-World Examples

### Stateless
| Service | Why Stateless? |
|---------|----------------|
| REST APIs | Scalable, cacheable |
| DNS servers | Each lookup independent |
| CDN edge servers | Distribute globally |
| Load balancers | Route without tracking |

### Stateful
| Service | Why Stateful? |
|---------|----------------|
| Database connections | Transaction context |
| Shopping carts | Remember items |
| Online games | Player state |
| Chat applications | Conversation history |

---

## HTTP: Stateless Protocol with Stateful Workarounds

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              HOW WE ADD STATE TO STATELESS HTTP                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. COOKIES                                                               │
│   ──────────                                                               │
│      Server: Set-Cookie: session=abc123                                    │
│      Browser: Stores cookie, sends with every request                      │
│      Server: Looks up session=abc123, finds user state                     │
│                                                                             │
│   2. URL REWRITING                                                         │
│   ────────────────                                                         │
│      /cart?session=abc123                                                  │
│      /checkout?session=abc123                                              │
│      Session ID embedded in every URL                                      │
│                                                                             │
│   3. HIDDEN FORM FIELDS                                                    │
│   ─────────────────────                                                    │
│      <input type="hidden" name="session" value="abc123">                   │
│      Submitted with every form POST                                        │
│                                                                             │
│   4. SERVER-SIDE SESSIONS                                                  │
│   ───────────────────────                                                  │
│      Server stores: { "abc123": { cart: [...], user: {...} } }            │
│      Client only knows session ID (in cookie)                              │
│      All state lives on server                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KEY TAKEAWAYS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. STATELESS = Simple, Scalable, Resilient                                │
│     • Any server can handle any request                                    │
│     • Crash? No state lost. Just restart.                                  │
│     • Client does more work (tracks state)                                 │
│                                                                             │
│  2. STATEFUL = Feature-rich, Complex                                       │
│     • Server remembers context                                             │
│     • Enables undo, history, prefetching                                   │
│     • Scaling requires session affinity                                    │
│                                                                             │
│  3. REAL SYSTEMS = Hybrid approach                                         │
│     • HTTP is stateless (protocol level)                                   │
│     • Cookies/sessions add state (application level)                       │
│     • Choose based on requirements                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
