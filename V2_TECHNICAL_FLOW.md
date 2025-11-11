# V2 Technical Flow Documentation

## Overview

This document explains the complete technical flow of how a user message is processed, how confidence scores are calculated, and how the system decides whether to auto-send a response or queue it for agent review.

---

## Complete Message Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SENDS MESSAGE                           │
│              "What languages can you speak?"                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: API Endpoint                                            │
│  POST /api/ai/generate                                           │
│  File: backend/app/routers/ai.py                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Agent Orchestrator                                      │
│  File: backend/app/services/agent_orchestrator.py               │
│  Function: orchestrate_response()                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Router Agent - Intent Classification                   │
│  File: backend/app/services/router_agent.py                     │
│  Function: classify_intent()                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
        ┌──────────────────┐  ┌──────────────────┐
        │  ESCALATION       │  │  KNOWLEDGE      │
        │  PATH             │  │  PATH           │
        └──────────────────┘  └──────────────────┘
```

---

## Step-by-Step Technical Flow

### Step 1: API Request (`backend/app/routers/ai.py`)

**Entry Point:**
```python
POST /api/ai/generate
{
    "conversation_id": 123,
    "user_message": "What languages can you speak?"
}
```

**Code Flow:**
```python
@router.post("/generate")
async def generate_response(request: AIGenerateRequest, db: Session):
    # Uses multi-agent orchestrator by default
    result = await orchestrate_response(
        conversation_id=request.conversation_id,
        user_message=request.user_message,
        db=db
    )
    return AIGenerateResponse(...)
```

**What Happens:**
- Receives user message and conversation ID
- Calls `orchestrate_response()` to process through multi-agent system
- Returns response with confidence score, intent, and agent type

---

### Step 2: Agent Orchestrator (`backend/app/services/agent_orchestrator.py`)

**Function: `orchestrate_response()`**

**Code:**
```python
async def orchestrate_response(conversation_id, user_message, db):
    # Step 1: Router classifies intent
    intent_result = classify_intent(user_message)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]  # e.g., 0.23
    
    # Step 2: Check if escalation is needed
    if should_escalate(intent, confidence, user_message):
        # ESCALATION PATH
        escalation_reason = get_escalation_reason(intent, confidence, user_message)
        result = await handle_escalation(...)
        return result
    
    # Step 3: Route to knowledge agent
    if intent in ["faq", "order_inquiry", "general"]:
        result = await handle_knowledge_query(...)
        return result
```

**Decision Logic:**
- **If `should_escalate()` returns True** → Goes to Escalation Agent
- **If intent is FAQ/order/general** → Goes to Knowledge Agent
- **If intent is technical_support** → Goes to Knowledge Agent (with lower threshold)

---

### Step 3: Router Agent - Intent Classification (`backend/app/services/router_agent.py`)

**Function: `classify_intent(user_message)`**

**How It Works:**

1. **Generate Embedding:**
   ```python
   user_embedding = generate_embedding(user_message.lower())
   # Converts "What languages can you speak?" to 384-dimensional vector
   ```

2. **Compare to Intent Examples:**
   ```python
   INTENT_EXAMPLES = {
       "faq": ["What is your return policy?", "How do I track my order?", ...],
       "general": ["Hello", "Hi there", "Help me", "What can you do?", ...],
       "order_inquiry": ["Where is my order?", ...],
       "technical_support": ["The website is not working", ...],
       "complaint": ["I'm not happy", ...]
   }
   ```

3. **Calculate Similarity:**
   ```python
   for intent, examples in INTENT_EXAMPLES.items():
       similarities = [
           cosine_similarity(user_embedding, example_embedding)
           for example_embedding in example_embeddings
       ]
       intent_scores[intent] = max(similarities)  # Best match
   ```

4. **Return Best Intent:**
   ```python
   best_intent = max(intent_scores, key=intent_scores.get)
   # Example result:
   # {
   #     "intent": "general",
   #     "confidence": 0.23,  # Low because "What languages..." doesn't match examples well
   #     "all_scores": {"general": 0.23, "faq": 0.15, ...}
   # }
   ```

**Why Confidence is Low:**
- "What languages can you speak?" doesn't semantically match any intent examples
- The "general" examples are greetings ("Hello", "Hi there") which are different
- Cosine similarity between embeddings is low (0.23)

---

### Step 4A: Escalation Path (`backend/app/services/escalation_agent.py`)

**Triggered When:**
```python
def should_escalate(intent, confidence, user_message):
    # Low confidence (< 0.4)
    if confidence < 0.4:  # 0.23 < 0.4 → TRUE
        return True
    
    # Complaint intent
    if intent == "complaint":
        return True
    
    # Explicit escalation request
    if any(keyword in user_message.lower() for keyword in ["human", "agent", ...]):
        return True
