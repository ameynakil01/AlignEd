import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import settings
from ..models.schemas import RoleBenchmark, SkillMatch, GapAnalysisResult

logger = logging.getLogger(__name__)


class GapEngine:
    """Computes semantic curriculum and skill gaps using vector embeddings and cosine similarity."""

    _model: Optional[SentenceTransformer] = None
    _roles_cache: Optional[Dict[str, RoleBenchmark]] = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Lazy loads sentence-transformers all-MiniLM-L6-v2 model on CPU."""
        if cls._model is None:
            logger.info(f"Loading SentenceTransformer embedding model: {settings.EMBEDDING_MODEL_NAME}")
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")
        return cls._model

    @classmethod
    def load_benchmarks(cls) -> Dict[str, RoleBenchmark]:
        """Loads and caches role benchmark specifications from role_benchmarks.json."""
        if cls._roles_cache is None:
            if not settings.BENCHMARKS_FILE.exists():
                raise FileNotFoundError(f"Role benchmarks file not found: {settings.BENCHMARKS_FILE}")
            
            with open(settings.BENCHMARKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            roles_map = {}
            for role_data in data.get("roles", []):
                role_obj = RoleBenchmark(**role_data)
                roles_map[role_obj.id] = role_obj
            cls._roles_cache = roles_map
        return cls._roles_cache

    @classmethod
    def get_role_by_id(cls, role_id: str) -> Optional[RoleBenchmark]:
        """Fetch role benchmark definition by its unique identifier."""
        roles = cls.load_benchmarks()
        return roles.get(role_id)

    @classmethod
    def get_all_roles(cls) -> List[RoleBenchmark]:
        """Return all available industry role benchmark profiles."""
        roles = cls.load_benchmarks()
        return list(roles.values())

    @classmethod
    def compute_cosine_similarity(cls, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two 1D vector embeddings."""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    @classmethod
    def analyze_gap(
        cls,
        role_id: str,
        student_skills: List[str],
        threshold: Optional[float] = None
    ) -> GapAnalysisResult:
        """
        Calculates match score and delineates covered vs missing skills.
        
        Algorithm:
        1. For each role benchmark skill, check for direct exact/substring normalized match (similarity = 1.0).
        2. If not exact, encode student skills and benchmark skill into dense vectors.
        3. Compute cosine similarity against all student skills and select the maximum score S.
        4. If S >= threshold (default 0.70), mark Covered; else Missing.
        5. Compute match_percentage = (len(covered) / total) * 100.
        """
        effective_threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        role = cls.get_role_by_id(role_id)
        if not role:
            raise ValueError(f"Role ID '{role_id}' not found in benchmark repository.")

        benchmark_skills = role.skills
        if not benchmark_skills:
            return GapAnalysisResult(
                role_id=role.id,
                role_title=role.title,
                match_percentage=100.0,
                covered_count=0,
                missing_count=0,
                total_count=0,
                covered_skills=[],
                missing_skills=[],
                benchmark_skills=[],
                summary_message="No benchmark skills configured for this role."
            )

        # Normalize student skills for fast exact lookup
        cleaned_student_skills = [s.strip() for s in student_skills if s and s.strip()]
        student_skills_lower_map = {s.lower(): s for s in cleaned_student_skills}

        # Precompute embeddings for student skills if any exist
        student_embeddings = None
        model = None
        if cleaned_student_skills:
            model = cls.get_model()
            student_embeddings = model.encode(cleaned_student_skills, normalize_embeddings=True)

        covered_matches: List[SkillMatch] = []
        missing_matches: List[SkillMatch] = []
        all_matches: List[SkillMatch] = []

        for b_skill in benchmark_skills:
            b_name = b_skill.name
            b_lower = b_name.lower()
            
            best_sim = 0.0
            matched_with: Optional[str] = None

            # 1. Exact or composite substring match check
            if b_lower in student_skills_lower_map:
                best_sim = 1.0
                matched_with = student_skills_lower_map[b_lower]
            else:
                # Check slash variants (e.g., "FastAPI/Flask" matching "FastAPI" or "Flask")
                subparts = [p.strip().lower() for p in b_name.replace("(", "/").replace(")", "").split("/") if p.strip()]
                for part in subparts:
                    if part in student_skills_lower_map:
                        best_sim = 1.0
                        matched_with = student_skills_lower_map[part]
                        break

            # 2. Vector embedding similarity if no exact match found
            if best_sim < 1.0 and student_embeddings is not None and len(student_embeddings) > 0 and model is not None:
                b_emb = model.encode([b_name], normalize_embeddings=True)[0]
                similarities = np.dot(student_embeddings, b_emb)
                max_idx = int(np.argmax(similarities))
                sim_score = float(similarities[max_idx])
                if sim_score > best_sim:
                    best_sim = max(0.0, min(1.0, sim_score))
                    matched_with = cleaned_student_skills[max_idx]

            # Priority categorization
            if b_skill.importance == "core" or b_skill.weight >= 0.95:
                priority = "high"
            elif b_skill.weight >= 0.85:
                priority = "medium"
            else:
                priority = "low"

            status = "covered" if best_sim >= effective_threshold else "missing"

            match_obj = SkillMatch(
                skill_name=b_name,
                category=b_skill.category,
                importance=b_skill.importance,
                weight=b_skill.weight,
                similarity=round(best_sim, 3),
                status=status,
                priority=priority,
                matched_with=matched_with if best_sim >= 0.4 else None,
                description=b_skill.description
            )

            all_matches.append(match_obj)
            if status == "covered":
                covered_matches.append(match_obj)
            else:
                missing_matches.append(match_obj)

        total_skills = len(benchmark_skills)
        covered_count = len(covered_matches)
        missing_count = len(missing_matches)
        match_percentage = round((covered_count / total_skills) * 100, 1) if total_skills > 0 else 0.0

        if match_percentage >= 80:
            summary = f"Outstanding alignment! You possess {covered_count} of {total_skills} critical skills ({match_percentage}%). Focus on the few remaining gaps to become job-ready."
        elif match_percentage >= 50:
            summary = f"Strong foundational profile with {match_percentage}% role match. Targeted practice on {missing_count} missing skills will bridge the curriculum gap."
        elif match_percentage >= 20:
            summary = f"Emerging alignment ({match_percentage}%). Recommended high-priority modules will rapidly accelerate your proficiency towards the {role.title} benchmark."
        else:
            summary = f"Early stage alignment ({match_percentage}%). Follow our structured weekly roadmap to systematically master the {role.title} stack from first principles."

        return GapAnalysisResult(
            role_id=role.id,
            role_title=role.title,
            match_percentage=match_percentage,
            covered_count=covered_count,
            missing_count=missing_count,
            total_count=total_skills,
            covered_skills=covered_matches,
            missing_skills=missing_matches,
            benchmark_skills=all_matches,
            summary_message=summary
        )
