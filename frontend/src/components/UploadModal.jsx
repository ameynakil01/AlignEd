import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Sparkles, X, ChevronRight } from 'lucide-react';
import { parseDocument } from '../services/api';

const SAMPLE_PRESETS = [
  {
    name: 'CS Student Syllabus (Python, SQL, HTML)',
    role: 'backend-python-engineer',
    text: `Department of Computer Science & Engineering
Course: CS301 - Data Structures & Web Foundations
Prerequisites: Basic programming concepts.
Topics Covered:
- Core Python programming fundamentals, lists, dictionaries, recursion
- Introduction to SQL databases, relational schema creation, table queries
- Basics of HTML5 markup, web documents, and CSS styling
- Version control basics using Git command line`
  },
  {
    name: 'Junior Flutter Enthusiast (Dart, Git)',
    role: 'junior-flutter-developer',
    text: `Student Resume: Mobile App Enthusiast
Skills & Projects:
- Dart programming language, object-oriented concepts, asynchronous Futures
- Git and GitHub for version control and collaborative branching
- Basic SQLite database operations and mobile UI prototypes
- Exposure to RESTful JSON responses and HTTP status codes`
  },
  {
    name: 'Frontend Aspirant (JavaScript, React)',
    role: 'frontend-web-developer',
    text: `Frontend Engineering Bootcamp Syllabus
Modules:
- Modern JavaScript ES6+, closures, promises, async/await
- React component fundamentals, stateful hooks (useState, useEffect)
- Semantic HTML5 and responsive styling using Tailwind CSS
- Consuming REST APIs and debugging browser client state`
  }
];

export default function UploadModal({ isOpen, onClose, roles, selectedRole, setSelectedRole, onAnalysisComplete }) {
  const dialogRef = useRef(null);
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('pdf'); // 'pdf' | 'text'
  const [selectedFile, setSelectedFile] = useState(null);
  const [pastedText, setPastedText] = useState('');
  const [studentName, setStudentName] = useState('Alex Rivers');
  const [isParsing, setIsParsing] = useState(false);
  const [parsedSkills, setParsedSkills] = useState([]);
  const [parseError, setParseError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Modern Web Guidance: Native <dialog> lifecycle and light-dismiss fallback
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }

    // Light-dismiss click boundary fallback for non-supporting browsers
    const handleBackdropClick = (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const isInside =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (!isInside) {
        onClose();
      }
    };

    dialog.addEventListener('click', handleBackdropClick);
    return () => dialog.removeEventListener('click', handleBackdropClick);
  }, [isOpen, onClose]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      triggerAutoParse(file, null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      triggerAutoParse(file, null);
    }
  };

  const handleApplyPreset = (preset) => {
    setPastedText(preset.text);
    setActiveTab('text');
    setSelectedRole(preset.role);
    triggerAutoParse(null, preset.text);
  };

  const triggerAutoParse = async (file, text) => {
    setIsParsing(true);
    setParseError(null);
    try {
      const result = await parseDocument({ file, rawText: text });
      setParsedSkills(result.skills || []);
    } catch (err) {
      setParseError(err.message || 'Failed to extract skills');
    } finally {
      setIsParsing(false);
    }
  };

  const handleProceed = () => {
    if (parsedSkills.length === 0) {
      setParseError('Please parse a document or paste syllabus text with detected skills first.');
      return;
    }
    onAnalysisComplete({
      roleId: selectedRole,
      studentName,
      extractedSkills: parsedSkills,
    });
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby="upload-modal-title"
      className="p-0 rounded-2xl bg-slate-900 text-slate-100 border border-slate-700/80 shadow-2xl max-w-2xl w-full mx-auto backdrop:backdrop-blur-md"
    >
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h2 id="upload-modal-title" className="text-lg font-semibold text-white">
              Map Syllabus & Career Profile
            </h2>
            <p className="text-xs text-slate-400">
              Upload your semester curriculum or resume to benchmark against real roles
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="p-6 space-y-5 max-h-[80vh] overflow-y-auto">
        {/* Student Name & Target Role Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Student / Candidate Name
            </label>
            <input
              type="text"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="e.g. Alex Rivers"
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Target Job Benchmark
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title} ({r.category})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Preset quick buttons */}
        <div>
          <span className="text-xs font-medium text-slate-400 mb-1.5 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Quick Presets (One-click sample curricula):
          </span>
          <div className="flex flex-wrap gap-2 mt-1">
            {SAMPLE_PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 text-slate-300 border border-slate-700 hover:border-slate-600 transition flex items-center gap-1"
              >
                <span>{preset.name}</span>
                <ChevronRight className="w-3 h-3 text-slate-400" />
              </button>
            ))}
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('pdf')}
            className={`flex-1 py-2 text-sm font-medium border-b-2 transition ${
              activeTab === 'pdf'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Upload PDF Document
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`flex-1 py-2 text-sm font-medium border-b-2 transition ${
              activeTab === 'text'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Paste Syllabus / Resume Text
          </button>
        </div>

        {/* Upload File Mode */}
        {activeTab === 'pdf' && (
          <div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-7 text-center cursor-pointer transition ${
                isDragOver
                  ? 'border-indigo-500 bg-indigo-950/20'
                  : 'border-slate-700 hover:border-slate-600 bg-slate-800/40'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-indigo-600/10 text-indigo-400 flex items-center justify-center">
                <FileText className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-slate-200">
                {selectedFile ? selectedFile.name : 'Drag & drop your syllabus PDF here, or click to browse'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Supports official university syllabus PDFs or student resumes (Max 15MB)
              </p>
            </div>
          </div>
        )}

        {/* Paste Text Mode */}
        {activeTab === 'text' && (
          <div className="space-y-2">
            <textarea
              rows={6}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your course outcomes, syllabus module descriptions, or resume technical sections..."
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              disabled={isParsing || !pastedText.trim()}
              onClick={() => triggerAutoParse(null, pastedText)}
              className="px-3.5 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-xs font-medium text-white transition disabled:opacity-50"
            >
              {isParsing ? 'Parsing with spaCy...' : 'Extract Skills From Text'}
            </button>
          </div>
        )}

        {/* Feedback & Parsing status */}
        {isParsing && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-300 text-xs">
            <div className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            <span>Analyzing document structure and extracting tech entities using spaCy...</span>
          </div>
        )}

        {parseError && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{parseError}</span>
          </div>
        )}

        {/* Extracted Skills Preview Chips */}
        {parsedSkills.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {parsedSkills.length} Technical Skills Extracted:
              </span>
              <span className="text-[11px] text-slate-400">spaCy Normalized</span>
            </div>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
              {parsedSkills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-800 bg-slate-900/80">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleProceed}
          disabled={parsedSkills.length === 0}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Calculate Career Gap</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </dialog>
  );
}

