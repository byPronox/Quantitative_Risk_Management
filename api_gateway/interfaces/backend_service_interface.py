# api_gateway/interfaces/backend_service_interface.py
"""
BackendServiceInterface defines the contract for backend communication.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BackendServiceInterface(ABC):
    @abstractmethod
    async def predict_cicids(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def predict_lanl(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def predict_combined(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_nvd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def analyze_nvd_risk(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_nvd_enterprise_metrics(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_nvd_queue_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def clear_nvd_queue(self) -> Dict[str, Any]:
        pass
