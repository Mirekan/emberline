import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { sceneParamsFor, stageState } from "./stageState";

const TERRAIN_VERTEX = /* glsl */ `
uniform float uTime;
uniform float uHeat;
varying float vHeight;
varying vec3 vWorld;

void main() {
  vec3 p = position;
  float t = uTime * 0.12;
  float broad = sin(p.x * 0.14 + t) * cos(p.y * 0.12 - t * 0.7);
  float ridge = sin((p.x + p.y) * 0.29 + t * 1.4)
              * cos((p.x - p.y) * 0.19 - t);
  float detail = sin(p.x * 0.53 + p.y * 0.4 + t * 1.8) * 0.22;
  float centerCalm = smoothstep(0.0, 25.0, abs(p.x));
  float height = (broad * 1.7 + ridge * 0.65 + detail) * (0.32 + uHeat * 1.6);
  p.z = height * mix(0.4, 1.0, centerCalm);
  vHeight = p.z;
  vec4 world = modelMatrix * vec4(p, 1.0);
  vWorld = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

const TERRAIN_FRAGMENT = /* glsl */ `
precision highp float;
uniform float uHeat;
uniform float uCool;
uniform float uOpacity;
uniform vec3 uBase;
uniform vec3 uEmber;
uniform vec3 uCalm;
uniform vec3 uFog;
varying float vHeight;
varying vec3 vWorld;

void main() {
  float level = clamp((vHeight + 2.0) / 5.5, 0.0, 1.0);
  vec2 gridPos = vWorld.xz * 0.45;
  vec2 grid = abs(fract(gridPos) - 0.5) / fwidth(gridPos);
  float line = 1.0 - min(min(grid.x, grid.y), 1.0);
  vec3 hot = mix(uEmber, uCalm, uCool);
  vec3 color = mix(uBase, hot * 0.38, pow(level, 1.6) * 0.9);
  float peak = smoothstep(0.38, 0.92, level);
  color += hot * peak * (0.42 + uHeat * 0.9);
  color += vec3(0.16, 0.19, 0.17) * line * (0.28 + level * 0.45);
  float distanceToCamera = length(vWorld - cameraPosition);
  float fog = clamp(1.0 - exp(-distanceToCamera * 0.026), 0.0, 1.0);
  color = mix(color, uFog, fog);
  gl_FragColor = vec4(color, uOpacity);
}
`;

const EMBER_VERTEX = /* glsl */ `
uniform float uTime;
uniform float uHeat;
uniform float uHeight;
uniform float uPixelRatio;
attribute vec3 aSeed;
varying float vLife;
varying float vDepth;

void main() {
  float speed = 0.55 + aSeed.x * 1.5;
  float life = fract(aSeed.y + uTime * 0.028 * speed * (0.45 + uHeat * 1.75));
  vec3 p = position;
  p.y = life * uHeight;
  float angle = aSeed.z * 6.28318 + uTime * (0.18 + aSeed.x * 0.28);
  float sway = 0.55 + uHeat * 0.9;
  p.x += sin(angle) * sway + sin(uTime * 0.4 + aSeed.y * 12.0) * 0.7;
  p.z += cos(angle * 0.9) * sway * 0.7 + cos(uTime * 0.5 + aSeed.x * 9.0) * 0.6;
  vLife = life;
  vec4 viewPosition = modelViewMatrix * vec4(p, 1.0);
  vDepth = -viewPosition.z;
  gl_Position = projectionMatrix * viewPosition;
  float size = (0.2 + aSeed.x * 0.36) * (1.0 + uHeat * 0.7);
  gl_PointSize = min(size * uPixelRatio * (240.0 / max(vDepth, 1.0)), 40.0 * uPixelRatio);
}
`;

const EMBER_FRAGMENT = /* glsl */ `
precision highp float;
uniform float uHeat;
uniform float uCool;
uniform float uIntensity;
varying float vLife;
varying float vDepth;