```

**Function: `handle_escalation()`**

**What Happens:**

1. **Update Conversation Status:**
   ```python
   conversation.status = ConversationStatus.ESCALATED
   ```

2. **Create Escalation Message in Database:**
   ```python
   escalation_message = Message(
       content="Conversation escalated to human agent. Reason: Low confidence in intent classification (0.23)",
       message_type=MessageType.AGENT_ONLY,
       confidence_score=1.0,  # Escalation is certain
       agent_type="escalation"
   )
   ```

3. **Generate Customer Response:**
   ```python
   response = "I understand you need assistance. I'm connecting you with a human agent who can help you better. Please hold while we transfer your conversation."
   
   if escalation_reason:
       response += f" (Reason: {escalation_reason})"
   # Final: "I understand you need assistance... (Reason: Low confidence in intent classification (0.23))"
   ```

4. **Return Result:**
   ```python
   return {
       "response": response,  # The customer-facing message
       "confidence_score": 1.0,  # Escalation is certain
       "escalation_reason": "Low confidence in intent classification (0.23)",
       "agent_type": "escalation",
       "should_auto_send": True  # Always auto-send escalations
   }
   ```

**Why Two Messages Appear:**
1. **Internal message** (stored in DB): "Conversation escalated to human agent. Reason: ..."
2. **Customer message** (sent to user): "I understand you need assistance..."

---

### Step 4B: Knowledge Agent Path (`backend/app/services/knowledge_agent.py`)

**Triggered When:**
- Intent confidence >= 0.4
- Intent is "faq", "order_inquiry", or "general"

**Function: `handle_knowledge_query()`**

**What Happens:**

1. **Search Knowledge Base:**
   ```python
   matched_articles = search_knowledge_base_vector(user_message, db, top_k=3)
   # Uses vector embeddings to find semantically similar articles
   ```

2. **Calculate Confidence Score:**
   ```python
   def calculate_confidence_score(matched_articles, query):
       if not matched_articles:
           return 0.3  # No matches
       
       best_score = matched_articles[0].get("similarity") or matched_articles[0].get("match_score", 0)
       
       if best_score > 0.7:
           return 0.85  # High confidence
       elif best_score > 0.5:
           return 0.65  # Medium confidence
       elif best_score > 0.3:
           return 0.4   # Low confidence
       else:
           return 0.3   # Very low confidence
   ```

3. **Build Context from Knowledge Base:**
   ```python
   context = ""
   if matched_articles:
       context = "Relevant information:\n\n"
       for article in matched_articles[:2]:
           context += f"**{article['title']}**\n{article['content'][:300]}...\n\n"
   ```

4. **Generate Response:**
   ```python
   if OLLAMA_AVAILABLE:
       response = await generate_ollama_response(user_message, context)
   else:
       response = generate_fallback_response(user_message, matched_articles)
   ```

5. **Return Result:**
   ```python
   return {
       "response": response,
       "confidence_score": confidence,  # e.g., 0.65
       "matched_articles": matched_articles,
       "should_auto_send": confidence >= AUTO_SEND_THRESHOLD  # 0.65 >= 0.65 → True
   }
   ```

---

## Confidence Score Calculation

### Two Types of Confidence Scores

#### 1. Intent Classification Confidence (Router Agent)

**Location:** `backend/app/services/router_agent.py`

**How It's Calculated:**
- Compares user message embedding to intent example embeddings
- Uses cosine similarity (0.0 to 1.0)
- Returns the maximum similarity score

**Example:**
```
User: "What languages can you speak?"
Intent Examples:
  - "Hello" → similarity: 0.15
  - "Hi there" → similarity: 0.18
  - "What can you do?" → similarity: 0.23 (best match)
