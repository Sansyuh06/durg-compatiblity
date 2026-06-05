"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Activity, RefreshCw, Shield, 
  Search, FileText, Microscope, BookOpen,
  AlertTriangle
} from "lucide-react";

type TaskLevel = "easy" | "medium" | "hard";

interface ActionResponse {
  observation: { step_number: number; drug_name: string; episode_done: boolean; current_output?: { message?: string; source?: string; error?: string; data?: Record<string, unknown>; hint?: string; }; };
  reward: { value: number; message: string; breakdown?: Record<string, number>; };
  info: { steps_remaining: number; max_steps: number; };
  action_type?: string; parameters?: Record<string, unknown>; done?: boolean;
}

const AsciiProteinBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const chars = " .,:;=|iI+hHOE#X@".split(""); 
    
    // Generate an alpha helix folded protein path
    // Geometry: True Beta Barrel (GFP / Green Fluorescent Protein)
    interface ProteinPoint {
      baseX: number; baseY: number; baseZ: number;
      x: number; y: number; z: number;
      vx: number; vy: number; vz: number;
      char: string;
      isText: boolean;
      isSparkle: boolean;
      colorType: string;
    }
    const points: ProteinPoint[] = [];
    const numStrands = 11;
    const strandLength = 550; // Massively increased structure height
    const barrelRadius = 280; // Massively increased barrel radius
    const twistRate = 0.8; // The barrel twists slightly from bottom to top

    // 1. Beta Strands (The outer cylindrical cage of wide ribbons)
    for (let s = 0; s < numStrands; s++) {
        const theta = (s / numStrands) * Math.PI * 2;
        
        const numSteps = 100; // Further reduced for ultra-smooth 60fps
        for (let i = 0; i < numSteps; i++) {
            const t = (i / numSteps) - 0.5; // -0.5 to 0.5
            const y = t * strandLength;
            
            const currentTheta = theta + t * twistRate;
            const bx = Math.cos(currentTheta) * barrelRadius;
            const bz = Math.sin(currentTheta) * barrelRadius;
            
            // Sweep points across the tangent to create wide, flat Beta Sheets
            for (let w = -1; w <= 1; w++) { // 3 points per step
                 const ribbonWidth = 14; 
                 const wx = w * ribbonWidth * -Math.sin(currentTheta);
                 const wz = w * ribbonWidth * Math.cos(currentTheta);
                 
                 const x = bx + wx;
                 const z = bz + wz;
                 
                 points.push({
                     baseX: x, baseY: y, baseZ: z,
                     x: x, y: y, z: z,
                     vx: 0, vy: 0, vz: 0,
                     char: chars[Math.floor(Math.random() * chars.length)],
                     isText: Math.random() > 0.6, // 40% Text, 60% fast dots
                     isSparkle: Math.random() > 0.98,
                     colorType: 'strand' 
                 });
            }
        }
    }

    // 2. Connecting Loops (Thin strings connecting the strands at the top/bottom)
    const loopPoints = 100; // Drastically reduced for 60fps
    for (let s = 0; s < numStrands; s++) {
        const isTop = s % 2 === 0;
        const theta1 = (s / numStrands) * Math.PI * 2;
        const theta2 = ((s + 1) / numStrands) * Math.PI * 2;
        
        const tEnd = isTop ? 0.5 : -0.5;
        const currentTheta1 = theta1 + tEnd * twistRate;
        const currentTheta2 = theta2 + tEnd * twistRate;
        
        const x1 = Math.cos(currentTheta1) * barrelRadius;
        const z1 = Math.sin(currentTheta1) * barrelRadius;
        const y1 = tEnd * strandLength;
        
        const x2 = Math.cos(currentTheta2) * barrelRadius;
        const z2 = Math.sin(currentTheta2) * barrelRadius;
        const y2 = tEnd * strandLength;
        
        // Bezier curve bulging outward to connect them
        const midTheta = (currentTheta1 + currentTheta2) / 2;
        const loopRadius = barrelRadius + 40 + Math.random() * 40; 
        const cpX = Math.cos(midTheta) * loopRadius;
        const cpZ = Math.sin(midTheta) * loopRadius;
        const cpY = y1 + (isTop ? 80 : -80); 
        
        for (let i = 0; i < loopPoints; i++) {
            const lt = i / loopPoints;
            const omt = 1 - lt;
            
            const bx = omt*omt*x1 + 2*omt*lt*cpX + lt*lt*x2;
            const by = omt*omt*y1 + 2*omt*lt*cpY + lt*lt*y2;
            const bz = omt*omt*z1 + 2*omt*lt*cpZ + lt*lt*z2;
            
            points.push({
                 baseX: bx, baseY: by, baseZ: bz,
                 x: bx, y: by, z: bz,
                 vx: 0, vy: 0, vz: 0,
                 char: chars[Math.floor(Math.random() * chars.length)],
                 isText: Math.random() > 0.5, 
                 isSparkle: Math.random() > 0.98,
                 colorType: 'loop'
            });
        }
    }

    // 3. Central Chromophore (The dense, glowing core molecule)
    const corePoints = 400; // Further reduced for performance
    for (let i = 0; i < corePoints; i++) {
        const t = (i / corePoints) * Math.PI * 6;
        const bx = Math.sin(t * 3) * 80; // Scaled up core
        const by = (t / (Math.PI*6) - 0.5) * 220; // Scaled up core
        const bz = Math.cos(t * 2) * 80; // Scaled up core
        
        // Thicken the core
        for(let j=0; j<3; j++) {
            const rx = (Math.random() - 0.5) * 30;
            const ry = (Math.random() - 0.5) * 30;
            const rz = (Math.random() - 0.5) * 30;
            points.push({
                 baseX: bx + rx, baseY: by + ry, baseZ: bz + rz,
                 x: bx + rx, y: by + ry, z: bz + rz,
                 vx: 0, vy: 0, vz: 0,
                 char: chars[Math.floor(Math.random() * chars.length)],
                 isText: true, // 100% text for the glowing core
                 isSparkle: Math.random() > 0.8, // Heavy sparkle
                 colorType: 'core'
            });
        }
    }

    let mouseX = width / 2;
    let mouseY = height / 2;
    
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };
    
    const handleClick = (e: MouseEvent) => {
      const mx = e.clientX;
      const my = e.clientY;
      const cx = width / 2;
      const cy = height / 2;
      
      points.forEach(p => {
        // Approximate 2D screen pos (no rotation for calculation speed)
        const screenX = cx + p.x;
        const screenY = cy + p.y;
        
        const dist = Math.hypot(screenX - mx, screenY - my);
        if (dist < 400) {
          const force = (400 - dist) / 10;
          const angle = Math.atan2(screenY - my, screenX - mx);
          p.vx += Math.cos(angle) * force * 4;
          p.vy += Math.sin(angle) * force * 4;
          p.vz += (Math.random() - 0.5) * force * 5;
        }
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('click', handleClick);

    let time = 0;
    
    // Pre-calculate Multi-Color Depth Palettes to match the GFP reference image
    const buildDepthArray = (r: number, g: number, b: number) => Array.from({length: 20}, (_, i) => {
        const normalizedZ = i / 19;
        const alpha = 0.05 + (1 - normalizedZ) * 0.95;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    });

    const depthPalettes: Record<string, string[]> = {
        strand: buildDepthArray(56, 189, 248), // Sky Blue / Cyan for the beta sheets
        loop: buildDepthArray(192, 132, 252),  // Purple for the connecting loops
        core: buildDepthArray(74, 222, 128)    // Vibrant Green for the chromophore core
    };

    const draw = () => {
      ctx.fillStyle = '#03060f'; 
      ctx.fillRect(0, 0, width, height);
      ctx.font = '11px "IBM Plex Mono", monospace'; // Crisp, readable ASCII text size
      
      const cx = width / 2;
      const cy = height / 2;
      
      const targetRotX = (mouseY - cy) * 0.002;
      const targetRotY = (mouseX - cx) * 0.002;

      time += 0.005;

      // OPTIMIZATION: Precalculate sine/cosine for the entire frame!
      const rotX = time + targetRotX;
      const rotY = time * 0.5 + targetRotY;
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      points.forEach(p => {
        // Spring physics
        p.vx += (p.baseX - p.x) * 0.03;
        p.vy += (p.baseY - p.y) * 0.03;
        p.vz += (p.baseZ - p.z) * 0.03;
        
        p.vx *= 0.85; 
        p.vy *= 0.85;
        p.vz *= 0.85;
        
        p.x += p.vx;
        p.y += p.vy;
        p.z += p.vz;

        // Apply fast pre-calculated rotation
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.z * cosY + p.x * sinY;
        const y2 = p.y * cosX - z1 * sinX;
        const z2 = z1 * cosX + p.y * sinX;

        const fov = 1000;
        const zScale = fov / (fov + z2 + 400); 
        
        const screenX = cx + x1 * zScale;
        const screenY = cy + y2 * zScale;

        if (screenY < 0 || screenY > height || screenX < 0 || screenX > width) return;

        // OPTIMIZATION: Fast bucketed Z-depth colors from the multi-color palette
        const zBucket = Math.max(0, Math.min(19, Math.floor((z2 + 400) / 40)));
        ctx.fillStyle = p.isSparkle ? '#ffffff' : depthPalettes[p.colorType][zBucket];
        
        // Fast rendering: mix text and dots based on pre-calc
        if (p.isText) {
          ctx.fillText(p.char, screenX, screenY);
        } else {
          ctx.fillRect(screenX, screenY, 1.5, 1.5);
        }
      });

      requestAnimationFrame(draw);
    };

    const animId = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('click', handleClick);
      cancelAnimationFrame(animId);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0 opacity-80" />;
};

const HandDrawnLogo = ({ className = "w-[120px] h-[150px] mx-auto mb-6 opacity-90 drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]" }: { className?: string }) => (
  <svg viewBox="0 0 120 150" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    {/* Middle Yellow Fold */}
    <polygon points="15,65 95,45 105,65 25,85" fill="#fef08a" stroke="white" strokeWidth="4" strokeLinejoin="round" />
    <path d="M 25 70 L 90 53 M 30 75 L 85 60 M 40 80 L 80 67" stroke="#fde047" strokeWidth="2" strokeLinecap="round" />

    {/* Top Blue Fold */}
    <polygon points="10,25 100,5 95,45 15,65" fill="#bfdbfe" stroke="white" strokeWidth="4" strokeLinejoin="round" />
    <path d="M 15 35 L 90 15 M 20 45 L 85 25 M 25 55 L 80 35 M 12 45 L 60 20 M 30 60 L 95 35 M 40 25 L 80 15" stroke="#93c5fd" strokeWidth="2" strokeLinecap="round" />

    {/* Bottom Green Fold */}
    <polygon points="25,85 105,65 100,105 20,125" fill="#bbf7d0" stroke="white" strokeWidth="4" strokeLinejoin="round" />
    <path d="M 30 95 L 95 75 M 35 105 L 90 85 M 40 115 L 85 95 M 25 105 L 70 80 M 40 120 L 95 100 M 70 115 L 100 95" stroke="#86efac" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const AnimatedHandDrawnLogo = () => (
  <div className="flex flex-col items-center justify-center">
    <svg width="200" height="250" viewBox="0 0 120 150" fill="none" xmlns="http://www.w3.org/2000/svg" className="mx-auto mb-6 opacity-90 drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]">
      {/* Background fills fade in slightly later */}
      <motion.polygon 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 1 }}
        points="15,65 95,45 105,65 25,85" fill="#fef08a" stroke="none" 
      />
      <motion.polygon 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 1 }}
        points="10,25 100,5 95,45 15,65" fill="#bfdbfe" stroke="none" 
      />
      <motion.polygon 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 1 }}
        points="25,85 105,65 100,105 20,125" fill="#bbf7d0" stroke="none" 
      />

      {/* Scribble lines animate drawing */}
      <motion.path 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, ease: "easeInOut" }}
        d="M 25 70 L 90 53 M 30 75 L 85 60 M 40 80 L 80 67" stroke="#eab308" strokeWidth="3" strokeLinecap="round" 
      />
      <motion.path 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
        d="M 15 35 L 90 15 M 20 45 L 85 25 M 25 55 L 80 35 M 12 45 L 60 20 M 30 60 L 95 35 M 40 25 L 80 15" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" 
      />
      <motion.path 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, ease: "easeInOut", delay: 0.4 }}
        d="M 30 95 L 95 75 M 35 105 L 90 85 M 40 115 L 85 95 M 25 105 L 70 80 M 40 120 L 95 100 M 70 115 L 100 95" stroke="#22c55e" strokeWidth="3" strokeLinecap="round" 
      />

      {/* Outlines animate drawing */}
      <motion.polygon 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1, ease: "easeInOut", delay: 0.5 }}
        points="15,65 95,45 105,65 25,85" fill="none" stroke="white" strokeWidth="4" strokeLinejoin="round" 
      />
      <motion.polygon 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1, ease: "easeInOut", delay: 0.6 }}
        points="10,25 100,5 95,45 15,65" fill="none" stroke="white" strokeWidth="4" strokeLinejoin="round" 
      />
      <motion.polygon 
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1, ease: "easeInOut", delay: 0.7 }}
        points="25,85 105,65 100,105 20,125" fill="none" stroke="white" strokeWidth="4" strokeLinejoin="round" 
      />
    </svg>
    
    <motion.h1 
      initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, delay: 1 }}
      className="text-6xl text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]"
      style={{ fontFamily: '"Dirty Enough", cursive' }}
    >
      Foldables
    </motion.h1>
  </div>
);

