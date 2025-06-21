from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database.models import Risk, Observation
from database.db import SessionLocal
from api.schemas import RiskCreate, RiskOut, CICIDSFeatures, LANLFeatures, CombinedFeatures, ObservationCreate, ObservationOut
from typing import List
from ml.engine import PredictionFactory, PredictionStrategy
import logging
from queue_manager.queue import MessageQueue

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
        mq = MessageQueue()
        mq.send_message({
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

@router.post("/observations/", response_model=ObservationOut)
def create_observation(obs: ObservationCreate, db: Session = Depends(get_db)):
    db_obs = Observation(**obs.dict())
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)
    return db_obs

@router.get("/observations/{risk_id}", response_model=List[ObservationOut])
def list_observations(risk_id: int, db: Session = Depends(get_db)):
    return db.query(Observation).filter(Observation.risk_id == risk_id).all()

@router.delete("/observations/{observation_id}", status_code=204)
def delete_observation(observation_id: int, db: Session = Depends(get_db)):
    db_obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not db_obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    db.delete(db_obs)
    db.commit()
    return

@router.patch("/risks/{risk_id}/status", response_model=RiskOut)
def update_risk_status(risk_id: int, status: str = Body(...), db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    risk.status = status
    db.commit()
    db.refresh(risk)
    return risk