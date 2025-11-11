# V2 Multi-Agent AI Platform - Architecture Documentation

## System Overview

The V2 platform extends the MVP with:
- **Vector RAG** for semantic search
- **Multi-Agent Orchestration** (Router, Knowledge, Escalation agents)
- **Evaluation Metrics** (BLEU, semantic similarity, CSAT)
- **Self-Improving Feedback Loops** (automatic retraining)
- **A/B Testing Framework** for model comparison

---

## Architecture Diagram

```
┌─────────────┐
│   Customer  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Router Agent   │ ← Intent Classification
└──────┬──────────┘
       │
       ├───► ┌─────────────────┐
       │     │ Knowledge Agent  │ ← FAQ/Order Queries
       │     └────────┬─────────┘
       │              │
       │              ▼
       │     ┌─────────────────┐
       │     │  Vector RAG     │ ← Semantic Search
       │     │  (ChromaDB)     │
       │     └─────────────────┘
       │
       └───► ┌─────────────────┐
             │ Escalation Agent│ ← Complaints/Low Confidence
             └─────────────────┘
                    │
                    ▼
             ┌─────────────────┐
             │  Human Agent    │
             └─────────────────┘

Feedback Loop:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Feedback   │───► │ Training Data │───► │ Retraining │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Model Update │
                                          └──────────────┘
```

---

## Component Details

### 1. Vector RAG Service (`rag_service.py`)

**Purpose:** Semantic search using vector embeddings

**Key Functions:**
- `generate_embedding(text)` - Create embeddings using sentence-transformers
- `search_knowledge_base_vector(query, db)` - Semantic search in ChromaDB
- `add_article_to_vector_db()` - Store article embeddings

**Technology:**
- `sentence-transformers` (all-MiniLM-L6-v2) - Embedding model
- `chromadb` - Vector database
- Fallback to keyword search if embeddings unavailable

**Data Flow:**
1. Knowledge base article created/updated
2. Embedding generated automatically
3. Stored in ChromaDB + SQLite (JSON column)
4. Query → Embedding → Similarity search → Top K results

---

### 2. Multi-Agent Orchestration

#### Router Agent (`router_agent.py`)

**Purpose:** Intent classification and routing decisions

**Key Functions:**
- `classify_intent(user_message)` - Classify intent using embedding similarity
- `should_escalate(intent, confidence, message)` - Escalation logic

**Intent Categories:**
- `faq` - General questions
- `order_inquiry` - Order status, tracking
- `technical_support` - Technical issues
- `complaint` - Customer complaints (auto-escalate)
- `general` - Greetings, general queries

**Classification Method:**
- Few-shot learning using embedding similarity
- Compares user message to intent examples
- Returns intent + confidence score

#### Knowledge Agent (`knowledge_agent.py`)

**Purpose:** Handle FAQ and knowledge base queries

**Key Functions:**
- `handle_knowledge_query(user_message, conversation_id, db)` - Process query
- Uses vector RAG for retrieval
- Generates response using Ollama or fallback

**Flow:**
1. Search knowledge base (vector RAG)
2. Calculate confidence from similarity
3. Build context from matched articles
4. Generate LLM response
5. Return response + confidence + matched articles

#### Escalation Agent (`escalation_agent.py`)

**Purpose:** Manage handoff to human agents

**Key Functions:**
- `handle_escalation(conversation_id, user_message, reason, db)` - Escalate conversation
- Updates conversation status to "escalated"
- Creates escalation message

**Escalation Triggers:**
- Low confidence (< 0.4)
- Complaint intent
- Explicit escalation request ("human agent", "speak to someone")

#### Orchestrator (`agent_orchestrator.py`)

**Purpose:** Coordinate multi-agent system

**Key Functions:**
- `orchestrate_response(conversation_id, user_message, db)` - Main orchestration

**Flow:**
1. Router classifies intent
2. Check if escalation needed
3. Route to Knowledge Agent (FAQ/orders) or Escalation Agent
4. Return response with intent, confidence, agent_type

---

### 3. Evaluation Service (`evaluation_service.py`)

**Purpose:** Calculate quality metrics

