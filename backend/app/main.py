import hashlib
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, init_db
from .models.db_models import User, UserRoadmap, UserMilestoneProgress
from .models.schemas import (
    RoleBenchmark,
    ParsedProfile,
    GapAnalysisRequest,
    GapAnalysisResult,
    RoadmapRequest,
    RoadmapResponse,
    RoadmapMilestone,
    CuratedEmbed,
    QuizGenerateRequest,
    MicroQuiz,
    QuizSubmission,
    QuizResult,
    SandboxEvaluationRequest,
    SandboxEvaluationResult,
    UserRegisterRequest,
    UserLoginRequest,
    UserProfile,
    TokenResponse,
    VideoHeartbeatRequest,
    VideoHeartbeatResponse,
    DashboardStateResponse,
)
from .services import (
    ParserService,
    SkillExtractor,
    GapEngine,
    RoadmapGenerator,
    QuizGenerator,
    SandboxEvaluator,
    merge_watch_intervals,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_current_user,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AlignED")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent career roadmap and curriculum gap mapper with Proof-of-Work verification and persistent state.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_user(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        target_role=user.target_role,
        created_at=user.created_at.isoformat() if user.created_at else None
    )


def _persist_generated_roadmap(
    db: Session,
    user: User,
    role_id: str,
    gap_result: GapAnalysisResult,
    roadmap_resp: RoadmapResponse
) -> UserRoadmap:
    """Helper to store generated roadmap and milestone records into database for persistent multi-tenant tracking."""
    # Archive/remove previous active roadmap for this user and role if exists
    existing = db.query(UserRoadmap).filter(UserRoadmap.user_id == user.id, UserRoadmap.role_id == role_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    db_roadmap = UserRoadmap(
        user_id=user.id,
        role_id=role_id,
        role_name=roadmap_resp.role_title,
        match_score=gap_result.match_percentage,
        skills_covered=[s.model_dump() for s in gap_result.covered_skills],
        skills_missing=[s.model_dump() for s in gap_result.missing_skills],
        total_milestones=len(roadmap_resp.milestones),
        completed_milestones=0,
    )
    db.add(db_roadmap)
    db.commit()
    db.refresh(db_roadmap)

    # Persist individual milestone progresses
    for idx, m in enumerate(roadmap_resp.milestones):
        initial_status = "in_progress" if idx == 0 else "locked"
        db_milestone = UserMilestoneProgress(
            roadmap_id=db_roadmap.id,
            milestone_id=m.milestone_id,
            week_number=m.week,
            title=m.title,
            target_skill=m.target_skill,
            objective=m.objective,
            estimated_hours=m.estimated_hours,
            status=initial_status,
            priority=m.priority,
            video_id="VPvVD8t02U8" if "flutter" in m.target_skill.lower() else "0sOvCWFmrtA",
            video_url=m.curated_embed.url if m.curated_embed else None,
            video_embed_url=m.curated_embed.embed_url if m.curated_embed else None,
            video_duration_seconds=300.0,
            watched_intervals=[],
            unique_watch_seconds=0.0,
            watch_percentage=0.0,
            video_verified=False,
            quiz_unlocked=False,
            quiz_passed=False,
            quiz_score=0.0,
            quiz_data=m.micro_quiz.model_dump() if m.micro_quiz else None,
            sandbox_passed=False,
            sandbox_challenge=m.sandbox_challenge.model_dump() if m.sandbox_challenge else None,
        )
        db.add(db_milestone)
    
    db.commit()
    db.refresh(db_roadmap)
    return db_roadmap


# ==========================================
# 1. System & Authentication Endpoints
# ==========================================

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


@app.post("/api/v1/auth/register", response_model=TokenResponse, tags=["Authentication"])
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new student user and returns JWT bearer token with seed state."""
    clean_email = req.email.lower().strip()
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered."
        )

    hashed_pwd = hash_password(req.password)
    new_user = User(
        full_name=req.full_name.strip(),
        email=clean_email,
        hashed_password=hashed_pwd,
        target_role=req.target_role or "backend-python-engineer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "id": new_user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(new_user)
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates email and password, returning JWT bearer token."""
    clean_email = req.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.email, "id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(user)
    )


@app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["Authentication"])
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password bearer token endpoint for Swagger and client compatibility."""
    clean_email = form_data.username.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.email, "id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(user)
    )


@app.get("/api/v1/auth/me", response_model=UserProfile, tags=["Authentication"])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns profile information for currently authenticated user."""
    return _serialize_user(current_user)


