# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    Part 4: Containerization                               ║
# ║                                                                           ║
# ║  This Dockerfile demonstrates container concepts from the lecture:        ║
# ║  • Namespaces: Process isolation                                          ║
# ║  • Union filesystem: Layered file system                                  ║
# ║  • Control groups (cgroups): Resource limits                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                       DOCKERFILE OVERVIEW                                   │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │                                                                             │
# │   Each instruction creates a LAYER in the image:                           │
# │                                                                             │
# │         Container Layer (writable at runtime)                              │
# │                     ↑                                                       │
# │   ┌─────────────────────────────────────────┐                              │
# │   │  Layer 9: CMD (entry point)             │                              │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 8: HEALTHCHECK                   │                              │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 7: ENV, EXPOSE                   │                              │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 6: COPY server.py                │  ◄── Your application       │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 5: pip install                   │  ◄── Python dependencies    │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 4: COPY requirements.txt         │                              │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 3: WORKDIR /app                  │                              │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 2: RUN apt-get (curl)            │  ◄── System tools           │
# │   ├─────────────────────────────────────────┤                              │
# │   │  Layer 1: python:3.11-slim              │  ◄── Base image             │
# │   └─────────────────────────────────────────┘                              │
# │                                                                             │
# │   • Lower layers are READ-ONLY and CACHED                                  │
# │   • Only changed layers get rebuilt                                        │
# │   • Layers are SHARED between containers (efficient!)                      │
# │                                                                             │
# └─────────────────────────────────────────────────────────────────────────────┘


# =============================================================================
# LAYER 1: Base Image
# =============================================================================
#
#   This is the foundation layer - a minimal Linux with Python installed.
#
#   Why python:3.11-slim?
#   ─────────────────────
#   • "slim" = minimal Debian without extra packages (~45MB vs ~350MB)
#   • Smaller image = faster download, less attack surface
#   • Still has everything needed to run Python
#
#   Image hierarchy:
#   ────────────────
#       scratch (empty)
#           └── debian:bookworm-slim
#                   └── python:3.11-slim  ◄── We start here
#
FROM python:3.11-slim


# =============================================================================
# LAYER 2: Metadata (Labels)
# =============================================================================
#
#   Labels add metadata to the image. Visible with:
#       docker inspect ds-exercise02
#
#   Common labels:
#   ──────────────
#   • maintainer    - Who to contact
#   • version       - Image version
#   • description   - What this image does
#
LABEL maintainer="DS Course 2025"
LABEL description="Distributed Systems Exercise 02 - Process Concepts"
LABEL lecture="Lecture 3: Processes"


# =============================================================================
# LAYER 3: System Dependencies
# =============================================================================
#
#   Install system packages needed by the application.
#
#   Best practices:
#   ───────────────
#   • Combine commands with && to reduce layers
#   • Clean up cache to reduce image size
#   • Use --no-install-recommends to minimize packages
#
#   ┌────────────────────────────────────────────────────────────────────────┐
#   │  Without cleanup:        With cleanup:                                 │
#   │  ────────────────        ─────────────                                 │
#   │                                                                        │
#   │  apt-get update          apt-get update && \                          │
#   │  apt-get install curl    apt-get install curl && \                    │
#   │                          rm -rf /var/lib/apt/lists/*                  │
#   │                                                                        │
#   │  Layer: ~50MB            Layer: ~5MB                                  │
#   └────────────────────────────────────────────────────────────────────────┘
#
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*


# =============================================================================
# LAYER 4: Working Directory
# =============================================================================
#
#   Set the working directory inside the container.
#   All subsequent commands run from this directory.
#
#   Container filesystem:
#   ─────────────────────
#       /
#       ├── bin/
#       ├── etc/
#       ├── home/
#       ├── usr/
#       └── app/          ◄── WORKDIR creates this
#           ├── requirements.txt
#           └── server.py
#
WORKDIR /app


