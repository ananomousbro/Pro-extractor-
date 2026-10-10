import React, { useState } from 'react';
import { 
  Bot, 
  Terminal, 
  CheckCircle2, 
  Database, 
  Server, 
  Layers, 
  FileText, 
  Zap,
  PlayCircle,
  Upload,
  ShieldCheck,
  Code,
  Download,
  Copy,
  Check,
  KeyRound,
  ExternalLink
} from 'lucide-react';

interface ExtractorPlatform {
  id: string;
  name: string;
  category: 'Adda247' | 'RWA / Appx' | 'PhysicsWallah' | 'Careerwill';
  endpoint: string;
  authMethod: string;
  status: 'Active & Verified' | 'Ready';
  description: string;
  command: string;
  tokenGuide?: string;
}

const PLATFORMS: ExtractorPlatform[] = [
  {
    id: 'adda247',
    name: 'Adda247 (OLC & Live Batches)',
    category: 'Adda247',
    endpoint: 'store.adda247.com & videotest.adda247.com',
    authMethod: 'Session Token / X-Jwt-Token (src=aweb)',
    status: 'Active & Verified',
    description: 'Adda247 महापैक्स, लाइव क्लासेस, HLS (.m3u8 360p/480p/720p) एवं पीडीएफ नोट्स एक्सट्रैक्टर। Burp Suite कैप्चर और टोकन सपोर्ट।',
    command: '/adda या /adda247',
    tokenGuide: 'store.adda247.com पर लॉगिन करें > F12 > Network टैब > Headers से "X-Jwt-Token" कॉपी करें।'
  },
  {
    id: 'rwa_appx',
    name: 'RWA (Rojgar With Ankit) & Appx Master',
    category: 'RWA / Appx',
    endpoint: 'rozgarapinew.teachx.in & transcoded-videos.classx.co.in',
    authMethod: 'Client-Service: Appx, Auth-Key: appxapi, JWT Bearer',
    status: 'Active & Verified',
    description: 'RWA एवं 9,700+ Appx प्लेटफॉर्म्स के लाइव HLS m3u8 स्ट्रीम्स, वीडियो लेक्चर्स और पीडीएफ नोट्स एक्सट्रैक्टर। Master AES Decryptor से लैस।',
    command: '/rwa या /appx',
    tokenGuide: 'rojgarwithankit.co.in पर लॉगिन करें > Headers से JWT Authorization टोकन कॉपी करें।'
  },
  {
    id: 'pw',
    name: 'PhysicsWallah (PW) PenPencil v3',
    category: 'PhysicsWallah',
    endpoint: 'api.penpencil.co / batch-service',
    authMethod: 'Direct Bearer JWT (Bypasses OTP) / Client-Id 5eb393ee95fab7468a79d189',
    status: 'Active & Verified',
    description: 'PW बैचेस, लक्ष्य/अर्जुन/यकीन वीडियो लेक्चर्स (.m3u8), डीपीपी एवं नोट्स पीडीएफ एक्सट्रैक्टर। OTP की ज़रूरत नहीं—डायरेक्ट वेब टोकन से 100% वर्किंग।',
    command: '/pw या /freepw',
    tokenGuide: 'www.pw.live पर लॉगिन करें > F12 > Network टैब > Request Headers से "Authorization: Bearer eyJ..." कॉपी करें।'
  },
  {
    id: 'careerwill',
    name: 'Careerwill (Rakesh Yadav / Gagan Pratap Sir)',
    category: 'Careerwill',
    endpoint: 'wbspec.crwilladmin.com & elearn.crwilladmin.com',
    authMethod: 'Session Token / ID*Password / cwkey AES-128',
    status: 'Active & Verified',
    description: 'कैरियरविल लाइव क्लासेस, वीडियो (.m3u8 Brightcove) एवं पीडीएफ नोट्स एक्सट्रैक्टर। Burp Suite बायपास के साथ टोकन सपोर्ट।',
    command: '/ugcw या /careerwill',
    tokenGuide: 'web.careerwill.com/login पर लॉगिन करके F12 > Application > Cookies में जाकर "token" कॉपी करें।'
  }
];

