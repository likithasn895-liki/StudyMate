run_tests.py
------------
Master test runner for StudyMate AI.
Runs every test suite and prints a final pass / fail report.

Usage:
    # Backend-only tests (no server needed):
    python run_tests.py --unit

    # Full integration tests (server must be running in another terminal):
    python run_tests.py --integration

    # Everything:
    python run_tests.py --all
"""

import sys
import os
import subprocess
import time
import argparse

sys.path.insert(0, os.path.dirname(__file__))

SEP   = '─' * 56
PASS  = '  ✅ PASS'
FAIL  = '  ❌ FAIL'
SKIP  = '  ⏭  SKIP'

results = []   # list of (suite_name, passed: bool)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def header(title: str):
    print(f'\n{"="*56}')
    print(f'  {title}')
    print('='*56)


def section(title: str):
    print(f'\n{SEP}')
    print(f'  {title}')
    print(SEP)


def check(label: str, condition: bool, detail: str = ''):
    status = PASS if condition else FAIL
    print(f'{status}  {label}')
    if not condition and detail:
        print(f'         ↳ {detail}')
    return condition


def record(suite: str, passed: bool):
    results.append((suite, passed))


# ---------------------------------------------------------------------------
# Suite 1 — Database layer
# ---------------------------------------------------------------------------

def test_database():
    section('Suite 1 / 5 — Database Layer')
    from database.database import (
        init_db, save_quiz_result, get_recent_quiz_results,
        get_quiz_stats, save_study_session, get_recent_sessions,
        get_session_stats, get_topic_performance, get_weekly_quiz_history,
        get_score_trend, get_best_and_worst, get_activity_breakdown,
        get_streak_days,
    )

    ok = True
    init_db()
    ok &= check('init_db() runs without error', True)

    save_quiz_result('Thermodynamics', 8, 10)
    save_quiz_result('Fluid Mechanics', 6, 10)
    save_quiz_result('Thermodynamics', 9, 10)
    ok &= check('save_quiz_result() — 3 rows inserted', True)

    save_study_session('Thermodynamics', 'summary', 15)
    save_study_session('Thermodynamics', 'quiz',    10)
    save_study_session('Fluid Mechanics', 'questions', 12)
    ok &= check('save_study_session() — 3 rows inserted', True)

    stats = get_quiz_stats()
    ok &= check('get_quiz_stats() returns total_quizzes >= 3',
                stats.get('total_quizzes', 0) >= 3,
                str(stats))
    ok &= check('get_quiz_stats() returns avg_percentage > 0',
                stats.get('avg_percentage', 0) > 0)

    recent = get_recent_quiz_results(5)
    ok &= check('get_recent_quiz_results() returns list',
                isinstance(recent, list) and len(recent) >= 1)

    ss = get_session_stats()
    ok &= check('get_session_stats() total_sessions >= 3',
                ss.get('total_sessions', 0) >= 3)

    tp = get_topic_performance()
    ok &= check('get_topic_performance() returns list with topic field',
                len(tp) > 0 and 'topic' in tp[0])

    wh = get_weekly_quiz_history()
    ok &= check('get_weekly_quiz_history() returns 7 days',
                len(wh) == 7)
    ok &= check('weekly_history entries have label field',
                all('label' in d for d in wh))

    trend = get_score_trend(5)
    ok &= check('get_score_trend() returns list',
                isinstance(trend, list))

    bw = get_best_and_worst()
    ok &= check('get_best_and_worst() has best key',
                'best' in bw)
    ok &= check('get_best_and_worst() best is not None',
                bw['best'] is not None)

    ab = get_activity_breakdown()
    ok &= check('get_activity_breakdown() returns list',
                isinstance(ab, list) and len(ab) > 0)

    streak = get_streak_days()
    ok &= check('get_streak_days() returns int >= 1',
                isinstance(streak, int) and streak >= 1,
                f'got {streak}')

    record('Database Layer', ok)
    return ok


# ---------------------------------------------------------------------------
# Suite 2 — PDF Reader
# ---------------------------------------------------------------------------

def test_pdf_reader():
    section('Suite 2 / 5 — PDF Reader')
    import tempfile
    from backend.pdf_reader import (
        extract_text_from_pdf, validate_pasted_text,
        clean_text, truncate_for_ai, text_stats, is_valid_pdf,
    )

    ok = True
    sample = os.path.join('sample_notes', 'sample_notes.pdf')

    if os.path.exists(sample):
        r = extract_text_from_pdf(sample)
        ok &= check('extract_text_from_pdf() success=True',
                    r['success'], r.get('message'))
        ok &= check('word_count >= 100',
                    r.get('word_count', 0) >= 100,
                    f"got {r.get('word_count')}")
        ok &= check("text contains 'Thermodynamics'",
                    'thermodynamics' in r.get('text', '').lower())
    else:
        print(f'{SKIP}  sample PDF not found — run create_sample_pdf.py first')

    # Validation — bad inputs
    r2 = extract_text_from_pdf('nonexistent.pdf')
    ok &= check('non-existent file → success=False', not r2['success'])

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, mode='wb') as tf:
        tf.write(b'Not a PDF')
        fake = tf.name
    r3 = extract_text_from_pdf(fake)
    os.unlink(fake)
    ok &= check('non-PDF bytes → success=False', not r3['success'])

    # Paste validation
    ok &= check('empty paste → success=False',
                not validate_pasted_text('')['success'])
    ok &= check('short paste → success=False',
                not validate_pasted_text('hi there')['success'])

    long = ('Thermodynamics is the study of heat, work, and energy. '
            'Engineers use these principles in engines and power plants. '
            'The first law states energy is conserved.') * 2
    r4 = validate_pasted_text(long)
    ok &= check('valid paste → success=True', r4['success'])
    ok &= check('valid paste returns word_count > 0',
                r4.get('word_count', 0) > 0)

    # Utilities
    cleaned = clean_text('  hello   world  \n\n\n\nbye  ')
    ok &= check('clean_text removes triple blank lines',
                '\n\n\n' not in cleaned)

    words_50  = 'word ' * 50
    words_4k  = 'word ' * 4000
    ok &= check('truncate_for_ai: short text unchanged',
                'truncated' not in truncate_for_ai(words_50, 3000))
    ok &= check('truncate_for_ai: long text truncated',
                'truncated' in truncate_for_ai(words_4k, 3000))

    stats = text_stats('one two three four five six seven eight nine ten')
    ok &= check('text_stats word_count == 10', stats['word_count'] == 10)

    record('PDF Reader', ok)
    return ok


# ---------------------------------------------------------------------------
# Suite 3 — Quiz Manager
# ---------------------------------------------------------------------------

def test_quiz_manager():
    section('Suite 3 / 5 — Quiz Manager')
    from backend.quiz_manager import (
        parse_mcq_questions, grade_quiz, get_performance_feedback,
    )

    ok = True
    SAMPLE_MCQ = """
