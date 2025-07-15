import os
import httpx
from fastapi import HTTPException

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "https://thoughts-avg0.onrender.com")

async def user_login(username: str, password: str):
    url = f"{USER_SERVICE_URL}/login"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"username": username, "password": password})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Login failed")
        return response.json()

async def get_user_profile(token: str):
    url = f"{USER_SERVICE_URL}/profile"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch profile")
        return response.json()
