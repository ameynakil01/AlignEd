# AlignED — AI-Driven Curated Career Pathways & Curriculum Gap Mapper with Interactive Proof-of-Work Verification

> **AlignED** is an intelligent career navigation and verification platform designed for college and diploma students. It parses semester syllabi or resumes (PDF/text), extracts and normalizes technical competencies using spaCy NER, maps curriculum gaps against live industry role benchmarks using local vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`), and prompts the Google Gemini API to synthesize structured, week-by-week learning trajectories with interactive Proof-of-Work (PoW) milestone verification.

---

## 🌟 Key Features

1. **Intelligent Document Ingestion & Skill Parsing**:
   - Ingests university syllabus PDFs or student resumes via `pypdf`.
   - spaCy (`en_core_web_sm`) entity ruler and canonical tech taxonomy normalizes skills across Languages, Frameworks, Cloud, Databases, and Dev Tools.

2. **Vector-Based Curriculum Gap Engine**:
   - CPU-based vector embeddings using `all-MiniLM-L6-v2` (`SentenceTransformer`).
   - Computes cosine similarity $S = \cos(v_{\text{benchmark}}, v_{\text{extracted}})$.
   - Skills with $S \ge 0.70$ are classified as **Covered**; $S < 0.70$ are classified as **Missing**.
   - Generates priority ratings (`High`, `Medium`, `Low`) based on role weight and core importance.

3. **Google Gemini Generative AI Trajectories**:
   - Integrates Google Gemini API (`google-genai` SDK using `gemini-2.5-flash` or `gemini-1.5-flash`) via `GEMINI_API_KEY`.
   - Generates personalized, week-by-week structured JSON trajectories with automated fallback to expert-calibrated curricula.

4. **Interactive Proof-of-Work (PoW) Verification Gates**:
   - **In-App Curated Embeds**: Video masterclasses (with watch threshold telemetry tracking $\ge 75\%$) and document reader scroll depth analysis.
   - **Scenario Micro-Quizzes**: Dynamically generated, timed 3-question conceptual scenario tests (60-second limit per question) with instant grade evaluation (pass threshold $\ge 2/3$).
   - **Live In-Browser Code Sandbox**: Embedded code editor with live DOM iframe rendering, console logging, and unit test criteria validation.
   - **Cryptographic Milestone Claims**: Verified milestones unlock the subsequent week's pathway with visual progress celebration.

---

## 🏗️ Architecture & Tech Stack

```
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI endpoints, CORS, routers
│   │   ├── config.py            # Pydantic BaseSettings & env configs
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic schemas (Roadmap, Quiz, Sandbox, Gap)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── parser_service.py      # PDF text extraction via pypdf
│   │   │   ├── skill_extractor.py     # spaCy NER + tech taxonomy
│   │   │   ├── gap_engine.py          # all-MiniLM-L6-v2 vector embeddings
│   │   │   ├── roadmap_generator.py   # Google Gemini API roadmap generator
│   │   │   ├── quiz_generator.py      # Dynamic scenario MCQs & answer evaluation
│   │   │   └── sandbox_evaluator.py   # DOM & regex code verification
│   │   └── data/
│   │       └── role_benchmarks.json   # Pre-seeded industry job benchmarks
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       ├── __init__.py
│       ├── test_gap_engine.py
│       └── test_assessment.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadModal.jsx        # PDF drag & drop + text preset picker
│   │   │   ├── GapDashboard.jsx       # Match gauge, acquired & missing chips
│   │   │   ├── RoadmapTimeline.jsx    # Weekly milestone stepper graph
│   │   │   ├── EmbeddedViewer.jsx     # Video/doc telemetry tracker
│   │   │   ├── MicroQuiz.jsx          # Timed scenario assessment
│   │   │   └── CodeSandbox.jsx        # Live code editor & DOM validation
│   │   ├── services/
│   │   │   └── api.js                 # REST client for FastAPI endpoints
│   │   ├── App.jsx                    # Master application interface
│   │   ├── index.css                  # Tailwind CSS & modern dialog styling
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 20+** and **npm**

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
pytest -v tests/

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Diagnostic health check and embedding model status |
| `GET` | `/api/v1/roles` | Retrieve list of pre-seeded role benchmarks |
| `GET` | `/api/v1/roles/{role_id}` | Retrieve specific role benchmark profile |
| `POST` | `/api/v1/parse-document` | Upload PDF or send raw text to extract skills with spaCy |
| `POST` | `/api/v1/analyze-gap` | Compute vector embedding cosine similarity & gap metrics |
| `POST` | `/api/v1/generate-roadmap` | Generate structured weekly milestones via Gemini |
| `POST` | `/api/v1/generate-quiz` | Generate 3 scenario-based MCQs for a given skill |
| `POST` | `/api/v1/submit-quiz` | Evaluate quiz submission against session answer key |
| `POST` | `/api/v1/evaluate-sandbox` | Verify hands-on code against syntax and DOM unit criteria |
| `POST` | `/api/v1/verify-milestone` | Confirm all 3 PoW gates to unlock subsequent milestones |

---

## 🛡️ Modern Web Guidance Adherence
- **Native `<dialog>` Architecture**: Upload and Milestone Workspace overlays utilize native `<dialog>` elements triggered via `showModal()`.
- **Light Dismiss with Coordinate Fallback**: Supports declarative `closedby="any"` alongside click boundary detection on `::backdrop` to ensure smooth dismissal across all modern desktop and mobile browsers.
- **Scroll Containment**: Utilizes `overscroll-behavior: contain` and `overflow: hidden` on backdrop containers to prevent background document scrolling without causing scrollbar layout shifts.
