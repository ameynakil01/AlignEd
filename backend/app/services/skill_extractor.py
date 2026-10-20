import re
from typing import List, Dict, Set, Tuple
import spacy
from spacy.pipeline import EntityRuler
from ..config import settings


# Canonical taxonomy of technical skills across disciplines
TECH_TAXONOMY = {
    # Languages
    "python": ("Python", "Languages"),
    "dart": ("Dart", "Languages"),
    "javascript": ("JavaScript", "Languages"),
    "js": ("JavaScript", "Languages"),
    "typescript": ("TypeScript", "Languages"),
    "ts": ("TypeScript", "Languages"),
    "html": ("HTML5", "Languages"),
    "html5": ("HTML5", "Languages"),
    "css": ("CSS3", "Languages"),
    "css3": ("CSS3", "Languages"),
    "sql": ("SQL", "Languages"),
    "c++": ("C++", "Languages"),
    "cpp": ("C++", "Languages"),
    "java": ("Java", "Languages"),
    "c#": ("C#", "Languages"),
    "kotlin": ("Kotlin", "Languages"),
    "swift": ("Swift", "Languages"),
    "golang": ("Go", "Languages"),
    "go": ("Go", "Languages"),
    "rust": ("Rust", "Languages"),
    "r": ("R", "Languages"),

    # Mobile & Frontend Frameworks
    "flutter": ("Flutter", "Frameworks"),
    "react": ("React", "Frameworks"),
    "react.js": ("React", "Frameworks"),
    "reactjs": ("React", "Frameworks"),
    "next.js": ("Next.js", "Frameworks"),
    "nextjs": ("Next.js", "Frameworks"),
    "vue": ("Vue.js", "Frameworks"),
    "vue.js": ("Vue.js", "Frameworks"),
    "angular": ("Angular", "Frameworks"),
    "tailwind": ("Tailwind CSS", "Frameworks"),
    "tailwind css": ("Tailwind CSS", "Frameworks"),
    "tailwindcss": ("Tailwind CSS", "Frameworks"),
    "bootstrap": ("Bootstrap", "Frameworks"),
    "state management": ("State Management", "Frameworks"),
    "provider": ("Provider", "Frameworks"),
    "riverpod": ("Riverpod", "Frameworks"),
    "bloc": ("Bloc", "Frameworks"),
    "redux": ("Redux", "Frameworks"),
    "mobx": ("MobX", "Frameworks"),

    # Backend Frameworks
    "fastapi": ("FastAPI", "Frameworks"),
    "fast-api": ("FastAPI", "Frameworks"),
    "flask": ("Flask", "Frameworks"),
    "django": ("Django", "Frameworks"),
    "express": ("Express.js", "Frameworks"),
    "express.js": ("Express.js", "Frameworks"),
    "node.js": ("Node.js", "Frameworks"),
    "nodejs": ("Node.js", "Frameworks"),
    "spring boot": ("Spring Boot", "Frameworks"),

    # Data Science & ML
    "pandas": ("Pandas", "Data Processing"),
    "numpy": ("NumPy", "Data Processing"),
    "scipy": ("SciPy", "Data Processing"),
    "scikit-learn": ("Scikit-Learn", "Data Processing"),
    "sklearn": ("Scikit-Learn", "Data Processing"),
    "pytorch": ("PyTorch", "Data Processing"),
    "tensorflow": ("TensorFlow", "Data Processing"),
    "excel": ("Excel/Pivot Tables", "Data Processing"),
    "pivot tables": ("Excel/Pivot Tables", "Data Processing"),
    "data visualization": ("Data Visualization", "Data Processing"),
    "tableau": ("Tableau", "Data Processing"),
    "power bi": ("Power BI", "Data Processing"),
    "matplotlib": ("Matplotlib", "Data Processing"),
    "seaborn": ("Seaborn", "Data Processing"),
    "statistical analysis": ("Statistical Analysis", "Data Processing"),
    "statistics": ("Statistical Analysis", "Data Processing"),

    # Databases & Caching
    "postgresql": ("PostgreSQL", "Databases"),
    "postgres": ("PostgreSQL", "Databases"),
    "mysql": ("MySQL", "Databases"),
    "sqlite": ("SQLite", "Databases"),
    "mongodb": ("MongoDB", "Databases"),
    "redis": ("Redis", "Databases"),
    "firebase": ("Firebase/Firestore", "Databases"),
    "firestore": ("Firebase/Firestore", "Databases"),
    "supabase": ("Supabase", "Databases"),
    "dynamodb": ("DynamoDB", "Databases"),

    # Cloud, DevOps & Tools
    "docker": ("Docker", "DevOps"),
    "kubernetes": ("Kubernetes", "DevOps"),
    "git": ("Git", "Dev Tools"),
    "github": ("Git", "Dev Tools"),
    "gitlab": ("Git", "Dev Tools"),
    "rest apis": ("REST APIs", "Networking"),
    "rest api": ("REST APIs", "Networking"),
    "restful": ("REST APIs", "Networking"),
    "graphql": ("GraphQL", "Networking"),
    "unit testing": ("Unit Testing", "Quality Assurance"),
    "pytest": ("Unit Testing", "Quality Assurance"),
    "jest": ("Unit Testing", "Quality Assurance"),
    "ci/cd": ("CI/CD", "DevOps"),
    "aws": ("AWS", "Cloud"),
    "gcp": ("GCP", "Cloud"),
    "azure": ("Azure", "Cloud"),
}


