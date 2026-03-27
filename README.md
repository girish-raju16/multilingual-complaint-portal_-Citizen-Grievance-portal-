# 🏛️ Multilingual Government Complaint Portal

A full-stack AI-powered portal where citizens can submit complaints in their **native language** via voice, text, or file upload. The system automatically transcribes, translates, classifies, routes, and generates PDF reports.

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Speech-to-Text | **OpenAI Whisper** | Transcribe voice in 99 languages |
| Translation + Summarization | **Ollama (Llama3)** | Translate to English + generate summaries |
| Classification | **TensorFlow + USE** | Classify complaint category & priority |
| API Backend | **FastAPI** | REST API + pipeline orchestration |
| Frontend | **Streamlit** | Citizen portal + Admin dashboard |
| Database | **SQLite + SQLAlchemy** | Store complaints |
| Reports | **ReportLab** | Auto-generate PDF reports |

---

## Project Structure

```
multilingual-complaint-portal/
├── backend/
│   ├── main.py                    # FastAPI app + all routes
│   ├── database.py                # SQLAlchemy models
│   ├── services/
│   │   ├── whisper_service.py     # Whisper STT
│   │   ├── ollama_service.py      # Translation + summarization
│   │   └── classifier_service.py # TensorFlow classifier
│   └── utils/
│       └── report_generator.py   # ReportLab PDF generator
├── frontend/
│   └── app.py                    # Streamlit portal
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- ffmpeg (for Whisper audio processing)

```bash
# Install ffmpeg (Ubuntu/Debian)
sudo apt install ffmpeg

# Install ffmpeg (macOS)
brew install ffmpeg

# Pull Ollama model
ollama pull llama3
```

### 2. Install Dependencies

```bash
cd multilingual-complaint-portal
pip install -r requirements.txt
```

### 3. Run the Backend (FastAPI)

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be live at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### 4. Run the Frontend (Streamlit)

Open a new terminal:

```bash
streamlit run frontend/app.py
```

Portal will open at: http://localhost:8501

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |
| POST | `/submit/voice` | Submit voice complaint (audio file) |
| POST | `/submit/text` | Submit text complaint |
| POST | `/submit/file` | Submit document complaint |
| GET | `/complaints` | List all complaints (filterable) |
| GET | `/complaints/{id}` | Get single complaint |
| PATCH | `/complaints/{id}/status` | Update complaint status |
| GET | `/complaints/{id}/report` | Download PDF report |
| GET | `/stats` | Dashboard statistics |

---

## Supported Languages

Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Urdu, Arabic, French, Spanish, and 90+ more via Whisper.

---

## Complaint Categories

| Category | Department |
|----------|------------|
| Infrastructure | Public Works Department |
| Healthcare | Department of Health |
| Education | Department of Education |
| Safety & Security | Police / Home Department |
| Environment | Environment Department |
| Water & Sanitation | Water Board |
| Electricity | Electricity Board |
| Transportation | Transport Department |
| Administrative | General Administration |

---

## Improving the Classifier

The TensorFlow model trains automatically on first run using seed data.
To improve accuracy, add more labeled examples in `classifier_service.py → SEED_DATA` and delete the `./models/` folder to retrain.

For production, fine-tune on real complaint datasets from your specific region.

---

## Environment Variables (optional)

Create a `.env` file:

```
OLLAMA_MODEL=llama3          # or mistral, gemma2
WHISPER_MODEL_SIZE=base      # tiny|base|small|medium|large
DATABASE_URL=sqlite:///./complaints.db
```
