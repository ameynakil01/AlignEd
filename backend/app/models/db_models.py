import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    target_role = Column(String(100), default="backend-python-engineer", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    roadmaps = relationship("UserRoadmap", back_populates="user", cascade="all, delete-orphan")


class UserRoadmap(Base):
    __tablename__ = "user_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(100), nullable=False)
    role_name = Column(String(150), nullable=False)
    match_score = Column(Float, default=0.0, nullable=False)
    skills_covered = Column(JSON, default=list, nullable=False)
    skills_missing = Column(JSON, default=list, nullable=False)
    total_milestones = Column(Integer, default=0, nullable=False)
    completed_milestones = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="roadmaps")
    milestones = relationship(
        "UserMilestoneProgress",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="UserMilestoneProgress.week_number"
    )


class UserMilestoneProgress(Base):
    __tablename__ = "user_milestone_progress"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("user_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_id = Column(String(100), nullable=False, index=True)
    week_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    target_skill = Column(String(150), nullable=False)
    objective = Column(Text, nullable=True)
    estimated_hours = Column(Integer, default=10, nullable=False)
    status = Column(String(50), default="locked", nullable=False)  # 'locked', 'in_progress', 'verified_green', 'failed_retry_red'
    priority = Column(String(20), default="high", nullable=False)

    # Video Telemetry & Anti-Cheat
    video_id = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)
    video_embed_url = Column(String(500), nullable=True)
    video_duration_seconds = Column(Float, default=0.0, nullable=False)
    watched_intervals = Column(JSON, default=list, nullable=False)  # List of [start, end]
    unique_watch_seconds = Column(Float, default=0.0, nullable=False)
    watch_percentage = Column(Float, default=0.0, nullable=False)
    video_verified = Column(Boolean, default=False, nullable=False)

    # Micro-Quiz PoW
    quiz_unlocked = Column(Boolean, default=False, nullable=False)
    quiz_passed = Column(Boolean, default=False, nullable=False)
    quiz_score = Column(Float, default=0.0, nullable=False)
    quiz_data = Column(JSON, nullable=True)

    # In-Browser Code Sandbox
    sandbox_passed = Column(Boolean, default=False, nullable=False)
    sandbox_challenge = Column(JSON, nullable=True)

    # Final Verification
    proof_of_work_hash = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    roadmap = relationship("UserRoadmap", back_populates="milestones")

