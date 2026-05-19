// Scroll Velocity Distortion Shader
varying vec2 vUv;
varying vec3 vPosition;

uniform float uTime;
uniform vec2 uScrollVelocity;
uniform float uIntensity;
uniform sampler2D uNoiseTexture;

void main() {
  vUv = uv;
  vPosition = position;
  
  vec3 pos = position;
  
  // Scroll velocity based distortion
  float velocityMagnitude = length(uScrollVelocity);
  vec2 velocityDirection = normalize(uScrollVelocity);
  
  // Apply distortion based on scroll direction and speed
  pos.x += sin(uTime * 3.0 + position.y * 2.0) * velocityDirection.x * velocityMagnitude * 0.2;
  pos.y += cos(uTime * 2.5 + position.x * 2.0) * velocityDirection.y * velocityMagnitude * 0.2;
  
  // Noise-based distortion
  vec2 noiseUv = vUv * 3.0 + uTime * 0.5;
  vec3 noise = texture2D(uNoiseTexture, noiseUv).rgb;
  
  pos.x += (noise.r - 0.5) * velocityMagnitude * 0.1 * uIntensity;
  pos.y += (noise.g - 0.5) * velocityMagnitude * 0.1 * uIntensity;
  
  // Wave distortion
  float wave = sin(uTime * 4.0 + length(position) * 5.0) * 0.05;
  pos += normal * wave * uIntensity;
  
  // Stretch effect based on velocity
  float stretch = 1.0 + velocityMagnitude * 0.3;
  pos.x *= 1.0 + (velocityDirection.x * stretch - 1.0) * 0.1;
  pos.y *= 1.0 + (velocityDirection.y * stretch - 1.0) * 0.1;
  
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
