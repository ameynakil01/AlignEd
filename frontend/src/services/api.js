/**
 * AlignED Frontend API Service
 * Connects to FastAPI backend (/api/v1)
 */

const API_BASE = '/api/v1';

export async function fetchRoles() {
  const res = await fetch(`${API_BASE}/roles`);
  if (!res.ok) throw new Error(`Failed to fetch roles: ${res.statusText}`);
  return res.json();
}

export async function fetchRole(roleId) {
  const res = await fetch(`${API_BASE}/roles/${roleId}`);
  if (!res.ok) throw new Error(`Failed to fetch role: ${res.statusText}`);
  return res.json();
}

export async function parseDocument({ file, rawText }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  if (rawText) {
    formData.append('raw_text', rawText);
  }

  const res = await fetch(`${API_BASE}/parse-document`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Document parsing failed');
  }
  return res.json();
}

export async function analyzeGap(roleId, studentSkills) {
  const res = await fetch(`${API_BASE}/analyze-gap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role_id: roleId,
      student_skills: studentSkills,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Gap analysis failed');
  }
  return res.json();
}

export async function generateRoadmap(roleId, studentSkills, studentName = 'Student') {
  const res = await fetch(`${API_BASE}/generate-roadmap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role_id: roleId,
      student_skills: studentSkills,
      student_name: studentName,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Roadmap generation failed');
  }
  return res.json();
}

export async function generateQuiz(skillName, difficulty = 'intermediate', roleTitle = null) {
  const res = await fetch(`${API_BASE}/generate-quiz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      skill_name: skillName,
      difficulty,
      role_title: roleTitle,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Quiz generation failed');
  }
  return res.json();
}

export async function submitQuiz(quizId, answers, timeSpentSeconds = 0) {
  const res = await fetch(`${API_BASE}/submit-quiz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      quiz_id: quizId,
      answers,
      time_spent_seconds: timeSpentSeconds,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Quiz submission failed');
  }
  return res.json();
}

export async function evaluateSandbox(challengeId, code, language, skillName = null) {
  const res = await fetch(`${API_BASE}/evaluate-sandbox`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      challenge_id: challengeId,
      code,
      language,
      skill_name: skillName,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Sandbox evaluation failed');
  }
  return res.json();
}

export async function verifyMilestone(milestoneId, quizPassed, sandboxPassed, videoEngagementCompleted) {
  const res = await fetch(`${API_BASE}/verify-milestone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      milestone_id: milestoneId,
      quiz_passed: quizPassed,
      sandbox_passed: sandboxPassed,
      video_engagement_completed: videoEngagementCompleted,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Milestone verification failed');
  }
  return res.json();
}
