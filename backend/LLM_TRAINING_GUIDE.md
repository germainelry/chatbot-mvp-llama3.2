# LLM Training & Knowledge Integration Guide

## Complete Guide to Training, Fine-tuning, and RAG Systems

**Using Your AI Customer Support Assistant as Reference**

---

## 📖 Table of Contents

1. [⚠️ MUST READ: Does Your AI Actually Learn?](#-must-read-does-your-ai-actually-learn)
2. [Current System Overview](#current-system-overview)
3. [Understanding RAG (What You Built)](#understanding-rag)
4. [Knowledge Integration Approaches](#knowledge-integration-approaches)
5. [Fine-tuning Deep Dive](#fine-tuning-deep-dive)
6. [Data Collection vs Active Learning](#-critical-data-collection-vs-active-learning)
7. [Using Your Feedback Data](#using-your-feedback-data)
8. [Implementation Examples](#implementation-examples)
9. [Interview Talking Points](#interview-talking-points)
10. [Reality Check](#-quick-reality-check-what-your-system-does-vs-doesnt-do)

---

## ⚠️ MUST READ: Does Your AI Actually Learn?

### The Critical Question You'll Be Asked

**"When an agent clicks 'Helpful' on a response, what happens?"**

❌ **What You Might Think:**
> "The AI learns from that feedback and improves."

✅ **The Truth:**
> "Nothing happens to the AI. The feedback is stored in the database for future training."

### Why This Matters for Your Interview

This is THE question that separates candidates who understand AI systems from those who don't. Get this wrong and you'll lose credibility immediately.

**The Reality:**
1. ✅ Your system **COLLECTS** feedback (Phase 1 of RLHF)
2. ❌ Your system **DOES NOT** train on feedback (Phase 2 not implemented)
3. ✅ You're building a dataset for **FUTURE** fine-tuning
4. ❌ The AI model weights **NEVER** change from feedback

### What Actually Happens Step-by-Step

```
Agent clicks "Helpful" and resolves conversation
    ↓
Frontend: POST /api/feedback
    ↓
Backend: Creates Feedback record in SQLite
    ↓
Database: Stores rating + conversation_id + notes
    ↓
❌ No training pipeline runs
❌ No model update happens
❌ AI continues using base Llama 3.2
    ↓
✅ Data is ready for FUTURE training (when you implement it)
```

### The Two Things That DO Change Your AI

**1. Knowledge Base Updates (Immediate Effect via RAG):**
```
Agent adds new KB article
    ↓
Next customer query searches KB
    ↓
New article appears in search results
    ↓
✅ AI immediately has access to new info
```

**2. Prompt Changes (Immediate Effect):**
```
You modify the system prompt in code
    ↓
Restart backend
    ↓
✅ AI behavior changes immediately
```

### The Correct Interview Answer

**Question: "How does your system learn from agent feedback?"**

**Your Answer:**
> "Currently, we're in the data collection phase of RLHF. When agents provide feedback—ratings, corrections, and notes—we store that in our database along with the full conversation context. This creates a high-quality training dataset where every example is validated by an expert.
> 
> The AI doesn't automatically retrain because we're building the dataset first. Once we have 1,000+ validated examples, the next step would be implementing the training pipeline: extract the feedback data, format it for fine-tuning, train using LoRA to preserve the base model while adapting to our domain, A/B test against the baseline, and deploy if metrics improve.
> 
> The key advantage of this approach is we're collecting real-world data from actual conversations, which is far more valuable than synthetic training data. The feedback system is the foundation—the training pipeline is the next iteration."

---

## Current System Overview

### What You Built: RAG-Based System

Your AI Customer Support Assistant uses **Retrieval-Augmented Generation (RAG)** to provide contextual responses without training the model.

**Your Knowledge Base (from `seed_data.py`):**
```python
articles = [
    {
        "title": "Return & Refund Policy",
        "content": "Our return policy allows you to return items within 30 days...",
        "category": "Returns",
        "tags": "return,refund,exchange,policy,30 days"
    },
    {
        "title": "Shipping Information",
        "content": "We offer multiple shipping options...",
        "category": "Shipping", 
        "tags": "shipping,delivery,tracking,express,standard"
    },
    # ... more articles
]
```

**Key Point:** These articles are **NOT built into Llama 3.2**. They're stored in your SQLite database and retrieved on-demand.

---

## Understanding RAG

### What is RAG?

**RAG = Retrieval + Augmented + Generation**

1. **Retrieval**: Search for relevant information
2. **Augmented**: Add that information to the prompt
3. **Generation**: LLM generates response using the context

### Your RAG Implementation

**File: `backend/app/services/llm_service.py`**

```python
async def generate_ai_response(conversation_id: int, user_message: str, db: Session):
    """
    Generate AI response using Ollama or fallback logic.
    """
    
    # STEP 1: RETRIEVAL - Search knowledge base
    matched_articles = search_knowledge_base(user_message, db)
    
    # STEP 2: Build context from retrieved articles
    context = ""
    if matched_articles:
        context = "Relevant information:\n\n"
        for article in matched_articles[:2]:  # Top 2 matches
            context += f"**{article['title']}**\n{article['content'][:300]}...\n\n"
    
    # STEP 3: AUGMENTED - Inject context into prompt
    prompt = f"""You are a helpful customer support assistant. 
    Use the following information to answer:
    
    {context}
    
    Customer Question: {user_message}
    
    Provide a helpful, concise response."""
    
    # STEP 4: GENERATION - LLM generates response
    response = await generate_ollama_response(user_message, context)
    
    return {
        "response": response,
        "confidence_score": confidence,
        "matched_articles": matched_articles
    }
```

### How Your Retrieval Works

**File: `backend/app/services/llm_service.py`**

```python
def search_knowledge_base(query: str, db: Session) -> List[Dict]:
    """Simple keyword-based knowledge base search."""
    query_lower = query.lower()
    
    # Get all articles from database
    all_articles = db.query(KnowledgeBase).all()
    
    matched_articles = []
    for article in all_articles:
        # Combine searchable fields
        article_text = f"{article.title} {article.content} {article.tags}".lower()
        
        # Count keyword matches
        query_words = set(query_lower.split())
        article_words = set(article_text.split())
        common_words = query_words.intersection(article_words)
        
        if common_words:
            # Calculate match score
            match_score = len(common_words) / len(query_words)
            matched_articles.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "match_score": match_score
            })
    
    # Sort by relevance
    matched_articles.sort(key=lambda x: x["match_score"], reverse=True)
    return matched_articles[:3]  # Top 3
```

**Current Method:** Keyword matching (simple but works)

**Example Flow:**
```
User asks: "What's your return policy?"
    ↓
Query words: ["what's", "your", "return", "policy"]
    ↓
Search articles for matching words
    ↓
Article "Return & Refund Policy" has: ["return", "policy"] = 50% match
    ↓
Inject article content into prompt
    ↓
Llama 3.2 generates response using the context
    ↓
Return: "Our return policy allows returns within 30 days..."
```

---

## Knowledge Integration Approaches

There are **4 main ways** to give an LLM knowledge:

| Approach | How it Works | Best For | Your Use |
|----------|--------------|----------|----------|
| **1. RAG** | Retrieve & inject into prompt | Dynamic knowledge, frequent updates | ✅ Current |
| **2. Context Learning** | Include examples in prompt | Few examples, no training | ✅ Easy to add |
| **3. Fine-tuning** | Update model weights | Large datasets, specialized domain | 🔄 Future |
| **4. Pre-training** | Train from scratch | New language/domain | ❌ Too expensive |

---

## Approach 1: RAG (Your Current System)

### ✅ Pros
- **No training needed** - Works immediately
- **Knowledge updates instantly** - Just update database
- **Works with any LLM** - Not model-specific
- **Cheap** - No GPU required
- **Explainable** - You can see what context was used
- **Easy to debug** - Check retrieval results

### ❌ Cons
- **Limited by context window** - Can't fit entire knowledge base
- **Requires retrieval step** - Adds latency (~100ms)
- **Quality depends on retrieval** - Bad search = bad response

### 📈 Improving Your RAG System

#### **Upgrade 1: Semantic Search (Replace Keywords)**

**Current (Keywords):**
```python
# Matches exact words: "return" matches "return" but not "refund"
query_words = set(query_lower.split())
article_words = set(article_text.split())
common_words = query_words.intersection(article_words)
```

**Better (Semantic Search):**
```python
# Install
pip install sentence-transformers chromadb

# Create embeddings
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("knowledge_base")

# Embed all articles once
def embed_knowledge_base(db):
    articles = db.query(KnowledgeBase).all()
    for article in articles:
        embedding = embedding_model.encode(article.content)
        collection.add(
            documents=[article.content],
            embeddings=[embedding.tolist()],
            metadatas=[{
                "title": article.title,
                "category": article.category,
                "id": article.id
            }],
            ids=[f"article_{article.id}"]
        )

# Search with semantic similarity
def search_knowledge_base_semantic(query: str) -> List[Dict]:
    query_embedding = embedding_model.encode(query)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=3
    )
    return results
```

**Why Better:**
- "return policy" matches "refund guidelines" (semantic similarity)
- "shipping info" matches "delivery details"
- "password reset" matches "login problems"

**Example:**
```
Query: "How do I get my money back?"
    ↓
Embedding: [0.23, -0.45, 0.12, ...] (768 dimensions)
    ↓
Semantic search finds: "Return & Refund Policy" (high similarity)
    ↓
Even though query doesn't contain "return" or "refund"!
```

#### **Upgrade 2: Hybrid Search (Best of Both)**

```python
def search_knowledge_base_hybrid(query: str, db: Session):
    # Get keyword matches
    keyword_results = search_keyword(query, db)
    
    # Get semantic matches
    semantic_results = search_semantic(query)
    
    # Combine and rerank
    combined = combine_results(keyword_results, semantic_results)
    return rerank(combined)  # Use cross-encoder for final ranking
```

#### **Upgrade 3: Add Metadata Filtering**

```python
# Search only in specific category
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    where={"category": "Returns"}  # Filter by category
)

# Your current categories: Returns, Shipping, Account, Products
```

---

## Approach 2: Context Learning (In-Prompt Examples)

### What is it?

Adding example conversations to the prompt (no training needed).

### How to Add to Your System

**File: `backend/app/services/llm_service.py`**

```python
async def generate_ollama_response(user_message: str, context: str) -> str:
    """Generate response using Ollama LLM."""
    
    # Add few-shot examples
    examples = """
    Example conversations:
    
    User: What's your return policy?
    Assistant: Our return policy allows returns within 30 days of purchase for a full refund. Items must be in original condition with tags attached. Would you like help initiating a return?
    
    User: How long does shipping take?
    Assistant: We offer multiple shipping options: Standard (3-5 days), Express (2-3 days), and Overnight (1 day). Orders before 2 PM EST ship same day. Would you like to track an existing order?
    
    User: I forgot my password
    Assistant: I can help you reset your password. Go to the login page and click 'Forgot Password'. You'll receive a reset link via email valid for 24 hours. Need help with anything else?
    """
    
    prompt = f"""You are a helpful customer support assistant.

{examples}

Use the following information to answer the customer's question:

{context}

Customer Question: {user_message}

Provide a helpful, concise response."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response['message']['content']
```

### ✅ Pros
- Quick to implement
- Teaches tone and style
- No training needed
- Can update examples anytime

### ❌ Cons
- Uses context window space
- Only 3-5 examples fit
- Doesn't scale to hundreds of examples

---

## Approach 3: Fine-tuning

### What is Fine-tuning?

**Continuing to train** a pre-trained model on your specific data to update its weights.

### When to Fine-tune?

Fine-tune when you have:
- ✅ **1,000+ quality examples** (your feedback data!)
- ✅ **Consistent domain/style** you want to teach
- ✅ **Resources** for training (GPU or cloud)
- ✅ **Patterns** the model should internalize

**Don't fine-tune if:**
- ❌ Less than 100 examples
- ❌ Knowledge changes frequently
- ❌ RAG is working well

### Types of Fine-tuning

#### **Option A: Full Fine-tuning**

Update all model weights.

**Pros:** Best performance  
**Cons:** Very expensive (requires powerful GPU)  
**When:** Large datasets (10,000+ examples)

#### **Option B: LoRA (Low-Rank Adaptation) ⭐ Recommended**

Only update small "adapter" layers.

**Pros:** 
- Much cheaper (3GB GPU vs 80GB)
- Faster training
- Can merge adapters
- Preserve base model

**Cons:**
- Slightly less powerful than full fine-tuning

#### **Option C: QLoRA (Quantized LoRA)**

LoRA + 4-bit quantization.

**Pros:**
- Even cheaper (1GB GPU)
- Can run on consumer hardware
- Good quality

**Cons:**
- Need to load in 4-bit mode

---

## ⚠️ CRITICAL: Data Collection vs Active Learning

### What Actually Happens When You Click "Helpful"?

**Current Reality (Data Collection Phase):**

```
Agent clicks "Helpful" or provides correction
    ↓
Frontend sends POST /api/feedback
    ↓
Backend stores in SQLite database
    ↓
Data sits in "feedback" table
    ↓
❌ AI DOES NOT LEARN FROM THIS
    ↓
AI continues using base Llama 3.2 model (unchanged)
```

**What People THINK Happens (But Doesn't):**
- ❌ AI immediately learns from feedback
- ❌ Model improves automatically
- ❌ Future responses get better
- ❌ Feedback changes AI behavior

**What ACTUALLY Happens:**
- ✅ Feedback stored in database
- ✅ Shows in analytics dashboard
- ✅ Creates training dataset for FUTURE use
- ❌ No automatic retraining
- ❌ No model updates
- ❌ No immediate AI improvement

### Why Doesn't the AI Learn?

**You're in Phase 1: Data Collection**

```python
# What happens in backend/app/routers/feedback.py
@router.post("")
async def create_feedback(feedback: FeedbackCreate, db: Session):
    # Create feedback entry
    db_feedback = Feedback(
        conversation_id=feedback.conversation_id,
        rating=feedback.rating,
        agent_correction=feedback.agent_correction,
        notes=feedback.notes
    )
    
    db.add(db_feedback)
    db.commit()  # Just saves to database
    
    # ❌ No training happens here
    # ❌ No model update happens here
    # ❌ AI doesn't change at all
    
    return db_feedback
```

### The Three Phases of RLHF (V2 Updated)

**Phase 1: Data Collection (Implemented) ✅**
```
Agents provide feedback
    ↓
Store in TrainingData model
    ↓
Calculate evaluation metrics (BLEU, semantic similarity)
    ↓
Build training dataset
    ↓
Wait until enough data (1000+ examples)
```

**Phase 2: Retraining Pipeline (V2 - Implemented) ✅**
```
Manual trigger: POST /api/feedback/retrain
    ↓
Process unprocessed TrainingData entries
    ↓
Re-embed knowledge base articles (if corrections affect KB)
    ↓
Update few-shot intent examples (if corrections affect intent)
    ↓
Mark as "processed"
    ↓
✅ Knowledge base embeddings updated (immediate effect via RAG)
✅ Intent classification improved (immediate effect)
```

**Phase 3: Model Fine-tuning (Not Implemented Yet) ❌**
```
Extract 1000+ training examples
    ↓
Format for fine-tuning (JSONL)
    ↓
Fine-tune model with LoRA
    ↓
A/B test new vs old model
    ↓
Deploy improved model
    ↓
AI model weights actually change!
```

### Interview Clarification

**When asked: "How does your system learn from feedback?"**

**❌ WRONG Answer:**
> "When agents mark responses as helpful, the AI learns and improves."

**✅ CORRECT Answer:**
> "Currently, we're in the data collection phase of RLHF. When agents provide feedback, we store it in our database along with the full conversation context, ratings, and corrections. This creates a high-quality training dataset where every example is validated by an expert.
> 
> The AI doesn't automatically retrain—that's by design for an MVP. Once we have 1,000+ validated examples, we'll implement Phase 2: the training pipeline. This would extract the feedback data, fine-tune the model using LoRA, A/B test against the baseline, and deploy if metrics improve.
> 
> We're essentially building the infrastructure for continuous improvement. The feedback system is the foundation—next step is closing the loop with automated retraining."

---

## V2 Retraining Service

### What's Implemented in V2

**File: `backend/app/services/retraining_service.py`**

The V2 retraining service implements Phase 2 of RLHF:

1. **TrainingData Model**: Stores original AI response + agent correction pairs
2. **Retraining Pipeline**: Processes feedback and updates system components
3. **Export Function**: Exports training data in JSONL format for future fine-tuning

**Key Functions:**
- `collect_training_data()`: Creates TrainingData entries from Feedback
- `process_retraining()`: Processes unprocessed training data
- `export_training_data_jsonl()`: Exports for model fine-tuning

### What Actually Improves

**✅ Immediate Improvements (Phase 2):**
- Knowledge base embeddings updated → Better RAG retrieval
- Intent examples updated → Better intent classification
- Vector database re-initialized → Consistent semantic search

**❌ Not Yet Improved (Phase 3):**
- LLM model weights (requires fine-tuning)
- Base model behavior (still uses Llama 3.2 unchanged)

## Using Your Feedback Data for Fine-tuning

### You're Already Collecting Training Data! 🎉

**V2 TrainingData model collects:**

```python
# backend/app/models.py
class TrainingData(Base):
    feedback_id = ...  # Links to Feedback
    conversation_id = ...
    message_id = ...
    original_ai_response = ...  # What AI said
    agent_correction = ...  # What agent would say instead
    intent = ...  # Classified intent
    processed = ...  # 0 = unprocessed, 1 = processed
    processed_at = ...  # When retraining happened
```

**This is gold for training!** Phase 2 (retraining) improves embeddings/intent. Phase 3 (fine-tuning) would improve model weights.

### Extract Training Dataset (V2 - Already Implemented)

**V2 provides export function:**

```python
# backend/app/services/retraining_service.py
def export_training_data_jsonl(db: Session, limit: Optional[int] = None) -> str:
    """Export training data in JSONL format for model fine-tuning."""
    
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
```

**Usage:**
```python
# Trigger retraining (updates embeddings/intent)
POST /api/feedback/retrain

# Export processed training data for fine-tuning
GET /api/feedback/training-data/export
```

**This is ready for Phase 3 fine-tuning!** The JSONL format is compatible with LoRA fine-tuning pipelines.

### Fine-tuning with Ollama (Simplest)

**Step 1: Create Modelfile**

```bash
# File: Modelfile
FROM llama3.2

PARAMETER temperature 0.7
PARAMETER top_p 0.9

SYSTEM """You are a customer support assistant. You are helpful, professional, and concise.

Key policies:
- Returns: 30 days, original condition
- Shipping: Standard (3-5 days), Express (2-3 days)
- Always offer to escalate if unsure"""

# Add training examples from your best agent responses
MESSAGE user What's your return policy?
MESSAGE assistant Our return policy allows returns within 30 days of purchase for a full refund. Items must be in original condition with tags attached. To initiate a return: 1) Log into your account, 2) Go to Order History, 3) Click 'Request Return', 4) Print the prepaid label, 5) Ship within 5 business days. Would you like help with a specific return?

MESSAGE user How do I track my order?
MESSAGE assistant I can help you track your order! You'll receive a tracking number via email once your order ships. You can also track by: 1) Logging into your account, 2) Going to Order History, 3) Clicking on your order to see tracking info. Do you have your order number handy?

# ... add 50-100 more examples from your feedback data
```

**Step 2: Create custom model**

```bash
ollama create my-support-agent -f Modelfile
```

**Step 3: Use it**

```python
# In your llm_service.py, change model name
OLLAMA_MODEL = "my-support-agent"  # Instead of "llama3.2"
```

### Fine-tuning with LoRA (Advanced, Better Quality)

```python
# Install dependencies
pip install transformers peft accelerate bitsandbytes datasets

# Load training data
from datasets import Dataset
import json

# Load your extracted training data
with open("training_data.jsonl", "r") as f:
    data = [json.loads(line) for line in f]

dataset = Dataset.from_list(data)

# Load base model
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model_name = "meta-llama/Llama-3.2-3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,  # QLoRA - use 4-bit
    device_map="auto"
)

# Prepare for training
model = prepare_model_for_kbit_training(model)

# Configure LoRA
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Train
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./my-support-model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()

# Save
model.save_pretrained("./my-support-model-lora")
tokenizer.save_pretrained("./my-support-model-lora")
```

### Loading Your Fine-tuned Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B")

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "./my-support-model-lora")

# Merge adapter with base (optional, for faster inference)
model = model.merge_and_unload()

# Use it
tokenizer = AutoTokenizer.from_pretrained("./my-support-model-lora")
inputs = tokenizer("What's your return policy?", return_tensors="pt")
outputs = model.generate(**inputs, max_length=200)
response = tokenizer.decode(outputs[0])
```

---

## Approach 4: Hybrid (RAG + Fine-tuning) ⭐ Best of Both

### The Winning Strategy

**Combine RAG with fine-tuned model:**

1. **Fine-tune** on your agent conversations to learn:
   - Tone and style
   - Common patterns
   - How to structure responses
   
2. **Use RAG** for:
   - Specific policies (can change)
   - Recent information
   - Detailed procedures

```python
# Pseudo-code for hybrid approach
async def generate_response(query, db):
    # 1. Retrieve relevant knowledge (RAG)
    articles = search_knowledge_base(query, db)
    context = build_context(articles)
    
    # 2. Use fine-tuned model (knows your style)
    prompt = f"{context}\n\nUser: {query}\nAssistant:"
    response = fine_tuned_model.generate(prompt)
    
    return response
```

**Benefits:**
- ✅ Model knows your company's communication style
- ✅ Can still update knowledge without retraining
- ✅ Best accuracy
- ✅ Fastest inference

---

## Decision Framework

### Choose Your Approach

```
Do you have < 100 training examples?
    ↓ YES
    Use RAG only
    Add few-shot examples to prompts
    
    ↓ NO
    
Do you have 100-1000 examples?
    ↓ YES
    Use RAG + Context Learning
    Consider Ollama Modelfile approach
    
    ↓ NO
    
Do you have 1000+ examples?
    ↓ YES
    
Is your knowledge static or dynamic?
    ↓ DYNAMIC (changes often)
    Use RAG + Fine-tuning hybrid
    Fine-tune for style, RAG for facts
    
    ↓ STATIC (rarely changes)
    Consider full fine-tuning
    Or fine-tuning + RAG for best results
```

### For Your V2 System

**Now (V2 - Implemented):**
- ✅ Vector RAG with semantic search (sentence-transformers + ChromaDB)
- ✅ Collecting feedback data (TrainingData model)
- ✅ Retraining pipeline (updates embeddings/intent)
- ✅ Evaluation metrics (BLEU, semantic similarity, CSAT)
- ✅ Multi-agent orchestration

**Next 1-2 months (100+ feedbacks):**
- 🔄 Create custom Ollama model with Modelfile
- 🔄 Use best agent responses as training examples
- 🔄 Improve retraining automation (scheduled triggers)

**Next 3-6 months (1000+ feedbacks):**
- 🔄 Fine-tune with LoRA on collected feedback (Phase 3)
- 🔄 Hybrid: Fine-tuned model + Vector RAG retrieval
- 🔄 A/B test vs base model (framework already implemented)
- 🔄 Automated retraining pipeline (scheduled)

---

## Implementation Examples

### Example 1: Add Semantic Search to Your System

**Step 1: Install dependencies**
```bash
pip install sentence-transformers chromadb
```

**Step 2: Create embedding service**

```python
# File: backend/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("knowledge_base")
    
    def embed_knowledge_base(self, articles: List[Dict]):
        """Embed all knowledge base articles."""
        for article in articles:
            embedding = self.model.encode(article['content'])
            self.collection.add(
                documents=[article['content']],
                embeddings=[embedding.tolist()],
                metadatas=[{
                    "id": article['id'],
                    "title": article['title'],
                    "category": article['category']
                }],
                ids=[f"article_{article['id']}"]
            )
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search knowledge base with semantic similarity."""
        query_embedding = self.model.encode(query)
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        return results

# Initialize on startup
embedding_service = EmbeddingService()
```

**Step 3: Update your llm_service.py**

```python
# Add to backend/app/services/llm_service.py

from app.services.embedding_service import embedding_service

def search_knowledge_base_semantic(query: str) -> List[Dict]:
    """Search using semantic similarity instead of keywords."""
    results = embedding_service.search(query, n_results=3)
    
    matched_articles = []
    for i, doc in enumerate(results['documents'][0]):
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        
        # Convert distance to similarity score (0-1)
        similarity = 1 / (1 + distance)
        
        matched_articles.append({
            "id": metadata['id'],
            "title": metadata['title'],
            "content": doc,
            "category": metadata['category'],
            "match_score": similarity
        })
    
    return matched_articles

# Update generate_ai_response to use semantic search
async def generate_ai_response(conversation_id: int, user_message: str, db: Session):
    # Use semantic search instead of keyword
    matched_articles = search_knowledge_base_semantic(user_message)
    # ... rest stays the same
```

**Step 4: Embed articles on startup**

```python
# In backend/app/main.py

from app.services.embedding_service import embedding_service

@app.on_event("startup")
async def startup_event():
    init_db()
    print("🚀 Database initialized")
    
    # Embed knowledge base
    from app.models import KnowledgeBase
    db = SessionLocal()
    articles = db.query(KnowledgeBase).all()
    article_dicts = [{
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "category": a.category
    } for a in articles]
    embedding_service.embed_knowledge_base(article_dicts)
    print("🧠 Knowledge base embedded")
    
    db.close()
```

### Example 2: Extract Training Data Script

```python
# File: backend/extract_training_data.py

from app.database import SessionLocal
from app.models import Feedback, Conversation, Message
import json

def extract_training_data():
    db = SessionLocal()
    
    training_examples = []
    
    # Get helpful feedback
    helpful_feedback = db.query(Feedback).filter(
        Feedback.rating == "helpful"
    ).all()
    
    for feedback in helpful_feedback:
        messages = db.query(Message).filter(
            Message.conversation_id == feedback.conversation_id
        ).order_by(Message.created_at).all()
        
        conversation = []
        for msg in messages:
            if msg.message_type == "customer":
                conversation.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.message_type in ["final", "agent_edited", "agent_only"]:
                conversation.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        if len(conversation) >= 2:  # At least one exchange
            training_examples.append({
                "messages": conversation,
                "rating": "helpful"
            })
    
    # Get corrections
    corrections = db.query(Feedback).filter(
        Feedback.agent_correction.isnot(None)
    ).all()
    
    for feedback in corrections:
        messages = db.query(Message).filter(
            Message.conversation_id == feedback.conversation_id
        ).order_by(Message.created_at).all()
        
        conversation = []
        for msg in messages[:-1]:  # All except last
            if msg.message_type == "customer":
                conversation.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.message_type in ["final", "agent_edited"]:
                conversation.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        # Add corrected response as the "right" answer
        conversation.append({
            "role": "assistant",
            "content": feedback.agent_correction
        })
        
        training_examples.append({
            "messages": conversation,
            "rating": "corrected",
            "notes": feedback.notes
        })
    
    # Save to JSONL
    with open("training_data.jsonl", "w") as f:
        for example in training_examples:
            f.write(json.dumps(example) + "\n")
    
    print(f"✅ Extracted {len(training_examples)} training examples")
    db.close()

if __name__ == "__main__":
    extract_training_data()
```

**Run it:**
```bash
cd backend
python extract_training_data.py
```

---

## Interview Talking Points

### Question: "How do you train the AI on your knowledge base?"

**Your Answer:**

> "I implemented a RAG system where we retrieve relevant articles from our knowledge base and inject them into the LLM's context window. This means the model doesn't need training—it uses the information we provide in real-time. The key advantage is that knowledge updates are instant: when an agent adds a new article or updates a policy, the AI immediately has access to it.
>
> For retrieval, I started with keyword matching for MVP speed, but I've architected it to easily upgrade to semantic search using vector embeddings. That would improve match quality significantly.
>
> Importantly, we're collecting high-quality training data through our HITL feedback system. Agent corrections and ratings form preference pairs perfect for fine-tuning. Once we have 1,000+ examples, we can fine-tune using techniques like LoRA to teach the model our company's tone and common patterns, while keeping RAG for dynamic facts. That hybrid approach gives us the best of both worlds."

### Question: "What's the difference between RAG and fine-tuning?"

**Your Answer:**

> "RAG is about giving the model information at inference time—you search your knowledge base and add relevant context to the prompt. No training needed, updates are instant, and it works with any LLM. The tradeoff is it requires a retrieval step and is limited by context window size.
>
> Fine-tuning actually updates the model's weights by continuing training on your domain-specific data. The model 'learns' your patterns and can internalize knowledge. It's better for teaching tone, style, and frequent patterns, but it's expensive, requires quality training data, and updates mean retraining.
>
> The best approach is often hybrid: fine-tune on your conversation style and common patterns, then use RAG for specific facts and policies that change. That's our roadmap—RAG now for agility, fine-tuning later when we have enough data."

### Question: "How do you collect data for model improvement?"

**Your Answer:**

> "Our HITL system is designed for this. Every AI response can be reviewed by agents who provide ratings—helpful, not helpful, or needs improvement—plus optional corrections showing what they would have said instead. We also track when agents edit AI drafts before sending.
>
> This creates perfect training data for RLHF: preference pairs (AI response vs agent correction), reward signals (ratings), full conversation context, and qualitative feedback explaining why changes were needed.
>
> We're essentially building a high-quality dataset where every data point is validated by an expert. That's gold for fine-tuning. The feedback loop is: agents correct → we collect data → we fine-tune → model improves → fewer corrections needed. It's a virtuous cycle."

### Question: "What would you build next?"

**Your Answer:**

> "Three priorities:
>
> 1. **Upgrade retrieval to semantic search**: Move from keyword matching to vector embeddings using sentence transformers. This would significantly improve article matching quality, especially for paraphrased questions.
>
> 2. **Close the feedback loop**: Once we have 500-1000 quality examples, implement automated retraining. Extract training data from feedback, fine-tune using LoRA, A/B test the new model, and deploy if metrics improve. Make this a continuous cycle.
>
> 3. **Intent classification**: Add a classifier to categorize incoming questions (returns, shipping, technical, etc.) to enable better routing, specialized prompts per category, and topic-based analytics to identify knowledge gaps.
>
> Long-term, I'd explore multi-agent orchestration—specialist agents per domain with a router agent for intent-based routing. But RAG + fine-tuning hybrid would deliver the most immediate value."

---

## Summary Comparison Table

| Aspect | RAG (Current) | Fine-tuning | Hybrid (Best) |
|--------|---------------|-------------|---------------|
| **Training needed** | ❌ No | ✅ Yes | ✅ Yes |
| **Update speed** | ⚡ Instant | 🐌 Requires retraining | ⚡ Instant (RAG part) |
| **Cost** | 💰 Low | 💰💰💰 High | 💰💰 Medium |
| **Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Great | ⭐⭐⭐⭐⭐ Best |
| **Best for** | Dynamic knowledge | Learning style/patterns | Production systems |
| **Your timeline** | ✅ Now | 🔄 3-6 months | 🔄 6+ months |
| **Data needed** | 0 examples | 1000+ examples | 1000+ examples |
| **GPU required** | ❌ No | ✅ Yes | ✅ Yes (one-time) |

---

## Key Takeaways

1. **RAG is perfect for MVP** - No training, instant updates, works great
2. **You're collecting training data** - Your feedback system is building a dataset
3. **Semantic search is low-hanging fruit** - Big improvement, easy to implement
4. **Fine-tuning is the long-term play** - Wait until you have 1000+ examples
5. **Hybrid is the goal** - Fine-tune for style, RAG for facts
6. **Your architecture supports all approaches** - No major refactor needed

---

## Resources for Deep Learning

**Semantic Search:**
- Sentence Transformers: https://www.sbert.net/
- ChromaDB: https://www.trychroma.com/

**Fine-tuning:**
- Hugging Face PEFT: https://huggingface.co/docs/peft
- LoRA paper: https://arxiv.org/abs/2106.09685
- QLoRA: https://arxiv.org/abs/2305.14314

**RAG:**
- LangChain RAG: https://python.langchain.com/docs/use_cases/question_answering/
- RAG paper: https://arxiv.org/abs/2005.11401

**RLHF:**
- OpenAI's RLHF: https://openai.com/research/learning-from-human-preferences
- Anthropic's Constitutional AI: https://arxiv.org/abs/2212.08073

---

---

## 🎯 Quick Reality Check: What Your V2 System Does vs Doesn't Do

### Does Your AI "Learn" Right Now?

**❌ NO - Model Weights Don't Change:**
- Clicking "Helpful" does NOT fine-tune the model
- Agent corrections do NOT update LLM weights
- Feedback does NOT change base model behavior
- The AI still uses base Llama 3.2 (unchanged)

**✅ YES - System Components DO Improve (V2 Phase 2):**
- Knowledge base embeddings updated → Better RAG retrieval (immediate)
- Intent examples updated → Better intent classification (immediate)
- Vector database re-initialized → Consistent semantic search (immediate)
- Prompt changes → Immediate effect
- Feedback → Stored for FUTURE model fine-tuning (Phase 3)
- Analytics → Shows feedback trends and evaluation metrics

### The Complete Picture

```
┌─────────────────────────────────────────────────────────┐
│ WHAT'S IMPLEMENTED (V2 - Phase 1 & 2)                  │
├─────────────────────────────────────────────────────────┤
│ ✅ Vector RAG with semantic search (sentence-transformers)│
│ ✅ Feedback collection system (TrainingData model)      │
│ ✅ Retraining pipeline (updates embeddings/intent)      │
│ ✅ Evaluation metrics (BLEU, semantic similarity, CSAT) │
│ ✅ Multi-agent orchestration                            │
│ ✅ Analytics dashboard                                  │
│ ✅ Knowledge base CRUD with auto-embedding              │
│ ✅ A/B testing framework                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ WHAT'S NOT IMPLEMENTED (Phase 3)                        │
├─────────────────────────────────────────────────────────┤
│ ❌ Model fine-tuning (LLM weights don't change)        │
│ ❌ Automatic scheduled retraining                       │
│ ❌ Model deployment automation                          │
│ ❌ Few-shot examples in prompts (easy to add)          │
└─────────────────────────────────────────────────────────┘
```

### When to Say What in Your Interview

**Question: "Does your AI learn from feedback?"**

❌ **WRONG:** "Yes, when agents click 'Helpful', the AI learns and improves."

✅ **CORRECT (V2):** "We're in Phase 1 and Phase 2 of RLHF. Phase 1 collects high-quality training data—agent feedback is stored in our TrainingData model with full context, ratings, and corrections. Phase 2 (retraining pipeline) is implemented: we can trigger retraining which updates knowledge base embeddings and intent classification examples, improving the system immediately through better RAG and intent routing. Phase 3 (model fine-tuning) is next: once we have 1,000+ validated examples, we'll extract the data, fine-tune with LoRA, A/B test, and deploy. The infrastructure is ready; we're building the dataset and already improving system components."

**Question: "What's few-shot learning?"**

❌ **WRONG:** "It's when the model learns from a few examples of feedback."

✅ **CORRECT:** "Few-shot learning is adding 3-5 example Q&A pairs directly in the prompt—no training needed. The model sees examples and mimics the pattern. It's different from fine-tuning, which actually updates model weights. I could easily add few-shot examples to our prompts right now for immediate style improvements."

**Question: "How does RAG work in your system?"**

❌ **WRONG:** "RAG trains the model on our knowledge base."

✅ **CORRECT (V2):** "RAG retrieves relevant knowledge base articles at inference time and injects them into the prompt. The model doesn't train on the KB—it reads articles in real-time. This means updates are instant: when agents add a new article, embeddings are generated automatically and the AI immediately has access via semantic search. V2 uses vector embeddings (sentence-transformers + ChromaDB) for semantic search, which dramatically improves retrieval quality over keyword matching."

### Your Three-Phase Roadmap (For Interview)

**Phase 1: Data Collection (V2 - Implemented) ✅**
- ✅ Vector RAG implementation (semantic search)
- ✅ Feedback system (TrainingData model)
- ✅ Knowledge base management with auto-embedding
- ✅ Analytics dashboard with evaluation metrics
- ✅ Multi-agent orchestration
- ✅ A/B testing framework
- 🎯 Goal: Collect 1000+ quality examples

**Phase 2: Retraining Pipeline (V2 - Implemented) ✅**
- ✅ Retraining service (updates embeddings/intent)
- ✅ Training data export (JSONL format)
- ✅ Evaluation metrics calculation
- 🔄 Add few-shot examples to prompts (easy to add)
- 🔄 Automated scheduled retraining (future)
- 🎯 Goal: System components improving continuously

**Phase 3: Model Fine-tuning (Future) 📈**
- 📈 Extract 1000+ training examples
- 📈 Fine-tune model with LoRA
- 📈 A/B test vs base model
- 📈 Deploy improved model
- 🎯 Goal: LLM model weights actually improve

---

**You have a production-ready RAG system with a clear path to fine-tuning. That's exactly what they're looking for! 🚀**

