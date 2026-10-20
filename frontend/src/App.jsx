import React, { useState, useEffect, useRef } from 'react';
import confetti from 'canvas-confetti';
import {
  Compass,
  Upload,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  X,
  Play,
  HelpCircle,
  Code2,
  Video,
  Award,
  BookOpen,
  ArrowRight,
  Layers,
  ChevronRight,
  RefreshCw
} from 'lucide-react';

import {
  fetchRoles,
  analyzeGap,
  generateRoadmap,
  verifyMilestone,
} from './services/api';

import UploadModal from './components/UploadModal';
import GapDashboard from './components/GapDashboard';
import RoadmapTimeline from './components/RoadmapTimeline';
import EmbeddedViewer from './components/EmbeddedViewer';
import MicroQuiz from './components/MicroQuiz';
import CodeSandbox from './components/CodeSandbox';

export default function App() {
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('backend-python-engineer');
  const [studentName, setStudentName] = useState('Alex Rivers');

  const [gapData, setGapData] = useState(null);
  const [roadmap, setRoadmap] = useState(null);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isGeneratingRoadmap, setIsGeneratingRoadmap] = useState(false);
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  // Active Milestone Drawer/Modal State
  const [activeMilestone, setActiveMilestone] = useState(null);
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState('embed'); // 'embed' | 'quiz' | 'sandbox'

  // Per-milestone verification tracking state: { [milestone_id]: { embed: boolean, quiz: boolean, sandbox: boolean } }
  const [milestoneProgress, setMilestoneProgress] = useState({});

  const workspaceDialogRef = useRef(null);

  // Initialize roles and seed with sample student analysis
  useEffect(() => {
    async function loadData() {
      try {
        const fetchedRoles = await fetchRoles();
        setRoles(fetchedRoles);

        if (fetchedRoles.length > 0) {
          const defaultRoleId = 'backend-python-engineer';
          setSelectedRole(defaultRoleId);

          // Seed default sample skills for immediate rich demonstration
          const defaultSkills = ['Python', 'SQL', 'Git', 'HTML5/CSS3'];
          const initialGap = await analyzeGap(defaultRoleId, defaultSkills);
          setGapData(initialGap);

          const initialRoadmap = await generateRoadmap(defaultRoleId, defaultSkills, 'Alex Rivers');
          setRoadmap(initialRoadmap);
        }
      } catch (err) {
        console.error('Initial data load error:', err);
      } finally {
        setIsLoadingInitial(false);
      }
    }
    loadData();
  }, []);

  // Modern Web Guidance: Native <dialog> lifecycle and light dismiss for workspace modal
  useEffect(() => {
    const dialog = workspaceDialogRef.current;
    if (!dialog) return;

    if (activeMilestone) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }

    const handleBackdropClick = (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const isInside =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (!isInside) {
        setActiveMilestone(null);
      }
    };

    dialog.addEventListener('click', handleBackdropClick);
    return () => dialog.removeEventListener('click', handleBackdropClick);
  }, [activeMilestone]);

  // Handle new analysis from UploadModal
  const handleAnalysisComplete = async ({ roleId, studentName: name, extractedSkills }) => {
    setStudentName(name);
    setSelectedRole(roleId);

    try {
      const gap = await analyzeGap(roleId, extractedSkills);
      setGapData(gap);

      setIsGeneratingRoadmap(true);
      const rm = await generateRoadmap(roleId, extractedSkills, name);
      setRoadmap(rm);
    } catch (err) {
      console.error('Gap analysis error:', err);
    } finally {
      setIsGeneratingRoadmap(false);
    }
  };

  // Trigger manual roadmap regeneration
  const handleRegenerateRoadmap = async () => {
    if (!gapData) return;
    setIsGeneratingRoadmap(true);
    try {
      const coveredNames = gapData.covered_skills.map((s) => s.skill_name);
      const rm = await generateRoadmap(selectedRole, coveredNames, studentName);
      setRoadmap(rm);
    } catch (err) {
      console.error('Roadmap regeneration error:', err);
    } finally {
      setIsGeneratingRoadmap(false);
    }
  };

  // Switch role directly from header dropdown
  const handleRoleChange = async (newRoleId) => {
    setSelectedRole(newRoleId);
    if (!gapData) return;
    try {
      const coveredNames = gapData.covered_skills.map((s) => s.skill_name);
      const gap = await analyzeGap(newRoleId, coveredNames);
      setGapData(gap);

      setIsGeneratingRoadmap(true);
      const rm = await generateRoadmap(newRoleId, coveredNames, studentName);
      setRoadmap(rm);
    } catch (err) {
      console.error('Role switch error:', err);
    } finally {
      setIsGeneratingRoadmap(false);
    }
  };

  // Milestone Progress Gate Handlers
  const currentMilestoneId = activeMilestone?.milestone_id;
  const currentProgress = milestoneProgress[currentMilestoneId] || {
    embed: activeMilestone?.status === 'verified_green',
    quiz: activeMilestone?.status === 'verified_green',
    sandbox: activeMilestone?.status === 'verified_green',
  };

  const handleEngagementComplete = () => {
    if (!currentMilestoneId) return;
    setMilestoneProgress((prev) => ({
      ...prev,
      [currentMilestoneId]: {
        ...(prev[currentMilestoneId] || {}),
        embed: true,
      },
    }));
  };

  const handleQuizComplete = (passed) => {
    if (!currentMilestoneId) return;
    setMilestoneProgress((prev) => ({
      ...prev,
      [currentMilestoneId]: {
        ...(prev[currentMilestoneId] || {}),
        quiz: passed,
      },
    }));
  };

  const handleSandboxComplete = (passed) => {
    if (!currentMilestoneId) return;
    setMilestoneProgress((prev) => ({
      ...prev,
      [currentMilestoneId]: {
        ...(prev[currentMilestoneId] || {}),
        sandbox: passed,
      },
    }));
  };

  const isAllMilestoneCriteriaMet =
    currentProgress.embed && currentProgress.quiz && currentProgress.sandbox;

  // Claim final Proof-of-Work Verification
  const handleClaimVerification = async () => {
    if (!activeMilestone || !isAllMilestoneCriteriaMet) return;

    try {
      await verifyMilestone(
        activeMilestone.milestone_id,
        currentProgress.quiz,
        currentProgress.sandbox,
        currentProgress.embed
      );

      // Confetti celebration
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
      });

      // Update roadmap milestones state: mark current verified and unlock next
      setRoadmap((prev) => {
        if (!prev) return prev;
        const updated = prev.milestones.map((m, idx) => {
          if (m.milestone_id === activeMilestone.milestone_id) {
            return { ...m, status: 'verified_green' };
          }
          // Unlock next milestone if locked
          const currentIndex = prev.milestones.findIndex(
            (item) => item.milestone_id === activeMilestone.milestone_id
          );
          if (idx === currentIndex + 1 && m.status === 'locked') {
            return { ...m, status: 'in_progress' };
          }
          return m;
        });
        return { ...prev, milestones: updated };
      });

      // Close modal
      setActiveMilestone(null);
    } catch (err) {
      console.error('Milestone verification error:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 w-full bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <Compass className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-lg font-black text-white tracking-tight">AlignED</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 font-mono font-bold border border-indigo-500/30">
                  AI v2.5
                </span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wide">
                Curated Career Pathways & PoW Verification
              </p>
            </div>
          </div>

          {/* Role Selector & Upload Button */}
          <div className="flex items-center gap-3">
            <select
              value={selectedRole}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="hidden sm:block px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs font-medium text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  Target: {r.title}
                </option>
              ))}
            </select>

            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition flex items-center gap-2 cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              <span>Map Syllabus / Resume</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {isLoadingInitial ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-medium text-slate-400">Loading AlignED Career Intelligence Engine...</p>
          </div>
        ) : (
          <>
            {/* Module 1 & 2: Gap Analysis Dashboard */}
            <GapDashboard
              gapData={gapData}
              roleData={roles.find((r) => r.id === selectedRole)}
              onGenerateRoadmap={handleRegenerateRoadmap}
              isGeneratingRoadmap={isGeneratingRoadmap}
              hasRoadmap={Boolean(roadmap)}
            />

            {/* Module 3 & 4: Interactive Roadmap Timeline */}
            {roadmap && (
              <RoadmapTimeline
                roadmap={roadmap}
                activeMilestoneId={activeMilestone?.milestone_id}
                onSelectMilestone={(m) => {
                  setActiveMilestone(m);
                  setActiveWorkspaceTab('embed');
                }}
              />
            )}
          </>
        )}
      </main>

      {/* Upload & Syllabus Parser Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        roles={roles}
        selectedRole={selectedRole}
        setSelectedRole={setSelectedRole}
        onAnalysisComplete={handleAnalysisComplete}
      />

      {/* Milestone Learning & Verification Workspace Modal */}
      <dialog
        ref={workspaceDialogRef}
        closedby="any"
        aria-labelledby="workspace-modal-title"
        className="p-0 rounded-3xl bg-slate-900 text-slate-100 border border-slate-700/80 shadow-2xl max-w-4xl w-full mx-auto backdrop:backdrop-blur-md"
      >
        {activeMilestone && (
          <div className="flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-1 rounded-lg bg-indigo-950 text-indigo-300 font-mono text-xs font-bold border border-indigo-800">
                  WEEK {activeMilestone.week}
                </span>
                <div>
                  <h3 id="workspace-modal-title" className="text-base font-bold text-white">
                    {activeMilestone.title}
                  </h3>
                  <span className="text-xs text-slate-400">
                    Target Skill: <strong className="text-indigo-400">{activeMilestone.target_skill}</strong>
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveMilestone(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 3 Proof-of-Work Verification Gate Tabs */}
            <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 pt-2">
              <button
                type="button"
                onClick={() => setActiveWorkspaceTab('embed')}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
                  activeWorkspaceTab === 'embed'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <Video className="w-3.5 h-3.5" />
                <span>1. Curated Embed</span>
                {currentProgress.embed && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              </button>

              <button
                type="button"
                onClick={() => setActiveWorkspaceTab('quiz')}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
                  activeWorkspaceTab === 'quiz'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>2. Scenario Micro-Quiz</span>
                {currentProgress.quiz && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              </button>

              <button
                type="button"
                onClick={() => setActiveWorkspaceTab('sandbox')}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition cursor-pointer ${
                  activeWorkspaceTab === 'sandbox'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>3. Live Code Sandbox</span>
                {currentProgress.sandbox && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              </button>
            </div>

            {/* Active Workspace Content */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {activeWorkspaceTab === 'embed' && (
                <EmbeddedViewer
                  curatedEmbed={activeMilestone.curated_embed}
                  onEngagementComplete={handleEngagementComplete}
                  isCompleted={currentProgress.embed}
                />
              )}

              {activeWorkspaceTab === 'quiz' && (
                <MicroQuiz
                  quiz={activeMilestone.micro_quiz}
                  onQuizComplete={handleQuizComplete}
                  isPassed={currentProgress.quiz}
                  isEngagementComplete={currentProgress.embed}
                />
              )}

              {activeWorkspaceTab === 'sandbox' && (
                <CodeSandbox
                  challenge={activeMilestone.sandbox_challenge}
                  onSandboxComplete={handleSandboxComplete}
                  isCompleted={currentProgress.sandbox}
                  isEngagementComplete={currentProgress.embed}
                />
              )}
            </div>

            {/* PoW Verification Checklist Footer */}
            <div className="p-4 px-6 border-t border-slate-800 bg-slate-900/90 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4 text-xs font-medium">
                <span
                  className={`flex items-center gap-1.5 ${
                    currentProgress.embed ? 'text-emerald-400' : 'text-slate-500'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>≥75% Material Engagement</span>
                </span>

                <span
                  className={`flex items-center gap-1.5 ${
                    currentProgress.quiz ? 'text-emerald-400' : 'text-slate-500'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Scenario MCQ (≥2/3)</span>
                </span>

                <span
                  className={`flex items-center gap-1.5 ${
                    currentProgress.sandbox ? 'text-emerald-400' : 'text-slate-500'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Sandbox Unit Tests</span>
                </span>
              </div>

              <button
                type="button"
                onClick={handleClaimVerification}
                disabled={!isAllMilestoneCriteriaMet}
                className={`px-5 py-2.5 rounded-xl text-xs font-bold tracking-wide uppercase transition flex items-center gap-2 ${
                  isAllMilestoneCriteriaMet
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 cursor-pointer animate-bounce'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Claim Verified PoW & Unlock Next</span>
              </button>
            </div>
          </div>
        )}
      </dialog>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 bg-slate-900/40 text-center text-xs text-slate-500">
        <p>AlignED — AI-Driven Curated Career Pathways & Curriculum Gap Mapper</p>
        <p className="text-[11px] text-slate-600 mt-1">
          Powered by Google Gemini 2.5 Flash, spaCy NER, and all-MiniLM-L6-v2 local vector embeddings.
        </p>
      </footer>
    </div>
  );
}
