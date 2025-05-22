from pydantic import BaseModel, Field

class RiskCreate(BaseModel):
    name: str
    probability: float
    impact: float

class RiskOut(RiskCreate):
    id: int

    class Config:
        from_attributes = True

class CICIDSFeatures(BaseModel):
    Flow_Duration: int = Field(..., alias="Flow Duration")
    Total_Fwd_Packets: int = Field(..., alias="Total Fwd Packets")
    Total_Backward_Packets: int = Field(..., alias="Total Backward Packets")
    Total_Length_of_Fwd_Packets: int = Field(..., alias="Total Length of Fwd Packets")
    Total_Length_of_Bwd_Packets: int = Field(..., alias="Total Length of Bwd Packets")
    Fwd_Packet_Length_Mean: float = Field(..., alias="Fwd Packet Length Mean")
    Bwd_Packet_Length_Mean: float = Field(..., alias="Bwd Packet Length Mean")
    Flow_Bytes_s: float = Field(..., alias="Flow Bytes/s")
    Flow_Packets_s: float = Field(..., alias="Flow Packets/s")
    Packet_Length_Mean: float = Field(..., alias="Packet Length Mean")
    Packet_Length_Std: float = Field(..., alias="Packet Length Std")
    Average_Packet_Size: float = Field(..., alias="Average Packet Size")
    Avg_Fwd_Segment_Size: float = Field(..., alias="Avg Fwd Segment Size")
    Avg_Bwd_Segment_Size: float = Field(..., alias="Avg Bwd Segment Size")
    Init_Win_bytes_forward: int = Field(..., alias="Init_Win_bytes_forward")
    Init_Win_bytes_backward: int = Field(..., alias="Init_Win_bytes_backward")