Result: intent="general", confidence=0.23
```

**Why It Can Be Low:**
- User question doesn't match any intent examples semantically
- Intent examples are limited (only 5 per category)
- Embedding model may not capture semantic similarity well for certain phrases

#### 2. Knowledge Base Match Confidence (Knowledge Agent)

**Location:** `backend/app/services/knowledge_agent.py`

**How It's Calculated:**
- Based on vector similarity to knowledge base articles
- Uses the best matching article's similarity score
- Maps similarity to confidence ranges

**Mapping:**
```
Similarity > 0.7  → Confidence: 0.85 (High)
Similarity > 0.5  → Confidence: 0.65 (Medium)
Similarity > 0.3  → Confidence: 0.4  (Low)
Similarity ≤ 0.3  → Confidence: 0.3  (Very Low)
No matches        → Confidence: 0.3
```

**Example:**
```
User: "What is your return policy?"
Knowledge Base Search:
  - Article: "Return Policy" → similarity: 0.82
Result: confidence = 0.85 (high)
```

---

## Auto-Send vs Pending Review Decision

### Decision Logic

**Location:** `backend/app/services/llm_service.py`

**Threshold:**
```python
AUTO_SEND_THRESHOLD = 0.65  # Default, can be set via environment variable
```

**Decision:**
```python
should_auto_send = confidence_score >= AUTO_SEND_THRESHOLD
```

### Confidence Ranges

| Confidence Score | Action | Reason |
|-----------------|--------|--------|
| **≥ 0.65** | ✅ **Auto-Send** | High confidence in knowledge base match |
| **0.5 - 0.64** | ⏸️ **Pending Review** | Medium confidence, needs agent verification |
| **< 0.5** | ⏸️ **Pending Review** | Low confidence, likely needs human help |

### Special Cases

1. **Escalation Messages:**
   ```python
   # Always auto-send, regardless of confidence
   "should_auto_send": True
   ```

2. **Technical Support:**
   ```python
   # Lower threshold (0.6 instead of 0.65)
   if intent == "technical_support" and confidence < 0.6:
       escalate()
   ```

---

## Response Generation Methods

### Method 1: Ollama LLM (Primary)

**Location:** `backend/app/services/llm_service.py`

**Function: `generate_ollama_response()`**

**Prompt Template:**
```
You are a helpful customer support assistant. Use the following information to answer the customer's question.

[Knowledge Base Context]

Customer Question: [user_message]

Provide a helpful, concise response. If the information provided doesn't fully answer the question, acknowledge this and offer to escalate to a human agent.
```

**How It Works:**
1. Builds context from top 2 matched knowledge base articles
2. Sends to Ollama with system + user messages
3. Returns LLM-generated response

**Example:**
```
Context: "**Return Policy**\nOur return policy allows returns within 30 days..."
User: "Can I return this item?"
Response: "Yes, you can return items within 30 days of purchase. Please provide your order number..."
```

### Method 2: Fallback Response (When Ollama Unavailable)

**Location:** `backend/app/services/llm_service.py`

**Function: `generate_fallback_response()`**

**How It Works:**
1. Checks if matched articles exist
2. If yes: Uses article content
3. If no: Uses keyword-based rule matching

**Rule-Based Responses:**
```python
if "return" or "refund" in message:
    return "I'd be happy to help with your return. Our return policy allows returns within 30 days..."

elif "shipping" or "delivery" in message:
    return "I can help you with shipping information. Could you please provide your order number?..."

elif "hi" or "hello" in message:
    return "Hello! I'm here to help you with any questions..."

else:
    return "I'm here to help! I can assist with questions about orders, returns, shipping..."
```

**Example:**
```
User: "What languages can you speak?"
No keyword matches → Generic response:
"I'm here to help! I can assist with questions about orders, returns, shipping, account issues, and product information. Could you provide more details about what you need help with?"
```

### Method 3: Escalation Response (When Confidence Low)

**Location:** `backend/app/services/escalation_agent.py`

**Function: `handle_escalation()`**

**Response Template:**
```python
base_response = "I understand you need assistance. I'm connecting you with a human agent who can help you better. Please hold while we transfer your conversation."

if escalation_reason:
    response = base_response + f" (Reason: {escalation_reason})"
```

**Example:**
```
Escalation Reason: "Low confidence in intent classification (0.23)"
Final Response: "I understand you need assistance. I'm connecting you with a human agent who can help you better. Please hold while we transfer your conversation. (Reason: Low confidence in intent classification (0.23))"
```

---

## Vector RAG Search Process

### Step 1: Generate Query Embedding

**Location:** `backend/app/services/rag_service.py`

```python
def generate_embedding(text: str) -> List[float]:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()  # 384-dimensional vector
```

### Step 2: Search ChromaDB

**Location:** `backend/app/services/rag_service.py`

```python
def search_knowledge_base_vector(query: str, db: Session, top_k: int = 3):
    query_embedding = generate_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Results contain:
    # - ids: Article IDs
    # - distances: Cosine distances (lower = more similar)
    # - documents: Article text
