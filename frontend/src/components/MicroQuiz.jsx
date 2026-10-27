import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, XCircle, AlertCircle, RefreshCw, ShieldCheck, ArrowRight, Award } from 'lucide-react';
import { submitQuiz } from '../services/api';

export default function MicroQuiz({ quiz, onQuizComplete, isPassed, isEngagementComplete, milestoneId }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(60);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const questions = quiz?.questions || [];
  const currentQ = questions[currentIdx];
  const totalQuestions = questions.length;

  // Countdown timer for active question
  useEffect(() => {
    if (quizResult || !isEngagementComplete) return;

    setTimeLeft(60);
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          // Timeout for current question: advance or auto-submit
          handleNextQuestion();
          return 60;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentIdx, quizResult, isEngagementComplete]);

  const handleSelectOption = (optIndex) => {
    if (quizResult) return;
    setAnswers((prev) => ({
      ...prev,
      [currentQ.id]: optIndex,
    }));
  };

  const handleNextQuestion = () => {
    if (currentIdx < totalQuestions - 1) {
      setCurrentIdx((prev) => prev + 1);
    } else {
      handleSubmitQuiz();
    }
  };

  const handleSubmitQuiz = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const result = await submitQuiz(quiz.quiz_id, answers, 60, quiz.questions, milestoneId);
      setQuizResult(result);
      if (result.passed) {
        onQuizComplete(true);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Quiz submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setCurrentIdx(0);
    setQuizResult(null);
    setTimeLeft(60);
  };

  if (!isEngagementComplete) {
    return (
      <div className="p-8 text-center rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
          <Clock className="w-6 h-6" />
        </div>
        <h4 className="text-base font-semibold text-white">PoW Micro-Quiz Locked</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Please complete at least 75% of the Curated Video / Documentation reader before taking this timed scenario assessment.
        </p>
      </div>
    );
  }

  if (totalQuestions === 0) {
    return <div className="p-4 text-xs text-slate-400">No questions available for this quiz.</div>;
  }

  // Review View after submission
  if (quizResult) {
    return (
      <div className="space-y-6">
        <div
          className={`p-6 rounded-2xl border text-center space-y-3 ${
            quizResult.passed
              ? 'bg-emerald-950/20 border-emerald-800/80'
              : 'bg-rose-950/20 border-rose-800/80'
          }`}
        >
          <div
            className={`w-14 h-14 mx-auto rounded-2xl flex items-center justify-center ${
              quizResult.passed
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-rose-500/20 text-rose-400'
            }`}
          >
            {quizResult.passed ? <Award className="w-8 h-8" /> : <XCircle className="w-8 h-8" />}
          </div>

          <div>
            <h3 className="text-xl font-bold text-white">
              {quizResult.passed ? 'Proof-of-Work Verified!' : 'Assessment Incomplete'}
            </h3>
            <p className="text-xs text-slate-300 mt-1">{quizResult.feedback}</p>
          </div>

          <div className="flex items-center justify-center gap-6 pt-2 text-xs font-mono">
            <span>
              Score: <strong className="text-white">{quizResult.score} / {quizResult.total_questions}</strong>
            </span>
            <span>
              Percentage: <strong className="text-white">{quizResult.percentage}%</strong>
            </span>
            <span>
              Passing Threshold: <strong className="text-white">≥67% (2/3)</strong>
            </span>
          </div>

          {!quizResult.passed && (
            <button
              onClick={handleRetry}
              className="mt-3 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold inline-flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Assessment</span>
            </button>
          )}
        </div>

        {/* Detailed Question Explanations Review */}
        <div className="space-y-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Answers & Architectural Explanations Review:
          </h4>

          {quizResult.answers_review?.map((review, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border space-y-3 ${
                review.is_correct
                  ? 'bg-slate-900 border-emerald-800/40'
                  : 'bg-slate-900 border-rose-800/40'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <span className="text-xs font-semibold text-white">
                  Q{review.question_id}: {review.question}
                </span>
                {review.is_correct ? (
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-[10px] font-bold border border-emerald-800">
                    CORRECT
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 text-[10px] font-bold border border-rose-800">
                    INCORRECT
                  </span>
                )}
              </div>

              <div className="space-y-1.5 text-xs">
                {review.options?.map((opt, oIdx) => {
                  let optStyle = 'border-slate-800 text-slate-400';
                  if (oIdx === review.correct_index) {
                    optStyle = 'border-emerald-600 bg-emerald-950/40 text-emerald-300 font-medium';
                  } else if (oIdx === review.selected_index && !review.is_correct) {
                    optStyle = 'border-rose-600 bg-rose-950/40 text-rose-300';
                  }

                  return (
                    <div key={oIdx} className={`p-2.5 rounded-lg border text-xs ${optStyle}`}>
                      <span>{String.fromCharCode(65 + oIdx)}. {opt}</span>
                    </div>
                  );
                })}
              </div>

              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300">
                <strong className="text-indigo-400 font-medium">Why this matters: </strong>
                <span>{review.explanation}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Active Test View
  const selectedAnswer = answers[currentQ.id];

  return (
    <div className="space-y-5">
      {/* Top Bar: Progress and Countdown Timer */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-indigo-400">
            Scenario Question {currentIdx + 1} of {totalQuestions}
          </span>
          <div className="w-24 h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-indigo-500 transition-all"
              style={{ width: `${((currentIdx + 1) / totalQuestions) * 100}%` }}
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Clock className={`w-4 h-4 ${timeLeft <= 15 ? 'text-rose-400 animate-pulse' : 'text-amber-400'}`} />
          <span
            className={`text-xs font-mono font-bold px-2.5 py-1 rounded-lg border ${
              timeLeft <= 15
                ? 'bg-rose-950/60 text-rose-400 border-rose-800'
                : 'bg-slate-800 text-slate-200 border-slate-700'
            }`}
          >
            {timeLeft}s remaining
          </span>
        </div>
      </div>

      {/* Scenario Question Box */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm md:text-base font-semibold text-white leading-relaxed">
          {currentQ.question}
        </h3>

        {/* 4 Options */}
        <div className="space-y-2.5 pt-2">
          {currentQ.options.map((option, idx) => {
            const isSelected = selectedAnswer === idx;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectOption(idx)}
                className={`w-full p-3.5 rounded-xl border text-left text-xs md:text-sm font-medium transition cursor-pointer flex items-center gap-3 ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-950/50 text-white shadow-md shadow-indigo-600/20'
                    : 'border-slate-800 hover:border-slate-700 bg-slate-800/40 text-slate-300 hover:text-white'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-lg border flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-600 text-white'
                      : 'border-slate-700 bg-slate-800 text-slate-400'
                  }`}
                >
                  {String.fromCharCode(65 + idx)}
                </div>
                <span>{option}</span>
              </button>
            );
          })}
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-2">
        <span className="text-xs text-slate-500">
          Timed 60s per question • Passing score ≥ 2/3
        </span>

        <button
          type="button"
          onClick={handleNextQuestion}
          disabled={selectedAnswer === undefined || isSubmitting}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center gap-2 shadow-md shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {isSubmitting ? (
            <span>Evaluating Proof-of-Work...</span>
          ) : currentIdx < totalQuestions - 1 ? (
            <>
              <span>Next Scenario</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          ) : (
            <>
              <span>Submit & Grade Assessment</span>
              <ShieldCheck className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