Q1. What is Newton's first law?
A) Force equals mass times acceleration
B) An object at rest stays at rest unless acted upon
C) Every action has an equal and opposite reaction
D) Energy cannot be created or destroyed
Answer: B
Explanation: Newton's first law defines inertia.

Q2. What does PV = nRT represent?
A) Newton's second law
B) Carnot efficiency
C) The ideal gas law
D) Fourier's law
Answer: C
Explanation: PV = nRT is the ideal gas equation.

Q3. What does the second law of thermodynamics state?
A) Energy is conserved
B) Entropy always increases in isolated systems
C) Temperature is constant
D) Pressure equals force divided by area
Answer: B
Explanation: The second law describes entropy.
"""

    qs = parse_mcq_questions(SAMPLE_MCQ)
    ok &= check('parse_mcq_questions() returns 3 questions',
                len(qs) == 3, f'got {len(qs)}')
    ok &= check('all questions have text',
                all(bool(q['question']) for q in qs))
    ok &= check('all questions have 4 options',
                all(len(q['options']) == 4 for q in qs))
    ok &= check('all questions have answer field',
                all(bool(q['answer']) for q in qs))

    # Grade: Q1 correct (B), Q2 wrong (A), Q3 correct (B)
    answers = {'0': 'B', '1': 'A', '2': 'B'}
    result  = grade_quiz(qs, answers)
    ok &= check('grade_quiz() score == 2',    result['score'] == 2,
                f"got {result['score']}")
    ok &= check('grade_quiz() total == 3',    result['total'] == 3)
    ok &= check('grade_quiz() percentage == 66.67',
                result['percentage'] == 66.67)
    ok &= check('results list has 3 items',   len(result['results']) == 3)
    ok &= check('Q1 is_correct == True',      result['results'][0]['is_correct'])
    ok &= check('Q2 is_correct == False',     not result['results'][1]['is_correct'])
    ok &= check('Q3 is_correct == True',      result['results'][2]['is_correct'])

    # Feedback
    ok &= check('feedback 90% contains Excellent',
                'Excellent' in get_performance_feedback(90))
    ok &= check('feedback 75% contains Good',
                'Good' in get_performance_feedback(75))
    ok &= check('feedback 50% contains Halfway',
                'Halfway' in get_performance_feedback(50))
    ok &= check('feedback 30% contains Keep going',
                'Keep' in get_performance_feedback(30))

    # Edge cases — format variants
    VARIANT = """
