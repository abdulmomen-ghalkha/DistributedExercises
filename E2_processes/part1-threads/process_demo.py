"""
================================================================================
PROCESSES DEMONSTRATION 
================================================================================

Course: Distributed Systems - Processes

Learning Objectives:
    1. Understand process creation and execution
    2. Observe parallel vs sequential execution
    3. Learn why processes don't share memory by default
    4. Explore Inter-Process Communication (IPC) mechanisms
    5. Compare process vs thread overhead

================================================================================
KEY TERMINOLOGY
================================================================================

    +------------------+--------------------------------------------------------+
    | Term             | Definition                                             |
    +------------------+--------------------------------------------------------+
    | Process          | Independent program with its own memory space          |
    | PID              | Process ID - unique number assigned by the OS          |
    | Parent Process   | The process that creates other processes (your script) |
    | Child Process    | A new process created by the parent                    |
    | p.start()        | Tells OS to create and run the child process           |
    | p.join()         | Makes parent WAIT for child to finish                  |
    +------------------+--------------------------------------------------------+

================================================================================
PROCESS DUTIES BY ROLE
================================================================================

    PARENT PROCESS (PID: e.g., 10921)       CHILD PROCESS (PID: e.g., 10922)
    --------------------------------        --------------------------------
    - Create process object                 - Execute target function
    - Call p.start()                        - Do the actual work
    - Call p.join() to wait                 - Access its own memory copy
    - Collect results via IPC               - Send results via IPC
    - Handle cleanup                        - Exit when function completes
    
    NOTE: Parent does NOT execute the worker function!
          Parent only manages the lifecycle of child processes.

================================================================================
"""

import multiprocessing
import time
import os
from typing import Optional, Tuple


# =============================================================================
# DEMO 1a: PARALLEL Process Execution
# =============================================================================
"""
PARALLEL EXECUTION PATTERN
==========================

When to use: When tasks are independent and can run simultaneously.

Code Pattern:
    processes = []
    for i in range(3):
        p = Process(target=worker)
        processes.append(p)
        p.start()               # <-- Start ALL processes first
    
    for p in processes:         
        p.join()                # <-- THEN wait for all to finish

Timeline Visualization:
    
    Time:   0.0s    0.1s    0.2s    0.3s    0.4s    0.5s
            |-------|-------|-------|-------|-------|
    PID 36: [=================WORKING=================]
    PID 37: [=================WORKING=================]
    PID 38: [=================WORKING=================]
            ^                                         ^
            All start together                        All finish together
    
    Total time: ~0.5s (processes overlap)
"""

def worker_function(worker_id, start_reference, sleep_s: float = 0.5):
    """
    Simple worker function executed by CHILD process.
    
    Parameters:
        worker_id: Our custom label (0, 1, 2) - assigned by us in the loop
        start_reference: Reference time to calculate relative timestamps
    
    Note: os.getpid() returns the Process ID assigned by the Operating System.
          This proves each worker runs in a SEPARATE process.
    """
    start_time = time.time() - start_reference
    print(f"    [Process {worker_id}] PID={os.getpid()}, Started at t={start_time:.3f}s")
    time.sleep(sleep_s)  # Simulate work
    end_time = time.time() - start_reference
    print(f"    [Process {worker_id}] PID={os.getpid()}, Finished at t={end_time:.3f}s (duration: {end_time - start_time:.3f}s)")


# =============================================================================
# MATH OPERATION FUNCTIONS: Each runs in a separate child process
# =============================================================================
"""
MATH OPERATIONS EXAMPLE
=======================

Demonstrates how different operations can run in separate processes.
Each operation gets its own PID from the OS.

    PARENT (PID=1000)
         |
         +---> ADD Process (PID=1001): 10 + 5 = 15
         |
         +---> MUL Process (PID=1002): 10 * 5 = 50
         |
         +---> DIV Process (PID=1003): 10 / 5 = 2.0

Key Insight: Each math operation runs in complete isolation!
"""

def math_add(a, b, start_reference, sleep_s: float = 0.3):
    """Addition operation in a separate process."""
    start_time = time.time() - start_reference
    time.sleep(sleep_s)  # Simulate computation time
    result = a + b
    end_time = time.time() - start_reference
    print(f"    [ADD] PID={os.getpid()}, t={start_time:.3f}s: {a} + {b} = {result} (finished t={end_time:.3f}s)")

