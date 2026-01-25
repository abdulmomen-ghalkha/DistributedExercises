"""
================================================================================
Part 2: Dispatcher/Worker Pattern - SOLUTION
================================================================================

This module implements the Dispatcher/Worker concurrency model, a fundamental
pattern used in servers, thread pools, and distributed systems.

================================================================================
WHAT IS THE DISPATCHER/WORKER PATTERN?
================================================================================

The pattern separates concerns into two roles:

    DISPATCHER (1 thread)          WORKERS (N threads)
    ─────────────────────          ────────────────────
    • Receives all requests        • Process tasks in parallel
    • Routes work to queue         • Pull from shared queue
    • Manages worker lifecycle     • Return results
    • Single point of entry        • Interchangeable/stateless

This is how real servers work! When you call a gRPC service or REST API,
a dispatcher accepts your connection and hands it to an available worker.

================================================================================
ARCHITECTURE OVERVIEW
================================================================================

                         Incoming Requests
                         (tasks to process)
                               │
                               │  submit_task()
                               ▼
                    ┌──────────────────┐
                    │    DISPATCHER    │  ← Single point of entry
                    │                  │    (1 thread)
                    │  • Receives work │
                    │  • Manages pool  │
                    │  • Routes tasks  │
                    └────────┬─────────┘
                             │
                             │  task_queue.put(task)
                             ▼
               ┌─────────────────────────────┐
               │         TASK QUEUE          │  ← Thread-safe buffer
               │                             │    (queue.Queue)
               │  ┌─────┬─────┬─────┬─────┐  │
               │  │Task1│Task2│Task3│ ... │  │
               │  └─────┴─────┴─────┴─────┘  │
               └─────────────┬───────────────┘
                             │
                             │  task_queue.get()
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │Worker 0│    │Worker 1│    │Worker 2│  ← Parallel processing
         │        │    │        │    │        │    (N threads)
         │ Loop:  │    │ Loop:  │    │ Loop:  │
         │ • get  │    │ • get  │    │ • get  │
         │ • work │    │ • work │    │ • work │
         │ • put  │    │ • put  │    │ • put  │
         └───┬────┘    └───┬────┘    └───┬────┘
             │             │             │
             │  result_queue.put(result) │
             ▼             ▼             ▼
        ┌─────────────────────────────────────┐
        │           RESULT QUEUE              │  ← Completed work
        │  ┌──────┬──────┬──────┐             │
        │  │Res 1 │Res 2 │Res 3 │             │
        │  └──────┴──────┴──────┘             │
        └─────────────────────────────────────┘
                         │
                         │  get_result()
                         ▼
                   Back to caller

================================================================================
WHY USE THIS PATTERN?
================================================================================

    WITHOUT Dispatcher/Worker          WITH Dispatcher/Worker
    ──────────────────────────         ─────────────────────────
    
    Request 1 ──► Thread 1             Request 1 ─┐
    Request 2 ──► Thread 2                        │    ┌──► Worker 1
    Request 3 ──► Thread 3             Request 2 ─┼──► Queue ──► Worker 2
    Request 4 ──► Thread 4                        │    └──► Worker 3
    ...                                Request 3 ─┘
    Request N ──► Thread N             
    
    Problems:                          Benefits:
    • Unbounded thread creation        • Fixed thread pool (bounded)
    • Resource exhaustion              • Work queued if busy
    • No backpressure                  • Backpressure via queue size
    • Thread per connection            • Reuse threads efficiently

================================================================================
"""

import threading
import queue
import time
import socket
import json
import random


# =============================================================================
# WORKER CLASS
# =============================================================================

