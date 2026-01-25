"""
================================================================================
Part 4: Containerized Server - SOLUTION
================================================================================

A simple server designed to run in a Docker container.
Demonstrates container-friendly design patterns.

================================================================================
WHAT MAKES A SERVER "CONTAINER-FRIENDLY"?
================================================================================

Containers are like lightweight VMs, but share the host kernel.
A container-friendly server should:

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                  CONTAINER-FRIENDLY DESIGN PRINCIPLES                   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │  1. ENVIRONMENT VARIABLES for configuration                            │
    │     ───────────────────────────────────────                            │
    │     • No hardcoded values                                              │
    │     • docker run -e SERVER_PORT=8080 my-container                     │
    │     • Easy to change without rebuilding                                │
    │                                                                         │
    │  2. HEALTH ENDPOINTS for orchestration                                 │
    │     ──────────────────────────────────                                 │
    │     • Kubernetes, Docker Swarm need to check if app is alive          │
    │     • GET /health returns status                                       │
    │     • Enables automatic restart on failure                             │
    │                                                                         │
    │  3. GRACEFUL SHUTDOWN on SIGTERM                                       │
    │     ────────────────────────────────                                   │
    │     • Docker sends SIGTERM before SIGKILL                             │
    │     • Finish current requests, clean up resources                      │
    │     • Don't lose data!                                                 │
    │                                                                         │
    │  4. LOGGING TO STDOUT                                                  │
    │     ─────────────────────                                              │
    │     • Don't write to files (ephemeral filesystem!)                    │
    │     • docker logs my-container captures stdout                        │
    │     • Centralized logging systems expect stdout                        │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘

================================================================================
CONTAINER ARCHITECTURE
================================================================================

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           HOST MACHINE                                  │
    │                                                                         │
    │    ┌─────────────────────────────────────────────────────────────┐     │
    │    │                    DOCKER CONTAINER                         │     │
    │    │                                                             │     │
    │    │   ┌─────────────────────────────────────────────────────┐   │     │
    │    │   │              ContainerizedServer                    │   │     │
    │    │   │                                                     │   │     │
    │    │   │  Environment:                                       │   │     │
    │    │   │    SERVER_HOST=0.0.0.0                              │   │     │
    │    │   │    SERVER_PORT=8000     ◄── From docker run -e     │   │     │
    │    │   │    WORKER_COUNT=4                                   │   │     │
    │    │   │                                                     │   │     │
    │    │   │  Endpoints:                                         │   │     │
    │    │   │    GET /health   ──► {"status": "healthy"}         │   │     │
    │    │   │    GET /info     ──► {"hostname": "abc123"}        │   │     │
    │    │   │    POST /calculate ──► {"result": 15}              │   │     │
    │    │   │                                                     │   │     │
    │    │   └─────────────────────────────────────────────────────┘   │     │
    │    │                          │                                  │     │
    │    │                          │ :8000                            │     │
    │    │                          ▼                                  │     │
    │    └──────────────────────────┼──────────────────────────────────┘     │
    │                               │                                        │
    │                               │ -p 8000:8000 (port mapping)           │
    │                               ▼                                        │
    │                    Host port 8000                                      │
    └─────────────────────────────────────────────────────────────────────────┘

================================================================================
CONTAINER vs VIRTUAL MACHINE
================================================================================

    ┌─────────────────────────────────┐    ┌─────────────────────────────────┐
    │        VIRTUAL MACHINES         │    │          CONTAINERS             │
    ├─────────────────────────────────┤    ├─────────────────────────────────┤
    │                                 │    │                                 │
    │  ┌─────┐ ┌─────┐ ┌─────┐       │    │  ┌─────┐ ┌─────┐ ┌─────┐       │
    │  │App A│ │App B│ │App C│       │    │  │App A│ │App B│ │App C│       │
    │  ├─────┤ ├─────┤ ├─────┤       │    │  └─────┘ └─────┘ └─────┘       │
    │  │Guest│ │Guest│ │Guest│       │    │  ─────────────────────────      │
    │  │ OS  │ │ OS  │ │ OS  │       │    │     Container Runtime          │
    │  └─────┘ └─────┘ └─────┘       │    │  ─────────────────────────      │
    │  ─────────────────────────      │    │         Host OS                │
    │        Hypervisor               │    │        (shared!)               │
    │  ─────────────────────────      │    │                                 │
    │         Host OS                 │    │                                 │
    │                                 │    │                                 │
    ├─────────────────────────────────┤    ├─────────────────────────────────┤
    │  • Full OS per VM               │    │  • Shared kernel                │
    │  • GB of memory                 │    │  • MB of memory                 │
    │  • Minutes to start             │    │  • Seconds to start             │
    │  • Strong isolation             │    │  • Process-level isolation      │
    └─────────────────────────────────┘    └─────────────────────────────────┘

================================================================================
CONTAINER BUILDING BLOCKS
================================================================================

    1. NAMESPACES (Isolation)
    ─────────────────────────
    
        ┌───────────────────────────────────────────────────────────────┐
        │                       HOST SYSTEM                             │
        │                                                               │
        │  ┌─────────────────────┐    ┌─────────────────────┐          │
        │  │    Container A      │    │    Container B      │          │
        │  │                     │    │                     │          │
        │  │  PID namespace:     │    │  PID namespace:     │          │
        │  │    PID 1 (init)     │    │    PID 1 (init)     │ ← Same!  │
        │  │    PID 2 (app)      │    │    PID 2 (app)      │          │
        │  │                     │    │                     │          │
        │  │  Network namespace: │    │  Network namespace: │          │
        │  │    eth0, localhost  │    │    eth0, localhost  │ ← Own!   │
        │  │                     │    │                     │          │
        │  └─────────────────────┘    └─────────────────────┘          │
        │                                                               │
        │  Real PIDs: 5432, 5433        Real PIDs: 6789, 6790         │
        │  (Host sees different PIDs than containers!)                 │
        └───────────────────────────────────────────────────────────────┘
    
    2. UNION FILESYSTEM (Layers)
    ────────────────────────────
    
              Container Layer (writable) ◄── Your changes
                     ↑
        ┌──────────────────────────────────────────────┐
        │     Layer 4: COPY server.py                  │ ◄── Your code
        ├──────────────────────────────────────────────┤
        │     Layer 3: pip install                     │ ◄── Dependencies
        ├──────────────────────────────────────────────┤
        │     Layer 2: apt-get install curl            │ ◄── System tools
        ├──────────────────────────────────────────────┤
        │     Layer 1: python:3.11-slim                │ ◄── Base image
        └──────────────────────────────────────────────┘
        
        • Read-only layers are SHARED between containers!
        • Only top layer is writable
        • Very efficient storage
    
    3. CGROUPS (Resource Limits)
    ────────────────────────────
    
        docker run --memory=256m --cpus=0.5 my-container
                        │            │
                        │            └── Max 50% of one CPU
                        └── Max 256MB memory
        
        Prevents one container from consuming all resources!

================================================================================
"""

