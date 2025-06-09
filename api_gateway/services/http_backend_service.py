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

    async def analyze_nvd_risk(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.NVD_URL + "/analyze_risk")
            resp.raise_for_status()
            logger.info("Gateway: NVD analyze risk request succeeded.")
            return resp.json()

    async def get_nvd_enterprise_metrics(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.NVD_URL + "/enterprise_metrics")
            resp.raise_for_status()
            logger.info("Gateway: NVD enterprise metrics request succeeded.")
            return resp.json()

    async def get_nvd_queue_status(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(gateway_settings.NVD_URL + "/queue_status")
            resp.raise_for_status()
            logger.info("Gateway: NVD queue status request succeeded.")
            return resp.json()

    async def clear_nvd_queue(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.NVD_URL + "/clear_queue")
            resp.raise_for_status()
            logger.info("Gateway: NVD clear queue request succeeded.")
            return resp.json()

    async def add_keyword_to_queue(self, keyword: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_settings.NVD_URL + "/add_to_queue", json={"keyword": keyword})
            resp.raise_for_status()
            logger.info("Gateway: Add keyword to queue request succeeded.")
            return resp.json()