class Worker(threading.Thread):
    """
    Worker thread that processes tasks from a shared queue.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         WORKER LIFECYCLE                                │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐         │
    │    │  START  │────►│  WAIT   │────►│ PROCESS │────►│  DONE?  │         │
    │    └─────────┘     │for task │     │  task   │     └────┬────┘         │
    │                    └────┬────┘     └─────────┘          │              │
    │                         │               ▲           No  │  Yes         │
    │                         │               │          ┌────┴────┐         │
    │                         │               └──────────┤         ▼         │
    │                         │                          │    ┌─────────┐    │
    │                    timeout                         │    │SHUTDOWN │    │
    │                         │                          │    └─────────┘    │
    │                         ▼                          │                   │
    │                    ┌─────────┐                     │                   │
    │                    │  CHECK  │─── task=None ───────┘                   │
    │                    │  QUEUE  │                                         │
    │                    └────┬────┘                                         │
    │                         │ task found                                   │
    │                         └────────────────────────►(PROCESS)            │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Key behaviors:
    ─────────────
    • Blocks on queue.get() waiting for work (efficient, no busy-wait)
    • Uses timeout to periodically check for shutdown
    • Receives None as shutdown signal (sentinel value pattern)
    • Marks tasks done with task_done() for join() synchronization
    """
    
    def __init__(self, worker_id, task_queue, result_queue):
        """
        Initialize a worker thread.
        
        Parameters:
        ───────────
        worker_id    : int           - Unique identifier for logging
        task_queue   : queue.Queue   - Shared queue to pull tasks from
        result_queue : queue.Queue   - Shared queue to push results to
        
        Shared State:
        ─────────────
            ┌────────────────────────────────────────────┐
            │              SHARED RESOURCES              │
            │                                            │
            │   task_queue ◄─── Dispatcher puts tasks    │
            │        │                                   │
            │        ▼                                   │
            │   [Worker 0] [Worker 1] [Worker 2]         │
            │        │         │          │              │
            │        └─────────┼──────────┘              │
            │                  ▼                         │
            │            result_queue ──► Dispatcher     │
            │                                            │
            └────────────────────────────────────────────┘
        """
        super().__init__()
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.daemon = True  # Dies when main thread dies (won't block exit)
        
    def run(self):
        """
        Main worker loop - runs until shutdown signal received.
        
        Loop structure:
        ───────────────
            while True:
                ┌─────────────────────────────────────┐
                │ 1. WAIT for task (blocking call)    │
                │    task = queue.get(timeout=1)      │
                ├─────────────────────────────────────┤
                │ 2. CHECK for shutdown               │
                │    if task is None: break           │
                ├─────────────────────────────────────┤
                │ 3. PROCESS the task                 │
                │    result = process_task(task)      │
                ├─────────────────────────────────────┤
                │ 4. STORE result                     │
                │    result_queue.put(result)         │
                ├─────────────────────────────────────┤
                │ 5. SIGNAL completion                │
                │    task_queue.task_done()           │
                └─────────────────────────────────────┘
        """
        print(f"[Worker {self.worker_id}] Started")
        
        while True:
            try:
                # ─────────────────────────────────────────────────────────
                # STEP 1: Wait for task
                # ─────────────────────────────────────────────────────────
                # Blocks here until:
                #   a) A task is available, OR
                #   b) Timeout expires (then raises queue.Empty)
                #
                # Why timeout? So we can periodically check if we should
                # shut down, rather than blocking forever.
                task = self.task_queue.get(timeout=1)
                
                # ─────────────────────────────────────────────────────────
                # STEP 2: Check for shutdown signal
                # ─────────────────────────────────────────────────────────
                # Sentinel value pattern: None means "stop working"
                #
                #   Dispatcher                    Worker
                #       │                           │
                #       │  task_queue.put(None)     │
                #       │─────────────────────────► │
                #       │                           │ if task is None:
                #       │                           │     break
                #
                if task is None:
                    print(f"[Worker {self.worker_id}] Shutting down")
                    break
                
                # ─────────────────────────────────────────────────────────
                # STEP 3: Process the task
                # ─────────────────────────────────────────────────────────
                result = self.process_task(task)
                
                # ─────────────────────────────────────────────────────────
                # STEP 4: Store result for collection
                # ─────────────────────────────────────────────────────────
                self.result_queue.put(result)
                
                # ─────────────────────────────────────────────────────────
                # STEP 5: Mark task as done
                # ─────────────────────────────────────────────────────────
                # This decrements the "unfinished tasks" counter.
                # Allows task_queue.join() to know when all work is done.
                self.task_queue.task_done()
                
            except queue.Empty:
                # Timeout expired, no task available
                # Loop back and try again (allows shutdown check)
                continue
    
    def process_task(self, task):
        """
        Process a single calculation task.
        
        Task format (input):
        ────────────────────
            {
                'id': 1,              # Unique task identifier
                'operation': 'add',   # One of: add, multiply, subtract
                'a': 10,              # First operand
                'b': 5                # Second operand
            }
        
        Result format (output):
        ───────────────────────
            {
                'task_id': 1,         # Same as input id
                'result': 15,         # Computed value
                'worker_id': 0        # Which worker processed it
            }
        
        Processing timeline:
        ────────────────────
            Time ──────────────────────────────────────────►
            
            │ Parse │ Simulate work │ Calculate │ Return │
            │       │  (0.1-0.5s)   │           │        │
            └───────┴───────────────┴───────────┴────────┘
        """
        task_id = task['id']
        operation = task['operation']
        a = task['a']
        b = task['b']
        
        print(f"[Worker {self.worker_id}] Processing task {task_id}: {a} {operation} {b}")
        
        # Simulate variable processing time (real work would go here)
        time.sleep(random.uniform(0.1, 0.5))
        
        # Perform the calculation
        if operation == 'add':
            result = a + b
        elif operation == 'multiply':
            result = a * b
        elif operation == 'subtract':
            result = a - b
        else:
            result = None
        
        return {
            'task_id': task_id,
            'result': result,
            'worker_id': self.worker_id
        }


