import httpx

def main():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

    # 1. Parse text test
    res_parse = client.post("/api/v1/parse-document", data={"raw_text": "Proficient in Python, PostgreSQL, Docker, Git, and REST APIs."})
    assert res_parse.status_code == 200, f"Parse failed: {res_parse.text}"
    skills = res_parse.json().get("skills", [])
    print("[PASS] 1. Document Parser:", skills)

    # 2. Gap analysis test
    res_gap = client.post("/api/v1/analyze-gap", json={"role_id": "backend-python-engineer", "student_skills": skills})
    assert res_gap.status_code == 200, f"Gap failed: {res_gap.text}"
    gap = res_gap.json()
    print(f"[PASS] 2. Gap Engine: {gap['match_percentage']}% match ({gap['covered_count']}/{gap['total_count']} covered)")

    # 3. Roadmap generation test
    res_rm = client.post("/api/v1/generate-roadmap", json={"role_id": "backend-python-engineer", "student_skills": skills, "student_name": "Alex"})
    assert res_rm.status_code == 200, f"Roadmap failed: {res_rm.text}"
    rm = res_rm.json()
    print(f"[PASS] 3. Roadmap Generator: {rm['total_weeks']} weeks, {len(rm['milestones'])} milestones")

    # 4. Quiz generation test
    res_quiz = client.post("/api/v1/generate-quiz", json={"skill_name": "FastAPI/Flask", "difficulty": "intermediate"})
    assert res_quiz.status_code == 200, f"Quiz gen failed: {res_quiz.text}"
    quiz = res_quiz.json()
    print(f"[PASS] 4. Quiz Generator: {quiz['quiz_id']}, {len(quiz['questions'])} scenario MCQs")

    # 5. Quiz submit test
    answers = {q["id"]: q["correct_index"] for q in quiz["questions"]}
    res_sub = client.post("/api/v1/submit-quiz", json={"quiz_id": quiz["quiz_id"], "answers": answers})
    assert res_sub.status_code == 200, f"Quiz submit failed: {res_sub.text}"
    sub = res_sub.json()
    print(f"[PASS] 5. Quiz Evaluator: Score {sub['score']}/{sub['total_questions']} (Passed: {sub['passed']})")

    # 6. Sandbox test
    res_sb = client.post("/api/v1/evaluate-sandbox", json={"challenge_id": "fastapi-route", "code": "function validate(req) { return req.valid; }", "language": "javascript"})
    assert res_sb.status_code == 200, f"Sandbox failed: {res_sb.text}"
    sb = res_sb.json()
    print(f"[PASS] 6. Sandbox Evaluator: Passed: {sb['passed']}, Score: {sb['score_percentage']}%")

    # 7. Milestone verify test
    res_vf = client.post("/api/v1/verify-milestone", json={"milestone_id": "ms-week-1", "quiz_passed": True, "sandbox_passed": True, "video_engagement_completed": True})
    assert res_vf.status_code == 200, f"Verify failed: {res_vf.text}"
    vf = res_vf.json()
    print(f"[PASS] 7. Milestone Verification: Status: {vf['status']}, Hash: {vf['proof_of_work_hash']}")

    print("\n>>> ALL 7 END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    main()
