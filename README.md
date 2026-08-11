# InboxIQ

### AI-Powered Email Copilot for Gmail

InboxIQ is an AI-powered email assistant built on top of Gmail that helps users understand, prioritize, and respond to emails faster. It combines LLM-powered analysis with Gmail integration to provide summaries, smart replies, importance scoring, phishing detection, action-item extraction, and more.

InboxIQ is designed around a **human-in-the-loop workflow**: AI generates recommendations and drafts, but emails are never sent automatically.

---

## Features

* **AI Summarization** — Generate 15-second, detailed, or bullet-point summaries.
* **Smart Replies** — Generate context-aware replies based on the email, thread history, importance, and tone.
* **AI Email Writer** — Generate emails from a simple instruction and adjust tone, length, and style.
* **Importance Scoring** — Classify emails by importance and identify positive/negative signals affecting the score.
* **Priority Detection** — Categorize messages as critical, high, medium, or low priority.
* **Phishing Detection** — Identify suspicious emails and explain potential security risks in plain English.
* **Action Items** — Extract tasks, deadlines, and follow-up requirements from emails.
* **Tone Analysis** — Analyze drafts for potentially inappropriate, aggressive, or unclear language.
* **Email Simplification** — Rewrite complicated emails into clear, plain English.
* **Thread Summaries** — Summarize conversations, decisions, and outstanding questions.
* **Category Filtering** — Organize messages into categories such as important, requires action, informational, newsletters, and low-value mail.

---

## Architecture

InboxIQ uses a containerized full-stack architecture:

```text
                    ┌──────────────────┐
                    │      Gmail       │
                    │     Gmail API    │
                    └────────┬─────────┘
                             │ OAuth 2.0
                             ▼
┌─────────────────────────────────────────────────┐
│                  Next.js Frontend                │
│           TypeScript + Tailwind CSS              │
└───────────────────────┬─────────────────────────┘
                        │ REST API
                        ▼
┌─────────────────────────────────────────────────┐
│                  FastAPI Backend                 │
│                                                 │
│  Auth │ Gmail │ AI Services │ REST API │ JWT    │
└───────────────┬─────────────────┬───────────────┘
                │                 │
                ▼                 ▼
        ┌──────────────┐   ┌──────────────┐
        │ PostgreSQL   │   │ Celery/Redis │
        │  + pgvector  │   │ Background   │
        │              │   │ Processing   │
        └──────────────┘   └──────┬───────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │   LLM Provider │
                         │ Groq / OpenAI  │
                         └────────────────┘
```

### AI Processing Pipeline

New emails are processed through multiple AI services concurrently:

```text
Gmail Sync
    ↓
Email Ingestion
    ↓
Concurrent AI Analysis
    ├── Summarization
    ├── Importance
    ├── Priority
    ├── Phishing Detection
    └── Action Items
    ↓
PostgreSQL
    ↓
InboxIQ Dashboard
```

Background processing is handled with **Celery and Redis**, while database operations use **async SQLAlchemy** with isolated sessions for concurrent tasks.

---

## Technology Stack

| Layer             | Technology                              |
| ----------------- | --------------------------------------- |
| Frontend          | Next.js, TypeScript, Tailwind CSS       |
| Backend           | Python, FastAPI                         |
| Database          | PostgreSQL, pgvector                    |
| ORM               | SQLAlchemy                              |
| AI                | Groq, OpenAI-compatible LLM abstraction |
| Background Jobs   | Celery, Redis                           |
| Authentication    | Google OAuth 2.0, JWT                   |
| Email Integration | Gmail API                               |
| Migrations        | Alembic                                 |
| Infrastructure    | Docker, Docker Compose                  |

---

## Getting Started

### Prerequisites

* Docker Desktop
* Google Cloud project
* Gmail API enabled
* Google OAuth credentials
* Groq API key or compatible LLM provider

### 1. Clone the repository

```bash
git clone <repository-url>
cd InboxIQ
```

### 2. Configure environment variables

Create the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Create the frontend environment file:

```bash
cp frontend/.env.local.example frontend/.env.local
```

Configure your API keys, database settings, and Google OAuth credentials in the appropriate files.

### 3. Start the application

```bash
docker compose up --build
```

The application will be available at:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

---

## Project Structure

```text
InboxIQ/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── llm/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── ai/
│   │   └── workers/
│   ├── alembic/
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
│
├── docker-compose.yml
└── README.md
```

---

## Design Principles

### Human-in-the-Loop

InboxIQ does not automatically send emails. AI-generated replies remain drafts until the user explicitly chooses to send them.

### Provider Abstraction

The AI layer uses an `LLMProvider` abstraction, allowing the application to switch between supported LLM providers without changing the core AI services.

### Concurrent Processing

Email synchronization and AI analysis are designed to process multiple messages concurrently while maintaining safe database access through isolated asynchronous sessions.

### Security

Gmail access uses OAuth 2.0 authentication and protected backend routes. Sensitive credentials are stored through environment variables and are excluded from version control.

---

## Future Improvements

* AI Daily Briefing
* Advanced Security Center
* Personalized writing-style learning
* Contact and relationship intelligence
* "Ask My Inbox" semantic search
* pgvector-powered RAG
* Automated follow-up detection
* Improved email composition and rewriting
* Comprehensive unit and integration testing

---

## License

This project is a personal software engineering project developed for educational and portfolio purposes.