**Key Functions:**
- `calculate_bleu_score(reference, candidate)` - BLEU score calculation
- `calculate_semantic_similarity(text1, text2)` - Cosine similarity
- `aggregate_evaluation_metrics(db, days)` - Aggregate metrics over time

**Metrics:**
- **BLEU Score:** Measures response quality vs agent corrections
- **Semantic Similarity:** Measures retrieval accuracy
- **CSAT:** Customer satisfaction (1-5 scale)
- **Deflection Rate:** % resolved without escalation

**Storage:**
- `EvaluationMetrics` model stores computed scores
- Linked to messages and conversations

---

### 4. Retraining Service (`retraining_service.py`)

**Purpose:** Process feedback and update models

**Key Functions:**
- `collect_training_data(db)` - Format feedback for training
- `process_retraining(db)` - Run retraining pipeline
- `export_training_data_jsonl(db)` - Export for fine-tuning

**Retraining Pipeline:**
1. Collect feedback with corrections → `TrainingData`
2. Re-embed knowledge articles with negative feedback
3. Generate few-shot examples from corrections
4. Update intent examples based on misclassifications
5. Mark training data as processed

**Training Data Format:**
```json
{
  "original": "AI response",
  "correction": "Agent correction",
  "intent": "faq",
  "conversation_id": 123
}
```

---

### 5. Experiment Service (`experiment_service.py`)

**Purpose:** A/B testing and model version comparison

**Key Functions:**
- `assign_experiment_variant(conversation_id, experiment_id, db)` - Traffic splitting
- `compare_experiment_versions(experiment_id, db)` - Compare metrics
- `create_experiment(...)` - Create new experiment

**Experiment Flow:**
1. Create model versions (embedding model, prompts, thresholds)
2. Create experiment with variants A & B
3. Assign conversations to variants (traffic split)
4. Track metrics per variant
5. Compare and determine winner

**Comparison Metrics:**
- CSAT (40% weight)
- Deflection rate (40% weight)
- Average confidence (20% weight)

---

## Database Schema

### New Models

**EvaluationMetrics:**
- `message_id`, `conversation_id`
- `bleu_score`, `semantic_similarity`, `csat_score`

**TrainingData:**
- `feedback_id`, `conversation_id`, `message_id`
- `original_ai_response`, `agent_correction`
- `intent`, `processed`, `processed_at`

**Correction:**
- `message_id`, `original_content`, `corrected_content`
- `diff_summary`, `reason`

**AgentAction:**
- `conversation_id`, `message_id`
- `action_type` (approve, reject, edit, escalate)
- `action_data` (JSON)

**ModelVersion:**
- `name`, `description`, `config` (JSON)
- `is_active`

**Experiment:**
- `name`, `description`
- `variant_a_version_id`, `variant_b_version_id`
- `traffic_split`, `status`

### Updated Models

**Conversation:**
- Added: `csat_score`, `experiment_id`

**Message:**
- Added: `intent`, `agent_type`

**KnowledgeBase:**
- Added: `embedding` (JSON column)

---

## API Endpoints

### New Endpoints

**Analytics:**
- `GET /api/analytics/evaluation` - Evaluation metrics
- `GET /api/analytics/agent-performance` - Agent performance metrics

**Feedback:**
- `POST /api/feedback/retrain` - Trigger retraining
- `GET /api/feedback/training-data/export` - Export training data

**Experiments:**
- `POST /api/experiments/model-versions` - Create model version
- `GET /api/experiments/model-versions` - List model versions
- `POST /api/experiments/experiments` - Create experiment
- `GET /api/experiments/experiments` - List experiments
- `GET /api/experiments/experiments/{id}/comparison` - Compare variants
- `GET /api/experiments/experiments/active` - Get active experiment

**Conversations:**
- `PATCH /api/conversations/{id}` - Now accepts `csat_score`

**AI:**
- `POST /api/ai/generate` - Now returns `intent`, `intent_confidence`, `agent_type`

---

## Data Flow Examples

### 1. Customer Query Flow

