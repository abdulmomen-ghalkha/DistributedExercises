# Part 4: Containers

## Overview

This part covers **containerization** - the technology that revolutionized how we deploy and run applications.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              CONTAINERS                                      ║
║                                                                              ║
║    "Package your application and all its dependencies into a single unit    ║
║     that runs consistently everywhere - laptop, server, cloud."             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Container Building Blocks

### 1. Namespaces - Isolation

Namespaces make processes think they're alone on the system.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HOST SYSTEM                                        │
│                                                                              │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │       Container A           │    │       Container B           │        │
│   │                             │    │                             │        │
│   │   PID Namespace:            │    │   PID Namespace:            │        │
│   │     PID 1 (init)            │    │     PID 1 (init)   ← Same!  │        │
│   │     PID 2 (app)             │    │     PID 2 (app)             │        │
│   │                             │    │                             │        │
│   │   Network Namespace:        │    │   Network Namespace:        │        │
│   │     eth0: 172.17.0.2        │    │     eth0: 172.17.0.3        │        │
│   │     localhost               │    │     localhost      ← Own!   │        │
│   │                             │    │                             │        │
│   │   Mount Namespace:          │    │   Mount Namespace:          │        │
│   │     /app → container files  │    │     /app → container files  │        │
│   │                             │    │                             │        │
│   └─────────────────────────────┘    └─────────────────────────────┘        │
│                                                                              │
│   Host sees real PIDs: 5432, 5433        Host sees: 6789, 6790              │
│                                                                              │
│   TYPES OF NAMESPACES:                                                       │
│   • PID      - Process IDs                                                  │
│   • Network  - Network interfaces, IPs                                      │
│   • Mount    - Filesystem mounts                                            │
│   • UTS      - Hostname                                                     │
│   • IPC      - Inter-process communication                                  │
│   • User     - User/group IDs                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Union Filesystem - Layers

Images are built in layers. Layers are shared and cached.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNION FILESYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│            Container Layer (writable)                                        │
│                    ↑                                                         │
│    ┌───────────────────────────────────────────────────────┐                │
│    │     Layer 4: COPY server.py                           │ ← Your code    │
│    ├───────────────────────────────────────────────────────┤                │
│    │     Layer 3: RUN pip install                          │ ← Dependencies │
│    ├───────────────────────────────────────────────────────┤                │
│    │     Layer 2: RUN apt-get install curl                 │ ← System tools │
│    ├───────────────────────────────────────────────────────┤                │
│    │     Layer 1: python:3.11-slim                         │ ← Base image   │
│    └───────────────────────────────────────────────────────┘                │
│                                                                              │
│   KEY BENEFITS:                                                              │
│   • Lower layers are READ-ONLY (immutable)                                  │
│   • Layers are SHARED between containers                                    │
│   • Only changed layers rebuild (fast!)                                     │
│   • Container writes go to top layer only                                   │
│                                                                              │
│   LAYER SHARING EXAMPLE:                                                     │
│                                                                              │
│   Container 1          Container 2          Container 3                     │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐                   │
│   │ writable │         │ writable │         │ writable │                   │
│   ├──────────┤         ├──────────┤         ├──────────┤                   │
│   │  app.py  │         │ other.py │         │ test.py  │                   │
│   └────┬─────┘         └────┬─────┘         └────┬─────┘                   │
│        │                    │                    │                          │
│        └────────────────────┼────────────────────┘                          │
│                             ▼                                                │
│              ┌─────────────────────────────┐                                │
│              │  SHARED: python:3.11-slim   │  ← One copy on disk!          │
│              │          pip packages        │                                │
│              │          system tools        │                                │
│              └─────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Control Groups (cgroups) - Resource Limits

