from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.models import Risk
from database.db import SessionLocal
from .schemas import RiskCreate, RiskOut, CICIDSFeatures, LANLFeatures, CombinedFeatures
from typing import List
from ml.engine import predict_cicids, predict_lanl

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/risks/", response_model=RiskOut)
def create_risk(risk: RiskCreate, db: Session = Depends(get_db)):
    db_risk = Risk(**risk.dict())
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    return db_risk

@router.get("/risks/", response_model=List[RiskOut])
def list_risks(db: Session = Depends(get_db)):
    return db.query(Risk).all()

@router.post("/predict/cicids/")
def predict_cicids_endpoint(features: CICIDSFeatures):
    probability = predict_cicids(features.dict(by_alias=True))
    return {"attack_probability": probability}

@router.post("/predict/lanl/")
def predict_lanl_endpoint(features: LANLFeatures):
    probability = predict_lanl(features.dict(by_alias=True))
    return {"attack_probability": probability}

@router.post("/predict/combined/")
def predict_combined_endpoint(features: CombinedFeatures):
    prob_cicids = predict_cicids(features.cicids.dict(by_alias=True))
    prob_lanl = predict_lanl(features.lanl.dict(by_alias=True))
    combined_score = (prob_cicids + prob_lanl) / 2
    return {
        "cicids_probability": prob_cicids,
        "lanl_probability": prob_lanl,
        "combined_score": combined_score
    }