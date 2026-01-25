"""
================================================================================
Part 3: Client for Stateless vs Stateful Comparison
================================================================================

This client demonstrates the practical differences between
stateless and stateful servers by performing the same task
on both and comparing the results.

================================================================================
THE EXPERIMENT
================================================================================

    Task: Calculate ((10 + 5) × 2) - 3 = 27

    We'll do this SAME calculation on both servers and compare:
    • How much data the client needs to send
    • What features are available
    • The overall experience

================================================================================
SIDE-BY-SIDE COMPARISON
================================================================================

    ┌─────────────────────────────────┬─────────────────────────────────┐
    │        STATELESS SERVER         │         STATEFUL SERVER         │
    ├─────────────────────────────────┼─────────────────────────────────┤
    │                                 │                                 │
    │  Request 1:                     │  Request 1:                     │
    │    send(add, 10, 5)            │    send(calculate, 10, 5, add)  │
    │    → get 15                     │    → get 15                     │
    │    CLIENT stores 15             │    SERVER stores 15             │
    │                                 │                                 │
    │  Request 2:                     │  Request 2:                     │
    │    send(multiply, 15, 2)       │    send(use_last, 2, multiply)  │
    │          ▲                      │         (no 15 needed!)         │
    │          │                      │    → get 30                     │
    │    CLIENT sends 15              │    SERVER stores 30             │
    │    → get 30                     │                                 │
    │    CLIENT stores 30             │  Request 3:                     │
    │                                 │    send(use_last, 3, subtract)  │
    │  Request 3:                     │         (no 30 needed!)         │
    │    send(subtract, 30, 3)       │    → get 27                     │
    │          ▲                      │                                 │
    │          │                      │  BONUS: history, undo, stats    │
    │    CLIENT sends 30              │                                 │
    │    → get 27                     │                                 │
    │                                 │                                 │
    ├─────────────────────────────────┼─────────────────────────────────┤
    │  Data sent: 6 numbers           │  Data sent: 4 numbers           │
    │  (10, 5, 15, 2, 30, 3)         │  (10, 5, 2, 3)                  │
    │                                 │                                 │
    │  Features: NONE                 │  Features: history, undo, stats │
    └─────────────────────────────────┴─────────────────────────────────┘

================================================================================
ARCHITECTURE OVERVIEW
================================================================================

                                CLIENT
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌───────────────────┐       ┌───────────────────┐
         │  STATELESS SERVER │       │  STATEFUL SERVER  │
         │    (port 8001)    │       │    (port 8002)    │
         ├───────────────────┤       ├───────────────────┤
         │                   │       │                   │
         │  No sessions      │       │  sessions = {     │
         │  No memory        │       │    "abc": {...}   │
         │  No history       │       │    "xyz": {...}   │
         │                   │       │  }                │
         │  Just calculate   │       │                   │
         │  and forget!      │       │  Remember         │
         │                   │       │  everything!      │
         └───────────────────┘       └───────────────────┘

================================================================================
"""

import socket
import json
import threading
import time


