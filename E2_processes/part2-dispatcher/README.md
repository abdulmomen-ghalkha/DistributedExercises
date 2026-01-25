# Part 2: Dispatcher/Worker Pattern

## Overview

This part implements the **Dispatcher/Worker model**.

## The Pattern

```
                         ┌──────────────┐
    Network Requests ───►│  DISPATCHER  │
    (from clients)       │              │
                         │ - Receives   │
                         │ - Queues     │
                         │ - Distributes│
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
               ┌────────┐  ┌────────┐  ┌────────┐
               │WORKER 1│  │WORKER 2│  │WORKER 3│
               │        │  │        │  │        │
               │Process │  │Process │  │Process │
               │Request │  │Request │  │Request │
               └────────┘  └────────┘  └────────┘
```

## Why This Pattern?

1. **Improve performance** - Multiple requests handled in parallel
2. **Scale to multiprocessor** - Workers can run on different cores
3. **Hide network latency** - One worker waits for I/O, others continue
4. **Simpler structure** - Blocking calls are easy to understand

## How It Works

1. **Dispatcher Thread**:
   - Listens for incoming requests
   - Puts requests in a shared queue
   - Does NOT process requests itself

2. **Worker Threads**:
   - Wait for tasks from queue
   - Process tasks independently
   - Put results back (or respond directly)

3. **Queue**:
   - Thread-safe data structure
   - Automatic load balancing
   - Workers take next available task

## Running the Demo

```bash
python dispatcher_worker.py
```

## Expected Output

```
[Dispatcher] Starting 3 workers...
[Worker 0] Started
[Worker 1] Started
[Worker 2] Started
[Dispatcher] Received task 1
[Dispatcher] Received task 2
[Worker 0] Processing task 1: 10 add 5
[Worker 1] Processing task 2: 7 multiply 8
...
[Dispatcher] Got result: Task 1 = 15 (by Worker 0)
[Dispatcher] Got result: Task 2 = 56 (by Worker 1)
```

## Connection to gRPC

We will get to replicate this in Exercise 03?

```python
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
```

This IS the dispatcher/worker pattern!
- gRPC is the dispatcher
- ThreadPoolExecutor provides workers
- You just didn't see it explicitly

## Key Code Components

```python
# Shared queue for tasks
task_queue = queue.Queue()

# Worker waits for tasks
task = task_queue.get()  # Blocks until task available

# Dispatcher adds tasks
task_queue.put(new_task)
```
