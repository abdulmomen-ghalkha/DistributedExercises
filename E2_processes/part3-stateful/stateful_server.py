"""
================================================================================
Part 3: Stateful Server - SOLUTION
================================================================================

A stateful server KEEPS information about clients between requests.
It remembers who you are and what you've done!

================================================================================
WHAT IS A STATEFUL SERVER?
================================================================================

The server maintains a "memory" of each client's session:
- Previous results
- Operation history
- Preferences and context

    Request 1                    Request 2                    Request 3
        │                            │                            │
        ▼                            ▼                            ▼
    ┌────────┐                  ┌────────┐                  ┌────────┐
    │ Server │  ──(remember)──► │ Server │  ──(remember)──► │ Server │
    │        │                  │        │                  │        │
    │ Memory:│                  │ Memory:│                  │ Memory:│
    │  - 15  │                  │  - 15  │                  │  - 15  │
    │        │                  │  - 30  │                  │  - 30  │
    │        │                  │        │                  │  - 27  │
    └────────┘                  └────────┘                  └────────┘
        │                            │                            │
        │ "I remember you!           │ "Your last result          │ "Here's your
        │  Session started."         │  was 15."                  │  full history!"
        ▼                            ▼                            ▼

================================================================================
STATEFUL SERVER CAPABILITIES (from lecture)
================================================================================

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                       STATEFUL CAPABILITIES                             │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ✓ Records file open status (for prefetching)                          │
    │  ✓ Tracks client sessions (knows who you are)                          │
    │  ✓ Knows what data client has cached                                   │
    │  ✓ Can anticipate client needs                                         │
    │  ✓ Supports undo/history operations                                    │
    │                                                                         │
    │  Features ONLY stateful servers can provide:                           │
    │  ──────────────────────────────────────────                            │
    │  • "Use last result" (server remembers it)                             │
    │  • "Undo" (server has history)                                         │
    │  • "Show history" (server tracked operations)                          │
    │  • "Prefetch next page" (server knows your position)                   │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

================================================================================
SESSION-BASED ARCHITECTURE
================================================================================

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        SESSION MANAGEMENT                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │   Client A (session: abc123)          Client B (session: xyz789)       │
    │          │                                    │                         │
    │          ▼                                    ▼                         │
    │   ┌─────────────────────────────────────────────────────────┐          │
    │   │                     STATEFUL SERVER                     │          │
    │   │                                                         │          │
    │   │   sessions = {                                          │          │
    │   │       "abc123": {                "xyz789": {            │          │
    │   │           "last_result": 15,         "last_result": 42, │          │
    │   │           "history": [...],          "history": [...],  │          │
    │   │           "created": ...             "created": ...     │          │
    │   │       }                          }                      │          │
    │   │   }                                                     │          │
    │   │                                                         │          │
    │   │   Each client has their own private memory space!       │          │
    │   └─────────────────────────────────────────────────────────┘          │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

================================================================================
REQUEST/RESPONSE FLOW (with state)
================================================================================

    Client                              Stateful Server
    ──────                              ───────────────
       │                                       │
       │    ┌──────────────────────────┐       │
       │    │ Request 1:               │       │
       │    │   operation: "calculate" │       │
       │    │   a: 10, b: 5, op: "add" │       │
       │────┴──────────────────────────┴──────►│
       │                                       │ Process: 10 + 5 = 15
       │                                       │ STORE: last_result = 15
       │                                       │ STORE: history.append(...)
       │           ┌───────────────────┐       │
       │◄──────────┤   result: 15      │───────│
       │           └───────────────────┘       │
       │                                       │
       │    ┌──────────────────────────┐       │
       │    │ Request 2:               │       │
       │    │   operation: "use_last"  │       │
       │    │   b: 2                   │◄── Only need second operand!
       │    │   op: "multiply"         │       │
       │────┴──────────────────────────┴──────►│
       │                                       │ RECALL: last_result = 15
       │                                       │ Process: 15 × 2 = 30
       │                                       │ STORE: last_result = 30
       │           ┌───────────────────┐       │
       │◄──────────┤   result: 30      │───────│
       │           └───────────────────┘       │
       │                                       │

    Key insight: Client didn't send "15" - server remembered it!

================================================================================
BENEFITS vs DRAWBACKS
================================================================================

    ┌─────────────────────────────────┐    ┌─────────────────────────────┐
    │          BENEFITS               │    │         DRAWBACKS           │
    ├─────────────────────────────────┤    ├─────────────────────────────┤
    │                                 │    │                             │
    │  ✓ Can prefetch data            │    │  ✗ Complex crash recovery   │
    │    (knows what's next)          │    │    (must restore state)     │
    │                                 │    │                             │
    │  ✓ Optimize based on history    │    │  ✗ State inconsistencies    │
    │    (caching, prediction)        │    │    possible                 │
    │                                 │    │                             │
    │  ✓ Less bandwidth               │    │  ✗ Harder to scale          │
    │    (don't resend context)       │    │    (session affinity)       │
    │                                 │    │                             │
    │  ✓ Rich features                │    │  ✗ Memory grows             │
    │    (undo, history, etc.)        │    │    (more sessions = more)   │
    │                                 │    │                             │
    └─────────────────────────────────┘    └─────────────────────────────┘

================================================================================
SCALING CHALLENGE OF STATEFUL
================================================================================

    With STATEFUL servers, requests must go to the SAME server:

    Load Balancer (with session affinity / sticky sessions)
         │
         ├─── Request A (session X) ───► Server 1  ◄──┐
         │                                            │
         ├─── Request B (session Y) ───► Server 2    │ Same session
         │                                            │ must go to
         ├─── Request C (session X) ───► Server 1  ◄──┘ same server!
         │                               
         └─── Request D (session Y) ───► Server 2  
                                              
    If Server 1 crashes, session X is LOST! 
    (Unless we replicate state, which is complex)

================================================================================
"""

