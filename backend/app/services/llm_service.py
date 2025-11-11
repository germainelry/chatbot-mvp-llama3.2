"""
LLM service with Ollama integration and fallback logic.
Implements confidence scoring for Human-in-the-Loop workflow.
"""
import os
from typing import Dict, List
from sqlalchemy.orm import Session
import re

from app.models import KnowledgeBase, Message, Conversation
from app.services.rag_service import search_knowledge_base_vector

# Ollama will be optional - fallback to rule-based for reliability
OLLAMA_AVAILABLE = False
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    print("⚠️  Ollama not available, using fallback responses")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Auto-send threshold: AI responses with confidence >= this value are sent automatically
# Lower values = more automation but potentially lower quality
# Higher values = more agent review but better quality assurance
AUTO_SEND_THRESHOLD = float(os.getenv("AUTO_SEND_THRESHOLD", "0.65"))


def search_knowledge_base(query: str, db: Session) -> List[Dict]:
    """
    Search knowledge base using vector embeddings (with keyword fallback).
    """
    # Use vector search (will fallback to keyword if embeddings unavailable)
    return search_knowledge_base_vector(query, db, top_k=3)


def calculate_confidence_score(matched_articles: List[Dict], query: str) -> float:
    """
    Calculate confidence score based on knowledge base matches.
    Uses similarity score from vector search if available, otherwise match_score.
    
    Scoring logic:
    - High similarity (>0.7): 0.85 confidence
    - Medium similarity (0.5-0.7): 0.65 confidence
    - Low similarity (0.3-0.5): 0.4 confidence
    - No matches: 0.3 confidence
    """
    if not matched_articles:
        return 0.3
    
    # Use similarity if available (from vector search), otherwise match_score
    best_score = matched_articles[0].get("similarity") or matched_articles[0].get("match_score", 0)
    
    if best_score > 0.7:
        return 0.85
    elif best_score > 0.5:
        return 0.65
    elif best_score > 0.3:
        return 0.4
    else:
        return 0.3


async def generate_ai_response(
    conversation_id: int,
    user_message: str,
    db: Session
) -> Dict:
    """
    Generate AI response using Ollama or fallback logic.
    Returns response with confidence score for HITL decision.
    """
    
    # Search knowledge base
    matched_articles = search_knowledge_base(user_message, db)
    
    # Calculate confidence
    confidence = calculate_confidence_score(matched_articles, user_message)
    
    # Build context from knowledge base
    context = ""
    if matched_articles:
        context = "Relevant information:\n\n"
        for article in matched_articles[:2]:  # Use top 2
            context += f"**{article['title']}**\n{article['content'][:300]}...\n\n"
    
    # Try Ollama first
    if OLLAMA_AVAILABLE:
        try:
            response = await generate_ollama_response(user_message, context)
            return {
                "response": response,
                "confidence_score": confidence,
                "matched_articles": matched_articles,
                "reasoning": "Generated using Ollama LLM",
                "auto_send_threshold": AUTO_SEND_THRESHOLD,
                "should_auto_send": confidence >= AUTO_SEND_THRESHOLD
            }
        except Exception as e:
            print(f"Ollama failed: {e}, using fallback")
    
    # Fallback to rule-based responses
    response = generate_fallback_response(user_message, matched_articles)
    
    return {
        "response": response,
        "confidence_score": confidence,
        "matched_articles": matched_articles,
        "reasoning": "Generated using fallback logic (Ollama unavailable)",
        "auto_send_threshold": AUTO_SEND_THRESHOLD,
        "should_auto_send": confidence >= AUTO_SEND_THRESHOLD
    }


async def generate_ollama_response(user_message: str, context: str) -> str:
    """Generate response using Ollama LLM."""
    prompt = f"""You are a helpful customer support assistant. Use the following information to answer the customer's question.

{context}

Customer Question: {user_message}

Provide a helpful, concise response. If the information provided doesn't fully answer the question, acknowledge this and offer to escalate to a human agent."""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        raise Exception(f"Ollama generation failed: {e}")


def generate_fallback_response(user_message: str, matched_articles: List[Dict]) -> str:
    """
    Rule-based fallback responses for demo reliability.
    Uses matched knowledge base articles to construct response.
    """
    user_message_lower = user_message.lower()
    
    # If we have matched articles, use them
    if matched_articles and matched_articles[0]["match_score"] > 0.3:
        article = matched_articles[0]
        return f"Based on our {article['category']} policy:\n\n{article['content'][:200]}...\n\nWould you like more specific information about this?"
    
    # Keyword-based responses
    if any(word in user_message_lower for word in ["return", "refund", "exchange"]):
        return "I'd be happy to help with your return. Our return policy allows returns within 30 days of purchase. Could you provide your order number so I can check the specifics?"
    
    elif any(word in user_message_lower for word in ["shipping", "delivery", "tracking"]):
        return "I can help you with shipping information. Could you please provide your order number? Standard shipping typically takes 3-5 business days."
    
    elif any(word in user_message_lower for word in ["account", "login", "password", "reset"]):
        return "For account issues, I can help you reset your password or update your account information. What specific issue are you experiencing?"
    
    elif any(word in user_message_lower for word in ["product", "item", "specs", "details", "price"]):
        return "I'd be happy to provide product information. Which product are you interested in learning more about?"
    
    elif any(word in user_message_lower for word in ["cancel", "order"]):
        return "I can help you with your order. If you'd like to cancel or modify an order, please provide your order number and I'll check if it's possible."
    
    elif any(word in user_message_lower for word in ["hi", "hello", "hey"]):
        return "Hello! I'm here to help you with any questions about your order, returns, shipping, or our products. How can I assist you today?"
    
    else:
        # Generic helpful response
        return "I'm here to help! I can assist with questions about orders, returns, shipping, account issues, and product information. Could you provide more details about what you need help with?"

