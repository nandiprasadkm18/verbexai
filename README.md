# 🎙️ Verbex: AI-Powered Meeting Intelligence

Verbex is a state-of-the-art meeting intelligence platform designed to transform raw conversations into structured, actionable data. It leverages high-performance AI models to capture, transcribe, and analyze meetings in real-time, integrating seamlessly with your existing engineering workflows.

![Verbex Banner](https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&q=80&w=2070)

---

## 🚀 Key Features

### 1. **Hybrid Transcription Engine**
- **Live Feedback**: Instant feedback using the Web Speech API.
- **Precision Refinement**: Ultra-fast, high-fidelity transcription powered by **Groq Whisper Large V3**.
- **Screen Audio Mixing**: Seamlessly mix your microphone and system audio (tabs/windows) to capture full presentation context.

### 2. **AI Intelligence Extraction**
- **Automated Registry**: Extract tasks and decisions automatically using **Groq LLaMA 3.3 (gpt-oss-120b)**.
- **Smart TL;DR**: Generates immediate strategic summaries for every meeting.
- **Confidence Scoring**: Every extraction is measured for precision and contextual relevance.

### 3. **Enterprise Integration**
- **GitHub & Jira Sync**: Push extracted tasks directly to your issue trackers.
- **Bi-directional Mapping**: Automatically maps AI-extracted owners to real team members' GitHub/Jira accounts.
- **Bi-directional Status Sync**: Keep your project boards up-to-date with one click.

### 4. **Management Oversight**
- **Manager Dashboard**: Real-time meeting stats, health score trends, and system performance metrics.
- **Speaker Map**: Track team ownership, load, and notable contributions.
- **Stale Task Detection**: Automatically identify blockers that have been unresolved across multiple sessions.

---

## 🛠️ Tech Stack

- **Frontend**: React (Vite), TypeScript, Lucide Icons, Vanilla CSS (Premium Finish).
- **Backend**: FastAPI (Python), Prisma ORM, PostgreSQL.
- **AI Services**: Groq (LLaMA 3.3 & Whisper), OpenAI (Fallback).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 🚦 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Groq API Key](https://console.groq.com/keys)
- [Node.js](https://nodejs.org/) (Optional, for local development)
- [Python 3.10+](https://www.python.org/) (Optional, for local development)

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sumans-19/Verbex-AI.git
   cd Verbex-AI
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL="postgresql://user:password@db:5432/verbex"
   GROQ_API_KEY="your_groq_api_key"
   GITHUB_TOKEN="your_personal_access_token"
   JIRA_API_TOKEN="your_jira_api_token"
   JIRA_EMAIL="your_email@example.com"
   JIRA_SERVER="https://your-domain.atlassian.net"
   ```

3. **Launch the platform:**
   ```bash
   docker-compose up --build
   ```

4. **Access Verbex:**
   - **Frontend**: [http://localhost:5173](http://localhost:5173)
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📖 Platform Guide

- **New Meeting**: Navigate here to start a live session or upload an existing recording. You can also paste transcript texts for retrospective intelligence extraction.
- **Task Board**: View all engineering tasks extracted from meetings with real-time status sync to GitHub and Jira.
- **Speaker Map**: Review the "Ownership Map" to see which team members are leading specific projects and who needs support.
- **Stale Tasks**: Check here for critical blockers that are overdue and require management intervention.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Built with ❤️ by the Verbex Team.
