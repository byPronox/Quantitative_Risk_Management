from sqlalchemy import Column, Integer, String, Float
from database.db import Base

class Risk(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    probability = Column(Float)
    impact = Column(Float)

