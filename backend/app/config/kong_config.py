# backend/app/config/kong_config.py
"""
Kong Gateway configuration for Konnect integration
"""
import os

class KongSettings:
    # Kong Konnect URLs from your configuration
    KONG_PROXY_URL = os.getenv("KONG_PROXY_URL", "https://kong-b27b67aff4usnspl9.kongcloud.dev")
    KONG_ADMIN_API = os.getenv("KONG_ADMIN_API", "https://us.api.konghq.com/v2/control-planes/9d98c0ba-3ac1-44fd-b497-59743e18a80a")
    KONG_CONTROL_PLANE_ID = os.getenv("KONG_CONTROL_PLANE_ID", "9d98c0ba-3ac1-44fd-b497-59743e18a80a")
    
    # Kong authentication (you'll need to get these from Konnect)
    KONG_TOKEN = os.getenv("KONG_TOKEN", "kpat_wj1ejmjRNKPuG9Z8sRHqTEKp2DAiHufItUtpe73J1sgghDCLF")  # Personal Access Token from Konnect
    
    # Service configuration
    BACKEND_SERVICE_NAME = "quantitative-risk-backend"
    BACKEND_SERVICE_URL = os.getenv("BACKEND_URL", "http://backend:8000")

kong_settings = KongSettings()