export function App() {
  const [selectedPlatform, setSelectedPlatform] = useState<ExtractorPlatform>(PLATFORMS[0]);
  const [activeTab, setActiveTab] = useState<'all' | 'Adda247' | 'RWA / Appx' | 'PhysicsWallah' | 'Careerwill'>('all');
  const [copied, setCopied] = useState(false);
  const [inputText, setInputText] = useState('');
  const [parsedOutput, setParsedOutput] = useState<{ title: string; url: string }[] | null>(null);

  const filteredPlatforms = activeTab === 'all' 
    ? PLATFORMS 
    : PLATFORMS.filter(p => p.category === activeTab);

  const handleParseTxt = () => {
    if (!inputText.trim()) return;
    const lines = inputText.split('\n');
    const results: { title: string; url: string }[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.includes('http://') || line.includes('https://') || line.includes('.m3u8') || line.includes('.pdf') || line.includes('UGPro_')) {
        const title = i > 0 ? lines[i - 1].trim() : `Lecture ${results.length + 1}`;
        results.push({ 
          title: title.length > 5 && !title.includes('http') ? title : `Item ${results.length + 1}`, 
          url: line 
        });
      }
    }
    setParsedOutput(results.length > 0 ? results : [{ title: 'Raw Dump', url: inputText }]);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header Bar */}
        <header className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-6 gap-4">
          <div className="flex items-center space-x-3">
            <div className="h-12 w-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Bot className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                DREAM TXT EXTRACTOR BOT
                <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-medium">
                  Engine v5 Live
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Adda247, RWA (Appx), PhysicsWallah और Careerwill एडटेक एक्सट्रैक्शन और यूप्लॉडर सिस्टम
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
              <Server className="h-4 w-4 text-indigo-400" />
              <span>Host: 0.0.0.0:3000</span>
            </div>
            <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-800/40 rounded-lg px-3 py-1.5 text-xs text-emerald-300">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>Dev Server Online</span>
            </div>
          </div>
        </header>

        {/* Categories Tab Bar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800/80 pb-2">
          {(['all', 'Adda247', 'RWA / Appx', 'PhysicsWallah', 'Careerwill'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {tab === 'all' ? 'सभी प्लेटफॉर्म्स' : tab}
            </button>
          ))}
        </div>

        {/* Grid List of Platforms */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredPlatforms.map(platform => (
            <div 
              key={platform.id}
              onClick={() => setSelectedPlatform(platform)}
              className={`cursor-pointer transition-all rounded-xl border p-5 ${
                selectedPlatform.id === platform.id 
                  ? 'bg-slate-900 border-indigo-500 shadow-md shadow-indigo-500/10' 
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className={`inline-block text-[11px] px-2.5 py-0.5 rounded-full font-semibold mb-2 ${
                    platform.category === 'Adda247'
                      ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/50'
                      : platform.category === 'RWA / Appx'
                      ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/50'
                      : platform.category === 'PhysicsWallah'
                      ? 'bg-purple-950/80 text-purple-300 border border-purple-800/50'
                      : 'bg-rose-950/80 text-rose-300 border border-rose-800/50'
                  }`}>
                     श्रेणी: {platform.category}
                  </span>
                  <h3 className="text-lg font-bold text-white">{platform.name}</h3>
                </div>
                <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {platform.status}
                </span>
              </div>

              <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                {platform.description}
              </p>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>कमांड: <strong className="text-indigo-400 font-semibold">{platform.command}</strong></span>
                <span className="truncate max-w-[200px] text-slate-500">{platform.endpoint}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Selected Platform Details & Bypass Guide */}
        {selectedPlatform.tokenGuide && (
          <div className="bg-slate-900/90 border border-indigo-950/80 rounded-xl p-5 flex items-start gap-4">
            <div className="p-2.5 bg-indigo-950 text-indigo-400 rounded-lg">
              <KeyRound className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <div className="text-sm font-semibold text-white">
                {selectedPlatform.name} — टोकन और ऑथेंटिकेशन गाइड:
              </div>
              <p className="text-xs text-slate-300 font-mono">
                {selectedPlatform.tokenGuide}
              </p>
            </div>
          </div>
        )}

        {/* TXT Uploader & Parser Section */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Upload className="h-5 w-5 text-indigo-400" />
              {selectedPlatform.name} — TXT फ़ाइल पार्सर और यूप्लॉडर टूल
            </h3>
            <span className="text-xs font-mono bg-indigo-950 text-indigo-300 px-3 py-1 rounded-full border border-indigo-800/60">
              Auth: {selectedPlatform.authMethod}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
                यहाँ अपनी TXT फाइल का डेटा पेस्ट करें या ड्रॉप करें:
              </label>
              <textarea
                rows={7}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="उदाहरण:
Class 1: Reasoning Basic
https://videotest.adda247.com/demo/updated/master.m3u8
Class 2: Math Lecture 01
https://transcoded-videos.classx.co.in/videos/rozgar-data/master.m3u8"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleParseTxt}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                <PlayCircle className="h-4 w-4" />
                TXT डेटा पार्स करें (Parse Links)
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
                  पार्स किए गए लिंक्स ({parsedOutput ? parsedOutput.length : 0}):
                </label>
                {parsedOutput && parsedOutput.length > 0 && (
                  <button
                    onClick={() => copyToClipboard(parsedOutput.map(i => `${i.title}\n${i.url}`).join('\n\n'))}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    {copied ? 'कॉपी हो गया!' : 'सभी कॉपी करें'}
                  </button>
                )}
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 h-[180px] overflow-y-auto space-y-2 text-xs font-mono">
                {parsedOutput ? (
                  parsedOutput.map((item, idx) => (
                    <div key={idx} className="border-b border-slate-900 pb-2 last:border-0">
                      <div className="text-indigo-300 font-semibold">{item.title}</div>
                      <div className="text-slate-400 truncate select-all">{item.url}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500 text-center py-10">
                    अभी कोई डेटा पार्स नहीं किया गया है। बाएँ बॉक्स में डेटा डालकर पार्स बटन दबाएं।
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
export default App;
