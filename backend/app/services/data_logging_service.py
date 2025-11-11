"""
Data logging service for comprehensive conversation and agent action tracking.
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import difflib

from app.models import AgentAction, Correction, Message, Conversation


def log_agent_action(
    action_type: str,
    conversation_id: Optional[int],
    message_id: Optional[int],
    action_data: Optional[Dict] = None,
    db: Session = None
):
    """
    Log an agent action (approve, reject, edit, escalate).
    """
    if db is None:
        return
    
    agent_action = AgentAction(
        conversation_id=conversation_id,
        message_id=message_id,
        action_type=action_type,
        action_data=json.dumps(action_data) if action_data else None
    )
    
    db.add(agent_action)
    db.commit()
    return agent_action


def create_correction(
    message_id: int,
    original_content: str,
    corrected_content: str,
    reason: Optional[str] = None,
    db: Session = None
):
    """
    Create a correction record with diff calculation.
    """
    if db is None:
        return None
    
    # Calculate diff summary
    diff_summary = calculate_diff_summary(original_content, corrected_content)
    
    correction = Correction(
        message_id=message_id,
        original_content=original_content,
        corrected_content=corrected_content,
        diff_summary=diff_summary,
        reason=reason
    )
    
    db.add(correction)
    db.commit()
    db.refresh(correction)
    
    return correction


def calculate_diff_summary(original: str, corrected: str) -> str:
    """
    Calculate a human-readable diff summary.
    """
    original_lines = original.splitlines()
    corrected_lines = corrected.splitlines()
    
    diff = list(difflib.unified_diff(
        original_lines,
        corrected_lines,
        lineterm='',
        n=3
    ))
    
    if not diff:
        return "No changes"
    
    # Return first few lines of diff
    return "\n".join(diff[:10])


def export_conversation_data(
    conversation_id: int,
    db: Session
) -> Dict:
    """
    Export all data for a conversation in training-ready format.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        return {}
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    corrections = db.query(Correction).join(Message).filter(
        Message.conversation_id == conversation_id
    ).all()
    
    actions = db.query(AgentAction).filter(
        AgentAction.conversation_id == conversation_id
    ).all()
    
    return {
        "conversation_id": conversation_id,
        "customer_id": conversation.customer_id,
        "status": conversation.status.value,
        "csat_score": conversation.csat_score,
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "type": msg.message_type.value,
                "confidence": msg.confidence_score,
                "intent": msg.intent,
                "agent_type": msg.agent_type,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "corrections": [
            {
                "message_id": corr.message_id,
                "original": corr.original_content,
                "corrected": corr.corrected_content,
                "reason": corr.reason,
                "created_at": corr.created_at.isoformat()
            }
            for corr in corrections
        ],
        "agent_actions": [
            {
                "action_type": action.action_type,
                "action_data": json.loads(action.action_data) if action.action_data else None,
                "created_at": action.created_at.isoformat()
            }
            for action in actions
        ]
    }


def get_agent_performance_metrics(
    db: Session,
    days: int = 30
) -> Dict:
    """
    Calculate agent performance metrics.
    """
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all actions in date range
    actions = db.query(AgentAction).filter(
        AgentAction.created_at >= start_date
    ).all()
    
    # Count by action type
    action_counts = {}
    for action in actions:
        action_counts[action.action_type] = action_counts.get(action.action_type, 0) + 1
    
    # Get approval rate
    total_reviews = sum(action_counts.values())
    approvals = action_counts.get("approve", 0)
    approval_rate = (approvals / total_reviews * 100) if total_reviews > 0 else 0
    
    # Get correction frequency
    corrections = db.query(Correction).filter(
        Correction.created_at >= start_date
    ).count()
    
    return {
        "total_actions": total_reviews,
        "approval_rate": round(approval_rate, 2),
        "correction_frequency": corrections,
        "action_breakdown": action_counts
    }

