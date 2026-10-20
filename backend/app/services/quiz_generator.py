import json
import logging
import uuid
import re
from typing import Dict, Any, Optional, List

from ..config import settings
from ..models.schemas import QuizQuestion, MicroQuiz, QuizResult, QuizSubmission

logger = logging.getLogger(__name__)

# Server-side cryptographic/session quiz registry to evaluate answers securely
_QUIZ_REGISTRY: Dict[str, MicroQuiz] = {}


class QuizGenerator:
    """Generates and evaluates scenario-based Proof-of-Work micro-quizzes."""

    @classmethod
    def _create_gemini_client(cls):
        if not settings.GEMINI_API_KEY:
            return None
        try:
            from google import genai
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai: {e}")
            return None

    @classmethod
    def register_quiz(cls, quiz: MicroQuiz):
        """Store quiz in session registry for server-side evaluation."""
        _QUIZ_REGISTRY[quiz.quiz_id] = quiz

    @classmethod
    def generate_quiz(
        cls,
        skill_name: str,
        difficulty: str = "intermediate",
        role_title: Optional[str] = None
    ) -> MicroQuiz:
        """
        Generates 3 scenario-based MCQs using Google Gemini API or pre-calibrated bank.
        Stores answer keys in server registry.
        """
        client = cls._create_gemini_client()
        quiz_id = f"quiz-{uuid.uuid4().hex[:10]}"

        if client:
            try:
                quiz = cls._generate_via_gemini(client, quiz_id, skill_name, difficulty, role_title)
                if quiz and len(quiz.questions) == 3:
                    cls.register_quiz(quiz)
                    return quiz
            except Exception as e:
                logger.error(f"Gemini dynamic quiz generation failed: {e}. Falling back to calibrated scenario.")

        # Fallback scenario generation
        quiz = cls._generate_calibrated_quiz(quiz_id, skill_name, difficulty)
        cls.register_quiz(quiz)
        return quiz

    @classmethod
    def _generate_via_gemini(
        cls,
        client,
        quiz_id: str,
        skill_name: str,
        difficulty: str,
        role_title: Optional[str]
    ) -> Optional[MicroQuiz]:
        context = f"in the context of a {role_title}" if role_title else ""
        prompt = f"""
Generate an interactive, timed Proof-of-Work technical micro-quiz for the skill '{skill_name}' {context}.
Difficulty Level: {difficulty}

Requirements:
- Exactly 3 practical, scenario-based multiple choice questions reflecting real-world engineering situations.
- Do NOT ask dry textbook definitions. Ask situational debugging, architectural tradeoffs, or production incident choices.
- Exactly 4 options per question.
- 'correct_index' must be an integer (0, 1, 2, or 3).
- 'explanation' must explain concisely why the chosen answer is technically superior.

Format ONLY as valid JSON conforming strictly to:
{{
  "quiz_id": "{quiz_id}",
  "skill": "{skill_name}",
  "questions": [
    {{
      "id": 1,
      "question": "scenario description...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "..."
    }},
    {{
      "id": 2,
      "question": "scenario description...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 1,
      "explanation": "..."
    }},
    {{
      "id": 3,
      "question": "scenario description...",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 2,
      "explanation": "..."
    }}
  ]
}}
"""
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.25,
            }
        )
        raw_text = response.text.strip()
        cleaned_json = re.sub(r'^```json\s*', '', raw_text)
        cleaned_json = re.sub(r'\s*```$', '', cleaned_json)
        data = json.loads(cleaned_json)

        questions = [QuizQuestion(**q) for q in data.get("questions", [])]
        return MicroQuiz(
            quiz_id=data.get("quiz_id", quiz_id),
            skill=data.get("skill", skill_name),
            questions=questions,
            passing_score=2,
            time_limit_per_question=60
        )

    @classmethod
    def _generate_calibrated_quiz(cls, quiz_id: str, skill_name: str, difficulty: str) -> MicroQuiz:
        questions = [
            QuizQuestion(
                id=1,
                question=f"A production service utilizing {skill_name} experiences intermittent memory pressure during peak spikes. What is the most effective approach to identify and resolve the issue?",
                options=[
                    "Double the physical RAM indefinitely without profiling heap allocations.",
                    "Analyze heap dumps, inspect object lifecycle retention, and fix unclosed connections/streams.",
                    "Force garbage collection synchronously at the start of every client request.",
                    "Disable logging and monitoring dashboards."
                ],
                correct_index=1,
                explanation="Profiling memory allocations and identifying long-lived references or unclosed handles directly resolves the root leak without masking symptoms."
            ),
            QuizQuestion(
                id=2,
                question=f"When designing a resilient client or consumer for an asynchronous {skill_name} pipeline, how should transient downstream network timeouts be handled?",
                options=[
                    "Immediately discard the message and log nothing.",
                    "Implement exponential backoff with jitter and route persistent failures to a Dead Letter Queue (DLQ).",
                    "Block the main application thread until the downstream endpoint answers.",
                    "Retry infinitely in an unthrottled synchronous while-loop."
                ],
                correct_index=1,
                explanation="Exponential backoff with jitter prevents thundering herd problems on struggling downstream dependencies, while DLQs isolate unprocessable payloads."
            ),
            QuizQuestion(
                id=3,
                question=f"In a team environment adopting CI/CD for {skill_name}, what verification step must pass before merging code into the main branch?",
                options=[
                    "Manual verbal approval with no automated checks.",
                    "Automated unit/integration test suites, linter checks, and static analysis security scans.",
                    "Only verifying that the code compiles locally on the developer's laptop.",
                    "Directly pushing to the production branch to test live."
                ],
                correct_index=1,
                explanation="Automated test pipelines verify regression safety, syntax compliance, and security posture objectively before integration."
            )
        ]

        return MicroQuiz(
            quiz_id=quiz_id,
            skill=skill_name,
            questions=questions,
            passing_score=2,
            time_limit_per_question=60
        )

    @classmethod
    def evaluate_submission(cls, submission: QuizSubmission) -> QuizResult:
        """
        Evaluates submitted answers against session-bound questions.
        Computes score, pass/fail status, and provides answer reviews.
        """
        quiz = _QUIZ_REGISTRY.get(submission.quiz_id)
        if not quiz:
            # If not in local in-memory registry, create standard validation
            raise ValueError(f"Quiz ID '{submission.quiz_id}' not found in active verification session.")

        score = 0
        total_questions = len(quiz.questions)
        reviews = []

        for q in quiz.questions:
            student_ans = submission.answers.get(q.id)
            is_correct = (student_ans is not None) and (student_ans == q.correct_index)
            if is_correct:
                score += 1
            
            reviews.append({
                "question_id": q.id,
                "question": q.question,
                "selected_index": student_ans,
                "correct_index": q.correct_index,
                "is_correct": is_correct,
                "explanation": q.explanation,
                "options": q.options
            })

        percentage = round((score / total_questions) * 100, 1) if total_questions > 0 else 0.0
        passed = score >= quiz.passing_score

        if passed:
            feedback = f"Proof-of-Work Verified! You scored {score}/{total_questions} ({percentage}%). Milestone knowledge requirements met."
        else:
            feedback = f"Assessment score: {score}/{total_questions} ({percentage}%). Passing requires at least {quiz.passing_score}/{total_questions}. Review the explanations and retry."

        return QuizResult(
            quiz_id=submission.quiz_id,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            passed=passed,
            feedback=feedback,
            answers_review=reviews
        )
