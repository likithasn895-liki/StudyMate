app.py
------
Main entry point for StudyMate AI.
Starts the Flask web server and defines all API routes.

Routes:
  GET  /                    → Serve the frontend
  POST /api/upload          → Upload a PDF and extract text
  POST /api/paste           → Accept pasted text
  POST /api/summarize       → Generate an AI summary
  POST /api/questions       → Generate practice questions
  POST /api/quiz/generate   → Generate an MCQ quiz
  POST /api/quiz/submit     → Submit quiz answers and get a score
  POST /api/study-plan      → Generate a personalized study plan
  GET  /api/dashboard       → Get dashboard statistics
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    static_folder='frontend',   # serve frontend files from /frontend
    static_url_path=''
)
CORS(app)   # allow the browser frontend to call these API endpoints

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB limit
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# ---------------------------------------------------------------------------
# Import backend modules
# ---------------------------------------------------------------------------

from backend.pdf_reader import (
    extract_text_from_pdf,
    validate_pasted_text,
    clean_text,
    save_uploaded_file
)
from backend.study_generator import (
    generate_summary,
    generate_questions,
    generate_mcq_for_quiz,
    generate_study_plan
)
from backend.quiz_manager import (
    parse_mcq_questions,
    save_and_grade_quiz,
    get_performance_feedback
)
from backend.study_planner import validate_plan_inputs
from database.database import (
    init_db,
    get_recent_quiz_results,
    get_quiz_stats,
    save_study_session,
    get_recent_sessions,
    get_session_stats,
    get_topic_performance,
    get_weekly_quiz_history,
    get_score_trend,
    get_best_and_worst,
    get_activity_breakdown,
    get_streak_days,
)

# Initialise the database when the server starts
init_db()

# ---------------------------------------------------------------------------
# In-memory session store (holds extracted text for the current session)
# For a production app this would use Flask sessions or a cache.
# ---------------------------------------------------------------------------
_current_text_store = {'text': '', 'source': ''}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Frontend Route
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('frontend', 'index.html')


