from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

CICIDS_URL = os.getenv("CICIDS_URL", "http://cicids:8000/predict/cicids/")
LANL_URL = os.getenv("LANL_URL", "http://lanl:8000/predict/lanl/")
NVD_URL = os.getenv("NVD_URL", "http://nvd:8000/nvd")
COMBINED_URL = os.getenv("COMBINED_URL", "http://combined:8000/predict/combined/")

@app.post("/predict/cicids/")
async def gateway_cicids(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(CICIDS_URL, json=data)
        return resp.json()

@app.post("/predict/lanl/")
async def gateway_lanl(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(LANL_URL, json=data)
        return resp.json()

@app.get("/nvd")
async def gateway_nvd(request: Request):
    params = dict(request.query_params)
    async with httpx.AsyncClient() as client:
        resp = await client.get(NVD_URL, params=params)
        return resp.json()

@app.post("/predict/combined/")
async def gateway_combined(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(COMBINED_URL, json=data)
        return resp.json()