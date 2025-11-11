"""
Router Agent - Classifies user intent and routes to appropriate agent.
Uses embedding similarity for few-shot intent classification.
"""
from typing import Dict, Optional, List
from app.services.rag_service import generate_embedding, cosine_similarity, EMBEDDING_AVAILABLE

# Intent categories
INTENT_CATEGORIES = [
    "faq",
    "order_inquiry",
    "technical_support",
    "complaint",
    "general"
]

# Intent examples for few-shot classification
INTENT_EXAMPLES = {
    "faq": [
        "What is your return policy?",
        "How do I track my order?",
        "What are your shipping options?",
        "How do I reset my password?",
        "What is your refund policy?",
    ],
    "order_inquiry": [
        "Where is my order?",
        "When will my order arrive?",
        "I need to cancel my order",
        "Can I modify my order?",
        "What's the status of order #12345?",
    ],
    "technical_support": [
        "The website is not working",
        "I can't log into my account",
        "The app keeps crashing",
        "I'm having trouble with checkout",
        "The payment failed",
    ],
    "complaint": [
        "I'm not happy with my purchase",
        "The product arrived damaged",
        "The service was terrible",
        "I want to file a complaint",
        "This is unacceptable",
    ],
    "general": [
        "Hello",
        "Hi there",
        "Help me",
        "I need assistance",
        "What can you do?",
    ]
}


def classify_intent(user_message: str) -> Dict[str, any]:
    """
    Classify user intent using embedding similarity to intent examples.
    Returns intent category and confidence score.
    """
    if not EMBEDDING_AVAILABLE:
        # Fallback to keyword-based classification
        return classify_intent_keyword(user_message)
    
    # Generate embedding for user message
    user_embedding = generate_embedding(user_message.lower())
    if user_embedding is None:
        return classify_intent_keyword(user_message)
    
    # Calculate similarity to each intent category
    intent_scores = {}
    for intent, examples in INTENT_EXAMPLES.items():
        # Get average embedding for intent examples
        example_embeddings = []
        for example in examples:
            emb = generate_embedding(example.lower())
            if emb:
                example_embeddings.append(emb)
        
        if example_embeddings:
            # Calculate average similarity to examples
            similarities = [
                cosine_similarity(user_embedding, ex_emb)
                for ex_emb in example_embeddings
            ]
            intent_scores[intent] = max(similarities)  # Use max similarity
    
    if not intent_scores:
        return {
            "intent": "general",
            "confidence": 0.5
        }
    
    # Get intent with highest score
    best_intent = max(intent_scores, key=intent_scores.get)
    confidence = intent_scores[best_intent]
    
    return {
        "intent": best_intent,
        "confidence": float(confidence),
        "all_scores": intent_scores
    }


def classify_intent_keyword(user_message: str) -> Dict[str, any]:
    """
    Fallback keyword-based intent classification.
    """
    user_lower = user_message.lower()
    
    # Keyword patterns for each intent
    keyword_patterns = {
        "order_inquiry": ["order", "track", "shipment", "delivery", "cancel order"],
        "technical_support": ["not working", "error", "bug", "crash", "login", "password"],
        "complaint": ["complaint", "unhappy", "terrible", "bad", "damaged", "wrong"],
        "faq": ["policy", "return", "refund", "shipping", "how", "what", "when"],
    }
    
    scores = {}
    for intent, keywords in keyword_patterns.items():
        matches = sum(1 for keyword in keywords if keyword in user_lower)
        scores[intent] = matches / len(keywords) if keywords else 0
    
    if not scores or max(scores.values()) == 0:
        return {
            "intent": "general",
            "confidence": 0.5
        }
    
    best_intent = max(scores, key=scores.get)
    return {
        "intent": best_intent,
        "confidence": float(scores[best_intent])
    }


def should_escalate(intent: str, confidence: float, user_message: str) -> bool:
    """
    Determine if conversation should be escalated to human agent.
    Escalation triggers:
    - Low confidence (< 0.4)
    - Complaint intent (always escalate)
    - Explicit escalation request
    """
    # Explicit escalation request
    escalation_keywords = ["human", "agent", "representative", "speak to someone", "escalate"]
    if any(keyword in user_message.lower() for keyword in escalation_keywords):
        return True
    
    # Complaint intent always escalates
    if intent == "complaint":
        return True
    
    # Low confidence
    if confidence < 0.4:
        return True
    
    return False