void main() {
  float distanceFromCenter = length(gl_PointCoord - 0.5);
  float alpha = smoothstep(0.5, 0.05, distanceFromCenter);
  float fade = smoothstep(0.0, 0.16, vLife) * (1.0 - smoothstep(0.55, 1.0, vLife));
  fade *= smoothstep(2.5, 6.0, vDepth);
  vec3 ember = mix(vec3(1.0, 0.616, 0.298), vec3(0.906, 0.694, 0.518), vLife);
  vec3 calm = mix(vec3(0.615, 0.855, 0.72), vec3(0.545, 0.78, 0.65), vLife);
  vec3 color = mix(ember, calm, uCool);
  float opacity = alpha * fade * (0.42 + uHeat) * (1.0 - uCool * 0.6) * uIntensity;
  if (opacity < 0.004) discard;
  gl_FragColor = vec4(color, opacity);
}
`;

function SceneContent({ theme }: { theme: "light" | "dark" }) {
  const terrainMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: TERRAIN_VERTEX,
        fragmentShader: TERRAIN_FRAGMENT,
        transparent: true,
        uniforms: {
          uTime: { value: 0 },
          uHeat: { value: 0.42 },
          uCool: { value: 0 },
          uOpacity: { value: theme === "dark" ? 0.78 : 0.18 },
          uBase: { value: new THREE.Color("#0b100e") },
          uEmber: { value: new THREE.Color("#fa773f") },
          uCalm: { value: new THREE.Color("#6fc496") },
          uFog: { value: new THREE.Color("#0a0d0c") },
        },
      }),
    [],
  );
  const emberMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: EMBER_VERTEX,
        fragmentShader: EMBER_FRAGMENT,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          uTime: { value: 0 },
          uHeat: { value: 0.42 },
          uCool: { value: 0 },
          uHeight: { value: 12 },
          uPixelRatio: { value: Math.min(window.devicePixelRatio || 1, 1.5) },
          uIntensity: { value: theme === "dark" ? 1 : 0.34 },
        },
      }),
    [],
  );
  const terrainGeometry = useMemo(() => new THREE.PlaneGeometry(120, 78, 168, 108), []);
  const emberGeometry = useMemo(() => {
    const count = 2300;
    const positions = new Float32Array(count * 3);
    const seeds = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const radius = Math.sqrt(Math.random());
      positions[i * 3] = (Math.random() > 0.5 ? 1 : -1) * radius * 32;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = -30 + Math.random() * 80;
      seeds[i * 3] = Math.random();
      seeds[i * 3 + 1] = Math.random();
      seeds[i * 3 + 2] = Math.random();
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aSeed", new THREE.BufferAttribute(seeds, 3));
    return geometry;
  }, []);
  const lookTarget = useRef(new THREE.Vector3(0, 1.6, -6));

  useEffect(() => {
    terrainMaterial.uniforms.uOpacity.value = theme === "dark" ? 0.78 : 0.18;
    emberMaterial.uniforms.uIntensity.value = theme === "dark" ? 1 : 0.34;
  }, [emberMaterial, terrainMaterial, theme]);

  useEffect(
    () => () => {
      terrainGeometry.dispose();
      emberGeometry.dispose();
      terrainMaterial.dispose();
      emberMaterial.dispose();
    },
    [emberGeometry, emberMaterial, terrainGeometry, terrainMaterial],
  );

  useFrame((state, rawDelta) => {
    const delta = Math.min(rawDelta, 0.05);
    const stage = stageState;
    stage.smoothProgress += (stage.progress - stage.smoothProgress) * Math.min(1, delta * 3);
    stage.smoothPointerX += (stage.pointerX - stage.smoothPointerX) * Math.min(1, delta * 2);
    stage.smoothPointerY += (stage.pointerY - stage.smoothPointerY) * Math.min(1, delta * 2);

    const params = sceneParamsFor(stage.reducedMotion ? 0 : stage.smoothProgress);
    const time = stage.reducedMotion ? 9 : state.clock.elapsedTime;
    terrainMaterial.uniforms.uTime.value = time;
    terrainMaterial.uniforms.uHeat.value = params.heat;
    terrainMaterial.uniforms.uCool.value = params.cool;
    emberMaterial.uniforms.uTime.value = time;
    emberMaterial.uniforms.uHeat.value = params.heat;
    emberMaterial.uniforms.uCool.value = params.cool;
    emberMaterial.uniforms.uHeight.value = 9 + params.heat * 3.5;

    const pointerX = stage.reducedMotion ? 0 : stage.smoothPointerX;
    const pointerY = stage.reducedMotion ? 0 : stage.smoothPointerY;
    const camera = state.camera;
    const follow = Math.min(1, delta * 2.2);
    camera.position.x += (pointerX * 2.4 - camera.position.x) * follow;
    camera.position.y += (params.camY - pointerY * 1.2 - camera.position.y) * follow;
    camera.position.z += (params.camZ - camera.position.z) * follow;
    lookTarget.current.set(pointerX * 1.2, 1.6 - pointerY * 0.5, -6);
    camera.lookAt(lookTarget.current);
  });

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <primitive object={terrainGeometry} attach="geometry" />
        <primitive object={terrainMaterial} attach="material" />
      </mesh>
      <points>
        <primitive object={emberGeometry} attach="geometry" />
        <primitive object={emberMaterial} attach="material" />
      </points>
    </group>
  );
}

export default function EmberStage({ theme }: { theme: "light" | "dark" }) {
  useEffect(() => {
    const onPointerMove = (event: PointerEvent) => {
      stageState.pointerX = (event.clientX / window.innerWidth) * 2 - 1;
      stageState.pointerY = (event.clientY / window.innerHeight) * 2 - 1;
    };
    const resetPointer = () => {
      stageState.pointerX = 0;
      stageState.pointerY = 0;
    };
    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const syncMotionPreference = () => {
      stageState.reducedMotion = motionPreference.matches;
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerleave", resetPointer);
    motionPreference.addEventListener("change", syncMotionPreference);
    syncMotionPreference();

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", resetPointer);
      motionPreference.removeEventListener("change", syncMotionPreference);
    };
  }, []);

  return (
    <div className="ember-stage" aria-hidden="true">
      <Canvas
        dpr={[1, 1.5]}
        camera={{ fov: 42, near: 0.1, far: 150, position: [0, 9, 30] }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        fallback={<div className="ember-stage-fallback" />}
        onCreated={({ gl }) => gl.setClearColor(0x000000, 0)}
      >
        <SceneContent theme={theme} />
      </Canvas>
    </div>
  );
}
