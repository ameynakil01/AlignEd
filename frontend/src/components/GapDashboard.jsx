import React from 'react';
import { CheckCircle, AlertTriangle, ArrowRight, Target, Award, Sparkles, BookOpen } from 'lucide-react';

export default function GapDashboard({ gapData, roleData, onGenerateRoadmap, isGeneratingRoadmap, hasRoadmap }) {
  if (!gapData) {
    return (
      <div className="p-8 text-center rounded-2xl bg-slate-900 border border-slate-800 text-slate-400">
        <Target className="w-12 h-12 mx-auto mb-3 text-slate-500 animate-pulse" />
        <p className="text-base font-medium text-slate-300">No Gap Analysis Loaded</p>
        <p className="text-xs text-slate-500 mt-1">Upload a syllabus or pick a sample preset to view your curriculum alignment.</p>
      </div>
    );
  }

  const {
    role_title,
    match_percentage,
    covered_count,
    missing_count,
    total_count,
    covered_skills,
    missing_skills,
    summary_message,
  } = gapData;

  // Gauge color selection
  let gaugeColor = 'text-rose-500';
  let badgeText = 'Needs Bridge Pathway';
  let badgeBg = 'bg-rose-500/10 text-rose-400 border-rose-500/30';

  if (match_percentage >= 75) {
    gaugeColor = 'text-emerald-500';
    badgeText = 'Industry Ready Alignment';
    badgeBg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (match_percentage >= 50) {
    gaugeColor = 'text-amber-500';
    badgeText = 'Strong Core Foundation';
    badgeBg = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }

  // Circular gauge SVG calculation
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (match_percentage / 100) * circumference;

  return (
    <div className="space-y-6">
      {/* Top Banner Card with Visual Match Score Gauge */}
      <div className="p-6 md:p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/40 border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-xl text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold tracking-wide uppercase ${badgeBg}">
              <Award className="w-3.5 h-3.5" />
              <span>{badgeText}</span>
            </div>

            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {role_title} Curriculum Match
            </h2>

            <p className="text-sm text-slate-300 leading-relaxed">
              {summary_message}
            </p>

            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs font-medium text-slate-400 pt-1">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                {covered_count} Skills Mastered
              </span>
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                {missing_count} Skills Missing
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                {total_count} Benchmark Targets
              </span>
            </div>
          </div>

          {/* Radial Match Score Gauge */}
          <div className="flex flex-col items-center">
            <div className="relative w-36 h-36 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 128 128">
                <circle
                  cx="64"
                  cy="64"
                  r={radius}
                  className="text-slate-800"
                  strokeWidth="10"
                  stroke="currentColor"
                  fill="transparent"
                />
                <circle
                  cx="64"
                  cy="64"
                  r={radius}
                  className={`${gaugeColor} transition-all duration-1000 ease-out`}
                  strokeWidth="10"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-extrabold text-white tracking-tight">
                  {Math.round(match_percentage)}%
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  Role Match
                </span>
              </div>
            </div>

            <button
              onClick={onGenerateRoadmap}
              disabled={isGeneratingRoadmap}
              className="mt-4 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            >
              {isGeneratingRoadmap ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Prompting Gemini 2.5 Flash...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>{hasRoadmap ? 'Regenerate PoW Roadmap' : 'Generate Curated PoW Roadmap'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Skills Matrix Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Covered Skills Column (Green) */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <CheckCircle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Skills Acquired</h3>
                <p className="text-xs text-slate-400">Verified by vector cosine similarity (S ≥ 0.70)</p>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 text-xs font-semibold">
              {covered_skills.length} Covered
            </span>
          </div>

          {covered_skills.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">
              No matching competencies detected yet. Follow the weekly milestones below.
            </p>
          ) : (
            <div className="space-y-2.5">
              {covered_skills.map((skill, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-between hover:border-emerald-500/40 transition"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{skill.skill_name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono">
                        {skill.category}
                      </span>
                    </div>
                    {skill.matched_with && (
                      <p className="text-[11px] text-slate-400">
                        Mapped to student competency: <span className="text-emerald-400 font-medium">"{skill.matched_with}"</span>
                      </p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="inline-block px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60 text-[11px] font-mono font-semibold">
                      {(skill.similarity * 100).toFixed(0)}% Match
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Skills Column (Red with Priority Badges) */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Critical Missing Skills</h3>
                <p className="text-xs text-slate-400">Target gaps scheduled in Proof-of-Work milestones</p>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-rose-950/60 text-rose-300 border border-rose-800/40 text-xs font-semibold">
              {missing_skills.length} Missing
            </span>
          </div>

          {missing_skills.length === 0 ? (
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-center">
              <p className="text-sm font-medium text-emerald-300">All Core Role Skills Satisfied!</p>
              <p className="text-xs text-slate-400 mt-1">Review advanced mastery milestones to prepare for senior interviews.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {missing_skills.map((skill, idx) => {
                let priorityColor = 'bg-rose-950/60 text-rose-300 border-rose-800/50';
                if (skill.priority === 'medium') {
                  priorityColor = 'bg-amber-950/60 text-amber-300 border-amber-800/50';
                } else if (skill.priority === 'low') {
                  priorityColor = 'bg-blue-950/60 text-blue-300 border-blue-800/50';
                }

                return (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-between hover:border-rose-500/40 transition"
                  >
                    <div className="space-y-0.5 max-w-[70%]">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">{skill.skill_name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono">
                          {skill.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">
                        {skill.description || 'Target competency for production-grade engineering.'}
                      </p>
                    </div>

                    <div className="text-right flex-shrink-0 flex flex-col items-end gap-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wide border ${priorityColor}`}>
                        {skill.priority} Priority
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Weight: {skill.weight.toFixed(2)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