def math_sub(a, b, start_reference, sleep_s: float = 0.3):
    """Addition operation in a separate process."""
    start_time = time.time() - start_reference
    time.sleep(sleep_s)  # Simulate computation time
    result = a - b
    end_time = time.time() - start_reference
    print(f"    [SUB] PID={os.getpid()}, t={start_time:.3f}s: {a} - {b} = {result} (finished t={end_time:.3f}s)")


def math_multiply(a, b, start_reference, sleep_s: float = 0.3):
    """Multiplication operation in a separate process."""
    start_time = time.time() - start_reference
    time.sleep(sleep_s)  # Simulate computation time
    result = a * b
    end_time = time.time() - start_reference
    print(f"    [MUL] PID={os.getpid()}, t={start_time:.3f}s: {a} * {b} = {result} (finished t={end_time:.3f}s)")


def math_divide(a, b, start_reference, sleep_s: float = 0.3):
    """Division operation in a separate process."""
    start_time = time.time() - start_reference
    time.sleep(sleep_s)  # Simulate computation time
    result = a / b
    end_time = time.time() - start_reference
    print(f"    [DIV] PID={os.getpid()}, t={start_time:.3f}s: {a} / {b} = {result} (finished t={end_time:.3f}s)")


def demo_parallel_execution(
    n_workers: int = 4,
    worker_sleep_s: float = 0.5,
    math_sleep_s: float = 0.3,
) -> Tuple[float, float]:
    """Demonstrate PARALLEL process execution.

    Returns:
        (total_workers_time_s, total_math_time_s)
    """
    print("\n" + "=" * 70)
    print("DEMO 1a: PARALLEL Execution")
    print("Pattern: join() AFTER all processes start")
    print("=" * 70)
    
    print(f"\n    Main/Parent process PID: {os.getpid()}")
    print(f"\n    Starting {n_workers} child processes...\n")
    
    start_reference = time.time()
    
    # PARALLEL PATTERN: Start ALL processes first
    processes = []
    for i in range(n_workers):
        p = multiprocessing.Process(
            target=worker_function,
            args=(i, start_reference, worker_sleep_s),
        )
        processes.append(p)
        p.start()  # Start immediately, don't wait
    
    # THEN wait for all to complete
    for p in processes:
        p.join()
    
    total_time = time.time() - start_reference
    
    print(f"""
    RESULTS:
    +------------------+------------------------------------------+
    | Total Time       | {total_time:.3f}s                                    |
    | Expected         | ~{worker_sleep_s:.3f}s (all workers overlap)          |
    | Execution Type   | PARALLEL                                 |
    +------------------+------------------------------------------+
    
    OBSERVATION: All {n_workers} processes started within milliseconds of each other
                 and finished at almost the same time!
    """)
    
    # -------------------------------------------------------------------------
    # MATH OPERATIONS EXAMPLE (PARALLEL)
    # -------------------------------------------------------------------------
    """
    PARALLEL MATH TIMELINE:
    
        Time:   0.0s         0.1s         0.2s         0.3s
                |------------|------------|------------|
        ADD:    [===========COMPUTING===========]
        MUL:    [===========COMPUTING===========]
        DIV:    [===========COMPUTING===========]
                ^                                ^
                All start together               All finish together
        
        Total: ~0.3s (operations overlap)
    """
    print("    " + "-" * 62)
    print("    MATH OPERATIONS EXAMPLE (PARALLEL)")
    print("    " + "-" * 62)
    print(f"\n    Parent PID={os.getpid()} spawning 3 math operations...\n")
    
    start_reference = time.time()
    
    # PARALLEL: Start all operations first
    p_add = multiprocessing.Process(target=math_add, args=(10, 5, start_reference, math_sleep_s))
    p_mul = multiprocessing.Process(target=math_multiply, args=(10, 5, start_reference, math_sleep_s))
    p_div = multiprocessing.Process(target=math_divide, args=(10, 5, start_reference, math_sleep_s))
    p_sub = multiprocessing.Process(target=math_sub, args=(10, 5, start_reference, math_sleep_s))

    p_add.start()
    p_mul.start()
    p_div.start()
    p_sub.start()

    # THEN wait for all to complete
    p_add.join()
    p_mul.join()
    p_div.join()
    p_sub.join()

    total_math_time = time.time() - start_reference
    
    print(f"""
    MATH OPERATIONS RESULTS (PARALLEL):
    +------------------+------------------------------------------+
    | Total Time       | {total_math_time:.3f}s                                    |
    | Expected         | ~{math_sleep_s:.3f}s (all 3 ops overlap)                |
    +------------------+------------------------------------------+
    
    OBSERVATION: All operations started at ~t=0.0s (parallel execution)!
    """)

    return total_time, total_math_time


