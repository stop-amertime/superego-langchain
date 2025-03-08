# Superego LangGraph Integration

This project integrates a React frontend with a LangGraph backend to enhance Superego's agentic capabilities. The system uses WebSockets for real-time communication, with LangGraph providing structured agent workflows.

## Project Structure

```
/
├── backend/                # Python FastAPI and LangGraph backend
│   ├── app/                
│   │   ├── agents.py       # LangGraph agent implementation
│   │   ├── llm_client.py   # OpenRouter API client
│   │   ├── main.py         # FastAPI server with WebSocket support
│   │   └── models.py       # Data models for the application
│   ├── .env                # Environment variables (API keys)
│   ├── requirements.txt    # Python dependencies
│   └── run.py              # Script to run the backend server
│
└── frontend/              # React frontend
    ├── src/
    │   ├── api/           # API clients (WebSocket)
    │   ├── components/    # UI components
    │   ├── types/         # TypeScript type definitions
    │   ├── App.tsx        # Main application component
    │   └── main.tsx       # Entry point
    ├── package.json       # Node.js dependencies
    └── index.html         # HTML entry point
```

## Prerequisites

- Python 3.8+
- Node.js 14+
- OpenRouter API key (for LLM access)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd superego-langchain
```

### 2. Backend Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
# Edit .env file and add your OpenRouter API key
OPENROUTER_API_KEY=your_key_here
```

### 3. Frontend Setup

```bash
# Install Node.js dependencies
cd ../frontend
npm install
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
python run.py
```

The backend server will start on http://localhost:8000.

### 2. Start the Frontend Development Server

```bash
cd ../frontend
npm run dev
```

The frontend development server will start on http://localhost:3000.

## Key Features

1. **Superego Input Screening**: Evaluates user requests before processing
2. **LangGraph Agents**: Structured workflow for processing requests
3. **Real-time Communication**: WebSockets enable streaming responses
4. **Thinking Visibility**: See the LLM's thought process during evaluation

## API Endpoints

- `GET /` - Health check endpoint
- `GET /constitution` - Get the current Superego constitution
- `POST /conversations` - Create a new conversation
- `GET /conversations/{conversation_id}` - Get a conversation by ID
- `WebSocket /ws/{client_id}` - WebSocket endpoint for real-time communication

## Environment Variables

### Backend (.env)

- `OPENROUTER_API_KEY` - API key for OpenRouter (required)
- `HOST` - Host to run the backend server on (default: 0.0.0.0)
- `PORT` - Port to run the backend server on (default: 8000)
- `BASE_MODEL` - Model to use for the base LLM (default: anthropic/claude-3.7-sonnet)
- `SUPEREGO_MODEL` - Model to use for the Superego (default: anthropic/claude-3.7-sonnet:thinking)

## Future Improvements

- Additional tool integrations (web search, file reading, etc.)
- More sophisticated superego output monitoring
- Enhanced UI for viewing agent actions and tool usage
- Better handling of conversation history and persistence