# ---------------------------------------------------------------------------
# Route 1: Upload PDF
# ---------------------------------------------------------------------------

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """
    Receive a PDF file, save it temporarily, extract text, and return it.
    Expects: multipart/form-data with field 'file'
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file was included in the request.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    if not _allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are supported.'}), 400

    filename = secure_filename(file.filename)
    saved_path = save_uploaded_file(file, filename)

    result = extract_text_from_pdf(saved_path)

    # Clean up the temporary file
    try:
        os.remove(saved_path)
    except OSError:
        pass

    if result['success']:
        _current_text_store['text'] = result['text']
        _current_text_store['source'] = filename
        save_study_session(filename, 'upload')

    return jsonify(result)


# ---------------------------------------------------------------------------
# Route 2: Accept Pasted Text
# ---------------------------------------------------------------------------

@app.route('/api/paste', methods=['POST'])
def paste_text():
    """
    Accept plain text pasted by the student.
    Expects JSON: { "text": "..." }
    """
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({'success': False, 'message': 'No text provided.'}), 400

    result = validate_pasted_text(data['text'])

    if result['success']:
        _current_text_store['text'] = result['text']
        _current_text_store['source'] = 'pasted_text'
        save_study_session('Pasted Notes', 'paste')

    return jsonify(result)


# ---------------------------------------------------------------------------
# Route 3: Generate Summary
# ---------------------------------------------------------------------------

@app.route('/api/summarize', methods=['POST'])
def summarize():
    """
    Generate an AI summary of the current study text.
    Expects JSON: { "text": "..." }  (optional — uses stored text if omitted)
    """
    data = request.get_json(silent=True) or {}
    text = data.get('text', '') or _current_text_store.get('text', '')

    if not text:
        return jsonify({'success': False, 'message': 'No study material found. Please upload a PDF or paste text first.'}), 400

    result = generate_summary(text)

    if result['success']:
        topic = _current_text_store.get('source', 'Unknown')
        save_study_session(topic, 'summary')

    return jsonify(result)


# ---------------------------------------------------------------------------
# Route 4: Generate Questions
# ---------------------------------------------------------------------------

@app.route('/api/questions', methods=['POST'])
def questions():
    """
    Generate practice questions from the study material.
    Expects JSON: { "text": "...", "type": "short|long|mcq|all" }
    """
    data = request.get_json(silent=True) or {}
    text = data.get('text', '') or _current_text_store.get('text', '')
    question_type = data.get('type', 'all')

    if not text:
        return jsonify({'success': False, 'message': 'No study material found. Please upload a PDF or paste text first.'}), 400

    result = generate_questions(text, question_type)

    if result['success']:
        topic = _current_text_store.get('source', 'Unknown')
        save_study_session(topic, 'questions')

    return jsonify(result)


# ---------------------------------------------------------------------------
# Route 5: Generate Quiz
# ---------------------------------------------------------------------------

@app.route('/api/quiz/generate', methods=['POST'])
def generate_quiz():
    """
    Generate an MCQ quiz from the study material.
    Expects JSON: { "text": "...", "num_questions": 5 }
    Returns parsed question objects ready for the quiz UI.
    """
    data = request.get_json(silent=True) or {}
    text = data.get('text', '') or _current_text_store.get('text', '')
    try:
        num_questions = max(3, min(int(data.get('num_questions', 5)), 10))
    except (ValueError, TypeError):
        num_questions = 5

    if not text:
        return jsonify({'success': False, 'message': 'No study material found. Please upload a PDF or paste text first.'}), 400

    raw_result = generate_mcq_for_quiz(text, num_questions)

    if not raw_result['success']:
        return jsonify(raw_result)

    parsed = parse_mcq_questions(raw_result['raw_text'])

    if not parsed:
        return jsonify({
            'success': False,
            'message': 'Could not parse questions from AI output. Please try again.',
            'raw_text': raw_result['raw_text']
        })

    # Return questions WITHOUT the answer so the student can't see it in browser dev tools
    safe_questions = [
        {
            'index': i,
            'question': q['question'],
            'options': q['options']
        }
        for i, q in enumerate(parsed)
    ]

    # Store the full questions (with answers) server-side for grading
    _current_text_store['quiz_questions'] = parsed

    return jsonify({
        'success': True,
        'questions': safe_questions,
        'total': len(safe_questions),
        'message': f'{len(safe_questions)} questions generated.'
    })


# ---------------------------------------------------------------------------
# Route 6: Submit Quiz
# ---------------------------------------------------------------------------

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """
    Receive student answers, grade the quiz, save the result.
    Expects JSON: { "answers": {"0": "A", "1": "C", ...}, "topic": "..." }
    """
    data = request.get_json(silent=True) or {}
    student_answers = data.get('answers', {})
    topic = data.get('topic', _current_text_store.get('source', 'General'))

    questions = _current_text_store.get('quiz_questions', [])
    if not questions:
        return jsonify({'success': False, 'message': 'No active quiz found. Please generate a quiz first.'}), 400

    grading = save_and_grade_quiz(topic, questions, student_answers)
    grading['feedback'] = get_performance_feedback(grading['percentage'])
    grading['success'] = True

    return jsonify(grading)


# ---------------------------------------------------------------------------
# Route 7: Generate Study Plan
# ---------------------------------------------------------------------------

@app.route('/api/study-plan', methods=['POST'])
def study_plan():
    """
    Generate a personalized study plan.
    Expects JSON: {
        "topics": ["Topic A", "Topic B"],
        "daily_hours": 2,
        "days": 7,
        "priorities": {"Topic A": "high", "Topic B": "low"}  (optional)
    }
    """
    data = request.get_json(silent=True) or {}
    topics      = data.get('topics', [])
    try:
        daily_hours = float(data.get('daily_hours', 2))
        days        = int(data.get('days', 7))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'daily_hours and days must be numbers.'}), 400
    priorities  = data.get('priorities', None)

    validation = validate_plan_inputs(topics, daily_hours, days)
    if not validation['valid']:
        return jsonify({'success': False, 'message': validation['message']}), 400

    result = generate_study_plan(topics, daily_hours, days, priorities)

    if result.get('success'):
        save_study_session(', '.join(topics[:3]), 'study_plan')

    return jsonify(result)


# ---------------------------------------------------------------------------
# Route 8: Dashboard
# ---------------------------------------------------------------------------

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Return all statistics needed for the student dashboard."""
    return jsonify({
        'success':         True,
        'quiz_stats':      get_quiz_stats(),
        'session_stats':   get_session_stats(),
        'recent_quizzes':  get_recent_quiz_results(8),
        'recent_sessions': get_recent_sessions(8),
        'topic_performance':  get_topic_performance(),
        'weekly_history':     get_weekly_quiz_history(),
        'score_trend':        get_score_trend(10),
        'best_and_worst':     get_best_and_worst(),
        'activity_breakdown': get_activity_breakdown(),
        'streak_days':        get_streak_days(),
    })


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'message': 'File is too large. Maximum size is 10 MB.'}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found.'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500


# ---------------------------------------------------------------------------
# Start the server
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from backend.study_generator import USE_REAL_AI, IBM_MODEL_ID
    print("=" * 55)
    print("  StudyMate AI – Backend Server")
    print("  Running at: http://127.0.0.1:5000")
    print(f"  AI Mode    : {'🤖 IBM watsonx (' + IBM_MODEL_ID + ')' if USE_REAL_AI else '🔧 Demo mode (no credentials)'}")
    print("=" * 55)
    app.run(debug=True, port=5000)

