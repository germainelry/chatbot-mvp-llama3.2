# AI Customer Support Assistant MVP

A full-stack AI-powered customer support system with **Human-in-the-Loop (HITL)** capabilities, powered by Ollama's Llama 3.2 LLM model. This MVP demonstrates modern agentic AI systems, prompt engineering, and product metrics for AI applications.

## Project Goals

This MVP provides:

- Agentic AI systems with LLM integration using Ollama Llama 3.2
- Human-in-the-Loop workflows (pre-send & post-send)
- Product metrics for AI systems (deflection rate, resolution rate, feedback sentiment)
- Feedback collection architecture for model improvement (RLHF)
- Knowledge base integration with RAG (Retrieval-Augmented Generation)
- Agent supervision dashboard
- Real-time analytics

## Architecture

```
Backend (FastAPI + SQLite)
├── LLM Service (Ollama Llama 3.2 + Fallback)
├── Knowledge Base (RAG Implementation)
├── Confidence Scoring
└── Feedback Collection

Frontend (React + TypeScript + Tailwind)
├── Customer Chat Interface
├── Agent Supervision Dashboard
├── Analytics Dashboard
└── Knowledge Base Management
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Ollama with Llama 3.2 (recommended)

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Seed database
python seed_data.py

# Run server
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at: http://localhost:5173

### Ollama Setup

```bash
# Install Ollama from https://ollama.ai

# Start Ollama
ollama serve

# Pull Llama 3.2 model
ollama pull llama3.2
```

**Note:** The system works without Ollama using intelligent fallback responses based on keyword matching and knowledge base articles. However, for optimal performance, we recommend using Ollama with the Llama 3.2 model.

## Key Features

### 1. Human-in-the-Loop Workflows

**Pre-Send Review (Primary Workflow):**
- AI generates draft response with confidence score using Ollama Llama 3.2
- Low confidence (<65%) → Auto-queue for agent review
- Agent can: Approve, Edit, or Escalate
- Edits tracked as corrections for model improvement

**Post-Send Feedback:**
- Agent rates AI responses (Helpful/Not Helpful/Needs Improvement)
- Collects corrections and notes
- Builds training dataset for RLHF

### 2. Confidence Scoring

- **High (>=80%)**: High confidence, auto-sent to customer
- **Good (65-79%)**: Good confidence, auto-sent to customer
- **Medium (50-64%)**: Medium confidence, requires agent review
- **Low (<50%)**: Low confidence, requires intervention

Based on knowledge base match quality and keyword relevance.

### 3. Product Metrics Dashboard

Critical metrics for AI system evaluation:

- **Deflection Rate**: % conversations handled without escalation
- **Resolution Rate**: % successfully resolved
- **Escalation Rate**: % requiring human-only intervention
- **Avg Confidence Score**: Model quality indicator
- **Feedback Sentiment**: Agent satisfaction (% helpful)

### 4. Knowledge Base Management

- CRUD interface for articles
- Category-based organization
- Keyword-based retrieval (can be upgraded to vector embeddings)
- Powers AI context generation via RAG

### 5. LLM Integration

- **Primary**: Ollama with Llama 3.2 model for local inference
- **Fallback**: Intelligent rule-based responses when Ollama unavailable
- **RAG**: Retrieval-Augmented Generation for context-aware responses
- **Confidence Calibration**: Match-based scoring for quality assurance

## Usage Guide

1. **Customer Chat** (`/customer`):
   - Send a question (e.g., "What's your return policy?")
   - AI responds using Ollama Llama 3.2 with confidence score
   - High confidence responses sent automatically
   - Low confidence queries queued for agent review

2. **Agent Dashboard** (`/agent`):
   - View conversation queue
   - Review AI draft responses
   - See confidence indicators
   - Edit responses if needed
   - Send and provide feedback

3. **Analytics** (`/analytics`):
   - View key metrics
   - Review feedback history
   - Monitor deflection and resolution rates
   - Track model performance

4. **Knowledge Base** (`/knowledge-base`):
   - Browse and manage articles
   - Add new articles
   - Update existing content
   - See immediate impact on AI responses via RAG

## Technical Architecture

### Product Strategy
- **HITL Paradigm**: Balances automation efficiency with quality control
- **Confidence Thresholds**: Configurable via environment variables (default: 65%)
- **Feedback Loops**: Critical for RLHF and continuous improvement
- **Metrics Selection**: Focused on operational impact and AI quality

### Technical Implementation
- **Scalability**: Designed for async queues, vector DBs, and caching
- **Fallback Strategy**: Ensures reliability when Ollama unavailable
- **Type Safety**: TypeScript + Pydantic for contract enforcement
- **Modular Design**: Easy to swap LLMs, databases, or add features

### AI/ML Implementation
- **LLM**: Ollama Llama 3.2 for local inference
- **Prompt Engineering**: System prompts with knowledge base context injection
- **Confidence Calibration**: Match-based scoring (can be upgraded to model logits)
- **RAG Implementation**: Keyword-based retrieval (can be upgraded to embeddings + vector DB)
- **Training Data Collection**: Structured feedback for future fine-tuning

### Operational Features
- **Agent Experience**: Clear indicators, edit capabilities, minimal friction
- **Customer Experience**: Fast responses for high-confidence, quality assurance for low
- **Monitoring**: Real-time metrics for operational decision-making
- **Iteration**: Feedback directly informs knowledge base improvements

## Project Structure

```
mvp-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # Database models
│   │   ├── routers/             # API endpoints
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── ai.py
│   │   │   ├── feedback.py
│   │   │   ├── knowledge_base.py
│   │   │   └── analytics.py
│   │   └── services/
│   │       └── llm_service.py   # Ollama LLM integration
│   ├── seed_data.py             # Database seeding
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── CustomerChat.tsx
│   │   │   ├── AgentDashboard.tsx
│   │   │   ├── Analytics.tsx
│   │   │   └── KnowledgeBase.tsx
│   │   └── services/
│   │       └── api.ts           # API client
│   └── package.json
│
└── README.md
```

## Key Differentiators

1. **Dual HITL Workflows**: Both pre-send and post-send paradigms
2. **Product Metrics**: Aligned with AI product management best practices
3. **Confidence Scoring**: Data-driven intervention decisions
4. **Feedback Architecture**: Structured collection for model improvement
5. **Operational Focus**: Tools for agents, metrics for ops teams
6. **Ollama Integration**: Local LLM inference with Llama 3.2
7. **Scalability Considerations**: Documented throughout codebase

## Production Roadmap

**To scale this to production:**

1. **Authentication & Authorization**: Add user management, role-based access
2. **Real-time Communication**: WebSockets for live updates
3. **Vector Database**: Pinecone/Weaviate for semantic search
4. **Model Fine-tuning**: Use collected feedback for RLHF
5. **Async Queue**: Celery/RabbitMQ for background processing
6. **Monitoring**: DataDog/Sentry for observability
7. **Database**: PostgreSQL for production scale
8. **Caching**: Redis for response caching
9. **LLM Router**: Multiple model support with cost optimization
10. **A/B Testing**: Experiment framework for model versions

## Configuration

### Environment Variables

- `AUTO_SEND_THRESHOLD`: Confidence threshold for auto-sending responses (default: 0.65)
- `OLLAMA_MODEL`: Ollama model name (default: "llama3.2")
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: "http://localhost:11434")

## License

MIT License. Feel free to use, modify, and distribute.

---

**© 2025 Germaine Luah. All rights reserved.**
