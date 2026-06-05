import { motion } from "framer-motion";

export default function MolecularDocking() {
  return (
    <div className="panel p-0 overflow-hidden border border-white/[0.05]">
      <div className="p-4 border-b border-white/[0.05]">
        <div className="text-sm font-mono tracking-wider text-white/80 uppercase">
          Protein-Ligand Docking Dynamics — Molecular Recognition Visualizer
        </div>
      </div>

      <div className="flex flex-col md:flex-row bg-[#060D1A]">
        {/* Left Canvas - Target Drug */}
        <div className="flex-1 relative h-[300px] flex items-center justify-center">
          <div className="absolute top-4 left-4 z-10">
            <div className="font-mono text-[10px] text-white/40 mb-1">TARGET DRUG</div>
            <select className="bg-black/30 border border-white/10 rounded px-3 py-1.5 text-xs text-white outline-none">
              <option>Valproic Acid</option>
              <option>Lamotrigine</option>
            </select>
          </div>
          
          <div className="relative w-48 h-48">
            <div className="absolute inset-0 border border-[#FF5252]/20 rounded-full animate-[spin_10s_linear_infinite]" />
            <div className="absolute inset-4 border border-[#FF5252]/40 rounded-full mix-blend-screen" style={{ transform: "rotateX(60deg)" }} />
            <div className="absolute inset-8 bg-[#FF5252]/10 blur-xl rounded-full" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-[#FF5252] rounded-full blur-md" />
            {/* Docking collisions */}
            <motion.div animate={{ x: [0, 20, 0], y: [0, -20, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="absolute top-1/4 right-1/4 w-3 h-3 bg-white rounded-full" />
            <motion.div animate={{ x: [0, -30, 0], y: [0, 10, 0] }} transition={{ repeat: Infinity, duration: 3 }} className="absolute bottom-1/4 left-1/4 w-2 h-2 bg-white/60 rounded-full" />
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#02050A] to-transparent">
            <div className="font-mono text-[9px] text-[#FF5252]">OFF-TARGET BINDING DETECTED: AR Receptor (0.71)</div>
          </div>
        </div>

        {/* VS Divider */}
        <div className="flex flex-col items-center justify-center gap-3 bg-black/50 border-l border-r border-white/[0.05] p-2 md:w-16">
          <span className="font-sans text-xl font-bold text-white/20 md:[writing-mode:vertical-rl]">VS</span>
          <div className="bg-[#FF5252]/10 border border-[#FF5252]/20 text-[#FF5252] rounded px-2 py-1 text-[8px] font-mono md:[writing-mode:vertical-rl] whitespace-nowrap">
            PCOS RISK
          </div>
          <div className="bg-[#00E676]/10 border border-[#00E676]/20 text-[#00E676] rounded px-2 py-1 text-[8px] font-mono md:[writing-mode:vertical-rl] whitespace-nowrap">
            SAFE
          </div>
        </div>

        {/* Right Canvas - Reference Drug */}
        <div className="flex-1 relative h-[300px] flex items-center justify-center">
          <div className="absolute top-4 right-4 z-10 text-right">
            <div className="font-mono text-[10px] text-white/40 mb-1">COMPARE AGAINST</div>
            <select className="bg-black/30 border border-white/10 rounded px-3 py-1.5 text-xs text-white outline-none">
              <option>Lamotrigine</option>
              <option>Valproic Acid</option>
            </select>
          </div>

          <div className="relative w-48 h-48">
            <div className="absolute inset-0 border border-[#00E676]/20 rounded-full animate-[spin_15s_linear_infinite]" />
            <div className="absolute inset-4 border border-[#00D4FF]/40 rounded-full mix-blend-screen" style={{ transform: "rotateX(-60deg)" }} />
            <div className="absolute inset-8 bg-[#00E676]/10 blur-xl rounded-full" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-[#00D4FF] rounded-full blur-md" />
            {/* Stable docking */}
            <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 4 }} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 border border-white/20 rounded-full" />
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#02050A] to-transparent text-right">
            <div className="font-mono text-[9px] text-[#00E676]">STABLE TARGET BINDING: Nav1.2 (0.94)</div>
          </div>
        </div>
      </div>

      <div className="p-3 bg-[#02050A] text-[9px] text-[#00D4FF]/70 font-mono border-t border-white/[0.05]">
        Science Note: Binding energies derived from Qiskit VQE simulation. Off-target contacts predicted from ChEMBL bioactivity data (pChEMBL {">"} 6).
      </div>
    </div>
  );
}
