"""
Evaluation service for calculating BLEU scores, semantic similarity, and other metrics.
"""
import os
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import numpy as np

# Try to import nltk for BLEU calculation
BLEU_AVAILABLE = False
try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
    BLEU_AVAILABLE = True
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
except ImportError:
    print("⚠️  nltk not available, BLEU scores will not be calculated")

# Import RAG service for embeddings
from app.services.rag_service import generate_embedding, cosine_similarity, EMBEDDING_AVAILABLE


def calculate_bleu_score(reference: str, candidate: str) -> Optional[float]:
    """
    Calculate BLEU score between reference (agent correction) and candidate (AI response).
    Returns None if NLTK is not available.
    """
    if not BLEU_AVAILABLE:
        return None
    
    try:
        # Tokenize sentences
        reference_tokens = reference.lower().split()
        candidate_tokens = candidate.lower().split()
        
        # Calculate BLEU with smoothing
        smoothing = SmoothingFunction().method1
        score = sentence_bleu(
            [reference_tokens],
            candidate_tokens,
            smoothing_function=smoothing
        )
        
        return float(score)
    except Exception as e:
        print(f"Error calculating BLEU score: {e}")
        return None


def calculate_semantic_similarity(text1: str, text2: str) -> Optional[float]:
    """
    Calculate semantic similarity using cosine similarity of embeddings.
    Returns None if embeddings are not available.
    """
    if not EMBEDDING_AVAILABLE:
        return None
    
    try:
        embedding1 = generate_embedding(text1)
        embedding2 = generate_embedding(text2)
        
        if embedding1 is None or embedding2 is None:
            return None
        
        similarity = cosine_similarity(embedding1, embedding2)
        return similarity
    except Exception as e:
        print(f"Error calculating semantic similarity: {e}")
        return None


def evaluate_ai_response(
    ai_response: str,
    agent_correction: Optional[str] = None,
    db: Session = None
) -> Dict:
    """
    Evaluate an AI response against agent correction.
    Returns dictionary with BLEU score and semantic similarity.
    """
    metrics = {
        "bleu_score": None,
        "semantic_similarity": None
    }
    
    if agent_correction:
        # Calculate BLEU score
        bleu = calculate_bleu_score(agent_correction, ai_response)
        metrics["bleu_score"] = bleu
        
        # Calculate semantic similarity
        similarity = calculate_semantic_similarity(agent_correction, ai_response)
        metrics["semantic_similarity"] = similarity
    
    return metrics


def aggregate_evaluation_metrics(
    db: Session,
    days: int = 30
) -> Dict:
    """
    Aggregate evaluation metrics over time.
    Returns trends for BLEU scores, semantic similarity, and CSAT.
    """
    from datetime import datetime, timedelta
    from app.models import EvaluationMetrics, Conversation, Feedback
    from sqlalchemy import func
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get all evaluation metrics in date range
    metrics = db.query(EvaluationMetrics).filter(
        EvaluationMetrics.created_at >= start_date
    ).all()
    
    # Calculate averages
    bleu_scores = [m.bleu_score for m in metrics if m.bleu_score is not None]
    semantic_similarities = [m.semantic_similarity for m in metrics if m.semantic_similarity is not None]
    
    # Get CSAT scores
    csat_scores = db.query(Conversation.csat_score).filter(
        Conversation.csat_score.isnot(None),
        Conversation.resolved_at >= start_date
    ).all()
    csat_values = [c[0] for c in csat_scores if c[0] is not None]
    
    # Calculate deflection trend (resolved vs escalated)
    resolved_count = db.query(func.count(Conversation.id)).filter(
        Conversation.status == "resolved",
        Conversation.resolved_at >= start_date
    ).scalar() or 0
    
    escalated_count = db.query(func.count(Conversation.id)).filter(
        Conversation.status == "escalated",
        Conversation.updated_at >= start_date
    ).scalar() or 0
    
    total = resolved_count + escalated_count
    deflection_rate = (resolved_count / total * 100) if total > 0 else 0
    
    return {
        "avg_bleu_score": float(np.mean(bleu_scores)) if bleu_scores else None,
        "avg_semantic_similarity": float(np.mean(semantic_similarities)) if semantic_similarities else None,
        "avg_csat": float(np.mean(csat_values)) if csat_values else None,
        "deflection_rate": deflection_rate,
        "total_evaluations": len(metrics),
        "total_csat_responses": len(csat_values)
    }


def save_evaluation_metrics(
    message_id: Optional[int],
    conversation_id: Optional[int],
    bleu_score: Optional[float],
    semantic_similarity: Optional[float],
    csat_score: Optional[int],
    db: Session
):
    """
    Save evaluation metrics to database.
    """
    from app.models import EvaluationMetrics
    
    eval_metric = EvaluationMetrics(
        message_id=message_id,
        conversation_id=conversation_id,
        bleu_score=bleu_score,
        semantic_similarity=semantic_similarity,
        csat_score=csat_score
    )
    
    db.add(eval_metric)
    db.commit()
    db.refresh(eval_metric)
    
    return eval_metric