# =============================================================================
# DEMO 1b: SEQUENTIAL Process Execution
# =============================================================================
"""
SEQUENTIAL EXECUTION PATTERN
============================

When this happens: When you call join() immediately after each start().

Code Pattern (INEFFICIENT):
    for i in range(3):
        p = Process(target=worker)
        p.start()
        p.join()                # <-- Wait HERE before starting next!

Timeline Visualization:
    
    Time:   0.0s    0.5s    1.0s    1.5s
            |-------|-------|-------|
    PID 36: [=WORK=]
    PID 37:         [=WORK=]
    PID 38:                 [=WORK=]
            ^       ^       ^       ^
            Start   Start   Start   All
            P0      P1      P2      Done
    
    Total time: ~1.5s (0.5 + 0.5 + 0.5, no overlap)
"""

def demo_sequential_execution(
    n_workers: int = 4,
    worker_sleep_s: float = 0.5,
    math_sleep_s: float = 0.3,
) -> Tuple[float, float]:
    """Demonstrate SEQUENTIAL process execution (inefficient pattern).

    Returns:
        (total_workers_time_s, total_math_time_s)
    """
    print("\n" + "=" * 70)
    print("DEMO 1b: SEQUENTIAL Execution")
    print("Pattern: join() INSIDE loop (waits after each process)")
    print("=" * 70)
    
    print(f"\n    Main/Parent process PID: {os.getpid()}")
    print(f"\n    Starting {n_workers} child processes ONE AT A TIME...\n")
    
    start_reference = time.time()
    
    # SEQUENTIAL PATTERN: Wait for each process before starting next
    for i in range(n_workers):
        p = multiprocessing.Process(target=worker_function, args=(i, start_reference, worker_sleep_s))
        p.start()
        p.join()  # BLOCKS here until this process finishes!
    
    total_time = time.time() - start_reference
    
    print(f"""
    RESULTS:
    +------------------+------------------------------------------+
    | Total Time       | {total_time:.3f}s                                    |
    | Expected         | ~{(n_workers * worker_sleep_s):.3f}s ({worker_sleep_s:.3f}s × {n_workers}, one by one) |
    | Execution Type   | SEQUENTIAL                               |
    +------------------+------------------------------------------+
    
    OBSERVATION: Each process must FINISH before the next one STARTS.
                 Notice the start times: ~0.0s, ~{worker_sleep_s:.3f}s, ~{(2*worker_sleep_s):.3f}s (etc.)
    """)
    
    # -------------------------------------------------------------------------
    # MATH OPERATIONS EXAMPLE (SEQUENTIAL)
    # -------------------------------------------------------------------------
    """
    SEQUENTIAL MATH TIMELINE:
    
        Time:   0.0s         0.3s         0.6s         0.9s
                |------------|------------|------------|
        ADD:    [==COMPUTING==]
        MUL:                 [==COMPUTING==]
        DIV:                              [==COMPUTING==]
                ^            ^            ^            ^
                ADD starts   MUL starts   DIV starts   All done
                             (after ADD)  (after MUL)
        
        Total: ~0.9s (0.3 + 0.3 + 0.3, no overlap)
    """
    print("    " + "-" * 62)
    print("    MATH OPERATIONS EXAMPLE (SEQUENTIAL)")
    print("    " + "-" * 62)
    print(f"\n    Parent PID={os.getpid()} spawning 3 math operations ONE BY ONE...\n")
    
    start_reference = time.time()
    
    # SEQUENTIAL: Start and wait for each before starting next
    p_add = multiprocessing.Process(target=math_add, args=(10, 5, start_reference, math_sleep_s))
    p_add.start()
    p_add.join()  # Wait for ADD to finish
    
    p_mul = multiprocessing.Process(target=math_multiply, args=(10, 5, start_reference, math_sleep_s))
    p_mul.start()
    p_mul.join()  # Wait for MUL to finish
    
    p_div = multiprocessing.Process(target=math_divide, args=(10, 5, start_reference, math_sleep_s))
    p_div.start()
    p_div.join()  # Wait for DIV to finish

    p_sub = multiprocessing.Process(target=math_sub, args=(10, 5, start_reference, math_sleep_s))
    p_sub.start()
    p_sub.join()  # Wait for DIV to finish


    
    total_math_time = time.time() - start_reference
    
    print(f"""
    MATH OPERATIONS RESULTS (SEQUENTIAL):
    +------------------+------------------------------------------+
    | Total Time       | {total_math_time:.3f}s                                    |
    | Expected         | ~{(3*math_sleep_s):.3f}s ({math_sleep_s:.3f}s × 3, one by one)         |
    +------------------+------------------------------------------+
    
    OBSERVATION: Notice start times: ~0.0s, ~0.3s, ~0.6s (sequential)!
    """)

    return total_time, total_math_time


