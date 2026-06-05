"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Activity, FlaskConical, Dna, Shield, Atom, Brain } from "lucide-react";

const STATS = [
  { value: "9", label: "Pipelines", suffix: "" },
  { value: "6", label: "Data Sources", suffix: "" },
  { value: "10", label: "DDI Pairs", suffix: "+" },
  { value: "6", label: "NCT Trials", suffix: "" },
];

const FEATURES = [
  { icon: <FlaskConical size={18} />, title: "Drug Triage", desc: "9-pipeline scoring across efficacy, safety, genomics, ADMET, and DDI.", href: "/analyze" },
  { icon: <Atom size={18} />, title: "Quantum Protein", desc: "VQE binding simulations and structural modeling.", href: "/protein" },
  { icon: <Shield size={18} />, title: "ADMET Profile", desc: "Lipinski rules, Tox21 profiling, and BBB scoring.", href: "/admet" },
  { icon: <Activity size={18} />, title: "PK Modeling", desc: "Real-time concentration curves with therapeutic range validation.", href: "/pk" },
  { icon: <Dna size={18} />, title: "Pharmacogenomics", desc: "CYP2D6/2C9/3A4/2C19 metabolizer phenotype integration.", href: "/analyze" },
  { icon: <Brain size={18} />, title: "DDI Engine", desc: "DrugBank-verified drug-drug interaction checking with severity grading.", href: "/ddi" },
];

const SOURCES = [
  "ChEMBL Bioactivity", "DrugBank Open Data", "CPIC Clinical Guidelines",
  "BBBP/MoleculeNet", "FDA FAERS (OpenFDA)", "Tox21/EPA", "ClinicalTrials.gov",
];

export default function HomePage() {
  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative min-h-[85vh] flex flex-col items-center justify-center text-center px-6">
        {/* Radial glow */}
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(74,250,154,0.04) 0%, transparent 70%)"
        }} />

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <span className="tag tag-cyan text-[10px] mb-6 inline-block">COMPUTATIONAL DRUG TRIAGE</span>
        </motion.div>

        <motion.h1
          className="text-4xl md:text-6xl lg:text-7xl font-light tracking-tight text-white/90 max-w-4xl leading-[1.1]"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
        >
          The drug <span className="italic font-serif" style={{ fontFamily: "var(--font-instrument)" }}>that fits.</span>
        </motion.h1>

        <motion.p
          className="mt-6 text-sm md:text-base text-white/35 max-w-xl leading-relaxed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          9 computational pipelines. 6 clinical data sources. One patient-specific ranking.
          Precision pharmacovigilance for the real world.
        </motion.p>

        <motion.div
          className="mt-10 flex items-center gap-4"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <Link href="/analyze" className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#4AFA9A] text-[#080A0F] text-sm font-mono font-semibold rounded hover:bg-[#3de88a] transition-colors">
            Analyze Patient <ArrowRight size={14} />
          </Link>
          <Link href="/compare" className="inline-flex items-center gap-2 px-6 py-2.5 border border-white/10 text-white/60 text-sm font-mono rounded hover:border-white/20 hover:text-white/80 transition-colors">
            Compare Drugs
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          {STATS.map((s, i) => (
            <div key={i} className="text-center animate-count-up" style={{ animationDelay: `${0.9 + i * 0.1}s` }}>
              <span className="text-3xl md:text-4xl font-mono font-bold text-[#4AFA9A]">{s.value}{s.suffix}</span>
              <span className="block text-[10px] font-mono text-white/25 tracking-wider uppercase mt-1">{s.label}</span>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features Bento Grid */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:auto-rows-[240px]">
          {FEATURES.map((f, i) => (
            <Link 
              key={i} 
              href={f.href}
              className={`group relative panel block overflow-hidden transition-all duration-500 hover:border-[#4AFA9A]/30 hover:shadow-[0_0_40px_-10px_rgba(74,250,154,0.15)] ${
                i === 0 || i === 5 ? "md:col-span-2" : "md:col-span-1"
              }`}
            >
              {/* Subtle hover gradient wash */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4AFA9A]/0 to-[#4AFA9A]/0 group-hover:from-[#4AFA9A]/5 group-hover:to-transparent transition-all duration-700 pointer-events-none" />
              
              <motion.div
                className="h-full p-8 flex flex-col justify-between relative z-10"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5, type: "spring", stiffness: 100 }}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-white/5 border border-white/10 group-hover:border-[#4AFA9A]/40 group-hover:bg-[#4AFA9A]/10 transition-all duration-500">
                    <span className="text-white/60 group-hover:text-[#4AFA9A] transition-colors">{f.icon}</span>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-white/90 tracking-tight group-hover:text-white transition-colors mb-2">
                    {f.title}
                  </h3>
                  <p className="text-sm text-white/40 leading-relaxed font-light group-hover:text-white/60 transition-colors">
                    {f.desc}
                  </p>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </section>

      {/* Data sources ticker */}
      <section className="border-t border-white/[0.05] py-6 overflow-hidden">
        <div className="flex items-center gap-8 animate-scroll whitespace-nowrap">
          {[...SOURCES, ...SOURCES].map((s, i) => (
            <span key={i} className="text-[10px] font-mono text-white/15 tracking-wider uppercase flex-shrink-0">{s}</span>
          ))}
        </div>
        <style jsx>{`
          @keyframes scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
          .animate-scroll { animation: scroll 30s linear infinite; }
        `}</style>
      </section>
    </div>
  );
}
