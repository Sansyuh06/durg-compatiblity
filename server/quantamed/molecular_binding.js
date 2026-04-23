// ═══════════════════════════════════════════════════════════
// MOLECULAR BINDING COLLISION SIMULATOR
// Three.js dual-canvas drug binding visualization
// ═══════════════════════════════════════════════════════════

const DRUG_DB = {
  vpa: {
    name: 'Valproic Acid', formula: 'C8H16O2', energy: -2.71, safety: 63, offTarget: 2,
    atoms: [
      {t:'C',p:[0,0,0]},{t:'C',p:[.4,.3,.1]},{t:'C',p:[.8,0,.2]},{t:'C',p:[1.1,.4,0]},
      {t:'C',p:[-.4,.3,.2]},{t:'C',p:[-.8,0,.1]},{t:'C',p:[-1.1,.4,0]},{t:'C',p:[0,-.5,.3]},
      {t:'O',p:[.35,-.8,.1]},{t:'O',p:[-.1,-.9,-.2]}
    ],
    bonds: [[0,1],[1,2],[2,3],[0,4],[4,5],[5,6],[0,7],[7,8],[7,9]]
  },
  ltg: {
    name: 'Lamotrigine', formula: 'C9H7Cl2N5', energy: -2.84, safety: 88, offTarget: 0,
    atoms: [
      {t:'C',p:[0,0,0]},{t:'C',p:[.5,.4,0]},{t:'C',p:[1,.2,.1]},{t:'C',p:[1,-.4,.1]},
      {t:'C',p:[.5,-.6,0]},{t:'C',p:[0,-.5,0]},{t:'C',p:[-.5,.2,0]},{t:'C',p:[-.5,-.6,0]},
      {t:'C',p:[-1,-.2,0]},{t:'N',p:[-.3,.6,.1]},{t:'N',p:[-.8,.5,.1]},{t:'N',p:[-1,.4,.1]},
      {t:'N',p:[.2,.7,.1]},{t:'N',p:[-.5,.9,.1]},{t:'Cl',p:[1.5,.6,.2]},{t:'Cl',p:[1.5,-.7,.2]},
      {t:'H',p:[.2,1.1,0]},{t:'H',p:[-.2,1.2,0]}
    ],
    bonds: [[0,1],[1,2],[2,3],[3,4],[4,5],[5,0],[6,9],[9,10],[10,11],[11,8],[8,12],[12,6],[2,14],[3,15],[9,16],[12,17],[6,0]]
  },
  lev: {
    name: 'Levetiracetam', formula: 'C8H14N2O2', energy: -2.21, safety: 91, offTarget: 0,
    atoms: [
      {t:'C',p:[0,0,0]},{t:'C',p:[.4,.4,0]},{t:'C',p:[.8,0,.1]},{t:'C',p:[.4,-.5,.1]},
      {t:'C',p:[-.3,-.3,0]},{t:'N',p:[-.6,.3,.1]},{t:'C',p:[-1,0,0]},{t:'O',p:[-1.3,.4,.1]},
      {t:'O',p:[.8,.8,.1]},{t:'N',p:[-.8,-.5,0]}
    ],
    bonds: [[0,1],[1,2],[2,3],[3,4],[4,0],[0,5],[5,6],[6,7],[1,8],[4,9]]
  },
  tpm: {
    name: 'Topiramate', formula: 'C12H21NO8S', energy: -2.44, safety: 74, offTarget: 1,
    atoms: [
      {t:'C',p:[0,0,0]},{t:'C',p:[.5,.3,0]},{t:'C',p:[.8,-.2,.1]},{t:'O',p:[.3,-.5,.1]},
      {t:'C',p:[-.4,.4,0]},{t:'O',p:[-.7,0,.1]},{t:'C',p:[-1,.3,0]},{t:'N',p:[.2,.8,.1]},
      {t:'S',p:[1,.5,.2]},{t:'O',p:[1.3,.2,.1]},{t:'O',p:[1,.9,.2]}
    ],
    bonds: [[0,1],[1,2],[2,3],[3,0],[0,4],[4,5],[5,6],[1,7],[2,8],[8,9],[8,10]]
  },
  zns: {
    name: 'Zonisamide', formula: 'C8H8N2O3S', energy: -2.05, safety: 76, offTarget: 1,
    atoms: [
      {t:'C',p:[0,0,0]},{t:'C',p:[.4,.4,0]},{t:'C',p:[.8,.2,.1]},{t:'C',p:[.8,-.3,.1]},
      {t:'C',p:[.4,-.5,0]},{t:'C',p:[0,-.3,0]},{t:'N',p:[-.4,.3,.1]},{t:'S',p:[-.6,-.2,.1]},
      {t:'O',p:[-1,0,.2]},{t:'O',p:[-.6,-.7,.1]},{t:'N',p:[1,.5,.2]}
    ],
    bonds: [[0,1],[1,2],[2,3],[3,4],[4,5],[5,0],[0,6],[6,7],[7,8],[7,9],[2,10]]
  }
};

