"""
Escalation Agent - Manages handoff to human agents.
Tracks escalation reasons and prepares context for human agents.
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Conversation, ConversationStatus, Message, MessageType


async def handle_escalation(
    conversation_id: int,
    user_message: str,
    escalation_reason: str,
    db: Session
) -> Dict:
    """
    Handle escalation to human agent.
    Updates conversation status and creates escalation message.
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        return {
            "error": "Conversation not found",
            "agent_type": "escalation"
        }
    
    # Update conversation status
    conversation.status = ConversationStatus.ESCALATED
    conversation.updated_at = datetime.utcnow()
    
    # Create escalation message
    escalation_message = Message(
        conversation_id=conversation_id,
        content=f"Conversation escalated to human agent. Reason: {escalation_reason}",
        message_type=MessageType.AGENT_ONLY,
        confidence_score=1.0,  # Human agent has full confidence
        agent_type="escalation"
    )
    
    db.add(escalation_message)
    db.commit()
    db.refresh(escalation_message)
    
    # Prepare response for customer
    response = f"I understand you need assistance. I'm connecting you with a human agent who can help you better. Please hold while we transfer your conversation."
    
    if escalation_reason:
        response += f" (Reason: {escalation_reason})"
    
    return {
        "response": response,
        "confidence_score": 1.0,  # Escalation is certain
        "escalation_reason": escalation_reason,
        "conversation_status": "escalated",
        "agent_type": "escalation",
        "should_auto_send": True  # Escalation messages are always sent
    }


def get_escalation_reason(intent: str, confidence: float, user_message: str) -> str:
    """
    Generate human-readable escalation reason.
    """
    if confidence < 0.4:
        return f"Low confidence in intent classification ({confidence:.2f})"
    
    if intent == "complaint":
        return "Customer complaint requires human attention"
    
    escalation_keywords = ["human", "agent", "representative", "speak to someone"]
    if any(keyword in user_message.lower() for keyword in escalation_keywords):
        return "Explicit request for human agent"
    
    return f"Intent classification: {intent} (confidence: {confidence:.2f})"

