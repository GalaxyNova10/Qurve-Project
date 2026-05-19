// Volumetric Fog Fragment Shader
varying vec2 vUv;
varying vec3 vPosition;
varying float vDepth;

uniform float uTime;
uniform float uDensity;
uniform float uIntensity;
uniform vec3 uLightPosition;
uniform sampler2D uNoiseTexture;

void main() {
  vec2 uv = vUv;
  
  // Sample noise texture for organic movement
  vec2 noiseUv = uv * 2.0 + uTime * 0.1;
  vec3 noise = texture2D(uNoiseTexture, noiseUv).rgb;
  
  // Calculate distance from light source
  float lightDistance = distance(vPosition, uLightPosition);
  float lightInfluence = 1.0 - smoothstep(0.0, 5.0, lightDistance);
  
  // Volumetric density calculation
  float volumetricDensity = uDensity * (0.5 + noise.r * 0.5);
  volumetricDensity *= uIntensity;
  volumetricDensity *= lightInfluence;
  
  // Depth-based falloff
  float depthFalloff = 1.0 - smoothstep(0.0, 10.0, vDepth);
  volumetricDensity *= depthFalloff;
  
  // Color mixing - purple to cyan gradient
  vec3 fogColor = mix(
    vec3(0.48, 0.23, 0.93), // Purple
    vec3(0.02, 0.73, 0.84), // Cyan
    noise.g
  );
  
  // Final fog color with intensity
  vec3 finalColor = fogColor * volumetricDensity;
  
  // Add subtle glow
  float glow = sin(uTime * 2.0 + vDepth) * 0.1 + 0.9;
  finalColor *= glow;
  
  gl_FragColor = vec4(finalColor, volumetricDensity);
}