# =============================================================================
# COMPARISON: Parallel vs Sequential
# =============================================================================

def demo_comparison_summary(
    n_workers: int = 4,
    worker_sleep_s: float = 0.5,
    n_math_ops: int = 4,
    math_sleep_s: float = 0.3,
    actual_parallel_s: Optional[float] = None,
    actual_sequential_s: Optional[float] = None,
    actual_math_parallel_s: Optional[float] = None,
    actual_math_sequential_s: Optional[float] = None,
):
    """
    Print a *dynamic* comparison table of parallel vs sequential execution.

    - n_workers / worker_sleep_s control the "3 workers @ 0.5s" part.
    - n_math_ops / math_sleep_s control the math ops comparison.
    - actual_* args are optional: pass the measured totals from your demos
      (so the table shows both expected and actual).
    """

    # -----------------------------
    # Expected times (simple model)
    # -----------------------------
    expected_parallel = worker_sleep_s
    expected_sequential = n_workers * worker_sleep_s

    expected_math_parallel = math_sleep_s
    expected_math_sequential = n_math_ops * math_sleep_s

    # -----------------------------
    # Helper formatting
    # -----------------------------
    def fmt_expected(sec: float) -> str:
        return f"~{sec:.3f}s"

    def fmt_expected_and_actual(expected: float, actual: Optional[float]) -> str:
        if actual is None:
            return fmt_expected(expected)
        return f"{fmt_expected(expected)} (actual {actual:.3f}s)"

    def fmt_time(t: float) -> str:
        return f"t={t:.2f}s"

    # start times for math ops
    # Parallel: all at t=0.00
    # Sequential: op k starts at k * math_sleep_s
    math_parallel_starts = [0.0] * n_math_ops
    math_sequential_starts = [i * math_sleep_s for i in range(n_math_ops)]

    def label_for_op(i: int) -> str:
        # For your default 3 ops: ADD, MUL, DIV
        if i == 0:
            return "OP1"
        if i == 1:
            return "OP2"
        if i == 2:
            return "OP3"
        if i == 3:
            return "OP4"
        return f"OP{i+1}"

    # -----------------------------
    # Print table
    # -----------------------------
    print("\n" + "=" * 70)
    print("COMPARISON: Parallel vs Sequential Execution (Dynamic)")
    print("=" * 70)

    col_w = 28
    def cell(s: str) -> str:
        return f"{s:<{col_w}}"

    print(f"""
    +-------------------------+------------------------------+------------------------------+
    | Aspect                  | PARALLEL                     | SEQUENTIAL                   |
    +-------------------------+------------------------------+------------------------------+
    | join() placement        | AFTER all start()            | INSIDE loop                  |
    +-------------------------+------------------------------+------------------------------+
    | Workers (count)         | {cell(str(n_workers))} | {cell(str(n_workers))} |
    | Worker duration each    | {cell(f"{worker_sleep_s:.3f}s")} | {cell(f"{worker_sleep_s:.3f}s")} |
    +-------------------------+------------------------------+------------------------------+
    | Total time (workers)    | {cell(fmt_expected_and_actual(expected_parallel, actual_parallel_s))} | {cell(fmt_expected_and_actual(expected_sequential, actual_sequential_s))} |
    +-------------------------+------------------------------+------------------------------+
    | CPU utilization         | HIGH (multiple cores)        | LOW (one core at a time)     |
    +-------------------------+------------------------------+------------------------------+
    | Use case                | Independent tasks            | Tasks with dependencies      |
    +-------------------------+------------------------------+------------------------------+
    """)

    # -----------------------------
    # Math ops comparison (dynamic)
    # -----------------------------
    print("    MATH OPERATIONS COMPARISON (Dynamic)")
    print("    " + "-" * 66)

    # Build rows for start times
    start_rows = []
    for i in range(n_math_ops):
        op_label = label_for_op(i)
        p = fmt_time(math_parallel_starts[i])
        s = fmt_time(math_sequential_starts[i])
        # For sequential, add a short hint after the first one
        if i > 0:
            s += f" (after {label_for_op(i-1)})"
        start_rows.append((op_label, p, s))

    # Print as a compact table
    print("    +-------------------------+------------------------------+------------------------------+")
    print("    | Metric                  | PARALLEL                     | SEQUENTIAL                   |")
    print("    +-------------------------+------------------------------+------------------------------+")
    print(f"    | Ops count               | {cell(str(n_math_ops))} | {cell(str(n_math_ops))} |")
    print(f"    | Op duration each        | {cell(f'{math_sleep_s:.3f}s')} | {cell(f'{math_sleep_s:.3f}s')} |")
    print("    +-------------------------+------------------------------+------------------------------+")
    for op_label, p, s in start_rows:
        print(f"    | {op_label} start time{'':<12} | {p:<28} | {s:<28} |")
    print("    +-------------------------+------------------------------+------------------------------+")
    print(f"    | Total time (math ops)   | {cell(fmt_expected_and_actual(expected_math_parallel, actual_math_parallel_s))} | {cell(fmt_expected_and_actual(expected_math_sequential, actual_math_sequential_s))} |")
    print("    +-------------------------+------------------------------+------------------------------+")



