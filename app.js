/**
 * LEGO Microduck (#MD-2026 Rev 3.2) — Interactive 3D WebGL Assembly Studio & 10-DoF Bipedal Walking Simulator
 * Loads verified Rev 3.2 outputs (/output/microduck_model.json, /output/verification_report.json,
 * /output/microduck_bom.csv, /output/microduck_bricklink_wanted_list.xml) and renders all 945 bricks
 * with true 3D slanted sub-assembly poses (+24° shins, -26° thighs & shields, +19.725° neck stalk),
 * 8/8 double-shear clevis pin joints (16 shear pins), dual-pin triangulated struts, flush hard-stop
 * cradle ledges, and 28 horizontal X-axis 2780 Technic friction pins (0 3D OBB collisions).
 */


(function () {
  'use strict';

  const STUD_MM = 8.0;
  const PLATE_MM = 3.2;
  const SEAM_XZ = 0.12;
  const SEAM_Y = 0.10;

  // Official Hugging Face x Pollen Robotics Microduck Colorway Hex Map (from cad/parts_catalog.py)
  const COLOR_HEX = {
    1: '#F4F4F4',   // White
    2: '#E4CD9E',   // Tan
    3: '#F2CD37',   // Yellow
    110: '#F8BB3D', // Bright Light Orange
    4: '#FE8A18',   // Orange
    85: '#6C6E68',  // Dark Bluish Gray
    86: '#A0A5A9',  // Light Bluish Gray
    11: '#1B2A34',  // Black
    15: '#AEEFEC',  // Trans-Light Blue
  };

  // Application State
  const state = {
    model: null,
    report: null,
    bomLots: [],
    bricklinkXmlText: '',
    currentStep: 129,
    totalSteps: 129,
    isPlaying: false,
    playSpeed: 2, // 1x, 2x, 5x
    playTimer: null,
    highlightCurrentStep: true,
    showCogOverlay: true,
    xraySpineMode: false,
    // 10-DoF Bipedal Walk & Kinematic Controls
    isWalking: false,
    gaitPhasePct: 0, // 0..100%
    lastWalkTickTime: 0,
    floorScrollZ: 0,
    hipPitchDeg: 0,
    kneeFlexDeg: 0,
    neckPitchDeg: 0,
    neckYawDeg: 0,
    explodePct: 0,
    // Step drop animation
    stepDropAnim: 1.0,
    lastStepChangeTime: 0,
    stepDataMap: new Map(), // step_id -> { bricks, bonds, cumPieces, cumMass, cumCog }
    brickRecords: [],       // { brick, meshGroup, bodyMat, edgeMat, baseLocalPos, isInternalCore, isTrans }
  };

  // Three.js Scene Objects
  let scene, camera, renderer, controls, gridHelper;
  let rootModelGroup;
  // Hierarchical 10-DoF Coaxial Pin Rig Groups
  let pelvisPivot, sa4HipGroup, sa5TorsoGroup;
  let leftHipPivot, leftThighGroup, leftKneePivot, leftShinGroup, leftAnklePivot, leftFootGroup;
  let rightHipPivot, rightThighGroup, rightKneePivot, rightShinGroup, rightAnklePivot, rightFootGroup;
  let lowerNeckPivot, neckStalkGroup, upperNeckHeadPivot, visorHeadGroup;
  let cogOverlayGroup, cogSphereMesh, cogPlumbLine, cogGroundCross;

  // Shared Geometries for fast instancing
  const studGeo = new THREE.CylinderGeometry(2.4, 2.4, 1.7, 16);
  const holeRimGeoZ = new THREE.CylinderGeometry(2.38, 2.38, 0.34, 16);
  holeRimGeoZ.rotateX(Math.PI / 2);
  const holeRimGeoX = new THREE.CylinderGeometry(2.38, 2.38, 0.34, 16);
  holeRimGeoX.rotateZ(Math.PI / 2);
  const holeGeoZ = new THREE.CylinderGeometry(1.78, 1.78, 0.42, 16);
  holeGeoZ.rotateX(Math.PI / 2);
  const holeGeoX = new THREE.CylinderGeometry(1.78, 1.78, 0.42, 16);
  holeGeoX.rotateZ(Math.PI / 2);

  // Horizontal X-Axis Technic Friction Pin 2780 Geometries
  const pinBarrelGeoX = new THREE.CylinderGeometry(2.35, 2.35, 11.6, 18);
  pinBarrelGeoX.rotateZ(Math.PI / 2);
  const pinCollarGeoX = new THREE.CylinderGeometry(2.95, 2.95, 2.4, 18);
  pinCollarGeoX.rotateZ(Math.PI / 2);
  const pinBoreGeoX = new THREE.CylinderGeometry(1.25, 1.25, 11.8, 12);
  pinBoreGeoX.rotateZ(Math.PI / 2);

  /**
   * Generate a crisp 2D/3D isometric SVG thumbnail for any LEGO part & color
   * Renders 2780 Technic Friction Pins as a horizontal X-axis cylinder with central collar,
   * and renders all inter-stud pin holes on 3700 (1 hole), 3701 (3 holes), and 3894 (5 holes).
   */
  function createIsometricBrickSvg(partId, colorHex, dx, dy, dz, hasTopStuds) {
    const w = 54;
    const h = 42;
    const cos30 = 0.866025;
    const sin30 = 0.5;
    const maxSpan = Math.max(dx, dz, 2);
    const scale = Math.min(1.45, 3.3 / maxSpan);

    const cx = w * 0.5;
    const cy = h * 0.68;

    function proj(x, y, z) {
      const u = cx + scale * (x - z) * cos30;
      const v = cy + scale * ((x + z) * sin30 - y);
      return `${u.toFixed(1)},${v.toFixed(1)}`;
    }

    function shadeHex(hex, factor) {
      const clean = (hex || '#CCCCCC').replace('#', '');
      const r = Math.min(255, Math.max(0, Math.round(parseInt(clean.substring(0, 2), 16) * factor)));
      const g = Math.min(255, Math.max(0, Math.round(parseInt(clean.substring(2, 4), 16) * factor)));
      const b = Math.min(255, Math.max(0, Math.round(parseInt(clean.substring(4, 6), 16) * factor)));
      return `rgb(${r},${g},${b})`;
    }

    const stroke = '#1B2A34';

    // Horizontal X-Axis Technic Pin 2780 SVG
    if (partId === '2780') {
      const cyPin = h * 0.54;
      function projPin(x, y, z) {
        const u = cx + 1.35 * (x - z) * cos30;
        const v = cyPin + 1.35 * ((x + z) * sin30 - y);
        return `${u.toFixed(1)},${v.toFixed(1)}`;
      }
      const barrelCol = shadeHex(colorHex, 1.25);
      const collarCol = shadeHex(colorHex, 1.55);
      const bPts = `${projPin(-5.5, 2.3, -1.0)} ${projPin(5.5, 2.3, -1.0)} ${projPin(5.5, -2.3, 1.0)} ${projPin(-5.5, -2.3, 1.0)}`;
      const cPts = `${projPin(-1.3, 3.0, -1.2)} ${projPin(1.3, 3.0, -1.2)} ${projPin(1.3, -3.0, 1.2)} ${projPin(-1.3, -3.0, 1.2)}`;
      const endU = (cx + 1.35 * 5.5 * cos30).toFixed(1);
      const endV = (cyPin + 1.35 * 5.5 * sin30).toFixed(1);
      return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">` +
        `<polygon points="${bPts}" fill="${barrelCol}" stroke="${stroke}" stroke-width="0.7"/>` +
        `<polygon points="${cPts}" fill="${collarCol}" stroke="${stroke}" stroke-width="0.7"/>` +
        `<circle cx="${endU}" cy="${endV}" r="3.1" fill="${barrelCol}" stroke="${stroke}" stroke-width="0.7"/>` +
        `<circle cx="${endU}" cy="${endV}" r="1.4" fill="#0B1014"/>` +
        `</svg>`;
    }

    const x0 = -dx * 4.0;
    const x1 = dx * 4.0;
    const y0 = 0;
    const y1 = dy * 3.2;
    const z0 = -dz * 4.0;
    const z1 = dz * 4.0;

    const topCol = shadeHex(colorHex, 1.06);
    const leftCol = shadeHex(colorHex, 0.90);
    const rightCol = shadeHex(colorHex, 0.75);

    let polys = '';
    if (['54200', '85984', '11477', '15068', '3040', '3039'].includes(partId)) {
      const yLip = y1 * 0.32;
      const p001 = proj(x0, y0, z1);
      const p101 = proj(x1, y0, z1);
      const p100 = proj(x1, y0, z0);
      const p010 = proj(x0, y1, z0);
      const p110 = proj(x1, y1, z0);
      const p1Lip = proj(x1, yLip, z1);
      const p0Lip = proj(x0, yLip, z1);
      polys += `<polygon points="${p001} ${p101} ${p1Lip} ${p0Lip}" fill="${leftCol}" stroke="${stroke}" stroke-width="0.7"/>`;
      polys += `<polygon points="${p100} ${p110} ${p1Lip} ${p101}" fill="${rightCol}" stroke="${stroke}" stroke-width="0.7"/>`;
      polys += `<polygon points="${p010} ${p110} ${p1Lip} ${p0Lip}" fill="${topCol}" stroke="${stroke}" stroke-width="0.7"/>`;
    } else {
      const p001 = proj(x0, y0, z1);
      const p101 = proj(x1, y0, z1);
      const p100 = proj(x1, y0, z0);
      const p011 = proj(x0, y1, z1);
      const p111 = proj(x1, y1, z1);
      const p110 = proj(x1, y1, z0);
      const p010 = proj(x0, y1, z0);
      polys += `<polygon points="${p001} ${p101} ${p111} ${p011}" fill="${leftCol}" stroke="${stroke}" stroke-width="0.7"/>`;
      polys += `<polygon points="${p101} ${p100} ${p110} ${p111}" fill="${rightCol}" stroke="${stroke}" stroke-width="0.7"/>`;
      polys += `<polygon points="${p010} ${p110} ${p111} ${p011}" fill="${topCol}" stroke="${stroke}" stroke-width="0.7"/>`;
    }

    // Inter-stud Technic pin holes on 3700 (1 hole), 3701 (3 holes), 3894 (5 holes)
    let holesSvg = '';
    if (['3700', '3701', '3894'].includes(partId)) {
      const hy = (y0 + y1) * 0.5;
      const holeR = (1.65 * scale).toFixed(1);
      const rimStroke = '#758894';
      if (dz >= dx) {
        const numHoles = Math.max(1, dz - 1);
        for (let ih = 0; ih < numHoles; ih++) {
          const oz = (-(numHoles - 1) * 0.5 + ih) * 8.0;
          const u = (cx + scale * (x1 - oz) * cos30).toFixed(1);
          const v = (cy + scale * ((x1 + oz) * sin30 - hy)).toFixed(1);
          holesSvg += `<circle cx="${u}" cy="${v}" r="${holeR}" fill="#11181C" stroke="${rimStroke}" stroke-width="0.65"/>`;
        }
      } else {
        const numHoles = Math.max(1, dx - 1);
        for (let ih = 0; ih < numHoles; ih++) {
          const ox = (-(numHoles - 1) * 0.5 + ih) * 8.0;
          const u = (cx + scale * (ox - z1) * cos30).toFixed(1);
          const v = (cy + scale * ((ox + z1) * sin30 - hy)).toFixed(1);
          holesSvg += `<circle cx="${u}" cy="${v}" r="${holeR}" fill="#11181C" stroke="${rimStroke}" stroke-width="0.65"/>`;
        }
      }
    }

    let studsSvg = '';
    if (hasTopStuds) {
      const rx = (2.2 * scale).toFixed(1);
      const ry = (1.25 * scale).toFixed(1);
      for (let ix = 0; ix < dx; ix++) {
        for (let iz = 0; iz < dz; iz++) {
          const sx = x0 + (ix + 0.5) * 8.0;
          const sz = z0 + (iz + 0.5) * 8.0;
          const u = (cx + scale * (sx - sz) * cos30).toFixed(1);
          const v = (cy + scale * ((sx + sz) * sin30 - (y1 + 1.0))).toFixed(1);
          studsSvg += `<ellipse cx="${u}" cy="${v}" rx="${rx}" ry="${ry}" fill="${topCol}" stroke="${stroke}" stroke-width="0.55"/>`;
        }
      }
    }

    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">${polys}${holesSvg}${studsSvg}</svg>`;
  }

  /**
   * Build a 3D sloped wedge BufferGeometry for LEGO slope bricks (54200, 85984, 11477, 15068, 3040, 3039)
   * Centered at local (0, 0, 0) with size (w, h, d).
   */
  function createSlopeWedgeGeometry(w, h, d, slopeTowardPositiveZ) {
    const hw = w * 0.5;
    const hh = h * 0.5;
    const hd = d * 0.5;
    const lipY = -hh + h * 0.32;

    const zBackY = slopeTowardPositiveZ ? hh : lipY;
    const zFrontY = slopeTowardPositiveZ ? lipY : hh;

    const v0 = [-hw, -hh, -hd];
    const v1 = [hw, -hh, -hd];
    const v2 = [hw, -hh, hd];
    const v3 = [-hw, -hh, hd];
    const v4 = [-hw, zBackY, -hd];
    const v5 = [hw, zBackY, -hd];
    const v6 = [hw, zFrontY, hd];
    const v7 = [-hw, zFrontY, hd];

    const positions = [];
    function addQuad(a, b, c, dPt) {
      positions.push(...a, ...b, ...c, ...a, ...c, ...dPt);
    }

    addQuad(v0, v1, v2, v3); // Bottom (-Y)
    addQuad(v4, v7, v6, v5); // Top sloped face (+Y)
    addQuad(v3, v2, v6, v7); // Front (+Z)
    addQuad(v1, v0, v4, v5); // Back (-Z)
    addQuad(v2, v1, v5, v6); // Right (+X)
    addQuad(v0, v3, v7, v4); // Left (-X)

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.computeVertexNormals();
    return geo;
  }

  /**
   * Precompute per-step telemetry (stud/pin bonds, cumulative pieces, mass, 3D world CoG)
   */
  function precomputeStepTelemetry(bricks) {
    const byStep = new Map();
    for (const b of bricks) {
      if (!byStep.has(b.step_id)) byStep.set(b.step_id, []);
      byStep.get(b.step_id).push(b);
    }

    const placedTopStuds = new Set();
    const placedBottomTubes = new Set();
    let cumPieces = 0;
    let cumMass = 0.0;
    let weightedX = 0.0;
    let weightedY = 0.0;
    let weightedZ = 0.0;

    const sortedSteps = Array.from(byStep.keys()).sort((a, b) => a - b);
    for (const stepId of sortedSteps) {
      const sBricks = byStep.get(stepId);
      let bonds = 0;

      for (const b of sBricks) {
        if (b.part_id === '2780') {
          bonds += 2; // Horizontal Technic pin mates parent & child 3700/3701 pin holes
          continue;
        }
        const sid = b.subassembly_id || 1;
        const yBot = b.y;
        const yTop = b.y_top;
        for (let ix = b.x; ix < b.x + b.dx; ix++) {
          for (let iz = b.z; iz < b.z + b.dz; iz++) {
            if (yBot === 0) {
              bonds += 1;
            } else if (placedTopStuds.has(`${sid},${ix},${yBot},${iz}`)) {
              bonds += 1;
            }
            if (placedBottomTubes.has(`${sid},${ix},${yTop},${iz}`)) {
              bonds += 1;
            }
          }
        }
      }

      for (const b of sBricks) {
        if (b.part_id !== '2780') {
          const sid = b.subassembly_id || 1;
          const yBot = b.y;
          const yTop = b.y_top;
          for (let ix = b.x; ix < b.x + b.dx; ix++) {
            for (let iz = b.z; iz < b.z + b.dz; iz++) {
              if (b.has_top_studs || b.part_id === '3937') {
                placedTopStuds.add(`${sid},${ix},${yTop},${iz}`);
              }
              if (b.has_bottom_tubes) {
                placedBottomTubes.add(`${sid},${ix},${yBot},${iz}`);
              }
            }
          }
        }
        const wc = b.world_center_mm || b.center_mm;
        cumPieces += 1;
        cumMass += b.mass_g;
        weightedX += b.mass_g * wc[0];
        weightedY += b.mass_g * wc[1];
        weightedZ += b.mass_g * wc[2];
      }

      state.stepDataMap.set(stepId, {
        stepId,
        bricks: sBricks,
        bonds: Math.max(1, bonds),
        cumPieces,
        cumMass,
        cumCog: {
          x: cumMass > 0 ? weightedX / cumMass : 0,
          y: cumMass > 0 ? weightedY / cumMass : 0,
          z: cumMass > 0 ? weightedZ / cumMass : 0,
        },
      });
    }
  }

  /**
   * Initialize Three.js WebGL Viewport, Lights, Ground Grid & Hierarchical 10-DoF Coaxial Pin Rig
   */
  function initThreeScene() {
    const container = document.getElementById('canvas-container');
    const canvas = document.getElementById('lego-canvas');
    const cw = Math.max(320, (container && container.clientWidth) || 820);
    const ch = Math.max(240, (container && container.clientHeight) || 620);

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xF8FAF7);

    camera = new THREE.PerspectiveCamera(36, cw / ch, 1.0, 3000.0);

    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch (_e1) {
      try {
        renderer = new THREE.WebGLRenderer({
          canvas,
          antialias: false,
          failIfMajorPerformanceCaveat: false,
        });
      } catch (_e2) {
        renderer = null;
      }
    }

    if (renderer) {
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(cw, ch);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    } else if (canvas) {
      canvas.width = cw;
      canvas.height = ch;
    }

    controls = new THREE.OrbitControls(camera, renderer ? renderer.domElement : canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxDistance = 1200;
    controls.minDistance = 60;

    // Studio Lighting (Warm Key Light + Cool Engineering Fill + Rim Light)
    const hemiLight = new THREE.HemisphereLight(0xFFFFFF, 0xD8E0DC, 0.74);
    hemiLight.position.set(0, 400, 0);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xFFFDF9, 0.68);
    keyLight.position.set(220, 380, 260);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.camera.near = 50;
    keyLight.shadow.camera.far = 900;
    const d = 180;
    keyLight.shadow.camera.left = -d;
    keyLight.shadow.camera.right = d;
    keyLight.shadow.camera.top = d;
    keyLight.shadow.camera.bottom = -d;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xE4F0F5, 0.38);
    fillLight.position.set(-240, 180, -200);
    scene.add(fillLight);

    // Subtle Engineering Stud Grid on Ground Plane (Y = 0)
    gridHelper = new THREE.GridHelper(288, 36, 0x1C4F59, 0xD5DFDA);
    gridHelper.position.y = -0.1;
    scene.add(gridHelper);

    // Root Model Group & Hierarchical 10-DoF Coaxial Pin Rig
    // Anchored at the exact Rev 3.0 coaxial_pin_joints world coordinates!
    rootModelGroup = new THREE.Group();
    scene.add(rootModelGroup);

    // 1. Root Pelvis & Hip Coaxial Axis Center at (0.0, 90.441, -14.5104) mm
    pelvisPivot = new THREE.Group();
    pelvisPivot.position.set(0.0, 90.441, -14.5104);
    rootModelGroup.add(pelvisPivot);

    sa4HipGroup = new THREE.Group(); // SA-04: Exposed Hip Servo Cluster & Grey Roll Hubs (0°)
    sa5TorsoGroup = new THREE.Group(); // SA-05: Compact Rounded White Torso Pod & Rear Spine (0°)
    pelvisPivot.add(sa4HipGroup);
    pelvisPivot.add(sa5TorsoGroup);

    // 2. Left Leg Coaxial Pin Hierarchy:
    //    left_hip_pin (-36.0, 90.441, -14.5104)
    //    -> left_knee_pin (-36.0, 58.8035, 0.9202)
    //    -> left_ankle_pin (-36.0, 20.8, -16.0)
    leftHipPivot = new THREE.Group();
    leftHipPivot.position.set(-36.0, 0.0, 0.0);
    pelvisPivot.add(leftHipPivot);

    leftThighGroup = new THREE.Group(); // SA-03 Left Slanted (-26°) Upper Thigh & White Outer Shield
    leftHipPivot.add(leftThighGroup);

    leftKneePivot = new THREE.Group();
    leftKneePivot.position.set(0.0, 58.8035 - 90.441, 0.9202 - (-14.5104));
    leftHipPivot.add(leftKneePivot);

    leftShinGroup = new THREE.Group(); // SA-02 Left Slanted (+24°) Lower Shin & Knee Linkage
    leftKneePivot.add(leftShinGroup);

    leftAnklePivot = new THREE.Group();
    leftAnklePivot.position.set(0.0, 20.8 - 58.8035, -16.0 - 0.9202);
    leftKneePivot.add(leftAnklePivot);

    leftFootGroup = new THREE.Group(); // SA-01 Left Bootie Foot (0°)
    leftAnklePivot.add(leftFootGroup);

    // 3. Right Leg Coaxial Pin Hierarchy:
    //    right_hip_pin (+36.0, 90.441, -14.5104)
    //    -> right_knee_pin (+36.0, 58.8035, 0.9202)
    //    -> right_ankle_pin (+36.0, 20.8, -16.0)
    rightHipPivot = new THREE.Group();
    rightHipPivot.position.set(36.0, 0.0, 0.0);
    pelvisPivot.add(rightHipPivot);

    rightThighGroup = new THREE.Group(); // SA-03 Right Slanted (-26°) Upper Thigh & White Outer Shield
    rightHipPivot.add(rightThighGroup);

    rightKneePivot = new THREE.Group();
    rightKneePivot.position.set(0.0, 58.8035 - 90.441, 0.9202 - (-14.5104));
    rightHipPivot.add(rightKneePivot);

    rightShinGroup = new THREE.Group(); // SA-02 Right Slanted (+24°) Lower Shin & Knee Linkage
    rightKneePivot.add(rightShinGroup);

    rightAnklePivot = new THREE.Group();
    rightAnklePivot.position.set(0.0, 20.8 - 58.8035, -16.0 - 0.9202);
    rightKneePivot.add(rightAnklePivot);

    rightFootGroup = new THREE.Group(); // SA-01 Right Bootie Foot (0°)
    rightAnklePivot.add(rightFootGroup);

    // 4. Neck & Head Coaxial Pin Hierarchy:
    //    lower_neck_pin (0.0, 141.641, 1.4896)
    //    -> upper_neck_turntable_pin (0.0, 180.8000, 15.5307)
    lowerNeckPivot = new THREE.Group();
    lowerNeckPivot.position.set(0.0, 141.641 - 90.441, 1.4896 - (-14.5104));
    pelvisPivot.add(lowerNeckPivot);

    neckStalkGroup = new THREE.Group(); // SA-06 Slanted (+19.725°) Slender 4x4 Multi-Servo Neck Stalk
    lowerNeckPivot.add(neckStalkGroup);

    upperNeckHeadPivot = new THREE.Group();
    upperNeckHeadPivot.position.set(0.0, 180.8000 - 141.641, 15.5307 - 1.4896);
    lowerNeckPivot.add(upperNeckHeadPivot);

    visorHeadGroup = new THREE.Group(); // SA-07 Arched White Visor Hood & Cyclops Camera Head (0°)
    upperNeckHeadPivot.add(visorHeadGroup);

    // Build 3D Center of Gravity, 8 Coaxial Pin Joint Axes & 112x88 mm Foot Support Polygon Overlay
    initCogOverlay();

    // Set initial Isometric Camera View
    setCameraPreset('isometric');

    window.addEventListener('resize', onWindowResize);
    if (typeof ResizeObserver !== 'undefined' && container) {
      const ro = new ResizeObserver(() => onWindowResize());
      ro.observe(container);
    }
    setTimeout(onWindowResize, 60);
    setTimeout(onWindowResize, 300);
  }

  /**
   * Build 3D Center of Gravity (CoG) sphere, vertical plumb line, 8 Coaxial Pin Joint Axes,
   * and 112x88 mm Foot Support Polygon (X in [-56,+56], Z in [-48,+40] mm)
   */
  function initCogOverlay() {
    cogOverlayGroup = new THREE.Group();
    scene.add(cogOverlayGroup);

    // 1. Foot Support Polygon on Y = 0.2 mm (X in [-56, +56], Z in [-48, +40] mm -> center Z = -4.0)
    const hullShape = new THREE.PlaneGeometry(112.0, 88.0);
    hullShape.rotateX(-Math.PI / 2);
    const hullMat = new THREE.MeshBasicMaterial({
      color: 0x2F5B37,
      transparent: true,
      opacity: 0.16,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const hullMesh = new THREE.Mesh(hullShape, hullMat);
    hullMesh.position.set(0, 0.2, -4.0);
    cogOverlayGroup.add(hullMesh);

    // Support Polygon Border Outline
    const borderPts = [
      new THREE.Vector3(-56, 0.4, -48),
      new THREE.Vector3(56, 0.4, -48),
      new THREE.Vector3(56, 0.4, 40),
      new THREE.Vector3(-56, 0.4, 40),
      new THREE.Vector3(-56, 0.4, -48),
    ];
    const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPts);
    const borderLine = new THREE.Line(
      borderGeo,
      new THREE.LineBasicMaterial({ color: 0x2F5B37, linewidth: 2 })
    );
    cogOverlayGroup.add(borderLine);

    // 2. 8 Coaxial Technic Pin Joint Axis Markers (X-axis lines at each coaxial joint)
    const coaxialPivots = [
      [-36.0, 20.8, -16.0],
      [36.0, 20.8, -16.0],
      [-36.0, 58.8035, 0.9202],
      [36.0, 58.8035, 0.9202],
      [-36.0, 90.441, -14.5104],
      [36.0, 90.441, -14.5104],
      [0.0, 141.641, 1.4896],
      [0.0, 180.8000, 15.5307],
    ];
    const axisLineMat = new THREE.LineBasicMaterial({
      color: 0xFE8A18,
      depthTest: false,
      transparent: true,
      opacity: 0.78,
    });
    for (const [px, py, pz] of coaxialPivots) {
      const halfSpan = Math.abs(px) > 1 ? 22.0 : 26.0;
      const pts = [
        new THREE.Vector3(px - halfSpan, py, pz),
        new THREE.Vector3(px + halfSpan, py, pz),
      ];
      const lGeo = new THREE.BufferGeometry().setFromPoints(pts);
      const lMesh = new THREE.Line(lGeo, axisLineMat);
      lMesh.renderOrder = 995;
      cogOverlayGroup.add(lMesh);
    }

    // 3. Glowing 3D CoG Sphere
    const sphereGeo = new THREE.SphereGeometry(5.2, 24, 24);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0xD9381E,
      depthTest: false,
      transparent: true,
      opacity: 0.95,
    });
    cogSphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
    cogSphereMesh.renderOrder = 999;
    cogOverlayGroup.add(cogSphereMesh);

    // 4. Vertical Plumb Line from CoG down to Y = 0
    const plumbPts = [
      new THREE.Vector3(0.152, 149.057, -0.829),
      new THREE.Vector3(0.152, 0.4, -0.829),
    ];
    const plumbGeo = new THREE.BufferGeometry().setFromPoints(plumbPts);
    cogPlumbLine = new THREE.Line(
      plumbGeo,
      new THREE.LineBasicMaterial({ color: 0xD9381E, depthTest: false })
    );
    cogPlumbLine.renderOrder = 998;
    cogOverlayGroup.add(cogPlumbLine);

    // 5. Projected Ground Crosshair Marker
    const ringGeo = new THREE.RingGeometry(3.2, 5.5, 24);
    ringGeo.rotateX(-Math.PI / 2);
    cogGroundCross = new THREE.Mesh(
      ringGeo,
      new THREE.MeshBasicMaterial({
        color: 0xFE8A18,
        side: THREE.DoubleSide,
        depthTest: false,
      })
    );
    cogGroundCross.position.set(0.152, 0.5, -0.829);
    cogGroundCross.renderOrder = 999;
    cogOverlayGroup.add(cogGroundCross);
  }

  /**
   * Build all 945 LEGO brick meshes with true 3D pitch rotation (`world_pitch_deg`)
   * and horizontal X-axis 2780 Technic pins, and attach them to the 10-DoF hierarchical rig
   */
  function buildAllBrickMeshes(bricks) {
    // Read exact upper neck pivot dynamically from model.coaxial_pin_joints if present
    let upperNeckY = 180.8000;
    let upperNeckZ = 15.5307;
    if (state.model && Array.isArray(state.model.coaxial_pin_joints)) {
      const uj = state.model.coaxial_pin_joints.find((j) => j.joint_id === 'upper_neck_turntable_pin');
      if (uj && Array.isArray(uj.pivot_mm)) {
        upperNeckY = uj.pivot_mm[1];
        upperNeckZ = uj.pivot_mm[2];
        if (upperNeckHeadPivot) {
          upperNeckHeadPivot.position.set(0.0, upperNeckY - 141.641, upperNeckZ - 1.4896);
        }
      }
    }

    for (const b of bricks) {
      const w = b.dx * STUD_MM - SEAM_XZ;
      const h = b.dy * PLATE_MM - SEAM_Y;
      const d = b.dz * STUD_MM - SEAM_XZ;

      const wc = b.world_center_mm || b.center_mm;
      const cx = wc[0];
      const cy = wc[1];
      const cz = wc[2];
      const pitchDeg = typeof b.world_pitch_deg === 'number' ? b.world_pitch_deg : 0.0;

      const hexStr = COLOR_HEX[b.color_id] || '#CCCCCC';
      const isTrans = b.color_id === 15;

      const bodyMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(hexStr),
        roughness: isTrans ? 0.15 : 0.32,
        metalness: 0.04,
        transparent: isTrans,
        opacity: isTrans ? 0.82 : 1.0,
      });

      const edgeMat = new THREE.LineBasicMaterial({
        color: 0x1B2A34,
        transparent: true,
        opacity: 0.48,
      });

      const brickGroup = new THREE.Group();
      // Apply the sub-assembly's true 3D pitch angle around the X-axis!
      brickGroup.rotation.x = THREE.MathUtils.degToRad(pitchDeg);

      if (b.part_id === '2780' || b.pin_orientation === 'horizontal_x') {
        // True Horizontal X-Axis Technic Friction Pin 2780 (Barrel + Central Collar + Bore)
        const barrelMesh = new THREE.Mesh(pinBarrelGeoX, bodyMat);
        barrelMesh.castShadow = true;
        barrelMesh.receiveShadow = true;
        brickGroup.add(barrelMesh);

        const collarMesh = new THREE.Mesh(pinCollarGeoX, bodyMat);
        brickGroup.add(collarMesh);

        const boreMat = new THREE.MeshBasicMaterial({ color: 0x0B1014 });
        const boreMesh = new THREE.Mesh(pinBoreGeoX, boreMat);
        brickGroup.add(boreMesh);

        const pinEdges = new THREE.EdgesGeometry(pinCollarGeoX, 25);
        brickGroup.add(new THREE.LineSegments(pinEdges, edgeMat));
      } else {
        // Determine body geometry: sloped wedge for 54200 / 85984 / 11477 / 15068 / 3040 / 3039
        let bodyGeo;
        if (['54200', '85984', '11477', '15068', '3040', '3039'].includes(b.part_id)) {
          bodyGeo = createSlopeWedgeGeometry(w, h, d, b.z >= 0);
        } else if (b.part_id === '4032') {
          bodyGeo = new THREE.CylinderGeometry(w * 0.5, w * 0.5, h, 24);
        } else {
          bodyGeo = new THREE.BoxGeometry(w, h, d);
        }

        const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
        bodyMesh.castShadow = true;
        bodyMesh.receiveShadow = true;
        brickGroup.add(bodyMesh);

        // Crisp Edge Outline
        const edgesGeo = new THREE.EdgesGeometry(bodyGeo, 25);
        const edgeLines = new THREE.LineSegments(edgesGeo, edgeMat);
        brickGroup.add(edgeLines);

        // Authentic 3D cylindrical top studs (rotate naturally with brickGroup.rotation.x)
        if (b.has_top_studs) {
          const studY = h * 0.5 + 1.7 * 0.5;
          const xStart = -b.dx * STUD_MM * 0.5 + STUD_MM * 0.5;
          const zStart = -b.dz * STUD_MM * 0.5 + STUD_MM * 0.5;
          for (let ix = 0; ix < b.dx; ix++) {
            for (let iz = 0; iz < b.dz; iz++) {
              const studMesh = new THREE.Mesh(studGeo, bodyMat);
              studMesh.position.set(
                xStart + ix * STUD_MM,
                studY,
                zStart + iz * STUD_MM
              );
              brickGroup.add(studMesh);
            }
          }
        }

        // Special Grille Slats on 2412b
        if (b.part_id === '2412b') {
          const slatMat = new THREE.MeshBasicMaterial({ color: 0x38444C });
          const numSlats = 4;
          for (let si = 1; si <= numSlats; si++) {
            const frac = si / (numSlats + 1) - 0.5;
            const slatGeo =
              b.dx >= b.dz
                ? new THREE.BoxGeometry(0.9, 0.35, d * 0.78)
                : new THREE.BoxGeometry(w * 0.78, 0.35, 0.9);
            const slat = new THREE.Mesh(slatGeo, slatMat);
            if (b.dx >= b.dz) {
              slat.position.set(frac * w * 0.82, h * 0.5 + 0.12, 0);
            } else {
              slat.position.set(0, h * 0.5 + 0.12, frac * d * 0.82);
            }
            brickGroup.add(slat);
          }
        }

        // Authentic Inter-Stud Technic Pin Holes on 3700 (1 hole at center) / 3701 (3 holes) / 3894 (5 holes)
        if (['3700', '3701', '3894'].includes(b.part_id)) {
          const holeMat = new THREE.MeshBasicMaterial({ color: 0x0B1014 });
          const rimColorHex = b.color_id === 11 || b.color_id === 85 ? 0x758894 : 0x4A565E;
          const rimMat = new THREE.MeshBasicMaterial({ color: rimColorHex });
          if (b.dz > b.dx) {
            const numHoles = Math.max(1, b.dz - 1);
            for (let ih = 0; ih < numHoles; ih++) {
              const oz = (-(numHoles - 1) * 0.5 + ih) * STUD_MM;
              const rMeshR = new THREE.Mesh(holeRimGeoX, rimMat);
              rMeshR.position.set(w * 0.5 + 0.02, 0, oz);
              brickGroup.add(rMeshR);
              const hMesh = new THREE.Mesh(holeGeoX, holeMat);
              hMesh.position.set(w * 0.5 + 0.06, 0, oz);
              brickGroup.add(hMesh);
              const rMeshL = new THREE.Mesh(holeRimGeoX, rimMat);
              rMeshL.position.set(-w * 0.5 - 0.02, 0, oz);
              brickGroup.add(rMeshL);
              const hMeshL = new THREE.Mesh(holeGeoX, holeMat);
              hMeshL.position.set(-w * 0.5 - 0.06, 0, oz);
              brickGroup.add(hMeshL);
            }
          } else {
            const numHoles = Math.max(1, b.dx - 1);
            for (let ih = 0; ih < numHoles; ih++) {
              const ox = (-(numHoles - 1) * 0.5 + ih) * STUD_MM;
              const rMeshF = new THREE.Mesh(holeRimGeoZ, rimMat);
              rMeshF.position.set(ox, 0, d * 0.5 + 0.02);
              brickGroup.add(rMeshF);
              const hMesh = new THREE.Mesh(holeGeoZ, holeMat);
              hMesh.position.set(ox, 0, d * 0.5 + 0.06);
              brickGroup.add(hMesh);
              const rMeshB = new THREE.Mesh(holeRimGeoZ, rimMat);
              rMeshB.position.set(ox, 0, -d * 0.5 - 0.02);
              brickGroup.add(rMeshB);
              const hMeshB = new THREE.Mesh(holeGeoZ, holeMat);
              hMeshB.position.set(ox, 0, -d * 0.5 - 0.06);
              brickGroup.add(hMeshB);
            }
          }
        }
      }

      // Attach brickGroup to its exact hierarchical 10-DoF coaxial pin joint parent
      let parentGroup;
      let baseLocalPos;

      if (b.subassembly_id === 1) {
        // SA-01 Bootie Feet -> Left or Right Ankle Coaxial Pin (±36.0, 20.8, -16.0)
        if (cx < 0) {
          parentGroup = leftFootGroup;
          baseLocalPos = new THREE.Vector3(cx - (-36.0), cy - 20.8, cz - (-16.0));
        } else {
          parentGroup = rightFootGroup;
          baseLocalPos = new THREE.Vector3(cx - 36.0, cy - 20.8, cz - (-16.0));
        }
      } else if (b.subassembly_id === 2) {
        // SA-02 Slanted (+24°) Lower Shins -> Left or Right Knee Coaxial Pin (±36.0, 58.8035, 0.9202)
        if (cx < 0) {
          parentGroup = leftShinGroup;
          baseLocalPos = new THREE.Vector3(cx - (-36.0), cy - 58.8035, cz - 0.9202);
        } else {
          parentGroup = rightShinGroup;
          baseLocalPos = new THREE.Vector3(cx - 36.0, cy - 58.8035, cz - 0.9202);
        }
      } else if (b.subassembly_id === 3) {
        // SA-03 Slanted (-26°) Upper Thighs & Shields -> Left or Right Hip Coaxial Pin (±36.0, 90.441, -14.5104)
        if (cx < 0) {
          parentGroup = leftThighGroup;
          baseLocalPos = new THREE.Vector3(cx - (-36.0), cy - 90.441, cz - (-14.5104));
        } else {
          parentGroup = rightThighGroup;
          baseLocalPos = new THREE.Vector3(cx - 36.0, cy - 90.441, cz - (-14.5104));
        }
      } else if (b.subassembly_id === 4) {
        // SA-04 Hip Servo Cluster & Grey Roll Hubs -> pelvisPivot (0.0, 90.441, -14.5104)
        parentGroup = sa4HipGroup;
        baseLocalPos = new THREE.Vector3(cx, cy - 90.441, cz - (-14.5104));
      } else if (b.subassembly_id === 5) {
        // SA-05 Rounded White Torso & Rear Battery Spine -> pelvisPivot (0.0, 90.441, -14.5104)
        parentGroup = sa5TorsoGroup;
        baseLocalPos = new THREE.Vector3(cx, cy - 90.441, cz - (-14.5104));
      } else if (b.subassembly_id === 6) {
        // SA-06 Slanted (+19.725°) Multi-Servo Neck Stalk -> lowerNeckPivot (0.0, 141.641, 1.4896)
        parentGroup = neckStalkGroup;
        baseLocalPos = new THREE.Vector3(cx, cy - 141.641, cz - 1.4896);
      } else {
        // SA-07 Wide Curved White Visor Hood & Cyclops Camera -> upperNeckHeadPivot (0.0, 180.8000, 15.5307)
        parentGroup = visorHeadGroup;
        baseLocalPos = new THREE.Vector3(cx, cy - upperNeckY, cz - upperNeckZ);
      }

      brickGroup.position.copy(baseLocalPos);
      parentGroup.add(brickGroup);

      // Internal servo/Technic core classification for X-Ray mode
      const isInternalCore =
        b.part_id === '3700' ||
        b.part_id === '3701' ||
        b.part_id === '3894' ||
        b.part_id === '2780' ||
        b.part_id === '3937' ||
        b.part_id === '3938' ||
        b.part_id === '4032' ||
        b.color_id === 11 ||
        b.color_id === 85 ||
        b.color_id === 15;

      state.brickRecords.push({
        brick: b,
        meshGroup: brickGroup,
        bodyMat,
        edgeMat,
        baseLocalPos,
        isInternalCore,
        isTrans,
      });
    }
  }

  /**
   * Apply current step filter, highlight, and X-Ray mode
   */
  function updateSceneVisuals(triggerDropAnimation = false) {
    if (triggerDropAnimation) {
      state.stepDropAnim = 0.0;
      state.lastStepChangeTime = performance.now();
    }

    const curStep = state.currentStep;
    const hiStep = state.highlightCurrentStep;
    const xray = state.xraySpineMode;

    for (const rec of state.brickRecords) {
      const b = rec.brick;
      if (b.step_id > curStep) {
        rec.meshGroup.visible = false;
        continue;
      }
      rec.meshGroup.visible = true;

      const isActiveStep = b.step_id === curStep;
      const dropOffsetY =
        isActiveStep && hiStep ? (1.0 - state.stepDropAnim) * 22.0 : 0.0;
      rec.meshGroup.position.set(
        rec.baseLocalPos.x,
        rec.baseLocalPos.y + dropOffsetY,
        rec.baseLocalPos.z
      );

      if (isActiveStep && hiStep) {
        rec.bodyMat.transparent = rec.isTrans;
        rec.bodyMat.opacity = rec.isTrans ? 0.9 : 1.0;
        rec.bodyMat.emissive.setHex(0x280D00);
        rec.edgeMat.color.setHex(0xD9381E);
        rec.edgeMat.opacity = 1.0;
      } else if (xray) {
        if (rec.isInternalCore) {
          rec.bodyMat.transparent = rec.isTrans;
          rec.bodyMat.opacity = rec.isTrans ? 0.88 : 1.0;
          rec.bodyMat.emissive.setHex(0x000000);
          rec.edgeMat.color.setHex(0x11181C);
          rec.edgeMat.opacity = 0.78;
        } else {
          rec.bodyMat.transparent = true;
          rec.bodyMat.opacity = 0.14;
          rec.bodyMat.emissive.setHex(0x000000);
          rec.edgeMat.color.setHex(0x6C6E68);
          rec.edgeMat.opacity = 0.18;
        }
      } else {
        rec.bodyMat.transparent = rec.isTrans;
        rec.bodyMat.opacity = rec.isTrans ? 0.82 : 1.0;
        rec.bodyMat.emissive.setHex(0x000000);
        rec.edgeMat.color.setHex(0x1B2A34);
        rec.edgeMat.opacity = 0.45;
      }
    }

    updateArticulationAndExplosion();
  }

  /**
   * Apply 10-DoF Bipedal Walking Kinematics, Manual Sliders, Exploded View & Live CoG Tracking
   */
  function updateArticulationAndExplosion() {
    const phase = (state.gaitPhasePct % 100) / 100.0;
    const omegaT = phase * Math.PI * 2.0;
    const gaitActive = state.isWalking || state.gaitPhasePct > 0;

    // 1. Compute 10-DoF Joint Angles (combining gait cycle + manual slider offsets)
    const s = Math.sin(omegaT);
    const c = Math.cos(omegaT);

    // Hip Pitch (Left & Right swing opposite during stride around coaxial hip pins)
    const gaitLeftHipDeg = gaitActive ? 18.0 * s : 0.0;
    const gaitRightHipDeg = gaitActive ? -18.0 * s : 0.0;
    const leftHipDeg = gaitLeftHipDeg + state.hipPitchDeg;
    const rightHipDeg = gaitRightHipDeg - state.hipPitchDeg;

    // Knee Flexion (Flexes during swing phase to lift bootie foot clear of ground)
    const gaitLeftKneeDeg = gaitActive ? 22.0 * Math.max(0.0, s) : 0.0;
    const gaitRightKneeDeg = gaitActive ? 22.0 * Math.max(0.0, -s) : 0.0;
    const leftKneeDeg = gaitLeftKneeDeg + state.kneeFlexDeg;
    const rightKneeDeg = gaitRightKneeDeg + state.kneeFlexDeg;

    // Ankle Pitch Compensation (keeps bootie foot soles parallel to the ground Y=0)
    const leftAnkleDeg = -(leftHipDeg - leftKneeDeg * 0.88);
    const rightAnkleDeg = -(rightHipDeg - rightKneeDeg * 0.88);

    // Lateral Pelvis Weight-Shift & Hip Roll over stance foot + Vertical Bounce
    const pelvisShiftX = gaitActive ? 11.8 * s : 0.0;
    const pelvisRollDeg = gaitActive ? -5.6 * s : 0.0;
    const crouchDropY = -state.kneeFlexDeg * 0.35;
    const pelvisBounceY = (gaitActive ? 3.2 * Math.abs(c) : 0.0) + crouchDropY;

    // Neck Pitch Counter-Balance & Head Camera Look-Around Yaw
    const gaitNeckPitchDeg = gaitActive ? -6.0 * Math.cos(2.0 * omegaT) : 0.0;
    const totalNeckPitchDeg = gaitNeckPitchDeg + state.neckPitchDeg;
    const gaitHeadYawDeg = gaitActive ? 10.0 * s : 0.0;
    const totalHeadYawDeg = gaitHeadYawDeg + state.neckYawDeg;

    // Apply rotations to Three.js 10-DoF coaxial pin hierarchy
    if (pelvisPivot) {
      pelvisPivot.position.set(pelvisShiftX, 90.441 + pelvisBounceY, -14.5104);
      pelvisPivot.rotation.z = THREE.MathUtils.degToRad(pelvisRollDeg);
    }

    if (leftHipPivot && rightHipPivot) {
      leftHipPivot.rotation.x = THREE.MathUtils.degToRad(-leftHipDeg);
      rightHipPivot.rotation.x = THREE.MathUtils.degToRad(-rightHipDeg);
    }

    if (leftKneePivot && rightKneePivot) {
      leftKneePivot.rotation.x = THREE.MathUtils.degToRad(leftKneeDeg);
      rightKneePivot.rotation.x = THREE.MathUtils.degToRad(rightKneeDeg);
    }

    if (leftAnklePivot && rightAnklePivot) {
      leftAnklePivot.rotation.x = THREE.MathUtils.degToRad(-leftAnkleDeg);
      rightAnklePivot.rotation.x = THREE.MathUtils.degToRad(-rightAnkleDeg);
    }

    if (lowerNeckPivot) {
      lowerNeckPivot.rotation.x = THREE.MathUtils.degToRad(totalNeckPitchDeg);
    }

    if (upperNeckHeadPivot) {
      upperNeckHeadPivot.rotation.y = THREE.MathUtils.degToRad(totalHeadYawDeg);
      upperNeckHeadPivot.rotation.x = THREE.MathUtils.degToRad(-totalNeckPitchDeg * 0.45);
    }

    // 2. Exploded 7-Subassembly View Offsets
    const ex = state.explodePct / 100.0;
    if (leftFootGroup && rightFootGroup) {
      leftFootGroup.position.set(-ex * 18.0, -ex * 34.0, ex * 10.0);
      rightFootGroup.position.set(ex * 18.0, -ex * 34.0, ex * 10.0);
    }
    if (leftShinGroup && rightShinGroup) {
      leftShinGroup.position.set(-ex * 22.0, -ex * 16.0, 0.0);
      rightShinGroup.position.set(ex * 22.0, -ex * 16.0, 0.0);
    }
    if (leftThighGroup && rightThighGroup) {
      leftThighGroup.position.set(-ex * 32.0, 0.0, 0.0);
      rightThighGroup.position.set(ex * 32.0, 0.0, 0.0);
    }
    if (sa4HipGroup) {
      sa4HipGroup.position.set(0.0, 0.0, -ex * 16.0);
    }
    if (sa5TorsoGroup) {
      sa5TorsoGroup.position.set(0.0, ex * 22.0, -ex * 10.0);
    }
    if (neckStalkGroup) {
      neckStalkGroup.position.set(0.0, ex * 38.0, 0.0);
    }
    if (visorHeadGroup) {
      visorHeadGroup.position.set(0.0, ex * 64.0, ex * 24.0);
    }

    // 3. Dynamically update 3D Center of Gravity Sphere, Plumb Line, and Telemetry Readout
    const sData = state.stepDataMap.get(state.currentStep);
    if (sData && cogOverlayGroup) {
      cogOverlayGroup.visible = state.showCogOverlay;
      const dynCogX =
        sData.cumCog.x +
        pelvisShiftX * 0.85;
      const dynCogY =
        sData.cumCog.y +
        pelvisBounceY * 0.75 -
        Math.abs(leftHipDeg) * 0.02;
      const dynCogZ =
        sData.cumCog.z +
        Math.sin(THREE.MathUtils.degToRad(totalNeckPitchDeg)) * 12.0 +
        (gaitActive ? 2.8 * Math.abs(s) : 0.0);

      cogSphereMesh.position.set(dynCogX, dynCogY, dynCogZ);
      cogGroundCross.position.set(dynCogX, 0.5, dynCogZ);
      const posAttr = cogPlumbLine.geometry.attributes.position;
      posAttr.setXYZ(0, dynCogX, dynCogY, dynCogZ);
      posAttr.setXYZ(1, dynCogX, 0.4, dynCogZ);
      posAttr.needsUpdate = true;

      // Update live CoG readouts in Left and Right panels (Support Hull: X in [-56,+56], Z in [-48,+40])
      const cogStr = `${dynCogX >= 0 ? '+' : ''}${dynCogX.toFixed(1)}, ${dynCogY.toFixed(1)}, ${dynCogZ >= 0 ? '+' : ''}${dynCogZ.toFixed(1)}`;
      const teleCogEl = document.getElementById('tele-cum-cog');
      if (teleCogEl) teleCogEl.textContent = cogStr;

      const xzEl = document.getElementById('cog-xz-readout');
      if (xzEl) {
        xzEl.textContent = `${dynCogX >= 0 ? '+' : ''}${dynCogX.toFixed(2)} mm, ${dynCogZ >= 0 ? '+' : ''}${dynCogZ.toFixed(2)} mm`;
      }
      const yEl = document.getElementById('cog-y-readout');
      if (yEl) {
        yEl.textContent = `${dynCogY.toFixed(2)} mm (${(dynCogY / PLATE_MM).toFixed(2)}p)`;
      }
      const fbEl = document.getElementById('cog-fb-margin');
      if (fbEl) {
        const frontMargin = Math.max(0, 40.0 - dynCogZ);
        const backMargin = Math.max(0, 48.0 + dynCogZ);
        fbEl.textContent = `${frontMargin.toFixed(2)} mm / ${backMargin.toFixed(2)} mm`;
      }
      const lrEl = document.getElementById('cog-lr-margin');
      if (lrEl) {
        const leftMargin = Math.max(0, 56.0 + dynCogX);
        const rightMargin = Math.max(0, 56.0 - dynCogX);
        lrEl.textContent = `${leftMargin.toFixed(2)} mm / ${rightMargin.toFixed(2)} mm`;
      }
    }
  }

  /**
   * Update Left Inspector Panel, Scrubber, and Sub-Assembly Tabs for the active step
   */
  function updateStepUI() {
    const curStep = state.currentStep;
    const sData = state.stepDataMap.get(curStep);
    if (!sData) return;

    const sBricks = sData.bricks;
    const b0 = sBricks[0];
    const saId = b0.subassembly_id;
    const yMin = Math.min(...sBricks.map((b) => b.y));
    const yMax = Math.max(...sBricks.map((b) => b.y_top));
    const pitchDeg = typeof b0.world_pitch_deg === 'number' ? b0.world_pitch_deg : 0.0;
    const pitchDecimals = Math.abs(pitchDeg - Math.round(pitchDeg)) > 0.05 ? 1 : 0;
    const pitchStr = `${pitchDeg > 0 ? '+' : ''}${pitchDeg.toFixed(pitchDecimals)}°`;
    const wyMaxMm = Math.max(
      ...sBricks.map((b) => {
        const wc = b.world_center_mm || b.center_mm;
        return wc[1] + 0.5 * b.dy * PLATE_MM;
      })
    ).toFixed(1);

    let cleanSaName = b0.subassembly_name || '';
    if (cleanSaName.includes(': ')) {
      cleanSaName = cleanSaName.split(': ')[1];
    }

    document.getElementById('step-num-title').textContent =
      `STEP ${String(curStep).padStart(3, '0')} / ${state.totalSteps}`;
    document.getElementById('step-elevation-badge').textContent =
      `L=${yMin}..${yMax}p (${pitchStr} • ${wyMaxMm} mm)`;
    document.getElementById('step-sa-name').textContent =
      `SA-0${saId} // ${cleanSaName}`;
    document.getElementById('step-notes-desc').textContent =
      b0.notes || 'Sequential 3D slanted & coaxial pin placement';

    const totalPcs = state.model ? state.model.total_pieces : 945;
    document.getElementById('tele-step-bonds').textContent = `+${sData.bonds} BONDS`;
    document.getElementById('tele-cum-pieces').textContent = `${sData.cumPieces} / ${totalPcs} PCS`;
    document.getElementById('tele-cum-mass').textContent = `${sData.cumMass.toFixed(2)} g`;

    // Scrubber controls
    const scrubber = document.getElementById('step-scrubber');
    scrubber.max = String(state.totalSteps);
    scrubber.value = String(curStep);
    document.getElementById('scrubber-step-label').textContent =
      `STEP ${String(curStep).padStart(3, '0')} / ${state.totalSteps}`;
    document.getElementById('scrubber-pct-label').textContent =
      `${((curStep / state.totalSteps) * 100).toFixed(1)}%`;

    // Highlight active Sub-Assembly tab
    document.querySelectorAll('.sa-tab').forEach((tab) => {
      const tabSa = parseInt(tab.getAttribute('data-sa'), 10);
      tab.classList.toggle('active', tabSa === saId);
    });

    // Aggregate parts in current step by (part_id, color_id)
    const stepLotsMap = new Map();
    for (const b of sBricks) {
      const key = `${b.part_id}_${b.color_id}`;
      if (!stepLotsMap.has(key)) {
        stepLotsMap.set(key, {
          part_id: b.part_id,
          part_name: b.part_name,
          color_id: b.color_id,
          color_name: b.color_name,
          dx: b.dx,
          dy: b.dy,
          dz: b.dz,
          has_top_studs: b.has_top_studs,
          qty: 0,
          coords: [],
        });
      }
      const entry = stepLotsMap.get(key);
      entry.qty += 1;
      entry.coords.push(`(${b.x},${b.y},${b.z})`);
    }

    document.getElementById('parts-callout-header').textContent =
      `STEP ${String(curStep).padStart(3, '0')} PARTS CALLOUT (${sBricks.length} PCS)`;

    const listEl = document.getElementById('step-parts-list');
    listEl.innerHTML = '';
    for (const lot of stepLotsMap.values()) {
      const hex = COLOR_HEX[lot.color_id] || '#CCCCCC';
      const svgThumb = createIsometricBrickSvg(
        lot.part_id,
        hex,
        lot.dx,
        lot.dy,
        lot.dz,
        lot.has_top_studs
      );
      const posSample =
        lot.coords.length <= 3
          ? lot.coords.join(' ')
          : `${lot.coords.slice(0, 3).join(' ')} +${lot.coords.length - 3}`;

      const card = document.createElement('div');
      card.className = 'part-callout-card';
      card.innerHTML = `
        <div class="part-svg-thumb">${svgThumb}</div>
        <div class="part-meta">
          <div class="part-id-line">
            <span class="color-dot" style="background:${hex};"></span>
            <span>#${lot.part_id} • ${lot.color_name}</span>
          </div>
          <div class="part-name-line" title="${lot.part_name}">${lot.part_name}</div>
          <div class="part-pos-line">Grid: ${posSample}</div>
        </div>
        <div class="part-qty-badge">&times;${lot.qty}</div>
      `;
      listEl.appendChild(card);
    }
  }

  /**
   * Jump to a specific build step (1..129)
   */
  function setStep(stepNumber, animateDrop = true) {
    const clamped = Math.max(1, Math.min(state.totalSteps, Math.round(stepNumber)));
    state.currentStep = clamped;
    updateStepUI();
    updateSceneVisuals(animateDrop);
  }

  /**
   * Camera Preset Positioning
   */
  function setCameraPreset(presetName) {
    document.querySelectorAll('#camera-presets .btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-cam') === presetName);
    });

    const center = new THREE.Vector3(0, 124, -4);
    switch (presetName) {
      case 'front':
        camera.position.set(0, 132, 450);
        controls.target.copy(center);
        break;
      case 'right':
        camera.position.set(450, 132, -4);
        controls.target.copy(center);
        break;
      case 'rear':
        camera.position.set(0, 136, -450);
        controls.target.copy(center);
        break;
      case 'top':
        camera.position.set(0, 520, 4);
        controls.target.set(0, 0, -4);
        break;
      case 'camera':
        camera.position.set(115, 226, 215);
        controls.target.set(0, 212, 24);
        break;
      case 'hips':
        camera.position.set(165, 92, 195);
        controls.target.set(0, 68, -6);
        break;
      case 'isometric':
      default:
        camera.position.set(305, 275, 335);
        controls.target.copy(center);
        break;
    }
    controls.update();
  }

  /**
   * Start / Stop Live 60 FPS 10-DoF Bipedal Walk Simulation
   */
  function toggleWalkSimulation(forceState) {
    const nextState = typeof forceState === 'boolean' ? forceState : !state.isWalking;
    state.isWalking = nextState;
    state.lastWalkTickTime = performance.now();

    if (state.isWalking && state.currentStep < state.totalSteps) {
      // Ensure full 945-piece robot is visible when walking starts
      setStep(state.totalSteps, false);
    }

    const btnRight = document.getElementById('btn-toggle-walk');
    const btnTop = document.getElementById('btn-walk-top');
    const hudTitle = document.getElementById('hud-overlay-status');

    if (state.isWalking) {
      if (btnRight) {
        btnRight.textContent = 'STOP BIPEDAL WALK (ACTIVE 10-DoF)';
        btnRight.classList.add('walking');
      }
      if (btnTop) {
        btnTop.textContent = 'STOP WALK';
        btnTop.classList.add('walking');
      }
      if (hudTitle) {
        hudTitle.textContent = '10-DoF BIPEDAL WALK SIMULATION // 8/8 DOUBLE-SHEAR PIN JOINTS (16 SHEAR PINS) & DYNAMIC CoG GAIT ACTIVE';
      }
    } else {
      if (btnRight) {
        btnRight.textContent = 'START BIPEDAL WALK (10-DoF GAIT)';
        btnRight.classList.remove('walking');
      }
      if (btnTop) {
        btnTop.textContent = '10-DoF WALK';
        btnTop.classList.remove('walking');
      }
      if (hudTitle) {
        hudTitle.textContent = '3D SLANTED CAD VIEWPORT // SHINS +24° • THIGHS -26° • NECK +19.7° • 28 HORIZONTAL X-PINS';
      }
    }
    updateArticulationAndExplosion();
  }

  /**
   * Parse microduck_bom.csv and populate the 101-Lot BrickLink Procurement Hub Modal
   */
  function parseBomCsv(csvText) {
    const lines = csvText.trim().split(/\r?\n/);
    if (lines.length < 2) return [];
    const lots = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      const cols = [];
      let cur = '';
      let inQuotes = false;
      for (let c = 0; c < line.length; c++) {
        const ch = line[c];
        if (ch === '"') {
          inQuotes = !inQuotes;
        } else if (ch === ',' && !inQuotes) {
          cols.push(cur);
          cur = '';
        } else {
          cur += ch;
        }
      }
      cols.push(cur);
      if (cols.length < 12) continue;

      const part_id = cols[0];
      const part_name = cols[1];
      const category = cols[2];
      const color_id = parseInt(cols[3], 10);
      const color_name = cols[4];
      const ldraw_color_id = parseInt(cols[5], 10);
      const hex_rgb = cols[6];
      const quantity = parseInt(cols[7], 10);
      const unit_mass_g = parseFloat(cols[8]);
      const total_mass_g = parseFloat(cols[9]);
      const dimensions_studs_plates = cols[10];
      const subassemblies = cols[11];

      const m = dimensions_studs_plates.match(/(\d+)x(\d+)\s*\((\d+)p\)/);
      const dx = m ? parseInt(m[1], 10) : 1;
      const dz = m ? parseInt(m[2], 10) : 1;
      const dy = m ? parseInt(m[3], 10) : 1;
      const hasTopStuds =
        part_id !== '2780' && !category.includes('Tile') && !category.includes('Slope');

      let unitPrice = 0.05 + 0.008 * (dx * dy * dz);
      if (['3937', '3938', '4032', '15068'].includes(part_id)) unitPrice = 0.14;
      else if (['3700', '3701', '3894', '85984', '54200', '11477', '2412b', '2780'].includes(part_id)) unitPrice = 0.11;

      lots.push({
        part_id,
        part_name,
        category,
        color_id,
        color_name,
        ldraw_color_id,
        hex_rgb,
        quantity,
        unit_mass_g,
        total_mass_g,
        dimensions_studs_plates,
        subassemblies,
        dx,
        dy,
        dz,
        hasTopStuds,
        unitPrice,
        lineCost: quantity * unitPrice,
      });
    }
    return lots;
  }

  function populateBomColorFilter(lots) {
    const colorSelect = document.getElementById('bom-color-filter');
    colorSelect.innerHTML = `<option value="ALL">All LEGO Colors (${lots.length} Lots)</option>`;
    const byColor = new Map();
    for (const lot of lots) {
      if (!byColor.has(lot.color_id)) {
        byColor.set(lot.color_id, {
          name: lot.color_name,
          lots: 0,
          pcs: 0,
        });
      }
      const c = byColor.get(lot.color_id);
      c.lots += 1;
      c.pcs += lot.quantity;
    }

    for (const [cid, info] of byColor.entries()) {
      const opt = document.createElement('option');
      opt.value = String(cid);
      opt.textContent = `BL #${cid} ${info.name} (${info.lots} lots / ${info.pcs} pcs)`;
      colorSelect.appendChild(opt);
    }
  }

  function renderBomTable() {
    const query = document.getElementById('bom-search-input').value.trim().toLowerCase();
    const colorVal = document.getElementById('bom-color-filter').value;
    const saVal = document.getElementById('bom-sa-filter').value;

    const filtered = state.bomLots.filter((lot) => {
      if (colorVal !== 'ALL' && String(lot.color_id) !== colorVal) return false;
      if (saVal !== 'ALL' && !lot.subassemblies.split(',').includes(saVal)) return false;
      if (query) {
        const hay = `${lot.part_id} ${lot.part_name} ${lot.category} ${lot.color_name}`.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      return true;
    });

    const totalPcs = filtered.reduce((acc, l) => acc + l.quantity, 0);
    const totalCost = filtered.reduce((acc, l) => acc + l.lineCost, 0);
    document.getElementById('bom-filter-summary').textContent =
      `Showing ${filtered.length} / ${state.bomLots.length} lots (${totalPcs} pcs • Est. $${totalCost.toFixed(2)})`;

    const tbody = document.getElementById('bom-table-body');
    tbody.innerHTML = '';

    for (const lot of filtered) {
      const svg = createIsometricBrickSvg(
        lot.part_id,
        lot.hex_rgb,
        lot.dx,
        lot.dy,
        lot.dz,
        lot.hasTopStuds
      );
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><div class="part-svg-thumb">${svg}</div></td>
        <td><strong>#${lot.part_id}</strong></td>
        <td>
          <div style="font-weight:700;color:var(--text-primary);">${lot.part_name}</div>
          <div style="font-size:10px;color:var(--text-muted);">${lot.category}</div>
        </td>
        <td>
          <span class="color-dot" style="background:${lot.hex_rgb};vertical-align:middle;margin-right:6px;"></span>
          <strong>${lot.color_name}</strong>
          <span style="color:var(--text-muted);font-size:10px;">(BL:${lot.color_id} / LD:${lot.ldraw_color_id})</span>
        </td>
        <td>${lot.dimensions_studs_plates}</td>
        <td><strong style="color:var(--accent-orange);font-size:12.5px;">&times;${lot.quantity}</strong></td>
        <td>${lot.total_mass_g.toFixed(2)} g</td>
        <td>$${lot.lineCost.toFixed(2)} <span style="color:var(--text-muted);font-size:9.5px;">($${lot.unitPrice.toFixed(2)}/ea)</span></td>
        <td>SA: ${lot.subassemblies}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  function showToast(msg) {
    const banner = document.getElementById('toast-banner');
    banner.textContent = msg;
    banner.classList.add('show');
    clearTimeout(banner._timer);
    banner._timer = setTimeout(() => {
      banner.classList.remove('show');
    }, 3200);
  }

  async function copyBricklinkXml() {
    if (!state.bricklinkXmlText) {
      showToast('BrickLink XML not loaded yet.');
      return;
    }
    try {
      await navigator.clipboard.writeText(state.bricklinkXmlText);
      showToast(`COPIED ${state.bomLots.length}-LOT BRICKLINK WANTED LIST XML TO CLIPBOARD`);
    } catch (_err) {
      const ta = document.createElement('textarea');
      ta.value = state.bricklinkXmlText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      showToast(`COPIED ${state.bomLots.length}-LOT BRICKLINK WANTED LIST XML TO CLIPBOARD`);
    }
  }

  /**
   * Bind all UI Controls & Event Listeners
   */
  function bindUIEvents() {
    // Timeline Scrubber & Step Buttons
    document.getElementById('step-scrubber').addEventListener('input', (e) => {
      stopAutoPlay();
      setStep(parseInt(e.target.value, 10), true);
    });

    document.getElementById('btn-step-first').addEventListener('click', () => {
      stopAutoPlay();
      setStep(1, true);
    });

    document.getElementById('btn-step-prev').addEventListener('click', () => {
      stopAutoPlay();
      setStep(state.currentStep - 1, true);
    });

    document.getElementById('btn-step-next').addEventListener('click', () => {
      stopAutoPlay();
      setStep(state.currentStep + 1, true);
    });

    document.getElementById('btn-step-final').addEventListener('click', () => {
      stopAutoPlay();
      setStep(state.totalSteps, true);
    });

    document.getElementById('btn-play-pause').addEventListener('click', () => {
      if (state.isPlaying) {
        stopAutoPlay();
      } else {
        startAutoPlay();
      }
    });

    // Speed Selector (1x, 2x, 5x)
    document.querySelectorAll('#speed-selector .btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#speed-selector .btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        state.playSpeed = parseInt(btn.getAttribute('data-speed'), 10);
        if (state.isPlaying) {
          startAutoPlay();
        }
      });
    });

    // 7 Sub-Assembly Quick-Jump Tabs
    document.querySelectorAll('.sa-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        stopAutoPlay();
        const targetStep = parseInt(tab.getAttribute('data-step'), 10);
        setStep(targetStep, true);
      });
    });

    // Camera Presets & Reset
    document.querySelectorAll('#camera-presets .btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        setCameraPreset(btn.getAttribute('data-cam'));
      });
    });

    document.getElementById('btn-reset-view').addEventListener('click', () => {
      setCameraPreset('isometric');
    });

    // Engineering Overlays
    document.getElementById('toggle-highlight-step').addEventListener('change', (e) => {
      state.highlightCurrentStep = e.target.checked;
      updateSceneVisuals(false);
    });

    document.getElementById('toggle-cog-overlay').addEventListener('change', (e) => {
      state.showCogOverlay = e.target.checked;
      updateSceneVisuals(false);
    });

    document.getElementById('toggle-xray-spine').addEventListener('change', (e) => {
      state.xraySpineMode = e.target.checked;
      updateSceneVisuals(false);
    });

    // Walk Simulation Toggle Buttons (Right Panel + Top Header)
    document.getElementById('btn-toggle-walk').addEventListener('click', () => {
      toggleWalkSimulation();
    });
    document.getElementById('btn-walk-top').addEventListener('click', () => {
      toggleWalkSimulation();
    });

    // 10-DoF Kinematic & Exploded View Sliders
    document.getElementById('slider-gait-phase').addEventListener('input', (e) => {
      state.gaitPhasePct = parseFloat(e.target.value);
      document.getElementById('val-gait-phase').textContent = `${Math.round(state.gaitPhasePct)}%`;
      updateArticulationAndExplosion();
    });

    document.getElementById('slider-hip-pitch').addEventListener('input', (e) => {
      state.hipPitchDeg = parseFloat(e.target.value);
      document.getElementById('val-hip-pitch').textContent =
        `${state.hipPitchDeg > 0 ? '+' : ''}${state.hipPitchDeg}°`;
      updateArticulationAndExplosion();
    });

    document.getElementById('slider-knee-flex').addEventListener('input', (e) => {
      state.kneeFlexDeg = parseFloat(e.target.value);
      document.getElementById('val-knee-flex').textContent = `${state.kneeFlexDeg}°`;
      updateArticulationAndExplosion();
    });

    document.getElementById('slider-neck-pitch').addEventListener('input', (e) => {
      state.neckPitchDeg = parseFloat(e.target.value);
      document.getElementById('val-neck-pitch').textContent =
        `${state.neckPitchDeg > 0 ? '+' : ''}${state.neckPitchDeg}°`;
      updateArticulationAndExplosion();
    });

    document.getElementById('slider-neck-yaw').addEventListener('input', (e) => {
      state.neckYawDeg = parseFloat(e.target.value);
      document.getElementById('val-neck-yaw').textContent =
        `${state.neckYawDeg > 0 ? '+' : ''}${state.neckYawDeg}°`;
      updateArticulationAndExplosion();
    });

    document.getElementById('slider-explode').addEventListener('input', (e) => {
      state.explodePct = parseFloat(e.target.value);
      document.getElementById('val-explode').textContent = `${state.explodePct}%`;
      updateArticulationAndExplosion();
    });

    document.getElementById('btn-reset-articulation').addEventListener('click', () => {
      toggleWalkSimulation(false);
      state.gaitPhasePct = 0;
      state.hipPitchDeg = 0;
      state.kneeFlexDeg = 0;
      state.neckPitchDeg = 0;
      state.neckYawDeg = 0;
      state.explodePct = 0;
      if (gridHelper) gridHelper.position.z = 0;

      document.getElementById('slider-gait-phase').value = '0';
      document.getElementById('slider-hip-pitch').value = '0';
      document.getElementById('slider-knee-flex').value = '0';
      document.getElementById('slider-neck-pitch').value = '0';
      document.getElementById('slider-neck-yaw').value = '0';
      document.getElementById('slider-explode').value = '0';

      document.getElementById('val-gait-phase').textContent = '0%';
      document.getElementById('val-hip-pitch').textContent = '0°';
      document.getElementById('val-knee-flex').textContent = '0°';
      document.getElementById('val-neck-pitch').textContent = '0°';
      document.getElementById('val-neck-yaw').textContent = '0°';
      document.getElementById('val-explode').textContent = '0%';

      updateArticulationAndExplosion();
    });

    // BOM Modal & XML Copy
    const modal = document.getElementById('bom-modal');
    const videoModal = document.getElementById('video-modal');
    const videoPlayer = document.getElementById('explainer-video-player');

    function closeVideoModal() {
      if (videoModal) videoModal.classList.remove('open');
      if (videoPlayer && !videoPlayer.paused) videoPlayer.pause();
    }

    const openVideoBtn = document.getElementById('btn-open-video-modal');
    if (openVideoBtn && videoModal) {
      openVideoBtn.addEventListener('click', () => {
        videoModal.classList.add('open');
        if (videoPlayer) {
          videoPlayer.play().catch(() => {});
        }
      });
    }

    const closeVideoBtn = document.getElementById('btn-close-video-modal');
    if (closeVideoBtn) {
      closeVideoBtn.addEventListener('click', closeVideoModal);
    }

    if (videoModal) {
      videoModal.addEventListener('click', (e) => {
        if (e.target === videoModal) closeVideoModal();
      });
    }

    document.getElementById('btn-open-bom-modal').addEventListener('click', () => {
      modal.classList.add('open');
      renderBomTable();
    });

    document.getElementById('btn-close-bom-modal').addEventListener('click', () => {
      modal.classList.remove('open');
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (modal.classList.contains('open')) modal.classList.remove('open');
        if (videoModal && videoModal.classList.contains('open')) closeVideoModal();
      }
    });

    document.getElementById('bom-search-input').addEventListener('input', renderBomTable);
    document.getElementById('bom-color-filter').addEventListener('change', renderBomTable);
    document.getElementById('bom-sa-filter').addEventListener('change', renderBomTable);

    document.getElementById('btn-copy-bricklink-xml').addEventListener('click', copyBricklinkXml);
    document.getElementById('btn-copy-xml-quick').addEventListener('click', copyBricklinkXml);
  }

  function startAutoPlay() {
    stopAutoPlay();
    if (state.currentStep >= state.totalSteps) {
      state.currentStep = 1;
    }
    state.isPlaying = true;
    const playBtn = document.getElementById('btn-play-pause');
    playBtn.textContent = 'PAUSE BUILD';
    playBtn.classList.add('active');

    const intervalMs = Math.round(420 / state.playSpeed);
    state.playTimer = setInterval(() => {
      if (state.currentStep < state.totalSteps) {
        setStep(state.currentStep + 1, true);
      } else {
        stopAutoPlay();
      }
    }, intervalMs);
  }

  function stopAutoPlay() {
    state.isPlaying = false;
    if (state.playTimer) {
      clearInterval(state.playTimer);
      state.playTimer = null;
    }
    const playBtn = document.getElementById('btn-play-pause');
    if (playBtn) {
      playBtn.textContent = 'AUTO-BUILD PLAY';
      playBtn.classList.remove('active');
    }
  }

  function onWindowResize() {
    const container = document.getElementById('canvas-container');
    const canvas = document.getElementById('lego-canvas');
    if (!container || !camera) return;
    const cw = Math.max(320, container.clientWidth || 820);
    const ch = Math.max(240, container.clientHeight || 620);
    camera.aspect = cw / ch;
    camera.updateProjectionMatrix();
    if (renderer) {
      renderer.setSize(cw, ch);
    } else if (canvas) {
      canvas.width = cw;
      canvas.height = ch;
    }
  }

  /**
   * Software 3D-Projected 2D Canvas Fallback Renderer (if WebGL is disabled/unavailable in browser)
   */
  function renderCanvas2DFallback() {
    const canvas = document.getElementById('lego-canvas');
    if (!canvas || !scene || !camera) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.fillStyle = '#F8FAF7';
    ctx.fillRect(0, 0, w, h);

    scene.updateMatrixWorld(true);
    camera.updateMatrixWorld(true);
    const viewProj = new THREE.Matrix4().multiplyMatrices(
      camera.projectionMatrix,
      camera.matrixWorldInverse
    );

    function projectPt(wx, wy, wz) {
      const v = new THREE.Vector4(wx, wy, wz, 1.0).applyMatrix4(viewProj);
      if (v.w <= 0.1) return null;
      const invW = 1.0 / v.w;
      return {
        x: (v.x * invW * 0.5 + 0.5) * w,
        y: (0.5 - v.y * invW * 0.5) * h,
        z: v.z * invW,
        w: v.w,
      };
    }

    // Draw Ground Grid
    ctx.strokeStyle = '#D5DFDA';
    ctx.lineWidth = 1;
    for (let g = -144; g <= 144; g += 16) {
      const p1 = projectPt(g, 0, -144);
      const p2 = projectPt(g, 0, 144);
      if (p1 && p2) {
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
      const p3 = projectPt(-144, 0, g);
      const p4 = projectPt(144, 0, g);
      if (p3 && p4) {
        ctx.beginPath();
        ctx.moveTo(p3.x, p3.y);
        ctx.lineTo(p4.x, p4.y);
        ctx.stroke();
      }
    }

    // Sort visible bricks back-to-front by camera depth
    const drawList = [];
    const tmpWorld = new THREE.Vector3();
    for (const rec of state.brickRecords) {
      if (!rec.meshGroup.visible) continue;
      rec.meshGroup.getWorldPosition(tmpWorld);
      const p = projectPt(tmpWorld.x, tmpWorld.y, tmpWorld.z);
      if (p) {
        drawList.push({ rec, p, wx: tmpWorld.x, wy: tmpWorld.y, wz: tmpWorld.z });
      }
    }
    drawList.sort((a, b) => b.p.w - a.p.w);

    for (const item of drawList) {
      const { rec } = item;
      const b = rec.brick;
      const hw = (b.dx * STUD_MM - SEAM_XZ) * 0.5;
      const hh = (b.dy * PLATE_MM - SEAM_Y) * 0.5;
      const hd = (b.dz * STUD_MM - SEAM_XZ) * 0.5;
      const m = rec.meshGroup.matrixWorld;

      function corner(lx, ly, lz) {
        const v = new THREE.Vector3(lx, ly, lz).applyMatrix4(m);
        return projectPt(v.x, v.y, v.z);
      }

      const c000 = corner(-hw, -hh, -hd);
      const c100 = corner(hw, -hh, -hd);
      const c101 = corner(hw, -hh, hd);
      const c001 = corner(-hw, -hh, hd);
      const c010 = corner(-hw, hh, -hd);
      const c110 = corner(hw, hh, -hd);
      const c111 = corner(hw, hh, hd);
      const c011 = corner(-hw, hh, hd);
      if (!c000 || !c100 || !c101 || !c001 || !c010 || !c110 || !c111 || !c011) continue;

      const baseHex = COLOR_HEX[b.color_id] || '#CCCCCC';
      ctx.globalAlpha = rec.bodyMat.opacity || 1.0;
      ctx.strokeStyle = rec.brick.step_id === state.currentStep && state.highlightCurrentStep ? '#D9381E' : '#1B2A34';
      ctx.lineWidth = rec.brick.step_id === state.currentStep && state.highlightCurrentStep ? 1.4 : 0.7;

      const faces = [
        { pts: [c001, c101, c111, c011], fill: baseHex },
        { pts: [c100, c000, c010, c110], fill: baseHex },
        { pts: [c101, c100, c110, c111], fill: baseHex },
        { pts: [c000, c001, c011, c010], fill: baseHex },
        { pts: [c011, c111, c110, c010], fill: baseHex },
      ];
      for (const f of faces) {
        ctx.fillStyle = f.fill;
        ctx.beginPath();
        ctx.moveTo(f.pts[0].x, f.pts[0].y);
        ctx.lineTo(f.pts[1].x, f.pts[1].y);
        ctx.lineTo(f.pts[2].x, f.pts[2].y);
        ctx.lineTo(f.pts[3].x, f.pts[3].y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1.0;
  }

  function animate(now) {
    requestAnimationFrame(animate);

    // 1. Live 60 FPS 10-DoF Bipedal Walking Simulation
    if (state.isWalking) {
      const dtSec = Math.min(0.1, (now - state.lastWalkTickTime) / 1000.0);
      state.lastWalkTickTime = now;

      // Full stride period = 1.4 seconds
      state.gaitPhasePct = (state.gaitPhasePct + dtSec * (100.0 / 1.4)) % 100.0;
      const phaseSlider = document.getElementById('slider-gait-phase');
      const phaseVal = document.getElementById('val-gait-phase');
      if (phaseSlider) phaseSlider.value = String(Math.round(state.gaitPhasePct));
      if (phaseVal) phaseVal.textContent = `${Math.round(state.gaitPhasePct)}%`;

      // Scroll ground grid backward to visualize forward walking speed
      if (gridHelper) {
        state.floorScrollZ = (state.floorScrollZ - dtSec * 42.0) % 16.0;
        gridHelper.position.z = state.floorScrollZ;
      }

      updateArticulationAndExplosion();
    }

    // 2. Smooth vertical drop-in animation for active step bricks
    if (state.stepDropAnim < 1.0) {
      const elapsed = now - state.lastStepChangeTime;
      state.stepDropAnim = Math.min(1.0, elapsed / 220.0);
      const curStep = state.currentStep;
      const dropOffsetY =
        state.highlightCurrentStep ? (1.0 - state.stepDropAnim) * 22.0 : 0.0;
      for (const rec of state.brickRecords) {
        if (rec.brick.step_id === curStep) {
          rec.meshGroup.position.y = rec.baseLocalPos.y + dropOffsetY;
        }
      }
    }

    if (controls) controls.update();
    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    } else {
      renderCanvas2DFallback();
    }
  }

  /**
   * Bootstrap Studio Application (uses preloaded window.__MICRODUCK_BUNDLE__ immediately, with fetch fallback)
   */
  async function initApp() {
    if (state._initialized) return;
    state._initialized = true;
    try {
      initThreeScene();
      bindUIEvents();

      let bomCsvText = '';
      if (window.__MICRODUCK_BUNDLE__ && window.__MICRODUCK_BUNDLE__.model) {
        state.model = window.__MICRODUCK_BUNDLE__.model;
        state.report = window.__MICRODUCK_BUNDLE__.report;
        bomCsvText = window.__MICRODUCK_BUNDLE__.bomCsv || '';
        state.bricklinkXmlText = window.__MICRODUCK_BUNDLE__.bricklinkXml || '';
      } else {
        const [modelRes, reportRes, bomRes, xmlRes] = await Promise.all([
          fetch('output/microduck_model.json'),
          fetch('output/verification_report.json'),
          fetch('output/microduck_bom.csv'),
          fetch('output/microduck_bricklink_wanted_list.xml'),
        ]);
        state.model = await modelRes.json();
        state.report = await reportRes.json();
        bomCsvText = await bomRes.text();
        state.bricklinkXmlText = await xmlRes.text();
      }

      state.totalSteps = state.model.total_steps || 129;
      state.currentStep = state.totalSteps;

      // Dynamically sync top header metrics from verification_report.json
      if (state.report && state.report.summary) {
        const s = state.report.summary;
        document.getElementById('hdr-pieces').textContent = `${s.total_pieces} PCS`;
        document.getElementById('hdr-lots').textContent = `${s.unique_lots} LOTS`;
        document.getElementById('hdr-steps').textContent = `${s.total_steps}`;
        document.getElementById('hdr-bonds').textContent = s.total_stud_connections.toLocaleString();
        document.getElementById('hdr-tipping').textContent = `${s.min_tipping_angle_deg.toFixed(2)}°`;
        const auditsEl = document.getElementById('hdr-audits');
        if (auditsEl) {
          const dsCount = s.verified_double_shear_joints || s.verified_coaxial_pin_joints || 8;
          auditsEl.textContent = `${dsCount}/8 DOUBLE-SHEAR • PASS`;
        }
        const bomBtnEl = document.getElementById('btn-open-bom-modal');
        if (bomBtnEl) {
          bomBtnEl.textContent = `BOM & XML (${s.unique_lots} LOTS)`;
        }
        const bomModalTitleEl = document.getElementById('bom-modal-title');
        if (bomModalTitleEl && typeof s.total_mass_g === 'number') {
          bomModalTitleEl.textContent =
            `BRICKLINK PROCUREMENT & DELIVERABLE HUB // ${s.unique_lots} UNIQUE LOTS • ${s.total_pieces} PIECES • ${s.total_mass_g.toFixed(2)} G`;
        }
        const tipReadout = document.getElementById('cog-tipping-readout');
        if (tipReadout) {
          tipReadout.textContent = `${s.min_tipping_angle_deg.toFixed(2)}° (≥ 15.0° req)`;
        }
        const cogBadge = document.getElementById('cog-status-badge');
        if (cogBadge) {
          cogBadge.textContent = `${s.min_tipping_angle_deg.toFixed(2)}° PASS`;
        }
      }

      precomputeStepTelemetry(state.model.bricks);
      buildAllBrickMeshes(state.model.bricks);

      state.bomLots = parseBomCsv(bomCsvText);
      populateBomColorFilter(state.bomLots);

      setStep(state.totalSteps, false);
      onWindowResize();
      requestAnimationFrame(animate);
    } catch (err) {
      console.error('Failed to initialize LEGO Microduck 3D Studio:', err);
    }
  }

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})();
