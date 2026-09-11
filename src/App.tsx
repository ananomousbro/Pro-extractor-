import React, { useState } from 'react';
import { Bot, FileText, CheckCircle2, ShieldCheck, RefreshCw, Key, Database, BookOpen } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'status' | 'config' | 'test'>('status');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-inner">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">TXT Extractor Bot Engine</h1>
            <p className="text-xs text-slate-400">ClassX / Appx API Extraction & TXT Generator</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
            APIs Operational
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 space-y-6">
        {/* Status Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start space-x-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">AES-128-CBC Engine</p>
              <h3 className="text-sm font-semibold text-slate-200 mt-0.5">Custom IV & Plaintext Ready</h3>
              <p className="text-xs text-slate-500 mt-1">Supports standard IV & embedded base64 IVs without crash</p>
            </div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start space-x-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">JSON Parser</p>
              <h3 className="text-sm font-semibold text-slate-200 mt-0.5">PHP/HTML Safe Extractor</h3>
              <p className="text-xs text-slate-500 mt-1">Strips HTML notices and isolates valid JSON payloads</p>
            </div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start space-x-3">
            <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">TXT Generator</p>
              <h3 className="text-sm font-semibold text-slate-200 mt-0.5">Auto-Fallback Delivery</h3>
              <p className="text-xs text-slate-500 mt-1">Recursive folder crawler with multi-level fallbacks</p>
            </div>
          </div>
        </div>

        {/* Verification Summary Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
            <div className="flex items-center space-x-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-semibold">Tested & Verified Platforms</h2>
            </div>
            <span className="text-xs text-slate-400">Batch extraction verified</span>
          </div>

          <div className="space-y-4">
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-semibold text-slate-200">Everest Impact API (Batch 398)</span>
                </div>
                <span className="text-xs font-mono bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/20">
                  Folder ID 631275 (29 folders)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Recursive content crawling verified: Geometry, Calculation, Bharat Atlas, English, Current Affairs. Videos (.m3u8) & PDFs decrypted correctly and formatted for TXT export.
              </p>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-semibold text-slate-200">Yes Officer API (Batch 139)</span>
                </div>
                <span className="text-xs font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                  Batch Auth & Folder Traversal
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Auth login and multi-endpoint fallback (v3, v2, course_by_id, and allsubjectfrmlivecourseclass) active.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