```

### Step 3: Calculate Similarity

```python
similarity = 1.0 - distance  # Convert distance to similarity
# distance 0.0 → similarity 1.0 (perfect match)
# distance 0.3 → similarity 0.7 (good match)
# distance 0.7 → similarity 0.3 (poor match)
```

### Step 4: Fallback to Keyword Search

**If embeddings unavailable:**
```python
def search_knowledge_base_keyword(query: str, db: Session, top_k: int = 3):
    query_words = set(query.lower().split())
    
    for article in all_articles:
        article_words = set(article_text.lower().split())
        common_words = query_words.intersection(article_words)
        
        match_score = len(common_words) / len(query_words)
        # "return policy" vs "return refund" → 1/2 = 0.5 match_score
```

---

## Complete Example Flow

### Example 1: Low Confidence Escalation

**User Message:** "What languages can you speak?"

**Step 1: Router Agent**
```
classify_intent("What languages can you speak?")
→ intent="general", confidence=0.23
```

**Step 2: Escalation Check**
```
should_escalate(intent="general", confidence=0.23, message="...")
→ 0.23 < 0.4 → TRUE
```

**Step 3: Escalation Agent**
```
handle_escalation(conversation_id, user_message, "Low confidence in intent classification (0.23)")
→ Updates conversation status to "escalated"
→ Creates internal message: "Conversation escalated to human agent. Reason: Low confidence in intent classification (0.23)"
→ Generates customer response: "I understand you need assistance. I'm connecting you with a human agent who can help you better. Please hold while we transfer your conversation. (Reason: Low confidence in intent classification (0.23))"
→ Returns: {confidence_score: 1.0, should_auto_send: True}
```

**Result:**
- ✅ Auto-sent (escalation always auto-sends)
- Confidence: 1.0 (escalation is certain)
- Two messages appear:
  1. Internal: "Conversation escalated to human agent..."
  2. Customer: "I understand you need assistance..."

---

### Example 2: High Confidence Auto-Send

**User Message:** "What is your return policy?"

**Step 1: Router Agent**
```
classify_intent("What is your return policy?")
→ intent="faq", confidence=0.78
```

**Step 2: Escalation Check**
```
should_escalate(intent="faq", confidence=0.78, message="...")
→ 0.78 >= 0.4 → FALSE (no escalation)
```

**Step 3: Knowledge Agent**
```
handle_knowledge_query("What is your return policy?", conversation_id, db)
→ search_knowledge_base_vector() finds article "Return Policy"
→ similarity: 0.82
→ confidence_score: 0.85 (high)
→ generate_ollama_response() with context
→ Response: "Our return policy allows returns within 30 days of purchase..."
→ Returns: {confidence_score: 0.85, should_auto_send: True}
```

**Result:**
- ✅ Auto-sent (0.85 >= 0.65)
- Confidence: 0.85
- Response generated from knowledge base + LLM

---

### Example 3: Medium Confidence Pending Review

**User Message:** "How do I track my shipment?"

**Step 1: Router Agent**
```
classify_intent("How do I track my shipment?")
→ intent="order_inquiry", confidence=0.65
```

**Step 2: Escalation Check**
```
should_escalate(intent="order_inquiry", confidence=0.65, message="...")
→ 0.65 >= 0.4 → FALSE (no escalation)
```

**Step 3: Knowledge Agent**
```
handle_knowledge_query("How do I track my shipment?", conversation_id, db)
→ search_knowledge_base_vector() finds article "Shipping Information"
→ similarity: 0.52
→ confidence_score: 0.65 (medium)
→ generate_ollama_response() with context
→ Response: "You can track your shipment using your order number..."
→ Returns: {confidence_score: 0.65, should_auto_send: True}
```

**Result:**
- ✅ Auto-sent (0.65 >= 0.65, exactly at threshold)
- Confidence: 0.65
- Response generated from knowledge base + LLM

---

## Key Configuration Values

### Confidence Thresholds

**Location:** `backend/app/services/llm_service.py`

```python
AUTO_SEND_THRESHOLD = 0.65  # Can be set via AUTO_SEND_THRESHOLD env var
```

**Escalation Threshold:**
```python
# In router_agent.py
if confidence < 0.4:  # Hard-coded
    escalate()
