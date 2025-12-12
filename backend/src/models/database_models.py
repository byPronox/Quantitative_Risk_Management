"""
Database models using SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON
from sqlalchemy.sql import func
from datetime import datetime

from config.database import Base


class RiskAnalysis(Base):
    """Risk analysis database model"""
    __tablename__ = "risk_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(50), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    overall_risk_score = Column(Float, nullable=False)
    overall_risk_level = Column(String(20), nullable=False)
    assets_analyzed = Column(JSON, nullable=False)
    vulnerabilities_found = Column(Integer, default=0)
    recommendations = Column(JSON, nullable=True)
    analysis_metadata = Column(JSON, nullable=True)  # Changed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Asset(Base):
    """Asset database model"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)
    version = Column(String(100), nullable=True)
    vendor = Column(String(200), nullable=True)
    cpe = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Vulnerability(Base):
    """Vulnerability database model"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(20), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    cvss_score = Column(Float, nullable=True)
    severity = Column(String(20), nullable=False)
    published_date = Column(DateTime(timezone=True), nullable=True)
    last_modified = Column(DateTime(timezone=True), nullable=True)
    affected_cpes = Column(JSON, nullable=True)
    references = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NvdJob(Base):
    """NVD Job database model"""
    __tablename__ = "nvd_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    keyword = Column(String(255), index=True)
    status = Column(String(50), default="pending")
    total_results = Column(Integer, default=0)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_via = Column(String(50), nullable=True)
    vulnerabilities = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NmapJob(Base):
    """Nmap Job database model"""
    __tablename__ = "nmap_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    target = Column(String(255), index=True, nullable=False)
    status = Column(String(50), default="queued")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class User(Base):
    """User database model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
