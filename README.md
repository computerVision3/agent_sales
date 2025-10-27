# Agent Sales Platform

A sophisticated full-stack application that combines AI-powered sales agents with data analysis capabilities. Built with React and Python, this platform leverages LangChain and advanced AI tools to provide intelligent data analysis, web searching, and interactive chat functionalities.

## Overview

This platform is designed to:
- Process and analyze sales data using AI-powered agents
- Perform intelligent web searches for business intelligence
- Analyze CSV data files with natural language queries
- Provide real-time chat interface with AI agents
- Store conversation history in PostgreSQL
- Handle streaming responses for real-time updates

## Project Structure

```
├── frontend/                 # Next.js frontend application
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components for chat UI
│   │   ├── chat-header.tsx  # Chat interface header
│   │   ├── chat-message.tsx # Message component
│   │   ├── chat-window.tsx  # Main chat container
│   │   └── message-input.tsx# User input component
│   ├── hooks/              # Custom React hooks
│   └── styles/             # CSS and styling files
└── backend/                # FastAPI Python backend
    ├── agents/             # AI agent implementation
    │   ├── nodes.py        # Agent processing nodes
    │   ├── tools.py        # Agent tool definitions
    │   └── config.py       # Agent configuration
    ├── tools/              # Utility tools
    │   ├── data_analyzer.py# CSV data analysis tool
    │   ├── web_search.py   # Web search functionality
    │   └── zauba_corp.py   # Corporate data tools
    ├── settings/           # Configuration
    └── api/                # FastAPI routes
```

## Key Features

### Data Analysis
- CSV file processing with natural language queries
- Pandas DataFrame integration for data manipulation
- Intelligent data summarization and insights
- Support for multiple data formats and sources

### AI Integration
- LangChain-powered conversational agents
- DuckDuckGo web search integration
- PostgreSQL chat history management
- Asynchronous tool execution pipeline

### User Interface
- Modern, responsive chat interface
- Real-time updates via server-sent events
- Streaming response support
- Rich UI components using Radix UI

## Tech Stack

### Frontend
- Next.js 14+ for server-side rendering
- React with TypeScript for type safety
- Radix UI Components for accessible UI elements
- Server-Sent Events (SSE) for real-time updates

### Backend
- Python 3.13+ with async support
- FastAPI for high-performance API endpoints
- LangChain for AI agent orchestration
- LangGraph for workflow management
- PostgreSQL for persistent storage
- Pydantic for data validation
- DuckDuckGo integration for web searches

## Prerequisites

- Python 3.13 or higher
- Node.js
- pnpm (for frontend package management)
- Docker (for containerization)

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -e .
   ```

3. Configure environment variables:
   - Set up PostgreSQL connection details
   - Configure any required API keys
   - Set model parameters if needed

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Start the development server:
   ```bash
   pnpm dev
   ```

## Docker Support

The project includes Docker support for containerized deployment:

```bash
# Build and start all services
docker-compose up --build

# Start specific services
docker-compose up frontend backend
```

## API Endpoints

### Chat Interface
- `GET /stream`: Server-sent events endpoint for real-time chat
- Additional endpoints for chat history and session management

### Data Analysis
- Endpoints for CSV file processing
- Data analysis query endpoints
- Web search integration endpoints

## Development Guidelines

### Adding New Tools
1. Create a new tool in `backend/tools/`
2. Define input/output schemas using Pydantic
3. Register the tool with the agent system
4. Update API routes if needed

### Frontend Components
- Use Radix UI for consistent styling
- Follow TypeScript type definitions
- Implement error boundaries where needed
- Handle loading and error states

## Project Status

Current version: 0.1.0 (Development)

### Upcoming Features
- Enhanced data analysis capabilities
- Additional data source integrations
- Improved chat history management
- Advanced agent orchestration

## License

[Add appropriate license information]