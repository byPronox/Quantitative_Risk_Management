"""
Pydantic schemas for ML Prediction Service API.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class CICIDSFeatures(BaseModel):
    """Schema for CICIDS model features."""
    flow_duration: float = Field(..., alias="Flow Duration", description="Flow duration")
    total_fwd_packets: int = Field(..., alias="Total Fwd Packets", description="Total forward packets")
    total_backward_packets: int = Field(..., alias="Total Backward Packets", description="Total backward packets")
    total_length_of_fwd_packets: int = Field(..., alias="Total Length of Fwd Packets", description="Total length of forward packets")
    total_length_of_bwd_packets: int = Field(..., alias="Total Length of Bwd Packets", description="Total length of backward packets")
    fwd_packet_length_mean: float = Field(..., alias="Fwd Packet Length Mean", description="Forward packet length mean")
    bwd_packet_length_mean: float = Field(..., alias="Bwd Packet Length Mean", description="Backward packet length mean")
    flow_bytes_s: float = Field(..., alias="Flow Bytes/s", description="Flow bytes per second")
    flow_packets_s: float = Field(..., alias="Flow Packets/s", description="Flow packets per second")
    packet_length_mean: float = Field(..., alias="Packet Length Mean", description="Packet length mean")
    packet_length_std: float = Field(..., alias="Packet Length Std", description="Packet length standard deviation")
    average_packet_size: float = Field(..., alias="Average Packet Size", description="Average packet size")
    avg_fwd_segment_size: float = Field(..., alias="Avg Fwd Segment Size", description="Average forward segment size")
    avg_bwd_segment_size: float = Field(..., alias="Avg Bwd Segment Size", description="Average backward segment size")
    init_win_bytes_forward: int = Field(..., alias="Init_Win_bytes_forward", description="Initial window bytes forward")
    init_win_bytes_backward: int = Field(..., alias="Init_Win_bytes_backward", description="Initial window bytes backward")
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "Flow Duration": 100,
                "Total Fwd Packets": 10000,
                "Total Backward Packets": 1,
                "Total Length of Fwd Packets": 1000000,
                "Total Length of Bwd Packets": 100,
                "Fwd Packet Length Mean": 1500,
                "Bwd Packet Length Mean": 10,
                "Flow Bytes/s": 10000000,
                "Flow Packets/s": 100000,
                "Packet Length Mean": 1400,
                "Packet Length Std": 500,
                "Average Packet Size": 1450,
                "Avg Fwd Segment Size": 1500,
                "Avg Bwd Segment Size": 10,
                "Init_Win_bytes_forward": 64,
                "Init_Win_bytes_backward": 64
            }
        }

class LANLFeatures(BaseModel):
    """Schema for LANL model features."""
    time: int = Field(..., description="Unix timestamp")
    user: str = Field(..., description="User identifier")
    computer: str = Field(..., description="Computer identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "time": 1640995200,
                "user": "user123",
                "computer": "computer456"
            }
        }

class CombinedFeatures(BaseModel):
    """Schema for combined model predictions."""
    cicids: CICIDSFeatures = Field(..., description="CICIDS model features")
    lanl: LANLFeatures = Field(..., description="LANL model features")

class PredictionResponse(BaseModel):
    """Schema for prediction responses."""
    model: str = Field(..., description="Model name used for prediction")
    probability: float = Field(..., description="Risk probability (0.0 to 1.0)")
    features: Dict[str, Any] = Field(..., description="Input features used")
    timestamp: str = Field(..., description="Prediction timestamp")

class CombinedPredictionResponse(BaseModel):
    """Schema for combined prediction responses."""
    cicids_probability: float = Field(..., description="CICIDS model probability")
    lanl_probability: float = Field(..., description="LANL model probability")
    combined_score: float = Field(..., description="Combined risk score")
    timestamp: str = Field(..., description="Prediction timestamp")

class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    models_loaded: list = Field(..., description="List of loaded models")
    service: str = Field(..., description="Service name")

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