def send_to_stateless(operation, a, b):
    """
    Send request to stateless server.
    
    Request flow:
    ─────────────
    
        Client                          Stateless Server (8001)
           │                                     │
           │  ┌─────────────────────────────┐    │
           │  │ {                           │    │
           │  │   "operation": "<op>",      │    │
           │  │   "a": <num>,               │    │
           │  │   "b": <num>                │    │
           │  │ }                           │    │
           │──┴─────────────────────────────┴───►│
           │                                     │ Calculate
           │                                     │ FORGET!
           │  ┌─────────────────────────────┐    │
           │◄─┤ { "result": <num> }         │────│
           │  └─────────────────────────────┘    │
           │                                     │
    
    Note: Client must send BOTH operands - server has no memory!
    
    Parameters:
    ───────────
    operation : str - One of: "add", "multiply", "subtract", "divide"
    a         : int - First operand (client must track this!)
    b         : int - Second operand
    
    Returns:
    ────────
    dict : Response containing "result" and "server_type"
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8001))
    
    request = json.dumps({'operation': operation, 'a': a, 'b': b})
    sock.send(request.encode())
    
    response = json.loads(sock.recv(1024).decode())
    sock.close()
    
    return response


def send_to_stateful(operation, session_id=None, **kwargs):
    """
    Send request to stateful server.
    
    Request flow:
    ─────────────
    
        Client                          Stateful Server (8002)
           │                                     │
           │  ┌─────────────────────────────┐    │
           │  │ {                           │    │
           │  │   "operation": "<op>",      │    │
           │  │   "session_id": "<id>",     │◄── Session tracking!
           │  │   ...params...              │    │
           │  │ }                           │    │
           │──┴─────────────────────────────┴───►│
           │                                     │ Lookup session
           │                                     │ Calculate
           │                                     │ UPDATE session!
           │  ┌─────────────────────────────┐    │
           │◄─┤ { "result": <num>,          │────│
           │  │   "session_id": "<id>" }    │    │
           │  └─────────────────────────────┘    │
           │                                     │
    
    Note: Client sends session_id; server remembers context!
    
    Parameters:
    ───────────
    operation  : str        - Operation type (more options than stateless!)
    session_id : str|None   - Session identifier (None for new session)
    **kwargs   : dict       - Additional parameters (varies by operation)
    
    Supported operations:
    ─────────────────────
        "start_session" - Create new session
        "calculate"     - a OP b with full operands
        "use_last"      - last_result OP b (b only!)
        "undo"          - Remove last operation
        "history"       - Get operation history
        "stats"         - Get session statistics
    
    Returns:
    ────────
    dict : Response (varies by operation, always includes session_id)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8002))
    
    request = json.dumps({
        'operation': operation,
        'session_id': session_id,
        **kwargs
    })
    sock.send(request.encode())
    
    response = json.loads(sock.recv(1024).decode())
    sock.close()
    
    return response


