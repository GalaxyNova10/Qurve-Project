// Energy Field Vertex Shader
varying vec2 vUv;
varying vec3 vPosition;
varying float vEnergy;

uniform float uTime;
uniform float uIntensity;
uniform vec2 uScrollVelocity;

void main() {
  vUv = uv;
  vPosition = position;
  
  // Energy calculation based on position and time
  vEnergy = sin(length(position) * 2.0 - uTime * 3.0) * 0.5 + 0.5;
  vEnergy *= uIntensity;
  
  // Scroll velocity influence
  vec2 velocityDistortion = uScrollVelocity * 0.1;
  vec3 pos = position;
  pos.x += sin(uTime + position.y) * velocityDistortion.x;
  pos.y += cos(uTime + position.x) * velocityDistortion.y;
  
  // Turbulent movement
  float turbulence = sin(uTime * 2.0 + position.x * 5.0) * cos(uTime * 1.5 + position.y * 3.0);
  pos += normal * turbulence * 0.05 * uIntensity;
  
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