import socket
import json
import threading
import os
import signal
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


class ContainerizedServer:
    """
    Server designed for container deployment.
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                   CONTAINERIZED SERVER ARCHITECTURE                     │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                         │
    │   ┌─────────────────────────────────────────────────────────────────┐   │
    │   │                    ENVIRONMENT VARIABLES                        │   │
    │   │   SERVER_HOST ──► "0.0.0.0" (listen on all interfaces)         │   │
    │   │   SERVER_PORT ──► 8000                                          │   │
    │   │   WORKER_COUNT ──► 4 (thread pool size)                        │   │
    │   └─────────────────────────────────────────────────────────────────┘   │
    │                              │                                          │
    │                              ▼                                          │
    │   ┌─────────────────────────────────────────────────────────────────┐   │
    │   │                     SIGNAL HANDLERS                             │   │
    │   │   SIGTERM ──► graceful_shutdown()                              │   │
    │   │   SIGINT  ──► graceful_shutdown()  (Ctrl+C)                    │   │
    │   └─────────────────────────────────────────────────────────────────┘   │
    │                              │                                          │
    │                              ▼                                          │
    │   ┌─────────────────────────────────────────────────────────────────┐   │
    │   │                     REQUEST ROUTING                             │   │
    │   │                                                                 │   │
    │   │   GET /health    ──► health_check()    (for orchestration)     │   │
    │   │   GET /info      ──► container_info()  (debug/monitoring)      │   │
    │   │   POST /calculate ──► calculate()      (actual work)           │   │
    │   │   GET /          ──► endpoint_list()   (API discovery)         │   │
    │   │                                                                 │   │
    │   └─────────────────────────────────────────────────────────────────┘   │
    │                              │                                          │
    │                              ▼                                          │
    │   ┌─────────────────────────────────────────────────────────────────┐   │
    │   │                     THREAD POOL                                 │   │
    │   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
    │   │   │Worker 0 │ │Worker 1 │ │Worker 2 │ │Worker 3 │              │   │
    │   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘              │   │
    │   │                                                                 │   │
    │   │   Bounded pool prevents resource exhaustion                    │   │
    │   └─────────────────────────────────────────────────────────────────┘   │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    
    Container-friendly features:
    ────────────────────────────
    ✓ Environment variable configuration (no hardcoded values)
    ✓ Health check endpoint (/health) for orchestration
    ✓ Graceful shutdown on SIGTERM (clean exit)
    ✓ Logging to stdout (for `docker logs`)
    ✓ Process ID and hostname reporting (debugging)
    """
    
    def __init__(self):
        """
        Initialize server from environment variables.
        
        Environment variable configuration:
        ────────────────────────────────────
        
            ┌────────────────────────────────────────────────────────────┐
            │                CONFIGURATION SOURCES                       │
            ├────────────────────────────────────────────────────────────┤
            │                                                            │
            │   Dockerfile:                                              │
            │     ENV SERVER_HOST=0.0.0.0                                │
            │     ENV SERVER_PORT=8000      ◄── Defaults                │
            │     ENV WORKER_COUNT=4                                     │
            │                                                            │
            │   docker run:                                              │
            │     -e SERVER_PORT=9000       ◄── Override at runtime    │
            │     -e WORKER_COUNT=8                                      │
            │                                                            │
            │   Code reads with fallback:                                │
            │     os.environ.get('SERVER_PORT', '8000')                 │
            │                     │            │                        │
            │                     │            └── Default if not set   │
            │                     └── Check environment                  │
            │                                                            │
            └────────────────────────────────────────────────────────────┘
        
        Why 0.0.0.0 for host?
        ─────────────────────
            • "localhost" only accepts connections from inside container
            • "0.0.0.0" accepts connections from host (via port mapping)
            • Required for -p 8000:8000 to work!
        """
        # ─────────────────────────────────────────────────────────────────────
        # Read configuration from environment (container-friendly!)
        # ─────────────────────────────────────────────────────────────────────
        self.host = os.environ.get('SERVER_HOST', '0.0.0.0')
        self.port = int(os.environ.get('SERVER_PORT', '8000'))
        self.worker_count = int(os.environ.get('WORKER_COUNT', '4'))
        
        # Server state
        self.running = False
        self.request_count = 0
        self.start_time = None
        
        # ─────────────────────────────────────────────────────────────────────
        # Setup signal handlers for graceful shutdown
        # ─────────────────────────────────────────────────────────────────────
        #
        #   Docker stop lifecycle:
        #   ──────────────────────
        #
        #       docker stop my-container
        #              │
        #              ▼
        #       ┌─────────────┐
        #       │  SIGTERM    │  ◄── "Please shut down nicely"
        #       │  sent       │
        #       └──────┬──────┘
        #              │
        #              │  (10 seconds grace period by default)
        #              │
        #              ▼
        #       ┌─────────────┐
        #       │  SIGKILL    │  ◄── "Die immediately!" (if still running)
        #       │  sent       │
        #       └─────────────┘
        #
        #   We catch SIGTERM to shutdown gracefully!
        #
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)  # Also Ctrl+C
    
    def log(self, message):
        """
        Log to stdout (docker logs can capture this).
        
        Why stdout for containers?
        ──────────────────────────
        
            Traditional:                    Container-friendly:
            ────────────                    ────────────────────
            
            log to file ──► /var/log/       log to stdout ──► docker logs
                            app.log                           │
                               │                              ▼
                               │                        ┌─────────────┐
                               ▼                        │ Centralized │
                        (lost when                      │ Logging     │
                         container                      │ (ELK, etc.) │
                         restarts!)                     └─────────────┘
        
        Container filesystems are EPHEMERAL - files are lost on restart!
        stdout is captured by Docker and can be aggregated.
        """
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {message}", flush=True)  # flush=True for immediate output
    
    def handle_shutdown(self, signum, frame):
        """
        Handle SIGTERM/SIGINT for graceful shutdown.
        
        Graceful vs Immediate shutdown:
        ───────────────────────────────
        
            IMMEDIATE (bad):              GRACEFUL (good):
            ────────────────              ────────────────
            
            Request in progress           Request in progress
                  │                             │
            SIGKILL                        SIGTERM
                  │                             │
                  ▼                             ▼
            ┌─────────────┐              ┌─────────────┐
            │ Process     │              │ Set running │
            │ killed!     │              │ = False     │
            │             │              └──────┬──────┘
            │ Request     │                     │
            │ incomplete! │              ┌──────┴──────┐
            └─────────────┘              │ Finish      │
                                         │ current     │
                                         │ requests    │
                                         └──────┬──────┘
                                                │
                                         ┌──────┴──────┐
                                         │ Clean       │
                                         │ shutdown    │
                                         └─────────────┘
        
        Parameters:
        ───────────
        signum : int   - Signal number (15 for SIGTERM, 2 for SIGINT)
        frame  : frame - Current stack frame (unused)
        """
        self.log(f"Received signal {signum}, shutting down gracefully...")
        self.running = False  # This will cause main loop to exit
    
    def handle_client(self, client_socket, address):
        """
        Handle a client request.
        
        HTTP-like request routing:
        ──────────────────────────
        
            Incoming Request
                   │
                   ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                      ROUTER                                 │
            │                                                             │
            │  GET /health     ──────────────►  health_check()           │
            │                                   Return: {status, uptime}  │
            │                                                             │
            │  GET /info       ──────────────►  container_info()         │
            │                                   Return: {hostname, pid}   │
            │                                                             │
            │  POST /calculate ──────────────►  calculate()              │
            │                                   Return: {result}          │
            │                                                             │
            │  GET /           ──────────────►  endpoint_list()          │
            │  (default)                        Return: {endpoints}       │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        """
        try:
            data = client_socket.recv(1024).decode()
            
            if not data:
                return
            
            # Parse simple HTTP-like request
            lines = data.split('\n')
            request_line = lines[0] if lines else ''
            
            self.request_count += 1
            
            # ─────────────────────────────────────────────────────────────────
            # Route request to appropriate handler
            # ─────────────────────────────────────────────────────────────────
            if 'GET /health' in request_line:
                # Health endpoint for orchestration (Kubernetes, Docker Swarm)
                response = self.health_check()
                
            elif 'GET /info' in request_line:
                # Debug endpoint showing container environment
                response = self.container_info()
                
            elif 'POST /calculate' in request_line:
                # Actual application logic
                body = lines[-1] if lines else '{}'
                try:
                    request = json.loads(body)
                    response = self.calculate(request)
                except json.JSONDecodeError:
                    response = {'error': 'Invalid JSON'}
                    
            else:
                # Default: show available endpoints (API discovery)
                response = {
                    'endpoints': [
                        'GET /health - Health check for orchestration',
                        'GET /info - Container environment info',
                        'POST /calculate - Calculator API'
                    ]
                }
            
            # ─────────────────────────────────────────────────────────────────
            # Send HTTP response
            # ─────────────────────────────────────────────────────────────────
            response_body = json.dumps(response, indent=2)
            http_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "\r\n"
                f"{response_body}"
            )
            client_socket.send(http_response.encode())
            
            # Log to stdout (captured by docker logs)
            self.log(f"Request from {address[0]}: {request_line.strip()}")
            
        except Exception as e:
            self.log(f"Error handling request: {e}")
        finally:
            client_socket.close()
    
    def health_check(self):
        """
        Health check endpoint for container orchestration.
        
        Why health checks matter:
        ─────────────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                    ORCHESTRATION FLOW                       │
            │                                                             │
            │   Kubernetes/Docker Swarm                                   │
            │          │                                                  │
            │          │  GET /health                                     │
            │          │  (every 30 seconds)                              │
            │          ▼                                                  │
            │   ┌─────────────┐                                          │
            │   │  Container  │                                          │
            │   │  responds   │                                          │
            │   │  "healthy"  │                                          │
            │   └──────┬──────┘                                          │
            │          │                                                  │
            │          ▼                                                  │
            │   ┌─────────────────────────────────────────┐              │
            │   │  Response OK?                           │              │
            │   │                                         │              │
            │   │  YES ──► Keep container running        │              │
            │   │                                         │              │
            │   │  NO  ──► Restart container             │              │
            │   │          (after retry threshold)        │              │
            │   └─────────────────────────────────────────┘              │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        
        Dockerfile configuration:
        ─────────────────────────
            HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
                CMD curl -f http://localhost:8000/health || exit 1
        
        Returns:
        ────────
        dict : {status, uptime_seconds, requests_handled}
        """
        return {
            'status': 'healthy',
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'requests_handled': self.request_count
        }
    
    def container_info(self):
        """
        Return information about the container environment.
        
        Useful for:
        ───────────
        • Debugging which container handled a request
        • Verifying environment variable configuration
        • Checking resource allocation
        
        Container identification:
        ─────────────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                    LOAD BALANCER                            │
            │                         │                                   │
            │              ┌──────────┼──────────┐                       │
            │              ▼          ▼          ▼                       │
            │         ┌────────┐ ┌────────┐ ┌────────┐                   │
            │         │abc123  │ │def456  │ │ghi789  │ ◄── HOSTNAME     │
            │         │        │ │        │ │        │                   │
            │         │Worker 1│ │Worker 2│ │Worker 3│                   │
            │         └────────┘ └────────┘ └────────┘                   │
            │                                                             │
            │   /info response tells you WHICH container you're in!      │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        
        Returns:
        ────────
        dict : Container environment details
        """
        return {
            'hostname': os.environ.get('HOSTNAME', socket.gethostname()),
            'server_host': self.host,
            'server_port': self.port,
            'worker_count': self.worker_count,
            'process_id': os.getpid(),
            'python_version': sys.version,
            'environment': {
                'SERVER_HOST': os.environ.get('SERVER_HOST', 'not set'),
                'SERVER_PORT': os.environ.get('SERVER_PORT', 'not set'),
                'WORKER_COUNT': os.environ.get('WORKER_COUNT', 'not set')
            }
        }
    
    def calculate(self, request):
        """
        Simple calculator - the actual application logic.
        
        Request format:
        ───────────────
            {
                "operation": "add" | "multiply" | "subtract",
                "a": <number>,
                "b": <number>
            }
        
        Response format:
        ────────────────
            {
                "operation": "add",
                "a": 10,
                "b": 5,
                "result": 15,
                "processed_by": "abc123"  ◄── Container hostname!
            }
        
        The processed_by field shows which container handled the request.
        Useful for debugging load balancing!
        """
        operation = request.get('operation', 'add')
        a = request.get('a', 0)
        b = request.get('b', 0)
        
        if operation == 'add':
            result = a + b
        elif operation == 'multiply':
            result = a * b
        elif operation == 'subtract':
            result = a - b
        else:
            return {'error': f'Unknown operation: {operation}'}
        
        return {
            'operation': operation,
            'a': a,
            'b': b,
            'result': result,
            'processed_by': os.environ.get('HOSTNAME', 'unknown')
        }
    
    def start(self):
        """
        Start the server.
        
        Server startup sequence:
        ────────────────────────
        
            ┌─────────────────────────────────────────────────────────────┐
            │                    STARTUP SEQUENCE                         │
            ├─────────────────────────────────────────────────────────────┤
            │                                                             │
            │  1. Create server socket                                    │
            │     └── socket(AF_INET, SOCK_STREAM)                       │
            │                                                             │
            │  2. Bind to address                                         │
            │     └── bind((0.0.0.0, 8000))                              │
            │                                                             │
            │  3. Start listening                                         │
            │     └── listen(backlog=10)                                 │
            │                                                             │
            │  4. Log startup info                                        │
            │     └── (captured by docker logs)                          │
            │                                                             │
            │  5. Create thread pool                                      │
            │     └── ThreadPoolExecutor(max_workers=4)                  │
            │                                                             │
            │  6. Accept loop                                             │
            │     └── while self.running:                                │
            │           accept() → submit to pool                        │
            │                                                             │
            │  7. Shutdown (when SIGTERM received)                       │
            │     └── Close socket, exit cleanly                         │
            │                                                             │
            └─────────────────────────────────────────────────────────────┘
        """
        self.running = True
        self.start_time = time.time()
        
        # Create and configure socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        server_socket.settimeout(1)  # Allow checking self.running
        
        # Log startup info (captured by docker logs)
        self.log(f"Server starting on {self.host}:{self.port}")
        self.log(f"Worker threads: {self.worker_count}")
        self.log(f"Process ID: {os.getpid()}")
        self.log(f"Hostname: {os.environ.get('HOSTNAME', socket.gethostname())}")
        
        # Use thread pool for bounded concurrency
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    executor.submit(self.handle_client, client_socket, address)
                except socket.timeout:
                    continue  # Check if still running
        
        server_socket.close()
        self.log("Server stopped")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         CONTAINERIZED SERVER                                 ║