# =============================================================================
# DISPATCHER CLASS
# =============================================================================

class Dispatcher:
    """
    Dispatcher that receives requests and distributes them to workers.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      DISPATCHER RESPONSIBILITIES                        │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │    1. MANAGE WORKERS              2. RECEIVE TASKS                      │
    │    ──────────────────             ────────────────                      │
    │    • Create worker pool           • Accept incoming work                │
    │    • Track worker threads         • Validate requests                   │
    │    • Handle shutdown              • Route to queue                      │
    │                                                                         │
    │    3. DISTRIBUTE WORK             4. COLLECT RESULTS                    │
    │    ───────────────────            ──────────────────                    │
    │    • Put tasks in queue           • Gather from result queue            │
    │    • Load balancing is            • Return to callers                   │
    │      automatic (queue)            • Optional: aggregate                 │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    State diagram:
    ──────────────
    
        ┌──────────┐   start()    ┌─────────┐   shutdown()   ┌──────────┐
        │  CREATED │ ───────────► │ RUNNING │ ─────────────► │ STOPPED  │
        └──────────┘              └─────────┘                └──────────┘
              │                        │
              │                        │ submit_task()
              │                        ▼
              │                   ┌─────────┐
              │                   │ WORKING │ (tasks in queue)
              │                   └─────────┘
              │                        │
              └────────────────────────┘
    """
    
    def __init__(self, num_workers=3):
        """
        Initialize the dispatcher.
        
        Internal structure:
        ───────────────────
        
            Dispatcher
            ├── task_queue    : Queue    ──► Tasks waiting to be processed
            ├── result_queue  : Queue    ──► Completed task results
            ├── workers       : List     ──► Worker thread references
            └── num_workers   : int      ──► Size of thread pool
        
        Queue mechanics:
        ────────────────
        
            task_queue (thread-safe FIFO)
            ┌───┬───┬───┬───┬───┐
            │ T1│ T2│ T3│   │   │  ◄── put() adds here
            └───┴───┴───┴───┴───┘
              │
              └── get() removes from here (oldest first)
        
        Parameters:
        ───────────
        num_workers : int, default=3
            Number of worker threads to create. Consider:
            • CPU-bound work: num_workers ≈ CPU cores
            • I/O-bound work: num_workers can be higher (10-100+)
        """
        self.task_queue = queue.Queue()    # Unbounded by default
        self.result_queue = queue.Queue()  # Unbounded by default
        self.workers = []
        self.num_workers = num_workers
        
    def start(self):
        """
        Start all worker threads.
        
        Startup sequence:
        ─────────────────
        
            Dispatcher.start()
                   │
                   ▼
            ┌─────────────────────────────────────────┐
            │  for i in range(num_workers):          │
            │      worker = Worker(i, queues...)     │
            │      worker.start()  ◄── Thread begins │
            │      workers.append(worker)            │
            └─────────────────────────────────────────┘
                   │
                   ▼
            All workers now running and waiting for tasks
            
            Thread state after start():
            ───────────────────────────
            
            Main Thread          Worker 0         Worker 1         Worker 2
                 │                   │                │                │
                 │                   │ (waiting)      │ (waiting)      │ (waiting)
                 │                   │ queue.get()    │ queue.get()    │ queue.get()
                 ▼                   ▼                ▼                ▼
        """
        print(f"[Dispatcher] Starting {self.num_workers} workers...")
        
        for i in range(self.num_workers):
            worker = Worker(i, self.task_queue, self.result_queue)
            worker.start()
            self.workers.append(worker)
        
        print("[Dispatcher] All workers started")
    
    def submit_task(self, task):
        """
        Submit a task for processing.
        
        Flow:
        ─────
            Caller                  Dispatcher              Task Queue
               │                        │                        │
               │  submit_task(task)     │                        │
               │───────────────────────►│                        │
               │                        │  task_queue.put(task)  │
               │                        │───────────────────────►│
               │                        │                        │
               │  (returns immediately) │                        │
               │◄───────────────────────│                        │
               │                        │                        │
        
        Important: This is ASYNCHRONOUS
        ─────────────────────────────────
        • Task is queued, not processed yet
        • Returns immediately (non-blocking)
        • Use get_result() to retrieve the result later
        
        Parameters:
        ───────────
        task : dict
            Task dictionary with keys: id, operation, a, b
        """
        print(f"[Dispatcher] Received task {task['id']}")
        self.task_queue.put(task)
    
    def get_result(self, timeout=None):
        """
        Get a result from completed tasks.
        
        Blocking behavior:
        ──────────────────
        
            timeout=None         timeout=5              timeout=0
            ────────────         ─────────              ─────────
            Block forever        Block up to 5s         Return immediately
            until result         then return None       (non-blocking)
            
        Usage pattern:
        ──────────────
        
            # Submit multiple tasks
            for task in tasks:
                dispatcher.submit_task(task)
            
            # Collect all results
            results = []
            for _ in range(len(tasks)):
                result = dispatcher.get_result(timeout=5)
                if result:
                    results.append(result)
        
        Returns:
        ────────
        dict or None : Result dictionary, or None if timeout
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def shutdown(self):
        """
        Gracefully shutdown all workers.
        
        Shutdown sequence:
        ──────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │ STEP 1: Send shutdown signals (one None per worker)        │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │   task_queue.put(None)  ──► Worker 0 sees None, exits      │
            │   task_queue.put(None)  ──► Worker 1 sees None, exits      │
            │   task_queue.put(None)  ──► Worker 2 sees None, exits      │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ STEP 2: Wait for workers to finish (join)                  │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │   Main Thread      Worker 0      Worker 1      Worker 2    │
            │        │               │             │             │        │
            │        │  join()       │             │             │        │
            │        │──────────────►│ (exit)      │             │        │
            │        │               X             │             │        │
            │        │  join()                     │             │        │
            │        │────────────────────────────►│ (exit)      │        │
            │        │                             X             │        │
            │        │  join()                                   │        │
            │        │──────────────────────────────────────────►│ (exit) │
            │        │                                           X        │
            │        ▼                                                    │
            │   All workers stopped                                       │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        
        Why one None per worker?
        ────────────────────────
        Each worker calls get() once, receives one None, and exits.
        If we only sent one None, only one worker would stop!
        """
        print("[Dispatcher] Shutting down...")
        
        # Send shutdown signal to each worker
        # Each worker will receive exactly one None
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join()
        
        print("[Dispatcher] All workers stopped")


# =============================================================================
# DEMO: Basic Dispatcher/Worker
# =============================================================================

def demo_basic():
    """
    Demonstrate basic dispatcher/worker pattern.
    
    Execution timeline:
    ───────────────────
    
    Time ─────────────────────────────────────────────────────────────────►
    
    Main:    │ create │ start │ submit tasks │ wait for results │ shutdown │
             └────────┴───────┴──────────────┴──────────────────┴──────────┘
    
    Worker0:          │ wait  │ task1 │ task4 │ done │
                      └───────┴───────┴───────┴──────┘
    
    Worker1:          │ wait  │ task2 │ task5 │ done │
                      └───────┴───────┴───────┴──────┘
    
    Worker2:          │ wait  │ task3 │ done │
                      └───────┴───────┴──────┘
    
    Tasks get distributed across workers automatically!
    """
    print("\n" + "="*60)
    print("Demo: Basic Dispatcher/Worker Pattern")
    print("="*60)
    
    # ─────────────────────────────────────────────────────────────────────
    # SETUP: Create dispatcher with 3 workers
    # ─────────────────────────────────────────────────────────────────────
    dispatcher = Dispatcher(num_workers=3)
    dispatcher.start()
    
    # ─────────────────────────────────────────────────────────────────────
    # SUBMIT: Send tasks to dispatcher
    # ─────────────────────────────────────────────────────────────────────
    #
    #   Tasks flow:
    #   
    #       tasks ──► dispatcher.submit_task() ──► task_queue ──► workers
    #
    tasks = [
        {'id': 1, 'operation': 'add', 'a': 10, 'b': 5},       # 10 + 5 = 15
        {'id': 2, 'operation': 'multiply', 'a': 7, 'b': 8},   # 7 × 8 = 56
        {'id': 3, 'operation': 'subtract', 'a': 100, 'b': 37},# 100 - 37 = 63
        {'id': 4, 'operation': 'add', 'a': 25, 'b': 25},      # 25 + 25 = 50
        {'id': 5, 'operation': 'multiply', 'a': 12, 'b': 12}, # 12 × 12 = 144
    ]
    
    for task in tasks:
        dispatcher.submit_task(task)
    
    # ─────────────────────────────────────────────────────────────────────
    # COLLECT: Wait for and gather results
    # ─────────────────────────────────────────────────────────────────────
    #
    #   Results flow:
    #   
    #       workers ──► result_queue ──► dispatcher.get_result() ──► results
    #
    #   Note: Results may arrive in ANY ORDER (depends on processing time)
    #
    print("\n[Dispatcher] Waiting for results...")
    results = []
    for _ in range(len(tasks)):
        result = dispatcher.get_result(timeout=5)
        if result:
            results.append(result)
            print(f"[Dispatcher] Got result: Task {result['task_id']} = {result['result']} (by Worker {result['worker_id']})")
    
    # ─────────────────────────────────────────────────────────────────────
    # SHUTDOWN: Clean up workers
    # ─────────────────────────────────────────────────────────────────────
    dispatcher.shutdown()
    
    print("\nNotice: Tasks were distributed across multiple workers!")
    print("        Results may arrive out of order (parallel execution).")


# =============================================================================
# NETWORK DISPATCHER (More Realistic)
# =============================================================================

class NetworkDispatcher:
    """
    Dispatcher that accepts network connections.
    
    This is closer to how real servers work:
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    NETWORK DISPATCHER ARCHITECTURE                      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │   Client A ────┐                                                        │
    │                │     ┌─────────────────────┐                            │
    │   Client B ────┼────►│  Listener Thread    │                            │
    │                │     │  (accept sockets)   │                            │
    │   Client C ────┘     └──────────┬──────────┘                            │
    │                                 │                                       │
    │                                 │  task_queue.put(socket)               │
    │                                 ▼                                       │
    │                    ┌────────────────────────┐                           │
    │                    │      Task Queue        │                           │
    │                    │   (client sockets)     │                           │
    │                    └───────────┬────────────┘                           │
    │                                │                                        │
    │               ┌────────────────┼────────────────┐                       │
    │               ▼                ▼                ▼                       │
    │          ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
    │          │Worker 0 │     │Worker 1 │     │Worker 2 │                   │
    │          │         │     │         │     │         │                   │
    │          │• recv() │     │• recv() │     │• recv() │                   │
    │          │• process│     │• process│     │• process│                   │
    │          │• send() │     │• send() │     │• send() │                   │
    │          └────┬────┘     └────┬────┘     └────┬────┘                   │
    │               │              │               │                          │
    │               ▼              ▼               ▼                          │
    │           Response       Response        Response                       │
    │           to Client      to Client       to Client                      │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Key difference from basic dispatcher:
    ─────────────────────────────────────
    • Instead of task dicts, queue holds SOCKET CONNECTIONS
    • Workers receive data over network, send response back
    • This is how HTTP servers, gRPC servers, etc. work!
    """
    
    def __init__(self, host='localhost', port=9999, num_workers=3):
        """
        Initialize network dispatcher.
        
        Network setup:
        ──────────────
        
            Server Socket (listening)
                   │
                   │ bind(host, port)
                   │ listen(backlog)
                   ▼
            ┌──────────────┐
            │ localhost    │
            │    :9999     │  ◄── Clients connect here
            └──────────────┘
        """
        self.host = host
        self.port = port
        self.task_queue = queue.Queue()
        self.workers = []
        self.num_workers = num_workers
        self.running = False
        
    def start(self):
        """
        Start workers and network listener.
        
        Startup creates two types of threads:
        ──────────────────────────────────────
        
            Main Thread
                 │
                 ├───► Worker Thread 0 (handles connections)
                 ├───► Worker Thread 1 (handles connections)
                 ├───► Worker Thread 2 (handles connections)
                 │
                 └───► Listener Thread (accepts connections)
        """
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        # Start listener thread
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen)
        self.listener_thread.start()
        
        print(f"[NetworkDispatcher] Listening on {self.host}:{self.port}")
    
    def _listen(self):
        """
        Listen for incoming connections.
        
        Accept loop:
        ────────────
        
            while running:
                │
                ├──► accept() ◄── blocks until client connects
                │        │
                │        └──► task_queue.put(client_socket)
                │
                └──► (loop back)
        
        Connection flow:
        ────────────────
        
            Client                Server Socket              Queue
               │                        │                      │
               │  connect()             │                      │
               │───────────────────────►│                      │
               │                        │ accept()             │
               │                        │──────────┐           │
               │                        │          │           │
               │                        │◄─────────┘           │
               │                        │ (new socket)         │
               │                        │  put(socket)         │
               │                        │─────────────────────►│
               │                        │                      │
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)  # Backlog of 5 pending connections
        server_socket.settimeout(1)  # Check self.running every second
        
        while self.running:
            try:
                client_socket, address = server_socket.accept()
                print(f"[Dispatcher] Connection from {address}")
                
                # Hand off to worker via queue
                self.task_queue.put(client_socket)
                
            except socket.timeout:
                continue  # Check if still running
        
        server_socket.close()
    
    def _worker_loop(self, worker_id):
        """
        Worker loop that handles network connections.
        
        Per-connection handling:
        ────────────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                     CONNECTION LIFECYCLE                    │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │   1. GET socket from queue                                  │
            │      socket = task_queue.get()                              │
            │                                                             │
            │   2. RECEIVE request data                                   │
            │      data = socket.recv(1024)                               │
            │      request = json.loads(data)                             │
            │                                                             │
            │   3. PROCESS request                                        │
            │      result = calculate(request)                            │
            │                                                             │
            │   4. SEND response                                          │
            │      socket.send(json.dumps(response))                      │
            │                                                             │
            │   5. CLOSE connection                                       │
            │      socket.close()                                         │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        """
        while True:
            try:
                client_socket = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                # Receive request (JSON over TCP)
                data = client_socket.recv(1024).decode()
                request = json.loads(data)
                
                print(f"[Worker {worker_id}] Processing: {request}")
                
                # Process the calculation
                if request['operation'] == 'add':
                    result = request['a'] + request['b']
                elif request['operation'] == 'multiply':
                    result = request['a'] * request['b']
                else:
                    result = None
                
                # Send response back to client
                response = json.dumps({'result': result, 'worker': worker_id})
                client_socket.send(response.encode())
                
            finally:
                # Always close the connection
                client_socket.close()
    
    def stop(self):
        """Stop the dispatcher."""
        self.running = False
        self.listener_thread.join()