# =============================================================================
# LAYER 5: Python Dependencies
# =============================================================================
#
#   Copy requirements.txt FIRST, then install.
#   This enables Docker's layer caching!
#
#   Why separate COPY for requirements?
#   ────────────────────────────────────
#
#   ┌────────────────────────────────────────────────────────────────────────┐
#   │                      LAYER CACHING                                     │
#   │                                                                        │
#   │   If code changes but requirements don't:                             │
#   │                                                                        │
#   │   ┌─────────────────────────────┐                                      │
#   │   │ COPY requirements.txt       │  ◄── CACHED (unchanged)             │
#   │   ├─────────────────────────────┤                                      │
#   │   │ RUN pip install             │  ◄── CACHED (unchanged)             │
#   │   ├─────────────────────────────┤                                      │
#   │   │ COPY server.py              │  ◄── REBUILT (changed)              │
#   │   └─────────────────────────────┘                                      │
#   │                                                                        │
#   │   Only the last layer needs rebuilding!                               │
#   │   (pip install can take minutes - caching saves time)                 │
#   │                                                                        │
#   └────────────────────────────────────────────────────────────────────────┘
#
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =============================================================================
# LAYER 6: Application Code
# =============================================================================
#
#   Copy your application files into the container.
#   This layer changes most frequently, so it's LAST.
#
#   COPY syntax:
#   ────────────
#       COPY <src> <dest>
#       COPY server.py .     # Copy to WORKDIR (/app/server.py)
#       COPY . .             # Copy everything (less efficient caching)
#
COPY server.py .


# =============================================================================
# LAYER 7: Configuration
# =============================================================================
#
#   Environment variables configure the application.
#   Can be overridden at runtime with: docker run -e VAR=value
#
#   ┌────────────────────────────────────────────────────────────────────────┐
#   │                   ENVIRONMENT VARIABLE FLOW                            │
#   │                                                                        │
#   │   Dockerfile:                                                          │
#   │     ENV SERVER_PORT=8000        ◄── Default value                     │
#   │                                                                        │
#   │   docker run -e SERVER_PORT=9000   ◄── Override at runtime           │
#   │                                                                        │
#   │   Python code:                                                         │
#   │     port = os.environ.get('SERVER_PORT', '8000')                      │
#   │                                │            │                         │
#   │                                │            └── Fallback              │
#   │                                └── Gets 9000 (from runtime)           │
#   │                                                                        │
#   └────────────────────────────────────────────────────────────────────────┘
#
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV WORKER_COUNT=4

#
#   EXPOSE documents which port the container listens on.
#   NOTE: This is documentation only! It doesn't actually open the port.
#   You still need: docker run -p 8000:8000
#
#   Port mapping:
#   ─────────────
#       docker run -p <host_port>:<container_port>
#       docker run -p 8080:8000
#                     │     │
#                     │     └── Container's internal port
#                     └── Port on your machine
#
EXPOSE 8000


# =============================================================================
# LAYER 8: Health Check
# =============================================================================
#
#   Define how Docker checks if the container is healthy.
#   Used by orchestrators (Kubernetes, Docker Swarm) for auto-restart.
#
#   ┌────────────────────────────────────────────────────────────────────────┐
#   │                      HEALTH CHECK FLOW                                 │
#   │                                                                        │
#   │   ┌──────────┐     ┌──────────────────────────────────────────────┐   │
#   │   │  Docker  │     │  Every 30 seconds (--interval):             │   │
#   │   │  Daemon  │────►│    curl -f http://localhost:8000/health      │   │
#   │   └──────────┘     │                                              │   │
#   │        ▲           │  If fails 3 times (--retries):               │   │
#   │        │           │    Container marked "unhealthy"              │   │
#   │        │           │                                              │   │
#   │        │           │  Orchestrator can then restart container     │   │
#   │        │           └──────────────────────────────────────────────┘   │
#   │        │                                                              │
#   │   ┌────┴─────┐                                                        │
#   │   │ healthy  │  ──► Container keeps running                          │
#   │   │ unhealthy│  ──► Orchestrator restarts                            │
#   │   └──────────┘                                                        │
#   │                                                                        │
#   └────────────────────────────────────────────────────────────────────────┘
#
#   Parameters:
#   ───────────
#   --interval=30s     Check every 30 seconds
#   --timeout=3s       Wait max 3 seconds for response
#   --start-period=5s  Wait 5 seconds before first check (app startup)
#   --retries=3        Mark unhealthy after 3 consecutive failures
#
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1


