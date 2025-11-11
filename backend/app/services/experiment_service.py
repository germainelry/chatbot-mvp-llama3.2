"""
Experiment service for A/B testing and model version comparison.
"""
import random
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Experiment, ModelVersion, Conversation, EvaluationMetrics, Message


def assign_experiment_variant(conversation_id: int, experiment_id: int, db: Session) -> Optional[int]:
    """
    Assign conversation to experiment variant based on traffic split.
    Returns version_id (variant A or B).
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment or experiment.status != "active":
        return None
    
    # Use conversation_id as seed for consistent assignment
    random.seed(conversation_id)
    split = random.random()
    
    if split < experiment.traffic_split:
        return experiment.variant_a_version_id
    else:
        return experiment.variant_b_version_id


def get_active_experiment(db: Session) -> Optional[Experiment]:
    """Get the currently active experiment."""
    return db.query(Experiment).filter(
        Experiment.status == "active"
    ).first()


def compare_experiment_versions(experiment_id: int, db: Session) -> Dict:
    """
    Compare performance of experiment variants.
    Returns metrics comparison.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        return {}
    
    # Get conversations for each variant
    variant_a_convs = db.query(Conversation).filter(
        Conversation.experiment_id == experiment_id,
        Conversation.id % 2 == 0  # Simplified: use ID mod for variant assignment
    ).all()
    
    variant_b_convs = db.query(Conversation).filter(
        Conversation.experiment_id == experiment_id,
        Conversation.id % 2 == 1
    ).all()
    
    # Calculate metrics for variant A
    variant_a_metrics = calculate_variant_metrics(variant_a_convs, db)
    
    # Calculate metrics for variant B
    variant_b_metrics = calculate_variant_metrics(variant_b_convs, db)
    
    # Statistical comparison (simplified)
    comparison = {
        "variant_a": {
            "version_id": experiment.variant_a_version_id,
            "metrics": variant_a_metrics
        },
        "variant_b": {
            "version_id": experiment.variant_b_version_id,
            "metrics": variant_b_metrics
        },
        "winner": determine_winner(variant_a_metrics, variant_b_metrics)
    }
    
    return comparison


def calculate_variant_metrics(conversations: List, db: Session) -> Dict:
    """Calculate metrics for a variant."""
    if not conversations:
        return {
            "total_conversations": 0,
            "avg_csat": 0.0,
            "deflection_rate": 0.0,
            "avg_confidence": 0.0
        }
    
    conv_ids = [c.id for c in conversations]
    
    # CSAT
    csat_scores = [c.csat_score for c in conversations if c.csat_score]
    avg_csat = sum(csat_scores) / len(csat_scores) if csat_scores else 0.0
    
    # Deflection rate (resolved vs escalated)
    resolved = sum(1 for c in conversations if c.status.value == "resolved")
    escalated = sum(1 for c in conversations if c.status.value == "escalated")
    total = len(conversations)
    deflection_rate = (resolved / total * 100) if total > 0 else 0.0
    
    # Average confidence
    messages = db.query(Message).filter(
        Message.conversation_id.in_(conv_ids),
        Message.confidence_score.isnot(None)
    ).all()
    avg_confidence = sum(m.confidence_score for m in messages) / len(messages) if messages else 0.0
    
    return {
        "total_conversations": len(conversations),
        "avg_csat": round(avg_csat, 2),
        "deflection_rate": round(deflection_rate, 2),
        "avg_confidence": round(avg_confidence, 2)
    }


def determine_winner(variant_a_metrics: Dict, variant_b_metrics: Dict) -> Optional[str]:
    """
    Determine winning variant based on metrics.
    Simplified: uses weighted score.
    """
    if variant_a_metrics["total_conversations"] == 0 or variant_b_metrics["total_conversations"] == 0:
        return None
    
    # Weighted score: CSAT (40%), Deflection (40%), Confidence (20%)
    score_a = (
        variant_a_metrics["avg_csat"] * 0.4 +
        variant_a_metrics["deflection_rate"] * 0.4 +
        variant_a_metrics["avg_confidence"] * 20 * 0.2
    )
    
    score_b = (
        variant_b_metrics["avg_csat"] * 0.4 +
        variant_b_metrics["deflection_rate"] * 0.4 +
        variant_b_metrics["avg_confidence"] * 20 * 0.2
    )
    
    if score_a > score_b:
        return "variant_a"
    elif score_b > score_a:
        return "variant_b"
    else:
        return "tie"


def create_experiment(
    name: str,
    variant_a_version_id: int,
    variant_b_version_id: int,
    traffic_split: float = 0.5,
    description: Optional[str] = None,
    db: Session = None
) -> Experiment:
    """Create a new A/B test experiment."""
    if db is None:
        return None
    
    # Deactivate other experiments
    db.query(Experiment).filter(Experiment.status == "active").update({"status": "paused"})
    
    experiment = Experiment(
        name=name,
        description=description,
        variant_a_version_id=variant_a_version_id,
        variant_b_version_id=variant_b_version_id,
        traffic_split=traffic_split,
        status="active"
    )
    
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    
    return experiment