# =============================================================================
# DEMO 2: Processes Do NOT Share Memory
# =============================================================================
"""
MEMORY ISOLATION IN PROCESSES
=============================

Key Concept: Each process gets its OWN COPY of variables.
             Changes in one process do NOT affect others.

Why? Because processes have SEPARATE memory spaces.
     This is different from threads, which share memory.

    +------------------+     +------------------+     +------------------+
    |   PARENT         |     |   CHILD 0        |     |   CHILD 1        |
    |   Memory Space   |     |   Memory Space   |     |   Memory Space   |
    +------------------+     +------------------+     +------------------+
    | shared_list =    |     | shared_list =    |     | shared_list =    |
    | ["Initial"]      |     | ["Initial",      |     | ["Initial",      |
    |                  |     |  "From proc 0"]  |     |  "From proc 1"]  |
    +------------------+     +------------------+     +------------------+
           |                        |                        |
           |   Changes here DON'T affect parent or siblings  |
           +------------------------+------------------------+

"""

# Global variable - will NOT be shared between processes!
shared_list = []


def try_to_modify_shared(process_id):
    """
    Attempt to modify the 'shared' list.
    
    SPOILER: This won't work! Each process gets a COPY of shared_list,
             not a reference to the original.
    """
    shared_list.append(f"From process {process_id}")
    print(f"    [Process {process_id}] My local view: {shared_list}")