class SkillExtractor:
    """Extracts, normalizes, and categorizes technical skills using spaCy and custom entity rulers."""

    _nlp = None

    @classmethod
    def get_nlp(cls):
        """Lazy load or initialize spaCy NLP pipeline with EntityRuler."""
        if cls._nlp is None:
            try:
                cls._nlp = spacy.load(settings.SPACY_MODEL_NAME)
            except Exception:
                # Fallback to blank English model if package not found
                cls._nlp = spacy.blank("en")

            # Configure EntityRuler for tech skills
            if "entity_ruler" not in cls._nlp.pipe_names:
                ruler = cls._nlp.add_pipe("entity_ruler", before="ner" if "ner" in cls._nlp.pipe_names else None)
                patterns = []
                for term in TECH_TAXONOMY.keys():
                    patterns.append({
                        "label": "TECH_SKILL",
                        "pattern": [{"LOWER": word} for word in term.split()]
                    })
                ruler.add_patterns(patterns)
        return cls._nlp

    @classmethod
    def extract_skills(cls, text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Extract normalized unique skills from text using spaCy NER + regex keyword scanning.
        Returns:
            skills_list: Sorted list of canonical skill names
            categorized_skills: Dict mapping category -> list of canonical skill names
        """
        if not text or not text.strip():
            return [], {}

        found_canonical: Set[str] = set()
        categories_map: Dict[str, Set[str]] = {}

        # 1. spaCy pipeline evaluation
        nlp = cls.get_nlp()
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "TECH_SKILL":
                raw_match = ent.text.lower().strip()
                if raw_match in TECH_TAXONOMY:
                    canonical, cat = TECH_TAXONOMY[raw_match]
                    found_canonical.add(canonical)
                    categories_map.setdefault(cat, set()).add(canonical)

        # 2. Comprehensive boundary regex scan to ensure multi-token and punctuation-rich terms are captured
        # (e.g. C++, C#, HTML5/CSS3, Firebase/Firestore, REST APIs, Excel/Pivot Tables)
        lowered_text = text.lower()
        for term, (canonical, cat) in TECH_TAXONOMY.items():
            # Escape regex special characters in term
            escaped_term = re.escape(term)
            # Use boundary or non-alphanumeric lookaround
            pattern = rf'(?<![a-z0-9_]){escaped_term}(?![a-z0-9_])'
            if re.search(pattern, lowered_text):
                found_canonical.add(canonical)
                categories_map.setdefault(cat, set()).add(canonical)

        # 3. Handle slash-combined composite terms
        if re.search(r'\b(html5?\s*/\s*css3?)\b', lowered_text):
            found_canonical.add("HTML5/CSS3")
            categories_map.setdefault("Languages", set()).add("HTML5/CSS3")
        if re.search(r'\b(provider\s*/\s*riverpod)\b', lowered_text) or "provider" in lowered_text or "riverpod" in lowered_text:
            found_canonical.add("State Management (Provider/Riverpod)")
            categories_map.setdefault("Frameworks", set()).add("State Management (Provider/Riverpod)")
        if re.search(r'\b(firebase\s*/\s*firestore)\b', lowered_text):
            found_canonical.add("Firebase/Firestore")
            categories_map.setdefault("Databases", set()).add("Firebase/Firestore")
        if re.search(r'\b(fastapi\s*/\s*flask)\b', lowered_text):
            found_canonical.add("FastAPI/Flask")
            categories_map.setdefault("Frameworks", set()).add("FastAPI/Flask")
        if re.search(r'\b(excel\s*/\s*pivot\s*tables)\b', lowered_text):
            found_canonical.add("Excel/Pivot Tables")
            categories_map.setdefault("Data Processing", set()).add("Excel/Pivot Tables")
        if re.search(r'\b(javascript\s*/\s*typescript)\b', lowered_text):
            found_canonical.add("JavaScript/TypeScript")
            categories_map.setdefault("Languages", set()).add("JavaScript/TypeScript")

        sorted_skills = sorted(list(found_canonical))
        final_categories = {k: sorted(list(v)) for k, v in categories_map.items()}

        return sorted_skills, final_categories

