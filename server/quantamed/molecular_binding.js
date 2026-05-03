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
    scene.fog = new THREE.FogExp2(0x060d1a, 0.08);
    
    const camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
    camera.position.set(5, 3, 5);
    camera.lookAt(0, 1.0, 0);
    
    // Enhanced renderer with shadows and advanced settings
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
      stencil: false,
      depth: true
    });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.8;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.physicallyCorrectLights = true;
    container.appendChild(renderer.domElement);

    // ═══ CINEMATIC LIGHTING SYSTEM ═══
    const ambientLight = new THREE.AmbientLight(0x6688bb, 0.8);
    scene.add(ambientLight);
    
    const hemiLight = new THREE.HemisphereLight(0x88aaff, 0x1a0a2e, 1.2);
    hemiLight.position.set(0, 20, 0);
    scene.add(hemiLight);
    
    const mainLight = new THREE.DirectionalLight(0xffffff, 2.5);
    mainLight.position.set(8, 12, 6);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    mainLight.shadow.camera.near = 0.5;
    mainLight.shadow.camera.far = 50;
    mainLight.shadow.bias = -0.0001;
    scene.add(mainLight);
    
    const rimLight = new THREE.DirectionalLight(0x6699ff, 1.4);
    rimLight.position.set(-5, 3, -5);
    scene.add(rimLight);
    
    const accentLight1 = new THREE.PointLight(0x4488ff, 2.0, 25);
    accentLight1.position.set(-4, 3, 4);
    scene.add(accentLight1);
    
    const accentLight2 = new THREE.PointLight(0x8844ff, 1.5, 20);
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

    // ═══ LIPID BILAYER MEMBRANE ═══
    const membraneGroup = new THREE.Group();
    const membGeo = new THREE.PlaneGeometry(12, 8, 60, 40);
    const membPos = membGeo.attributes.position;
    for (let i = 0; i < membPos.count; i++) {
      const x = membPos.getX(i), y = membPos.getY(i);
      membPos.setZ(i, Math.sin(x*1.2)*0.04 + Math.cos(y*1.5)*0.03);
    }
    membGeo.computeVertexNormals();
    const membMat = new THREE.MeshPhysicalMaterial({
      color: 0x88ddcc, metalness: 0.0, roughness: 0.6,
      transparent: true, opacity: 0.35, side: THREE.DoubleSide,
      emissive: 0x44aa99, emissiveIntensity: 0.2
    });
    const membrane = new THREE.Mesh(membGeo, membMat);
    membrane.rotation.x = -Math.PI / 2;
    membrane.position.y = 0;
    membraneGroup.add(membrane);
    const memb2 = membrane.clone();
    memb2.position.y = -0.15;
    memb2.material = membMat.clone();
    memb2.material.opacity = 0.18;
    membraneGroup.add(memb2);
    // Lipid head particles
    for (let i = 0; i < 250; i++) {
      const x = (Math.random()-0.5)*11, z = (Math.random()-0.5)*7;
      if (Math.sqrt(x*x+z*z) < 0.8) continue;
      const hGeo = new THREE.SphereGeometry(0.035, 6, 6);
      const isTop = Math.random() > 0.5;
      const hMat = new THREE.MeshPhysicalMaterial({
        color: isTop ? 0xcceeee : 0xaaddcc, transparent: true, opacity: 0.3, roughness: 0.8
      });
      const head = new THREE.Mesh(hGeo, hMat);
      head.position.set(x, isTop ? 0.08 : -0.23, z);
      membraneGroup.add(head);
    }
    scene.add(membraneGroup);

    // ═══ PROTEIN RENDERING ENGINES ═══
    let proteinGroup = new THREE.Group();
    scene.add(proteinGroup);
    
    // Mode 1: Scientific Ribbon Engine (Flat ribbons and arrows)
    
    // Create high-fidelity alpha helix ribbons (flat ribbon look)
    function createAlphaHelix(startPos, length, turns, color) {
      const helixGroup = new THREE.Group();
      const pointsPerTurn = 50;
      const totalPoints = turns * pointsPerTurn;
      
      const backbonePts = [];
      for (let i = 0; i <= totalPoints; i++) {
        const t = i / totalPoints;
        const angle = t * turns * 2 * Math.PI;
        const y = t * length;
        const radius = 0.3;
        backbonePts.push(new THREE.Vector3(
          Math.cos(angle) * radius, y, Math.sin(angle) * radius
        ));
      }
      
      const backboneCurve = new THREE.CatmullRomCurve3(backbonePts);
      const ribbonWidth = 0.45;
      const ribbonThickness = 0.05;
      const segments = totalPoints;
      
      const ribbonGeometry = new THREE.BufferGeometry();
      const positions = [];
      const normals = [];
      const indices = [];
      
      for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const point = backboneCurve.getPoint(t);
        const tangent = backboneCurve.getTangent(t).normalize();
        
        // Calculate perpendicular vectors for the ribbon orientation
        // We want the ribbon face to point away from the helix axis
        const axisPoint = new THREE.Vector3(0, point.y, 0);
        const radialDir = new THREE.Vector3().subVectors(point, axisPoint).normalize();
        const sideDir = new THREE.Vector3().crossVectors(tangent, radialDir).normalize();
        
        const hw = ribbonWidth / 2;
        const ht = ribbonThickness / 2;
        
        // Create ribbon cross-section (4 vertices: TopLeft, TopRight, BottomLeft, BottomRight)
        // Face points out (radialDir)
        positions.push(
          point.x - sideDir.x * hw + radialDir.x * ht, point.y - sideDir.y * hw + radialDir.y * ht, point.z - sideDir.z * hw + radialDir.z * ht,
          point.x + sideDir.x * hw + radialDir.x * ht, point.y + sideDir.y * hw + radialDir.y * ht, point.z + sideDir.z * hw + radialDir.z * ht,
          point.x - sideDir.x * hw - radialDir.x * ht, point.y - sideDir.y * hw - radialDir.y * ht, point.z - sideDir.z * hw - radialDir.z * ht,
          point.x + sideDir.x * hw - radialDir.x * ht, point.y + sideDir.y * hw - radialDir.y * ht, point.z + sideDir.z * hw - radialDir.z * ht
        );
        
        // Simplified normals
        for (let j = 0; j < 2; j++) normals.push(radialDir.x, radialDir.y, radialDir.z);
        for (let j = 0; j < 2; j++) normals.push(-radialDir.x, -radialDir.y, -radialDir.z);
        
        if (i < segments) {
          const base = i * 4;
          // Outer face
          indices.push(base, base + 1, base + 5);
          indices.push(base, base + 5, base + 4);
          // Inner face
          indices.push(base + 2, base + 6, base + 7);
          indices.push(base + 2, base + 7, base + 3);
          // Edge faces
          indices.push(base, base + 4, base + 6);
          indices.push(base, base + 6, base + 2);
          indices.push(base + 1, base + 7, base + 5);
          indices.push(base + 1, base + 3, base + 7);
        }
      }
      
      ribbonGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      ribbonGeometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
      ribbonGeometry.setIndex(indices);
      
      const ribbonMat = new THREE.MeshPhysicalMaterial({
        color: color, metalness: 0.1, roughness: 0.3,
        transparent: true, opacity: 0.95, side: THREE.DoubleSide,
        emissive: color, emissiveIntensity: 0.35,
        clearcoat: 0.4, clearcoatRoughness: 0.2
      });
      
      const ribbon = new THREE.Mesh(ribbonGeometry, ribbonMat);
      ribbon.castShadow = true;
      ribbon.receiveShadow = true;
      ribbon.position.copy(startPos);
      helixGroup.add(ribbon);
      return helixGroup;
    }
    
    // Create sharp beta sheet arrows
    function createBetaSheet(startPos, endPos, width, color) {
      const sheetGroup = new THREE.Group();
      const direction = new THREE.Vector3().subVectors(endPos, startPos);
      const length = direction.length();
      direction.normalize();
      
      const sheetGeometry = new THREE.BufferGeometry();
      const positions = [];
      const normals = [];
      const indices = [];
      
      const segments = 10;
      const thickness = 0.04;
      
      for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const y = t * length;
        
        // Taper to arrow point at the end
        let currentWidth = width;
        if (t > 0.75) {
          const arrowT = (t - 0.75) / 0.25;
          currentWidth = width * 1.5 * (1 - arrowT);
        }
        
        const hw = currentWidth / 2;
        const ht = thickness / 2;
        
        positions.push(-hw, y, ht,  hw, y, ht); // Top
        positions.push(-hw, y, -ht, hw, y, -ht); // Bottom
        
        normals.push(0, 0, 1, 0, 0, 1, 0, 0, -1, 0, 0, -1);
        
        if (i < segments) {
          const base = i * 4;
          indices.push(base, base + 1, base + 5);
          indices.push(base, base + 5, base + 4);
          indices.push(base + 2, base + 6, base + 7);
          indices.push(base + 2, base + 7, base + 3);
          // Sides
          indices.push(base, base + 4, base + 6);
          indices.push(base, base + 6, base + 2);
          indices.push(base + 1, base + 7, base + 5);
          indices.push(base + 1, base + 3, base + 7);
        }
      }
      
      sheetGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      sheetGeometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
      sheetGeometry.setIndex(indices);
      
      const sheetMat = new THREE.MeshPhysicalMaterial({
        color: color, metalness: 0.15, roughness: 0.2,
        transparent: true, opacity: 0.95, side: THREE.DoubleSide,
        emissive: color, emissiveIntensity: 0.3,
        clearcoat: 0.5, clearcoatRoughness: 0.1
      });
      
      const sheet = new THREE.Mesh(sheetGeometry, sheetMat);
      sheet.position.copy(startPos);
      
      const up = new THREE.Vector3(0, 1, 0);
      if (Math.abs(direction.dot(up)) < 0.99) {
        const quat = new THREE.Quaternion().setFromUnitVectors(up, direction);
        sheet.quaternion.copy(quat);
      }
      sheet.castShadow = true;
      sheet.receiveShadow = true;
      sheetGroup.add(sheet);
      return sheetGroup;
    }
    
    // Connecting loops between helices
    function createLoop(start, end, color) {
      const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
      mid.y += 0.25;
      const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
      const tubeGeo = new THREE.TubeGeometry(curve, 16, 0.06, 6, false);
      const tubeMat = new THREE.MeshPhysicalMaterial({
        color: color, metalness: 0.1, roughness: 0.4,
        transparent: true, opacity: 0.8
      });
      return new THREE.Mesh(tubeGeo, tubeMat);
    }

    // Mode 2: Simplified 7-TM Engine (Cylindrical tubes)
    function buildSimplifiedProtein() {
      const group = new THREE.Group();
      const helixColors = [0xcc4444, 0xdd5555, 0xbb3333, 0xcc5544, 0xdd4444, 0xcc3838, 0xbb4848];
      const helixRadius = 0.55;
      for (let i = 0; i < 7; i++) {
        const angle = (i / 7) * Math.PI * 2;
        const hx = Math.cos(angle) * helixRadius;
        const hz = Math.sin(angle) * helixRadius;
        
        // Use TubeGeometry for simplified "Lego" look
        const backbonePts = [];
        for (let j = 0; j <= 40; j++) {
          const t = j / 40;
          const ay = t * 2.8;
          const ar = 0.25;
          const aa = t * 4.5 * 2 * Math.PI;
          backbonePts.push(new THREE.Vector3(Math.cos(aa)*ar, ay, Math.sin(aa)*ar));
        }
        const curve = new THREE.CatmullRomCurve3(backbonePts);
        const tubeGeo = new THREE.TubeGeometry(curve, 40, 0.15, 8, false);
        const tubeMat = new THREE.MeshPhysicalMaterial({ color: helixColors[i], roughness: 0.4, emissive: helixColors[i], emissiveIntensity: 0.25 });
        const tube = new THREE.Mesh(tubeGeo, tubeMat);
        tube.position.set(hx, -1.4, hz);
        tube.rotation.x = Math.sin(angle) * 0.06;
        tube.rotation.z = -Math.cos(angle) * 0.06;
        group.add(tube);
      }
      return group;
    }

    function buildScientificProtein() {
      const group = new THREE.Group();
      const h1 = createAlphaHelix(new THREE.Vector3(-0.8, -1.2, 0.4), 2.5, 4, 0xcc4444);
      group.add(h1);
      const h2 = createAlphaHelix(new THREE.Vector3(0.8, -1.0, -0.6), 2.2, 3.5, 0xdd5555);
      h2.rotation.z = 0.2;
      group.add(h2);
      const s1 = createBetaSheet(new THREE.Vector3(-1.2, -0.8, -0.4), new THREE.Vector3(-0.6, 1.2, 0.2), 0.5, 0xbb3333);
      group.add(s1);
      const s2 = createBetaSheet(new THREE.Vector3(1.0, -0.9, 0.5), new THREE.Vector3(0.4, 1.3, -0.1), 0.5, 0xcc5544);
      group.add(s2);
      for (let i = 0; i < 5; i++) {
        const start = new THREE.Vector3((Math.random()-0.5)*2, -1.4, (Math.random()-0.5)*2);
        const end = new THREE.Vector3((Math.random()-0.5)*2, 1.4, (Math.random()-0.5)*2);
        group.add(createLoop(start, end, 0xdd6666));
      }
      return group;
    }

    // Binding pocket glow at extracellular surface (top of receptor)
    const pocketGeo = new THREE.ConeGeometry(0.45, 0.8, 20, 1, true);
    const pocketMat = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(isLeft ? 0xff6600 : 0x00ffaa) },
        glowIntensity: { value: 1.5 },
        time: { value: 0 }
      },
      vertexShader: CustomShaders.glowVertex,
      fragmentShader: CustomShaders.glowFragment,
      transparent: true, side: THREE.DoubleSide, blending: THREE.AdditiveBlending
    });
    
    // Add glow particles around binding site
    const glowParticles = [];
    for (let i = 0; i < 30; i++) {
      const angle = (i / 30) * Math.PI * 2;
      const radius = 0.5 + Math.random() * 0.15;
      const particleGeo = new THREE.SphereGeometry(0.015, 6, 6);
      const particleMat = new THREE.MeshBasicMaterial({
        color: isLeft ? 0xff6600 : 0x00ffaa,
        transparent: true, opacity: 0.5
      });
      const particle = new THREE.Mesh(particleGeo, particleMat);
      particle.position.set(
        Math.cos(angle) * radius,
        1.6 + (Math.random() - 0.5) * 0.3,
        Math.sin(angle) * radius
      );
      particle.userData.angle = angle;
      particle.userData.radius = radius;
      particle.userData.speed = 0.5 + Math.random() * 0.5;
      glowParticles.push(particle);
    }

    let fidelity = 'scientific'; // Default
    let molecule = null; // Forward declaration to avoid TDZ crash

    function rebuildProtein() {
      scene.remove(proteinGroup);
      proteinGroup = (fidelity === 'scientific') ? buildScientificProtein() : buildSimplifiedProtein();
      
      // Re-add common elements (pocket, glow)
      const pocket = new THREE.Mesh(pocketGeo, pocketMat);
      pocket.rotation.x = Math.PI;
      pocket.position.y = 1.6;
      proteinGroup.add(pocket);
      glowParticles.forEach(p => proteinGroup.add(p));
      
      scene.add(proteinGroup);
    }
    rebuildProtein();
    

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

    // Fidelity toggle listener
    const fidelitySelect = document.getElementById('mol-fidelity');
    if (fidelitySelect) {
      fidelitySelect.addEventListener('change', (e) => {
        fidelity = e.target.value;
        rebuildProtein();
        // Also rebuild the ligand
        if (molecule) {
          scene.remove(molecule);
          molecule = buildMolecule(drugKey);
          scene.add(molecule);
        }
      });
    }

    // ═══ HIGH-FIDELITY LIGAND BUILDER ═══
    function buildMolecule(key) {
      const drug = DRUG_DB[key];
      const mol = new THREE.Group();
      const atomMeshes = [];
      
      if (fidelity === 'scientific') {
        // If it's a peptide fragment, render as ribbon
        if ((drug.name || '').toLowerCase().includes("fragment") || drug.atoms.length > 20) {
          const pts = drug.atoms.map(a => new THREE.Vector3(a.p[0], a.p[1], a.p[2]));
          const curve = new THREE.CatmullRomCurve3(pts);
          const tubeGeo = new THREE.TubeGeometry(curve, 40, 0.08, 8, false);
          const tubeMat = new THREE.MeshPhysicalMaterial({
            color: 0x3344aa, metalness: 0.2, roughness: 0.3,
            transparent: true, opacity: 0.9, emissive: 0x2233aa, emissiveIntensity: 0.1
          });
          const ribbon = new THREE.Mesh(tubeGeo, tubeMat);
          mol.add(ribbon);
          
          drug.atoms.forEach((a, i) => {
            if (i % 3 === 0) {
              const s = new THREE.Mesh(new THREE.IcosahedronGeometry(0.12, 1), new THREE.MeshBasicMaterial({color:0x4488ff}));
              s.position.set(a.p[0], a.p[1], a.p[2]);
              mol.add(s);
              atomMeshes.push(s);
            }
          });
        } else {
          // Scientific: Ball and Stick
          drug.atoms.forEach(a => {
            const r = (ATOM_RADIUS[a.t] || 0.15) * 0.7;
            const s = new THREE.Mesh(
              new THREE.SphereGeometry(r, 16, 16),
              new THREE.MeshPhysicalMaterial({color: 0x3344aa, metalness: 0.3, roughness: 0.2})
            );
            s.position.set(a.p[0], a.p[1], a.p[2]);
            mol.add(s);
            atomMeshes.push(s);
          });
          drug.bonds.forEach(b => {
            const a1 = drug.atoms[b[0]].p, a2 = drug.atoms[b[1]].p;
            const start = new THREE.Vector3(a1[0], a1[1], a1[2]);
            const end = new THREE.Vector3(a2[0], a2[1], a2[2]);
            const dist = start.distanceTo(end);
            const stick = new THREE.Mesh(
              new THREE.CylinderGeometry(0.04, 0.04, dist, 6),
              new THREE.MeshPhysicalMaterial({ color: 0x6677cc, transparent: true, opacity: 0.6 })
            );
            stick.position.copy(start).lerp(end, 0.5);
            stick.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), end.clone().sub(start).normalize());
            mol.add(stick);
          });
        }
      } else {
        // Simplified: Abstract Spheres
        drug.atoms.forEach(a => {
          const s = new THREE.Mesh(
            new THREE.SphereGeometry(0.25, 12, 12),
            new THREE.MeshStandardMaterial({color: 0x3344aa})
          );
          s.position.set(a.p[0], a.p[1], a.p[2]);
          mol.add(s);
          atomMeshes.push(s);
        });
      }
      
      // Solvent shell (aesthetic)
      for (let i = 0; i < 20; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;
        const r = 1.2 + Math.random() * 0.5;
        const water = new THREE.Mesh(new THREE.SphereGeometry(0.03, 6, 6), new THREE.MeshBasicMaterial({color: 0x4488ff, transparent: true, opacity: 0.2}));
        water.position.set(Math.sin(phi)*Math.cos(theta)*r, Math.sin(phi)*Math.sin(theta)*r, Math.cos(phi)*r);
        mol.add(water);
      }
      
      mol.position.set(0.5, 5, 1.5);
      mol.userData.atomMeshes = atomMeshes;
      return mol;
    }

    molecule = buildMolecule(drugKey);
    scene.add(molecule);

    // Approach curve
    // Drug approaches from above, descending toward receptor binding pocket
    const approachCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.5, 5, 1.5), new THREE.Vector3(0.8, 3.5, 0.8),
      new THREE.Vector3(0.2, 2.5, 0.3), new THREE.Vector3(0.05, 1.8, 0.1)
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

      // ═══ PHASE 1: DIFFUSION + APPROACH (0-119) ═══
      if (phase < 120) {
        const t = Easing.easeInOutCubic(phase / 120);
        const rawT = phase / 120;
        const pt = approachCurve.getPoint(t);
        // Brownian jitter during approach
        const brownian = 0.08 * (1 - t);
        molecule.position.set(
          pt.x + Math.sin(time * 5.3) * brownian + Math.cos(time * 7.1) * brownian * 0.5,
          pt.y + Math.cos(time * 4.7) * brownian + Math.sin(time * 6.3) * brownian * 0.3,
          pt.z + Math.sin(time * 3.9) * brownian * 0.6
        );
        molecule.rotation.y += 0.015 + (1 - t) * 0.01;
        molecule.rotation.x = Math.sin(time * 0.8) * 0.15 * (1 - t);
        molecule.rotation.z = Math.cos(time * 0.6) * 0.1 * (1 - t);
        
        // Animate solvent shell water molecules
        molecule.children.forEach(child => {
          if (child.userData.basePos) {
            const bp = child.userData.basePos;
            const d = child.userData.drift;
            child.position.set(
              bp.x + Math.sin(time * 1.5 + d) * 0.06,
              bp.y + Math.cos(time * 1.2 + d) * 0.04,
              bp.z + Math.sin(time * 0.9 + d) * 0.05
            );
          }
        });
        
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
        
        // Subtle binding vibration at receptor surface
        molecule.position.set(
          0.05 + Math.sin(time * 2) * 0.01,
          1.8 + Math.cos(time * 2.5) * 0.01,
          0.05 + Math.sin(time * 1.8) * 0.008
        );
        molecule.rotation.y += 0.005;
        molecule.rotation.z = Math.sin(time * 1.5) * 0.05;
        
        trailParticles.forEach(tp => { tp.visible = false; });
        
        // Enhanced burst with easing
        if (phase === 120) {
          burstParticles.forEach(bp => {
            bp.position.set(0.05, 1.8, 0.05);
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
            1.6 + ep.userData.height + Math.sin(time * 2 + i) * 0.1,
            Math.sin(angle) * ep.userData.radius
          );
          ep.material.opacity = easedT2 * 0.7 * (0.5 + Math.sin(time * 4 + i) * 0.5);
        });
        
        // Animate glow particles
        glowParticles.forEach((gp, i) => {
          const angle = time * gp.userData.speed + gp.userData.angle;
          gp.position.set(
            Math.cos(angle) * gp.userData.radius,
            1.6 + Math.sin(time * 2 + i * 0.1) * 0.05,
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
          0.05 + Math.sin(time) * 0.008,
          1.8 + Math.cos(time * 1.2) * 0.008,
          0.05
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
            1.6 + ep.userData.height + Math.sin(time * 2 + i) * 0.1,
            Math.sin(angle) * ep.userData.radius
          );
          ep.material.opacity = 0.5 * (0.6 + Math.sin(time * 3 + i) * 0.4);
        });
        
        // Glow particles orbit
        glowParticles.forEach((gp, i) => {
          const angle = time * gp.userData.speed + gp.userData.angle;
          gp.position.set(
            Math.cos(angle) * gp.userData.radius,
            1.6 + Math.sin(time * 2 + i * 0.1) * 0.05,
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
        camTheta += 0.002;
        
        let targetCamR = 6;
        let targetCamPhi = 0.35;
        
        if (phase < 120) {
          // Wide elevated shot to show ligand approaching from above
          targetCamR = 7 + Math.sin(time * 0.5) * 0.5;
          targetCamPhi = 0.45;
        } else if (phase < 180) {
          // Close-up of binding event
          targetCamR = 4 + Math.sin(time * 2) * 0.3;
          targetCamPhi = 0.25;
        } else {
          // Medium shot showing bound state in membrane context
          targetCamR = 5.5 + Math.sin(time * 0.8) * 0.4;
          targetCamPhi = 0.3;
        }
        
        const camR = camera.position.length();
        const newCamR = camR + (targetCamR - camR) * 0.02;
        camPhi += (targetCamPhi - camPhi) * 0.02;
        
        camera.position.set(
          newCamR * Math.cos(camPhi) * Math.sin(camTheta),
          newCamR * Math.sin(camPhi) + 1.0,
          newCamR * Math.cos(camPhi) * Math.cos(camTheta)
        );
      } else {
        const camR = 6;
        camera.position.set(
          camR * Math.cos(camPhi) * Math.sin(camTheta),
          camR * Math.sin(camPhi) + 1.0,
          camR * Math.cos(camPhi) * Math.cos(camTheta)
        );
      }
      
      camera.lookAt(0, 1.0, 0);
      
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
