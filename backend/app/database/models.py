from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Risk(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    probability = Column(Float)
    impact = Column(Float)
    status = Column(String, default="Pendiente")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False)
    content = Column(String, nullable=False)
    author = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)

    risk = relationship("Risk", backref="observations")

