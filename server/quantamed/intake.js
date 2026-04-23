const INTAKE_STEPS = [
  { id: 'demographics', title: 'Demographics & Vitals' },
  { id: 'clinical', title: 'Clinical History' },
  { id: 'genomics', title: 'Genomics & Biomarkers' },
  { id: 'labs', title: 'Labs & Organ Function' },
  { id: 'pharmacology', title: 'Pharmacology & Goals' }
];

let currentStepIndex = 0;

const initialPatientData = {
  basic_info: { age: '', gender: 'female', weight_kg: '', height_cm: '', bmi: '', ethnicity: '', pregnancy_status: 'false' },
  condition: { primary_diagnosis: 'epilepsy', subtype: '', severity: 'moderate', duration_months: '', comorbidities: '', family_history: '' },
  symptoms: { seizure_frequency_per_month: '', anxiety_score: '', depression_score: '', sleep_disturbance_score: '', fatigue_score: '', cognitive_impairment_score: '' },
  vitals: { heart_rate: '', blood_pressure: '', temperature: '' },
  current_meds: '', past_meds: '',
  genetics: { CYP2D6: 'normal', CYP3A4: 'normal', CYP2C19: 'normal', CYP2C9: 'normal', UGT1A4: '', HLA_variants: '' },
  epigenetics: { methylation_status: '' },
  organs: { liver_status: 'normal', kidney_status: 'normal', heart_status: 'normal', brain_status: '' },
  labs: { ALT: '', AST: '', ALP: '', bilirubin: '', creatinine: '', eGFR: '', glucose: '', HbA1c: '', lipid_profile: '', CRP: '' },
  biomarkers: { serotonin_level: '', dopamine_level: '', androgen_level: '', cortisol: '', inflammatory_markers: '' },
  target_expression: { GABA_activity: '', NMDA_activity: '', SERT_expression: '', D2_receptor_expression: '', ion_channel_activity: '' },
  drug_response_profile: { antiepileptic_response: '', ssri_response: '', benzodiazepine_response: '' },
  side_effect_history: '', allergies: '',
  pharmacokinetics: { absorption_rate: '', bioavailability: '', half_life_hours: '', clearance_rate: '', volume_of_distribution: '' },
  drug_levels: { current_plasma_concentration: '', therapeutic_range: '', toxicity_threshold: '' },
  lifestyle: { sleep_hours: '', sleep_quality: '', diet_type: '', exercise_frequency: '', stress_level: 'moderate', alcohol_use: 'none', smoking: 'false', caffeine_intake: '' },
  environment: { location: '', pollution_exposure: '', altitude: '' },
  wearables_data: { step_count: '', heart_rate_variability: '', sleep_cycles: '' },
  time_series: { symptom_trend: '', drug_response_timeline: '', side_effect_timeline: '' },
  imaging: { MRI_findings: '', EEG_patterns: '' },
  clinical_notes: { doctor_notes: '', patient_feedback: '' },
  risk_profile: { side_effect_tolerance: 'moderate', urgency_level: 'moderate', compliance_probability: '' },
  treatment_goal: { primary_goal: 'seizure_control', secondary_goal: '', quality_of_life_priority: 'true' }
};

let patientData = JSON.parse(JSON.stringify(initialPatientData));

