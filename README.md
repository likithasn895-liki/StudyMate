# StudyMate
AI powered smart study generator
# StudyMate AI 📚

> **An AI-powered study assistant for engineering students**  
> Upload your notes, generate summaries and practice questions, take interactive quizzes, build personalised study plans, and track your learning progress — all powered by IBM watsonx AI.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [System Architecture](#5-system-architecture)
6. [Prerequisites](#6-prerequisites)
7. [Installation](#7-installation)
8. [IBM watsonx Configuration](#8-ibm-watsonx-configuration)
9. [Running the Application](#9-running-the-application)
10. [Using StudyMate AI](#10-using-studymate-ai)
11. [API Reference](#11-api-reference)
12. [Running the Tests](#12-running-the-tests)
13. [Troubleshooting](#13-troubleshooting)
14. [Project Files Reference](#14-project-files-reference)

---

## 1. Project Overview

**StudyMate AI** is a web application that converts raw study material — uploaded as a PDF or pasted as text — into structured summaries, practice questions, and interactive quizzes. It connects to **IBM watsonx AI** (Granite 13B) to generate all content, and stores your quiz results and study sessions in a local SQLite database for progress tracking.

The project was built as a solution to **Problem Statement 13 – Smart Study Generator Agent** using:
- Python + Flask (backend)
- HTML, CSS, JavaScript (frontend)
- IBM watsonx AI via the official `ibm-watsonx-ai` SDK
- SQLite for persistence

---

## 2. Features

### 📁 PDF & Notes Upload
- Upload PDF study materials (up to 10 MB)
- Drag-and-drop or file picker
- Extracts readable text page-by-page using `pdfplumber`
- Word-count badge shows how much material was loaded
- Accepts pasted plain text as an alternative
- Clear error messages for scanned, corrupted, or non-PDF files

### 📝 AI Summary Generator
- Generates structured summaries with headings and bullet points
- Highlights key concepts, definitions, and important formulas
- Powered by IBM Granite 13B via watsonx
- Copy-to-clipboard with one click

### ❓ Question Generator
- **Short-answer** questions (5 questions with concise answers)
- **Long-answer** questions (3 questions for exam preparation)
- **MCQ** questions (5 questions with A/B/C/D options, correct answer, explanation)
- **All types** combined in one output
- All questions grounded in the uploaded material

### 🎯 Interactive Quiz
- AI-generated multiple-choice quiz (3–10 questions)
- Progress bar fills as you select answers
- Automatic scoring after submission
- Score colour: green ≥75%, orange ≥50%, red <50%
- Per-question review showing correct answer and explanation
- Retake option after completion

### 📅 Personalized Study Plan
- Input your topics, available hours/day, and number of days
- Per-topic priority settings (High / Medium / Low)
- AI-generated day-by-day schedule with activities
- Rule-based fallback plan when AI is in demo mode
- Activities progress from reading → practice → revision
- Plan overview summary with hour allocation per topic

### 📊 Student Dashboard
- **Stat cards**: Quizzes taken, average score, sessions, study streak
- **Weekly bar chart**: Quiz activity over the last 7 days (pure CSS)
- **Score trend sparkline**: Last 10 quiz scores colour-coded
- **Best & Worst quiz**: Highlights your highest and lowest attempts
- **Per-topic performance**: Table with attempts, avg/best/worst, progress bar
- **Activity breakdown**: Chip counters for each feature used
- **Recent quizzes**: Last 8 attempts with colour-coded badges
- **Recent sessions**: Last 8 sessions with activity emoji icons
- One-click refresh

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.12 + Flask 3 | Web server, API routes |
| AI | IBM watsonx AI (Granite 13B) | Summary, questions, study plans |
| PDF | pdfplumber | Text extraction from PDFs |
| Database | SQLite (built-in) | Quiz results, session logs |
| Frontend | HTML5 + CSS3 + Vanilla JS | Browser UI, no frameworks |
| Environment | python-dotenv | Secure credential management |
| Testing | Custom test suite (run_tests.py) | Unit + integration tests |

---

## 4. Project Structure

```
StudyMate-AI/
│
├── app.py                     # Flask server — all API routes
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .env                       # IBM credentials (never commit this)
├── .gitignore                 # Excludes .env, venv, __pycache__
│
├── backend/
│   ├── __init__.py
│   ├── pdf_reader.py          # PDF upload and text extraction
│   ├── study_generator.py     # IBM watsonx AI integration
│   ├── quiz_manager.py        # MCQ parsing and scoring
│   └── study_planner.py       # Study plan generation
│
├── database/
│   ├── __init__.py
│   └── database.py            # SQLite setup and all queries
│
├── frontend/
│   ├── index.html             # Single-page UI (6 tabs)
│   ├── style.css              # All styling (~850 lines)
│   └── script.js              # All interactivity (~860 lines)
│
├── sample_notes/
│   └── sample_notes.pdf       # Engineering thermodynamics notes
│
├── run_tests.py               # Master test runner (5 suites)
├── test_pdf.py                # PDF extraction tests
├── test_ai.py                 # IBM watsonx connection test
├── test_integration.py        # Full API integration tests
└── create_sample_pdf.py       # Generates the sample PDF
```

---

## 5. System Architecture

```
Browser (HTML/CSS/JS)
        │
        │  HTTP requests (fetch API)
        ▼
Flask Web Server (app.py :5000)
        │
        ├── /api/upload ──────► pdf_reader.py ──► pdfplumber
        ├── /api/paste  ──────► pdf_reader.py
        ├── /api/summarize ───► study_generator.py ──► IBM watsonx
        ├── /api/questions ───► study_generator.py ──► IBM watsonx
        ├── /api/quiz/generate► study_generator.py ──► IBM watsonx
        │                       quiz_manager.py (parse)
        ├── /api/quiz/submit ─► quiz_manager.py (grade)
        │                       database.py (save)
        ├── /api/study-plan ──► study_generator.py ──► IBM watsonx
        │                       study_planner.py (fallback)
        └── /api/dashboard ───► database.py (8 queries)
                    │
                    ▼
              studymate.db (SQLite)
              ├── quiz_results
              └── study_sessions
```

---

## 6. Prerequisites

| Requirement | Version | Check Command |
|---|---|---|
| Python | 3.10 or higher | `python --version` |
| pip | Any recent version | `pip --version` |
| IBM Cloud account | Free (Lite tier) | https://cloud.ibm.com |
| Modern browser | Chrome / Edge / Firefox | — |

> **Windows note:** All commands in this README are for PowerShell on Windows.

---

## 7. Installation

### 7.1 Clone or download the project

If you have Git:
```powershell
git clone <repository-url>
cd StudyMate-AI
```

Or extract the ZIP file and open a terminal inside the `StudyMate-AI` folder.

### 7.2 Create a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

Your terminal prompt should now show `(venv)`.

> If you get a permissions error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 7.3 Install dependencies

```powershell
pip install -r requirements.txt
```

### 7.4 Generate the sample PDF (first time only)

```powershell
python create_sample_pdf.py
```

This creates `sample_notes/sample_notes.pdf` — a 3-page thermodynamics study guide for testing.

### 7.5 Create your `.env` file

Create a file named `.env` in the project root (same folder as `app.py`) with this content:

```
IBM_API_KEY=your_ibm_api_key_here
IBM_PROJECT_ID=your_ibm_project_id_here
IBM_REGION=us-south
IBM_MODEL_ID=ibm/granite-13b-instruct-v2
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=studymate-dev-secret-change-in-production
MAX_INPUT_WORDS=3000
```

See [Section 8](#8-ibm-watsonx-configuration) for how to get your IBM credentials.

> ⚠️ **Never commit `.env` to Git.** It is already listed in `.gitignore`.

---

## 8. IBM watsonx Configuration

### 8.1 Create a free IBM Cloud account

1. Go to https://cloud.ibm.com/registration
2. Sign up with your email (no credit card needed for the Lite tier)
3. Verify your email and log in

### 8.2 Get your API Key

1. Go to https://cloud.ibm.com/iam/apikeys
2. Click **"Create an IBM Cloud API key"**
3. Name it `studymate-ai-key`
4. Click **"Create"** then **"Copy"** immediately (shown only once)
5. Paste it as `IBM_API_KEY=` in your `.env` file

### 8.3 Create a watsonx.ai project

1. Go to https://dataplatform.cloud.ibm.com/wx/home
2. Click **"New project"** → **"Create an empty project"**
3. Name it `StudyMate-AI` and click **"Create"**
4. Go to **Manage** → **General** → copy the **Project ID**
5. Paste it as `IBM_PROJECT_ID=` in your `.env` file

### 8.4 Associate Watson Machine Learning

1. Inside your project, go to **Manage** → **Services & integrations**
2. Click **"Associate service"**
3. Select **Watson Machine Learning** (Lite/free plan)
4. Click **"Associate"**

### 8.5 Verify the connection

```powershell
python test_ai.py
```

Expected output when credentials are correct:
```
  API Key    : ✅ SET
  Project ID : ✅ SET
  Mode       : 🤖 REAL IBM AI
  ...
  🎉 ALL TESTS PASSED — IBM watsonx is working!
```

### 8.6 Available models

If the default model is unavailable, change `IBM_MODEL_ID` in `.env`:

| Model ID | Notes |
|---|---|
| `ibm/granite-13b-instruct-v2` | Default — best quality |
| `ibm/granite-3-8b-instruct` | Smaller, faster |
| `meta-llama/llama-3-2-3b-instruct` | Alternative |

---

## 9. Running the Application

### Start the server

Make sure your virtual environment is active (`(venv)` in the terminal):

```powershell
python app.py
```

You will see:
```
[DB] Database initialised.
[AI] USE_REAL_AI = True  (model: ibm/granite-13b-instruct-v2)
=======================================================
  StudyMate AI – Backend Server
  Running at: http://127.0.0.1:5000
=======================================================
```

### Open the app

Open your browser and go to:
```
http://127.0.0.1:5000
```

### Stop the server

Press `Ctrl + C` in the terminal.

---

## 10. Using StudyMate AI

### Step 1 — Upload your study material

- Click the **📁 Upload** tab
- Either upload a PDF or paste your notes into the text area
- A green preview box confirms the material is loaded
- The blue badge shows the word count

### Step 2 — Generate a summary

- Click the **📝 Summary** tab
- Click **"⚡ Generate Summary"**
- A structured summary with headings, bullet points, and key formulas appears
- Use **"📋 Copy"** to copy it for your notes

### Step 3 — Generate practice questions

- Click the **❓ Questions** tab
- Choose: Short Answer / Long Answer / MCQ Only / All Types
- Click **"🧠 Generate Questions"**
- Questions with answers and explanations appear

### Step 4 — Take a quiz

- Click the **🎯 Quiz** tab
- Choose the number of questions (3–10)
- Enter a topic label (e.g. "Thermodynamics Chapter 2")
- Click **"🎯 Generate Quiz"**
- Answer each question using the radio buttons
- Click **"Submit Answers"** to see your score

### Step 5 — Create a study plan

- Click the **📅 Study Plan** tab
- Type your topics separated by commas
- Set your daily study hours and number of days
- Set priority levels for each topic
- Click **"📅 Generate Study Plan"**

### Step 6 — Track your progress

- Click the **📊 Dashboard** tab
- View your quiz statistics, weekly activity chart, and topic performance
- Click **"🔄 Refresh"** to reload with the latest data

---

## 11. API Reference

All API endpoints are served from `http://127.0.0.1:5000`.

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| `GET` | `/` | — | HTML page |
| `POST` | `/api/upload` | `multipart/form-data` with `file` | `{success, text, pages, word_count, message}` |
| `POST` | `/api/paste` | `{text}` | `{success, text, word_count, message}` |
| `POST` | `/api/summarize` | `{text?}` | `{success, summary, message}` |
| `POST` | `/api/questions` | `{text?, type}` | `{success, questions, message}` |
| `POST` | `/api/quiz/generate` | `{text?, num_questions}` | `{success, questions[], total, message}` |
| `POST` | `/api/quiz/submit` | `{answers{}, topic}` | `{success, score, total, percentage, feedback, results[]}` |
| `POST` | `/api/study-plan` | `{topics[], daily_hours, days, priorities?}` | `{success, type, plan/plan_text, summary?}` |
| `GET` | `/api/dashboard` | — | `{success, quiz_stats, session_stats, topic_performance, weekly_history, score_trend, best_and_worst, activity_breakdown, streak_days, recent_quizzes, recent_sessions}` |

### Question types

| Value | Description |
|---|---|
| `short` | 5 short-answer questions with concise answers |
| `long` | 3 long-answer questions for exam practice |
| `mcq` | 5 MCQs with A/B/C/D options, correct answer, explanation |
| `all` | All three types combined |

---

## 12. Running the Tests

### Run all tests (unit + integration)

The server must be running in a separate terminal for integration tests.

```powershell
# Terminal 1
python app.py

# Terminal 2
python run_tests.py --all
```

### Run only unit tests (no server needed)

```powershell
python run_tests.py --unit
```

### Run only integration tests

```powershell
python run_tests.py --integration
```

### Individual test scripts

```powershell
# PDF extraction tests
python test_pdf.py

# IBM watsonx connection test
python test_ai.py

# Full API integration test
python test_integration.py

# Database self-test
python database/database.py
```

### Expected result

```
========================================================
  FINAL REPORT
========================================================
  ✅  Database Layer
  ✅  PDF Reader
  ✅  Quiz Manager
  ✅  Study Generator
  ✅  Integration

  5/5 suites passed
  🎉 ALL SUITES PASSED!
```

---

## 13. Troubleshooting

### The app shows "Demo Mode" even after adding credentials

1. Make sure you saved the `.env` file (`Ctrl + S`)
2. Stop the server (`Ctrl + C`) and restart: `python app.py`
3. The startup line must say `USE_REAL_AI = True`

---

### `ImportError: No module named 'backend'`

The virtual environment is not active. Run:
```powershell
.\venv\Scripts\Activate
```

---

### `401 Unauthorized` from IBM watsonx

Your API key is incorrect or has expired.
1. Go to https://cloud.ibm.com/iam/apikeys
2. Create a new API key
3. Update `IBM_API_KEY` in `.env`

---

### `403 Forbidden` or project not found

Watson Machine Learning is not associated with your project.
1. Open your watsonx project
2. Go to **Manage → Services & integrations**
3. Click **"Associate service"** → select **Watson Machine Learning**

---

### Model not found / 404 error

The model is not available in your region.
Try changing `IBM_MODEL_ID` in `.env`:
```
IBM_MODEL_ID=ibm/granite-3-8b-instruct
```

---

### `pdfplumber` extracts no text

The PDF contains scanned images, not selectable text.
Use the **"Paste Text"** option in the Upload tab instead.

---

### Quiz shows "No active quiz found"

The server was restarted between generating and submitting the quiz.
Generate the quiz again — the server holds quiz questions in memory only for the current session.

---

### Port 5000 already in use

```powershell
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

---

### Database errors

Delete the database file and let it recreate:
```powershell
Remove-Item studymate.db
python app.py
```

---

## 14. Project Files Reference

| File | Lines | Purpose |
|---|---|---|
| `app.py` | ~395 | Flask server — 8 API routes, error handlers |
| `backend/pdf_reader.py` | ~290 | PDF extraction, text cleaning, paste validation |
| `backend/study_generator.py` | ~370 | IBM watsonx prompts, AI calls, demo stubs |
| `backend/quiz_manager.py` | ~225 | MCQ parsing, quiz grading, feedback |
| `backend/study_planner.py` | ~200 | Rule-based plan, AI prompt builder |
| `database/database.py` | ~265 | SQLite schema, 12 query functions |
| `frontend/index.html` | ~370 | Single-page app — 6 tabs |
| `frontend/style.css` | ~850 | Complete responsive design |
| `frontend/script.js` | ~860 | All interactivity, API calls, charts |
| `run_tests.py` | ~355 | Master test runner — 5 suites |
| `test_pdf.py` | ~140 | PDF extraction unit tests |
| `test_ai.py` | ~160 | IBM watsonx connection tests |
| `test_integration.py` | ~245 | Full API integration tests |
| `create_sample_pdf.py` | ~155 | Generates engineering study notes PDF |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `IBM_API_KEY` | Yes (for AI) | `your_ibm_api_key_here` | IBM Cloud API key |
| `IBM_PROJECT_ID` | Yes (for AI) | `your_ibm_project_id_here` | watsonx project ID |
| `IBM_REGION` | No | `us-south` | IBM Cloud region |
| `IBM_MODEL_ID` | No | `ibm/granite-13b-instruct-v2` | watsonx model |
| `FLASK_ENV` | No | `development` | Flask environment |
| `FLASK_DEBUG` | No | `True` | Flask debug mode |
| `SECRET_KEY` | No | `studymate-dev-secret...` | Flask secret key |
| `MAX_INPUT_WORDS` | No | `3000` | Max words sent to AI |

---

## Licence

This project was built for educational purposes as part of an IBM hackathon / problem statement submission.

---

*StudyMate AI · Powered by IBM watsonx · Built for Engineering Students*
