# Part 1: Threads vs Processes

## Overview

This part demonstrates the fundamental differences between threads and processes.

## Key Concepts

### Thread Context vs Process Context

```
┌─────────────────────────────────────────────────────────────┐
│                     PROCESS CONTEXT                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Memory maps, open files, environment variables...   │   │
│  │                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │THREAD CTX 1 │  │THREAD CTX 2 │  │THREAD CTX 3 │ │   │
│  │  │ - Stack     │  │ - Stack     │  │ - Stack     │ │   │
│  │  │ - Registers │  │ - Registers │  │ - Registers │ │   │
│  │  │ - PC        │  │ - PC        │  │ - PC        │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                     │   │
│  │            SHARED: Heap, Global Variables           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

PID 35 (PARENT)              PID 36         PID 37         PID 38
───────────────              ──────         ──────         ──────

start() ──────────────────►  worker(0)
start() ──────────────────────────────────► worker(1)
start() ──────────────────────────────────────────────────► worker(2)
    │                           │              │              │
    │                        (work)         (work)         (work)
    │                           │              │              │
 (waiting)                      │              │              │
    │                        exits          exits          exits
    ◄───────────────────────────┴──────────────┴──────────────┘
    │
All joins() return
    │
 Continues...

### Why Use Threads? 

1. **Faster context switching** - No kernel trap needed
2. **Avoid blocking** - One thread blocks, others continue
3. **Exploit parallelism** - Run on multiple CPU cores
4. **Simpler structure** - Easier than multiple processes

### Why NOT Use Threads?

1. **Race conditions** - Shared memory is dangerous
2. **No OS protection** - Threads can corrupt each other's data
3. **Harder to debug** - Non-deterministic behavior

## Running the Demos

```bash
# Thread demonstration
python thread_demo.py

# Process demonstration
python process_demo.py
```

## Expected Output Highlights

### Thread Demo - Race Condition
```
Unsafe counter (expected 100): 87   # Less than 100!
Safe counter (expected 100): 100    # Correct with lock
```

### Process Demo - Speed Comparison
```
Creating 100 threads: 0.05s
Creating 100 processes: 0.85s
Processes are 17x slower to create!
```

## Summary Table

| Aspect | Threads | Processes |
|--------|---------|-----------|
| Memory | Shared | Separate |
| Creation | Fast | Slow |
| Communication | Direct | IPC needed |
| Safety | Risky | Safe |
| Use case | I/O-bound | CPU-bound |
