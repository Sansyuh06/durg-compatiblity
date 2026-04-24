"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ShieldAlert, Activity, RefreshCw, Play, Shield, FolderOpen, 
  Search, FileText, Microscope, BookOpen, ClipboardCheck, Hourglass,
  AlertTriangle, Lightbulb
} from "lucide-react";

type TaskLevel = "easy" | "medium" | "hard";

interface ActionResponse {
  observation: { step_number: number; drug_name: string; episode_done: boolean; current_output?: any; };
  reward: { value: number; message: string; breakdown?: Record<string, number>; };
  info: { steps_remaining: number; max_steps: number; };
  action_type?: string; parameters?: any; done?: boolean;
}

export default function Home() {
  const [currentTask, setCurrentTask] = useState<TaskLevel>("easy");
  const [episodeActive, setEpisodeActive] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("IDLE");
  const [feed, setFeed] = useState<any[]>([]);
  
  const [stats, setStats] = useState({ episodes: 0, actions: 0, bestScore: null as null | number });
  const [currentScore, setCurrentScore] = useState<number | null>(null);
  const [breakdown, setBreakdown] = useState<any>(null);
  const [rewardMessage, setRewardMessage] = useState("");
  const [steps, setSteps] = useState({ current: 0, remaining: 0, max: 0 });

  const [submitFormOpen, setSubmitFormOpen] = useState(false);
  const [submitData, setSubmitData] = useState({ drug_name: '', primary_signal: '', secondary_signal: '', regulatory_action: 'monitor' });

  const feedEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [feed]);

  const addLog = (comp: any) => setFeed(f => [...f, comp]);
  const clearFeed = () => setFeed([]);

  const selectTask = (id: TaskLevel) => {
    setCurrentTask(id); setStatusText("IDLE"); setEpisodeActive(false); setSubmitFormOpen(false);
  };

  const hitApi = async (url: string, body?: any) => {
    const res = await fetch(url, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    return res.json();
  };

  const handleReset = async () => {
    setLoading(true); setSubmitFormOpen(false); clearFeed(); setCurrentScore(null);
    setBreakdown(null); setRewardMessage(""); setIsDone(false);

    try {
      const obs = await hitApi('/reset', { task_id: currentTask });
      setEpisodeActive(true); setSteps({ current: 0, remaining: 0, max: 0 });
      setStatusText(`ACTIVE`); setStats(s => ({ ...s, episodes: s.episodes + 1 }));
      addLog({ type: 'reset', data: obs, id: Date.now() });
    } catch (e: any) {
      alert("Reset failed: " + e.message); setStatusText("ERROR");
    } finally { setLoading(false); }
  };

  const handleAction = async (actionType: string) => {
    if (!episodeActive || isDone) return alert("Start a new episode first.");
    setLoading(true); setStats(s => ({ ...s, actions: s.actions + 1 }));

    try {
      const data: ActionResponse = await hitApi('/step', { action_type: actionType, parameters: {} });
      const { observation: obs, reward, info } = data;
      setSteps({ current: obs.step_number, remaining: info.steps_remaining, max: info.max_steps });
      if (obs.episode_done) handleDone(reward.value);

      addLog({ type: 'action', actionType, step: obs.step_number, output: obs.current_output, reward: reward.value, remaining: info.steps_remaining, id: Date.now() });
    } catch (e: any) {
      addLog({ type: 'error', message: e.message, id: Date.now() });
    } finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!episodeActive || isDone) return;
    if (!submitData.drug_name || !submitData.primary_signal) return alert("Fill required fields");

    setLoading(true); setSubmitFormOpen(false); setStats(s => ({ ...s, actions: s.actions + 1 }));

    try {
      const data: ActionResponse = await hitApi('/step', { action_type: 'submit', parameters: submitData });
      const { observation: obs, reward, info } = data;
      setSteps({ current: obs.step_number, remaining: info.steps_remaining, max: info.max_steps });
      
      setCurrentScore(reward.value); setBreakdown(reward.breakdown); setRewardMessage(reward.message);
      if (stats.bestScore === null || reward.value > stats.bestScore) setStats(s => ({ ...s, bestScore: reward.value }));
      handleDone(reward.value);

      addLog({ type: 'submit', param: submitData, score: reward.value, message: reward.message, id: Date.now() });
    } catch (e: any) { alert("Submit failed: " + e.message); } finally { setLoading(false); }
  };

  const handleDemo = async () => {
    setLoading(true); clearFeed(); setCurrentScore(null); setBreakdown(null); setIsDone(false);
    setStatusText("DEMO"); setEpisodeActive(false);

    try {
      const demoRes = await fetch(`/api/demo/${currentTask}`, { method: 'POST' });
      const demoData = await demoRes.json();
      let finalSc = 0;
      for (const step of demoData.steps) {
        await new Promise(r => setTimeout(r, 800));
        const { observation: obs, reward, info, action_type } = step;
        setSteps({ current: obs.step_number, remaining: info.steps_remaining, max: info.max_steps });

        if (action_type !== 'submit') {
          addLog({ type: 'action', actionType: action_type, step: obs.step_number, output: obs.current_output, reward: reward.value, remaining: info.steps_remaining, id: Date.now() + Math.random() });
        } else {
          setCurrentScore(reward.value); setBreakdown(reward.breakdown); setRewardMessage(reward.message); finalSc = reward.value;
          if (stats.bestScore === null || reward.value > stats.bestScore) setStats(s => ({ ...s, bestScore: reward.value }));
          addLog({ type: 'submit', param: step.parameters, score: reward.value, message: reward.message, id: Date.now() + Math.random() });
        }
      }
      handleDone(finalSc);
    } catch (e: any) { alert("Demo failed: " + e.message); setStatusText("ERROR"); } finally { setLoading(false); }
  };

  const handleDone = (score: number) => { setIsDone(true); setEpisodeActive(false); setStatusText(`DONE • ${score >= 0.7 ? 'SUCCESS' : 'FAILED'}`); };

  const getIcon = (type: string) => {
    switch(type) {
      case 'search_faers': return <Search className="w-5 h-5 text-cyan-400" />;
      case 'fetch_label': return <FileText className="w-5 h-5 text-purple-400" />;
      case 'analyze_signal': return <Activity className="w-5 h-5 text-emerald-400" />;
      case 'lookup_mechanism': return <Microscope className="w-5 h-5 text-pink-400" />;
      case 'check_literature': return <BookOpen className="w-5 h-5 text-blue-400" />;
      default: return <Shield className="w-5 h-5 text-gray-400" />;
    }
  };

  // Rich JSON Renderer
  const renderRichData = (data: any) => {
    if (!data || typeof data !== 'object') return <span className="text-gray-300">{String(data)}</span>;
    const metrics = ['PRR', 'ROR', 'EB05', 'IC025', 'prr', 'ror'];
    const hasMetrics = Object.keys(data).some(k => metrics.includes(k) && typeof data[k] === 'number');

    return (
      <div className="space-y-3 mt-3">
        {hasMetrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {Object.keys(data).filter(k => metrics.includes(k) || typeof data[k] === 'number').map(k => (
              <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} key={k} className="glass-panel rounded-xl p-3 flex flex-col items-center">
                <span className="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-widest">{k.replace(/_/g, ' ')}</span>
                <span className="text-lg font-mono font-bold text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]">{Number(data[k]).toFixed(2)}</span>
              </motion.div>
            ))}
          </div>
        )}
        
        {Object.keys(data).filter(k => !hasMetrics || (!metrics.includes(k) && typeof data[k] !== 'number')).map(k => {
          const val = data[k];
          const isString = typeof val === 'string';
          const isArray = Array.isArray(val);
          return (
            <div key={k} className="flex flex-col sm:flex-row sm:gap-4 border-t border-white/5 pt-3">
              <span className="text-[10px] uppercase font-bold text-gray-500 w-32 shrink-0 tracking-widest mt-0.5">{k.replace(/_/g,' ')}</span>
              <div className="text-gray-300 text-sm max-w-full font-light">
                {isString ? (
                  <span className={val.length < 30 && val === val.toUpperCase() ? "text-purple-300 font-bold bg-purple-500/20 px-2 py-1 rounded inline-block" : ""}>{val}</span>
                ) : isArray ? (
                  <div className="space-y-2">
                    {val.slice(0,3).map((item, i) => (
                      <div key={i} className="bg-black/40 px-3 py-2 rounded-lg border border-white/5 text-[12px] font-mono hover:border-white/10 transition-colors">
                        {typeof item === 'object' ? JSON.stringify(item).substring(0,120) + (JSON.stringify(item).length > 120 ? '...' : '') : String(item)}
                      </div>
                    ))}
                    {val.length > 3 && <div className="text-[10px] uppercase font-bold text-gray-500 italic px-1 pt-1 tracking-widest">+ {val.length - 3} more</div>}
                  </div>
                ) : typeof val === 'object' && val !== null ? (
                  <pre className="text-[11px] font-mono bg-black/60 border border-white/5 p-3 rounded-lg text-cyan-300/80 max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {JSON.stringify(val, null, 2)}
                  </pre>
                ) : String(val)}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const ActionBox = ({ title, desc, type, onClick, disabled }: any) => (
    <motion.button 
      whileHover={disabled ? {} : { scale: 1.02, y: -2 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      onClick={onClick} disabled={disabled}
      className={`p-4 rounded-2xl text-left relative overflow-hidden transition-all
        ${disabled ? 'opacity-40 bg-gray-900/40 cursor-not-allowed border border-white/5' : 'glass-action cursor-pointer'}
        ${type === 'submit' && !disabled ? 'border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.15)] bg-gradient-to-br from-cyan-950/40 to-black/80' : ''}
      `}
    >
      <div className="flex items-center gap-4 mb-2">
        <div className={`p-2.5 rounded-xl bg-black/50 border border-white/5 shadow-inner`}>{getIcon(type)}</div>
        <h3 className={`font-bold text-sm tracking-wide ${type === 'submit' ? 'text-cyan-400' : 'text-gray-100'}`}>{title}</h3>
      </div>
      <p className="text-xs text-gray-400 ml-[3.25rem] font-medium">{desc}</p>
    </motion.button>
  );

  return (
    <>
      <div className="glow-orb glow-purple"></div>
      <div className="glow-orb glow-cyan"></div>
      
      <div className="min-h-screen flex flex-col items-center pt-8 pb-20 px-4">
        
        {/* Header / Global Config */}
        <motion.header 
          initial={{ y: -30, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          className="w-full max-w-6xl glass-panel rounded-2xl p-5 mb-8 flex flex-col md:flex-row justify-between items-center z-10"
        >
          <div className="flex items-center gap-4 mb-4 md:mb-0">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-cyan-500 p-[1px]">
              <div className="w-full h-full bg-black/80 rounded-2xl flex items-center justify-center backdrop-blur-xl">
                <ShieldAlert className="text-white w-6 h-6" />
              </div>
            </div>
            <div>
              <h1 className="font-extrabold text-xl text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 tracking-tight">Foldables Pharmacovigilance</h1>
              <div className="flex gap-2 items-center text-[10px] uppercase font-bold tracking-widest text-gray-500">
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span> ONLINE</span>
                <span>•</span>
                <span>Pharmacovigilance Core</span>
              </div>
            </div>
          </div>

          <div className="flex gap-2 bg-black/40 p-1 rounded-xl border border-white/5">
            {['easy', 'medium', 'hard'].map(t => (
              <button key={t} onClick={() => selectTask(t as TaskLevel)} className="relative px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg z-0">
                {currentTask === t && <motion.div layoutId="tab" className="absolute inset-0 bg-white/10 border border-white/10 rounded-lg -z-10 shadow-lg"></motion.div>}
                <span className={currentTask === t ? 'text-white' : 'text-gray-500 hover:text-gray-300 transition-colors'}>{t}</span>
              </button>
            ))}
          </div>

          <div className="flex gap-3 mt-4 md:mt-0">
             <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleReset} disabled={loading} className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-bold rounded-xl flex items-center gap-2 text-xs transition-shadow shadow-[0_0_20px_rgba(168,85,247,0.3)] disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading && statusText !== 'DEMO' ? 'animate-spin' : ''}`}/> NEW EPISODE
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleDemo} disabled={loading} className="px-5 py-2.5 bg-black border border-cyan-500/30 text-cyan-400 font-bold rounded-xl flex items-center gap-2 text-xs hover:bg-cyan-500/10 transition-colors disabled:opacity-50">
              <Play className="w-4 h-4"/> AUTO DEMO
            </motion.button>
          </div>
        </motion.header>

        {/* Main Grid Workspace */}
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-0">
          
          {/* Agent Tools Sidebar */}
          <div className="lg:col-span-4 space-y-4">
            <div className="glass-panel rounded-2xl p-4 flex justify-between items-center">
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Agent Status</div>
              <div className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${episodeActive ? 'bg-green-500/20 text-green-400' : 'bg-gray-800 text-gray-400'}`}>
                {statusText}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
              <ActionBox title="Search FAERS" desc="Query adverse events" type="search_faers" onClick={()=>handleAction('search_faers')} disabled={!episodeActive || loading || isDone} />
              <ActionBox title="Fetch Label" desc="FDA documentation" type="fetch_label" onClick={()=>handleAction('fetch_label')} disabled={!episodeActive || loading || isDone} />
              <ActionBox title="Analyze Signal" desc="Compute PRR/ROR" type="analyze_signal" onClick={()=>handleAction('analyze_signal')} disabled={!episodeActive || loading || isDone} />
              <ActionBox title="Mechanism" desc="Pharmacology data" type="lookup_mechanism" onClick={()=>handleAction('lookup_mechanism')} disabled={!episodeActive || loading || isDone} />
              <ActionBox title="Literature" desc="Safety studies" type="check_literature" onClick={()=>handleAction('check_literature')} disabled={!episodeActive || loading || isDone} />
              <ActionBox title="Submit Assessment" desc="Final regulatory decision" type="submit" onClick={()=>setSubmitFormOpen(p=>!p)} disabled={!episodeActive || loading || isDone} />
            </div>

            <AnimatePresence>
              {submitFormOpen && (
                <motion.form initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} onSubmit={handleSubmit} className="glass-panel p-5 rounded-2xl border-cyan-500/30 flex flex-col gap-3 shadow-[0_0_30px_rgba(6,182,212,0.1)] overflow-hidden">
                  <div className="text-[10px] uppercase font-bold text-cyan-400 tracking-widest">Final Assessment Form</div>
                  <input placeholder="Drug Name" value={submitData.drug_name} onChange={e=>setSubmitData({...submitData, drug_name: e.target.value})} className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm" required />
                  <input placeholder="Primary Signal" value={submitData.primary_signal} onChange={e=>setSubmitData({...submitData, primary_signal: e.target.value})} className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm" required />
                  {currentTask === 'hard' && <input placeholder="Secondary Signal" value={submitData.secondary_signal} onChange={e=>setSubmitData({...submitData, secondary_signal: e.target.value})} className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm" />}
                  <select value={submitData.regulatory_action} onChange={e=>setSubmitData({...submitData, regulatory_action: e.target.value})} className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm">
                    <option value="monitor">Monitor (Enhanced Surveillance)</option>
                    <option value="restrict">Restrict (REMS / iPLEDGE)</option>
                    <option value="withdraw">Withdraw (Market Removal)</option>
                  </select>
                  <button type="submit" className="w-full py-3 mt-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white rounded-xl font-bold shadow-lg shadow-cyan-500/20">Submit Decision</button>
                </motion.form>
              )}
            </AnimatePresence>

               {/* Score Metric Card */}
             {breakdown && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel border-cyan-500/20 rounded-2xl p-5 mb-4 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-3xl rounded-full"></div>
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Total Score</div>
                  <div className={`text-6xl font-black mb-6 ${currentScore! >= 0.7 ? 'text-green-400' : currentScore! >= 0.5 ? 'text-yellow-400' : 'text-red-400'} drop-shadow-[0_0_15px_currentColor]`}>{currentScore!.toFixed(2)}</div>
                  <div className="space-y-2">
                    {Object.keys(breakdown).map(k => (
                      <div key={k} className="flex justify-between text-[11px] font-mono border-b border-white/5 pb-2">
                        <span className="text-gray-400">{k.replace(/_/g, ' ')}</span>
                        <span className={`font-bold ${breakdown[k] > 0 ? 'text-green-400' : breakdown[k] < 0 ? 'text-red-400' : 'text-gray-500'}`}>{breakdown[k] > 0 ? '+' : ''}{breakdown[k].toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
             )}

          </div>

          {/* Center Activity Timeline */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            
            <div className="flex items-center gap-4 text-gray-500 text-[10px] uppercase font-bold tracking-widest px-2">
              <span className="flex-1 border-b border-gray-800"></span>
              <span>Investigation Timeline</span>
              <span className="flex-1 border-b border-gray-800"></span>
            </div>

            <div className="space-y-6">
              <AnimatePresence>
                {feed.length === 0 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center p-20 text-gray-500 border border-dashed border-gray-800 rounded-3xl bg-black/20">
                    <Activity className="w-12 h-12 text-gray-700 mb-4" />
                    <p className="text-sm">Awaiting new episode initialization...</p>
                  </motion.div>
                )}

                {feed.map(item => (
                  <motion.div layout initial={{ opacity: 0, y: 30, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ type: 'spring', stiffness: 200, damping: 20 }} key={item.id} className="relative">
                    
                    {/* Vertical timeline line */}
                    <div className="absolute left-[24px] top-[40px] bottom-[-30px] w-[1px] bg-gradient-to-b from-gray-800 to-transparent -z-10 hidden sm:block"></div>

                    {item.type === 'reset' && (
                      <div className="glass-panel border-purple-500/30 rounded-2xl p-6 shadow-[0_4px_30px_rgba(168,85,247,0.1)]">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400 border border-purple-500/40 shadow-inner">
                            <FolderOpen className="w-6 h-6" />
                          </div>
                          <div>
                            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">New Case Authorized</div>
                            <div className="text-2xl font-black text-white tracking-tight">{item.data.drug_name}</div>
                          </div>
                        </div>
                        {item.data.current_output?.message && (
                          <div className="mt-5 p-4 bg-black/40 border border-white/5 rounded-xl text-sm font-light leading-relaxed text-gray-300">
                            {item.data.current_output.message}
                          </div>
                        )}
                      </div>
                    )}

                    {item.type === 'action' && (
                      <div className="glass-panel border-gray-800 rounded-2xl p-6 sm:ml-6 group hover:border-gray-700 transition-colors relative z-0">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center gap-3">
                             <div className="p-2 rounded-lg bg-black/50 border border-white/10 shadow-inner group-hover:bg-white/5 transition-colors">
                              {getIcon(item.actionType)}
                            </div>
                            <div className="font-bold text-white capitalize text-lg tracking-tight">{item.actionType.replace('_', ' ')}</div>
                          </div>
                          <div className="text-[10px] font-mono font-bold text-gray-500 bg-black/80 border border-white/5 px-2.5 py-1 rounded">STEP {item.step}</div>
                        </div>
                        
                        <div className="mb-4">
                           {item.output?.source && <div className="text-[10px] uppercase font-bold text-purple-400 mb-2">SOURCE: <span className="text-gray-300 font-normal">{item.output.source}</span></div>}
                           {item.output?.error && <div className="text-red-400 bg-red-950/40 p-3 rounded-lg mb-2 border border-red-500/30 text-sm">{item.output.error}</div>}
                           {item.output?.data && renderRichData(item.output.data)}
                           {item.output?.hint && <div className="mt-4 text-emerald-400 bg-emerald-950/30 border border-emerald-500/30 px-4 py-3 rounded-xl flex items-start gap-3 shadow-sm text-xs"><Lightbulb className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5"/> <span className="leading-relaxed">{item.output.hint}</span></div>}
                        </div>

                        <div className="flex justify-between items-center pt-3 border-t border-white/5">
                          <div className="text-[10px] font-bold text-green-400 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm"><span className="text-green-500">+</span> {item.reward.toFixed(2)} Reward</div>
                          <div className="text-[10px] font-bold text-gray-500 flex items-center gap-1.5"><Hourglass className="w-3 h-3"/> {item.remaining} remaining</div>
                        </div>
                      </div>
                    )}

                    {item.type === 'submit' && (
                      <div className="glass-panel border-cyan-500/40 rounded-2xl p-6 sm:ml-6 shadow-[0_0_40px_rgba(6,182,212,0.15)] relative overflow-hidden z-0">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-3xl rounded-full -z-10"></div>
                        
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/50 shadow-inner">
                            <ClipboardCheck className="w-7 h-7"/>
                          </div>
                          <div>
                            <div className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest shadow-cyan-500 drop-shadow-md">Assessment Concluded</div>
                            <div className="font-extrabold text-2xl text-white tracking-tight">Final Decision Logged</div>
                          </div>
                        </div>
                        
                        <div className="bg-black/60 p-5 rounded-xl border border-white/5 grid grid-cols-2 gap-5 mb-5">
                          <div><div className="text-[9px] text-gray-500 uppercase font-bold mb-1">Target Subject</div><div className="font-bold text-white text-base">{item.param.drug_name}</div></div>
                          <div><div className="text-[9px] text-gray-500 uppercase font-bold mb-1">Recommended Action</div><div className="font-bold text-cyan-300 bg-cyan-950/50 border border-cyan-500/30 px-2.5 py-1 rounded-md inline-block shadow-inner">{item.param.regulatory_action}</div></div>
                          <div className="col-span-2"><div className="text-[9px] text-gray-500 uppercase font-bold mb-1">Identified Signals</div><div className="font-medium text-gray-300 text-sm bg-white/5 p-2 rounded-lg border border-white/5">{item.param.primary_signal} {item.param.secondary_signal ? <span className="text-gray-500 mx-2">&bull;</span> : ''} {item.param.secondary_signal}</div></div>
                        </div>

                        <div className="pt-4 border-t border-white/5">
                           <div className="text-[12px] text-gray-300 italic border-l-2 border-cyan-500/50 pl-3 py-1 mb-2">"{item.message}"</div>
                        </div>
                      </div>
                    )}
                    
                    {item.type === 'error' && (
                      <div className="bg-red-950/40 border border-red-500/40 text-red-400 p-4 rounded-xl text-sm flex items-center gap-3 sm:ml-6 shadow-[0_0_15px_rgba(239,68,68,0.1)] font-medium">
                        <AlertTriangle className="w-5 h-5"/> {item.message}
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={feedEndRef} className="h-4"></div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