const ATOM_COLORS = {C:0x888888,O:0xff4444,N:0x4488ff,Cl:0x44cc44,H:0xcccccc,S:0xddaa22};
const ATOM_RADIUS = {C:.18,O:.2,N:.17,Cl:.22,H:.1,S:.2};

let molBindingInited = false;

function initMolecularBinding() {
  if (molBindingInited) return;
  molBindingInited = true;
  if (typeof THREE === 'undefined') return;

  const wrap = document.getElementById('mol-bind-wrap');
  if (!wrap) return;

  function createSim(canvasId, overlayId, drugKey, isLeft) {
    const container = document.getElementById(canvasId);
    if (!container) return null;
    const w = container.clientWidth || 500, h = container.clientHeight || 450;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060d1a);
    const camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
    camera.position.set(4, 2, 5);
    camera.lookAt(0, 0, 0);
    const renderer = new THREE.WebGLRenderer({antialias: true, alpha: false});
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Lighting
    scene.add(new THREE.AmbientLight(0x222244, 0.5));
    const dl = new THREE.DirectionalLight(0xffffff, 1.2);
    dl.position.set(5, 8, 5);
    scene.add(dl);
    scene.add(new THREE.PointLight(0x4488ff, 0.8, 20).position.set(-3, 2, 3) && new THREE.PointLight(0x4488ff, 0.8, 20));
    const pocketLight = new THREE.PointLight(isLeft ? 0xff2200 : 0x00ff88, 0.3, 8);
    scene.add(pocketLight);

    // Grid
    const grid = new THREE.GridHelper(20, 20, 0x0a1a30, 0x0a1a30);
    grid.position.y = -2;
    scene.add(grid);

    // Protein: Alpha helices
    const proteinGroup = new THREE.Group();
    for (let i = 0; i < 6; i++) {
      const pts = [];
      for (let t = 0; t <= 1; t += 1/60) {
        pts.push(new THREE.Vector3(0.3*Math.cos(t*3*2*Math.PI), t*2.5-1.25, 0.3*Math.sin(t*3*2*Math.PI)));
      }
      const curve = new THREE.CatmullRomCurve3(pts);
      const tubeGeo = new THREE.TubeGeometry(curve, 64, 0.08, 8, false);
      const tubeMat = new THREE.MeshPhongMaterial({color:0x1e50b4, shininess:60, transparent:true, opacity:0.85});
      const tube = new THREE.Mesh(tubeGeo, tubeMat);
      const angle = i * Math.PI / 3;
      tube.position.set(1.8*Math.cos(angle), 0, 1.8*Math.sin(angle));
      tube.rotation.y = angle;
      proteinGroup.add(tube);
    }

    // Beta sheets
    for (let j = -1; j <= 1; j++) {
      const planeGeo = new THREE.PlaneGeometry(1.2, 0.3);
      const planeMat = new THREE.MeshPhongMaterial({color:0x64c8dc, transparent:true, opacity:0.7, side:THREE.DoubleSide});
      const plane = new THREE.Mesh(planeGeo, planeMat);
      plane.position.set(0, j*0.5, 0);
      plane.rotation.y = j * 0.8;
      proteinGroup.add(plane);
    }

    // Binding pocket
    const pocketGeo = new THREE.ConeGeometry(0.6, 1.2, 16, 1, true);
    const pocketMat = new THREE.MeshStandardMaterial({color:0xFFD700, emissive:0xAA8800, emissiveIntensity:0.4, transparent:true, opacity:0.6});
    const pocket = new THREE.Mesh(pocketGeo, pocketMat);
    pocket.rotation.x = Math.PI;
    pocket.position.y = -0.2;
    proteinGroup.add(pocket);
    scene.add(proteinGroup);

    // Off-target markers (left only)
    const offTargetMarkers = [];
    if (isLeft) {
      const markers = [{pos:[-2.5,1,0.8], label:'AR'},{pos:[2.2,-0.8,1.5], label:'hERG'}];
      markers.forEach(m => {
        const g = new THREE.Group();
        for (let k = 0; k < 3; k++) {
          const s = new THREE.Mesh(new THREE.SphereGeometry(0.25, 12, 12), new THREE.MeshPhongMaterial({color:0xff4444, transparent:true, opacity:0.3}));
          s.position.set((k-1)*0.15, (k-1)*0.1, 0);
          g.add(s);
        }
        g.position.set(m.pos[0], m.pos[1], m.pos[2]);
        scene.add(g);
        offTargetMarkers.push(g);
      });
    }

    // Drug molecule builder
    function buildMolecule(key) {
      const drug = DRUG_DB[key];
      const mol = new THREE.Group();
      const atomMeshes = [];
      drug.atoms.forEach(a => {
        const sg = new THREE.SphereGeometry(ATOM_RADIUS[a.t]||0.15, 12, 12);
        const sm = new THREE.MeshPhongMaterial({color: ATOM_COLORS[a.t]||0x888888, shininess:40});
        const sp = new THREE.Mesh(sg, sm);
        sp.position.set(a.p[0], a.p[1], a.p[2]);
        mol.add(sp);
        atomMeshes.push(sp);
      });
      drug.bonds.forEach(b => {
        if (b[0] < drug.atoms.length && b[1] < drug.atoms.length) {
          const a1 = drug.atoms[b[0]].p, a2 = drug.atoms[b[1]].p;
          const start = new THREE.Vector3(a1[0],a1[1],a1[2]);
          const end = new THREE.Vector3(a2[0],a2[1],a2[2]);
          const dir = new THREE.Vector3().subVectors(end, start);
          const len = dir.length();
          const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.04,len,6), new THREE.MeshPhongMaterial({color:0x666666}));
          cyl.position.copy(start).add(dir.multiplyScalar(0.5));
          cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir.clone().normalize());
          mol.add(cyl);
        }
      });
      mol.position.set(0, 0, 6);
      return mol;
    }

    let molecule = buildMolecule(drugKey);
    scene.add(molecule);

    // Approach curve
    const approachCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0, 6), new THREE.Vector3(1.5, 1, 3), new THREE.Vector3(0.1, -0.3, 0.8)
    ]);

    // Trail particles
    const trailParticles = [];
    for (let i = 0; i < 20; i++) {
      const sp = new THREE.Mesh(new THREE.SphereGeometry(0.04,6,6), new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:0.3}));
      sp.visible = false;
      scene.add(sp);
      trailParticles.push(sp);
    }

    // Burst particles
    const burstParticles = [];
    for (let i = 0; i < 30; i++) {
      const color = isLeft ? 0xff6633 : 0x33ffaa;
      const sp = new THREE.Mesh(new THREE.SphereGeometry(0.06,6,6), new THREE.MeshBasicMaterial({color, transparent:true, opacity:0}));
      sp.userData.dir = new THREE.Vector3((Math.random()-0.5)*2, (Math.random()-0.5)*2, (Math.random()-0.5)*2).normalize();
      scene.add(sp);
      burstParticles.push(sp);
    }

    // Off-target particles
    const otParticles = [];
    if (isLeft) {
      for (let i = 0; i < 14; i++) {
        const sp = new THREE.Mesh(new THREE.SphereGeometry(0.05,6,6), new THREE.MeshBasicMaterial({color:0xff3333, transparent:true, opacity:0}));
        sp.visible = false;
        scene.add(sp);
        otParticles.push(sp);
      }
    }

    // Orbit controls (simple)
    let isDrag = false, prevMx = 0, prevMy = 0, camTheta = 0.8, camPhi = 0.3;
    const cvs = renderer.domElement;
    cvs.addEventListener('mousedown', e => { isDrag = true; prevMx = e.clientX; prevMy = e.clientY; });
    cvs.addEventListener('mousemove', e => {
      if (!isDrag) return;
      camTheta += (e.clientX - prevMx) * 0.005;
      camPhi = Math.max(-1, Math.min(1, camPhi + (e.clientY - prevMy) * 0.005));
      prevMx = e.clientX; prevMy = e.clientY;
    });
    cvs.addEventListener('mouseup', () => isDrag = false);
    cvs.addEventListener('mouseleave', () => isDrag = false);

    let frame = 0;
    let currentDrug = drugKey;

    function animate() {
      requestAnimationFrame(animate);
      frame++;
      const phase = frame % 300;
      const drug = DRUG_DB[currentDrug];

      // Phase 1: Approach (0-119)
      if (phase < 120) {
        const t = phase / 120;
        const pt = approachCurve.getPoint(t);
        molecule.position.copy(pt);
        molecule.rotation.y += 0.02;
        // Trail
        trailParticles.forEach((tp, i) => {
          const tt = Math.max(0, t - i * 0.015);
          if (tt > 0) { tp.visible = true; tp.position.copy(approachCurve.getPoint(tt)); tp.material.opacity = 0.3 * (1 - i/20); }
          else tp.visible = false;
        });
        burstParticles.forEach(bp => { bp.material.opacity = 0; });
      }
      // Phase 2: Binding (120-179)
      else if (phase < 180) {
        const t2 = (phase - 120) / 60;
        molecule.position.set(0.1 + Math.sin(frame*0.5)*0.02, -0.3 + Math.cos(frame*0.7)*0.02, 0.8 + Math.sin(frame*0.3)*0.02);
        molecule.rotation.y += 0.005;
        trailParticles.forEach(tp => { tp.visible = false; });
        // Burst
        if (phase === 120) {
          burstParticles.forEach(bp => { bp.position.set(0.1, -0.3, 0.8); bp.material.opacity = 1; });
        }
        burstParticles.forEach(bp => {
          bp.position.add(bp.userData.dir.clone().multiplyScalar(0.04));
          bp.material.opacity = Math.max(0, 1 - t2 * 1.5);
        });
        // Pocket glow
        pocketMat.emissiveIntensity = 0.5 + Math.max(0, 1 - t2 * 2);
      }
      // Phase 3: Off-target (180-299)
      else {
        const t3 = (phase - 180) / 120;
        molecule.position.set(0.1 + Math.sin(frame*0.5)*0.015, -0.3 + Math.cos(frame*0.7)*0.015, 0.8);
        pocketMat.emissiveIntensity = 0.4 + Math.sin(frame*0.1)*0.2;

        if (isLeft && drug.offTarget > 0) {
          otParticles.forEach((op, i) => {
            op.visible = true;
            const targetIdx = i < 8 ? 0 : 1;
            if (targetIdx === 1 && drug.offTarget < 2) { op.visible = false; return; }
            const target = targetIdx === 0 ? new THREE.Vector3(-2.5,1,0.8) : new THREE.Vector3(2.2,-0.8,1.5);
            const start = new THREE.Vector3(0.1, -0.3, 0.8);
            op.position.lerpVectors(start, target, Math.min(1, t3 * 1.5));
            op.material.opacity = t3 < 0.7 ? 0.8 : Math.max(0, 0.8 * (1 - (t3-0.7)/0.3));
            if (t3 > 0.6) {
              offTargetMarkers.forEach(m => {
                m.children.forEach(c => { c.material.opacity = 0.6 + Math.sin(frame*0.3)*0.4; });
              });
            }
          });
        } else if (isLeft) {
          otParticles.forEach(op => { op.visible = false; });
        }
      }

      // Camera orbit
      if (!isDrag) camTheta += 0.001;
      const camR = 5;
      camera.position.set(camR*Math.cos(camPhi)*Math.sin(camTheta), camR*Math.sin(camPhi)+0.5, camR*Math.cos(camPhi)*Math.cos(camTheta));
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);

      // Update overlay
      updateOverlay(overlayId, drug, phase, isLeft);
    }

    animate();

    return {
      switchDrug: function(key) {
        currentDrug = key;
        scene.remove(molecule);
        molecule = buildMolecule(key);
        scene.add(molecule);
        frame = 0;
      }
    };
  }

  // EEG canvas drawer
  function drawEEG(canvas, chaotic) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = chaotic ? '#ff6b6b' : '#20c997';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    const t = Date.now() * 0.003;
    for (let x = 0; x < w; x++) {
      const nx = x / w * 8;
      let y;
      if (chaotic) {
        y = h/2 + Math.sin(nx*3+t)*8 + Math.sin(nx*7+t*1.3)*6 + Math.random()*4 + Math.sin(nx*13+t*0.7)*3;
      } else {
        y = h/2 + Math.sin(nx*2+t)*10;
      }
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  function updateOverlay(id, drug, phase, isLeft) {
    const el = document.getElementById(id);
    if (!el) return;
    const phaseLabel = phase < 120 ? 'APPROACH' : phase < 180 ? 'BINDING' : 'SCANNING';
    const phaseColor = phase < 120 ? '#4DB8FF' : phase < 180 ? '#FFD700' : (drug.offTarget > 0 && isLeft ? '#ff6b6b' : '#20c997');
    el.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:${isLeft?'#ff6b6b':'#20c997'};border:1px solid ${isLeft?'rgba(255,107,107,0.3)':'rgba(32,201,151,0.3)'};padding:3px 8px;border-radius:4px;">${isLeft?'CURRENT DRUG':'RECOMMENDED'}</span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:9px;color:${phaseColor};letter-spacing:1px;">${phaseLabel}</span>
      </div>
      <div style="font-family:'Outfit',sans-serif;font-size:16px;font-weight:600;color:#fff;margin-bottom:12px;">${drug.name}</div>
      <div style="display:flex;gap:16px;font-family:'JetBrains Mono',monospace;font-size:10px;">
        <div><span style="color:var(--text2);">BINDING</span><br/><span style="color:#FFD700;font-size:13px;">${drug.energy} eV</span></div>
        <div><span style="color:var(--text2);">OFF-TARGET</span><br/><span style="color:${drug.offTarget>0&&isLeft?'#ff6b6b':'#20c997'};font-size:13px;">${isLeft?drug.offTarget:0}</span></div>
        <div><span style="color:var(--text2);">SAFETY</span><br/><span style="color:${drug.safety>=80?'#20c997':drug.safety>=70?'#FCC419':'#ff6b6b'};font-size:13px;">${drug.safety}/100</span></div>
      </div>
      <canvas id="eeg-${id}" width="200" height="30" style="margin-top:8px;width:100%;"></canvas>
    `;
    drawEEG(document.getElementById('eeg-'+id), isLeft && drug.offTarget > 0);
  }

  // Initialize both simulations
  const leftSim = createSim('mol-canvas-left', 'mol-overlay-left', 'vpa', true);
  const rightSim = createSim('mol-canvas-right', 'mol-overlay-right', 'ltg', false);

  // Drug switcher dropdowns
  const selLeft = document.getElementById('mol-drug-left');
  const selRight = document.getElementById('mol-drug-right');
  if (selLeft && leftSim) selLeft.addEventListener('change', () => leftSim.switchDrug(selLeft.value));
  if (selRight && rightSim) selRight.addEventListener('change', () => rightSim.switchDrug(selRight.value));
}
