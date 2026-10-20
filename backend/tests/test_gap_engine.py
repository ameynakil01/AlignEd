import pytest
from app.services.gap_engine import GapEngine
from app.services.skill_extractor import SkillExtractor


def test_benchmarks_loading():
    """Verify pre-seeded benchmarks load correctly and contain required roles."""
    roles = GapEngine.get_all_roles()
    assert len(roles) >= 4

    role_ids = [r.id for r in roles]
    assert "junior-flutter-developer" in role_ids
    assert "backend-python-engineer" in role_ids
    assert "data-analyst" in role_ids
    assert "frontend-web-developer" in role_ids


def test_gap_analysis_full_match():
    """Student possessing all required skills should get 100% match."""
    role = GapEngine.get_role_by_id("backend-python-engineer")
    assert role is not None

    all_role_skills = [s.name for s in role.skills]
    result = GapEngine.analyze_gap("backend-python-engineer", all_role_skills)

    assert result.match_percentage == 100.0
    assert result.covered_count == len(role.skills)
    assert result.missing_count == 0
    assert len(result.missing_skills) == 0


def test_gap_analysis_zero_match():
    """Student with zero relevant skills should get 0% match with all missing."""
    role = GapEngine.get_role_by_id("junior-flutter-developer")
    assert role is not None

    result = GapEngine.analyze_gap("junior-flutter-developer", ["Unrelated Cooking", "Woodworking"])
    assert result.match_percentage == 0.0
    assert result.missing_count == len(role.skills)
    assert result.covered_count == 0


def test_gap_analysis_partial_match():
    """Partial skill set should correctly partition covered vs missing skills."""
    skills = ["Python", "FastAPI", "Git"]
    result = GapEngine.analyze_gap("backend-python-engineer", skills)

    assert result.covered_count >= 3
    assert result.missing_count > 0
    assert 0.0 < result.match_percentage < 100.0

    covered_names = [s.skill_name for s in result.covered_skills]
    assert "Python" in covered_names
    assert "Git" in covered_names

    # Priority check
    for missing in result.missing_skills:
        assert missing.priority in ["high", "medium", "low"]


def test_skill_extractor_ner():
    """Test spaCy and regex tech skill extraction from syllabus text."""
    sample_syllabus = """
    Department of Computer Science
    Course: Advanced Web Application Engineering
    Prerequisites: Proficiency in Python and JavaScript.
    Course Modules:
    1. Developing RESTful microservices with FastAPI and PostgreSQL database.
    2. Containerization and deployment using Docker and Git version control.
    3. Automated unit testing using pytest and redis caching.
    """
    skills, categories = SkillExtractor.extract_skills(sample_syllabus)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills
    assert "Git" in skills
    assert "Unit Testing" in skills
    assert "Redis" in skills