Prevent containers from consuming all system resources.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTROL GROUPS (cgroups)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   docker run --memory=256m --cpus=0.5 my-container                          │
│                    │            │                                            │
│                    │            └── Max 50% of one CPU core                 │
│                    └── Max 256MB memory                                      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                        HOST RESOURCES                           │       │
│   │                                                                 │       │
│   │   Memory: 16GB total                                           │       │
│   │   ┌────────────────────────────────────────────────────────┐   │       │
│   │   │████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │       │
│   │   │  Container A: 256MB max                                │   │       │
│   │   └────────────────────────────────────────────────────────┘   │       │
│   │                                                                 │       │
│   │   CPU: 4 cores total                                           │       │
│   │   ┌────────────────────────────────────────────────────────┐   │       │
│   │   │Core 0: ██░░░░░░░░  Container A (50%)                  │   │       │
│   │   │Core 1: ░░░░░░░░░░  Available                          │   │       │
│   │   │Core 2: ░░░░░░░░░░  Available                          │   │       │
│   │   │Core 3: ░░░░░░░░░░  Available                          │   │       │
│   │   └────────────────────────────────────────────────────────┘   │       │
│   │                                                                 │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   WITHOUT CGROUPS:                    WITH CGROUPS:                         │
│   ────────────────                    ─────────────                         │
│   Runaway container uses              Container limited to                  │
│   ALL memory → host crashes           256MB → other containers safe        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## VMs vs Containers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VIRTUAL MACHINES vs CONTAINERS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│        VIRTUAL MACHINES                      CONTAINERS                      │
│   ┌─────────────────────────┐         ┌─────────────────────────┐           │
│   │                         │         │                         │           │
│   │  ┌─────┐┌─────┐┌─────┐ │         │  ┌─────┐┌─────┐┌─────┐ │           │
│   │  │App A││App B││App C│ │         │  │App A││App B││App C│ │           │
│   │  ├─────┤├─────┤├─────┤ │         │  └─────┘└─────┘└─────┘ │           │
│   │  │Guest││Guest││Guest│ │         │  ─────────────────────── │           │
│   │  │ OS  ││ OS  ││ OS  │ │         │    Container Runtime     │           │
│   │  └─────┘└─────┘└─────┘ │         │  ─────────────────────── │           │
│   │  ─────────────────────  │         │        Host OS           │           │
│   │       Hypervisor        │         │       (shared!)          │           │
│   │  ─────────────────────  │         │                         │           │
│   │        Host OS          │         └─────────────────────────┘           │
│   │                         │                                                │
│   └─────────────────────────┘                                                │
│                                                                              │
│   ┌─────────────────────┬───────────────────┬───────────────────┐           │
│   │      Aspect         │        VM         │     Container     │           │
│   ├─────────────────────┼───────────────────┼───────────────────┤           │
│   │ Isolation           │ Full (hardware)   │ Process-level     │           │
│   │ Startup time        │ Minutes           │ Seconds           │           │
│   │ Size                │ GBs               │ MBs               │           │
│   │ OS                  │ Own kernel        │ Shared kernel     │           │
│   │ Performance         │ ~5% overhead      │ ~1% overhead      │           │
│   │ Density             │ 10s per host      │ 100s per host     │           │
│   └─────────────────────┴───────────────────┴───────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Building the Container

### Dockerfile Structure

```dockerfile
# Layer 1: Base image
FROM python:3.11-slim

# Layer 2: System dependencies
RUN apt-get update && apt-get install -y curl

# Layer 3: Working directory
WORKDIR /app

# Layer 4: Python dependencies (cached if unchanged)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Layer 5: Application code
COPY server.py .

# Layer 6: Configuration
ENV SERVER_PORT=8000
EXPOSE 8000

# Layer 7: Health check
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# Layer 8: Entry point
CMD ["python", "server.py"]
```

### Build Commands

```bash
# Build image
docker build -t ds-exercise02 .

# View layers
docker history ds-exercise02

# List images
docker images
```

---

