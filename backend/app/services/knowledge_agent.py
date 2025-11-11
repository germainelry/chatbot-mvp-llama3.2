"""
Knowledge Agent - Handles FAQ and knowledge base queries.
Extracted from llm_service, specialized for knowledge retrieval.
"""
import os
from typing import Dict, List
from sqlalchemy.orm import Session

from app.services.llm_service import (
    generate_ollama_response,
    generate_fallback_response,
    OLLAMA_AVAILABLE,
    OLLAMA_MODEL,
    AUTO_SEND_THRESHOLD
)
from app.services.rag_service import search_knowledge_base_vector

# Re-export for convenience
def calculate_confidence_score(matched_articles: List[Dict], query: str) -> float:
    """Calculate confidence score based on knowledge base matches."""
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


async def handle_knowledge_query(
    user_message: str,
    conversation_id: int,
    db: Session
) -> Dict:
    """
    Handle knowledge base query using RAG.
    Returns response with confidence score.
    """
    # Search knowledge base
    matched_articles = search_knowledge_base_vector(user_message, db, top_k=3)
    
    # Calculate confidence
    confidence = calculate_confidence_score(matched_articles, user_message)
    
    # Build context from knowledge base
    context = ""
    if matched_articles:
        context = "Relevant information:\n\n"
        for article in matched_articles[:2]:  # Use top 2
            context += f"**{article['title']}**\n{article['content'][:300]}...\n\n"
    
    # Generate response using Ollama or fallback
    if OLLAMA_AVAILABLE:
        try:
            response = await generate_ollama_response(user_message, context)
            return {
                "response": response,
                "confidence_score": confidence,
                "matched_articles": matched_articles,
                "reasoning": "Generated using Knowledge Agent with Ollama LLM",
                "auto_send_threshold": AUTO_SEND_THRESHOLD,
                "should_auto_send": confidence >= AUTO_SEND_THRESHOLD,
                "agent_type": "knowledge"
            }
        except Exception as e:
            print(f"Ollama failed: {e}, using fallback")
    
    # Fallback to rule-based responses
    response = generate_fallback_response(user_message, matched_articles)
    
    return {
        "response": response,
        "confidence_score": confidence,
        "matched_articles": matched_articles,
        "reasoning": "Generated using Knowledge Agent with fallback logic",
        "auto_send_threshold": AUTO_SEND_THRESHOLD,
        "should_auto_send": confidence >= AUTO_SEND_THRESHOLD,
        "agent_type": "knowledge"
    }