║                       Container-Friendly Design                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

    This server demonstrates container-friendly design patterns:

    ┌─────────────────────────────────────────────────────────────────────┐
    │  CONTAINER-FRIENDLY FEATURES                                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  1. Environment variable configuration                             │
    │     └── Change settings without rebuilding image                   │
    │                                                                     │
    │  2. Health check endpoint (/health)                                │
    │     └── Kubernetes/Docker can monitor and restart                  │
    │                                                                     │
    │  3. Graceful shutdown on SIGTERM                                   │
    │     └── Finish requests before exiting                             │
    │                                                                     │
    │  4. Logging to stdout                                              │
    │     └── Captured by 'docker logs'                                  │
    │                                                                     │
    │  5. Container info endpoint (/info)                                │
    │     └── Debug which container handled request                      │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  DOCKER COMMANDS                                                    │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  Build:                                                            │
    │    docker build -t ds-server .                                     │
    │                                                                     │
    │  Run:                                                              │
    │    docker run -p 8000:8000 ds-server                              │
    │                                                                     │
    │  Run with resource limits (cgroups):                               │
    │    docker run -p 8000:8000 --memory=256m --cpus=0.5 ds-server     │
    │                                                                     │
    │  Run with custom config:                                           │
    │    docker run -p 9000:9000 \\                                      │
    │        -e SERVER_PORT=9000 \\                                      │
    │        -e WORKER_COUNT=8 \\                                        │
    │        ds-server                                                   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  TEST COMMANDS                                                      │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  Health check:                                                     │
    │    curl http://localhost:8000/health                               │
    │                                                                     │
    │  Container info:                                                   │
    │    curl http://localhost:8000/info                                 │
    │                                                                     │
    │  Calculate:                                                        │
    │    curl -X POST \\                                                  │
    │         -d '{"operation":"add","a":10,"b":5}' \\                   │
    │         http://localhost:8000/calculate                            │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    """)
    
    server = ContainerizedServer()
    server.start()