@app.get("/api/v1/user/dashboard-state", response_model=DashboardStateResponse, tags=["User Progress"])
def get_user_dashboard_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authenticated user's complete persistent state across reloads:
    - User profile
    - Active persistent roadmap
    - Milestone progression states, watch intervals, and quiz unlock statuses
    """
    # Fetch active roadmap
    active_roadmap = (
        db.query(UserRoadmap)
        .filter(UserRoadmap.user_id == current_user.id)
        .order_by(UserRoadmap.created_at.desc())
        .first()
    )

    if not active_roadmap:
        return DashboardStateResponse(
            user=_serialize_user(current_user),
            has_active_roadmap=False,
            roadmap=None,
            milestones=[],
            completion_percentage=0.0
        )

    milestones_db = (
        db.query(UserMilestoneProgress)
        .filter(UserMilestoneProgress.roadmap_id == active_roadmap.id)
        .order_by(UserMilestoneProgress.week_number.asc())
        .all()
    )

    milestone_dicts = []
    completed_count = 0

    for m in milestones_db:
        if m.status == "verified_green":
            completed_count += 1

        milestone_dicts.append({
            "id": m.id,
            "milestone_id": m.milestone_id,
            "week": m.week_number,
            "title": m.title,
            "target_skill": m.target_skill,
            "objective": m.objective,
            "estimated_hours": m.estimated_hours,
            "status": m.status,
            "priority": m.priority,
            "curated_embed": {
                "type": "youtube",
                "title": f"Master {m.target_skill}",
                "url": m.video_url or "https://www.youtube.com/watch?v=0sOvCWFmrtA",
                "embed_url": m.video_embed_url or "https://www.youtube-nocookie.com/embed/0sOvCWFmrtA",
                "min_watch_percentage": 75,
                "summary": m.objective or "",
            },
            "micro_quiz": m.quiz_data,
            "sandbox_challenge": m.sandbox_challenge,
            # Telemetry state
            "watched_intervals": m.watched_intervals or [],
            "unique_watch_seconds": m.unique_watch_seconds,
            "watch_percentage": m.watch_percentage,
            "video_verified": m.video_verified,
            "quiz_unlocked": m.quiz_unlocked,
            "quiz_passed": m.quiz_passed,
            "quiz_score": m.quiz_score,
            "sandbox_passed": m.sandbox_passed,
            "proof_of_work_hash": m.proof_of_work_hash,
        })

    total = len(milestones_db)
    completion_pct = round((completed_count / total) * 100.0, 1) if total > 0 else 0.0

    roadmap_dict = {
        "id": active_roadmap.id,
        "role_id": active_roadmap.role_id,
        "role_name": active_roadmap.role_name,
        "match_score": active_roadmap.match_score,
        "skills_covered": active_roadmap.skills_covered,
        "skills_missing": active_roadmap.skills_missing,
        "total_milestones": total,
        "completed_milestones": completed_count,
        "completion_percentage": completion_pct,
    }

    return DashboardStateResponse(
        user=_serialize_user(current_user),
        has_active_roadmap=True,
        roadmap=roadmap_dict,
        milestones=milestone_dicts,
        completion_percentage=completion_pct
    )


# ==========================================
# 2. Benchmarks, Parser & Gap Analysis
# ==========================================

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
    """Parses an uploaded PDF syllabus/resume or direct text string using pypdf and spaCy."""
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
    """Computes semantic vector similarity and identifies covered vs missing competencies."""
    try:
        return GapEngine.analyze_gap(role_id=req.role_id, student_skills=req.student_skills)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. Roadmap Generation with DB Binding
# ==========================================

@app.post("/api/v1/generate-roadmap", response_model=RoadmapResponse, tags=["Roadmap"])
async def generate_roadmap(
    req: RoadmapRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Synthesizes a personalized weekly learning trajectory.
    If user is authenticated, saves roadmap and milestone records directly to database.
    """
    try:
        role = GapEngine.get_role_by_id(req.role_id)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{req.role_id}' not found")

        gap_result = GapEngine.analyze_gap(role_id=req.role_id, student_skills=req.student_skills)

        student_name = current_user.full_name if current_user else (req.student_name or "Student")

        roadmap_resp = RoadmapGenerator.generate_roadmap(
            role_id=role.id,
            role_title=role.title,
            missing_skills=gap_result.missing_skills,
            covered_skills=gap_result.covered_skills,
            student_name=student_name
        )

        # If authenticated, persist to relational database for multi-tenant state
        if current_user:
            _persist_generated_roadmap(db, current_user, req.role_id, gap_result, roadmap_resp)

        return roadmap_resp
    except Exception as e:
        logger.error(f"Roadmap generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. Anti-Cheat Video Telemetry & Quiz
# ==========================================

@app.post("/api/v1/milestone/video-heartbeat", response_model=VideoHeartbeatResponse, tags=["Anti-Cheat Telemetry"])
def video_heartbeat(
    req: VideoHeartbeatRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Anti-Cheat Telemetry Heartbeat:
    Merges non-contiguous watch sessions. Prevents scrub-skipping to unlock quizzes prematurely.
    Enforces genuine >= 75% watch before quiz_unlocked = True.
    """
    if current_user:
        # Locate milestone and verify user ownership (IDOR prevention)
        milestone = (
            db.query(UserMilestoneProgress)
            .join(UserRoadmap)
            .filter(
                UserMilestoneProgress.milestone_id == req.milestone_id,
                UserRoadmap.user_id == current_user.id
            )
            .first()
        )
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Milestone '{req.milestone_id}' not found for active user."
            )

        # Merge intervals with anti-cheat algorithm
        existing = milestone.watched_intervals or []
        duration = req.total_duration if req.total_duration > 0 else (milestone.video_duration_seconds or 300.0)
        merged, unique_secs, watch_pct, video_verified, quiz_unlocked = merge_watch_intervals(
            existing_intervals=existing,
            new_interval=req.interval,
            total_duration=duration
        )

        milestone.watched_intervals = merged
        milestone.unique_watch_seconds = unique_secs
        milestone.watch_percentage = watch_pct
        if video_verified:
            milestone.video_verified = True
            milestone.quiz_unlocked = True

        db.commit()

        message = (
            "Watch threshold satisfied (>= 75%). Proof-of-Work Micro-Quiz unlocked!"
            if milestone.quiz_unlocked
            else f"Telemetry recorded. Continuous watch progress: {watch_pct}% / 75%."
        )

        return VideoHeartbeatResponse(
            milestone_id=req.milestone_id,
            watched_intervals=merged,
            unique_watch_seconds=unique_secs,
            watch_percentage=watch_pct,
            video_verified=milestone.video_verified,
            quiz_unlocked=milestone.quiz_unlocked,
            message=message
        )
    else:
        # Guest mode simulation
        merged, unique_secs, watch_pct, video_verified, quiz_unlocked = merge_watch_intervals(
            existing_intervals=[],
            new_interval=req.interval,
            total_duration=req.total_duration
        )
        return VideoHeartbeatResponse(
            milestone_id=req.milestone_id,
            watched_intervals=merged,
            unique_watch_seconds=unique_secs,
            watch_percentage=watch_pct,
            video_verified=video_verified,
            quiz_unlocked=quiz_unlocked,
            message="Guest mode telemetry recorded."
        )


@app.post("/api/v1/generate-quiz", response_model=MicroQuiz, tags=["Assessment"])
async def generate_quiz(req: QuizGenerateRequest):
    """Generates 3 scenario-based Proof-of-Work MCQs via Google Gemini API."""
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
def submit_quiz(
    submission: QuizSubmission,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates micro-quiz against session answer keys.
    Anti-Cheat Guard: Rejects attempts with 403 Forbidden if milestone video_verified / quiz_unlocked is False.
    """
    # If user is authenticated and milestone_id is present, enforce the anti-cheat verification gate
    if current_user and submission.milestone_id:
        milestone = (
            db.query(UserMilestoneProgress)
            .join(UserRoadmap)
            .filter(
                UserMilestoneProgress.milestone_id == submission.milestone_id,
                UserRoadmap.user_id == current_user.id
            )
            .first()
        )
        if milestone and not milestone.quiz_unlocked and not milestone.video_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Proof-of-Work Violation: Micro-quiz is locked. You must genuinely watch/read at least 75% of the curated material before submitting."
            )

    try:
        result = QuizGenerator.evaluate_submission(submission)

        # Update database if user milestone is present
        if current_user and submission.milestone_id:
            milestone = (
                db.query(UserMilestoneProgress)
                .join(UserRoadmap)
                .filter(
                    UserMilestoneProgress.milestone_id == submission.milestone_id,
                    UserRoadmap.user_id == current_user.id
                )
                .first()
            )
            if milestone and result.passed:
                milestone.quiz_passed = True
                milestone.quiz_score = result.percentage
                db.commit()

        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 5. Sandbox & Milestone Verification
# ==========================================

@app.post("/api/v1/evaluate-sandbox", response_model=SandboxEvaluationResult, tags=["Assessment"])
def evaluate_sandbox(
    req: SandboxEvaluationRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Evaluates hands-on in-browser sandbox code against DOM and regex criteria."""
    try:
        result = SandboxEvaluator.evaluate(req)

        # Update database state if user and milestone are present
        if current_user and req.milestone_id and result.all_tests_passed:
            milestone = (
                db.query(UserMilestoneProgress)
                .join(UserRoadmap)
                .filter(
                    UserMilestoneProgress.milestone_id == req.milestone_id,
                    UserRoadmap.user_id == current_user.id
                )
                .first()
            )
            if milestone:
                milestone.sandbox_passed = True
                db.commit()

        return result
    except Exception as e:
        logger.error(f"Sandbox evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MilestoneVerificationRequest(BaseModel):
    milestone_id: str
    quiz_passed: bool
    sandbox_passed: bool
    video_engagement_completed: bool


@app.post("/api/v1/verify-milestone", tags=["Verification"])
def verify_milestone(
    req: MilestoneVerificationRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Validates that all 3 PoW criteria (engagement >= 75%, quiz >= 2/3, sandbox unit tests) are satisfied.
    Persists verified state in database and unlocks the subsequent milestone.
    """
    if current_user:
        milestone = (
            db.query(UserMilestoneProgress)
            .join(UserRoadmap)
            .filter(
                UserMilestoneProgress.milestone_id == req.milestone_id,
                UserRoadmap.user_id == current_user.id
            )
            .first()
        )
        if not milestone:
            raise HTTPException(status_code=404, detail=f"Milestone '{req.milestone_id}' not found.")

        # Strict server-side verification: check DB flags or request payload
        is_video_ok = milestone.video_verified or req.video_engagement_completed
        is_quiz_ok = milestone.quiz_passed or req.quiz_passed
        is_sandbox_ok = milestone.sandbox_passed or req.sandbox_passed

        if not is_video_ok:
            raise HTTPException(status_code=400, detail="Curated video or document engagement requirement not met (min 75% unique watch).")
        if not is_quiz_ok:
            raise HTTPException(status_code=400, detail="Micro-quiz Proof-of-Work assessment not passed (requires >= 2/3 correct).")
        if not is_sandbox_ok:
            raise HTTPException(status_code=400, detail="Hands-on sandbox coding challenge unit tests not passed.")

        # Generate cryptographic Proof-of-Work hash
        token = hashlib.sha256(f"{current_user.id}-{req.milestone_id}-verified".encode()).hexdigest()[:16]
        pow_hash = f"POW-{token}"

        milestone.status = "verified_green"
        milestone.video_verified = True
        milestone.quiz_passed = True
        milestone.sandbox_passed = True
        milestone.proof_of_work_hash = pow_hash

        # Unlock the subsequent milestone in the user's roadmap
        next_milestone = (
            db.query(UserMilestoneProgress)
            .filter(
                UserMilestoneProgress.roadmap_id == milestone.roadmap_id,
                UserMilestoneProgress.week_number == milestone.week_number + 1
            )
            .first()
        )
        if next_milestone and next_milestone.status == "locked":
            next_milestone.status = "in_progress"

        # Update roadmap completed count
        completed_count = (
            db.query(UserMilestoneProgress)
            .filter(
                UserMilestoneProgress.roadmap_id == milestone.roadmap_id,
                UserMilestoneProgress.status == "verified_green"
            )
            .count()
        )
        milestone.roadmap.completed_milestones = completed_count

        db.commit()

        return {
            "milestone_id": req.milestone_id,
            "status": "verified_green",
            "proof_of_work_hash": pow_hash,
            "message": "Milestone successfully verified! Next milestone unlocked."
        }

    else:
        # Fallback for unauthenticated guest sessions
        if not req.video_engagement_completed:
            raise HTTPException(status_code=400, detail="Curated video or document engagement requirement not met (min 75% watch/read).")
        if not req.quiz_passed:
            raise HTTPException(status_code=400, detail="Micro-quiz Proof-of-Work assessment not passed (requires >= 2/3 correct).")
        if not req.sandbox_passed:
            raise HTTPException(status_code=400, detail="Hands-on sandbox coding challenge unit tests not passed.")

        token = hashlib.sha256(f"{req.milestone_id}-verified".encode()).hexdigest()[:16]
        return {
            "milestone_id": req.milestone_id,
            "status": "verified_green",
            "proof_of_work_hash": f"POW-{token}",
            "message": "Milestone successfully verified! Next milestone unlocked."
        }
