# Quick Start Guide (Windows) - V2 Multi-Agent Platform

Follow these steps to get the V2 Multi-Agent AI Customer Support Assistant running in under 10 minutes.

## Prerequisites Check

```powershell
# Check Python version (need 3.9+)
python --version

# Check Node.js version (need 18+)
node --version

# Check npm
npm --version
```

If any are missing, install them first.

## Step 1: Backend Setup (5 minutes)

Open PowerShell in the project root:

```powershell
# Navigate to backend
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies (this may take a few minutes - includes vector embeddings)
pip install -r requirements.txt

# Note: First run will download sentence-transformers model (~90MB)
# This enables Vector RAG for semantic search

# Seed database with sample data
python seed_data.py

# Note: ChromaDB will initialize automatically on first use
# Vector embeddings are generated automatically when knowledge base articles are created

# Start backend server
uvicorn app.main:app --reload
```

✅ Backend should now be running at http://localhost:8000

Leave this PowerShell window open!

## Step 2: Frontend Setup (3 minutes)

Open a NEW PowerShell window in the project root:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies (this may take a few minutes)
npm install

# Start frontend dev server
npm run dev
```

✅ Frontend should now be running at http://localhost:5173

Leave this PowerShell window open!

## Step 3: Open Application

Open your browser and navigate to: **http://localhost:5173**

You should see the AI Customer Support Assistant interface!

## Step 4: Test the System

### Test Customer Chat:
1. Click "Customer Chat" in the navigation
2. Send a message: "What's your return policy?"
3. You should get an AI response based on the seeded knowledge base

### Test Agent Dashboard:
1. Click "Agent Dashboard"
2. You'll see the conversation you just created
3. Click on it to see the messages
4. Try sending a new customer message to generate an AI draft

### Test Analytics:
1. Click "Analytics"
2. View the metrics dashboard
3. See the feedback history

### Test Knowledge Base:
1. Click "Knowledge Base"
2. Browse the pre-seeded articles
3. Try searching for "return"

## Optional: Ollama Setup (Advanced)

If you want to use real LLM responses instead of fallback:

1. Download Ollama from: https://ollama.ai
2. Install it
3. Open a NEW PowerShell window:

```powershell
# Start Ollama service
ollama serve

# In another window, pull the model
ollama pull llama3.2
```

The system will automatically use Ollama if it's running!

**Note:** The V2 system works with fallback responses, but Ollama enables:
- Multi-agent orchestration with real LLM responses
- Intent classification with embedding similarity
- Better quality responses from Knowledge Agent

## Troubleshooting

### Backend won't start:
- Check if port 8000 is already in use
- Make sure you're in the `backend` directory
- Verify Python version is 3.9+

### Frontend won't start:
- Check if port 5173 is already in use
- Make sure you're in the `frontend` directory
- Try deleting `node_modules` and running `npm install` again

### Database errors:
- Delete `backend/chatbot.db` and run `python seed_data.py` again

### CORS errors in browser:
- Make sure backend is running
- Check that both servers are on localhost

## Stopping the Application

Press `Ctrl+C` in each PowerShell window to stop the servers.

## V2 Features to Test

### Test Vector RAG:
1. Go to Knowledge Base
2. Add a new article (embeddings generated automatically)
3. Ask a question with different wording (semantic search finds it)

### Test Multi-Agent System:
1. Send: "What's your return policy?" → Routes to Knowledge Agent
2. Send: "I'm very unhappy with my order" → Routes to Escalation Agent
3. Check Agent Dashboard to see intent classification

### Test Evaluation Metrics:
1. Provide agent feedback with corrections
2. Check Analytics → Evaluation Metrics
3. See BLEU score and semantic similarity

## What's Next?

- Check out `V2_DEMO_SCRIPT.md` for a guided V2 demo walkthrough
- Read `V2_ARCHITECTURE.md` for system architecture details
- Read `V2_TECHNICAL_FLOW.md` for technical flow explanation
- Read `README.md` for project overview
- Explore the code to understand the implementation

---

**Ready for your interview! Good luck! 🚀**

