"""STUDENT: API Gateway - Port 8000 - Routes to microservices"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Calculator Gateway")

ADD_SERVICE_URL = os.getenv("ADD_SERVICE_URL", "http://localhost:5001")
MULTIPLY_SERVICE_URL = os.getenv("MULTIPLY_SERVICE_URL", "http://localhost:5002")

class CalcRequest(BaseModel):
    a: float
    b: float

@app.post("/add")
async def add(req: CalcRequest):
    """TODO: Forward to ADD_SERVICE_URL/add using httpx"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ADD_SERVICE_URL}/add", json={"a": req.a, "b": req.b})
        return response.json()
    pass

@app.post("/multiply")
async def multiply(req: CalcRequest):
    """TODO: Forward to MULTIPLY_SERVICE_URL/multiply"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MULTIPLY_SERVICE_URL}/multiply", json={"a": req.a, "b": req.b})
        return response.json()
    
    pass

@app.get("/health")
async def health():
    """TODO: Check health of all services, return {"gateway": "healthy", "add_service": ..., "multiply_service": ...}"""
    async with httpx.AsyncClient() as client: 
        results = { "gateway": "healthy", "add_service": "unreachable", "multiply_service": "unreachable", } 
        # Check ADD service 
        try: 
            r1 = await client.get(f"{ADD_SERVICE_URL}/health", timeout=2) 
            results["add_service"] = r1.json().get("status", "unknown") 
        except Exception: 
            results["add_service"] = "unreachable" 
        # Check MULTIPLY service
        try: 
            r2 = await client.get(f"{MULTIPLY_SERVICE_URL}/health", timeout=2) 
            results["multiply_service"] = r2.json().get("status", "unknown") 
        except Exception: 
            results["multiply_service"] = "unreachable" 
        return results
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
