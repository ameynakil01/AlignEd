import json
import logging
import uuid
import re
from typing import List, Dict, Any, Optional

from ..config import settings
from ..models.schemas import (
    RoadmapResponse,
    RoadmapMilestone,
    CuratedEmbed,
    MicroQuiz,
    QuizQuestion,
    SandboxChallenge,
    SandboxTestCase,
    SkillMatch,
)

logger = logging.getLogger(__name__)


# Calibrated resource bank for high-quality video embeds and interactive exercises
CURATED_RESOURCE_BANK: Dict[str, Dict[str, Any]] = {
    "Dart": {
        "video": {
            "title": "Dart Programming Tutorial - Full Course for Beginners",
            "url": "https://www.youtube.com/watch?v=Ej_Pcr4uC2Q",
            "embed_url": "https://www.youtube-nocookie.com/embed/Ej_Pcr4uC2Q",
            "summary": "Master core Dart syntax, null safety, asynchronous programming with Futures and Streams, and object-oriented class hierarchies."
        },
        "sandbox": {
            "title": "Dart Collections & Null Safety Exercise",
            "language": "javascript",
            "prompt": "Write a function `filterActiveUsers(users)` that takes an array of user objects and returns only users where `isActive === true` and `role !== null`, sorted by name ascending.",
            "starter_code": "function filterActiveUsers(users) {\n  // Implement logic to filter active users with valid non-null roles\n  return [];\n}",
            "test_cases": [
                {"description": "Filters inactive users", "assertion_type": "function_result", "expected": "active_only"},
                {"description": "Ensures role is not null", "assertion_type": "contains_regex", "expected": "role"}
            ],
            "solution_hint": "Use Array.prototype.filter to check user.isActive && user.role !== null, followed by .sort()."
        }
    },
    "Flutter": {
        "video": {
            "title": "Flutter Course for Beginners - 37hr Zero to Hero",
            "url": "https://www.youtube.com/watch?v=VPvVD8t02U8",
            "embed_url": "https://www.youtube-nocookie.com/embed/VPvVD8t02U8",
            "summary": "Build responsive cross-platform interfaces using Flutter widgets, layouts, animations, navigation, and theme customization."
        },
        "sandbox": {
            "title": "Flutter Widget Tree Simulator",
            "language": "html",
            "prompt": "Construct a responsive mobile card component simulating a Flutter Material card with an image header, title, and action button with class 'action-btn'.",
            "starter_code": "<div class=\"material-card p-4 rounded-xl shadow-md bg-slate-800\">\n  <!-- Add card title and an action button with class action-btn -->\n</div>",
            "test_cases": [
                {"description": "Contains action button with class action-btn", "assertion_type": "dom_element", "expected": ".action-btn"},
                {"description": "Renders material card container", "assertion_type": "dom_element", "expected": ".material-card"}
            ],
            "solution_hint": "Create an h3 title and a button element with class 'action-btn px-4 py-2 bg-indigo-600 rounded text-white'."
        }
    },
    "FastAPI/Flask": {
        "video": {
            "title": "FastAPI Full Course - Python Web APIs with Asynchronous Architecture",
            "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
            "embed_url": "https://www.youtube-nocookie.com/embed/0sOvCWFmrtA",
            "summary": "Deep dive into ASGI async endpoints, Pydantic request validation, dependency injection, and automatic OpenAPI documentation."
        },
        "sandbox": {
            "title": "Asynchronous API Route Validation",
            "language": "javascript",
            "prompt": "Implement an API payload validator `validateEndpointRequest(payload)` verifying that `email` contains an '@' sign and `age` is an integer >= 18. Return `{ valid: boolean, errors: string[] }`.",
            "starter_code": "function validateEndpointRequest(payload) {\n  const errors = [];\n  // Validate email format and age threshold\n  return { valid: errors.length === 0, errors };\n}",
            "test_cases": [
                {"description": "Validates valid payload", "assertion_type": "function_result", "expected": "valid"},
                {"description": "Validates email pattern", "assertion_type": "contains_regex", "expected": "@"}
            ],
            "solution_hint": "Check payload.email && payload.email.includes('@'), and Number.isInteger(payload.age) && payload.age >= 18."
        }
    },
    "PostgreSQL": {
        "video": {
            "title": "PostgreSQL Database Architecture & Query Optimization Course",
            "url": "https://www.youtube.com/watch?v=qw--VYLpxG4",
            "embed_url": "https://www.youtube-nocookie.com/embed/qw--VYLpxG4",
            "summary": "Relational data modeling, ACID transactions, B-Tree indexes, CTEs, and window functions in PostgreSQL."
        },
        "sandbox": {
            "title": "SQL Query Constructor & Normalization",
            "language": "javascript",
            "prompt": "Write a query generator `buildTopSalesQuery(limit)` that returns a parameterized SQL string selecting `user_id`, `SUM(amount) AS total` from `transactions`, grouped by `user_id`, ordered by `total DESC`, with `LIMIT ${limit}`.",
            "starter_code": "function buildTopSalesQuery(limit) {\n  // Return valid SQL SELECT statement\n  return '';\n}",
            "test_cases": [
                {"description": "Includes GROUP BY user_id", "assertion_type": "contains_regex", "expected": "GROUP BY user_id"},
                {"description": "Orders by total descending", "assertion_type": "contains_regex", "expected": "DESC"}
            ],
            "solution_hint": "Return `SELECT user_id, SUM(amount) AS total FROM transactions GROUP BY user_id ORDER BY total DESC LIMIT ${limit};`."
        }
    },
    "React": {
        "video": {
            "title": "React 19 & Modern Hooks Masterclass",
            "url": "https://www.youtube.com/watch?v=CgkZ7MvWUAA",
            "embed_url": "https://www.youtube-nocookie.com/embed/CgkZ7MvWUAA",
            "summary": "Stateful components, useEffect synchronization, custom hooks, context state management, and performance optimization."
        },
        "sandbox": {
            "title": "React Counter & DOM Event Handler",
            "language": "html",
            "prompt": "Build an interactive counter component containing a display span with id 'count-val' initialized to 0, an increment button with id 'btn-inc', and a decrement button with id 'btn-dec'. Include a script wiring click events.",
            "starter_code": "<div class=\"counter-box p-4 text-center\">\n  <span id=\"count-val\">0</span>\n  <!-- Add buttons and script to increment/decrement count-val -->\n</div>",
            "test_cases": [
                {"description": "Contains counter value element", "assertion_type": "dom_element", "expected": "#count-val"},
                {"description": "Contains increment button", "assertion_type": "dom_element", "expected": "#btn-inc"},
                {"description": "Contains decrement button", "assertion_type": "dom_element", "expected": "#btn-dec"}
            ],
            "solution_hint": "Add `<button id='btn-inc'>+</button>` and `<button id='btn-dec'>-</button>` with script modifying `#count-val.innerText`."
        }
    },
    "Docker": {
        "video": {
            "title": "Docker Tutorial for Beginners - Full Free Course",
            "url": "https://www.youtube.com/watch?v=3c-iBn73dDE",
            "embed_url": "https://www.youtube-nocookie.com/embed/3c-iBn73dDE",
            "summary": "Containerization fundamentals, multi-stage builds, port forwarding, docker networks, and docker-compose orchestration."
        },
        "sandbox": {
            "title": "Dockerfile Configuration Generator",
            "language": "javascript",
            "prompt": "Write a function `generateDockerfile(port)` returning a multi-line Dockerfile string containing `FROM python:3.11-slim`, `WORKDIR /app`, `COPY . .`, `EXPOSE ${port}`, and `CMD [\"python\", \"main.py\"]`.",
            "starter_code": "function generateDockerfile(port) {\n  // Generate Dockerfile string\n  return '';\n}",
            "test_cases": [
                {"description": "Specifies base image python:3.11-slim", "assertion_type": "contains_regex", "expected": "FROM python:3.11-slim"},
                {"description": "Exposes specified port", "assertion_type": "contains_regex", "expected": "EXPOSE"}
            ],
            "solution_hint": "Use template literals to join standard Docker commands."
        }
    },
    "REST APIs": {
        "video": {
            "title": "REST API Architecture and Design Principles",
            "url": "https://www.youtube.com/watch?v=-MTSQjw5DrM",
            "embed_url": "https://www.youtube-nocookie.com/embed/-MTSQjw5DrM",
            "summary": "HTTP verbs, RESTful resource URI conventions, status code semantics, pagination, and token-based authentication."
        },
        "sandbox": {
            "title": "REST API Response Status Handler",
            "language": "javascript",
            "prompt": "Write a function `formatApiResponse(statusCode, data, error)` that returns standard envelope `{ status: statusCode, success: boolean, payload: data || null, error: error || null }` where success is true only for 2xx status codes.",
            "starter_code": "function formatApiResponse(statusCode, data, error) {\n  // Return formatted JSON envelope\n  return {};\n}",
            "test_cases": [
                {"description": "Formats 200 OK correctly", "assertion_type": "function_result", "expected": "success"},
                {"description": "Returns status code property", "assertion_type": "contains_regex", "expected": "status"}
            ],
            "solution_hint": "Check `statusCode >= 200 && statusCode < 300` for `success` property."
        }
    },
    "Pandas": {
        "video": {
            "title": "Pandas Full Tutorial - Data Analysis with Python",
            "url": "https://www.youtube.com/watch?v=vmEHCJofslg",
            "embed_url": "https://www.youtube-nocookie.com/embed/vmEHCJofslg",
            "summary": "Master DataFrames, Series, filtering, indexing, aggregation, pivot tables, and handling missing datasets."
        },
        "sandbox": {
            "title": "Data Aggregation Matrix Processor",
            "language": "javascript",
            "prompt": "Write a function `computeSummaryStats(records)` taking array of numeric objects `[{ val: 10 }, { val: 20 }]` and returning `{ count, mean, min, max }`.",
            "starter_code": "function computeSummaryStats(records) {\n  // Compute statistics\n  return { count: 0, mean: 0, min: 0, max: 0 };\n}",
            "test_cases": [
                {"description": "Calculates correct count and mean", "assertion_type": "function_result", "expected": "valid_stats"},
                {"description": "Returns stats object keys", "assertion_type": "contains_regex", "expected": "mean"}
            ],
            "solution_hint": "Extract `val` array, use reduce to compute sum, then calculate mean, Math.min, Math.max."
        }
    }
}


