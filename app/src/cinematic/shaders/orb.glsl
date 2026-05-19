// AI Orb Vertex Shader
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
varying float vDistance;

uniform float uTime;
uniform float uIntensity;
uniform vec3 uCursor;

void main() {
  vUv = uv;
  vNormal = normalize(normalMatrix * normal);
  vPosition = position;
  vDistance = distance(position, vec3(0.0));
  
  vec3 pos = position;
  
  // Pulsing deformation
  float pulse = sin(uTime * 2.0 + vDistance * 0.5) * 0.1;
  pos += normal * pulse * uIntensity;
  
  // Cursor interaction
  float cursorInfluence = 1.0 - smoothstep(0.0, 2.0, distance(position, uCursor));
  pos += normal * cursorInfluence * 0.2;
  
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
