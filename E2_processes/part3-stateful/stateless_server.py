"""
================================================================================
Part 3: Stateless Server - SOLUTION
================================================================================

A stateless server does NOT keep any information about clients between requests.
Every request is completely independent - the server has amnesia!

================================================================================
WHAT IS A STATELESS SERVER?
================================================================================

The server treats each request as if it's the first time seeing this client.
No memory of previous interactions, no sessions, no history.

    Request 1                    Request 2                    Request 3
        │                            │                            │
        ▼                            ▼                            ▼
    ┌────────┐                  ┌────────┐                  ┌────────┐
    │ Server │  ──(forget)──►   │ Server │  ──(forget)──►   │ Server │
    └────────┘                  └────────┘                  └────────┘
        │                            │                            │
        │ "Who are you?              │ "Who are you?              │ "Who are you?
        │  Never seen                │  Never seen                │  Never seen
        │  you before!"              │  you before!"              │  you before!"
        ▼                            ▼                            ▼

================================================================================
STATELESS SERVER RULES (from lecture)
================================================================================

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         STATELESS RULES                                 │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  ✗ Don't record if file is open                                        │
    │  ✗ Don't track clients                                                 │
    │  ✗ Don't promise cache invalidation                                    │
    │  ✗ Don't remember previous requests                                    │
    │                                                                         │
    │  ✓ Each request is COMPLETELY independent                              │
    │  ✓ Client must send ALL necessary data                                 │
    │  ✓ Server processes and forgets immediately                            │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

================================================================================
REQUEST/RESPONSE FLOW
================================================================================

    Client                              Stateless Server
    ──────                              ────────────────
       │                                       │
       │    ┌──────────────────────────┐       │
       │    │ Request 1:               │       │
       │    │   operation: "add"       │       │
       │    │   a: 10                  │       │
       │    │   b: 5                   │       │
       │────┴──────────────────────────┴──────►│
       │                                       │ Process: 10 + 5
       │           ┌───────────────────┐       │
       │           │ Response 1:       │       │
       │◄──────────┤   result: 15      │───────│
       │           └───────────────────┘       │
       │                                       │ *** MEMORY WIPED ***
       │                                       │
       │    ┌──────────────────────────┐       │
       │    │ Request 2:               │       │
       │    │   operation: "multiply"  │       │
       │    │   a: 15  ◄── Client must │       │
       │    │   b: 2       send this!  │       │
       │────┴──────────────────────────┴──────►│
       │                                       │ Process: 15 × 2
       │           ┌───────────────────┐       │
       │◄──────────┤   result: 30      │───────│
       │           └───────────────────┘       │
       │                                       │ *** MEMORY WIPED ***
       │                                       │

    Key insight: Client must send "15" because server forgot!

================================================================================
BENEFITS vs DRAWBACKS
================================================================================

    ┌─────────────────────────────┐    ┌─────────────────────────────┐
    │         BENEFITS            │    │        DRAWBACKS            │
    ├─────────────────────────────┤    ├─────────────────────────────┤
    │                             │    │                             │
    │  ✓ Simple crash recovery    │    │  ✗ Can't prefetch           │
    │    (no state to restore)    │    │    (don't know what's next) │
    │                             │    │                             │
    │  ✓ Easy horizontal scaling  │    │  ✗ May repeat work          │
    │    (any server can handle   │    │    (no memory of past)      │
    │     any request)            │    │                             │
    │                             │    │  ✗ Client tracks state      │
    │  ✓ No state inconsistencies │    │    (more client complexity) │
    │    (nothing to get wrong)   │    │                             │
    │                             │    │  ✗ More bandwidth           │
    │  ✓ Simple implementation    │    │    (resend all data)        │
    │                             │    │                             │
    └─────────────────────────────┘    └─────────────────────────────┘

================================================================================
SCALING ADVANTAGE OF STATELESS
================================================================================

    With STATELESS servers, any server can handle any request:

    Load Balancer
         │
         ├─── Request A ───► Server 1 ───► Response
         │
         ├─── Request B ───► Server 2 ───► Response   (any server works!)
         │
         ├─── Request C ───► Server 3 ───► Response
         │
         └─── Request D ───► Server 1 ───► Response   (round-robin, random, etc.)

    No "sticky sessions" needed! No "session affinity"!
    This is why REST APIs are typically stateless.

================================================================================
"""