```
Customer: "Where is my order?"
    ↓
Router Agent: classify_intent() → "order_inquiry" (confidence: 0.85)
    ↓
Knowledge Agent: handle_knowledge_query()
    ↓
Vector RAG: search_knowledge_base_vector() → Top 3 articles
    ↓
LLM: Generate response with context
    ↓
Response: "Your order is being processed..." (confidence: 0.78)
    ↓
Message stored with: intent="order_inquiry", agent_type="knowledge"
```

### 2. Feedback → Retraining Flow

```
Agent provides feedback with correction
    ↓
Feedback.create() → TrainingData.create()
    ↓
Evaluation: calculate_bleu_score(), calculate_semantic_similarity()
    ↓
EvaluationMetrics.save()
    ↓
Trigger retraining: process_retraining()
    ↓
1. Collect training data
2. Re-embed knowledge articles
3. Generate few-shot examples
4. Update intent examples
    ↓
Model improvements reflected in next responses
```

### 3. A/B Testing Flow

```
Create experiment: "Test new embedding model"
    ↓
Variant A: old embeddings (50% traffic)
Variant B: new embeddings (50% traffic)
    ↓
Conversations assigned to variants
    ↓
Track metrics per variant:
- Variant A: CSAT 3.8, Deflection 65%
- Variant B: CSAT 4.2, Deflection 72%
    ↓
Compare: Variant B wins
    ↓
Promote Variant B to production
```

---

## Scalability Considerations

### Current (MVP/Demo)
- SQLite for relational data
- ChromaDB for vector storage (local)
- Synchronous processing
- Single server

### Production Path
- **Database:** PostgreSQL with pgvector extension
- **Vector DB:** Pinecone or Weaviate (managed)
- **Caching:** Redis for embeddings and frequent queries
- **Async Jobs:** Celery for retraining and batch processing
- **Message Queue:** RabbitMQ or Redis for agent coordination
- **Monitoring:** Prometheus + Grafana for metrics
- **Logging:** ELK stack for centralized logs

### Performance Optimizations
- Embedding caching (Redis)
- Batch embedding generation
- Async retraining jobs
- Connection pooling
- CDN for static assets

---

## Security Considerations

1. **API Authentication:** JWT tokens for agent dashboard
2. **Rate Limiting:** Prevent abuse of AI endpoints
3. **Data Privacy:** PII masking in training data exports
4. **Access Control:** Role-based access (agent vs admin)
5. **Audit Logging:** Track all agent actions

---

## Future Enhancements

1. **Advanced Intent Classification:** Fine-tuned classifier model
2. **Multi-turn Conversations:** Context-aware responses
3. **Sentiment Analysis:** Real-time sentiment detection
4. **Proactive Escalation:** ML-based escalation prediction
5. **Custom Agent Types:** Domain-specific agents (billing, technical, etc.)
6. **Real-time Updates:** WebSocket for live agent dashboard
7. **Advanced Analytics:** Conversation flow analysis, topic clustering

---

## Testing Strategy

1. **Unit Tests:** Individual agent functions
2. **Integration Tests:** End-to-end agent orchestration
3. **Evaluation Tests:** BLEU/semantic similarity accuracy
4. **Load Tests:** Vector search performance
5. **A/B Test Validation:** Statistical significance testing

---

## Deployment

### Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production
- Docker containers for backend/frontend
- Nginx reverse proxy
- PostgreSQL + pgvector
- Managed vector DB (Pinecone/Weaviate)
- Kubernetes for orchestration (optional)

---

## Monitoring & Observability

1. **Metrics:** Prometheus for system metrics
2. **Logs:** Structured logging (JSON)
3. **Tracing:** OpenTelemetry for distributed tracing
4. **Alerts:** AlertManager for critical issues
5. **Dashboards:** Grafana for visualization

---

## Conclusion

The V2 architecture demonstrates:
- **Modularity:** Each agent is independent and testable
- **Scalability:** Clear path to production infrastructure
- **Observability:** Comprehensive metrics and logging
- **Improvement:** Self-learning through feedback loops
- **Experimentation:** Data-driven model optimization

This design aligns with enterprise chatbot platforms and provides a solid foundation for production deployment.