class RoadmapGenerator:
    """Generates personalized, structured weekly learning trajectories with PoW verification."""

    @classmethod
    def _create_gemini_client(cls):
        """Instantiate google.genai Client if GEMINI_API_KEY is configured."""
        if not settings.GEMINI_API_KEY:
            return None
        try:
            from google import genai
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai client: {e}")
            return None

    @classmethod
    def generate_roadmap(
        cls,
        role_id: str,
        role_title: str,
        missing_skills: List[SkillMatch],
        covered_skills: List[SkillMatch],
        student_name: str = "Student"
    ) -> RoadmapResponse:
        """
        Orchestrates roadmap creation using Google Gemini API with fallback to deterministic expert curriculum.
        """
        client = cls._create_gemini_client()
        total_missing = len(missing_skills)

        # If student already covers everything or 0 missing skills, create an advanced mastery track
        target_skills = missing_skills if total_missing > 0 else covered_skills

        # Attempt Gemini generation if client is available
        if client and target_skills:
            try:
                roadmap = cls._generate_with_gemini(client, role_id, role_title, target_skills, covered_skills, student_name)
                if roadmap and len(roadmap.milestones) > 0:
                    return roadmap
            except Exception as e:
                logger.error(f"Gemini API roadmap generation failed, falling back to expert curriculum: {e}")

        # Deterministic, high-yield fallback generator
        return cls._generate_fallback_roadmap(role_id, role_title, target_skills, covered_skills, student_name)

    @classmethod
    def _generate_with_gemini(
        cls,
        client,
        role_id: str,
        role_title: str,
        target_skills: List[SkillMatch],
        covered_skills: List[SkillMatch],
        student_name: str
    ) -> Optional[RoadmapResponse]:
        """Calls Google Gemini API (gemini-2.5-flash / gemini-1.5-flash) to generate structured roadmap JSON."""
        skills_summary = ", ".join([f"{s.skill_name} ({s.category}, priority: {s.priority})" for s in target_skills])
        covered_summary = ", ".join([s.skill_name for s in covered_skills]) or "None"

        prompt = f"""
You are the Lead Curriculum Architect for AlignED, an engineering career platform.
Design a highly structured, week-by-week learning trajectory for a student named '{student_name}' aspiring to become a '{role_title}'.

Target Missing Skills to Bridge: {skills_summary}
Existing Student Strengths (Already Covered): {covered_summary}

Generate between 3 to 6 weekly milestones. For each milestone, provide:
1. week: int (1, 2, 3...)
2. milestone_id: string (unique e.g. ms-week-1)
3. title: string (actionable and motivating)
4. target_skill: string (must match one of the missing skills)
5. objective: string (clear learning goals)
6. estimated_hours: int (typically 8 to 14)
7. curated_embed: object with:
   - type: "youtube"
   - title: video title
   - url: real YouTube watch URL
   - embed_url: YouTube embed URL format 'https://www.youtube-nocookie.com/embed/VIDEO_ID'
   - min_watch_percentage: 75
   - min_read_seconds: 45
   - summary: concise summary of what to learn
8. micro_quiz: object with:
   - quiz_id: string
   - skill: target skill name
   - questions: 3 scenario-based MCQs. Each question must have:
     * id: int (1, 2, 3)
     * question: practical real-world scenario
     * options: 4 distinct strings
     * correct_index: int (0 to 3)
     * explanation: clear reasoning why the answer is correct
9. sandbox_challenge: object with:
   - challenge_id: string
   - title: practical coding exercise
   - language: "javascript" or "html"
   - prompt: exact specifications of what to write
   - starter_code: code template with comments
   - solution_hint: hint for completion
   - test_cases: array of 2 test cases with 'description', 'assertion_type' ("contains_regex" or "dom_element"), and 'expected' pattern.

Respond ONLY with valid JSON conforming to this schema. Do not include markdown preamble.
"""
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }
        )

        raw_text = response.text.strip()
        # Clean any accidental markdown backticks
        cleaned_json = re.sub(r'^```json\s*', '', raw_text)
        cleaned_json = re.sub(r'\s*```$', '', cleaned_json)

        data = json.loads(cleaned_json)
        milestones_list = []
        milestones_raw = data.get("milestones", data if isinstance(data, list) else [])

        for idx, m in enumerate(milestones_raw):
            status = "in_progress" if idx == 0 else "locked"
            m["status"] = status
            # Ensure required embed & quiz structure
            if "curated_embed" not in m:
                m["curated_embed"] = {
                    "type": "youtube",
                    "title": f"Learn {m.get('target_skill', 'Core Competency')}",
                    "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
                    "embed_url": "https://www.youtube-nocookie.com/embed/0sOvCWFmrtA",
                    "min_watch_percentage": 75,
                    "min_read_seconds": 45,
                    "summary": m.get("objective", "")
                }
            milestones_list.append(RoadmapMilestone(**m))

        total_count = len(target_skills) + len(covered_skills)
        match_perc = round((len(covered_skills) / total_count) * 100, 1) if total_count > 0 else 0.0

        return RoadmapResponse(
            roadmap_id=str(uuid.uuid4())[:8],
            role_id=role_id,
            role_title=role_title,
            student_name=student_name,
            match_percentage=match_perc,
            total_weeks=len(milestones_list),
            milestones=milestones_list
        )

    @classmethod
    def _generate_fallback_roadmap(
        cls,
        role_id: str,
        role_title: str,
        target_skills: List[SkillMatch],
        covered_skills: List[SkillMatch],
        student_name: str
    ) -> RoadmapResponse:
        """Deterministic expert curriculum generator with realistic embedded videos and sandboxes."""
        milestones: List[RoadmapMilestone] = []

        # Sort target skills: high priority first, then by weight
        sorted_targets = sorted(
            target_skills,
            key=lambda s: (0 if s.priority == "high" else 1 if s.priority == "medium" else 2, -s.weight)
        )

        for i, skill_match in enumerate(sorted_targets[:5]):
            week_num = i + 1
            skill_name = skill_match.skill_name
            res = CURATED_RESOURCE_BANK.get(skill_name, None)

            # Fallback video if not directly in resource bank
            if res:
                embed_info = res["video"]
                sandbox_info = res["sandbox"]
            else:
                embed_info = {
                    "title": f"Complete {skill_name} Engineering Bootcamp",
                    "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
                    "embed_url": "https://www.youtube-nocookie.com/embed/0sOvCWFmrtA",
                    "summary": f"Comprehensive masterclass covering architecture, best practices, and practical patterns for {skill_name}."
                }
                sandbox_info = {
                    "title": f"{skill_name} Hands-On Verification Challenge",
                    "language": "javascript",
                    "prompt": f"Implement a core handler function `process{re.sub(r'[^a-zA-Z]', '', skill_name)}Task(input)` that validates non-empty input and returns an execution object `{{ success: true, skill: '{skill_name}', processedAt: Date.now() }}`.",
                    "starter_code": f"function process{re.sub(r'[^a-zA-Z]', '', skill_name)}Task(input) {{\n  if (!input) throw new Error('Input is mandatory');\n  return {{\n    success: true,\n    skill: '{skill_name}',\n    processedAt: Date.now()\n  }};\n}}",
                    "test_cases": [
                        {"description": "Returns success true", "assertion_type": "contains_regex", "expected": "success"},
                        {"description": f"Verifies skill name {skill_name}", "assertion_type": "contains_regex", "expected": skill_name}
                    ],
                    "solution_hint": "Ensure input is checked and the returned object contains the exact keys requested."
                }

            # Pre-calibrated scenario questions for PoW quiz
            quiz_questions = [
                QuizQuestion(
                    id=1,
                    question=f"In a production system utilizing {skill_name}, an unexpected latency spike occurs under high concurrent traffic. What is the most architecturally sound initial triage step?",
                    options=[
                        "Immediately restart all servers without inspecting telemetry logs.",
                        "Inspect asynchronous event loops, database connection pool bottlenecks, and query latency traces.",
                        "Disable input validation to speed up request handling.",
                        "Convert all relational tables to flat files on disk."
                    ],
                    correct_index=1,
                    explanation=f"When debugging latency in {skill_name} systems, profiling event loops, connection pool saturation, and DB query execution times provides immediate root-cause visibility."
                ),
                QuizQuestion(
                    id=2,
                    question=f"Which design pattern is considered best practice when structuring modular components with {skill_name} to preserve separation of concerns?",
                    options=[
                        "Colocate UI presentation, network calls, and database mutations within a single top-level function.",
                        "Utilize layered architecture separating presentation, business logic/services, and repository data sources.",
                        "Use global mutable state across all modules without access barriers.",
                        "Avoid unit tests and rely exclusively on production monitoring."
                    ],
                    correct_index=1,
                    explanation="Layered architecture with dependency inversion isolates business logic from UI and transport mechanisms, making the system testable and maintainable."
                ),
                QuizQuestion(
                    id=3,
                    question=f"When deploying updates for a service built with {skill_name}, how should breaking schema changes be introduced safely?",
                    options=[
                        "Apply destructive DB column drops directly during peak traffic hours.",
                        "Adopt an expand-and-contract (parallel-run) migration strategy with backward-compatible API versions.",
                        "Ignore versioning and force client apps to fail until they update.",
                        "Delete the database and restore from the latest night backup."
                    ],
                    correct_index=1,
                    explanation="The expand-and-contract pattern allows new and legacy clients to operate concurrently during phased rollouts without downtime."
                )
            ]

            milestones.append(
                RoadmapMilestone(
                    milestone_id=f"ms-week-{week_num}",
                    week=week_num,
                    title=f"Week {week_num}: {skill_name} Core Competency & Hands-On Mastery",
                    target_skill=skill_name,
                    objective=f"Bridge the critical industry gap in {skill_name} through targeted concept mastery, architecture patterns, and verified code execution.",
                    estimated_hours=10,
                    status="in_progress" if week_num == 1 else "locked",
                    priority=skill_match.priority,
                    curated_embed=CuratedEmbed(
                        type="youtube",
                        title=embed_info["title"],
                        url=embed_info["url"],
                        embed_url=embed_info["embed_url"],
                        min_watch_percentage=75,
                        min_read_seconds=45,
                        summary=embed_info["summary"]
                    ),
                    micro_quiz=MicroQuiz(
                        quiz_id=f"quiz-{skill_name.lower().replace(' ', '-').replace('/', '-')}",
                        skill=skill_name,
                        questions=quiz_questions,
                        passing_score=2,
                        time_limit_per_question=60
                    ),
                    sandbox_challenge=SandboxChallenge(
                        challenge_id=f"sandbox-{skill_name.lower().replace(' ', '-').replace('/', '-')}",
                        title=sandbox_info["title"],
                        language=sandbox_info["language"],
                        prompt=sandbox_info["prompt"],
                        starter_code=sandbox_info["starter_code"],
                        solution_hint=sandbox_info["solution_hint"],
                        test_cases=[SandboxTestCase(**tc) for tc in sandbox_info["test_cases"]]
                    )
                )
            )

        total_skills = len(target_skills) + len(covered_skills)
        match_perc = round((len(covered_skills) / total_skills) * 100, 1) if total_skills > 0 else 0.0

        return RoadmapResponse(
            roadmap_id=str(uuid.uuid4())[:8],
            role_id=role_id,
            role_title=role_title,
            student_name=student_name,
            match_percentage=match_perc,
            total_weeks=len(milestones),
            milestones=milestones
        )
