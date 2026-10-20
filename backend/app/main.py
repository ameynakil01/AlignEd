import logging
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .models.schemas import (
    RoleBenchmark,
    ParsedProfile,
    GapAnalysisRequest,
    GapAnalysisResult,
    RoadmapRequest,
    RoadmapResponse,
    QuizGenerateRequest,
    MicroQuiz,
    QuizSubmission,
    QuizResult,
    SandboxEvaluationRequest,
    SandboxEvaluationResult,
)
from .services import (
    ParserService,
    SkillExtractor,
    GapEngine,
    RoadmapGenerator,
    QuizGenerator,
    SandboxEvaluator,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AlignED")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent career roadmap and curriculum gap mapper with Proof-of-Work verification."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """System health check and loaded model diagnostics."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }


@app.get("/api/v1/roles", response_model=List[RoleBenchmark], tags=["Benchmarks"])
async def list_roles():
    """Retrieve pre-seeded industry job benchmark profiles."""
    try:
        return GapEngine.get_all_roles()
    except Exception as e:
        logger.error(f"Error fetching roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/roles/{role_id}", response_model=RoleBenchmark, tags=["Benchmarks"])
async def get_role(role_id: str):
    """Retrieve a specific benchmark role by ID."""
    role = GapEngine.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
    return role


@app.post("/api/v1/parse-document", response_model=ParsedProfile, tags=["Parser"])
async def parse_document(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Parses an uploaded PDF syllabus/resume or direct text string.
    Extracts, normalizes, and categorizes technical competencies.
    """
    try:
        extracted_text = ""
        filename = None
        if file is not None:
            filename = file.filename
            content = await file.read()
            extracted_text = ParserService.parse_input(file_bytes=content, filename=filename)
        elif raw_text:
            extracted_text = ParserService.parse_input(raw_text=raw_text)
        else:
            raise HTTPException(status_code=400, detail="Either a file upload or raw_text is required.")

        skills, categories = SkillExtractor.extract_skills(extracted_text)

        return ParsedProfile(
            extracted_text=extracted_text,
            skills=skills,
            skill_categories=categories,
            metadata={
                "filename": filename,
                "character_count": len(extracted_text),
                "total_skills_detected": len(skills)
            }
        )
    except Exception as e:
        logger.error(f"Document parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")


@app.post("/api/v1/analyze-gap", response_model=GapAnalysisResult, tags=["Gap Engine"])
async def analyze_curriculum_gap(req: GapAnalysisRequest):
    """
    Computes semantic vector similarity between student skills and role benchmarks.
    Classifies skills into Covered (>= 0.70) vs Missing (< 0.70) and calculates match percentage.
    """
    try:
        return GapEngine.analyze_gap(role_id=req.role_id, student_skills=req.student_skills)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generate-roadmap", response_model=RoadmapResponse, tags=["Roadmap"])
async def generate_roadmap(req: RoadmapRequest):
    """
    Synthesizes a personalized week-by-week learning trajectory using Google Gemini API.
    Embeds video/docs, scenario micro-quizzes, and interactive sandbox challenges.
    """
    try:
        role = GapEngine.get_role_by_id(req.role_id)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{req.role_id}' not found")

        gap_result = GapEngine.analyze_gap(role_id=req.role_id, student_skills=req.student_skills)

        roadmap = RoadmapGenerator.generate_roadmap(
            role_id=role.id,
            role_title=role.title,
            missing_skills=gap_result.missing_skills,
            covered_skills=gap_result.covered_skills,
            student_name=req.student_name or "Student"
        )
        return roadmap
    except Exception as e:
        logger.error(f"Roadmap generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generate-quiz", response_model=MicroQuiz, tags=["Assessment"])
async def generate_quiz(req: QuizGenerateRequest):
    """
    Generates 3 scenario-based Proof-of-Work MCQs via Google Gemini API.
    """
    try:
        return QuizGenerator.generate_quiz(
            skill_name=req.skill_name,
            difficulty=req.difficulty,
            role_title=req.role_title
        )
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/submit-quiz", response_model=QuizResult, tags=["Assessment"])
async def submit_quiz(submission: QuizSubmission):
    """
    Evaluates submitted micro-quiz against session answer keys.
    """
    try:
        return QuizGenerator.evaluate_submission(submission)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/evaluate-sandbox", response_model=SandboxEvaluationResult, tags=["Assessment"])
async def evaluate_sandbox(req: SandboxEvaluationRequest):
    """
    Evaluates hands-on in-browser sandbox code against DOM, regex, and syntactic criteria.
    """
    try:
        return SandboxEvaluator.evaluate(req)
    except Exception as e:
        logger.error(f"Sandbox evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MilestoneVerificationRequest(BaseModel):
    milestone_id: str
    quiz_passed: bool
    sandbox_passed: bool
    video_engagement_completed: bool


@app.post("/api/v1/verify-milestone", tags=["Verification"])
async def verify_milestone(req: MilestoneVerificationRequest):
    """
    Validates that all 3 PoW criteria (engagement, quiz >= 2/3, sandbox unit tests) are satisfied.
    Returns status: verified_green.
    """
    if not req.video_engagement_completed:
        raise HTTPException(status_code=400, detail="Curated video or document engagement requirement not met (min 75% watch/read).")
    if not req.quiz_passed:
        raise HTTPException(status_code=400, detail="Micro-quiz Proof-of-Work assessment not passed (requires >= 2/3 correct).")
    if not req.sandbox_passed:
        raise HTTPException(status_code=400, detail="Hands-on sandbox coding challenge unit tests not passed.")

    import hashlib
    token = hashlib.sha256(f"{req.milestone_id}-verified".encode()).hexdigest()[:16]

    return {
        "milestone_id": req.milestone_id,
        "status": "verified_green",
        "proof_of_work_hash": f"POW-{token}",
        "message": "Milestone successfully verified! Next milestone unlocked."
    }

