# Open ATS Check

A modern web application that analyzes your CV/resume against **Applicant Tracking System (ATS)** standards and provides a detailed score report.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Multi-format Upload** — Supports PDF, DOCX, TXT, RTF, and HTML resumes
- **6-Point ATS Analysis**
  - Keyword Matching (hard skills, soft skills, job titles)
  - Formatting & Parseability
  - Contact Information Extraction
  - Work Experience & Longevity
  - Education & Certifications
  - Semantic / Contextual Analysis
- **Job Description Comparison** — Upload a job listing to get pros, cons, and actionable recommendations
- **Detailed Score Report** — Per-section scores with an overall ATS compatibility rating
- **Modern UI** — Dark-themed, responsive dashboard with animated score indicators

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/open-ats-check.git
cd open-ats-check
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### 3. Deploy

The app runs with **Gunicorn** in production:

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

Compatible with Render, Railway, Heroku, or any VPS.

## Project Structure

```
open-ats-check/
├── app.py              # Flask application & API routes
├── parsers.py          # File-to-text extraction (PDF, DOCX, TXT, RTF, HTML)
├── ats_checker.py      # ATS scoring engine (6 modules)
├── job_matcher.py      # Job description comparison
├── requirements.txt    # Python dependencies
├── static/
│   ├── index.html      # Frontend SPA
│   ├── styles.css      # Styling
│   └── app.js          # Frontend logic
└── README.md
```

## API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Serve the web interface |
| `/api/analyze` | POST | Upload CV → ATS score report (JSON) |
| `/api/compare` | POST | Upload CV + Job Description → comparison report (JSON) |

## License

MIT