def demo_network():
    """
    Demonstrate network dispatcher.
    
    This simulates a real client-server scenario:
    
        ┌────────────────────────────────────────────────────────────────┐
        │                      DEMO SCENARIO                             │
        ├────────────────────────────────────────────────────────────────┤
        │                                                                │
        │   Client 1 ─── "add 10 + 5" ───┐                              │
        │                                │     ┌──────────────┐         │
        │   Client 2 ─── "mul 7 × 8" ────┼────►│   Network    │         │
        │                                │     │  Dispatcher  │         │
        │   Client 3 ─── "add 100+200" ──┘     └──────────────┘         │
        │                                              │                 │
        │                                 ┌────────────┼────────────┐    │
        │                                 ▼            ▼            ▼    │
        │                            ┌────────┐  ┌────────┐  ┌────────┐ │
        │                            │   15   │  │   56   │  │  300   │ │
        │                            └────────┘  └────────┘  └────────┘ │
        │                                                                │
        └────────────────────────────────────────────────────────────────┘
    """
    print("\n" + "="*60)
    print("Demo: Network Dispatcher/Worker")
    print("="*60)
    
    # Start server
    dispatcher = NetworkDispatcher(port=9999, num_workers=3)
    dispatcher.start()
    
    time.sleep(0.5)  # Let server start up
    
    # ─────────────────────────────────────────────────────────────────────
    # CLIENT FUNCTION
    # ─────────────────────────────────────────────────────────────────────
    def client_request(request_id, operation, a, b):
        """
        Simulate a client making a request.
        
        Client flow:
        ────────────
            connect() ──► send(request) ──► recv(response) ──► close()
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9999))
        
        # Send request as JSON
        request = json.dumps({'operation': operation, 'a': a, 'b': b})
        sock.send(request.encode())
        
        # Receive response
        response = json.loads(sock.recv(1024).decode())
        print(f"[Client {request_id}] {a} {operation} {b} = {response['result']} (Worker {response['worker']})")
        
        sock.close()
    
    # ─────────────────────────────────────────────────────────────────────
    # CONCURRENT CLIENTS
    # ─────────────────────────────────────────────────────────────────────
    # Multiple clients connect simultaneously
    # Each runs in its own thread (simulating concurrent users)
    #
    threads = []
    requests = [
        (1, 'add', 10, 5),
        (2, 'multiply', 7, 8),
        (3, 'add', 100, 200),
    ]
    
    for req_id, op, a, b in requests:
        t = threading.Thread(target=client_request, args=(req_id, op, a, b))
        threads.append(t)
        t.start()
    
    # Wait for all clients to complete
    for t in threads:
        t.join()
    
    dispatcher.stop()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DISPATCHER/WORKER PATTERN                             ║
║                        Threading Implementation                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This demo shows the dispatcher/worker pattern - a fundamental architecture
used in servers, thread pools, and parallel processing systems.

┌─────────────────────────────────────────────────────────────────────────────┐
│  KEY CONCEPTS YOU'LL SEE:                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CENTRALIZED DISPATCH                                                    │
│     • One entry point for all requests                                      │
│     • Clean separation of concerns                                          │
│                                                                             │
│  2. THREAD POOL                                                             │
│     • Fixed number of reusable workers                                      │
│     • No thread-per-request overhead                                        │
│                                                                             │
│  3. QUEUE-BASED DISTRIBUTION                                                │
│     • Thread-safe work handoff                                              │
│     • Automatic load balancing                                              │
│     • Backpressure when overloaded                                          │
│                                                                             │
│  4. GRACEFUL SHUTDOWN                                                       │
│     • Sentinel values (None) signal termination                             │
│     • Workers finish current work before stopping                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")
    
    demo_basic()
    demo_network()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            KEY TAKEAWAYS                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

    ┌────────────────────────────────────────────────────────────────────┐
    │                                                                    │
    │  1. DISPATCHER receives ALL requests                               │
    │     └── Single point of entry, easy to monitor/control            │
    │                                                                    │
    │  2. WORKERS process requests in PARALLEL                           │
    │     └── Multiple tasks handled simultaneously                      │
    │                                                                    │
    │  3. QUEUE distributes work FAIRLY                                  │
    │     └── First-come-first-served, no worker favoritism             │
    │                                                                    │
    │  4. This is how REAL SERVERS work internally!                      │
    │     └── gRPC, HTTP servers, database pools, etc.                  │
    │                                                                    │
    └────────────────────────────────────────────────────────────────────┘

    Real-world examples using this pattern:
    ───────────────────────────────────────
    • Web servers (nginx, Apache)
    • gRPC servers
    • Database connection pools
    • Message queue consumers (RabbitMQ, Kafka)
    • Thread pools (Java ExecutorService, Python ThreadPoolExecutor)
""")