## Running the Container

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER RUN OPTIONS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BASIC RUN:                                                                 │
│   ──────────                                                                │
│   docker run -p 8000:8000 ds-exercise02                                     │
│              │                                                               │
│              └── -p host_port:container_port                                │
│                                                                              │
│   WITH RESOURCE LIMITS (cgroups):                                           │
│   ───────────────────────────────                                           │
│   docker run -p 8000:8000 \                                                 │
│       --memory=256m \                 ← Max memory                          │
│       --cpus=0.5 \                    ← Max CPU                             │
│       ds-exercise02                                                         │
│                                                                              │
│   WITH ENVIRONMENT VARIABLES:                                                │
│   ───────────────────────────                                               │
│   docker run -p 8000:8000 \                                                 │
│       -e SERVER_PORT=8000 \           ← Override ENV                        │
│       -e WORKER_COUNT=8 \                                                   │
│       ds-exercise02                                                         │
│                                                                              │
│   DETACHED MODE:                                                             │
│   ──────────────                                                            │
│   docker run -d -p 8000:8000 ds-exercise02                                  │
│              │                                                               │
│              └── -d runs in background                                      │
│                                                                              │
│   INTERACTIVE MODE:                                                          │
│   ─────────────────                                                         │
│   docker run -it ds-exercise02 /bin/bash                                    │
│              │                                                               │
│              └── -it for interactive terminal                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Container Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTAINER LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐   docker run    ┌─────────┐   SIGTERM     ┌─────────┐        │
│   │ Created │ ───────────────►│ Running │ ─────────────►│ Stopped │        │
│   └─────────┘                 └─────────┘               └─────────┘        │
│        │                           │                         │              │
│        │                           │ docker pause            │              │
│        │                           ▼                         │              │
│        │                      ┌─────────┐                   │              │
│        │                      │ Paused  │                   │              │
│        │                      └─────────┘                   │              │
│        │                                                     │              │
│        └──────────────── docker rm ──────────────────────────┘              │
│                                │                                            │
│                                ▼                                            │
│                          ┌─────────┐                                       │
│                          │ Removed │                                       │
│                          └─────────┘                                       │
│                                                                              │
│   GRACEFUL SHUTDOWN:                                                         │
│   ──────────────────                                                        │
│                                                                              │
│   docker stop my-container                                                  │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────┐                                                           │
│   │  SIGTERM    │  ← "Please shut down nicely"                             │
│   │  sent       │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          │  (10 second grace period)                                        │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────┐                                                           │
│   │  SIGKILL    │  ← "Die immediately!" (if still running)                 │
│   │  sent       │                                                           │
│   └─────────────┘                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Testing the Container

```bash
# Health check
curl http://localhost:8000/health
# Response: {"status": "healthy", "uptime_seconds": 42.5}

# Container info
curl http://localhost:8000/info
# Response: {"hostname": "abc123", "process_id": 1, ...}

# Calculate
curl -X POST \
     -d '{"operation":"add","a":10,"b":5}' \
     http://localhost:8000/calculate
# Response: {"result": 15, "processed_by": "abc123"}
```

---

## Container-Friendly Design Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTAINER-FRIENDLY DESIGN PATTERNS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. ENVIRONMENT VARIABLES for configuration                                │
│   ───────────────────────────────────────────                               │
│      ✓ No hardcoded values                                                  │
│      ✓ Change settings without rebuilding                                   │
│      ✓ Different config for dev/staging/prod                                │
│                                                                              │
│   2. HEALTH ENDPOINTS for orchestration                                     │
│   ─────────────────────────────────────                                     │
│      ✓ Kubernetes/Docker Swarm checks /health                              │
│      ✓ Automatic restart on failure                                         │
│      ✓ Load balancer integration                                            │
│                                                                              │
│   3. GRACEFUL SHUTDOWN on SIGTERM                                           │
│   ─────────────────────────────────                                         │
│      ✓ Finish in-flight requests                                           │
│      ✓ Close database connections                                          │
│      ✓ Release resources cleanly                                           │
│                                                                              │
│   4. LOGGING TO STDOUT                                                      │
│   ────────────────────                                                      │
│      ✓ docker logs captures stdout                                         │
│      ✓ Centralized logging systems expect stdout                           │
│      ✓ Container filesystem is ephemeral!                                  │
│                                                                              │
│   5. STATELESS DESIGN                                                       │
│   ───────────────────                                                       │
│      ✓ Store state in external services (Redis, DB)                        │
│      ✓ Containers can be replaced anytime                                  │
│      ✓ Horizontal scaling works                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KEY TAKEAWAYS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. CONTAINERS = Namespaces + Union FS + Cgroups                          │
│      • Namespaces provide isolation                                         │
│      • Union FS provides efficient layered storage                         │
│      • Cgroups provide resource limits                                      │
│                                                                              │
│   2. CONTAINERS ≠ VMs                                                       │
│      • Share host kernel (lighter weight)                                   │
│      • Start in seconds (not minutes)                                       │
│      • MBs instead of GBs                                                   │
│                                                                              │
│   3. IMAGES are built in LAYERS                                             │
│      • Layers are cached and shared                                         │
│      • Put frequently changing code last                                    │
│      • Optimize for cache hits                                              │
│                                                                              │
│   4. DESIGN for containers                                                   │
│      • Configure via environment variables                                  │
│      • Log to stdout                                                        │
│      • Handle SIGTERM gracefully                                            │
│      • Expose health endpoints                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