import socket
import json
import threading


class StatelessCalculatorServer:
    """
    Stateless calculator server.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    STATELESS SERVER ARCHITECTURE                        │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │                         ┌─────────────────────┐                         │
    │    Client Request ────► │  StatelessServer    │ ────► Response          │
    │                         │                     │                         │
    │                         │  • Parse request    │                         │
    │                         │  • Calculate        │                         │
    │                         │  • Return result    │                         │
    │                         │  • FORGET           │                         │
    │                         │                     │                         │
    │                         │  NO instance vars   │                         │
    │                         │  for client data!   │                         │
    │                         └─────────────────────┘                         │
    │                                                                         │
    │    Notice: No sessions dict, no history list, no last_result!          │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Each request is independent - server remembers nothing about clients.
    
    Instance variables (server config only, NOT client state):
    ──────────────────────────────────────────────────────────
    • host     : str   - Address to bind to
    • port     : int   - Port to listen on
    • running  : bool  - Server running flag
    
    What we DON'T have (stateless!):
    ────────────────────────────────
    • sessions       ✗  (no session tracking)
    • last_result    ✗  (no memory of previous ops)
    • history        ✗  (no operation history)
    • client_data    ✗  (no client-specific storage)
    """
    
    def __init__(self, host='localhost', port=8001):
        """
        Initialize stateless server.
        
        Note: We only store SERVER configuration, never CLIENT state.
        
        Parameters:
        ───────────
        host : str, default='localhost'
            Network interface to bind to
        port : int, default=8001
            TCP port to listen on
        """
        self.host = host
        self.port = port
        self.running = False
        # NOTE: No self.sessions, self.history, etc.!
    
    def handle_client(self, client_socket, address):
        """
        Handle a single client request.
        
        Request lifecycle:
        ──────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                    REQUEST PROCESSING                       │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │  1. RECEIVE ─────► 2. PARSE ─────► 3. CALCULATE            │
            │     (bytes)         (JSON)          (result)               │
            │                                        │                    │
            │                                        ▼                    │
            │  4. RESPOND ◄───── 5. CLOSE ◄───── 6. FORGET               │
            │     (JSON)          (socket)        (nothing stored!)      │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        
        Important: After close(), we have ZERO memory of this request!
        
        Expected request format:
        ────────────────────────
            {
                "operation": "add" | "multiply" | "subtract" | "divide",
                "a": <number>,      ◄── Client MUST send both operands!
                "b": <number>       ◄── We can't use "last result"
            }
        
        Response format:
        ────────────────
            {
                "result": <number>,
                "server_type": "stateless"
            }
        """
        try:
            # ─────────────────────────────────────────────────────────────
            # STEP 1: Receive raw bytes from socket
            # ─────────────────────────────────────────────────────────────
            data = client_socket.recv(1024).decode()
            
            # ─────────────────────────────────────────────────────────────
            # STEP 2: Parse JSON request
            # ─────────────────────────────────────────────────────────────
            request = json.loads(data)
            
            # ─────────────────────────────────────────────────────────────
            # STEP 3: Extract operation and operands
            # ─────────────────────────────────────────────────────────────
            # NOTE: Client MUST send ALL data - we don't remember anything!
            #
            #   Stateless requirement:
            #   ┌────────────────────────────────────────────────────────┐
            #   │  Client sends:  { "op": "multiply", "a": 15, "b": 2 } │
            #   │                                       ▲               │
            #   │                                       │               │
            #   │  Even if "15" was our last result,   │               │
            #   │  client must send it again! ─────────┘               │
            #   └────────────────────────────────────────────────────────┘
            #
            operation = request.get('operation')
            a = request.get('a')
            b = request.get('b')
            
            print(f"[Stateless] Request from {address}: {a} {operation} {b}")
            
            # ─────────────────────────────────────────────────────────────
            # STEP 4: Calculate result (NO STATE from previous requests)
            # ─────────────────────────────────────────────────────────────
            if operation == 'add':
                result = a + b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'divide':
                result = a / b if b != 0 else None
            else:
                result = None
            
            # ─────────────────────────────────────────────────────────────
            # STEP 5: Send response
            # ─────────────────────────────────────────────────────────────
            response = {
                'result': result,
                'server_type': 'stateless'  # Identifying ourselves
            }
            client_socket.send(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[Stateless] Error: {e}")
        finally:
            # ─────────────────────────────────────────────────────────────
            # STEP 6: Close connection and FORGET EVERYTHING
            # ─────────────────────────────────────────────────────────────
            #
            #   ┌────────────────────────────────────────────────────────┐
            #   │                    MEMORY STATE                        │
            #   │                                                        │
            #   │  Before close():                                       │
            #   │    - request data in local variables                   │
            #   │    - result computed                                   │
            #   │                                                        │
            #   │  After close():                                        │
            #   │    - All local variables go out of scope               │
            #   │    - NO instance variables stored client data          │
            #   │    - Server has ZERO memory of this interaction        │
            #   │                                                        │
            #   │  Next request: "Who are you? First time seeing you!"  │
            #   └────────────────────────────────────────────────────────┘
            #
            client_socket.close()
    
    def start(self):
        """
        Start the stateless server.
        
        Server loop:
        ────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                     MAIN SERVER LOOP                        │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │    ┌──────────┐                                             │
            │    │  LISTEN  │◄───────────────────────────────────┐       │
            │    └────┬─────┘                                     │       │
            │         │                                           │       │
            │         ▼                                           │       │
            │    ┌──────────┐                                     │       │
            │    │  ACCEPT  │ (blocks until client connects)      │       │
            │    └────┬─────┘                                     │       │
            │         │                                           │       │
            │         ▼                                           │       │
            │    ┌──────────┐     ┌──────────────────────┐       │       │
            │    │  SPAWN   │────►│  Handler Thread      │       │       │
            │    │  THREAD  │     │  • recv()            │       │       │
            │    └────┬─────┘     │  • process()         │       │       │
            │         │           │  • send()            │       │       │
            │         │           │  • close()           │       │       │
            │         │           │  • FORGET            │       │       │
            │         │           └──────────────────────┘       │       │
            │         │                                           │       │
            │         └───────────────────────────────────────────┘       │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        """
        self.running = True
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1)  # Allow checking self.running
        
        print(f"[Stateless Server] Running on {self.host}:{self.port}")
        print("[Stateless Server] I remember NOTHING between requests!")
        
        while self.running:
            try:
                client_socket, address = server_socket.accept()
                
                # Handle each client in a separate thread
                # (but still stateless - thread has no persistent memory)
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.start()
                
            except socket.timeout:
                continue  # Check if still running
        
        server_socket.close()
    
    def stop(self):
        """Stop the server."""
        self.running = False


