/**
 * AlignED Frontend API Service
 * Connects to FastAPI backend (/api/v1) with JWT authentication and video anti-cheat telemetry
 */

const API_BASE = '/api/v1';

export function getAuthToken() {
  return localStorage.getItem('aligned_token') || null;
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('aligned_token', token);
  } else {
    localStorage.removeItem('aligned_token');
  }
}

export function getAuthHeaders() {
  const token = getAuthToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ==========================================
// Authentication & User State
// ==========================================

export async function registerUser({ full_name, email, password, target_role }) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ full_name, email, password, target_role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Registration failed');
  }
  const data = await res.json();
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Login failed');
  }
  const data = await res.json();
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function getDashboardState() {
  const token = getAuthToken();
  if (!token) return null;

  const res = await fetch(`${API_BASE}/user/dashboard-state`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    if (res.status === 401) {
      setAuthToken(null);
      return null;
    }
    throw new Error(`Failed to load dashboard state: ${res.statusText}`);
  }
  return res.json();
}

// ==========================================
// Roles & Curriculum
// ==========================================

export async function fetchRoles() {
  const res = await fetch(`${API_BASE}/roles`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch roles: ${res.statusText}`);
  return res.json();
}

export async function fetchRole(roleId) {
  const res = await fetch(`${API_BASE}/roles/${roleId}`, { headers: getAuthHeaders() });
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

  const token = getAuthToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/parse-document`, {
    method: 'POST',
    headers,
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
    headers: getAuthHeaders(),
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
    headers: getAuthHeaders(),
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

// ==========================================
// Anti-Cheat Telemetry & Assessments
// ==========================================

export async function sendVideoHeartbeat(milestoneId, interval, totalDuration) {
  const res = await fetch(`${API_BASE}/milestone/video-heartbeat`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      milestone_id: milestoneId,
      interval: interval, // [start, end]
      total_duration: totalDuration,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to sync video heartbeat');
  }
  return res.json();
}

export async function generateQuiz(skillName, difficulty = 'intermediate', roleTitle = null) {
  const res = await fetch(`${API_BASE}/generate-quiz`, {
    method: 'POST',
    headers: getAuthHeaders(),
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

export async function submitQuiz(quizId, answers, timeSpentSeconds = 0, questions = null, milestoneId = null) {
  const res = await fetch(`${API_BASE}/submit-quiz`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      quiz_id: quizId,
      milestone_id: milestoneId,
      answers,
      time_spent_seconds: timeSpentSeconds,
      questions,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Quiz submission failed');
  }
  return res.json();
}

export async function evaluateSandbox(challengeId, code, language, skillName = null, milestoneId = null) {
  const res = await fetch(`${API_BASE}/evaluate-sandbox`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      challenge_id: challengeId,
      milestone_id: milestoneId,
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
    headers: getAuthHeaders(),
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