def demo_no_shared_memory():
    """Demonstrate that processes do NOT share memory."""
    print("\n" + "=" * 70)
    print("DEMO 2: Processes Do NOT Share Memory")
    print("=" * 70)
    
    global shared_list
    shared_list = ["Initial"]
    
    print(f"""
    SETUP:
    - Parent process has: shared_list = {shared_list}
    - We'll spawn 3 child processes that each try to append to it
    
    PREDICTION: What will shared_list contain after all processes finish?
    """)
    
    processes = []
    for i in range(3):
        p = multiprocessing.Process(target=try_to_modify_shared, args=(i,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    print(f"""
    RESULTS:
    +------------------+------------------------------------------+
    | Parent's list    | {shared_list!s:<40} |
    | Expected if      | ["Initial", "From 0", "From 1", "From 2"]|
    | memory was shared|                                          |
    +------------------+------------------------------------------+
    
    EXPLANATION:
    - Each child process got a COPY of shared_list
    - Modifications in child processes don't affect the parent
    - This is WHY we need IPC (Inter-Process Communication)!
    """)


# =============================================================================
# DEMO 3: Inter-Process Communication (IPC) with Queue
# =============================================================================
"""
INTER-PROCESS COMMUNICATION (IPC)
=================================

Problem: Processes can't share memory directly.
Solution: Use special IPC mechanisms like Queue, Pipe, or shared memory.

multiprocessing.Queue:
    - Thread and process safe
    - FIFO (First In, First Out)
    - Handles serialization automatically

    +-------------+                      +-------------+
    |  PRODUCER   |  --- put() --->      |             |
    |  (Child 1)  |                      |    QUEUE    |
    +-------------+                      |             |
                                         |  [item1]    |
    +-------------+                      |  [item2]    |
    |  CONSUMER   |  <--- get() ---      |  [item3]    |
    |  (Child 2)  |                      |             |
    +-------------+                      +-------------+
"""

def producer(queue, items, start_reference):
    """Producer process: puts items into the queue."""
    for item in items:
        t = time.time() - start_reference
        print(f"    [Producer  t={t:.3f}s] Putting: {item}")
        queue.put(item)
        time.sleep(0.1)
    queue.put(None)  # Sentinel value to signal "done"


def consumer(queue, start_reference):
    """Consumer process: gets items from the queue."""
    while True:
        item = queue.get()  # Blocks until item available
        if item is None:    # Check for sentinel
            break
        t = time.time() - start_reference
        print(f"    [Consumer  t={t:.3f}s] Got: {item}")


def demo_ipc_queue():
    """Demonstrate inter-process communication using Queue."""
    print("\n" + "=" * 70)
    print("DEMO 3: Inter-Process Communication (IPC) with Queue")
    print("=" * 70)
    print("""
    SETUP:
    - Producer process: puts items into queue
    - Consumer process: gets items from queue
    - They run in SEPARATE memory spaces but communicate via Queue!
    """)
    
    queue = multiprocessing.Queue()
    items = ["apple", "banana", "cherry"]
    start_reference = time.time()
    
    prod = multiprocessing.Process(target=producer, args=(queue, items, start_reference))
    cons = multiprocessing.Process(target=consumer, args=(queue, start_reference))
    
    prod.start()
    cons.start()
    
    prod.join()
    cons.join()
    
    print("""
    RESULTS:
    +------------------+------------------------------------------+
    | Communication    | SUCCESS - Producer and Consumer exchanged|
    |                  | data despite separate memory spaces!     |
    +------------------+------------------------------------------+
    
    IPC MECHANISMS IN PYTHON:
    +------------------+------------------------------------------+
    | Queue            | Multi-producer, multi-consumer FIFO      |
    | Pipe             | Two-way communication between 2 processes|
    | Value/Array      | Shared memory for simple data types      |
    | Manager          | Shared objects (lists, dicts, etc.)      |
    +------------------+------------------------------------------+
    """)


# =============================================================================
# DEMO 4: Explicit Shared Memory
# =============================================================================
"""
EXPLICIT SHARED MEMORY
======================

multiprocessing.Value and multiprocessing.Array allow explicit memory sharing.

IMPORTANT: Must use Lock to prevent race conditions!

Without Lock (UNSAFE):
    Process 0: reads value (0)
    Process 1: reads value (0)      <- Both read before either writes!
    Process 0: writes value (1)
    Process 1: writes value (1)     <- Lost update! Should be 2.

With Lock (SAFE):
    Process 0: acquires lock, reads (0), writes (1), releases lock
    Process 1: acquires lock, reads (1), writes (2), releases lock

═══════════════════════════════════════════════════════════════════

EXPLICIT SHARED MEMORY — RACE vs LOCK (timeline)
═══════════════════════════════════════════════════════════════════

Legend:
  R = read      +1 = compute      W = write
  [ CS ] = critical section (R → +1 → W)
  🔒 = lock acquired    🔓 = lock released    ⏸ = blocked/waiting
  Time flows →

───────────────────────────────────────────────────────────────────
 NO LOCK (UNSAFE — critical sections overlap)
───────────────────────────────────────────────────────────────────

Time:       t0          t1          t2          t3
            │───────────│───────────│───────────│

P0:         ├── R(0) ── +1 ── W(1) ─┤
                        │
P1:                     ├── R(0) ── +1 ── W(1) ─┤
                            ↑
                        stale read!

Shared:     0           0→          1           1   ❌ LOST UPDATE

Result: counter = 1   (expected: 2)

───────────────────────────────────────────────────────────────────
 WITH LOCK (SAFE — critical sections serialized)
───────────────────────────────────────────────────────────────────

Time:       t0          t1          t2          t3          t4
            │───────────│───────────│───────────│───────────│

P0:        🔒── R(0) ── +1 ── W(1) ─🔓
                              │
P1:                    ⏸ ⏸ ⏸ 🔒── R(1) ── +1 ── W(2) ─🔓
                       waiting     ↑
                                fresh read

Shared:     0                      1                       2   ✅

Result: counter = 2   (correct!)

───────────────────────────────────────────────────────────────────
 KEY INSIGHT
───────────────────────────────────────────────────────────────────

  Without lock    With lock
  ────────────    ─────────
  CS overlap      CS serialize      Same code, different synchronization,
  in time         in time           completely different outcome.

  P0: [====]                        The lock doesn't change WHAT runs,
  P1:    [====]   →   P0: [====]    it changes WHEN it runs.
         ↑↑↑              P1:    [====]
        DANGER!               SAFE
"""

def increment_shared_value(shared_value, lock, process_id, start_reference):
    """Safely increment a shared value using a lock."""
    start_time = time.time() - start_reference
    for _ in range(100):
        with lock:  # Acquire lock, increment, release lock
            shared_value.value += 1
    end_time = time.time() - start_reference
    print(f"    [Process {process_id}] Started t={start_time:.3f}s, Finished t={end_time:.3f}s")


def demo_explicit_shared_memory():
    """Demonstrate explicit shared memory with synchronization."""
    print("\n" + "=" * 70)
    print("DEMO 4: Explicit Shared Memory with Lock")
    print("=" * 70)
    print("""
    SETUP:
    - Shared integer value (starts at 0)
    - 3 processes, each increments 100 times
    - Expected final value: 300 (if synchronization works!)
    """)
    
    # 'i' = signed integer, initial value = 0
    shared_value = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    start_reference = time.time()
    
    processes = []
    for i in range(3):
        p = multiprocessing.Process(
            target=increment_shared_value,
            args=(shared_value, lock, i, start_reference)
        )
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    print(f"""
    RESULTS:
    +------------------+------------------------------------------+
    | Final Value      | {shared_value.value:<40} |
    | Expected Value   | 300 (3 processes × 100 increments)       |
    | Status           | {"SUCCESS!" if shared_value.value == 300 else "RACE CONDITION!":<40} |
    +------------------+------------------------------------------+
    
    KEY POINT: Lock ensures only ONE process modifies the value at a time.
    """)


# =============================================================================
# DEMO 5: Process vs Thread Creation Overhead
# =============================================================================
"""
PROCESS vs THREAD OVERHEAD
==========================

Processes are HEAVIER than threads because:

    +------------------+------------------------------------------+
    | Aspect           | Process              | Thread            |
    +------------------+------------------------------------------+
    | Memory           | Separate space       | Shared space      |
    | Creation cost    | HIGH (copy memory)   | LOW               |
    | Communication    | Need IPC             | Direct (shared)   |
    | Isolation        | Strong               | Weak              |
    | GIL bypass       | YES                  | NO                |
    +------------------+------------------------------------------+

When to use which:
    - CPU-bound tasks → Processes (bypass Python's GIL - Global Interpreter Lock)
    - I/O-bound tasks → Threads (lighter weight, GIL released during I/O)
"""

def cpu_work(n):
    """Simple CPU-bound work."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def demo_speed_comparison():
    """Compare process vs thread creation overhead."""
    print("\n" + "=" * 70)
    print("DEMO 5: Process vs Thread Creation Overhead")
    print("=" * 70)
    
    import threading
    
    iterations = 100
    
    # Measure thread creation time
    start = time.time()
    threads = []
    for _ in range(iterations):
        t = threading.Thread(target=cpu_work, args=(1000,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    thread_time = time.time() - start
    
    # Measure process creation time
    start = time.time()
    processes = []
    for _ in range(iterations):
        p = multiprocessing.Process(target=cpu_work, args=(1000,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    process_time = time.time() - start
    
    ratio = process_time / thread_time
    
    print(f"""
    RESULTS (creating {iterations} workers each):
    +------------------+------------------------------------------+
    | Threads          | {thread_time:.3f}s                                   |
    | Processes        | {process_time:.3f}s                                   |
    | Ratio            | Processes are {ratio:.1f}x slower to create    |
    +------------------+------------------------------------------+
    
    WHY PROCESSES ARE SLOWER TO CREATE:
    - OS must allocate new memory space
    - Must copy parent's memory (copy-on-write)
    - More kernel overhead
    
    WHEN TO USE EACH:
    +------------------+------------------------------------------+
    | Use Processes    | CPU-bound tasks (bypass GIL)             |
    |                  | Need strong isolation                    |
    |                  | Tasks that might crash                   |
    +------------------+------------------------------------------+
    | Use Threads      | I/O-bound tasks (network, disk)          |
    |                  | Need shared memory                       |
    |                  | Many lightweight tasks                   |
    +------------------+------------------------------------------+
    """)


# =============================================================================
# MAIN: Run All Demos
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("         PROCESSES DEMONSTRATION - A Teaching Guide")
    print("         Distributed Systems - Chapter 3: Processes")
    print("=" * 70)
    
    # Demo 1: Parallel vs Sequential Execution
    # (Measured totals are captured, so the comparison table prints BOTH expected and actual.)
    n_workers = 4
    worker_sleep_s = 0.5
    math_sleep_s = 0.3

    actual_parallel_s, actual_math_parallel_s = demo_parallel_execution(
        n_workers=n_workers,
        worker_sleep_s=worker_sleep_s,
        math_sleep_s=math_sleep_s,
    )
    actual_sequential_s, actual_math_sequential_s = demo_sequential_execution(
        n_workers=n_workers,
        worker_sleep_s=worker_sleep_s,
        math_sleep_s=math_sleep_s,
    )

    demo_comparison_summary(
        n_workers=n_workers,
        worker_sleep_s=worker_sleep_s,
        n_math_ops=3,
        math_sleep_s=math_sleep_s,
        actual_parallel_s=actual_parallel_s,
        actual_sequential_s=actual_sequential_s,
        actual_math_parallel_s=actual_math_parallel_s,
        actual_math_sequential_s=actual_math_sequential_s,
    )
    
    # Demo 2: Memory Isolation
    demo_no_shared_memory()
    
    # Demo 3: Inter-Process Communication
    demo_ipc_queue()
    
    # Demo 4: Explicit Shared Memory
    demo_explicit_shared_memory()
    
    # Demo 5: Process vs Thread Overhead
    demo_speed_comparison()
    
    # Final Summary
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
    +----+----------------------------------------------------------------+
    | #  | Takeaway                                                       |
    +----+----------------------------------------------------------------+
    | 1  | join() placement determines PARALLEL vs SEQUENTIAL execution   |
    +----+----------------------------------------------------------------+
    | 2  | Processes have SEPARATE memory spaces (safer but need IPC)     |
    +----+----------------------------------------------------------------+
    | 3  | Use Queue, Pipe, or shared memory for inter-process comm       |
    +----+----------------------------------------------------------------+
    | 4  | Always use Lock when sharing memory to prevent race conditions |
    +----+----------------------------------------------------------------+
    | 5  | Processes are heavier than threads (more creation overhead)    |
    +----+----------------------------------------------------------------+
    | 6  | Use processes for CPU-bound tasks (bypasses Python's GIL)      |
    +----+----------------------------------------------------------------+
    | 7  | Use threads for I/O-bound tasks (lighter weight)               |
    +----+----------------------------------------------------------------+
    """)