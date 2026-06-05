import { motion } from "framer-motion";

export default function TribeBrain({ drugName, state }: { drugName: string, state: "vpa" | "ltg" }) {
  const isVpa = state === "vpa";
  
  return (
    <div className="panel p-0 overflow-hidden border border-white/[0.05]">
      <div className="flex items-center justify-between p-4 bg-[#000A1E]/60 border-b border-[#00D4FF]/10">
        <div className="font-sans text-base font-bold text-white tracking-widest">
          🧠 TRIBE v2 — 3D Neural Activation Brain Twin (Multi-View)
        </div>
        <div className="flex gap-2 items-center">
          <div className="px-3 py-1.5 rounded bg-[#FF5252]/20 border border-[#FF5252]/30 text-[#FF5252] font-mono text-[10px] tracking-wider">
            ⚡ {drugName.toUpperCase()} STATE
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[#020810]">
        {/* Left Hemisphere */}
        <div className="relative h-[300px] bg-[#020810] flex items-center justify-center group overflow-hidden">
          <div className="absolute top-3 left-3 z-10">
            <div className="font-mono text-[10px] text-[#4DB8FF] tracking-wider">◀ LEFT HEMISPHERE</div>
            <div className={`font-sans text-2xl font-bold mt-1 ${isVpa ? "text-[#FF5252]" : "text-[#00E676]"}`}>
              {isVpa ? "87%" : "42%"}
            </div>
            <div className="font-mono text-[8px] text-white/40">ACTIVATION</div>
          </div>
          <div className="absolute bottom-3 left-3 right-3 z-10">
            <div className="font-mono text-[8px] text-[#78A0C8]/60 tracking-wider">AMG · HPC · PFC · INSULA</div>
          </div>
          
          {/* Simulated 3D Brain */}
          <div className="relative w-40 h-40 animate-[spin_30s_linear_infinite]">
            <div className={`absolute inset-0 rounded-full border-2 border-dashed ${isVpa ? "border-[#FF5252]/30" : "border-[#00E676]/30"} mix-blend-screen animate-[pulse_2s_ease-in-out_infinite]`} />
            <div className={`absolute inset-4 rounded-full border ${isVpa ? "border-[#FF5252]/20" : "border-[#00D4FF]/20"} mix-blend-screen`} style={{ transform: "rotateX(60deg) rotateY(30deg)" }} />
            <div className={`absolute inset-8 rounded-full border ${isVpa ? "border-[#FFAB40]/20" : "border-[#00E676]/20"} mix-blend-screen`} style={{ transform: "rotateX(-60deg) rotateY(30deg)" }} />
            <div className={`absolute inset-12 blur-2xl rounded-full ${isVpa ? "bg-[#FF5252]/20" : "bg-[#00E676]/10"}`} />
          </div>
        </div>

        {/* Right Hemisphere */}
        <div className="relative h-[300px] bg-[#020810] border-l border-r border-[#00D4FF]/10 flex items-center justify-center group overflow-hidden">
          <div className="absolute top-3 left-3 z-10">
            <div className="font-mono text-[10px] text-[#4DB8FF] tracking-wider">▶ RIGHT HEMISPHERE</div>
            <div className={`font-sans text-2xl font-bold mt-1 ${isVpa ? "text-[#FF5252]" : "text-[#00E676]"}`}>
              {isVpa ? "85%" : "38%"}
            </div>
            <div className="font-mono text-[8px] text-white/40">ACTIVATION</div>
          </div>
          <div className="absolute bottom-3 left-3 right-3 z-10">
            <div className="font-mono text-[8px] text-[#78A0C8]/60 tracking-wider">AMG · HPC · TEMPORAL · MOTOR</div>
          </div>
          
          <div className="relative w-40 h-40 animate-[spin_25s_linear_infinite_reverse]">
            <div className={`absolute inset-0 rounded-full border-2 border-dashed ${isVpa ? "border-[#FF5252]/30" : "border-[#00E676]/30"} mix-blend-screen animate-[pulse_2.5s_ease-in-out_infinite]`} />
            <div className={`absolute inset-4 rounded-full border ${isVpa ? "border-[#FF5252]/20" : "border-[#00D4FF]/20"} mix-blend-screen`} style={{ transform: "rotateX(40deg) rotateY(-30deg)" }} />
            <div className={`absolute inset-8 rounded-full border ${isVpa ? "border-[#FFAB40]/20" : "border-[#00E676]/20"} mix-blend-screen`} style={{ transform: "rotateX(-40deg) rotateY(-30deg)" }} />
            <div className={`absolute inset-12 blur-2xl rounded-full ${isVpa ? "bg-[#FF5252]/20" : "bg-[#00E676]/10"}`} />
          </div>
        </div>

        {/* Both Hemispheres */}
        <div className="relative h-[300px] bg-[#020810] flex items-center justify-center group overflow-hidden">
          <div className="absolute top-3 left-3 z-10">
            <div className="font-mono text-[10px] text-[#4DB8FF] tracking-wider">◆ BOTH HEMISPHERES</div>
            <div className={`font-sans text-2xl font-bold mt-1 ${isVpa ? "text-[#FF5252]" : "text-[#00E676]"}`}>
              {isVpa ? "86%" : "40%"}
            </div>
            <div className="font-mono text-[8px] text-white/40">AVG ACTIVATION</div>
          </div>
          <div className="absolute bottom-3 left-3 right-3 z-10">
            <div className="font-mono text-[8px] text-[#78A0C8]/60 tracking-wider">FULL CORTICAL SURFACE</div>
          </div>
          
          <div className="relative w-48 h-48 animate-[spin_40s_linear_infinite]">
            <div className={`absolute inset-0 rounded-full border-4 border-dotted ${isVpa ? "border-[#FF5252]/40" : "border-[#00E676]/40"} mix-blend-screen animate-[pulse_1.5s_ease-in-out_infinite]`} />
            <div className={`absolute inset-4 rounded-full border ${isVpa ? "border-[#FF5252]/30" : "border-[#00D4FF]/30"} mix-blend-screen`} style={{ transform: "rotateX(75deg) rotateY(15deg)" }} />
            <div className={`absolute inset-4 rounded-full border ${isVpa ? "border-[#FFAB40]/30" : "border-[#00E676]/30"} mix-blend-screen`} style={{ transform: "rotateX(-75deg) rotateY(-15deg)" }} />
            <div className={`absolute inset-10 blur-3xl rounded-full ${isVpa ? "bg-[#FF5252]/30" : "bg-[#00E676]/15"}`} />
          </div>
        </div>
      </div>

      <div className="p-3 bg-[#000A1E]/80 border-t border-[#00D4FF]/10 flex justify-between items-center">
        <div className="font-mono text-[9px] text-[#78A0C8]/80 tracking-wider">
          TRIBE v2 · SENSORY SIMULATION MODE · fsaverage5 CORTICAL SURFACE
        </div>
        <div className="flex items-center gap-2">
          <div className="w-20 h-1.5 rounded-full bg-gradient-to-r from-transparent via-[#00D4FF]/50 to-[#FF5252]" />
          <div className="font-mono text-[8px] text-white/60">LOW → HIGH</div>
        </div>
      </div>

      {/* EEG Strip */}
      <div className="p-4 bg-[#050C18]/95 border-t border-white/[0.05]">
        <div className="font-mono text-[9px] text-[#78A0C8]/60 tracking-widest mb-2">
          BRAIN REGION ACTIVATION TIME SERIES — EEG TRACE
        </div>
        <div className="h-16 relative overflow-hidden flex flex-col gap-1">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex-1 flex items-center">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 20">
                <path
                  d={`M0,10 Q50,${isVpa ? (i%2===0 ? -10 : 30) : 10} 100,10 T200,10 T300,10 T400,10 T500,10 T600,10 T700,10 T800,10 T900,10 T1000,10`}
                  fill="none"
                  stroke={isVpa ? (i===1 ? "#FF5252" : i===2 ? "#FFAB40" : "#00D4FF") : (i===1 ? "#00E676" : "#00D4FF")}
                  strokeWidth="1.5"
                  className={isVpa ? "animate-[dash_1s_linear_infinite]" : "animate-[dash_3s_linear_infinite]"}
                  strokeDasharray="50 50"
                />
              </svg>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
