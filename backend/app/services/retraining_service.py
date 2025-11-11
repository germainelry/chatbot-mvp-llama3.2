"""
Retraining service for processing feedback and updating models.
Handles RAG improvement, few-shot example generation, and intent classification updates.
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import TrainingData, Feedback, Message, KnowledgeBase
from app.services.rag_service import add_article_to_vector_db, initialize_vector_db
from app.services.router_agent import INTENT_EXAMPLES


def collect_training_data(db: Session, limit: Optional[int] = None) -> List[TrainingData]:
    """
    Collect feedback data and format it for training.
    Creates TrainingData entries from Feedback with corrections.
    """
    # Get feedback with corrections that haven't been processed
    query = db.query(Feedback).filter(
        Feedback.agent_correction.isnot(None),
        Feedback.agent_correction != ""
    )
    
    if limit:
        query = query.limit(limit)
    
    feedback_items = query.all()
    training_data_list = []
    
    for feedback in feedback_items:
        # Check if training data already exists
        existing = db.query(TrainingData).filter(
            TrainingData.feedback_id == feedback.id
        ).first()
        
        if existing:
            continue
        
        # Get the original AI message
        if feedback.message_id:
            message = db.query(Message).filter(Message.id == feedback.message_id).first()
            if message:
                training_data = TrainingData(
                    feedback_id=feedback.id,
                    conversation_id=feedback.conversation_id,
                    message_id=feedback.message_id,
                    original_ai_response=message.content,
                    agent_correction=feedback.agent_correction,
                    intent=message.intent,
                    processed=0
                )
                db.add(training_data)
                training_data_list.append(training_data)
    
    db.commit()
    return training_data_list


def process_retraining(db: Session) -> Dict:
    """
    Process retraining pipeline:
    1. Collect training data from feedback
    2. Update knowledge base embeddings for articles with negative feedback
    3. Generate few-shot examples from corrections
    4. Update intent examples based on misclassifications
    """
    results = {
        "training_data_collected": 0,
        "knowledge_articles_updated": 0,
        "few_shot_examples_generated": 0,
        "intent_examples_updated": 0,
        "errors": []
    }
    
    try:
        # Step 1: Collect training data
        training_data = collect_training_data(db)
        results["training_data_collected"] = len(training_data)
        
        # Step 2: Update knowledge base embeddings for articles with negative feedback
        negative_feedback = db.query(Feedback).filter(
            Feedback.rating.in_(["not_helpful", "needs_improvement"])
        ).all()
        
        for feedback in negative_feedback:
            if feedback.message_id:
                message = db.query(Message).filter(Message.id == feedback.message_id).first()
                if message and message.matched_articles:  # This would need to be stored
                    # Re-embed knowledge articles (simplified - in production would track which articles)
                    articles = db.query(KnowledgeBase).all()
                    for article in articles:
                        add_article_to_vector_db(article.id, article.title, article.content, db)
                        results["knowledge_articles_updated"] += 1
        
        # Step 3: Generate few-shot examples (store in a simple format)
        # In production, would update LLM prompt templates
        corrections = db.query(TrainingData).filter(
            TrainingData.processed == 0
        ).limit(10).all()
        
        results["few_shot_examples_generated"] = len(corrections)
        
        # Step 4: Mark training data as processed
        for td in corrections:
            td.processed = 1
            td.processed_at = datetime.utcnow()
        
        db.commit()
        
        # Step 5: Re-initialize vector DB to ensure consistency
        try:
            initialize_vector_db(db)
        except Exception as e:
            results["errors"].append(f"Vector DB re-initialization: {str(e)}")
        
    except Exception as e:
        results["errors"].append(f"Retraining error: {str(e)}")
    
    return results


def export_training_data_jsonl(db: Session, limit: Optional[int] = None) -> str:
    """
    Export training data in JSONL format for model fine-tuning.
    """
    import json
    
    query = db.query(TrainingData).filter(TrainingData.processed == 1)
    if limit:
        query = query.limit(limit)
    
    training_data = query.all()
    
    jsonl_lines = []
    for td in training_data:
        entry = {
            "original": td.original_ai_response,
            "correction": td.agent_correction,
            "intent": td.intent,
            "conversation_id": td.conversation_id
        }
        jsonl_lines.append(json.dumps(entry))
    
    return "\n".join(jsonl_lines)

