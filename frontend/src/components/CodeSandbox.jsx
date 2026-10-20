import React, { useState, useEffect, useRef } from 'react';
import { Play, CheckCircle2, XCircle, RotateCcw, ShieldCheck, Terminal, Eye, Code, HelpCircle } from 'lucide-react';
import { evaluateSandbox } from '../services/api';

export default function CodeSandbox({ challenge, onSandboxComplete, isCompleted, isEngagementComplete }) {
  const [code, setCode] = useState(challenge?.starter_code || '');
  const [isRunning, setIsRunning] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [consoleOutput, setConsoleOutput] = useState([]);
  const [showHint, setShowHint] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');

  const iframeRef = useRef(null);

  useEffect(() => {
    if (challenge?.starter_code) {
      setCode(challenge.starter_code);
      setPreviewHtml(challenge.starter_code);
      setEvaluationResult(null);
      setConsoleOutput([]);
    }
  }, [challenge]);

  const handleCodeChange = (e) => {
    const val = e.target.value;
    setCode(val);
    if (challenge?.language === 'html') {
      setPreviewHtml(val);
    }
  };

  const handleReset = () => {
    setCode(challenge?.starter_code || '');
    setPreviewHtml(challenge?.starter_code || '');
    setEvaluationResult(null);
    setConsoleOutput([]);
  };

  const handleRunVerification = async () => {
    setIsRunning(true);
    setConsoleOutput([]);

    try {
      // 1. Client-side runtime execution simulation & console capture
      const logs = [];
      const originalLog = console.log;
      console.log = (...args) => {
        logs.push(args.map((a) => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' '));
        originalLog(...args);
      };

      try {
        if (challenge?.language === 'javascript' || challenge?.language === 'js') {
          // Safe eval execution test
          const runner = new Function(code + '\n return true;');
          runner();
          logs.push('✓ Syntax execution passed with zero fatal exceptions.');
        } else if (challenge?.language === 'html') {
          setPreviewHtml(code);
          logs.push('✓ DOM tree successfully mounted in live preview iframe.');
        }
      } catch (clientErr) {
        logs.push(`Runtime error: ${clientErr.message}`);
      } finally {
        console.log = originalLog;
      }

      setConsoleOutput(logs);

      // 2. Call backend verification evaluator
      const result = await evaluateSandbox(
        challenge.challenge_id,
        code,
        challenge.language || 'javascript',
        challenge.title
      );

      setEvaluationResult(result);
      if (result.all_tests_passed) {
        onSandboxComplete(true);
      }
    } catch (err) {
      setEvaluationResult({
        passed: false,
        all_tests_passed: false,
        score_percentage: 0,
        results: [
          {
            description: 'Backend criteria evaluator',
            passed: false,
            details: err.message || 'Evaluation request failed',
          },
        ],
        feedback: 'Evaluation error. Check console output.',
      });
    } finally {
      setIsRunning(false);
    }
  };

  if (!isEngagementComplete) {
    return (
      <div className="p-8 text-center rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
          <Code className="w-6 h-6" />
        </div>
        <h4 className="text-base font-semibold text-white">Interactive Sandbox Locked</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Please complete at least 75% of the video/reading material to unlock this hands-on coding verification challenge.
        </p>
      </div>
    );
  }

  if (!challenge) {
    return <div className="p-4 text-xs text-slate-400">No challenge loaded.</div>;
  }

  return (
    <div className="space-y-5">
      {/* Challenge Prompt Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 text-[11px] font-mono uppercase font-bold border border-indigo-800">
                {challenge.language || 'JS'}
              </span>
              <h3 className="text-sm md:text-base font-bold text-white">{challenge.title}</h3>
            </div>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">{challenge.prompt}</p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition flex items-center gap-1.5"
            >
              <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>{showHint ? 'Hide Hint' : 'Hint'}</span>
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xs font-medium transition flex items-center gap-1"
              title="Reset code to starter template"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {showHint && challenge.solution_hint && (
          <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-300 flex items-start gap-2">
            <HelpCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold text-white">Solution Hint: </strong>
              <span>{challenge.solution_hint}</span>
            </div>
          </div>
        )}
      </div>

      {/* Editor & Live Preview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Code Editor */}
        <div className="space-y-2">
          <div className="flex items-center justify-between px-3 py-1.5 rounded-t-xl bg-slate-800 text-xs text-slate-300 font-mono">
            <span className="flex items-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-indigo-400" />
              <span>Solution Editor</span>
            </span>
            <span className="text-[11px] text-slate-400">{code.split('\n').length} lines</span>
          </div>

          <textarea
            value={code}
            onChange={handleCodeChange}
            rows={14}
            spellCheck={false}
            className="w-full p-4 rounded-b-xl bg-slate-950 border border-slate-800 text-indigo-200 font-mono text-xs leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
            placeholder="// Write your solution code here..."
          />
        </div>

        {/* Live Preview & Verification Checklist */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* Live DOM Preview (for HTML challenges) or Console Terminal */}
          {challenge.language === 'html' ? (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-t-xl bg-slate-800 text-xs text-slate-300 font-mono">
                <Eye className="w-3.5 h-3.5 text-emerald-400" />
                <span>Live DOM Render Sandbox</span>
              </div>
              <div className="h-44 w-full rounded-b-xl bg-slate-900 border border-slate-800 p-3 overflow-auto">
                <iframe
                  ref={iframeRef}
                  srcDoc={`<!DOCTYPE html><html><head><script src="https://cdn.tailwindcss.com"></script><style>body{color:#f8fafc;background:transparent;padding:12px;font-family:sans-serif;}</style></head><body>${previewHtml}</body></html>`}
                  title="DOM Preview"
                  className="w-full h-full border-0"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-t-xl bg-slate-800 text-xs text-slate-300 font-mono">
                <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                <span>Console & Execution Telemetry</span>
              </div>
              <div className="h-44 rounded-b-xl bg-slate-950 border border-slate-800 p-3 font-mono text-[11px] overflow-y-auto space-y-1 text-slate-300">
                {consoleOutput.length === 0 ? (
                  <span className="text-slate-600 italic">Click "Run Verification Tests" to evaluate solution...</span>
                ) : (
                  consoleOutput.map((line, idx) => (
                    <div key={idx} className="text-emerald-400 flex items-start gap-1">
                      <span className="text-slate-600">&gt;</span>
                      <span>{line}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Verification Results Panel */}
          {evaluationResult && (
            <div
              className={`p-4 rounded-xl border space-y-2.5 ${
                evaluationResult.all_tests_passed
                  ? 'bg-emerald-950/20 border-emerald-800/80'
                  : 'bg-rose-950/20 border-rose-800/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                  {evaluationResult.all_tests_passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                  {evaluationResult.all_tests_passed
                    ? 'All Unit Tests Passed (PoW Verified)'
                    : 'Unit Tests Pending'}
                </span>
                <span className="text-xs font-mono font-bold text-white">
                  {evaluationResult.score_percentage}% Pass Rate
                </span>
              </div>

              <div className="space-y-1.5">
                {evaluationResult.results?.map((t, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    {t.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="text-slate-200 font-medium">{t.description}: </span>
                      <span className={t.passed ? 'text-slate-400' : 'text-rose-300'}>{t.details}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Run Button */}
          <button
            type="button"
            onClick={handleRunVerification}
            disabled={isRunning || !code.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs tracking-wide shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Running Unit Criteria & DOM Tests...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Verification Tests</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

