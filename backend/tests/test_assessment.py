import pytest
from app.services.quiz_generator import QuizGenerator
from app.services.sandbox_evaluator import SandboxEvaluator
from app.models.schemas import QuizSubmission, SandboxEvaluationRequest


def test_quiz_generation_and_scoring():
    """Verify quiz generation, registration, and accurate grade evaluation."""
    quiz = QuizGenerator.generate_quiz(skill_name="Docker", difficulty="intermediate")

    assert quiz.skill == "Docker"
    assert len(quiz.questions) == 3
    for q in quiz.questions:
        assert len(q.options) == 4
        assert 0 <= q.correct_index <= 3
        assert len(q.explanation) > 0

    # Test passing submission (3/3 correct)
    answers_pass = {q.id: q.correct_index for q in quiz.questions}
    submission_pass = QuizSubmission(
        quiz_id=quiz.quiz_id,
        answers=answers_pass,
        time_spent_seconds=45
    )
    result_pass = QuizGenerator.evaluate_submission(submission_pass)
    assert result_pass.passed is True
    assert result_pass.score == 3
    assert result_pass.percentage == 100.0

    # Test failing submission (0/3 correct)
    answers_fail = {q.id: (q.correct_index + 1) % 4 for q in quiz.questions}
    submission_fail = QuizSubmission(
        quiz_id=quiz.quiz_id,
        answers=answers_fail,
        time_spent_seconds=30
    )
    result_fail = QuizGenerator.evaluate_submission(submission_fail)
    assert result_fail.passed is False
    assert result_fail.score == 0


def test_sandbox_evaluator_valid_js():
    """Test JavaScript challenge evaluation with valid syntax and criteria."""
    req = SandboxEvaluationRequest(
        challenge_id="test-js-01",
        language="javascript",
        code="""
        function processData(items) {
            if (!items) return [];
            return items.filter(x => x.active);
        }
        """
    )
    res = SandboxEvaluator.evaluate(req)
    assert res.all_tests_passed is True
    assert res.score_percentage == 100.0
    assert res.passed is True


def test_sandbox_evaluator_empty_code():
    """Empty code should fail verification gracefully."""
    req = SandboxEvaluationRequest(
        challenge_id="test-empty",
        language="javascript",
        code="   "
    )
    res = SandboxEvaluator.evaluate(req)
    assert res.passed is False
    assert res.score_percentage == 0.0


def test_sandbox_evaluator_html_card():
    """HTML widget challenge testing DOM element existence."""
    req = SandboxEvaluationRequest(
        challenge_id="flutter-card-challenge",
        language="html",
        code="""
        <div class="material-card shadow-lg p-4">
            <h3>Card Title</h3>
            <button class="btn-inc action-btn">Click Me</button>
        </div>
        """
    )
    res = SandboxEvaluator.evaluate(req)
    assert res.all_tests_passed is True
    assert res.passed is True

