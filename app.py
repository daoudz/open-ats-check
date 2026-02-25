"""
app.py - Main Flask application for the ATS Resume Checker.
Serves the frontend and exposes API endpoints for resume analysis.
"""

import os
import time
from flask import Flask, request, jsonify, send_from_directory, make_response
from parsers import extract_text
from ats_checker import analyze_resume
from job_matcher import compare_cv_to_job

app = Flask(__name__, static_folder='static')

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'rtf', 'html', 'htm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze an uploaded resume for ATS compatibility.
    
    Expects: multipart/form-data with a 'resume' file field.
    Returns: JSON with overall score and per-section breakdowns.
    """
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded. Please upload a file.'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            'error': f'Unsupported file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Reset file stream to beginning to ensure we read the full content
        file.stream.seek(0)

        # Parse the file
        result = extract_text(file, filename=file.filename)
        text = result['text']

        print(f"[ANALYZE] File: {file.filename}, Extracted {len(text)} chars, {len(text.split())} words")
        print(f"[ANALYZE] Preview: {text[:200]}...")

        if not text or len(text.strip()) < 20:
            return jsonify({
                'error': 'Could not extract meaningful text from the file. '
                         'The file may be empty, image-based, or corrupted.'
            }), 400

        # Run ATS analysis
        analysis = analyze_resume(text, metadata=result.get('metadata', {}))
        analysis['file_info'] = {
            'filename': file.filename,
            'format': result['format'],
            'text_length': len(text),
            'word_count': len(text.split()),
        }
        # Include text preview so user can verify correct file was parsed
        analysis['text_preview'] = text[:300] + ('...' if len(text) > 300 else '')
        analysis['timestamp'] = time.time()

        resp = make_response(jsonify(analysis))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred while analyzing the file: {str(e)}'}), 500


@app.route('/api/compare', methods=['POST'])
def compare():
    """
    Compare a resume against a job description.
    
    Expects: multipart/form-data with:
        - 'resume': the CV file
        - 'job_description': either a file or text field
    Returns: JSON with match score, pros, cons, and recommendations.
    """
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded.'}), 400

    file = request.files['resume']
    if file.filename == '' or not _allowed_file(file.filename):
        return jsonify({'error': 'Invalid or unsupported resume file.'}), 400

    # Get job description (either as file or text)
    job_text = None
    if 'job_description_file' in request.files:
        jd_file = request.files['job_description_file']
        if jd_file.filename:
            try:
                jd_result = extract_text(jd_file, filename=jd_file.filename)
                job_text = jd_result['text']
            except Exception:
                pass

    if not job_text:
        job_text = request.form.get('job_description', '').strip()

    if not job_text or len(job_text) < 20:
        return jsonify({
            'error': 'Please provide a job description (at least 20 characters). '
                     'You can paste it as text or upload a file.'
        }), 400

    try:
        # Reset file stream to beginning
        file.stream.seek(0)

        # Parse resume
        result = extract_text(file, filename=file.filename)
        cv_text = result['text']

        print(f"[COMPARE] File: {file.filename}, Extracted {len(cv_text)} chars")

        if not cv_text or len(cv_text.strip()) < 20:
            return jsonify({
                'error': 'Could not extract meaningful text from the resume file.'
            }), 400

        # Run ATS analysis on the resume as well
        ats_analysis = analyze_resume(cv_text, metadata=result.get('metadata', {}))

        # Compare CV to job description
        comparison = compare_cv_to_job(cv_text, job_text)

        # Combine results
        response = {
            'ats_analysis': ats_analysis,
            'comparison': comparison,
            'file_info': {
                'filename': file.filename,
                'format': result['format'],
                'word_count': len(cv_text.split()),
            },
            'text_preview': cv_text[:300] + ('...' if len(cv_text) > 300 else ''),
            'timestamp': time.time(),
        }

        resp = make_response(jsonify(response))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