1. What is Boyle's law?
a. PV = constant at constant temperature
b. V/T = constant at constant pressure
c. PV = nRT
d. F = ma
Correct answer: A
Explanation: Boyle's law states pressure and volume are inversely proportional.
"""
    qs2 = parse_mcq_questions(VARIANT)
    ok &= check('parser handles 1. numbering and a. options',
                len(qs2) == 1, f'got {len(qs2)}')

    record('Quiz Manager', ok)
    return ok


# ---------------------------------------------------------------------------
# Suite 4 — Study Generator (demo mode)
# ---------------------------------------------------------------------------

def test_study_generator():
    section('Suite 4 / 5 — Study Generator')
    from backend.study_generator import (
        generate_summary, generate_questions,
        generate_mcq_for_quiz, generate_study_plan, USE_REAL_AI,
    )
    from backend.quiz_manager import parse_mcq_questions

    ok = True
    mode = '🤖 IBM watsonx' if USE_REAL_AI else '🔧 Demo'
    print(f'  Mode: {mode}')

    sample = (
        'Thermodynamics studies heat, work, and temperature. '
        'The first law states energy is conserved. '
        'The second law states entropy always increases. '
        'The ideal gas law is PV = nRT. '
        'Carnot efficiency is 1 - T_cold/T_hot. '
        'Engineers apply these in engines and refrigerators.'
    ) * 3   # repeat to exceed 30-word minimum

    # Summary
    r = generate_summary(sample)
    ok &= check('generate_summary() success=True',   r['success'], r.get('message'))
    ok &= check('summary is non-empty string',        bool(r.get('summary', '').strip()))

    # Questions — all types
    for qtype in ('short', 'long', 'mcq', 'all'):
        r = generate_questions(sample, qtype)
        ok &= check(f'generate_questions({qtype}) success=True',
                    r['success'], r.get('message'))
        ok &= check(f'generate_questions({qtype}) non-empty',
                    bool(r.get('questions', '').strip()))

    # MCQ for quiz
    r = generate_mcq_for_quiz(sample, 3)
    ok &= check('generate_mcq_for_quiz() success=True', r['success'], r.get('message'))
    ok &= check('raw_text is non-empty', bool(r.get('raw_text', '').strip()))

    parsed = parse_mcq_questions(r['raw_text'])
    ok &= check('MCQ for quiz: 3 questions parsed',
                len(parsed) == 3, f'got {len(parsed)}')
    ok &= check('each question has ≥ 2 options',
                all(len(q['options']) >= 2 for q in parsed))

    # Study plan
    r = generate_study_plan(['Thermodynamics', 'Fluid Mechanics'],
                            daily_hours=2, days=5,
                            priorities={'Thermodynamics': 'high'})
    ok &= check('generate_study_plan() success=True', r.get('success'), r.get('message',''))
    ok &= check('plan has type field', bool(r.get('type')))

    # Short-text guard
    short = 'Hello world'
    ok &= check('too-short text → summary fails',
                not generate_summary(short)['success'])
    ok &= check('too-short text → questions fail',
                not generate_questions(short)['success'])

    record('Study Generator', ok)
    return ok


# ---------------------------------------------------------------------------
# Suite 5 — Integration (requires running server)
# ---------------------------------------------------------------------------

def test_integration():
    section('Suite 5 / 5 — Integration (live server)')
    try:
        import requests
    except ImportError:
        os.system(f'{sys.executable} -m pip install requests -q')
        import requests

    BASE = 'http://127.0.0.1:5000'
    ok   = True

    # Check server alive
    try:
        r = requests.get(f'{BASE}/api/dashboard', timeout=5)
        ok &= check('Server is reachable', r.status_code == 200)
    except requests.exceptions.ConnectionError:
        print(f'\n  ❌ Cannot connect to {BASE}')
        print('     Start the server first: python app.py')
        record('Integration', False)
        return False

    def post(path, **kwargs):
        return requests.post(f'{BASE}{path}', timeout=60, **kwargs)

    def get(path):
        return requests.get(f'{BASE}{path}', timeout=10)

    # GET /
    r = get('/')
    ok &= check('GET / → 200',            r.status_code == 200)
    ok &= check('GET / contains HTML',    'StudyMate' in r.text)

    # POST /api/paste
    TEXT = ('Thermodynamics is the study of heat, work, and temperature. '
            'The first law states energy cannot be created or destroyed. '
            'The second law states entropy always increases in isolated systems. '
            'PV = nRT is the ideal gas law. Engineers apply these laws everywhere.')

    r = post('/api/paste', json={'text': TEXT})
    d = r.json()
    ok &= check('POST /api/paste → success',    d.get('success') is True,  d.get('message'))
    ok &= check('paste returns word_count > 0', d.get('word_count', 0) > 0)

    # Edge: empty paste
    ok &= check('Empty paste → 200 + success=False',
                not post('/api/paste', json={'text': ''}).json().get('success'))

    # POST /api/summarize
    r = post('/api/summarize', json={})
    d = r.json()
    ok &= check('POST /api/summarize → success',   d.get('success') is True, d.get('message'))
    ok &= check('summary is non-empty',            bool(d.get('summary', '').strip()))

    # POST /api/questions — all types
    for qtype in ('short', 'long', 'mcq', 'all'):
        r = post('/api/questions', json={'type': qtype})
        d = r.json()
        ok &= check(f'questions type={qtype} → success',
                    d.get('success') is True, d.get('message'))

    # POST /api/quiz/generate
    r = post('/api/quiz/generate', json={'num_questions': 3})
    d = r.json()
    ok &= check('quiz/generate → success',       d.get('success') is True, d.get('message'))
    ok &= check('3 questions returned',           len(d.get('questions', [])) == 3)
    ok &= check('questions have text + options',
                all(bool(q.get('question')) and len(q.get('options', {})) >= 2
                    for q in d.get('questions', [])))

    # POST /api/quiz/submit
    n_q     = len(d.get('questions', []))
    answers = {str(i): 'A' for i in range(n_q)}
    r = post('/api/quiz/submit', json={'answers': answers, 'topic': 'Test Run'})
    d = r.json()
    ok &= check('quiz/submit → success',         d.get('success') is True,    d.get('message'))
    ok &= check('score field present',           isinstance(d.get('score'),   int))
    ok &= check('percentage field present',      isinstance(d.get('percentage'), (int, float)))
    ok &= check('results list present',          isinstance(d.get('results'), list))
    ok &= check('feedback non-empty',            bool(d.get('feedback', '')))

    # POST /api/study-plan
    r = post('/api/study-plan',
             json={'topics': ['Thermodynamics', 'Fluid Mechanics'],
                   'daily_hours': 2, 'days': 5})
    d = r.json()
    ok &= check('study-plan → success',          d.get('success') is True,  d.get('message'))
    ok &= check('plan has type field',           bool(d.get('type')))

    # Edge: empty topics → 400
    ok &= check('empty topics → 400',
                post('/api/study-plan',
                     json={'topics': [], 'daily_hours': 2, 'days': 5}).status_code == 400)

    # GET /api/dashboard
    r = get('/api/dashboard')
    d = r.json()
    ok &= check('GET /api/dashboard → success',       d.get('success') is True)
    ok &= check('quiz_stats present',                  'quiz_stats'      in d)
    ok &= check('session_stats present',               'session_stats'   in d)
    ok &= check('topic_performance present',           'topic_performance' in d)
    ok &= check('weekly_history is 7 days',
                len(d.get('weekly_history', [])) == 7)
    ok &= check('score_trend is list',
                isinstance(d.get('score_trend'), list))
    ok &= check('activity_breakdown is list',
                isinstance(d.get('activity_breakdown'), list))
    ok &= check('streak_days is int',
                isinstance(d.get('streak_days'), int))
    ok &= check('total_quizzes >= 1',
                d.get('quiz_stats', {}).get('total_quizzes', 0) >= 1)

    # PDF upload
    sample = os.path.join('sample_notes', 'sample_notes.pdf')
    if os.path.exists(sample):
        with open(sample, 'rb') as f:
            r = requests.post(f'{BASE}/api/upload',
                              files={'file': ('sample_notes.pdf', f, 'application/pdf')},
                              timeout=30)
        d = r.json()
        ok &= check('PDF upload → success',       d.get('success') is True,  d.get('message'))
        ok &= check('PDF word_count > 50',        d.get('word_count', 0) > 50)
    else:
        print(f'{SKIP}  PDF upload — sample PDF not found')

    record('Integration', ok)
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='StudyMate AI test runner')
    parser.add_argument('--unit',        action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--all',         action='store_true', help='Run all tests (default)')
    args = parser.parse_args()

    run_unit = args.unit or args.all or (not args.unit and not args.integration and not args.all)
    run_int  = args.integration or args.all

    header('StudyMate AI — Master Test Runner')
    print(f'  Unit tests       : {"YES" if run_unit else "skip"}')
    print(f'  Integration tests: {"YES" if run_int  else "skip"}')

    if run_unit:
        test_database()
        test_pdf_reader()
        test_quiz_manager()
        test_study_generator()

    if run_int:
        test_integration()

    # Final report
    total  = len(results)
    passed = sum(1 for _, ok in results if ok)
    failed = total - passed

    header('FINAL REPORT')
    for suite, ok in results:
        print(f'  {"✅" if ok else "❌"}  {suite}')

    print(f'\n  {passed}/{total} suites passed', end='')
    if failed:
        print(f'  ({failed} failed)')
        print('\n  Failed suites:')
        for suite, ok in results:
            if not ok:
                print(f'    ❌ {suite}')
    else:
        print()
        print('\n  🎉 ALL SUITES PASSED!')

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()

