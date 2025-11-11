# AI Customer Support Frontend

React + TypeScript frontend for AI Customer Support Assistant with Human-in-the-Loop workflows.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run development server:
```bash
npm run dev
```

Frontend will run at: http://localhost:5173

## Pages

### Customer Chat (`/customer`)
- Simple chat interface for customers
- Real-time AI responses
- Auto-send for high-confidence responses
- Queue low-confidence for agent review

### Agent Dashboard (`/agent`)
- Conversation queue with status filters
- AI draft review interface
- Confidence scoring indicators
- Pre-send review workflow (edit/approve/escalate)
- Post-send feedback collection
- HITL decision points clearly marked

### Analytics (`/analytics`)
- Key product metrics dashboard
- Deflection rate (% handled without escalation)
- Resolution rate
- Average confidence scores
- Feedback sentiment analysis
- Recent feedback history table

### Knowledge Base (`/knowledge-base`)
- CRUD interface for articles
- Category organization
- Search and filter
- Tag management
- Used by AI for context

## Architecture

### HITL Workflow Implementation

**Pre-Send Review (Primary):**
1. Customer message → AI generates draft
2. Confidence score calculated
3. If < 70%, queued for agent review
4. Agent can: send as-is, edit, or escalate
5. Edits tracked for feedback loop

**Post-Send Feedback:**
1. After sending, agent provides rating
2. Helpful/Not Helpful/Needs Improvement
3. Optional correction and notes
4. Data collected for model training

### Components
- Clean separation of concerns
- Type-safe API calls
- Real-time updates
- Responsive design
- Loading states and error handling

## Key Discussion Points

**Product Thinking:**
- HITL workflow balances automation vs quality
- Confidence thresholds configurable based on business needs
- Metrics track operational efficiency and AI quality
- Feedback loop enables continuous improvement

**Technical Decisions:**
- TypeScript for type safety
- Axios for API abstraction
- React Router for SPA navigation
- Tailwind for rapid UI development
- Real-time polling (would use WebSockets in production)

**Scalability:**
- Component-based architecture
- API service layer for easy backend swaps
- State management ready for Redux/Zustand
- Could add real-time with Socket.io
- Ready for authentication layer

