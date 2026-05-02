// ═══════════════════════════════════════════════════════════
// MOLECULAR BINDING COLLISION SIMULATOR - CINEMATIC EDITION
// Three.js dual-canvas drug binding visualization with advanced effects
// Enhanced with: Advanced lighting, smooth camera animations, custom shaders,
// particle effects, bloom post-processing, and cinematic rendering
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

// ═══════════════════════════════════════════════════════════
// CINEMATIC ENHANCEMENT UTILITIES
// ═══════════════════════════════════════════════════════════

// Easing functions for smooth animations
const Easing = {
  easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  easeOutElastic: t => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },
  easeInOutQuad: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
  easeOutCubic: t => 1 - Math.pow(1 - t, 3)
};

// Custom shader materials for cinematic effects
const CustomShaders = {
  // Fresnel shader for rim lighting effect
  fresnelVertex: `
    varying vec3 vNormal;
    varying vec3 vViewPosition;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      vViewPosition = -mvPosition.xyz;
      gl_Position = projectionMatrix * mvPosition;
    }
  `,
  fresnelFragment: `
    uniform vec3 baseColor;
    uniform vec3 rimColor;
    uniform float rimPower;
    uniform float rimIntensity;
    varying vec3 vNormal;
    varying vec3 vViewPosition;
    void main() {
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);
      float fresnel = pow(1.0 - max(0.0, dot(normal, viewDir)), rimPower);
      vec3 color = mix(baseColor, rimColor, fresnel * rimIntensity);
      gl_FragColor = vec4(color, 1.0);
    }
  `,
  // Glow shader for binding sites
  glowVertex: `
    varying vec3 vNormal;
    varying vec3 vPosition;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      vPosition = position;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  glowFragment: `
    uniform vec3 glowColor;
    uniform float glowIntensity;
    uniform float time;
    varying vec3 vNormal;
    varying vec3 vPosition;
    void main() {
      float pulse = 0.5 + 0.5 * sin(time * 2.0);
      float intensity = glowIntensity * (0.8 + 0.2 * pulse);
      vec3 color = glowColor * intensity;
      gl_FragColor = vec4(color, 0.6);
    }
  `
};

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
    scene.fog = new THREE.FogExp2(0x060d1a, 0.02);
    
    const camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
    camera.position.set(4, 2, 5);
    camera.lookAt(0, 0, 0);
    
    // Enhanced renderer with shadows
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance'
    });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // ═══ CINEMATIC LIGHTING SYSTEM ═══
    const ambientLight = new THREE.AmbientLight(0x1a2332, 0.4);
    scene.add(ambientLight);
    
    const hemiLight = new THREE.HemisphereLight(0x4488ff, 0x1a0a2e, 0.6);
    hemiLight.position.set(0, 20, 0);
    scene.add(hemiLight);
    
    const mainLight = new THREE.DirectionalLight(0xffffff, 1.5);
    mainLight.position.set(8, 12, 6);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    mainLight.shadow.camera.near = 0.5;
    mainLight.shadow.camera.far = 50;
    mainLight.shadow.bias = -0.0001;
    scene.add(mainLight);
    
    const rimLight = new THREE.DirectionalLight(0x6699ff, 0.8);
    rimLight.position.set(-5, 3, -5);
    scene.add(rimLight);
    
    const accentLight1 = new THREE.PointLight(0x4488ff, 1.2, 25);
    accentLight1.position.set(-4, 3, 4);
    scene.add(accentLight1);
    
    const accentLight2 = new THREE.PointLight(0x8844ff, 0.9, 20);
    accentLight2.position.set(4, 2, -3);
    scene.add(accentLight2);
    
    const pocketLight = new THREE.PointLight(isLeft ? 0xff3300 : 0x00ffaa, 0.5, 10);
    pocketLight.position.set(0, -0.2, 0);
    scene.add(pocketLight);
    
    const spotLight = new THREE.SpotLight(0xffffff, 0.8);
    spotLight.position.set(0, 10, 0);
    spotLight.angle = Math.PI / 6;
    spotLight.penumbra = 0.3;
    spotLight.decay = 2;
    spotLight.distance = 30;
    scene.add(spotLight);

    // Grid
    const grid = new THREE.GridHelper(20, 20, 0x0a1a30, 0x0a1a30);
    grid.position.y = -2;
    scene.add(grid);

    // ═══ ENHANCED PROTEIN RENDERING ═══
    const proteinGroup = new THREE.Group();
    
    // Alpha helices with Fresnel rim lighting
    for (let i = 0; i < 6; i++) {
      const pts = [];
      for (let t = 0; t <= 1; t += 1/80) {
        const radius = 0.35 + Math.sin(t * Math.PI * 6) * 0.05;
        pts.push(new THREE.Vector3(
          radius * Math.cos(t * 3 * 2 * Math.PI),
          t * 2.5 - 1.25,
          radius * Math.sin(t * 3 * 2 * Math.PI)
        ));
      }
      const curve = new THREE.CatmullRomCurve3(pts);
      const tubeGeo = new THREE.TubeGeometry(curve, 80, 0.1, 12, false);
      
      // Custom shader material with Fresnel effect
      const tubeMat = new THREE.ShaderMaterial({
        uniforms: {
          baseColor: { value: new THREE.Color(0x1e50b4) },
          rimColor: { value: new THREE.Color(0x4488ff) },
          rimPower: { value: 3.0 },
          rimIntensity: { value: 0.8 }
        },
        vertexShader: CustomShaders.fresnelVertex,
        fragmentShader: CustomShaders.fresnelFragment,
        transparent: true,
        opacity: 0.9
      });
      
      const tube = new THREE.Mesh(tubeGeo, tubeMat);
      tube.castShadow = true;
      tube.receiveShadow = true;
      const angle = i * Math.PI / 3;
      tube.position.set(1.8 * Math.cos(angle), 0, 1.8 * Math.sin(angle));
      tube.rotation.y = angle;
      proteinGroup.add(tube);
    }

    // Beta sheets with gradient and metallic finish
    for (let j = -1; j <= 1; j++) {
      const planeGeo = new THREE.PlaneGeometry(1.4, 0.35, 10, 10);
      const planeMat = new THREE.MeshStandardMaterial({
        color: 0x64c8dc,
        metalness: 0.3,
        roughness: 0.4,
        transparent: true,
        opacity: 0.75,
        side: THREE.DoubleSide,
        emissive: 0x2244aa,
        emissiveIntensity: 0.2
      });
      const plane = new THREE.Mesh(planeGeo, planeMat);
      plane.castShadow = true;
      plane.receiveShadow = true;
      plane.position.set(0, j * 0.5, 0);
      plane.rotation.y = j * 0.8;
      proteinGroup.add(plane);
    }

    // Binding pocket with glow shader
    const pocketGeo = new THREE.ConeGeometry(0.65, 1.3, 24, 1, true);
    const pocketMat = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(isLeft ? 0xff6600 : 0x00ffaa) },
        glowIntensity: { value: 1.5 },
        time: { value: 0 }
      },
      vertexShader: CustomShaders.glowVertex,
      fragmentShader: CustomShaders.glowFragment,
      transparent: true,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    const pocket = new THREE.Mesh(pocketGeo, pocketMat);
    pocket.rotation.x = Math.PI;
    pocket.position.y = -0.2;
    proteinGroup.add(pocket);
    
    // Add glow particles around binding site
    const glowParticles = [];
    for (let i = 0; i < 40; i++) {
      const angle = (i / 40) * Math.PI * 2;
      const radius = 0.7 + Math.random() * 0.2;
      const particleGeo = new THREE.SphereGeometry(0.02, 8, 8);
      const particleMat = new THREE.MeshBasicMaterial({
        color: isLeft ? 0xff6600 : 0x00ffaa,
        transparent: true,
        opacity: 0.6
      });
      const particle = new THREE.Mesh(particleGeo, particleMat);
      particle.position.set(
        Math.cos(angle) * radius,
        -0.2 + (Math.random() - 0.5) * 0.4,
        Math.sin(angle) * radius
      );
      particle.userData.angle = angle;
      particle.userData.radius = radius;
      particle.userData.speed = 0.5 + Math.random() * 0.5;
      glowParticles.push(particle);
      proteinGroup.add(particle);
    }
    
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

    // ═══ ENHANCED DRUG MOLECULE BUILDER ═══
    function buildMolecule(key) {
      const drug = DRUG_DB[key];
      const mol = new THREE.Group();
      const atomMeshes = [];
      
      drug.atoms.forEach(a => {
        const sg = new THREE.SphereGeometry(ATOM_RADIUS[a.t] || 0.15, 16, 16);
        const sm = new THREE.MeshStandardMaterial({
          color: ATOM_COLORS[a.t] || 0x888888,
          metalness: 0.4,
          roughness: 0.3,
          emissive: ATOM_COLORS[a.t] || 0x888888,
          emissiveIntensity: 0.1
        });
        const sp = new THREE.Mesh(sg, sm);
        sp.position.set(a.p[0], a.p[1], a.p[2]);
        sp.castShadow = true;
        sp.receiveShadow = true;
        mol.add(sp);
        atomMeshes.push(sp);
      });
      
      drug.bonds.forEach(b => {
        if (b[0] < drug.atoms.length && b[1] < drug.atoms.length) {
          const a1 = drug.atoms[b[0]].p, a2 = drug.atoms[b[1]].p;
          const start = new THREE.Vector3(a1[0], a1[1], a1[2]);
          const end = new THREE.Vector3(a2[0], a2[1], a2[2]);
          const dir = new THREE.Vector3().subVectors(end, start);
          const len = dir.length();
          const cyl = new THREE.Mesh(
            new THREE.CylinderGeometry(0.05, 0.05, len, 8),
            new THREE.MeshStandardMaterial({
              color: 0x888888,
              metalness: 0.5,
              roughness: 0.4
            })
          );
          cyl.position.copy(start).add(dir.multiplyScalar(0.5));
          cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
          cyl.castShadow = true;
          cyl.receiveShadow = true;
          mol.add(cyl);
        }
      });
      
      mol.position.set(0, 0, 6);
      mol.userData.atomMeshes = atomMeshes;
      return mol;
    }

    let molecule = buildMolecule(drugKey);
    scene.add(molecule);

    // Approach curve
    const approachCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0, 6), new THREE.Vector3(1.5, 1, 3), new THREE.Vector3(0.1, -0.3, 0.8)
    ]);

    // ═══ ENHANCED PARTICLE SYSTEMS ═══
    // Trail particles with glow
    const trailParticles = [];
    for (let i = 0; i < 30; i++) {
      const sp = new THREE.Mesh(
        new THREE.SphereGeometry(0.05, 8, 8),
        new THREE.MeshBasicMaterial({
          color: isLeft ? 0xff6633 : 0x33ffaa,
          transparent: true,
          opacity: 0.5,
          blending: THREE.AdditiveBlending
        })
      );
      sp.visible = false;
      scene.add(sp);
      trailParticles.push(sp);
    }

    // Burst particles with radial expansion
    const burstParticles = [];
    for (let i = 0; i < 50; i++) {
      const color = isLeft ? 0xff6633 : 0x33ffaa;
      const sp = new THREE.Mesh(
        new THREE.SphereGeometry(0.08, 8, 8),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0,
          blending: THREE.AdditiveBlending
        })
      );
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      sp.userData.dir = new THREE.Vector3(
        Math.sin(phi) * Math.cos(theta),
        Math.sin(phi) * Math.sin(theta),
        Math.cos(phi)
      );
      sp.userData.speed = 0.03 + Math.random() * 0.02;
      scene.add(sp);
      burstParticles.push(sp);
    }
    
    // Energy field particles
    const energyParticles = [];
    for (let i = 0; i < 60; i++) {
      const sp = new THREE.Mesh(
        new THREE.SphereGeometry(0.03, 6, 6),
        new THREE.MeshBasicMaterial({
          color: isLeft ? 0xff8844 : 0x44ffcc,
          transparent: true,
          opacity: 0,
          blending: THREE.AdditiveBlending
        })
      );
      sp.userData.offset = Math.random() * Math.PI * 2;
      sp.userData.radius = 0.8 + Math.random() * 0.4;
      sp.userData.height = (Math.random() - 0.5) * 0.6;
      sp.userData.speed = 0.5 + Math.random() * 1.0;
      scene.add(sp);
      energyParticles.push(sp);
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
      const time = frame * 0.016; // Approximate time in seconds

      // Update shader uniforms
      if (pocketMat.uniforms) {
        pocketMat.uniforms.time.value = time;
      }

      // ═══ PHASE 1: APPROACH (0-119) ═══
      if (phase < 120) {
        const t = Easing.easeInOutCubic(phase / 120);
        const rawT = phase / 120;
        const pt = approachCurve.getPoint(t);
        molecule.position.copy(pt);
        molecule.rotation.y += 0.02;
        molecule.rotation.x = Math.sin(time * 0.5) * 0.1;
        
        // Enhanced trail with fade
        trailParticles.forEach((tp, i) => {
          const tt = Math.max(0, rawT - i * 0.01);
          if (tt > 0) {
            tp.visible = true;
            tp.position.copy(approachCurve.getPoint(tt));
            const fadeOut = 1 - (i / trailParticles.length);
            tp.material.opacity = 0.6 * fadeOut * Math.sin(time * 3 + i * 0.5);
            tp.scale.setScalar(0.5 + fadeOut * 0.5);
          } else {
            tp.visible = false;
          }
        });
        
        burstParticles.forEach(bp => { bp.material.opacity = 0; });
        energyParticles.forEach(ep => { ep.material.opacity = 0; });
      }
      // ═══ PHASE 2: BINDING (120-179) ═══
      else if (phase < 180) {
        const t2 = (phase - 120) / 60;
        const easedT2 = Easing.easeOutCubic(t2);
        
        // Subtle binding vibration
        molecule.position.set(
          0.1 + Math.sin(time * 2) * 0.015,
          -0.3 + Math.cos(time * 2.5) * 0.015,
          0.8 + Math.sin(time * 1.8) * 0.01
        );
        molecule.rotation.y += 0.005;
        molecule.rotation.z = Math.sin(time * 1.5) * 0.05;
        
        trailParticles.forEach(tp => { tp.visible = false; });
        
        // Enhanced burst with easing
        if (phase === 120) {
          burstParticles.forEach(bp => {
            bp.position.set(0.1, -0.3, 0.8);
            bp.material.opacity = 1;
            bp.scale.setScalar(0.5);
          });
        }
        
        burstParticles.forEach(bp => {
          bp.position.add(bp.userData.dir.clone().multiplyScalar(bp.userData.speed));
          bp.material.opacity = Math.max(0, (1 - easedT2) * 0.9);
          bp.scale.setScalar(0.5 + easedT2 * 1.5);
        });
        
        // Pulsing pocket glow
        if (pocketMat.uniforms) {
          pocketMat.uniforms.glowIntensity.value = 1.5 + Math.sin(time * 3) * 0.5 + (1 - easedT2) * 2;
        }
        
        // Energy field activation
        energyParticles.forEach((ep, i) => {
          const angle = time * ep.userData.speed + ep.userData.offset;
          ep.position.set(
            Math.cos(angle) * ep.userData.radius,
            -0.2 + ep.userData.height + Math.sin(time * 2 + i) * 0.1,
            Math.sin(angle) * ep.userData.radius
          );
          ep.material.opacity = easedT2 * 0.7 * (0.5 + Math.sin(time * 4 + i) * 0.5);
        });
        
        // Animate glow particles
        glowParticles.forEach((gp, i) => {
          const angle = time * gp.userData.speed + gp.userData.angle;
          gp.position.set(
            Math.cos(angle) * gp.userData.radius,
            -0.2 + Math.sin(time * 2 + i * 0.1) * 0.05,
            Math.sin(angle) * gp.userData.radius
          );
          gp.material.opacity = 0.4 + Math.sin(time * 3 + i * 0.2) * 0.3;
        });
        
        // Dynamic lighting
        pocketLight.intensity = 0.5 + (1 - easedT2) * 1.5 + Math.sin(time * 4) * 0.3;
      }
      // ═══ PHASE 3: BOUND STATE (180-299) ═══
      else {
        const t3 = (phase - 180) / 120;
        
        // Stable bound state with micro-movements
        molecule.position.set(
          0.1 + Math.sin(time) * 0.01,
          -0.3 + Math.cos(time * 1.2) * 0.01,
          0.8
        );
        molecule.rotation.y += 0.002;
        
        // Steady glow
        if (pocketMat.uniforms) {
          pocketMat.uniforms.glowIntensity.value = 1.2 + Math.sin(time * 2) * 0.3;
        }
        
        // Continuous energy field
        energyParticles.forEach((ep, i) => {
          const angle = time * ep.userData.speed + ep.userData.offset;
          ep.position.set(
            Math.cos(angle) * ep.userData.radius,
            -0.2 + ep.userData.height + Math.sin(time * 2 + i) * 0.1,
            Math.sin(angle) * ep.userData.radius
          );
          ep.material.opacity = 0.5 * (0.6 + Math.sin(time * 3 + i) * 0.4);
        });
        
        // Glow particles orbit
        glowParticles.forEach((gp, i) => {
          const angle = time * gp.userData.speed + gp.userData.angle;
          gp.position.set(
            Math.cos(angle) * gp.userData.radius,
            -0.2 + Math.sin(time * 2 + i * 0.1) * 0.05,
            Math.sin(angle) * gp.userData.radius
          );
          gp.material.opacity = 0.5 + Math.sin(time * 2 + i * 0.2) * 0.2;
        });

        // Off-target effects
        if (isLeft && drug.offTarget > 0) {
          otParticles.forEach((op, i) => {
            op.visible = true;
            const targetIdx = i < 8 ? 0 : 1;
            if (targetIdx === 1 && drug.offTarget < 2) { op.visible = false; return; }
            const target = targetIdx === 0 ? new THREE.Vector3(-2.5, 1, 0.8) : new THREE.Vector3(2.2, -0.8, 1.5);
            const start = new THREE.Vector3(0.1, -0.3, 0.8);
            const easedT3 = Easing.easeInOutQuad(Math.min(1, t3 * 1.5));
            op.position.lerpVectors(start, target, easedT3);
            op.material.opacity = t3 < 0.7 ? 0.8 : Math.max(0, 0.8 * (1 - (t3 - 0.7) / 0.3));
            if (t3 > 0.6) {
              offTargetMarkers.forEach(m => {
                m.children.forEach(c => { c.material.opacity = 0.6 + Math.sin(time * 3) * 0.4; });
              });
            }
          });
        } else if (isLeft) {
          otParticles.forEach(op => { op.visible = false; });
        }
        
        pocketLight.intensity = 0.5 + Math.sin(time * 2) * 0.2;
      }

      // ═══ CINEMATIC CAMERA SYSTEM ═══
      if (!isDrag) {
        // Smooth orbital rotation
        camTheta += 0.002;
        
        // Dynamic camera distance based on phase
        let targetCamR = 5;
        let targetCamPhi = 0.3;
        
        if (phase < 120) {
          // Wide shot during approach
          targetCamR = 6 + Math.sin(time * 0.5) * 0.5;
          targetCamPhi = 0.4;
        } else if (phase < 180) {
          // Close-up during binding
          targetCamR = 3.5 + Math.sin(time * 2) * 0.3;
          targetCamPhi = 0.2;
        } else {
          // Medium shot for bound state
          targetCamR = 4.5 + Math.sin(time * 0.8) * 0.4;
          targetCamPhi = 0.25;
        }
        
        // Smooth camera transitions
        const camR = camera.position.length();
        const newCamR = camR + (targetCamR - camR) * 0.02;
        camPhi += (targetCamPhi - camPhi) * 0.02;
        
        camera.position.set(
          newCamR * Math.cos(camPhi) * Math.sin(camTheta),
          newCamR * Math.sin(camPhi) + 0.5,
          newCamR * Math.cos(camPhi) * Math.cos(camTheta)
        );
      } else {
        // Manual control
        const camR = 5;
        camera.position.set(
          camR * Math.cos(camPhi) * Math.sin(camTheta),
          camR * Math.sin(camPhi) + 0.5,
          camR * Math.cos(camPhi) * Math.cos(camTheta)
        );
      }
      
      camera.lookAt(0, 0, 0);
      
      // Render scene
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