def compare_servers():
    """
    Compare stateless and stateful servers for the same task.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         COMPARISON EXPERIMENT                           │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │   Task: Calculate ((10 + 5) × 2) - 3 = 27                              │
    │                                                                         │
    │   We'll perform this calculation on BOTH servers and observe:          │
    │   • How client interacts with each                                     │
    │   • How much data needs to be sent                                     │
    │   • What additional features stateful provides                         │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    """
    print("="*70)
    print("COMPARISON: Stateless vs Stateful Server")
    print("Task: Calculate ((10 + 5) × 2) - 3 = 27")
    print("="*70)
    
    # =========================================================================
    # STATELESS SERVER TEST
    # =========================================================================
    print("\n" + "-"*35)
    print("STATELESS SERVER")
    print("-"*35)
    print("""
    ┌────────────────────────────────────────────────────────────┐
    │  With STATELESS server:                                    │
    │  • Client tracks intermediate results                      │
    │  • Client sends ALL data with EVERY request               │
    │  • Server has no memory between requests                   │
    └────────────────────────────────────────────────────────────┘
    """)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: 10 + 5 = 15
    # ─────────────────────────────────────────────────────────────────────────
    #
    #   Client                     Server
    #      │   {add, 10, 5}          │
    #      │────────────────────────►│
    #      │◄────────────────────────│
    #      │   {result: 15}          │
    #      │                         │ *forgets*
    #   stores 15
    #
    result1 = send_to_stateless('add', 10, 5)['result']
    print(f"  Request 1: send(add, 10, 5) → {result1}")
    print(f"  Client stores: result = {result1}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: 15 × 2 = 30 (client must send result1!)
    # ─────────────────────────────────────────────────────────────────────────
    #
    #   Client                     Server
    #      │   {multiply, 15, 2}     │
    #      │──────────▲─────────────►│
    #      │          │              │
    #      │   Client sends 15!      │
    #      │◄────────────────────────│
    #      │   {result: 30}          │
    #   stores 30                    │ *forgets*
    #
    result2 = send_to_stateless('multiply', result1, 2)['result']
    print(f"  Request 2: send(multiply, {result1}, 2) → {result2}")
    print(f"  Client stores: result = {result2}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: 30 - 3 = 27 (client must send result2!)
    # ─────────────────────────────────────────────────────────────────────────
    result3 = send_to_stateless('subtract', result2, 3)['result']
    print(f"  Request 3: send(subtract, {result2}, 3) → {result3}")
    
    print(f"""
    ┌────────────────────────────────────────────────────────────┐
    │  Final: {result3}                                              │
    │  Total data sent: 6 numbers (10, 5, 15, 2, 30, 3)         │
    └────────────────────────────────────────────────────────────┘
    """)
    
    # =========================================================================
    # STATEFUL SERVER TEST
    # =========================================================================
    print("-"*35)
    print("STATEFUL SERVER")
    print("-"*35)
    print("""
    ┌────────────────────────────────────────────────────────────┐
    │  With STATEFUL server:                                     │
    │  • Server remembers last result                            │
    │  • Client can say "use your last result"                  │
    │  • Less data to send!                                      │
    └────────────────────────────────────────────────────────────┘
    """)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Start session
    # ─────────────────────────────────────────────────────────────────────────
    #
    #   Client                     Server
    #      │   {start_session}       │
    #      │────────────────────────►│
    #      │                         │ creates session "abc123"
    #      │◄────────────────────────│
    #      │   {session_id: abc123}  │
    #   stores session_id
    #
    resp = send_to_stateful('start_session')
    session_id = resp['session_id']
    print(f"  Session started: {session_id}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: 10 + 5 = 15 (server stores result)
    # ─────────────────────────────────────────────────────────────────────────
    #
    #   Client                     Server
    #      │   {calculate, 10+5}     │
    #      │────────────────────────►│
    #      │                         │ calculates 15
    #      │                         │ STORES last_result = 15
    #      │◄────────────────────────│
    #      │   {result: 15}          │
    #
    resp = send_to_stateful('calculate', session_id, a=10, b=5, op='add')
    print(f"  Request 1: send(calculate, 10, 5, add) → {resp['result']}")
    print(f"  Server stores: last_result = {resp['result']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: use_last × 2 = 30 (client doesn't send 15!)
    # ─────────────────────────────────────────────────────────────────────────
    #
    #   Client                     Server
    #      │   {use_last, 2, ×}      │
    #      │────────────────────────►│
    #      │                         │ RECALLS last_result = 15
    #      │   No 15 sent!           │ calculates 15 × 2 = 30
    #      │                         │ STORES last_result = 30
    #      │◄────────────────────────│
    #      │   {result: 30}          │
    #
    resp = send_to_stateful('use_last', session_id, b=2, op='multiply')
    print(f"  Request 2: send(use_last, 2, multiply) → {resp['result']}")
    print(f"  Server stores: last_result = {resp['result']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: use_last - 3 = 27 (client doesn't send 30!)
    # ─────────────────────────────────────────────────────────────────────────
    resp = send_to_stateful('use_last', session_id, b=3, op='subtract')
    print(f"  Request 3: send(use_last, 3, subtract) → {resp['result']}")
    
    print(f"""
    ┌────────────────────────────────────────────────────────────┐
    │  Final: {resp['result']}                                              │
    │  Total data sent: 4 numbers (10, 5, 2, 3) — 33% less!     │
    └────────────────────────────────────────────────────────────┘
    """)
    
    # =========================================================================
    # STATEFUL BONUS FEATURES
    # =========================================================================
    print("-"*35)
    print("STATEFUL BONUS FEATURES")
    print("-"*35)
    print("""
    ┌────────────────────────────────────────────────────────────┐
    │  Features ONLY possible with stateful server:              │
    │  • history - see all past operations                       │
    │  • undo    - revert the last operation                    │
    │  • stats   - session statistics                            │
    │                                                            │
    │  Stateless server: "What history? I just met you!"        │
    └────────────────────────────────────────────────────────────┘
    """)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Feature: History
    # ─────────────────────────────────────────────────────────────────────────
    resp = send_to_stateful('history', session_id)
    print("  History (stateless can't do this!):")
    for h in resp['history']:
        print(f"    • {h['operation']} = {h['result']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Feature: Undo
    # ─────────────────────────────────────────────────────────────────────────
    resp = send_to_stateful('undo', session_id)
    print(f"\n  Undo (stateless can't do this!): Removed {resp['undone']}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # History after undo
    # ─────────────────────────────────────────────────────────────────────────
    resp = send_to_stateful('history', session_id)
    print("\n  History after undo:")
    for h in resp['history']:
        print(f"    • {h['operation']} = {h['result']}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Import and start both servers
    from stateless_server import StatelessCalculatorServer
    from stateful_server import StatefulCalculatorServer
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              STATELESS vs STATEFUL SERVER COMPARISON                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

    This experiment runs the SAME calculation on both server types
    to demonstrate the practical differences.

    ┌─────────────────────────────────────────────────────────────────────┐
    │                       EXPERIMENT SETUP                              │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │                         CLIENT                                      │
    │                           │                                         │
    │              ┌────────────┴────────────┐                           │
    │              │                         │                           │
    │              ▼                         ▼                           │
    │    ┌─────────────────┐       ┌─────────────────┐                  │
    │    │    STATELESS    │       │    STATEFUL     │                  │
    │    │   port 8001     │       │   port 8002     │                  │
    │    │                 │       │                 │                  │
    │    │  No memory      │       │  Has sessions   │                  │
    │    │  No sessions    │       │  Has history    │                  │
    │    │  No history     │       │  Has undo       │                  │
    │    └─────────────────┘       └─────────────────┘                  │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    """)
    
    print("Starting both servers...")
    
    # Start servers
    stateless = StatelessCalculatorServer(port=8001)
    stateful = StatefulCalculatorServer(port=8002)
    
    t1 = threading.Thread(target=stateless.start)
    t2 = threading.Thread(target=stateful.start)
    t1.start()
    t2.start()
    
    time.sleep(1)  # Let servers start
    
    try:
        compare_servers()
    finally:
        stateless.stop()
        stateful.stop()
        t1.join()
        t2.join()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              SUMMARY                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

    ┌───────────────────────────────┬───────────────────────────────┐
    │          STATELESS            │          STATEFUL             │
    ├───────────────────────────────┼───────────────────────────────┤
    │                               │                               │
    │  ✓ Easy to scale              │  ✗ Harder to scale            │
    │    (any server, any request)  │    (session affinity needed)  │
    │                               │                               │
    │  ✓ Easy crash recovery        │  ✗ Crash loses state          │
    │    (no state to restore)      │    (unless persisted)         │
    │                               │                               │
    │  ✓ Simple implementation      │  ✓ More features              │
    │    (no state management)      │    (undo, history, prefetch)  │
    │                               │                               │
    │  ✗ Client tracks state        │  ✓ Server tracks state        │
    │    (more client complexity)   │    (simpler client)           │
    │                               │                               │
    │  ✗ More data sent             │  ✓ Less data sent             │
    │    (6 numbers in our test)    │    (4 numbers in our test)    │
    │                               │                               │
    │  ✗ No undo/history            │  ✓ Undo/history possible      │
    │                               │                               │
    └───────────────────────────────┴───────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  KEY INSIGHT:                                                       │
    │                                                                     │
    │  HTTP is STATELESS by design, but we often need state!             │
    │                                                                     │
    │  Solutions:                                                         │
    │  • Cookies        — Server sends, browser stores, browser returns  │
    │  • Sessions       — Server stores state, client has session ID     │
    │  • URL rewriting  — Session ID embedded in URL                     │
    │  • Hidden forms   — Session ID in form fields                      │
    │                                                                     │
    │  These add stateful BEHAVIOR on top of a stateless PROTOCOL!       │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    """)
