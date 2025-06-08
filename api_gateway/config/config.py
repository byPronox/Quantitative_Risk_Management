# api_gateway/config/config.py
"""
Centralized configuration for API Gateway URLs and secrets.
All sensitive data should be loaded from environment variables or Docker secrets.
"""
import os

class GatewaySettings:
    CICIDS_URL: str = os.getenv("CICIDS_URL", "http://cicids:8000/predict/cicids/")
    LANL_URL: str = os.getenv("LANL_URL", "http://lanl:8000/predict/lanl/")
    NVD_URL: str = os.getenv("NVD_URL", "http://nvd:8000/nvd")
    COMBINED_URL: str = os.getenv("COMBINED_URL", "http://combined:8000/predict/combined/")
    # Add more secrets/config as needed

gateway_settings = GatewaySettings()
