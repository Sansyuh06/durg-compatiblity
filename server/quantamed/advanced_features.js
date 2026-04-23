// ═══════════════════════════════════════════════════════════
// ADVANCED FEATURES MODULE
// Biomarker Timeline, Drug Repurposing, Ancestry PGx, Dose Optimization
// ═══════════════════════════════════════════════════════════

// ── 1. LIVE PATIENT BIOMARKER TIMELINE ─────────────────────
let biomarkerInited = false;
function initBiomarkerTimeline() {
  if (biomarkerInited) return;
  biomarkerInited = true;
  const wrap = document.getElementById('biomarker-timeline-wrap');
  if (!wrap || typeof Chart === 'undefined') return;

  const days = Array.from({length:90}, (_,i) => `Day ${i+1}`);
  const ltgResponse = days.map((_,i) => {
    const base = 3 - (i/90)*2.5;
    return Math.max(0.2, base + (Math.random()-0.5)*0.3);
  });
  const vpaRisk = days.map((_,i) => {
    const base = 1 + (i/90)*4;
    return Math.min(5, base + (Math.random()-0.5)*0.4);
  });
  const seizures = days.map((_,i) => Math.max(0, 3 - (i/30)*0.8 + (Math.random()-0.5)*1.2));
  const mood = days.map((_,i) => Math.min(10, 4 + (i/90)*3 + (Math.random()-0.5)*1));
  const sleep = days.map((_,i) => Math.min(9, 5 + (i/90)*2.5 + (Math.random()-0.5)*0.8));
  const fatigue = days.map((_,i) => Math.max(1, 7 - (i/90)*4 + (Math.random()-0.5)*1));

  // Main trajectory chart
  const ctx1 = document.getElementById('biomarker-chart-main');
  if (ctx1) {
    new Chart(ctx1.getContext('2d'), {
      type: 'line',
      data: {
        labels: days.filter((_,i) => i%3===0),
        datasets: [
          { label: 'LTG Response (Good)', data: ltgResponse.filter((_,i)=>i%3===0), borderColor: '#20c997', backgroundColor: 'rgba(32,201,151,0.1)', fill: true, tension: 0.4, pointRadius: 0 },
          { label: 'VPA Risk Accumulation', data: vpaRisk.filter((_,i)=>i%3===0), borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', fill: true, tension: 0.4, pointRadius: 0 }
        ]
      },
      options: {
        responsive: true, plugins: { legend: { labels: { color: '#868e96', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: { x: { ticks: { color: '#868e96', font: { size: 9 }, maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.03)' } }, y: { ticks: { color: '#868e96' }, grid: { color: 'rgba(255,255,255,0.03)' }, title: { display: true, text: 'Risk Score', color: '#868e96' } } }
      }
    });
  }

  // Secondary charts
  const miniCharts = [
    { id: 'bio-seizures', data: seizures, label: 'Seizures/mo', color: '#ff6b6b' },
    { id: 'bio-mood', data: mood, label: 'Mood Score', color: '#4DB8FF' },
    { id: 'bio-sleep', data: sleep, label: 'Sleep Hours', color: '#845EF7' },
    { id: 'bio-fatigue', data: fatigue, label: 'Fatigue', color: '#FCC419' }
  ];
  miniCharts.forEach(mc => {
    const el = document.getElementById(mc.id);
    if (!el) return;
    new Chart(el.getContext('2d'), {
      type: 'line',
      data: { labels: days.filter((_,i)=>i%5===0), datasets: [{ data: mc.data.filter((_,i)=>i%5===0), borderColor: mc.color, backgroundColor: mc.color+'15', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
    });
  });

  // Animate the "live" indicator
  const liveEl = document.getElementById('bio-live-indicator');
  if (liveEl) { setInterval(() => { liveEl.style.opacity = liveEl.style.opacity === '0.4' ? '1' : '0.4'; }, 1000); }
}

// ── 2. DRUG REPURPOSING SCANNER ────────────────────────────
let repurposingInited = false;
function initRepurposing() {
  if (repurposingInited) return;
  repurposingInited = true;
  const wrap = document.getElementById('repurposing-results');
  if (!wrap) return;

  const candidates = [
    { drug: 'Lamotrigine', primary: 'Epilepsy (Nav1.2)', secondary: 'Bipolar Depression', mechanism: 'Glutamate release inhibition via Nav channel blockade stabilizes mood circuits', confidence: 92, evidence: 'FDA-approved for bipolar maintenance', color: '#20c997' },
    { drug: 'Lamotrigine', primary: 'Epilepsy (Nav1.2)', secondary: 'Anxiety (comorbid)', mechanism: 'Moderate SERT affinity (pChEMBL 5.8) provides anxiolytic co-benefit', confidence: 67, evidence: 'Off-label use documented in literature', color: '#4DB8FF' },
    { drug: 'Levetiracetam', primary: 'Epilepsy (SV2A)', secondary: 'Neuropathic Pain', mechanism: 'SV2A modulation reduces aberrant neurotransmitter release in pain pathways', confidence: 54, evidence: 'Phase II trials show modest efficacy', color: '#FCC419' },
    { drug: 'Topiramate', primary: 'Epilepsy (AMPA/GABA)', secondary: 'Migraine Prophylaxis', mechanism: 'AMPA antagonism + carbonic anhydrase inhibition reduces cortical spreading depression', confidence: 88, evidence: 'FDA-approved for migraine prevention', color: '#20c997' },
    { drug: 'Topiramate', primary: 'Epilepsy (AMPA/GABA)', secondary: 'Weight Management', mechanism: 'Appetite suppression via hypothalamic modulation', confidence: 78, evidence: 'FDA-approved (Qsymia combination)', color: '#4DB8FF' }
  ];

  wrap.innerHTML = candidates.map(c => `
    <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <div>
          <span style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:600;color:var(--white);">${c.drug}</span>
          <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text2);margin-left:8px;">${c.primary}</span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:500;color:${c.color};background:${c.color}15;padding:4px 10px;border-radius:6px;">${c.confidence}% CONFIDENCE</div>
      </div>
      <div style="font-family:'Outfit',sans-serif;font-size:14px;color:${c.color};margin-bottom:8px;">→ ${c.secondary}</div>
      <div style="font-size:13px;color:var(--text);line-height:1.5;margin-bottom:8px;">${c.mechanism}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text2);">Evidence: ${c.evidence}</div>
      <div style="margin-top:8px;height:4px;background:rgba(255,255,255,0.05);border-radius:2px;overflow:hidden;">
        <div style="height:100%;width:${c.confidence}%;background:${c.color};border-radius:2px;transition:width 1s ease;"></div>
      </div>
    </div>
  `).join('');
}

// ── 3. GENETIC ANCESTRY PHARMACOGENOMICS CORRECTION ────────
let ancestryInited = false;
function initAncestryPGx() {
  if (ancestryInited) return;
  ancestryInited = true;
  const wrap = document.getElementById('ancestry-pgx-content');
  if (!wrap) return;

  const populations = {
    'European': { CYP2D6_PM: 7, CYP2C19_PM: 2, CYP2C9_PM: 3.5, CYP3A4_variant: 5 },
    'East Asian': { CYP2D6_PM: 1, CYP2C19_PM: 15, CYP2C9_PM: 3, CYP3A4_variant: 20 },
    'African': { CYP2D6_PM: 3, CYP2C19_PM: 4, CYP2C9_PM: 2, CYP3A4_variant: 70 },
    'South Asian': { CYP2D6_PM: 4, CYP2C19_PM: 12, CYP2C9_PM: 5, CYP3A4_variant: 15 },
    'Ethiopian': { CYP2D6_PM: 29, CYP2C19_PM: 5, CYP2C9_PM: 2.5, CYP3A4_variant: 8 },
    'Hispanic': { CYP2D6_PM: 5, CYP2C19_PM: 6, CYP2C9_PM: 7, CYP3A4_variant: 10 }
  };

  const enzymes = ['CYP2D6_PM','CYP2C19_PM','CYP2C9_PM','CYP3A4_variant'];
  const enzymeLabels = ['CYP2D6 PM','CYP2C19 PM','CYP2C9 PM','CYP3A4 Var'];
  const colors = ['#ff6b6b','#4DB8FF','#FCC419','#845EF7'];

  // Bar chart
  const ctx = document.getElementById('ancestry-chart');
  if (ctx) {
    new Chart(ctx.getContext('2d'), {
      type: 'bar',
      data: {
        labels: Object.keys(populations),
        datasets: enzymes.map((e,i) => ({
          label: enzymeLabels[i],
          data: Object.values(populations).map(p => p[e]),
          backgroundColor: colors[i]+'80',
          borderColor: colors[i],
          borderWidth: 1
        }))
      },
      options: {
        responsive: true, indexAxis: 'y',
        plugins: { legend: { labels: { color: '#868e96', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: { x: { ticks: { color: '#868e96' }, grid: { color: 'rgba(255,255,255,0.03)' }, title: { display: true, text: 'Allele Frequency (%)', color: '#868e96' } }, y: { ticks: { color: '#e9ecef', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.03)' } } }
      }
    });
  }

  // Risk adjustment table
  const tableWrap = document.getElementById('ancestry-risk-table');
  if (tableWrap) {
    const patientEthn = 'European';
    const pop = populations[patientEthn];
    tableWrap.innerHTML = `
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text2);margin-bottom:12px;">PATIENT ETHNICITY: <span style="color:var(--cyan);">${patientEthn.toUpperCase()}</span></div>
      <table class="matrix-table" style="width:100%;">
        <tr><th>Enzyme</th><th>Population PM %</th><th>Prior Risk</th><th>Adjusted Dose Factor</th></tr>
        ${enzymes.map((e,i) => {
          const freq = pop[e];
          const risk = freq > 10 ? 'HIGH' : freq > 5 ? 'MODERATE' : 'LOW';
          const factor = freq > 10 ? '0.5×' : freq > 5 ? '0.75×' : '1.0×';
          return `<tr><td style="color:${colors[i]};font-weight:500;">${enzymeLabels[i]}</td><td>${freq}%</td><td><span class="risk-chip ${risk === 'HIGH' ? 'HIGH' : risk === 'MODERATE' ? 'MOD' : 'LOW'}">${risk}</span></td><td style="font-family:'JetBrains Mono',monospace;font-weight:500;">${factor}</td></tr>`;
        }).join('')}
      </table>
    `;
  }
}

// ── 4. DOSE OPTIMIZATION ENGINE ────────────────────────────
let doseOptInited = false;
function initDoseOptimization() {
  if (doseOptInited) return;
  doseOptInited = true;
  const wrap = document.getElementById('dose-opt-content');
  if (!wrap || typeof Chart === 'undefined') return;

  const drugs = {
    ltg: { name: 'Lamotrigine', standard: 200, adjusted: 175, max: 400, therapeutic: [3, 14], unit: 'mg', halfLife: 25, bioavail: 98 },
    vpa: { name: 'Valproic Acid', standard: 1000, adjusted: 750, max: 1500, therapeutic: [50, 100], unit: 'mg', halfLife: 12, bioavail: 95 },
    lev: { name: 'Levetiracetam', standard: 1000, adjusted: 1000, max: 3000, therapeutic: [12, 46], unit: 'mg', halfLife: 7, bioavail: 100 },
    tpm: { name: 'Topiramate', standard: 200, adjusted: 150, max: 400, therapeutic: [5, 20], unit: 'mg', halfLife: 21, bioavail: 80 },
    zns: { name: 'Zonisamide', standard: 300, adjusted: 250, max: 600, therapeutic: [10, 40], unit: 'mg', halfLife: 63, bioavail: 65 }
  };

  function renderDoseChart(drugKey) {
    const drug = drugs[drugKey];
    const canvas = document.getElementById('dose-curve-chart');
    if (!canvas) return;

    // PK curve: C(t) = (F * D / Vd) * (ka/(ka-ke)) * (e^(-ke*t) - e^(-ka*t))
    const hours = Array.from({length:49}, (_,i) => i);
    const ka = 1.5; // absorption rate
    function pkCurve(dose, factor) {
      const ke = 0.693 / drug.halfLife;
      return hours.map(t => {
        const c = (drug.bioavail/100 * dose * factor / 50) * (ka/(ka-ke)) * (Math.exp(-ke*t) - Math.exp(-ka*t));
        return Math.max(0, c);
      });
    }

    const stdCurve = pkCurve(drug.standard, 1);
    const adjCurve = pkCurve(drug.adjusted, 0.85);
    const maxCurve = pkCurve(drug.max, 1);

    if (window._doseChart) window._doseChart.destroy();
    window._doseChart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: hours.map(h => h + 'h'),
        datasets: [
          { label: `Standard (${drug.standard}${drug.unit})`, data: stdCurve, borderColor: '#868e96', borderDash: [5,5], tension: 0.4, pointRadius: 0, borderWidth: 2 },
          { label: `Patient-Adjusted (${drug.adjusted}${drug.unit})`, data: adjCurve, borderColor: '#20c997', tension: 0.4, pointRadius: 0, borderWidth: 2.5, backgroundColor: 'rgba(32,201,151,0.1)', fill: true },
          { label: `Max Safe (${drug.max}${drug.unit})`, data: maxCurve, borderColor: '#ff6b6b', borderDash: [3,3], tension: 0.4, pointRadius: 0, borderWidth: 1.5 }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#868e96', font: { family: 'JetBrains Mono', size: 10 } } },
          annotation: undefined
        },
        scales: {
          x: { ticks: { color: '#868e96', maxTicksLimit: 12 }, grid: { color: 'rgba(255,255,255,0.03)' }, title: { display: true, text: 'Hours', color: '#868e96' } },
          y: { ticks: { color: '#868e96' }, grid: { color: 'rgba(255,255,255,0.03)' }, title: { display: true, text: 'Plasma Concentration (µg/mL)', color: '#868e96' } }
        }
      }
    });

    // Update dose cards
    const cardsEl = document.getElementById('dose-cards');
    if (cardsEl) {
      cardsEl.innerHTML = `
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text2);margin-bottom:8px;">STANDARD DOSE</div>
          <div style="font-family:'Outfit',sans-serif;font-size:28px;font-weight:600;color:var(--text);">${drug.standard} ${drug.unit}</div>
          <div style="font-size:11px;color:var(--text2);margin-top:4px;">Population average</div>
        </div>
        <div style="background:rgba(32,201,151,0.05);border:1px solid rgba(32,201,151,0.2);border-radius:12px;padding:20px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--green);margin-bottom:8px;">✦ PATIENT-ADJUSTED</div>
          <div style="font-family:'Outfit',sans-serif;font-size:28px;font-weight:600;color:var(--green);">${drug.adjusted} ${drug.unit}</div>
          <div style="font-size:11px;color:var(--text2);margin-top:4px;">CYP2D6 PM + 58kg + mild hepatic</div>
        </div>
        <div style="background:rgba(255,107,107,0.05);border:1px solid rgba(255,107,107,0.15);border-radius:12px;padding:20px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--red);margin-bottom:8px;">MAX SAFE DOSE</div>
          <div style="font-family:'Outfit',sans-serif;font-size:28px;font-weight:600;color:var(--red);">${drug.max} ${drug.unit}</div>
          <div style="font-size:11px;color:var(--text2);margin-top:4px;">Toxicity threshold for this patient</div>
        </div>
      `;
    }

    // PK params
    const pkEl = document.getElementById('dose-pk-params');
    if (pkEl) {
      pkEl.innerHTML = `
        <div class="quality-grid">
          <div class="quality-item"><div class="qi-label">HALF-LIFE</div><div class="qi-value">${drug.halfLife}h</div></div>
          <div class="quality-item"><div class="qi-label">BIOAVAILABILITY</div><div class="qi-value">${drug.bioavail}%</div></div>
          <div class="quality-item"><div class="qi-label">THERAPEUTIC RANGE</div><div class="qi-value ok">${drug.therapeutic[0]}-${drug.therapeutic[1]} µg/mL</div></div>
          <div class="quality-item"><div class="qi-label">DOSE ADJUSTMENT</div><div class="qi-value good">${Math.round((drug.adjusted/drug.standard)*100)}%</div></div>
        </div>
      `;
    }
  }

  // Initial render
  renderDoseChart('ltg');

  // Dropdown handler
  const sel = document.getElementById('dose-drug-select');
  if (sel) sel.addEventListener('change', () => renderDoseChart(sel.value));
}
