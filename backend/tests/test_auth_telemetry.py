import pytest
from fastapi import HTTPException
from app.main import (
    register_user,
    login_user,
    get_user_dashboard_state,
    video_heartbeat,
    submit_quiz
)
from app.database import Base, SessionLocal, init_db
from app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    VideoHeartbeatRequest,
    QuizSubmission
)
from app.models.db_models import User, UserRoadmap, UserMilestoneProgress
from app.services.telemetry import merge_watch_intervals

# Initialize test tables
init_db()


def test_telemetry_interval_merging():
    """Verify continuous and overlapping intervals merge properly and calculate unique seconds."""
    # Existing: [[0, 10]], New: [8, 20], Duration: 100s
    merged, unique_secs, pct, verified, unlocked = merge_watch_intervals(
        existing_intervals=[[0.0, 10.0]],
        new_interval=[8.0, 20.0],
        total_duration=100.0
    )
    assert len(merged) == 1
    assert merged[0] == [0.0, 20.0]
    assert unique_secs == 20.0
    assert pct == 20.0
    assert not verified
    assert not unlocked

    # Test watch threshold >= 75% unlocks quiz
    merged_full, unique_full, pct_full, verified_full, unlocked_full = merge_watch_intervals(
        existing_intervals=[[0.0, 60.0]],
        new_interval=[60.0, 80.0],
        total_duration=100.0
    )
    assert unique_full == 80.0
    assert pct_full == 80.0
    assert verified_full is True
    assert unlocked_full is True

    # Test chunk clamping (single chunk over 30s is clamped to 30s)
    _, clamped_secs, _, _, _ = merge_watch_intervals(
        existing_intervals=[],
        new_interval=[0.0, 1000.0],
        total_duration=2000.0
    )
    assert clamped_secs == 30.0


def test_auth_registration_and_login_flow():
    """Test user registration, duplicate prevention, and login issuance."""
    db = SessionLocal()
    try:
        # Clean up existing test user if present
        existing = db.query(User).filter(User.email == "test_flow@aligned.test").first()
        if existing:
            db.delete(existing)
            db.commit()

        # 1. Register new user
        reg_req = UserRegisterRequest(
            full_name="Flow Tester",
            email="test_flow@aligned.test",
            password="StrongPassword123!",
            target_role="backend-python-engineer"
        )
        token_resp = register_user(reg_req, db)
        assert token_resp.access_token is not None
        assert token_resp.user.email == "test_flow@aligned.test"

        # 2. Login user
        login_req = UserLoginRequest(
            email="test_flow@aligned.test",
            password="StrongPassword123!"
        )
        login_resp = login_user(login_req, db)
        assert login_resp.access_token is not None

        # 3. Retrieve user dashboard state
        user = db.query(User).filter(User.email == "test_flow@aligned.test").first()
        assert user is not None
        dash_state = get_user_dashboard_state(current_user=user, db=db)
        assert dash_state.user.email == "test_flow@aligned.test"
        assert dash_state.completion_percentage == 0.0

        # Clean up
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_anti_cheat_video_heartbeat_and_quiz_lock():
    """Verify anti-cheat prevents quiz submission before 75% video watch threshold."""
    db = SessionLocal()
    try:
        # Create test user and persistent roadmap milestone
        clean_email = "anticheat@aligned.test"
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        test_user = User(
            full_name="AntiCheat Student",
            email=clean_email,
            hashed_password="hash",
            target_role="backend-python-engineer"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        roadmap = UserRoadmap(
            user_id=test_user.id,
            role_id="backend-python-engineer",
            role_name="Backend Python Engineer",
            match_score=50.0,
            skills_covered=[],
            skills_missing=[],
            total_milestones=1,
            completed_milestones=0
        )
        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)

        milestone = UserMilestoneProgress(
            roadmap_id=roadmap.id,
            milestone_id="ms-docker-pow",
            week_number=1,
            title="Containerization with Docker",
            target_skill="Docker",
            objective="Build microservices",
            estimated_hours=8,
            status="in_progress",
            priority="HIGH",
            video_duration_seconds=100.0,
            watched_intervals=[],
            unique_watch_seconds=0.0,
            watch_percentage=0.0,
            video_verified=False,
            quiz_unlocked=False,
            quiz_passed=False,
            quiz_score=0.0,
            sandbox_passed=False
        )
        db.add(milestone)
        db.commit()
        db.refresh(milestone)

        # 1. Attempting to submit quiz before watching video should raise HTTP 403 Forbidden
        sub = QuizSubmission(
            quiz_id="quiz-docker",
            milestone_id="ms-docker-pow",
            answers={1: 1, 2: 1, 3: 1},
            time_spent_seconds=60
        )
        with pytest.raises(HTTPException) as exc_info:
            submit_quiz(submission=sub, current_user=test_user, db=db)
        assert exc_info.value.status_code == 403

        # 2. Dispatch partial video heartbeat (< 75%)
        hb1 = VideoHeartbeatRequest(
            milestone_id="ms-docker-pow",
            interval=[0.0, 30.0],
            total_duration=100.0
        )
        resp1 = video_heartbeat(req=hb1, current_user=test_user, db=db)
        assert resp1.watch_percentage == 30.0
        assert resp1.quiz_unlocked is False

        # 3. Dispatch second heartbeat satisfying >= 75% threshold
        hb2 = VideoHeartbeatRequest(
            milestone_id="ms-docker-pow",
            interval=[30.0, 60.0],
            total_duration=100.0
        )
        video_heartbeat(req=hb2, current_user=test_user, db=db)
        hb3 = VideoHeartbeatRequest(
            milestone_id="ms-docker-pow",
            interval=[60.0, 80.0],
            total_duration=100.0
        )
        resp3 = video_heartbeat(req=hb3, current_user=test_user, db=db)
        assert resp3.watch_percentage == 80.0
        assert resp3.quiz_unlocked is True
        assert resp3.video_verified is True

        # 4. Now quiz submission succeeds without 403 error
        sub_allowed = QuizSubmission(
            quiz_id="quiz-docker",
            milestone_id="ms-docker-pow",
            answers={1: 1, 2: 1, 3: 1},
            time_spent_seconds=60
        )
        res_allowed = submit_quiz(submission=sub_allowed, current_user=test_user, db=db)
        assert res_allowed.passed is True
        assert res_allowed.percentage == 100.0

        # Clean up
        db.delete(test_user)
        db.commit()
    finally:
        db.close()

