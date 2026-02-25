# Open ATS Check

> **AI-Powered Resume ATS Scanner** — Analyze your resume against Applicant Tracking System standards and compare it with job descriptions for maximum compatibility.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 📊 ATS Score Check
Upload your resume and get a **detailed ATS compatibility score** broken down into 6 modules:

| Module | What it checks |
|--------|---------------|
| **Keyword Matching** | Hard & soft skills against industry databases |
| **Formatting & Parseability** | Standard headings, length, layout structure |
| **Contact Information** | Email, phone, LinkedIn, name, location |
| **Work Experience** | Date ranges, years of experience, achievements |
| **Education & Certifications** | Degree levels, certifications, institutions |
| **Semantic Analysis** | Action verbs, quantified achievements, buzzwords |

### 🔍 Job Match Compare
Upload your resume **and** a job description to get:
- **Match Score** — How well your CV fits the role
- **Strengths** — What matches between your CV and the JD
- **Gaps** — Missing skills and keywords
- **Recommendations** — Actionable steps to improve your match

### 📥 Export Reports
Download your analysis as a **formatted text report** to share with others, complete with section breakdowns, scores, and recommendations.

### 📄 Multi-Format Support
Supports **PDF**, **DOCX**, **TXT**, **RTF**, and **HTML** resume files (up to 10 MB).

---

## 🖥️ Screenshots

The app features a modern dark theme with glassmorphism, animated score circles, and responsive design.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** installed on your system
- **pip** (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/daoudz/open-ats-check.git
cd open-ats-check
```

### 2. Create a Virtual Environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The app will start at **http://localhost:5000**. Open it in your browser.

---

## 📁 Project Structure

```
open-ats-check/
├── app.py              # Flask application & API endpoints
├── parsers.py          # Multi-format file → text extraction
├── ats_checker.py      # 6-module ATS scoring engine
├── job_matcher.py      # CV vs. job description comparison
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
└── static/
    ├── index.html      # Single-page frontend
    ├── styles.css      # Dark theme + glassmorphism styles
    └── app.js          # Frontend logic, rendering, export
```

---

## 🔌 API Reference

### `POST /api/analyze`

Analyze a resume for ATS compatibility.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `resume` | File | Resume file (PDF, DOCX, TXT, RTF, HTML) |

**Response:** `application/json`
```json
{
  "overall_score": 85.0,
  "sections": [
    {
      "name": "Keyword Matching",
      "score": 70,
      "icon": "🔑",
      "findings": ["Found 12 hard skills", "Found 5 soft skills"],
      "recommendations": ["Add more industry keywords"]
    }
  ],
  "file_info": { "filename": "resume.pdf", "format": "pdf", "word_count": 450 },
  "text_preview": "First 300 characters of extracted text..."
}
```

### `POST /api/compare`

Compare a resume against a job description.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `resume` | File | Resume file |
| `job_description` | Text | Job description text |
| `job_description_file` | File | *(optional)* Job description as a file |

**Response:** `application/json`
```json
{
  "comparison": {
    "match_score": 78.0,
    "pros": ["Matches 10 required skills"],
    "cons": ["Missing 2 required skills"],
    "recommendations": [{ "text": "Add skill X", "priority": "high", "action": "add" }],
    "keyword_analysis": {
      "matched_skills": ["python", "react"],
      "missing_skills": ["golang"],
      "extra_skills": ["java"]
    }
  },
  "ats_analysis": { "overall_score": 85.0, "sections": [...] },
  "file_info": { "filename": "resume.pdf", "format": "pdf", "word_count": 450 }
}
```

---

## 🌐 Deployment

### Option 1: Render (Recommended — Free Tier)

1. Push your code to GitHub (already done)
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo `daoudz/open-ats-check`
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
5. Click **Deploy**

### Option 2: Railway

1. Go to [railway.app](https://railway.app) → **New Project**
2. Choose **Deploy from GitHub** → Select `open-ats-check`
3. Railway auto-detects Python and deploys
4. Add environment variable: `PORT=5000` (if not auto-set)

### Option 3: Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a `Procfile` in the project root:
   ```
   web: gunicorn app:app
   ```
3. Deploy:
   ```bash
   heroku login
   heroku create open-ats-check
   git push heroku main
   ```

### Option 4: Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t open-ats-check .
docker run -p 5000:5000 open-ats-check
```

### Option 5: VPS / Self-Hosted (Ubuntu)

```bash
# Clone and setup
git clone https://github.com/daoudz/open-ats-check.git
cd open-ats-check
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Optional: use systemd for auto-restart
# Create /etc/systemd/system/ats-check.service
```

**Nginx reverse proxy** (optional, for custom domain):

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 10M;
    }
}
```

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PORT` | `5000` | Port to run the server on |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3, Flask |
| File Parsing | PyPDF2, python-docx, striprtf, BeautifulSoup4 |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Production Server | Gunicorn |
| Design | Dark theme, glassmorphism, CSS animations |

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<p align="center">
  <strong>◆ Open ATS Check</strong><br>
  <sub>Built with ❤️ for job seekers everywhere</sub>
</p>