```

**Technical Support Threshold:**
```python
# In agent_orchestrator.py
if intent == "technical_support" and confidence < 0.6:  # Hard-coded
    escalate()
```

### Intent Examples

**Location:** `backend/app/services/router_agent.py`

```python
INTENT_EXAMPLES = {
    "faq": 5 examples,
    "order_inquiry": 5 examples,
    "technical_support": 5 examples,
    "complaint": 5 examples,
    "general": 5 examples
}
```

**To Improve Intent Classification:**
- Add more diverse examples to each intent category
- Include questions like "What languages can you speak?" in "general" or "faq"
- Use actual customer queries as examples

---

## Database Storage

### Messages Table

**Location:** `backend/app/models.py`

**Fields:**
- `content`: The actual message text
- `message_type`: `ai_draft`, `agent_edited`, `final`, `agent_only`
- `confidence_score`: Confidence from knowledge agent (0.0-1.0)
- `intent`: Intent classification result
- `agent_type`: `router`, `knowledge`, `escalation`
- `original_ai_content`: If agent edited, stores original

**Example:**
```python
Message(
    content="I understand you need assistance...",
    message_type=MessageType.AGENT_ONLY,
    confidence_score=1.0,
    intent="general",
    agent_type="escalation"
)
```

### Conversations Table

**Fields:**
- `status`: `active`, `resolved`, `escalated`
- `csat_score`: Customer satisfaction (1-5)
- `experiment_id`: For A/B testing

**When Escalated:**
```python
conversation.status = ConversationStatus.ESCALATED
```

---

## Troubleshooting Low Confidence

### Why "What languages can you speak?" Gets Low Confidence

1. **Intent Classification:**
   - Question doesn't match any intent examples
   - "general" examples are greetings, not capability questions
   - Embedding similarity is low (0.23)

2. **Early Escalation:**
   - System escalates before checking knowledge base
   - Knowledge base might have relevant content, but it's never checked

### Solutions

**Option 1: Improve Intent Examples**
```python
INTENT_EXAMPLES = {
    "general": [
        "Hello",
        "Hi there",
        "What languages can you speak?",  # Add this
        "What can you do?",
        "What are your capabilities?"
    ]
}
```

**Option 2: Check Knowledge Base First**
Modify `agent_orchestrator.py` to check knowledge base before escalating:
```python
# Always check knowledge base first
result = await handle_knowledge_query(...)
kb_confidence = result["confidence_score"]

# Use combined confidence
combined = (intent_confidence * 0.3) + (kb_confidence * 0.7)

# Only escalate if both are low
if combined < 0.4:
    escalate()
```

**Option 3: Lower Escalation Threshold**
```python
# In router_agent.py
if confidence < 0.2:  # Instead of 0.4
    return True
```

---

## Summary

### Key Takeaways

1. **Two-Stage Process:**
   - Stage 1: Intent classification (Router Agent)
   - Stage 2: Knowledge base search (Knowledge Agent) OR Escalation

2. **Confidence Scores:**
   - Intent confidence: Based on similarity to intent examples
   - Knowledge confidence: Based on similarity to knowledge base articles
   - Final confidence: Used for auto-send decision

3. **Auto-Send Decision:**
   - `confidence >= 0.65` → Auto-send
   - `confidence < 0.65` → Pending review
   - Escalation → Always auto-send

4. **Response Generation:**
   - Primary: Ollama LLM with knowledge base context
   - Fallback: Rule-based responses
   - Escalation: Pre-defined escalation message

5. **Low Confidence Escalation:**
   - Triggered when intent confidence < 0.4
   - Happens BEFORE knowledge base check
   - Generates escalation message automatically

### Files to Reference

- **Orchestration:** `backend/app/services/agent_orchestrator.py`
- **Intent Classification:** `backend/app/services/router_agent.py`
- **Knowledge Search:** `backend/app/services/knowledge_agent.py`
- **Escalation:** `backend/app/services/escalation_agent.py`
- **Vector RAG:** `backend/app/services/rag_service.py`
- **LLM Generation:** `backend/app/services/llm_service.py`
- **API Endpoint:** `backend/app/routers/ai.py`

---

## Next Steps

To improve the system:

1. **Add more intent examples** to better classify diverse questions
2. **Modify orchestrator** to check knowledge base before escalating
3. **Tune confidence thresholds** based on actual performance data
4. **Add intent examples** for capability questions like "What languages can you speak?"
5. **Implement combined confidence** using both intent and knowledge base scores