import socket
import json
import threading
import uuid
import time


class StatefulCalculatorServer:
    """
    Stateful calculator server.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    STATEFUL SERVER ARCHITECTURE                         │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │                    ┌─────────────────────────────┐                      │
    │  Client Request ──►│    StatefulServer          │──► Response           │
    │  (with session_id) │                            │                       │
    │                    │  ┌─────────────────────┐   │                       │
    │                    │  │  SESSION STORE      │   │                       │
    │                    │  │                     │   │                       │
    │                    │  │  {                  │   │                       │
    │                    │  │    "abc123": {      │   │                       │
    │                    │  │      last_result,   │   │                       │
    │                    │  │      history,       │   │                       │
    │                    │  │      created_at     │   │                       │
    │                    │  │    },               │   │                       │
    │                    │  │    "xyz789": {...}  │   │                       │
    │                    │  │  }                  │   │                       │
    │                    │  └─────────────────────┘   │                       │
    │                    └─────────────────────────────┘                      │
    │                                                                         │
    │    Instance variables store CLIENT STATE:                               │
    │    • self.sessions     - Dict of all client sessions                   │
    │    • self.sessions_lock - Thread-safe access to sessions               │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Maintains session state for each client:
    - History of operations (can replay, analyze)
    - Last result (for chained calculations)
    - Usage statistics (operation count, timing)
    
    Session structure:
    ──────────────────
        sessions = {
            "<session_id>": {
                "created_at": <timestamp>,      # When session started
                "last_result": <number|None>,   # Most recent result
                "history": [...],               # All operations
                "operation_count": <int>        # Total ops performed
            }
        }
    """
    
    def __init__(self, host='localhost', port=8002):
        """
        Initialize stateful server.
        
        Note: We store BOTH server config AND client state!
        
        Internal structure:
        ───────────────────
        
            StatefulCalculatorServer
            │
            ├── host              : str       (server config)
            ├── port              : int       (server config)
            ├── running           : bool      (server state)
            │
            ├── sessions          : dict      (CLIENT STATE!)
            │   │
            │   ├── "abc123" ─────────────────────────────────────┐
            │   │   ├── created_at: 1706000000                    │
            │   │   ├── last_result: 15                           │ Client A's
            │   │   ├── history: [{op: "10+5", result: 15}, ...]  │ private
            │   │   └── operation_count: 5                        │ memory
            │   │                                                  │
            │   └── "xyz789" ─────────────────────────────────────┐
            │       ├── created_at: 1706000100                    │
            │       ├── last_result: 42                           │ Client B's
            │       ├── history: [{op: "40+2", result: 42}, ...]  │ private
            │       └── operation_count: 3                        │ memory
            │
            └── sessions_lock     : Lock      (thread safety)
        """
        self.host = host
        self.port = port
        self.running = False
        
        # ═══════════════════════════════════════════════════════════════════
        # THIS IS THE KEY DIFFERENCE FROM STATELESS!
        # ═══════════════════════════════════════════════════════════════════
        # We maintain a dictionary of ALL client sessions
        # Each session stores that client's history and state
        self.sessions = {}
        self.sessions_lock = threading.Lock()  # Thread-safe access
    
    def create_session(self):
        """
        Create a new client session.
        
        Session creation:
        ─────────────────
        
            create_session()
                   │
                   ▼
            ┌─────────────────────────────────────────┐
            │  1. Generate unique ID (UUID)           │
            │     session_id = "a1b2c3d4"            │
            │                                         │
            │  2. Initialize empty state              │
            │     {                                   │
            │       "created_at": now(),              │
            │       "last_result": None,              │
            │       "history": [],                    │
            │       "operation_count": 0              │
            │     }                                   │
            │                                         │
            │  3. Store in sessions dict              │
            │     sessions["a1b2c3d4"] = state       │
            └─────────────────────────────────────────┘
                   │
                   ▼
            Return session_id to client
            (client sends this with future requests)
        
        Returns:
        ────────
        str : Unique session identifier (first 8 chars of UUID)
        """
        session_id = str(uuid.uuid4())[:8]
        
        self.sessions[session_id] = {
            'created_at': time.time(),
            'last_result': None,      # Will store most recent result
            'history': [],            # Will store all operations
            'operation_count': 0      # Will count total operations
        }
        
        return session_id
    
    def get_session(self, session_id):
        """
        Get existing session or create new one.
        
        Session lookup flow:
        ────────────────────
        
            get_session(session_id)
                   │
                   ▼
            ┌─────────────────────────────────────────┐
            │  session_id provided and exists?        │
            └─────────────────────────────────────────┘
                   │                    │
                  YES                   NO
                   │                    │
                   ▼                    ▼
            ┌─────────────┐      ┌─────────────┐
            │ Return      │      │ Create new  │
            │ existing    │      │ session     │
            │ session     │      │             │
            └─────────────┘      └─────────────┘
        
        Thread safety:
        ──────────────
            with self.sessions_lock:  # Only one thread at a time
                # ... access self.sessions ...
        
        Returns:
        ────────
        tuple : (session_id, session_dict)
        """
        with self.sessions_lock:
            if session_id and session_id in self.sessions:
                return session_id, self.sessions[session_id]
            else:
                new_id = self.create_session()
                return new_id, self.sessions[new_id]
    
    def handle_client(self, client_socket, address):
        """
        Handle a client request with session state.
        
        ┌─────────────────────────────────────────────────────────────────────┐
        │                    STATEFUL REQUEST PROCESSING                      │
        ├─────────────────────────────────────────────────────────────────────┤
        │                                                                     │
        │  1. RECEIVE ─► 2. PARSE ─► 3. GET/CREATE SESSION                   │
        │                                      │                              │
        │                                      ▼                              │
        │  ┌────────────────────────────────────────────────────────────┐    │
        │  │                  OPERATION DISPATCH                        │    │
        │  │                                                            │    │
        │  │   "start_session" ──► Create new session                  │    │
        │  │   "calculate"     ──► Do math, store result in session    │    │
        │  │   "use_last"      ──► Use session's last_result           │    │
        │  │   "undo"          ──► Remove last from session history    │    │
        │  │   "history"       ──► Return session's full history       │    │
        │  │   "stats"         ──► Return session statistics           │    │
        │  │                                                            │    │
        │  └────────────────────────────────────────────────────────────┘    │
        │                                      │                              │
        │                                      ▼                              │
        │  4. UPDATE SESSION ─► 5. RESPOND ─► 6. CLOSE (but keep session!)   │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘
        
        Supported operations:
        ─────────────────────
        
            ┌───────────────────┬────────────────────────────────────────────┐
            │ Operation         │ Description                                │
            ├───────────────────┼────────────────────────────────────────────┤
            │ start_session     │ Create new session, return session_id     │
            │ calculate         │ a OP b, store result in session           │
            │ use_last          │ last_result OP b (use stored result!)     │
            │ undo              │ Remove last operation from history        │
            │ history           │ Return complete operation history         │
            │ stats             │ Return session statistics                 │
            └───────────────────┴────────────────────────────────────────────┘
        """
        try:
            # ─────────────────────────────────────────────────────────────────
            # STEP 1-2: Receive and parse request
            # ─────────────────────────────────────────────────────────────────
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 3: Get or create session
            # ─────────────────────────────────────────────────────────────────
            # This is THE KEY STATEFUL BEHAVIOR!
            # We look up (or create) the client's persistent session
            session_id, session = self.get_session(request.get('session_id'))
            
            operation = request.get('operation')
            
            print(f"[Stateful] Session {session_id}: {operation}")
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: start_session
            # ─────────────────────────────────────────────────────────────────
            if operation == 'start_session':
                #
                #   Client                              Server
                #      │                                   │
                #      │─── "start_session" ──────────────►│
                #      │                                   │ Create session
                #      │◄── session_id: "abc123" ──────────│
                #      │                                   │
                #
                response = {
                    'session_id': session_id,
                    'message': 'Session started',
                    'server_type': 'stateful'
                }
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: use_last (ONLY POSSIBLE WITH STATE!)
            # ─────────────────────────────────────────────────────────────────
            elif operation == 'use_last':
                #
                #   ┌────────────────────────────────────────────────────────┐
                #   │  This operation is IMPOSSIBLE in stateless server!    │
                #   │                                                        │
                #   │  Client sends:  { "operation": "use_last",            │
                #   │                   "b": 2,                              │
                #   │                   "op": "multiply" }                   │
                #   │                                                        │
                #   │  Server recalls: last_result = 15 (from session!)     │
                #   │  Server computes: 15 × 2 = 30                         │
                #   │  Server stores: last_result = 30                      │
                #   │                                                        │
                #   │  Client didn't send "15" - server remembered it!      │
                #   └────────────────────────────────────────────────────────┘
                #
                a = session['last_result']  # RETRIEVE FROM SESSION!
                b = request.get('b')
                op = request.get('op', 'add')
                
                if a is None:
                    response = {'error': 'No previous result'}
                else:
                    # Calculate using stored value
                    if op == 'add':
                        result = a + b
                    elif op == 'multiply':
                        result = a * b
                    elif op == 'subtract':
                        result = a - b
                    else:
                        result = None
                    
                    # UPDATE SESSION STATE
                    session['history'].append({
                        'operation': f"{a} {op} {b}",
                        'result': result
                    })
                    session['last_result'] = result
                    session['operation_count'] += 1
                    
                    response = {
                        'session_id': session_id,
                        'operation': f"last_result({a}) {op} {b}",
                        'result': result
                    }
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: calculate (normal calculation)
            # ─────────────────────────────────────────────────────────────────
            elif operation == 'calculate':
                a = request.get('a')
                b = request.get('b')
                op = request.get('op', 'add')
                
                if op == 'add':
                    result = a + b
                elif op == 'multiply':
                    result = a * b
                elif op == 'subtract':
                    result = a - b
                else:
                    result = None
                
                # UPDATE SESSION STATE (stateless server wouldn't do this!)
                session['history'].append({
                    'operation': f"{a} {op} {b}",
                    'result': result
                })
                session['last_result'] = result  # Store for "use_last"
                session['operation_count'] += 1
                
                response = {
                    'session_id': session_id,
                    'result': result
                }
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: undo (ONLY POSSIBLE WITH STATE!)
            # ─────────────────────────────────────────────────────────────────
            elif operation == 'undo':
                #
                #   ┌────────────────────────────────────────────────────────┐
                #   │  UNDO - only possible because we have history!        │
                #   │                                                        │
                #   │  Before undo:                                          │
                #   │    history = [{op: "10+5", result: 15},               │
                #   │               {op: "15*2", result: 30}]               │
                #   │    last_result = 30                                    │
                #   │                                                        │
                #   │  After undo:                                           │
                #   │    history = [{op: "10+5", result: 15}]               │
                #   │    last_result = 15  (restored!)                      │
                #   │                                                        │
                #   │  Stateless server: "Undo what? I have no history!"   │
                #   └────────────────────────────────────────────────────────┘
                #
                if session['history']:
                    removed = session['history'].pop()
                    
                    # Restore previous last_result
                    if session['history']:
                        session['last_result'] = session['history'][-1]['result']
                    else:
                        session['last_result'] = None
                    
                    response = {
                        'session_id': session_id,
                        'undone': removed,
                        'last_result': session['last_result']
                    }
                else:
                    response = {
                        'session_id': session_id,
                        'error': 'Nothing to undo'
                    }
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: history (ONLY POSSIBLE WITH STATE!)
            # ─────────────────────────────────────────────────────────────────
            elif operation == 'history':
                #
                #   Stateless server: "History? I just met you!"
                #   Stateful server:  "Let me show you everything we've done..."
                #
                response = {
                    'session_id': session_id,
                    'history': session['history'],
                    'operation_count': session['operation_count'],
                    'last_result': session['last_result']
                }
            
            # ─────────────────────────────────────────────────────────────────
            # OPERATION: stats (ONLY POSSIBLE WITH STATE!)
            # ─────────────────────────────────────────────────────────────────
            elif operation == 'stats':
                response = {
                    'session_id': session_id,
                    'total_sessions': len(self.sessions),
                    'your_operations': session['operation_count'],
                    'session_age': time.time() - session['created_at']
                }
            
            else:
                response = {'error': f'Unknown operation: {operation}'}
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 5: Send response
            # ─────────────────────────────────────────────────────────────────
            client_socket.send(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[Stateful] Error: {e}")
            client_socket.send(json.dumps({'error': str(e)}).encode())
        finally:
            # ─────────────────────────────────────────────────────────────────
            # STEP 6: Close connection BUT KEEP SESSION!
            # ─────────────────────────────────────────────────────────────────
            #
            #   ┌────────────────────────────────────────────────────────────┐
            #   │                    MEMORY STATE                            │
            #   │                                                            │
            #   │  After close():                                            │
            #   │    - Socket connection closed                              │
            #   │    - BUT session still in self.sessions!                  │
            #   │    - Client can reconnect with same session_id            │
            #   │    - All history preserved!                                │
            #   │                                                            │
            #   │  This is THE KEY difference from stateless!               │
            #   └────────────────────────────────────────────────────────────┘
            #
            client_socket.close()
    
    def start(self):
        """
        Start the stateful server.
        
        Server architecture:
        ────────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                   STATEFUL SERVER                           │
            │                                                             │
            │   ┌─────────────────────────────────────────────────────┐   │
            │   │                 SESSION STORE                       │   │
            │   │   (Persistent across all connections!)              │   │
            │   └─────────────────────────────────────────────────────┘   │
            │          ▲              ▲              ▲                    │
            │          │              │              │                    │
            │   ┌──────┴──────┐ ┌────┴─────┐ ┌─────┴─────┐              │
            │   │  Handler 1  │ │ Handler 2│ │ Handler 3 │              │
            │   │  (thread)   │ │ (thread) │ │ (thread)  │              │
            │   └─────────────┘ └──────────┘ └───────────┘              │
            │          ▲              ▲              ▲                    │
            │          │              │              │                    │
            │   ┌──────┴──────────────┴──────────────┴──────┐            │
            │   │              Accept Loop                   │            │
            │   │         (main server thread)               │            │
            │   └────────────────────────────────────────────┘            │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        """
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1)
        
        print(f"[Stateful Server] Running on {self.host}:{self.port}")
        print("[Stateful Server] I remember EVERYTHING about each session!")
        
        while self.running:
            try:
                client_socket, address = server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.start()
            except socket.timeout:
                continue
        
        server_socket.close()
    
    def stop(self):
        """Stop the server."""
        self.running = False


