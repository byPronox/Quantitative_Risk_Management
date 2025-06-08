# api_gateway/services/http_backend_service.py
"""
HttpBackendService implements BackendServiceInterface using httpx.
"""
from typing import Any, Dict
import httpx
import logging
from config.config import gateway_settings
from interfaces.backend_service_interface import BackendServiceInterface

logger = logging.getLogger("api_gateway")

class HttpBackendService(BackendServiceInterface):
    async def predict_cicids(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.CICIDS_URL, json=data)
            resp.raise_for_status()
            logger.info("Gateway: CICIDS prediction request succeeded.")
            return resp.json()

    async def predict_lanl(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.LANL_URL, json=data)
            resp.raise_for_status()
            logger.info("Gateway: LANL prediction request succeeded.")
            return resp.json()

    async def predict_combined(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.COMBINED_URL, json=data)
            resp.raise_for_status()
            logger.info("Gateway: Combined prediction request succeeded.")
            return resp.json()

    async def get_nvd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(gateway_settings.NVD_URL, params=params)
            resp.raise_for_status()
            logger.info("Gateway: NVD request succeeded.")
            return resp.json()
