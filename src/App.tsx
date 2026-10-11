import React from 'react';
import { Bot, CheckCircle2, ShieldAlert, Terminal, Cpu } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center space-x-4 mb-6">
          <div className="p-3 bg-indigo-600/20 border border-indigo-500/30 rounded-xl">
            <Bot className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">TXT Extractor Bot Dashboard</h1>
            <p className="text-sm text-slate-400">ClassPlus, AppX & Course Content Extraction Bot</p>
          </div>
        </div>

        <div className="space-y-4 mb-8">
          <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span className="text-sm font-medium">ClassPlus m.n.preview & Link Fixes</span>
            </div>
            <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-semibold">Active</span>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center space-x-3">
              <Cpu className="w-5 h-5 text-indigo-400" />
              <span className="text-sm font-medium">Python Bot Core Engine</span>
            </div>
            <span className="text-xs px-2.5 py-1 bg-indigo-500/10 text-indigo-400 rounded-full font-semibold">Ready</span>
          </div>
        </div>

        <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 text-xs text-slate-400 font-mono">
          <div className="flex items-center space-x-2 mb-2 text-slate-300">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <span>System Status Log</span>
          </div>
          <p>✓ Fixed URL redirection issue for media-cdn.classplusapp.com</p>
          <p>✓ All extraction modules loaded successfully.</p>
        </div>
      </div>
    </div>
  );
}
