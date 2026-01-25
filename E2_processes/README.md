# Exercise 02: Processes - Exercises SOLUTION

## 📋 Overview

This exercise covers **process and thread concepts** from Lecture 3 (Processes). Students explore threading, the dispatcher/worker model, stateful vs stateless servers, and containerization.

**Course:** 521290S Distributed Systems (2026)  

---

## 🎯 Learning Objectives

After completing this exercise, students should be able to:

1. **Compare threads vs processes** - Understand context switching, shared memory, and when to use each
2. **Implement dispatcher/worker pattern** - Build a multi-threaded server with explicit work distribution
3. **Design stateful vs stateless servers** - Understand tradeoffs and implement both
4. **Use containers** - Package and deploy distributed applications with Docker

---

## 📁 Solution Structure

```
solution/
├── README.md                    # This file
├── docker-compose.yml           # Container orchestration
├── part1-threads/               # Thread vs Process comparison
│   ├── thread_demo.py
│   ├── process_demo.py
│   └── README.md
├── part2-dispatcher/            # Dispatcher/Worker pattern
│   ├── dispatcher_worker.py
│   └── README.md
├── part3-stateful/              # Stateful vs Stateless servers
│   ├── stateless_server.py
│   ├── stateful_server.py
│   ├── client.py
│   └── README.md
└── part4-containers/            # Docker containerization
    ├── Dockerfile
    ├── server.py
    └── README.md
```

---

## 🔑 Key Concepts

### Part 1: Threads vs Processes

| Concept | Threads | Processes |
|---------|---------|-----------|
| **Memory** | Shared address space | Separate address space |
| **Context switch** | Fast (no kernel trap) | Slow (kernel involved) |
| **Communication** | Direct (shared memory) | IPC needed (pipes, sockets) |
| **Safety** | Prone to race conditions | Isolated, safer |
| **Creation** | Lightweight | Heavyweight |



### Part 2: Dispatcher/Worker Model

```
                    ┌──────────┐
   Requests ──────► │Dispatcher│
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
      ┌────────┐    ┌────────┐    ┌────────┐
      │Worker 1│    │Worker 2│    │Worker 3│
      └────────┘    └────────┘    └────────┘
```

### Part 3: Stateful vs Stateless Servers

| Aspect | Stateless | Stateful |
|--------|-----------|----------|
| **Client tracking** | None | Maintains session |
| **Crash recovery** | Easy | Complex |
| **Scalability** | High | Limited |
| **Performance** | May repeat work | Can prefetch/cache |



### Part 4: Containers

**Key building blocks:**
- **Namespaces**: Process isolation (PID, network, mount)
- **Union filesystem**: Layered file system
- **Control groups (cgroups)**: Resource limits


---

## 🎓 Grading Rubric

| Component | Points | Criteria |
|-----------|--------|----------|
| **Part 1: Threads vs Processes** | 25 | Both demos work, timing comparison shown |
| **Part 2: Dispatcher/Worker** | 25 | Dispatcher distributes work, workers process correctly |
| **Part 3: Stateful/Stateless** | 25 | Both servers work, differences demonstrated |
| **Part 4: Containers** | 15 | Dockerfile correct, container runs |
| **Analysis Questions** | 10 | Correct answers with reasoning |
| **Total** | 100 | |

---

## ⚠️ Common Student Mistakes

1. **Race conditions in Part 1** - Forgetting locks when sharing data
2. **Deadlocks in Part 2** - Incorrect queue handling
3. **Session leaks in Part 3** - Not cleaning up stateful sessions
4. **Dockerfile issues** - Wrong base image, missing dependencies

---
