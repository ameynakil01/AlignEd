import React from 'react';
import {
  Lock,
  PlayCircle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  Video,
  Code2,
  HelpCircle,
  Sparkles,
} from 'lucide-react';

export default function RoadmapTimeline({ roadmap, onSelectMilestone, activeMilestoneId }) {
  if (!roadmap || !roadmap.milestones || roadmap.milestones.length === 0) {
    return null;
  }

  const { milestones, role_title, total_weeks } = roadmap;

  const verifiedCount = milestones.filter((m) => m.status === 'verified_green').length;
  const progressPercent = Math.round((verifiedCount / total_weeks) * 100);

  return (
    <div className="space-y-6 pt-4">
      {/* Header & Milestone Progress Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              Personalized {role_title} Trajectory
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Proof-of-Work (PoW) verification required per milestone before unlocking subsequent weeks
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-xs font-semibold text-slate-300">
              {verifiedCount} of {total_weeks} Milestones Verified
            </span>
            <div className="w-36 h-2 rounded-full bg-slate-800 mt-1.5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-indigo-500 transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-indigo-400">
            {progressPercent}%
          </div>
        </div>
      </div>

      {/* Stepper / Timeline Nodes */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:content-[''] before:absolute before:left-3 sm:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-800">
        {milestones.map((m, idx) => {
          const isSelected = activeMilestoneId === m.milestone_id;
          const isVerified = m.status === 'verified_green';
          const isInProgress = m.status === 'in_progress';
          const isFailed = m.status === 'failed_retry_red';
          const isLocked = m.status === 'locked';

          // Node status icon & styling
          let nodeIcon = <Lock className="w-4 h-4 text-slate-500" />;
          let nodeRing = 'bg-slate-900 border-slate-700 text-slate-500';
          let cardBorder = 'border-slate-800 hover:border-slate-700 bg-slate-900/60';
          let statusBadge = (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[11px] font-medium border border-slate-700">
              <Lock className="w-3 h-3" /> Locked
            </span>
          );

          if (isVerified) {
            nodeIcon = <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
            nodeRing = 'bg-emerald-950 border-emerald-500 text-emerald-400 ring-4 ring-emerald-950/40';
            cardBorder = 'border-emerald-900/60 bg-emerald-950/10 hover:border-emerald-600/60';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-950/70 text-emerald-400 text-[11px] font-semibold border border-emerald-700/60">
                <ShieldCheck className="w-3.5 h-3.5" /> PoW Verified
              </span>
            );
          } else if (isInProgress) {
            nodeIcon = <PlayCircle className="w-4 h-4 text-indigo-400 animate-spin-slow" />;
            nodeRing = 'bg-indigo-950 border-indigo-500 text-indigo-400 ring-4 ring-indigo-950/60 shadow-lg shadow-indigo-600/30';
            cardBorder = 'border-indigo-600/60 bg-slate-900 glow-active';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 text-[11px] font-semibold border border-indigo-700/60">
                <Sparkles className="w-3 h-3 text-amber-400" /> In Progress
              </span>
            );
          } else if (isFailed) {
            nodeIcon = <XCircle className="w-4 h-4 text-rose-400" />;
            nodeRing = 'bg-rose-950 border-rose-500 text-rose-400 ring-4 ring-rose-950/40';
            cardBorder = 'border-rose-900/60 bg-rose-950/10 hover:border-rose-600/60';
            statusBadge = (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-950/70 text-rose-400 text-[11px] font-semibold border border-rose-700/60">
                <XCircle className="w-3.5 h-3.5" /> Assessment Failed (Retry Available)
              </span>
            );
          }

          return (
            <div key={m.milestone_id} className="relative group">
              {/* Stepper node circle */}
              <div
                className={`absolute -left-6 sm:-left-8 top-5 -translate-x-1/2 w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all ${nodeRing}`}
              >
                {nodeIcon}
              </div>

              {/* Milestone Card */}
              <div
                className={`p-6 rounded-2xl border transition-all duration-200 cursor-pointer ${cardBorder} ${
                  isSelected ? 'ring-2 ring-indigo-500 shadow-xl' : ''
                }`}
                onClick={() => onSelectMilestone(m)}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 text-xs font-mono font-bold">
                        WEEK {m.week}
                      </span>
                      {statusBadge}
                      <span className="px-2 py-0.5 rounded-md bg-indigo-950/50 text-indigo-300 text-xs font-semibold border border-indigo-800/40">
                        {m.target_skill}
                      </span>
                      <span className="flex items-center gap-1 text-slate-400 text-xs">
                        <Clock className="w-3 h-3" />
                        {m.estimated_hours}h est.
                      </span>
                    </div>

                    <h4 className="text-base font-semibold text-white group-hover:text-indigo-300 transition">
                      {m.title}
                    </h4>

                    <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
                      {m.objective}
                    </p>

                    {/* Integrated PoW Verification Pillars Pill */}
                    <div className="flex flex-wrap items-center gap-3 pt-2 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800/80 border border-slate-700/60">
                        <Video className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Curated Embed (≥75% Watch)</span>
                      </span>
                      <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800/80 border border-slate-700/60">
                        <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                        <span>Scenario MCQ PoW (≥2/3 Pass)</span>
                      </span>
                      <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800/80 border border-slate-700/60">
                        <Code2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Live Code Sandbox Verification</span>
                      </span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="flex-shrink-0 flex items-center md:self-center">
                    <button
                      type="button"
                      disabled={isLocked}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectMilestone(m);
                      }}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                        isLocked
                          ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                          : isVerified
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800 hover:bg-emerald-900 cursor-pointer'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 cursor-pointer'
                      }`}
                    >
                      <span>
                        {isVerified
                          ? 'Review Verified PoW'
                          : isLocked
                          ? 'Complete Prior Milestone'
                          : 'Open Verification Workspace'}
                      </span>
                      {!isLocked && <ArrowRight className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