# =============================================================================
# DEMONSTRATION: Stateful Capabilities
# =============================================================================

def demonstrate_stateful():
    """
    Show that stateful server remembers clients.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    DEMONSTRATION SCENARIO                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  Goal: Calculate ((10 + 5) × 2) - 3 = 27                               │
    │                                                                         │
    │  With STATEFUL server, we can use "use_last" feature:                  │
    │                                                                         │
    │    Step 1:  send(calculate, 10, 5, add)  → get 15  (server stores 15) │
    │    Step 2:  send(use_last, 2, multiply)  → get 30  (server uses 15!)  │
    │    Step 3:  send(use_last, 3, subtract)  → get 27  (server uses 30!)  │
    │                                                                         │
    │  Data sent by client:                                                  │
    │    Request 1: 10, 5        (2 numbers)                                 │
    │    Request 2: 2            (1 number - server has the other!)         │
    │    Request 3: 3            (1 number - server has the other!)         │
    │    ─────────────────────────                                           │
    │    Total:     4 numbers    (vs 6 for stateless - 33% less!)           │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Bonus features demonstrated:
    ────────────────────────────
    • history  - See all past operations
    • undo     - Remove last operation
    • stats    - Session statistics
    """
    print("\n" + "="*60)
    print("Stateful Server Demonstration")
    print("="*60)
    
    # Start server
    server = StatefulCalculatorServer(port=8002)
    server_thread = threading.Thread(target=server.start)
    server_thread.start()
    
    time.sleep(0.5)
    
    session_id = None
    
    def send_request(operation, **kwargs):
        """Helper to send request maintaining session."""
        nonlocal session_id
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8002))
        
        request = {'operation': operation, 'session_id': session_id, **kwargs}
        sock.send(json.dumps(request).encode())
        
        response = json.loads(sock.recv(1024).decode())
        sock.close()
        
        if 'session_id' in response:
            session_id = response['session_id']
        
        return response
    
    try:
        print("""
    ┌────────────────────────────────────────────────────────────┐
    │  Calculating: ((10 + 5) × 2) - 3 = 27                     │
    │                                                            │
    │  With STATEFUL server, server remembers intermediate      │
    │  results - client doesn't need to send them!              │
    └────────────────────────────────────────────────────────────┘
        """)
        
        # ─────────────────────────────────────────────────────────────────
        # Step 1: Start session
        # ─────────────────────────────────────────────────────────────────
        print("  Step 1: Starting session...")
        resp = send_request('start_session')
        print(f"    Server: 'Your session ID is {resp['session_id']}'")
        print(f"    Server: 'I will remember everything for you!'")
        
        # ─────────────────────────────────────────────────────────────────
        # Step 2: Calculate 10 + 5 = 15
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 2: Calculate 10 + 5")
        resp = send_request('calculate', a=10, b=5, op='add')
        print(f"    Client: 'Please calculate 10 + 5'")
        print(f"    Server: 'Result is {resp['result']}'")
        print(f"    Server: *stores last_result = {resp['result']}*")
        
        # ─────────────────────────────────────────────────────────────────
        # Step 3: Use LAST RESULT × 2 = 30
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 3: Use LAST RESULT × 2")
        print("    Client: 'Multiply your last result by 2'")
        print("            (Notice: Client only sends '2', not '15'!)")
        resp = send_request('use_last', b=2, op='multiply')
        print(f"    Server: 'You want last_result(15) × 2 = {resp['result']}'")
        print(f"    Server: *stores last_result = {resp['result']}*")
        
        # ─────────────────────────────────────────────────────────────────
        # Step 4: Use LAST RESULT - 3 = 27
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 4: Use LAST RESULT - 3")
        print("    Client: 'Subtract 3 from your last result'")
        print("            (Notice: Client only sends '3', not '30'!)")
        resp = send_request('use_last', b=3, op='subtract')
        print(f"    Server: 'You want last_result(30) - 3 = {resp['result']}'")
        
        # ─────────────────────────────────────────────────────────────────
        # Bonus: View history (ONLY STATEFUL CAN DO THIS!)
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 5: View HISTORY (stateless can't do this!)")
        resp = send_request('history')
        print(f"    Server: 'Here's everything we've done:'")
        for i, h in enumerate(resp['history']):
            print(f"      {i+1}. {h['operation']} = {h['result']}")
        
        # ─────────────────────────────────────────────────────────────────
        # Bonus: Undo last operation (ONLY STATEFUL CAN DO THIS!)
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 6: UNDO last operation (stateless can't do this!)")
        resp = send_request('undo')
        print(f"    Server: 'I removed: {resp['undone']}'")
        print(f"    Server: 'Your last result is now: {resp['last_result']}'")
        
        # ─────────────────────────────────────────────────────────────────
        # View history after undo
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 7: View history after undo")
        resp = send_request('history')
        for i, h in enumerate(resp['history']):
            print(f"      {i+1}. {h['operation']} = {h['result']}")
        
        print("""
    ┌────────────────────────────────────────────────────────────┐
    │  Summary:                                                  │
    │                                                            │
    │  Data sent by client: 4 numbers (10, 5, 2, 3)             │
    │  vs Stateless: 6 numbers (10, 5, 15, 2, 30, 3)            │
    │                                                            │
    │  Features used:                                            │
    │  • use_last  - Server remembered previous result          │
    │  • history   - Server tracked all operations              │
    │  • undo      - Server can revert operations               │
    │                                                            │
    │  ALL of these are IMPOSSIBLE with stateless server!       │
    └────────────────────────────────────────────────────────────┘
        """)
        
    finally:
        server.stop()
        server_thread.join()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demonstrate_stateful()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     STATEFUL SERVER - KEY POINTS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────┐
    │  CHARACTERISTICS                                                    │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  ✓ Remembers clients (sessions)                                    │
    │  ✓ Can use previous results                                        │
    │  ✓ Supports undo/history                                           │
    │  ✓ Can prefetch/optimize                                           │
    │  ✓ Less data transferred                                           │
    │                                                                     │
    │  ✗ Harder to scale (session must go to same server)               │
    │  ✗ Crash loses state (unless persisted)                           │
    │  ✗ Memory grows with sessions                                      │
    │  ✗ Complex implementation                                          │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  REAL-WORLD EXAMPLES                                                │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  • Database connections (connection pools, transactions)           │
    │  • Shopping carts (remember items across page loads)               │
    │  • Online games (player state, inventory)                          │
    │  • Chat applications (conversation history)                        │
    │  • Web sessions (login state via cookies)                          │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  HTTP IS STATELESS... BUT WE ADD STATE!                            │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  1. Cookies      - Server sends, browser stores, browser returns  │
    │  2. URL params   - /cart?session=abc123                           │
    │  3. Hidden forms - <input type="hidden" name="session">           │
    │  4. Server-side  - Sessions stored on server, ID in cookie        │
    │                                                                     │
    │  This is how we get stateful behavior over stateless HTTP!        │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    """)