# =============================================================================
# LAYER 9: Entry Point
# =============================================================================
#
#   CMD specifies what command runs when the container starts.
#
#   CMD vs ENTRYPOINT:
#   ──────────────────
#   • CMD can be overridden:      docker run myimage python other.py
#   • ENTRYPOINT is fixed:        docker run myimage (always runs entrypoint)
#
#   Exec form vs Shell form:
#   ────────────────────────
#   CMD ["python", "server.py"]   ◄── Exec form (recommended)
#   CMD python server.py          ◄── Shell form (runs in /bin/sh -c)
#
#   Exec form is preferred because:
#   • Signals (SIGTERM) go directly to the process
#   • No shell overhead
#   • More predictable behavior
#
CMD ["python", "server.py"]


# =============================================================================
# BUILD & RUN INSTRUCTIONS
# =============================================================================
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                           DOCKER COMMANDS                                   │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │                                                                             │
# │  BUILD IMAGE:                                                              │
# │  ────────────                                                              │
# │    docker build -t ds-exercise02 .                                         │
# │                  │                │                                        │
# │                  │                └── Context (current directory)          │
# │                  └── Tag (name) the image                                  │
# │                                                                             │
# │  VIEW LAYERS:                                                              │
# │  ────────────                                                              │
# │    docker history ds-exercise02                                            │
# │                                                                             │
# │  RUN CONTAINER:                                                            │
# │  ──────────────                                                            │
# │    docker run -p 8000:8000 ds-exercise02                                   │
# │               │                                                            │
# │               └── Map host:container ports                                 │
# │                                                                             │
# │  RUN WITH RESOURCE LIMITS (cgroups):                                       │
# │  ───────────────────────────────────                                       │
# │    docker run -p 8000:8000 \                                               │
# │        --memory=256m \        ◄── Max 256MB memory                        │
# │        --cpus=0.5 \           ◄── Max 50% of one CPU                      │
# │        ds-exercise02                                                       │
# │                                                                             │
# │  RUN WITH CUSTOM CONFIG:                                                   │
# │  ───────────────────────                                                   │
# │    docker run -p 9000:9000 \                                               │
# │        -e SERVER_PORT=9000 \  ◄── Override environment                    │
# │        -e WORKER_COUNT=8 \                                                 │
# │        ds-exercise02                                                       │
# │                                                                             │
# │  VIEW LOGS:                                                                │
# │  ──────────                                                                │
# │    docker logs <container_id>                                              │
# │    docker logs -f <container_id>   ◄── Follow (tail -f style)            │
# │                                                                             │
# │  EXEC INTO CONTAINER:                                                      │
# │  ────────────────────                                                      │
# │    docker exec -it <container_id> /bin/bash                                │
# │                                                                             │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                           TEST ENDPOINTS                                    │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │                                                                             │
# │  Health check:                                                             │
# │    curl http://localhost:8000/health                                       │
# │                                                                             │
# │  Container info:                                                           │
# │    curl http://localhost:8000/info                                         │
# │                                                                             │
# │  Calculate:                                                                │
# │    curl -X POST \                                                          │
# │         -d '{"operation":"add","a":10,"b":5}' \                           │
# │         http://localhost:8000/calculate                                    │
# │                                                                             │
# └─────────────────────────────────────────────────────────────────────────────┘