function renderWizard() {
  const container = document.getElementById('intake-wizard');
  if (!container) return;

  let progressHtml = INTAKE_STEPS.map((s, i) => `
    <div class="progress-step ${i === 0 ? 'active' : ''}" id="prog-${i}">
      <div class="progress-step-fill"></div>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="wizard-container">
      <button class="wiz-quickfill" onclick="fillDemoData()">✦ Quick Fill Preset</button>
      <div class="wizard-header">
        <div class="wizard-title">Interactive Patient Intake</div>
        <div class="wizard-subtitle">Initialize decision support parameters</div>
      </div>
      <div class="wizard-progress">${progressHtml}</div>
      
      <form id="wizard-form">
        <!-- Step 1 -->
        <div class="wizard-step-content active" id="step-0">
          <div class="section-title">Demographics & Vitals</div>
          <div class="form-grid">
            <div class="form-group"><label>Age <span class="optional">yrs</span></label><input type="number" class="form-input" data-path="basic_info.age" oninput="updateData(this)"></div>
            <div class="form-group"><label>Gender</label>
              <select class="form-select" data-path="basic_info.gender" onchange="updateData(this)">
                <option value="female">Female</option><option value="male">Male</option><option value="other">Other</option>
              </select>
            </div>
            <div class="form-group"><label>Weight <span class="optional">kg</span></label><input type="number" class="form-input" data-path="basic_info.weight_kg" oninput="updateData(this)"></div>
            <div class="form-group"><label>Pregnancy Status</label>
              <select class="form-select" data-path="basic_info.pregnancy_status" onchange="updateData(this)">
                <option value="false">Not Pregnant</option><option value="true">Pregnant</option>
              </select>
            </div>
            <div class="form-group"><label>Heart Rate <span class="optional">bpm</span></label><input type="number" class="form-input" data-path="vitals.heart_rate" oninput="updateData(this)"></div>
            <div class="form-group"><label>Blood Pressure <span class="optional">mmHg</span></label><input type="text" class="form-input" data-path="vitals.blood_pressure" placeholder="e.g. 120/80" oninput="updateData(this)"></div>
          </div>
          <div class="section-title" style="margin-top:24px;">Lifestyle</div>
          <div class="form-grid">
            <div class="form-group"><label>Stress Level</label>
              <select class="form-select" data-path="lifestyle.stress_level" onchange="updateData(this)">
                <option value="low">Low</option><option value="moderate" selected>Moderate</option><option value="high">High</option>
              </select>
            </div>
            <div class="form-group"><label>Sleep Hours <span class="optional">/night</span></label><input type="number" class="form-input" data-path="lifestyle.sleep_hours" oninput="updateData(this)"></div>
          </div>
        </div>

        <!-- Step 2 -->
        <div class="wizard-step-content" id="step-1">
          <div class="section-title">Clinical History</div>
          <div class="form-grid">
            <div class="form-group"><label>Primary Diagnosis</label><input type="text" class="form-input" data-path="condition.primary_diagnosis" oninput="updateData(this)" value="Epilepsy"></div>
            <div class="form-group"><label>Subtype</label><input type="text" class="form-input" data-path="condition.subtype" oninput="updateData(this)"></div>
            <div class="form-group"><label>Severity</label>
              <select class="form-select" data-path="condition.severity" onchange="updateData(this)">
                <option value="mild">Mild</option><option value="moderate" selected>Moderate</option><option value="severe">Severe</option>
              </select>
            </div>
            <div class="form-group"><label>Duration <span class="optional">months</span></label><input type="number" class="form-input" data-path="condition.duration_months" oninput="updateData(this)"></div>
            <div class="form-group full"><label>Comorbidities <span class="optional">comma separated</span></label><input type="text" class="form-input" data-path="condition.comorbidities" placeholder="e.g. PCOS, Anxiety" oninput="updateData(this)"></div>
          </div>
        </div>

        <!-- Step 3 -->
        <div class="wizard-step-content" id="step-2">
          <div class="section-title">Genomics & Biomarkers</div>
          <div class="form-grid">
            <div class="form-group"><label>CYP2D6</label>
              <select class="form-select" data-path="genetics.CYP2D6" onchange="updateData(this)">
                <option value="normal">Normal</option><option value="intermediate">Intermediate</option><option value="poor">Poor Metabolizer</option><option value="ultrarapid">Ultrarapid</option>
              </select>
            </div>
            <div class="form-group"><label>CYP2C19</label>
              <select class="form-select" data-path="genetics.CYP2C19" onchange="updateData(this)">
                <option value="normal">Normal</option><option value="intermediate">Intermediate</option><option value="poor">Poor Metabolizer</option>
              </select>
            </div>
            <div class="form-group"><label>Androgen Level</label>
              <select class="form-select" data-path="biomarkers.androgen_level" onchange="updateData(this)">
                <option value="">Unknown</option><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option>
              </select>
            </div>
            <div class="form-group"><label>Serotonin Level</label>
              <select class="form-select" data-path="biomarkers.serotonin_level" onchange="updateData(this)">
                <option value="">Unknown</option><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Step 4 -->
        <div class="wizard-step-content" id="step-3">
          <div class="section-title">Labs & Organ Function</div>
          <div class="form-grid">
            <div class="form-group"><label>Liver Status</label>
              <select class="form-select" data-path="organs.liver_status" onchange="updateData(this)">
                <option value="normal">Normal</option><option value="mild_impairment">Mild Impairment</option><option value="severe">Severe Impairment</option>
              </select>
            </div>
            <div class="form-group"><label>Kidney Status</label>
              <select class="form-select" data-path="organs.kidney_status" onchange="updateData(this)">
                <option value="normal">Normal</option><option value="mild_impairment">Mild Impairment</option><option value="severe">Severe Impairment</option>
              </select>
            </div>
            <div class="form-group"><label>ALT <span class="optional">U/L</span></label><input type="number" class="form-input" data-path="labs.ALT" oninput="updateData(this)"></div>
            <div class="form-group"><label>eGFR <span class="optional">mL/min/1.73m2</span></label><input type="number" class="form-input" data-path="labs.eGFR" oninput="updateData(this)"></div>
          </div>
        </div>

        <!-- Step 5 -->
        <div class="wizard-step-content" id="step-4">
          <div class="section-title">Pharmacology & Goals</div>
          <div class="form-grid full">
            <div class="form-group"><label>Current Medications <span class="optional">Drug (Dose)</span></label><input type="text" class="form-input" data-path="current_meds" placeholder="e.g. Valproic Acid (1000mg)" oninput="updateData(this)"></div>
            <div class="form-group"><label>Side Effect Tolerance</label>
              <select class="form-select" data-path="risk_profile.side_effect_tolerance" onchange="updateData(this)">
                <option value="high">High</option><option value="moderate" selected>Moderate</option><option value="low">Low</option>
              </select>
            </div>
            <div class="form-group"><label>Primary Treatment Goal</label>
              <select class="form-select" data-path="treatment_goal.primary_goal" onchange="updateData(this)">
                <option value="seizure_control" selected>Seizure Control</option><option value="minimize_side_effects">Minimize Side Effects</option>
              </select>
            </div>
          </div>
        </div>

      </form>

      <div class="wizard-alert" id="wiz-alert">
        <div class="wizard-alert-icon">⚠️</div>
        <div class="wizard-alert-content" id="wiz-alert-msg"></div>
      </div>

      <div class="wizard-nav">
        <button class="wiz-btn wiz-btn-prev" onclick="prevStep()" id="btn-prev" style="visibility:hidden;">Back</button>
        <button class="wiz-btn wiz-btn-next" onclick="nextStep()" id="btn-next">Next Step</button>
      </div>

    </div>
  `;
}

function updateData(el) {
  const path = el.getAttribute('data-path');
  const val = el.value;
  const parts = path.split('.');
  if (parts.length === 1) {
    patientData[parts[0]] = val;
  } else {
    patientData[parts[0]][parts[1]] = val;
  }
  checkAlerts();
}

function fillDemoData() {
  patientData.basic_info.age = '24';
  patientData.basic_info.gender = 'female';
  patientData.basic_info.weight_kg = '62';
  patientData.basic_info.pregnancy_status = 'false';
  patientData.condition.primary_diagnosis = 'epilepsy';
  patientData.condition.subtype = 'Juvenile Myoclonic Epilepsy';
  patientData.condition.comorbidities = 'PCOS, Anxiety';
  patientData.genetics.CYP2D6 = 'poor';
  patientData.biomarkers.androgen_level = 'high';
  patientData.organs.liver_status = 'mild_impairment';
  patientData.labs.ALT = '42';
  patientData.current_meds = 'Valproic Acid (1000mg)';
  patientData.lifestyle.sleep_hours = '5';
  
  // Update inputs
  document.querySelectorAll('.form-input, .form-select').forEach(el => {
    const p = el.getAttribute('data-path').split('.');
    const v = p.length === 1 ? patientData[p[0]] : patientData[p[0]][p[1]];
    if(v !== undefined) el.value = v;
  });
  checkAlerts();
}

function checkAlerts() {
  const alertBox = document.getElementById('wiz-alert');
  const alertMsg = document.getElementById('wiz-alert-msg');
  let alerts = [];

  const isFemale = patientData.basic_info.gender === 'female';
  const hasPcos = patientData.condition.comorbidities.toLowerCase().includes('pcos');
  const hasVpa = patientData.current_meds.toLowerCase().includes('valpro');
  const isPregnant = patientData.basic_info.pregnancy_status === 'true';
  const cyp2d6 = patientData.genetics.CYP2D6;

  if (isFemale && hasPcos && hasVpa) {
    alerts.push("<strong>PCOS Exacerbation Risk</strong>Valproic acid is contraindicated in patients with PCOS due to hyperandrogenism risk.");
  }
  if (isFemale && isPregnant && hasVpa) {
    alerts.push("<strong>Teratogenicity Warning</strong>Valproic Acid is FDA Category X for pregnancy. Major risk of neural tube defects.");
  }
  if (cyp2d6 === 'poor') {
    alerts.push("<strong>CYP2D6 Poor Metabolizer</strong>High risk of drug accumulation for substrates. Requires dose adjustment.");
  }

  if (alerts.length > 0) {
    alertMsg.innerHTML = alerts.join('<br/><br/>');
    alertBox.classList.add('show');
  } else {
    alertBox.classList.remove('show');
  }
}

function updateNav() {
  document.getElementById('btn-prev').style.visibility = currentStepIndex === 0 ? 'hidden' : 'visible';
  const btnNext = document.getElementById('btn-next');
  if (currentStepIndex === INTAKE_STEPS.length - 1) {
    btnNext.innerText = 'Initialize Dashboard';
    btnNext.style.background = 'var(--green)';
  } else {
    btnNext.innerText = 'Next Step';
    btnNext.style.background = 'var(--cyan)';
  }
}

function nextStep() {
  if (currentStepIndex === INTAKE_STEPS.length - 1) {
    finishIntake();
    return;
  }
  document.getElementById('step-' + currentStepIndex).classList.remove('active');
  document.getElementById('prog-' + currentStepIndex).classList.add('completed');
  
  currentStepIndex++;
  
  document.getElementById('step-' + currentStepIndex).classList.add('active');
  document.getElementById('prog-' + currentStepIndex).classList.add('active');
  updateNav();
}

function prevStep() {
  if (currentStepIndex === 0) return;
  document.getElementById('step-' + currentStepIndex).classList.remove('active');
  document.getElementById('prog-' + currentStepIndex).classList.remove('active');
  
  currentStepIndex--;
  
  document.getElementById('step-' + currentStepIndex).classList.add('active');
  document.getElementById('prog-' + currentStepIndex).classList.remove('completed');
  updateNav();
}

function finishIntake() {
  const container = document.getElementById('intake-wizard');
  container.classList.add('hidden');
  
  const nameEl = document.querySelector('.patient-name');
  if(nameEl) nameEl.innerText = "Custom Patient";
  
  const dxEl = document.querySelector('.patient-dx');
  if(dxEl) dxEl.innerHTML = patientData.condition.subtype + '<br/>' + patientData.basic_info.gender + ' • ' + patientData.basic_info.age + 'y';
}

window.addEventListener('DOMContentLoaded', () => {
  renderWizard();
});
