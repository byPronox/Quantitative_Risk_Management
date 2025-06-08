from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.models import Risk
from database.db import SessionLocal
from api.schemas import RiskCreate, RiskOut, CICIDSFeatures, LANLFeatures, CombinedFeatures
from typing import List
from ml.engine import PredictionFactory, PredictionStrategy
import logging
from queue_manager.queue import queue

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cicids_strategy() -> PredictionStrategy:
    return PredictionFactory.get_strategy("cicids")

def get_lanl_strategy() -> PredictionStrategy:
    return PredictionFactory.get_strategy("lanl")

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

# Use lazy logging formatting for best practices

@router.post("/predict/cicids/")
def predict_cicids_endpoint(features: CICIDSFeatures, strategy: PredictionStrategy = Depends(get_cicids_strategy)):
    try:
        probability = strategy.predict(features.dict(by_alias=True))
        return {"attack_probability": probability}
    except Exception as e:
        logger.error("CICIDS prediction failed: %s", e)
        raise HTTPException(status_code=500, detail="Prediction failed") from e

@router.post("/predict/lanl/")
def predict_lanl_endpoint(features: LANLFeatures, strategy: PredictionStrategy = Depends(get_lanl_strategy)):
    try:
        probability = strategy.predict(features.dict(by_alias=True))
        return {"attack_probability": probability}
    except Exception as e:
        logger.error("LANL prediction failed: %s", e)
        raise HTTPException(status_code=500, detail="Prediction failed") from e

@router.post("/predict/combined/")
def predict_combined_endpoint(features: CombinedFeatures, cicids_strategy: PredictionStrategy = Depends(get_cicids_strategy), lanl_strategy: PredictionStrategy = Depends(get_lanl_strategy)):
    try:
        prob_cicids = cicids_strategy.predict(features.cicids.dict(by_alias=True))
        prob_lanl = lanl_strategy.predict(features.lanl.dict(by_alias=True))
        combined_score = (prob_cicids + prob_lanl) / 2
        # Send prediction result to message queue for async processing/logging
        queue.send_message({
            "type": "combined_prediction",
            "cicids_probability": prob_cicids,
            "lanl_probability": prob_lanl,
            "combined_score": combined_score
        })
        return {
            "cicids_probability": prob_cicids,
            "lanl_probability": prob_lanl,
            "combined_score": combined_score
        }
    except Exception as e:
        logger.error("Combined prediction failed: %s", e)
        raise HTTPException(status_code=500, detail="Prediction failed") from e