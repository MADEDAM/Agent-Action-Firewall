# 🛡️ Agent Action Firewall

AI Security Gateway that analyzes and controls AI agent actions before execution.

---

## 📌 Overview

Agent Action Firewall is a security platform designed to analyze AI agent actions before execution.

The system detects prompt injection attacks, masks sensitive information, controls tool permissions, calculates risk scores, and determines whether an action should be allowed, require administrator approval, or be blocked.

---

## ✨ Key Features

- Prompt Injection Detection
- Sensitive Data Masking
- Tool Permission Control
- Risk-based Decision Engine
- Administrator Approval Workflow
- Audit Logging
- Real-time Monitoring Dashboard

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python |
| AI | Ollama (Llama3) |
| Database | SQLite |
| Dashboard | Streamlit |
| Notification | Slack Webhook |

---

## 📂 Project Structure

```text
.
├── app/
├── dashboard/
├── frontend/
├── data/
├── tests/
├── requirements.txt
└── README.md
```

---

## 🚀 Installation

### Requirements

- Python 3.11+
- Node.js (LTS)
- Ollama

### 1. Create Python Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment (Windows)

```bash
.venv\Scripts\activate
```

### 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Install and Run Ollama

Download the required model.

```bash
ollama pull llama3
```

Start the Ollama server.

```bash
ollama serve
```

---

## ▶️ Run the Project

### Backend API Server

```bash
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Open Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

### Frontend

```bash
cd frontend
npm run dev
```

Open:

```
http://localhost:5173
```

---

### Dashboard

```bash
.venv\Scripts\activate
streamlit run dashboard/streamlit_app.py
```

Open:

```
http://localhost:8501
```

---

## 👥 Contributors

| Name | Role |
|------|------|
| BAEK EDAM | Security Engine, Dashboard |
| KIM NAHYUNG | AI Action Plan |
| JO JUNGWOO | Backend & Tool Execution |
