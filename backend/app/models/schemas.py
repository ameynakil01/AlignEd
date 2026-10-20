from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class RoleBenchmarkSkill(BaseModel):
    name: str
    category: str
    importance: Literal["core", "recommended", "optional"] = "core"
    weight: float = 1.0
    description: Optional[str] = None


class RoleBenchmark(BaseModel):
    id: str
    title: str
    category: str
    description: str
    skills: List[RoleBenchmarkSkill]


class ParseTextRequest(BaseModel):
    text: str
    target_role_id: Optional[str] = None


class ParsedProfile(BaseModel):
    extracted_text: str
    skills: List[str]
    skill_categories: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillMatch(BaseModel):
    skill_name: str
    category: str
    importance: str
    weight: float
    similarity: float
    status: Literal["covered", "missing"]
    priority: Literal["high", "medium", "low"]
    matched_with: Optional[str] = None
    description: Optional[str] = None


class GapAnalysisRequest(BaseModel):
    role_id: str
    student_skills: List[str]


class GapAnalysisResult(BaseModel):
    role_id: str
    role_title: str
    match_percentage: float
    covered_count: int
    missing_count: int
    total_count: int
    covered_skills: List[SkillMatch]
    missing_skills: List[SkillMatch]
    benchmark_skills: List[SkillMatch]
    summary_message: str


class CuratedEmbed(BaseModel):
    type: Literal["youtube", "documentation"]
    title: str
    url: str
    embed_url: str
    min_watch_percentage: int = 75
    min_read_seconds: int = 45
    summary: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str


class QuizQuestionClient(BaseModel):
    id: int
    question: str
    options: List[str]


class MicroQuiz(BaseModel):
    quiz_id: str
    skill: str
    questions: List[QuizQuestion]
    passing_score: int = 2
    time_limit_per_question: int = 60


class SandboxTestCase(BaseModel):
    description: str
    assertion_type: Literal["contains_regex", "dom_element", "output_match", "function_result"]
    expected: str


class SandboxChallenge(BaseModel):
    challenge_id: str
    title: str
    language: Literal["javascript", "html", "python"]
    prompt: str
    starter_code: str
    solution_hint: str
    test_cases: List[SandboxTestCase]


class RoadmapMilestone(BaseModel):
    milestone_id: str
    week: int
    title: str
    target_skill: str
    objective: str
    estimated_hours: int = 10
    status: Literal["locked", "in_progress", "verified_green", "failed_retry_red"] = "locked"
    priority: Literal["high", "medium", "low"] = "high"
    curated_embed: CuratedEmbed
    micro_quiz: MicroQuiz
    sandbox_challenge: SandboxChallenge
    verification_hash: Optional[str] = None


class RoadmapRequest(BaseModel):
    role_id: str
    student_skills: List[str]
    student_name: Optional[str] = "Student"


class RoadmapResponse(BaseModel):
    roadmap_id: str
    role_id: str
    role_title: str
    student_name: str
    match_percentage: float
    total_weeks: int
    milestones: List[RoadmapMilestone]


class QuizGenerateRequest(BaseModel):
    skill_name: str
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    role_title: Optional[str] = None


class QuizSubmission(BaseModel):
    quiz_id: str
    milestone_id: Optional[str] = None
    answers: Dict[int, int]
    time_spent_seconds: int = 0


class QuizResult(BaseModel):
    quiz_id: str
    score: int
    total_questions: int
    percentage: float
    passed: bool
    feedback: str
    answers_review: List[Dict[str, Any]]


class SandboxEvaluationRequest(BaseModel):
    challenge_id: str
    milestone_id: Optional[str] = None
    code: str
    language: str
    skill_name: Optional[str] = None


class SandboxTestCaseResult(BaseModel):
    description: str
    passed: bool
    details: str


class SandboxEvaluationResult(BaseModel):
    challenge_id: str
    passed: bool
    all_tests_passed: bool
    score_percentage: float
    results: List[SandboxTestCaseResult]
    stdout: Optional[str] = ""
    error_message: Optional[str] = None
    feedback: str
