# 🎙️ Verbex: AI-Powered Meeting Intelligence

Verbex is a state-of-the-art meeting intelligence platform designed to transform raw conversations into structured, actionable data. It leverages high-performance AI models to capture, transcribe, and analyze meetings in real-time, integrating seamlessly with your existing engineering workflows.

![Verbex Banner](https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&q=80&w=2070)

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Frontend: React/Vite] -->|REST API / Chunk Uploads| B[Backend: FastAPI]
    B -->|Prisma ORM| C[(Local PostgreSQL)]
    B -->|Audio Transcription| D[Groq Whisper V3]
    B -->|Intelligence Extraction| E[Groq LLaMA 3.3]
    B -->|Issue Tracking| F[GitHub API]
    B -->|Project Management| G[Jira API]
    D -.->|Transcribed Text| E
    E -.->|Tasks & Decisions| B
```

---

## 🚀 Key Features

### 1. **Hybrid Transcription Engine**
- **Live Feedback**: Instant feedback using the Web Speech API during live sessions.
- **Precision Refinement**: Ultra-fast, high-fidelity transcription powered by **Groq Whisper Large V3**.
- **Screen Audio Mixing**: Capture full presentation context by mixing microphone and system audio.

### 2. **AI Intelligence Extraction**
- **Automated Registry**: Extract tasks and decisions automatically using **Groq LLaMA 3.3**.
- **Meeting Health Scoring**: Real-time analysis of meeting productivity and actionability.
- **Smart TL;DR**: Immediate strategic summaries for every meeting.
- **Confidence Scoring**: Precision measurement for every extracted item.

### 3. **Enterprise Integration**
- **GitHub & Jira Sync**: Push extracted tasks directly to your issue trackers with a single click.
- **Employee Management**: Map AI-extracted owners to real team members with individualized credentials.
- **Bi-directional Status Sync**: Keep your project boards up-to-date with real-time status updates.

### 4. **Management Oversight**
- **Manager Dashboard**: Real-time meeting stats, health score trends, and system performance metrics.
- **Speaker Map**: Visualize team ownership, contribution load, and notable quotes.
- **Stale Task Detection**: Identify critical blockers that remain unresolved across sessions.

---

## 🛠️ Tech Stack

- **Frontend**: [React 18+](https://reactjs.org/), [Vite](https://vitejs.dev/), [TypeScript](https://www.typescriptlang.org/), [Lucide Icons](https://lucide.dev/), [Vanilla CSS](https://developer.mozilla.org/en-US/docs/Web/CSS).
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+), [Prisma ORM](https://www.prisma.io/), [PostgreSQL](https://www.postgresql.org/).
- **AI Services**: [Groq](https://groq.com/) (LLaMA 3.3 & Whisper V3), [OpenAI](https://openai.com/) (Fallback).
- **Infrastructure**: Local Development Server.

---

## 🚦 Getting Started

### Prerequisites

- [Groq API Key](https://console.groq.com/keys)
- [Node.js](https://nodejs.org/)
- [Python 3.10+](https://www.python.org/)
- [PostgreSQL](https://www.postgresql.org/)

### Local Setup

1. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory (see [Environment Variables](#environment-variables) for details).

2. **Run Backend (FastAPI):**
   ```bash
   cd backend
   python -m venv venv
   # Activate virtual env:
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   prisma db push
   python seed_db.py            # Seed initial employees
   uvicorn main:app --reload
   ```

3. **Run Frontend (React/Vite):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access Verbex:**
   - **Frontend**: [http://localhost:5173](http://localhost:5173)
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔐 Environment Variables

The backend requires several environment variables to function correctly. Create a `.env` file in the `backend/` directory:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g., `postgresql://postgres:nandi@localhost:5432/verbexai`) |
| `GROQ_API_KEY` | Your Groq Cloud API Key |
| `GITHUB_TOKEN` | Default GitHub Personal Access Token |
| `GITHUB_REPO_OWNER` | Default GitHub repository owner |
| `GITHUB_REPO_NAME` | Default GitHub repository name |
| `JIRA_EMAIL` | Default Jira account email |
| `JIRA_API_TOKEN` | Default Jira API Token |
| `JIRA_DOMAIN` | Default Jira domain (e.g., `company.atlassian.net`) |
| `JIRA_PROJECT_KEY` | Default Jira project key |

### Multi-Account Support (Optional)
Verbex supports mapping tasks to specific team members. You can provide additional credentials for members (e.g., `GITHUB_TOKEN1`, `JIRA_EMAIL1`, etc.) in the `.env` file to enable per-user integration.

---

## 🔧 Database Utilities

From the `backend/` directory, you can run the following helper scripts to manage your database state:
- **Seed Employees**: `python seed_db.py` (Populates default employee directory list in database)
- **Purge All Data**: `python clear_data.py` (Truncates all database tables and clears storage audio files)

---

## 📖 Platform Guide

- **New Meeting**: Start a live session with real-time transcription or upload audio/text files for processing.
- **Task Board**: Integrated Kanban view of all extracted tasks. Sync status directly to GitHub/Jira.
- **Decision Log**: Centralized repository of all critical decisions made during meetings.
- **Employee Manager**: Configure team members and their individual integration credentials.
- **Speaker Map**: Interactive visualization of meeting participation and ownership.
- **Manager View**: High-level platform metrics and performance trends.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Built with ❤️ by the Verbex Team.