export default function Home() {
  const [activeMainTab, setActiveMainTab] = useState<"home" | "discovery" | "simulation" | "pharmacovigilance" | "legacy_pv">("home");
  const [activeStep, setActiveStep] = useState<string>("1");
  const [currentTask] = useState<TaskLevel>("easy");
  const [episodeActive, setEpisodeActive] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("IDLE");
  const [feed, setFeed] = useState<Record<string, unknown>[]>([]);
  
  const [stats, setStats] = useState({ episodes: 0, actions: 0, bestScore: null as null | number });
  const [currentScore, setCurrentScore] = useState<number | null>(null);
  const [breakdown, setBreakdown] = useState<Record<string, number> | null>(null);
  const [steps, setSteps] = useState({ current: 0, remaining: 0, max: 0 });

  const [submitFormOpen, setSubmitFormOpen] = useState(false);
  const [submitData, setSubmitData] = useState({ drug_name: '', primary_signal: '', secondary_signal: '', regulatory_action: 'monitor' });
  const [caseDrug, setCaseDrug] = useState("—");

  const feedEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [feed]);

  const addLog = (comp: Record<string, unknown>) => setFeed(f => [...f, comp]);

  const hitApi = async (url: string, body?: Record<string, unknown>) => {
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
      setCaseDrug(obs.drug_name || "—");
      addLog({ type: 'reset', data: obs, id: Date.now() });
    } catch (e: unknown) {
      const error = e as Error;
      alert("Reset failed: " + error.message); setStatusText("ERROR");
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
    } catch (e: unknown) {
      const error = e as Error;
      addLog({ type: 'error', message: error.message, id: Date.now() });
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
      
      setCurrentScore(reward.value); setBreakdown(reward.breakdown || null);
      if (stats.bestScore === null || reward.value > stats.bestScore) setStats(s => ({ ...s, bestScore: reward.value }));
      handleDone(reward.value);

      addLog({ type: 'submit', param: submitData, score: reward.value, message: reward.message, id: Date.now() });
    } catch (e: unknown) { 
      const error = e as Error;
      alert("Submit failed: " + error.message); 
    } finally { setLoading(false); }
  };

  /* 
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

        if (action_type === 'reset' && step.data && step.data.drug_name) {
             setCaseDrug(step.data.drug_name);
        }

        if (action_type !== 'submit') {
          addLog({ type: 'action', actionType: action_type, step: obs.step_number, output: obs.current_output, reward: reward.value, remaining: info.steps_remaining, id: Date.now() + Math.random() });
        } else {
          setCurrentScore(reward.value); setBreakdown(reward.breakdown); finalSc = reward.value;
          if (stats.bestScore === null || reward.value > stats.bestScore) setStats(s => ({ ...s, bestScore: reward.value }));
          addLog({ type: 'submit', param: step.parameters, score: reward.value, message: reward.message, id: Date.now() + Math.random() });
        }
      }
      handleDone(finalSc);
    } catch (e: any) { alert("Demo failed: " + e.message); setStatusText("ERROR"); } finally { setLoading(false); }
  };
  */

  const handleDone = (score: number) => { setIsDone(true); setEpisodeActive(false); setStatusText(`DONE • ${score >= 0.7 ? 'SUCCESS' : 'FAILED'}`); };

  const getIcon = (type: string) => {
    switch(type) {
      case 'search_faers': return <Search size={16} />;
      case 'fetch_label': return <FileText size={16} />;
      case 'analyze_signal': return <Activity size={16} />;
      case 'lookup_mechanism': return <Microscope size={16} />;
      case 'check_literature': return <BookOpen size={16} />;
      default: return <Shield size={16} />;
    }
  };

  const renderRichData = (data: Record<string, unknown>) => {
    if (!data || typeof data !== 'object') return <span className="text-secondary">{String(data)}</span>;
    const metrics = ['PRR', 'ROR', 'EB05', 'IC025', 'prr', 'ror'];
    const hasMetrics = Object.keys(data).some(k => metrics.includes(k) && typeof data[k] === 'number');

    return (
      <div className="mt-3 flex flex-col gap-0">
        {hasMetrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
            {Object.keys(data).filter(k => metrics.includes(k) || typeof data[k] === 'number').map(k => (
              <div key={k} className="bg-[#ffffff05] border border-[#ffffff0f] rounded-[4px] p-[10px_12px]">
                <div className="font-mono text-[9px] text-muted uppercase tracking-[0.1em] mb-1">{k.replace(/_/g, ' ')}</div>
                <div className="font-mono text-[16px] font-medium text-cyan-accent">{Number(data[k]).toFixed(2)}</div>
              </div>
            ))}
          </div>
        )}
        
        {Object.keys(data).filter(k => !hasMetrics || (!metrics.includes(k) && typeof data[k] !== 'number')).map(k => {
          const val = data[k];
          const isString = typeof val === 'string';
          const isArray = Array.isArray(val);
          return (
            <div key={k} className="flex flex-row gap-4 border-t border-[#ffffff0a] py-2">
              <div className="font-mono text-[9px] text-muted uppercase tracking-[0.08em] min-w-[120px] shrink-0 pt-0.5">{k.replace(/_/g,' ')}</div>
              <div className="font-sans text-[13px] text-secondary flex-1">
                {isString ? (
                  <span className={val.length < 40 && val === val.toUpperCase() ? "tag" : ""}>{val}</span>
                ) : isArray ? (
                  <div className="flex flex-col gap-1">
                    {val.slice(0,3).map((item, i) => (
                      <div key={i} className="font-mono text-[11px] bg-[rgba(0,0,0,0.4)] border border-[#ffffff0d] rounded-[3px] px-[10px] py-[6px] max-w-full overflow-hidden text-ellipsis">
                        {typeof item === 'object' ? JSON.stringify(item).substring(0,120) + (JSON.stringify(item).length > 120 ? '...' : '') : String(item)}
                      </div>
                    ))}
                    {val.length > 3 && <div className="font-mono text-[9px] text-muted mt-1">+ {val.length - 3} more</div>}
                  </div>
                ) : typeof val === 'object' && val !== null ? (
                  <pre className="font-mono text-[11px] bg-[rgba(0,0,0,0.5)] border border-[#ffffff0d] rounded-[4px] p-[10px] max-h-[160px] overflow-y-auto text-[rgba(0,212,230,0.7)] whitespace-pre-wrap">
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

  interface ActionButtonProps {
    title: string;
    desc: string;
    type: string;
    onClick: () => void;
  }
  const ActionButton = ({ title, desc, type, onClick }: ActionButtonProps) => {
    const disabled = !episodeActive || loading || isDone;
    const isSubmit = type === 'submit';
    
    return (
      <button 
        onClick={onClick} 
        disabled={disabled}
        className={`h-[44px] flex items-center gap-3 px-3.5 rounded-[4px] transition-all duration-150 w-full text-left
          ${disabled ? 'opacity-25 cursor-not-allowed border border-transparent bg-transparent' : 
            isSubmit 
              ? 'border border-[rgba(0,212,230,0.2)] hover:border-[rgba(0,212,230,0.4)] hover:bg-[rgba(0,212,230,0.04)] bg-transparent' 
              : 'border border-transparent bg-transparent hover:bg-[rgba(255,255,255,0.03)] hover:border-[rgba(255,255,255,0.08)]'
          }
        `}
      >
        <div className="w-7 h-7 bg-[rgba(255,255,255,0.03)] border border-[#ffffff0f] rounded-[3px] flex items-center justify-center shrink-0">
          {getIcon(type)}
        </div>
        <div className="flex flex-col flex-1">
          <div className={`font-sans text-[13px] font-medium leading-tight ${isSubmit ? 'text-cyan-accent' : 'text-primary'}`}>{title}</div>
          <div className="font-mono text-[10px] text-muted mt-0.5">{desc}</div>
        </div>
        {isSubmit && <div className="font-mono text-[14px] text-cyan-accent ml-auto">→</div>}
      </button>
    );
  };

  return (
    <div className="relative min-h-screen bg-[#03060f]">
      
      {/* Full-screen Loading Animation Overlay */}
      <AnimatePresence>
        {loading && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#03060f]/95 backdrop-blur-md"
          >
            <AnimatedHandDrawnLogo />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ATMOSPHERIC BACKGROUND (PRISMA HERO STYLE) */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden flex items-start justify-center">
        {/* Soft cyan radial glow in top center */}
        <div className="absolute top-[-30%] w-[100vw] h-[70vh] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(0,212,230,0.15)_0%,transparent_70%)] blur-[80px]"></div>
        {/* Warm purple/magenta radial glow in bottom right for contrast */}
        <div className="absolute bottom-[-10%] right-[-10%] w-[60vw] h-[60vh] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(168,85,247,0.12)_0%,transparent_70%)] blur-[100px]"></div>
      </div>

      {/* 4.2 HEADER BAR -> FLOATING PILL */}
      <div className="fixed top-6 left-0 right-0 z-50 flex justify-center pointer-events-none px-4">
      <motion.header 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="pointer-events-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-8 px-6 py-2 rounded-full bg-[#0a0f1a]/70 backdrop-blur-2xl border border-white/10 shadow-[0_8_32px_rgba(0,0,0,0.5),0_0_40px_rgba(0,212,230,0.1)] w-full max-w-6xl"
      >
        {/* Left section */}
        <div className="flex items-center gap-4 pl-0">
          <div className="flex items-center gap-3">
            <HandDrawnLogo className="w-[30px] h-[38px] drop-shadow-[0_0_6px_rgba(255,255,255,0.3)] shrink-0" />
            <div className="flex flex-col justify-center">
              <div 
                className="text-[20px] text-white leading-none mb-1 translate-y-[2px]" 
                style={{ fontFamily: '"Dirty Enough", cursive' }}
              >
                Foldables
              </div>
              <div className="font-mono text-[9px] tracking-[0.15em] text-[#3a5070] leading-none">PHARMACOVIGILANCE</div>
            </div>
          </div>
          
          <div className="w-[1px] h-[20px] bg-white/10 mx-2 hidden sm:block"></div>
          
          <div className="hidden sm:flex items-center gap-1">
            <button 
              onClick={() => setActiveMainTab('home')}
              className={`px-4 py-1.5 rounded-full font-sans text-[11px] font-semibold tracking-[0.05em] transition-all duration-300 ${activeMainTab === 'home' ? 'bg-[#e8f0fe] text-[#03060f] shadow-[0_0_15px_rgba(255,255,255,0.3)]' : 'text-[#7090b0] hover:text-[#e8f0fe] bg-transparent'}`}
            >
              HOME
            </button>
            <button 
              onClick={() => setActiveMainTab('discovery')}
              className={`px-4 py-1.5 rounded-full font-sans text-[11px] font-semibold tracking-[0.05em] transition-all duration-300 ${activeMainTab === 'discovery' ? 'bg-[#e8f0fe] text-[#03060f] shadow-[0_0_15px_rgba(255,255,255,0.3)]' : 'text-[#7090b0] hover:text-[#e8f0fe] bg-transparent'}`}
            >
              DISCOVERY
            </button>
            <button 
              onClick={() => setActiveMainTab('simulation')}
              className={`px-4 py-1.5 rounded-full font-sans text-[11px] font-semibold tracking-[0.05em] transition-all duration-300 ${activeMainTab === 'simulation' ? 'bg-[#e8f0fe] text-[#03060f] shadow-[0_0_15px_rgba(255,255,255,0.3)]' : 'text-[#7090b0] hover:text-[#e8f0fe] bg-transparent'}`}
            >
              SIMULATION
            </button>
            <button 
              onClick={() => setActiveMainTab('pharmacovigilance')}
              className={`px-4 py-1.5 rounded-full font-sans text-[11px] font-semibold tracking-[0.05em] transition-all duration-300 ${activeMainTab === 'pharmacovigilance' ? 'bg-[#e8f0fe] text-[#03060f] shadow-[0_0_15px_rgba(255,255,255,0.3)]' : 'text-[#7090b0] hover:text-[#e8f0fe] bg-transparent'}`}
            >
              PHARMACOVIGILANCE
            </button>
          </div>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-5 flex-wrap justify-between md:justify-end">
          {episodeActive && (
            <div className="font-mono text-[11px] text-[#7090b0]">
              STEP {steps.current}/{steps.max}
            </div>
          )}

          <div className="flex items-center gap-2">
            <button 
              onClick={handleReset} 
              disabled={loading}
              className={`h-[32px] px-4 rounded-[3px] bg-[#00d4e6] text-[#03060f] font-mono text-[11px] font-semibold tracking-[0.08em] flex items-center justify-center gap-2 transition-colors
                ${loading && statusText !== 'DEMO' ? 'opacity-90' : 'hover:bg-[#00a8b8]'}
                ${loading ? 'opacity-40 cursor-not-allowed' : ''}
              `}
            >
              {loading && statusText !== 'DEMO' && <RefreshCw className="w-3 h-3 animate-spin" />}
              NEW EPISODE
            </button>
          </div>
        </div>
      </motion.header>
      </div>

      {activeMainTab === 'home' && (
        <div className="absolute inset-0 z-10 overflow-y-auto overflow-x-hidden pointer-events-auto scroll-smooth pb-32">
          <AsciiProteinBackground />
          
          {/* HERO SECTION - ascendmarketing.xyz style */}
          <div className="relative z-10 w-full min-h-[100vh] flex flex-col items-center justify-center text-center px-4 pointer-events-none">
             <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}>
               <HandDrawnLogo />
               <h1 
                 className="text-white text-6xl md:text-8xl lg:text-[130px] mb-4 drop-shadow-[0_0_20px_rgba(255,255,255,0.4)] pointer-events-auto leading-none"
                 style={{ fontFamily: '"Dirty Enough", cursive' }}
               >
                 Foldables
               </h1>
               <p className="text-white/80 font-mono text-[13px] tracking-[0.4em] uppercase mt-4">PHARMACOVIGILANCE SIGNAL TRIAGE</p>
             </motion.div>
             <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 1, duration: 1 }}
                className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4"
             >
               <div className="text-[10px] font-mono tracking-widest">SCROLL</div>
               <div className="w-[1px] h-12 bg-gradient-to-b from-white to-transparent"></div>
             </motion.div>
          </div>

          {/* SCROLLING ARCHITECTURE - ONE MASSIVE LIQUID GLASS PLANE */}
          <div className="relative z-10 w-full max-w-[1500px] mx-auto px-6 pb-40">
             <motion.div 
               initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-100px" }} transition={{ duration: 0.8 }}
               className="relative w-full rounded-[40px] p-8 md:p-14 
               backdrop-blur-[40px] bg-gradient-to-br from-white/[0.08] to-white/[0.01] 
               border-t border-l border-white/[0.2] border-r border-b border-white/[0.05]
               shadow-[inset_0_0_80px_rgba(255,255,255,0.03),0_50px_100px_rgba(0,0,0,0.8)]
               overflow-hidden pointer-events-auto"
             >
               {/* Inner Noise */}
               <div className="absolute inset-0 opacity-20 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}></div>
               
               <div className="relative z-10 w-full mb-12 border-b border-white/10 pb-6 flex flex-col md:flex-row justify-between items-start md:items-end">
                 <h2 className="text-white text-3xl md:text-5xl font-sans font-light tracking-tight">Architecture Overview</h2>
                 <div className="mt-4 md:mt-0 text-white/40 font-mono text-xs tracking-widest">13-STAGE VERDICT</div>
               </div>
               
               <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4 auto-rows-[130px]">
                {[
                  { step: '1', title: 'MOLECULAR DOCKING', mode: 'discovery', desc: 'Quantum-accelerated ligand binding analysis.' },
                  { step: '2', title: 'IN VIVO BRAIN SIMULATION', mode: 'simulation', desc: '3D Neural activation mapping.' },
                  { step: '3', title: 'PHARMACOGENOMIC PATHWAY', mode: 'discovery', desc: 'Metabolic pathway tracing.' },
                  { step: '4', title: 'ADME & HEPATOTOXICITY', mode: 'discovery', desc: 'Liver enzyme inhibition risks.' },
                  { step: '5', title: 'OFF-TARGET COLLISION', mode: 'discovery', desc: 'Receptor selectivity matrix.' },
                  { step: '6', title: 'SYSTEMIC CASCADE', mode: 'discovery', desc: 'Downstream biological impact.' },
                  { step: '6.5', title: 'PROTEIN-LIGAND DOCKING', mode: 'simulation', desc: 'High-resolution conformational shifts.' },
                  { step: '7', title: 'MULTI-DRUG INTERACTION', mode: 'discovery', desc: 'CYP450 competitive binding.' },
                  { step: '8', title: 'LIVE BIOMARKER TIMELINE', mode: 'legacy_pv', desc: 'Real-time patient serum levels.' },
                  { step: '9', title: 'DRUG REPURPOSING', mode: 'legacy_pv', desc: 'Off-label condition scanning.' },
                  { step: '10', title: 'GENETIC ANCESTRY', mode: 'legacy_pv', desc: 'Population-specific allele variations.' },
                  { step: '11', title: 'PERSONALIZED DOSE', mode: 'legacy_pv', desc: 'PK/PD modeling for exact dosing.' },
                  { step: 'FINAL', title: 'RL DOSING VERDICT', mode: 'legacy_pv', desc: 'AI-driven therapeutic recommendation.', colSpan: 'lg:col-span-2 xl:col-span-3' },
                ].map((item) => (
                    <div 
                      key={item.step}
                      onClick={() => { setActiveMainTab(item.mode as "home" | "discovery" | "simulation" | "pharmacovigilance" | "legacy_pv"); setActiveStep(item.step); }}
                      className={`relative group cursor-pointer transition-all duration-500 rounded-[20px] border border-white/[0.05] bg-white/[0.02] hover:bg-white/[0.08] hover:border-white/[0.15] hover:shadow-[0_10px_30px_rgba(0,0,0,0.5)] overflow-hidden ${item.colSpan || ''}`}
                    >
                      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.05] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                      <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center z-10 pointer-events-none">
                         <div className="font-mono text-[9px] tracking-[0.2em] mb-1 opacity-40 group-hover:opacity-100 transition-opacity duration-500 text-white">STEP {item.step}</div>
                         <div className="text-white text-[11px] md:text-[12px] font-sans font-semibold tracking-wide opacity-80 group-hover:opacity-100 group-hover:scale-[1.02] transition-all duration-500">{item.title}</div>
                         <div className="text-white/40 text-[10px] font-sans mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-100">{item.desc}</div>
                      </div>
                    </div>
                  ))}
               </div>
             </motion.div>
          </div>
        </div>
      )}

      {activeMainTab === 'discovery' && (
        <iframe src={`/quantamed?mode=quantamed&step=${activeStep}`} style={{ width: '100%', height: 'calc(100vh - 52px)', border: 'none' }} />
      )}
      
      {activeMainTab === 'simulation' && (
        <iframe src={`/quantamed?mode=protein&step=${activeStep}`} style={{ width: '100%', height: 'calc(100vh - 52px)', border: 'none' }} />
      )}

      {activeMainTab === 'legacy_pv' && (
        <iframe src={`/quantamed?mode=triage&step=${activeStep}`} style={{ width: '100%', height: 'calc(100vh - 52px)', border: 'none' }} />
      )}

      {activeMainTab === 'pharmacovigilance' && (
      <main className="flex-1 w-full max-w-[1800px] mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)_340px] gap-6 overflow-hidden">
        
        {/* LEFT COLUMN - CASE SELECTION */}
        <div className="flex flex-col gap-4">
          
          {/* 4.4.1 MISSION CARD */}
          <div className="panel panel-accent p-4">
            <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.12em]">ACTIVE CASE</div>
            <div className="font-sans text-[20px] font-semibold text-[#e8f0fe] mt-1 mb-3">{caseDrug}</div>
            <div className="flex flex-row gap-2">
              <div className="flex flex-col bg-[rgba(255,255,255,0.02)] border border-[#ffffff0d] rounded-[3px] px-3 py-2 flex-1">
                <div className="font-mono text-[9px] text-[#3a5070]">TASK</div>
                <div className="font-mono text-[13px] font-medium text-[#e8f0fe]">{currentTask.toUpperCase()}</div>
              </div>
              <div className="flex flex-col bg-[rgba(255,255,255,0.02)] border border-[#ffffff0d] rounded-[3px] px-3 py-2 flex-1">
                <div className="font-mono text-[9px] text-[#3a5070]">STEPS LEFT</div>
                <div className="font-mono text-[13px] font-medium text-[#e8f0fe]">{steps.remaining}</div>
              </div>
            </div>
          </div>

          {/* 4.4.2 INVESTIGATION TOOLS */}
          <div>
            <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.12em] mb-[10px]">INVESTIGATION TOOLS</div>
            <div className="flex flex-col gap-[2px]">
              <ActionButton title="Search FAERS" desc="Query adverse event database" type="search_faers" onClick={()=>handleAction('search_faers')} />
              <ActionButton title="Fetch Label" desc="Retrieve FDA drug labeling" type="fetch_label" onClick={()=>handleAction('fetch_label')} />
              <ActionButton title="Analyze Signal" desc="Compute PRR, ROR, EB05" type="analyze_signal" onClick={()=>handleAction('analyze_signal')} />
              <ActionButton title="Lookup Mechanism" desc="Pharmacology & pathophysiology" type="lookup_mechanism" onClick={()=>handleAction('lookup_mechanism')} />
              <ActionButton title="Check Literature" desc="Published safety evidence" type="check_literature" onClick={()=>handleAction('check_literature')} />
              <ActionButton title="Submit Assessment" desc="File regulatory decision" type="submit" onClick={()=>setSubmitFormOpen(p=>!p)} />
            </div>
          </div>

          {/* 4.4.3 SUBMIT FORM */}
          <AnimatePresence>
            {submitFormOpen && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="panel p-4 mt-1"
              >
                <div className="font-mono text-[9px] text-[#00d4e6] uppercase tracking-[0.12em] mb-3">REGULATORY ASSESSMENT FORM</div>
                <form onSubmit={handleSubmit} className="flex flex-col gap-2">
                  <input placeholder="Drug name *" value={submitData.drug_name} onChange={e=>setSubmitData({...submitData, drug_name: e.target.value})} required 
                    className="h-[36px] px-3 bg-[rgba(0,0,0,0.4)] border border-[#ffffff14] rounded-[4px] font-sans text-[13px] text-[#e8f0fe] placeholder-[#3a5070] focus:border-[rgba(0,212,230,0.4)] focus:bg-[rgba(0,212,230,0.03)] focus:outline-none transition-colors" />
                  
                  <input placeholder="Primary safety signal *" value={submitData.primary_signal} onChange={e=>setSubmitData({...submitData, primary_signal: e.target.value})} required 
                    className="h-[36px] px-3 bg-[rgba(0,0,0,0.4)] border border-[#ffffff14] rounded-[4px] font-sans text-[13px] text-[#e8f0fe] placeholder-[#3a5070] focus:border-[rgba(0,212,230,0.4)] focus:bg-[rgba(0,212,230,0.03)] focus:outline-none transition-colors" />
                  
                  {currentTask === 'hard' && (
                    <input placeholder="Secondary signal (optional)" value={submitData.secondary_signal} onChange={e=>setSubmitData({...submitData, secondary_signal: e.target.value})} 
                      className="h-[36px] px-3 bg-[rgba(0,0,0,0.4)] border border-[#ffffff14] rounded-[4px] font-sans text-[13px] text-[#e8f0fe] placeholder-[#3a5070] focus:border-[rgba(0,212,230,0.4)] focus:bg-[rgba(0,212,230,0.03)] focus:outline-none transition-colors" />
                  )}

                  <div className="relative">
                    <select value={submitData.regulatory_action} onChange={e=>setSubmitData({...submitData, regulatory_action: e.target.value})} 
                      className="w-full h-[36px] px-3 bg-[rgba(0,0,0,0.4)] border border-[#ffffff14] rounded-[4px] font-sans text-[13px] text-[#e8f0fe] focus:border-[rgba(0,212,230,0.4)] focus:bg-[rgba(0,212,230,0.03)] focus:outline-none transition-colors appearance-none"
                    >
                      <option value="monitor">Monitor — Enhanced Surveillance</option>
                      <option value="restrict">Restrict — REMS / iPLEDGE</option>
                      <option value="withdraw">Withdraw — Market Removal</option>
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[#3a5070] font-mono text-[10px]">▾</div>
                  </div>

                  <button type="submit" 
                    className="w-full h-[36px] mt-1 bg-[#00d4e6] hover:bg-[#00a8b8] text-[#03060f] font-mono text-[11px] font-semibold tracking-[0.08em] rounded-[4px] transition-colors"
                  >
                    SUBMIT DECISION →
                  </button>
                </form>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 4.4.4 SCORE PANEL */}
          <AnimatePresence>
            {breakdown && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: 0.1 }}
                className="panel p-5 mt-1"
              >
                <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.12em]">ASSESSMENT SCORE</div>
                <div 
                  className={`font-mono text-[48px] font-semibold leading-[1.1] my-2 ${currentScore! >= 0.7 ? 'text-[#00d4a0]' : currentScore! >= 0.5 ? 'text-[#e8a020]' : 'text-[#e04060]'}`}
                  style={{ animation: 'score-reveal 0.4s ease' }}
                >
                  {currentScore!.toFixed(2)}
                </div>
                
                <div className="w-full h-[3px] rounded-[2px] bg-[rgba(255,255,255,0.05)] mt-1 mb-4 overflow-hidden relative">
                  <div 
                    className="h-full transition-all duration-800 ease-in-out" 
                    style={{ 
                      width: `${Math.max(0, Math.min(100, currentScore! * 100))}%`,
                      backgroundColor: currentScore! >= 0.7 ? '#00d4a0' : currentScore! >= 0.5 ? '#e8a020' : '#e04060'
                    }}
                  ></div>
                </div>

                <div className="mt-[14px]">
                  <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.12em] mb-2">BREAKDOWN</div>
                  {Object.keys(breakdown).map((k) => (
                    <div key={k} className="flex justify-between border-t border-[#ffffff0a] py-2">
                      <div className="font-sans text-[12px] text-[#7090b0]">{k.replace(/_/g, ' ')}</div>
                      <div className={`font-mono text-[12px] font-medium ${breakdown[k] > 0 ? 'text-[#00d4a0]' : breakdown[k] < 0 ? 'text-[#e04060]' : 'text-[#3a5070]'}`}>
                        {breakdown[k] > 0 ? '+' : ''}{breakdown[k].toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* 4.5 RIGHT COLUMN */}
        <div className="flex flex-col gap-0">
          
          {/* 4.5.1 FEED HEADER */}
          <div className="panel scan-line rounded-t-[6px] rounded-b-none border-b-0 px-5 py-3 relative overflow-hidden flex justify-between items-center z-10">
            <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.12em]">INVESTIGATION TIMELINE</div>
            <div className="flex items-center gap-4">
              <div className="font-mono text-[10px] text-[#3a5070]">
                EP {stats.episodes} · ACT {stats.actions} · BEST {stats.bestScore !== null ? stats.bestScore.toFixed(2) : '—'}
              </div>
              {feed.length > 0 && (
                <button onClick={clearFeed} className="font-mono text-[9px] text-[#3a5070] hover:text-[#e8f0fe] bg-transparent border-none cursor-pointer">
                  CLEAR
                </button>
              )}
            </div>
          </div>

          {/* 4.5.2 EEG BASELINE SVG */}
          <div className="w-full h-[32px] bg-[rgba(3,6,15,0.8)] border-x border-[#ffffff12] relative z-0 flex items-center overflow-hidden">
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 32">
              <polyline 
                points="0,16 5,16 8,16 10,4 12,28 14,16 20,16 22,16 24,8 26,24 28,16 34,16 36,16 38,6 40,26 42,16 48,16 50,16 52,10 54,22 56,16 62,16 64,16 66,5 68,27 70,16 76,16 78,16 80,8 82,24 84,16 90,16 92,16 94,6 96,26 98,16 100,16" 
                stroke="#00d4e6" 
                strokeWidth="1" 
                fill="none" 
                strokeDasharray="200" 
                style={{ animation: 'eeg-pulse 3s linear infinite' }}
              />
            </svg>
          </div>

          {/* 4.5.3 FEED CONTENT AREA */}
          <div className="panel rounded-t-none rounded-b-[6px] border-t-0 p-5 min-h-[500px] max-h-[calc(100vh-200px)] overflow-y-auto">
            
            {feed.length === 0 && (
              <div className="flex flex-col items-center justify-center h-[320px]">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="rgba(0,212,230,0.2)" strokeWidth="1.5">
                  <path d="M0,20 L12,20 L16,8 L24,32 L28,20 L40,20" />
                </svg>
                <div className="font-sans text-[13px] text-[#3a5070] mt-4">Initialize an episode to begin signal investigation</div>
                <div className="font-mono text-[10px] text-[#3a5070] mt-[6px] opacity-50">Select task difficulty → NEW EPISODE</div>
              </div>
            )}

            {feed.map((item, idx) => (
              <div key={item.id}>
                {idx > 0 && (
                  <div className="h-[20px] w-full relative flex justify-center">
                    <div className="w-[1px] h-full bg-gradient-to-b from-[rgba(0,212,230,0.15)] to-[rgba(0,212,230,0.08)] relative">
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[4px] h-[4px] bg-[rgba(0,212,230,0.3)] rounded-full"></div>
                    </div>
                  </div>
                )}
                
                <motion.div layout initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
                  
                  {item.type === 'reset' && (
                    <div className="panel border-l-2 border-l-[#8080f0] px-5 py-4 mb-3">
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-[10px]">
                          <div className="w-[5px] h-[5px] rounded-full bg-[#8080f0]"></div>
                          <div className="font-mono text-[10px] text-[#8080f0] uppercase tracking-[0.1em]">NEW CASE OPENED</div>
                          <div className="font-mono text-[10px] text-[#3a5070] ml-auto">{new Date().toLocaleTimeString()}</div>
                        </div>
                        <div className="font-sans text-[22px] font-semibold text-[#e8f0fe]">{item.data.drug_name || 'Unknown Subject'}</div>
                        {item.data.current_output?.message && (
                          <div className="mt-2 p-[12px_14px] bg-[rgba(255,255,255,0.02)] border border-[#ffffff0d] rounded-[4px] font-sans text-[13px] text-[#7090b0] leading-[1.6]">
                            {item.data.current_output.message}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {item.type === 'action' && (
                    <div className="panel border-l-2 border-l-[rgba(255,255,255,0.07)] hover:border-l-[rgba(0,212,230,0.3)] transition-colors duration-150 px-5 py-4 mb-2">
                      <div className="flex justify-between items-center mb-3">
                        <div className="flex items-center gap-[10px]">
                          <div className="w-[24px] h-[24px] bg-[rgba(255,255,255,0.04)] rounded-[3px] flex items-center justify-center">
                            {getIcon(item.actionType)}
                          </div>
                          <div className="font-sans text-[13px] font-medium text-[#e8f0fe] capitalize">{item.actionType.replace(/_/g, ' ')}</div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="font-mono text-[9px] text-[#3a5070]">STEP {item.step}</div>
                          <div className="font-mono text-[10px] font-medium text-[#00d4a0] bg-[rgba(0,212,160,0.06)] border border-[rgba(0,212,160,0.2)] rounded-[3px] px-2 py-0.5">
                            +{item.reward.toFixed(2)}
                          </div>
                          <div className="font-mono text-[9px] text-[#3a5070]">{item.remaining} left</div>
                        </div>
                      </div>

                      {item.output?.source && (
                        <div className="font-mono text-[10px] text-[#3a5070] mb-2">
                          SOURCE: <span className="text-[#e8f0fe] font-medium">{item.output.source}</span>
                        </div>
                      )}

                      {item.output?.error && (
                        <div className="font-mono text-[11px] text-[#e04060] bg-[rgba(224,64,96,0.06)] border border-[rgba(224,64,96,0.2)] rounded-[4px] px-3 py-2 mb-2">
                          {item.output.error}
                        </div>
                      )}

                      {item.output?.data && renderRichData(item.output.data)}

                      {item.output?.hint && (
                        <div className="mt-2 px-3 py-2 bg-[rgba(0,212,160,0.04)] border border-[rgba(0,212,160,0.15)] rounded-[4px] font-sans text-[12px] text-[#00d4a0] flex flex-row gap-2 items-start">
                          <div className="text-[#00d4a0] shrink-0">→</div>
                          <div>{item.output.hint}</div>
                        </div>
                      )}
                    </div>
                  )}

                  {item.type === 'submit' && (
                    <div className="panel panel-accent border-l-2 border-l-[#00d4e6] p-5 mb-3">
                      <div className="flex justify-between items-start">
                        <div className="font-mono text-[9px] text-[#00d4e6] uppercase tracking-[0.1em]">ASSESSMENT FILED</div>
                        <div className={`font-mono text-[14px] font-semibold ${item.score >= 0.7 ? 'text-[#00d4a0]' : item.score >= 0.5 ? 'text-[#e8a020]' : 'text-[#e04060]'}`}>
                          {item.score.toFixed(2)}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3 mt-3">
                        <div>
                          <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.08em] mb-1">SUBJECT</div>
                          <div className="font-sans text-[14px] font-medium text-[#e8f0fe]">{item.param.drug_name}</div>
                        </div>
                        <div>
                          <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.08em] mb-1">ACTION</div>
                          <div className="font-mono text-[12px] font-medium text-[#00d4e6] uppercase">{item.param.regulatory_action}</div>
                        </div>
                        <div className="col-span-2">
                          <div className="font-mono text-[9px] text-[#3a5070] uppercase tracking-[0.08em] mb-1">SIGNALS</div>
                          <div className="font-sans text-[13px] text-[#7090b0]">
                            {item.param.primary_signal}
                            {item.param.secondary_signal && " · " + item.param.secondary_signal}
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-[#ffffff0d]">
                        <div className="font-sans text-[13px] text-[#7090b0] italic">
                          &quot;{item.message}&quot;
                        </div>
                      </div>
                    </div>
                  )}

                  {item.type === 'error' && (
                    <div className="font-mono text-[12px] text-[#e04060] bg-[rgba(224,64,96,0.06)] border border-[rgba(224,64,96,0.2)] rounded-[4px] px-[14px] py-[10px] mb-2 flex items-center gap-2">
                      <AlertTriangle size={14} className="shrink-0" />
                      {item.message}
                    </div>
                  )}

                </motion.div>
              </div>
            ))}
            <div ref={feedEndRef} className="h-4"></div>
          </div>
        </div>
      </main>
      )}
    </div>
  );
}