# =============================================================================
# DEMONSTRATION: Stateless Limitation
# =============================================================================

def demonstrate_stateless():
    """
    Show that stateless server has no memory.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    DEMONSTRATION SCENARIO                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  Goal: Calculate ((10 + 5) × 2) - 3 = 27                               │
    │                                                                         │
    │  With STATELESS server, client must track intermediate results:        │
    │                                                                         │
    │    Step 1:  send(add, 10, 5)     → get 15   → client stores 15        │
    │    Step 2:  send(multiply, 15, 2) → get 30  → client stores 30        │
    │    Step 3:  send(subtract, 30, 3) → get 27  → done!                   │
    │                                        ▲                               │
    │                                        │                               │
    │    Client had to send 15 and 30 ──────┘                               │
    │    (server didn't remember them)                                       │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Data sent by client:
    ────────────────────
        Request 1: 10, 5         (2 numbers)
        Request 2: 15, 2         (2 numbers - includes previous result!)
        Request 3: 30, 3         (2 numbers - includes previous result!)
        ─────────────────────────
        Total:     6 numbers
    
    Compare this to stateful server which only needs 4 numbers!
    """
    print("\n" + "="*60)
    print("Stateless Server Demonstration")
    print("="*60)
    
    print("""
    ┌────────────────────────────────────────────────────────────┐
    │  Calculating: ((10 + 5) × 2) - 3 = 27                     │
    │                                                            │
    │  With STATELESS server, client sends ALL data each time:  │
    └────────────────────────────────────────────────────────────┘
    """)
    
    def send_request(operation, a, b):
        """Helper to send request and get result."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8001))
        request = json.dumps({'operation': operation, 'a': a, 'b': b})
        sock.send(request.encode())
        response = json.loads(sock.recv(1024).decode())
        sock.close()
        return response['result']
    
    # Start server in background
    server = StatelessCalculatorServer(port=8001)
    server_thread = threading.Thread(target=server.start)
    server_thread.start()
    
    import time
    time.sleep(0.5)  # Let server start
    
    try:
        # ─────────────────────────────────────────────────────────────────
        # Step 1: 10 + 5 = 15
        # ─────────────────────────────────────────────────────────────────
        print("  Step 1:")
        print("    Client: 'Please calculate 10 + 5'")
        result1 = send_request('add', 10, 5)
        print(f"    Server: 'Result is {result1}'")
        print(f"    Server: *immediately forgets*")
        print(f"    Client: 'I'll store {result1} for later'")
        
        # ─────────────────────────────────────────────────────────────────
        # Step 2: 15 * 2 = 30
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 2:")
        print(f"    Client: 'Please calculate {result1} × 2'")
        print(f"            (Client must send {result1} - server forgot!)")
        result2 = send_request('multiply', result1, 2)
        print(f"    Server: 'Result is {result2}'")
        print(f"    Server: *immediately forgets*")
        print(f"    Client: 'I'll store {result2} for later'")
        
        # ─────────────────────────────────────────────────────────────────
        # Step 3: 30 - 3 = 27
        # ─────────────────────────────────────────────────────────────────
        print("\n  Step 3:")
        print(f"    Client: 'Please calculate {result2} - 3'")
        print(f"            (Client must send {result2} - server forgot!)")
        result3 = send_request('subtract', result2, 3)
        print(f"    Server: 'Result is {result3}'")
        
        print(f"""
    ┌────────────────────────────────────────────────────────────┐
    │  Final result: {result3}                                        │
    │                                                            │
    │  Data sent by client: 6 numbers (10, 5, 15, 2, 30, 3)     │
    │                                                            │
    │  Server remembered: NOTHING (stateless!)                   │
    └────────────────────────────────────────────────────────────┘
        """)
        
    finally:
        server.stop()
        server_thread.join()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demonstrate_stateless()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    STATELESS SERVER - KEY POINTS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────┐
    │  CHARACTERISTICS                                                    │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  ✓ No memory between requests                                      │
    │  ✓ Client sends ALL data each time                                 │
    │  ✓ Easy to scale (any server can handle any request)               │
    │  ✓ Easy crash recovery (no state to lose)                          │
    │                                                                     │
    │  ✗ Can't optimize based on history                                 │
    │  ✗ Client must track state                                         │
    │  ✗ More data transferred                                           │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  REAL-WORLD EXAMPLES                                                │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  • REST APIs (typically stateless)                                 │
    │  • DNS servers (each lookup independent)                           │
    │  • CDN edge servers (cache but no client state)                    │
    │  • HTTP protocol itself (stateless by design)                      │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    """)
