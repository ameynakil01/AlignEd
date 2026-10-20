import React, { useState, useEffect, useRef } from 'react';
import { Play, CheckCircle2, ShieldCheck, Clock, ExternalLink, BookOpen, AlertCircle } from 'lucide-react';

export default function EmbeddedViewer({ curatedEmbed, onEngagementComplete, isCompleted }) {
  const [watchProgress, setWatchProgress] = useState(isCompleted ? 100 : 0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [simulatedSeconds, setSimulatedSeconds] = useState(0);
  const [hasUnlocked, setHasUnlocked] = useState(isCompleted);
  const [activeTab, setActiveTab] = useState('video'); // 'video' | 'doc'
  const [scrollDepth, setScrollDepth] = useState(0);

  const docContainerRef = useRef(null);
  const targetThreshold = curatedEmbed?.min_watch_percentage || 75;

  // Active watch telemetry timer
  useEffect(() => {
    let interval = null;
    if (isPlaying && !hasUnlocked) {
      interval = setInterval(() => {
        setSimulatedSeconds((prev) => {
          const next = prev + 1;
          // Scale progress (each 2 seconds = ~5% progress in prototype demonstration)
          const newProgress = Math.min(100, Math.round((next / 30) * 100));
          setWatchProgress(newProgress);

          if (newProgress >= targetThreshold) {
            setHasUnlocked(true);
            onEngagementComplete();
          }
          return next;
        });
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, hasUnlocked, targetThreshold, onEngagementComplete]);

  // Track doc scroll depth
  const handleScroll = () => {
    if (!docContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = docContainerRef.current;
    const depth = Math.min(100, Math.round((scrollTop / (scrollHeight - clientHeight)) * 100));
    setScrollDepth(depth);
    if (depth >= 85 && !hasUnlocked) {
      setHasUnlocked(true);
      setWatchProgress(100);
      onEngagementComplete();
    }
  };

  const handleFastTrackSim = () => {
    setWatchProgress(100);
    setHasUnlocked(true);
    onEngagementComplete();
  };

  if (!curatedEmbed) {
    return <div className="p-4 text-xs text-slate-400">No curated material found.</div>;
  }

  return (
    <div className="space-y-4">
      {/* Viewer Tab Switcher & Status Pill */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('video')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'video'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Video Masterclass
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('doc')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'doc'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Curated Documentation Reader
          </button>
        </div>

        {/* Verification Status Pill */}
        <div className="flex items-center gap-3">
          {hasUnlocked ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/80 text-xs font-semibold shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Engagement Verified ({watchProgress}%)
            </span>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono">
                Watch Telemetry: <strong className="text-amber-400">{watchProgress}%</strong> / {targetThreshold}%
              </span>
              <button
                type="button"
                onClick={handleFastTrackSim}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-indigo-400 border border-slate-700 transition"
                title="Fast-track watch simulation for instant evaluation demo"
              >
                Fast-Track (Simulate ≥75%)
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Video Player Embed Mode */}
      {activeTab === 'video' && (
        <div className="space-y-3">
          <div className="relative aspect-video w-full rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-2xl">
            <iframe
              src={`${curatedEmbed.embed_url}?autoplay=0&enablejsapi=1&origin=${window.location.origin}`}
              title={curatedEmbed.title}
              className="w-full h-full border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>

          {/* Interactive Play & Watch Telemetry Controls */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 ${
                  isPlaying
                    ? 'bg-amber-600 hover:bg-amber-500 text-white'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30'
                }`}
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isPlaying ? 'Pause Watch Tracker' : 'Start Active Watch Tracker'}</span>
              </button>

              <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                <Clock className="w-3.5 h-3.5" />
                Session: {simulatedSeconds}s
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full sm:w-48 space-y-1">
              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>Required: {targetThreshold}%</span>
                <span>{watchProgress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    hasUnlocked ? 'bg-emerald-500' : 'bg-indigo-500'
                  }`}
                  style={{ width: `${watchProgress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Curated Documentation Reader Mode */}
      {activeTab === 'doc' && (
        <div
          ref={docContainerRef}
          onScroll={handleScroll}
          className="h-80 overflow-y-auto p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 text-xs leading-relaxed text-slate-300 font-sans"
        >
          <div className="border-b border-slate-800 pb-3">
            <h4 className="text-sm font-semibold text-white">{curatedEmbed.title} — Technical Specification</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">Scroll through documentation to verify reading engagement</p>
          </div>

          <div className="space-y-3">
            <h5 className="font-semibold text-indigo-400 text-xs">1. Core Architecture & Conceptual Foundations</h5>
            <p>
              In modern enterprise software engineering, robust competence requires mastering both programmatic paradigms and the underlying runtime lifecycle.
              State transitions, memory footprint constraints, and network I/O serialization must be planned to avoid regressions.
            </p>

            <h5 className="font-semibold text-indigo-400 text-xs">2. Critical Failure Modes & Triage Protocol</h5>
            <p>
              Production services must decouple telemetry capture from user-facing transaction paths.
              When evaluating high throughput concurrent requests, avoid blocking thread synchronization. Implement circuit breakers and graceful fallbacks.
            </p>

            <h5 className="font-semibold text-indigo-400 text-xs">3. Proof-of-Work Verification Criteria</h5>
            <p>
              Before unlocking the subsequent milestone, you must achieve at least 2 out of 3 correct answers on the scenario-based micro-quiz and pass all automated unit tests in the hands-on code sandbox.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-slate-400">
            <span>Scroll Depth: {scrollDepth}% (Requires 85%)</span>
            {scrollDepth >= 85 && (
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Reading Verified
              </span>
            )}
          </div>
        </div>
      )}

      {/* Summary Note */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
        <BookOpen className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Curriculum Objective: </span>
          <span>{curatedEmbed.summary}</span>
        </div>
      </div>
    </div>
  );
}
