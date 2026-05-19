import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, CheckCircle2, Info, Download, Activity, Play, Pause } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import EnergyLandscape3D from '../components/EnergyLandscape3D';
import { useGPUTelemetry } from '@/hooks/useGPUTelemetry';

// Enhanced GPU detection using WebGL debug extension
const getCurrentDeviceGPUFromWebGL = () => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl') as WebGLRenderingContext;
    
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        const renderer = (debugInfo as any).getParameter((gl as any).UNMASKED_RENDERER_WEBGL);
        console.log('GPU Renderer (WebGL Debug):', renderer);
        
        if (renderer) {
          // Enhanced GPU patterns
          const gpuPatterns = [
            /NVIDIA.*GeForce.*RTX.*(\d+)/gi,
            /NVIDIA.*GeForce.*GTX.*(\d+)/gi,
            /NVIDIA.*GeForce.*(\d+)/gi,
            /AMD.*Radeon.*RX.*(\d+)/gi,
            /AMD.*Radeon.*(\d+)/gi,
            /Intel.*HD.*Graphics/gi,
            /Intel.*UHD.*Graphics/gi,
            /Intel.*Iris.*Graphics/gi,
            /Intel.*Arc.*Graphics/gi,
            /Apple.*M\d+/gi,
            /M\d+.*Pro/gi
          ];
          
          for (const pattern of gpuPatterns) {
            const match = renderer.match(pattern);
            if (match) {
              console.log('GPU Pattern Matched (WebGL Debug):', pattern, '->', match[0] || match[1]);
              return match[0] || match[1] || 'Unknown GPU';
            }
          }
          
          const fallbackGPU = renderer.split('(')[0] || 'Unknown GPU';
          console.log('GPU Fallback (WebGL Debug):', fallbackGPU);
          return fallbackGPU;
        }
      }
    }
  } catch (error) {
    console.error('GPU detection error:', error);
    return 'Unknown GPU';
  }
};

// Main GPU detection function
const detectCurrentGPU = () => {
  console.log('Starting comprehensive GPU detection...');  
  // Try WebGL debug extension first (most accurate)
  const webglGPU = getCurrentDeviceGPUFromWebGL();
  if (webglGPU !== 'Unknown GPU') {
    console.log('Using WebGL debug detection:', webglGPU);
    return webglGPU;
  }
  
  // Try User Agent detection
  const userAgentGPU = getCurrentDeviceGPUFromUserAgent();
  if (userAgentGPU !== 'Unknown GPU') {
    console.log('Using User Agent detection:', userAgentGPU);
    return userAgentGPU;
  }
  
  // Try basic WebGL detection
  const basicWebGLGPU = getCurrentDeviceGPU();
  if (basicWebGLGPU !== 'Unknown GPU') {
    console.log('Using basic WebGL detection:', basicWebGLGPU);
    return basicWebGLGPU;
  }
  
  console.log('All detection methods failed, using fallback');
  return 'Unknown GPU';
};

// Function to detect current device GPU
const getCurrentDeviceGPU = () => {
  try {
    // Try to get GPU info from browser APIs
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl') as WebGLRenderingContext;
    
    if (gl) {
      // Try to get renderer info directly
      const renderer = gl.getParameter((gl as WebGLRenderingContext).RENDERER);
      if (renderer) {
        console.log('GPU Renderer:', renderer); // Debug log
        
        // Extract GPU info from renderer string
        if (renderer) {
          // Common GPU patterns to detect
          const gpuPatterns = [
            /NVIDIA.*GeForce.*RTX.*(\d+)/gi,
            /NVIDIA.*GeForce.*GTX.*(\d+)/gi,
            /NVIDIA.*GeForce.*(\d+)/gi,
            /AMD.*Radeon.*RX.*(\d+)/gi,
            /AMD.*Radeon.*(\d+)/gi,
            /Intel.*HD.*Graphics/gi,
            /Intel.*UHD.*Graphics/gi,
            /Intel.*Iris.*Graphics/gi,
            /Intel.*Arc.*Graphics/gi,
            /Apple.*M\d+/gi,
            /M\d+.*Pro/gi
          ];
        
          for (const pattern of gpuPatterns) {
            const match = renderer.match(pattern);
            if (match) {
              console.log('GPU Pattern Matched:', pattern, '->', match[0] || match[1]);
              return match[0] || match[1] || 'Unknown GPU';
            }
          }
        
          // Fallback to renderer string if no pattern matches
          const fallbackGPU = renderer.split('(')[0] || 'Unknown GPU';
          console.log('GPU Fallback:', fallbackGPU); // Debug log
          return fallbackGPU;
        }
        const fallbackGPU = renderer.split('(')[0] || 'Unknown GPU';
        console.log('GPU Fallback:', fallbackGPU); // Debug log
        return fallbackGPU;
      }
    }
  } catch (error) {
    console.error('GPU detection error:', error);
    return 'Unknown GPU';
  }
};

// Alternative GPU detection using User Agent
const getCurrentDeviceGPUFromUserAgent = () => {
  try {
    const userAgent = navigator.userAgent;
    console.log('User Agent:', userAgent);
    
    // Common GPU patterns in User Agent
    const gpuPatterns = [
      /NVIDIA.*GeForce.*RTX.*(\d+)/gi,
      /NVIDIA.*GeForce.*GTX.*(\d+)/gi,
      /NVIDIA.*GeForce.*(\d+)/gi,
      /AMD.*Radeon.*RX.*(\d+)/gi,
      /AMD.*Radeon.*(\d+)/gi,
      /Intel.*HD.*Graphics/gi,
      /Intel.*UHD.*Graphics/gi,
      /Intel.*Iris.*Graphics/gi,
      /Intel.*Arc.*Graphics/gi,
      /Apple.*M\d+/gi,
      /M\d+.*Pro/gi
    ];
    
    for (const pattern of gpuPatterns) {
      const match = userAgent.match(pattern);
      if (match) {
        console.log('GPU Pattern Matched (User Agent):', pattern, '->', match[0] || match[1]);
        return match[0] || match[1] || 'Unknown GPU';
      }
    }
    
    const fallbackGPU = 'Unknown GPU';
    console.log('GPU Fallback (User Agent):', fallbackGPU);
    return fallbackGPU;
  } catch (error) {
    console.error('GPU detection error:', error);
    return 'Unknown GPU';
  }
};

interface GPUMetrics {
  utilization: number;
  memory: number;
  temperature: number;
  power: number;
  energy: number;
}

export default function GPUTelemetryPage() {
  const { metrics: liveMetrics, isConnected, history: liveHistory } = useGPUTelemetry();
  
  // Get current device GPU
  const currentDeviceGPU = detectCurrentGPU();
  
  // Debug: Log the detected GPU
  console.log('Detected GPU:', currentDeviceGPU);
  console.log('Backend GPU:', liveMetrics?.gpu_name);
  
  const [metrics, setMetrics] = useState<GPUMetrics>({
    utilization: 0,
    memory: 0,
    temperature: 0,
    power: 0,
    energy: 1.5,
  });

  const [history, setHistory] = useState<any[]>([]);
  const [bifurcationData, setBifurcationData] = useState<any[]>([]);
  const [convergenceProgress, setConvergenceProgress] = useState(0);
  const [iteration, setIteration] = useState(0);
  const [isRunning, setIsRunning] = useState(true);

  // References to keep state fresh inside the requestAnimationFrame loop
  const isRunningRef = useRef(isRunning);
  useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

  useEffect(() => {
    if (!liveMetrics) return;
    setMetrics(prev => ({
      utilization: liveMetrics.utilization,
      memory: liveMetrics.vram_used_mb / 1024,
      temperature: liveMetrics.temperature_c,
      power: liveMetrics.power_draw_w,
      energy: prev.energy,
    }));
  }, [liveMetrics]);

  useEffect(() => {
    if (liveHistory.length === 0) return;
    setHistory(liveHistory.map((item, index) => ({
      time: index - liveHistory.length,
      utilization: item.utilization,
      memory: item.vram_total_mb > 0 ? (item.vram_used_mb / item.vram_total_mb) * 100 : 0,
      power: item.power_draw_w,
      temperature: item.temperature_c,
    })));
  }, [liveHistory]);

  // Continuous render/telemetry loop
  useEffect(() => {
    let animationFrameId: number;
    let lastUpdate = Date.now();
    let currentIteration = 12000;
    
    // Initial data
    const initialHistory = Array.from({ length: 60 }, (_, i) => ({
      time: -60 + i,
      utilization: 40 + Math.sin(i * 0.2) * 8,
      memory: 20 + Math.cos(i * 0.13) * 4,
      power: 40 + Math.sin(i * 0.17) * 10,
      temperature: 45 + Math.cos(i * 0.1) * 3,
    }));
    setHistory(initialHistory);

    const initialBifurcation = Array.from({ length: 50 }, (_, i) => {
      const t = i / 50;
      return {
        iteration: i * 200,
        energy: 1.5 * Math.exp(-t * 4) + (Math.sin(i) * 0.03) * (1 - t),
      };
    });
    setBifurcationData(initialBifurcation);
    
    const loop = () => {
      if (!isRunningRef.current) {
        animationFrameId = requestAnimationFrame(loop);
        return;
      }

      const now = Date.now();
      if (now - lastUpdate > 200) { 
        const timeFactor = now / 1000;
        
        if (!liveMetrics) {
          setMetrics(prev => {
            const newUtil = Math.max(0, Math.min(100, 45 + Math.sin(timeFactor) * 8));
            const newMem = Math.max(0, Math.min(24, 4 + Math.sin(timeFactor * 0.5) * 0.5));
            const newTemp = Math.max(0, Math.min(90, 42 + Math.sin(timeFactor * 0.2) * 2));
            const newPower = Math.max(0, Math.min(450, 65 + (newUtil / 100) * 35));
            const newEnergy = Math.max(-2, prev.energy - 0.005 + Math.sin(timeFactor) * 0.002);
            const newMetrics = { utilization: newUtil, memory: newMem, temperature: newTemp, power: newPower, energy: newEnergy };
            setHistory(prevHist => {
              const nextHist = [...prevHist.slice(1), {
                time: 0,
                utilization: newMetrics.utilization,
                memory: (newMetrics.memory / 24) * 100,
                power: (newMetrics.power / 450) * 100,
                temperature: (newMetrics.temperature / 100) * 100,
              }];
              return nextHist.map((d, i) => ({ ...d, time: i - 60 }));
            });
            return newMetrics;
          });
        }

        currentIteration += 15;
        setIteration(currentIteration);
        setConvergenceProgress(Math.min(100, (currentIteration / 15000) * 100));
        
        if (currentIteration % 200 < 15) {
           setBifurcationData(prev => {
             return [...prev.slice(1), {
               iteration: currentIteration,
               energy: Math.max(-2, 1.5 * Math.exp(-(currentIteration / 15000) * 4) + Math.sin(currentIteration / 100) * 0.02),
             }];
           });
        }
        
        lastUpdate = now;
      }
      animationFrameId = requestAnimationFrame(loop);
    };
    
    loop();
    return () => cancelAnimationFrame(animationFrameId);
  }, [liveMetrics]);

  return (
    <div className="flex flex-col h-full gap-6 bg-[#0B1220] text-[#E5E7EB] -m-8 p-8 font-sans">
      {/* Top Header matching image */}
      <div className="flex justify-between items-start border-b border-[#1F2937] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider flex items-center gap-2">
            <Activity className="text-[#10B981] w-6 h-6" /> 
            HIDDEN MARKOV REGIME DETECTION
          </h1>
          <p className="text-[#94A3B8] text-sm uppercase tracking-widest mt-1">GPU Telemetry Analysis Suite</p>
        </div>
        <div className="flex gap-8 items-center">
          <div className="flex bg-[#111827] rounded-md border border-[#1F2937] p-1">
            <button 
              onClick={() => setIsRunning(true)} 
              className={`px-3 py-1 text-xs font-semibold rounded-sm flex items-center gap-1 transition-colors ${isRunning ? 'bg-[#10B981] text-[#0B1220]' : 'text-[#94A3B8] hover:text-white'}`}
            >
              <Play className="w-3 h-3" /> Start
            </button>
            <button 
              onClick={() => setIsRunning(false)} 
              className={`px-3 py-1 text-xs font-semibold rounded-sm flex items-center gap-1 transition-colors ${!isRunning ? 'bg-[#F59E0B] text-[#0B1220]' : 'text-[#94A3B8] hover:text-white'}`}
            >
              <Pause className="w-3 h-3" /> Pause
            </button>
          </div>
          <div>
            <p className="text-[#64748B] text-xs font-semibold mb-1">GPU MODEL</p>
            <p className="text-white text-sm font-mono">{currentDeviceGPU || liveMetrics?.gpu_name || 'Telemetry unavailable'}</p>
          </div>
          <div>
            <p className="text-[#64748B] text-xs font-semibold mb-1">SAMPLING RATE</p>
            <p className="text-white text-sm font-mono">200 ms</p>
          </div>
          <div>
            <p className="text-[#64748B] text-xs font-semibold mb-1">UPTIME</p>
            <p className="text-white text-sm font-mono">2d 14h 32m</p>
          </div>
          <div>
            <p className="text-[#64748B] text-xs font-semibold mb-1">DATA STREAM</p>
            <p className={`text-sm font-mono flex items-center gap-2 ${isRunning ? 'text-[#10B981]' : 'text-[#F59E0B]'}`}>
              <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-[#10B981] animate-pulse' : 'bg-[#F59E0B]'}`}></span>
              {isConnected ? (isRunning ? 'LIVE' : 'PAUSED') : 'OFFLINE'}
            </p>
          </div>
        </div>
      </div>

      {/* 12-Column Main Grid */}
      <div className="grid lg:grid-cols-12 gap-6 items-stretch flex-1">

        {/* Left Column (col-span-3) */}
        <div className="lg:col-span-3 flex flex-col">
          <Card className="bg-[#111827] border-[#1F2937] flex-1 rounded-xl shadow-lg overflow-hidden">
            <CardHeader className="pb-2 border-b border-[#1F2937]/50 bg-[#0d1117]">
              <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold">System Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">GPU Utilization</span>
                <span className="text-[#10B981] font-mono font-medium">{metrics.utilization.toFixed(0)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">Memory Usage</span>
                <span className="text-[#0ea5e9] font-mono font-medium">{metrics.memory.toFixed(1)} GB <span className="text-[#64748B] text-xs">/ {(liveMetrics ? liveMetrics.vram_total_mb / 1024 : 0).toFixed(1)} GB</span></span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">GPU Temperature</span>
                <span className="text-[#ef4444] font-mono font-medium">{metrics.temperature.toFixed(0)} °C</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">Power Draw</span>
                <span className="text-[#eab308] font-mono font-medium">{metrics.power.toFixed(0)} W</span>
              </div>
              <div className="h-px bg-[#1F2937]/50 my-2"></div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">Core Clock</span>
                <span className="text-[#10B981] font-mono font-medium">2535 MHz</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">Memory Clock</span>
                <span className="text-[#10B981] font-mono font-medium">10502 MHz</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94A3B8] text-sm">Fan Speed</span>
                <span className="text-[#10B981] font-mono font-medium">68%</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Center Column (col-span-6) */}
        <div className="lg:col-span-6 flex flex-col gap-6">
          {/* 3D Energy Landscape */}
          <Card className="bg-[#111827] border-[#1F2937] flex-1 flex flex-col overflow-hidden relative rounded-xl shadow-lg">
              <div className="absolute top-4 left-4 z-10">
                 <h2 className="text-white font-semibold tracking-wider">3D ENERGY LANDSCAPE</h2>
                 <p className="text-[#94A3B8] text-sm">Simulated Bifurcation Convergence Path</p>
                 <div className="flex gap-4 mt-4 text-xs font-medium bg-[#111827]/80 backdrop-blur-sm p-2 rounded-lg border border-[#1F2937]">
                   <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#22c55e]"></span> Stable Regime</span>
                   <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#eab308]"></span> Transitional</span>
                   <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#ef4444]"></span> Unstable Regime</span>
                   <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#0ea5e9]"></span> Convergence Path</span>
                 </div>
              </div>
              
              {/* Legend for axes inside 3D view (overlay) */}
              <div className="absolute bottom-12 left-0 right-0 flex justify-between px-16 text-[#64748B] text-xs pointer-events-none z-10">
                 <span>Memory Bandwidth (GB/s)</span>
                 <span>GPU Utilization (%)</span>
              </div>
              
              {/* 3D Canvas */}
              <div className="flex-1 relative bg-[#0B1220]">
                <EnergyLandscape3D metrics={metrics} convergenceProgress={convergenceProgress} />
              </div>
              
              <div className="bg-[#0d1117] border-t border-[#1F2937] p-2 flex gap-4 text-xs text-[#94A3B8]">
                <button className="flex items-center gap-1 hover:text-white transition-colors"><Activity className="w-3 h-3" /> Rotate</button>
                <button className="flex items-center gap-1 hover:text-white transition-colors"><Info className="w-3 h-3" /> Zoom</button>
              </div>
            </Card>

            {/* Regime Probabilities & Current Regime - nested grid */}
            <div className="grid grid-cols-2 gap-6">
              <Card className="bg-[#111827] border-[#1F2937] rounded-xl shadow-lg">
                <CardHeader className="pb-2 pt-4 px-4 bg-[#0d1117] border-b border-[#1F2937]/50 rounded-t-xl">
                  <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold">Regime Probabilities (HMM)</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pt-3">
                  <div className="h-10 rounded-md overflow-hidden flex w-full border border-[#1F2937]/50 shadow-inner">
                    <div className="bg-[#10B981] flex items-center justify-center text-[#0B1220] font-bold text-sm transition-all duration-300" style={{ width: '62.3%' }}>62.3%</div>
                    <div className="bg-[#F59E0B] flex items-center justify-center text-[#0B1220] font-bold text-sm transition-all duration-300" style={{ width: '24.1%' }}>24.1%</div>
                    <div className="bg-[#EF4444] flex items-center justify-center text-white font-bold text-sm transition-all duration-300" style={{ width: '13.6%' }}>13.6%</div>
                  </div>
                  <div className="flex justify-between mt-3 text-[10px] text-[#94A3B8] uppercase font-semibold tracking-wider">
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#10B981]"></span> Stable</span>
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#F59E0B]"></span> Transitional</span>
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#EF4444]"></span> Unstable</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#111827] border-[#1F2937] rounded-xl shadow-lg">
                 <CardHeader className="pb-1 pt-4 px-4 bg-[#0d1117] border-b border-[#1F2937]/50 rounded-t-xl">
                  <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold">Current Regime</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pt-3">
                  <div className="flex items-center gap-2 text-[#10B981] text-xl font-bold">
                    Stable Regime <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <p className="text-[#64748B] text-xs mt-2 leading-relaxed">
                    System operating within normal parameters. All metrics are within acceptable ranges.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

        {/* Right Column (col-span-3) */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <Card className="bg-[#111827] border-[#1F2937] flex flex-col rounded-xl shadow-lg">
            <CardHeader className="pb-0 pt-4 px-4 flex flex-row justify-between items-center bg-[#0d1117] border-b border-[#1F2937]/50 rounded-t-xl">
              <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold mb-3">Utilization History</CardTitle>
              <select className="bg-[#0B1220] border border-[#1F2937] text-xs text-[#94A3B8] rounded-md px-2 py-1 outline-none mb-3 cursor-pointer hover:border-[#374151] transition-colors">
                <option>Last 60 Seconds</option>
              </select>
            </CardHeader>
            <CardContent className="px-2 pb-2 flex-1 relative pt-4">
              <div className="absolute top-2 right-4 flex gap-3 text-[10px] text-[#94A3B8] z-10 font-medium">
                 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#10B981]"></span> GPU</span>
                 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#0ea5e9]"></span> Mem</span>
                 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#eab308]"></span> Power</span>
                 <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#ef4444]"></span> Temp</span>
              </div>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: '#1F2937', color: '#E5E7EB' }} itemStyle={{ color: '#E5E7EB' }} />
                  <Line type="monotone" dataKey="utilization" stroke="#10B981" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="memory" stroke="#0ea5e9" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="power" stroke="#eab308" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="temperature" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-[#111827] border-[#1F2937] flex flex-col rounded-xl shadow-lg">
            <CardHeader className="pb-0 pt-4 px-4 flex flex-row justify-between items-center bg-[#0d1117] border-b border-[#1F2937]/50 rounded-t-xl">
              <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold mb-3">Simulated Bifurcation</CardTitle>
              <span className={`text-xs flex items-center gap-1 mb-3 ${isRunning ? 'text-[#10B981]' : 'text-[#F59E0B]'}`}>
                Status: {isRunning ? 'Converging' : 'Paused'}
              </span>
            </CardHeader>
            <CardContent className="px-4 pb-2 flex-1 flex pt-4">
              <div className="w-32 flex flex-col justify-center gap-3 text-xs bg-[#0B1220] p-3 rounded-lg border border-[#1F2937]/50 mr-2">
                <div className="flex justify-between items-center"><span className="text-[#64748B]">Iteration</span> <span className="text-white font-mono font-medium">{iteration.toLocaleString()}</span></div>
                <div className="flex justify-between items-center"><span className="text-[#64748B]">Step Size</span> <span className="text-white font-mono font-medium">0.0125</span></div>
                <div className="flex justify-between items-center"><span className="text-[#64748B]">Energy</span> <span className="text-white font-mono font-medium">{metrics.energy.toFixed(3)}</span></div>
                <div className="flex justify-between items-center"><span className="text-[#64748B]">Δ Energy</span> <span className="text-[#10B981] font-mono font-medium">-0.00024</span></div>
                <div className="h-px bg-[#1F2937]/50 my-1"></div>
                <div className="flex justify-between items-center"><span className="text-[#64748B]">Conv.</span> <span className="text-[#10B981] font-mono font-bold">{convergenceProgress.toFixed(1)}%</span></div>
              </div>
              <div className="flex-1">
                 <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={bifurcationData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                    <XAxis dataKey="iteration" stroke="#64748B" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
                    <YAxis stroke="#64748B" fontSize={10} tickLine={false} axisLine={false} domain={[-2, 2]} />
                    <Tooltip contentStyle={{ backgroundColor: '#0B1220', borderColor: '#1F2937', color: '#E5E7EB' }} />
                    <Line type="monotone" dataKey="energy" stroke="#0ea5e9" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Health & Alerts - nested grid */}
          <div className="grid grid-cols-2 gap-6">
            <Card className="bg-[#111827] border-[#1F2937] flex flex-col items-center justify-center relative rounded-xl shadow-lg overflow-hidden">
               <div className="absolute inset-0 bg-gradient-to-b from-[#10B981]/5 to-transparent"></div>
               <CardTitle className="text-[#94A3B8] text-xs uppercase tracking-widest absolute top-3 left-4 font-semibold">Health</CardTitle>
               <div className="relative w-16 h-16 flex items-center justify-center mt-2">
                 <svg className="w-full h-full transform -rotate-90">
                   <circle cx="32" cy="32" r="28" stroke="#1F2937" strokeWidth="6" fill="none" />
                   <circle cx="32" cy="32" r="28" stroke="#10B981" strokeWidth="6" fill="none" strokeDasharray="176" strokeDashoffset={176 - (176 * 86) / 100} className="transition-all duration-1000 ease-out" />
                 </svg>
                 <div className="absolute flex flex-col items-center">
                   <span className="text-white text-lg font-bold">86</span>
                 </div>
               </div>
               <span className="text-[#10B981] font-semibold text-xs mt-1">Good</span>
            </Card>

            <Card className="bg-[#111827] border-[#1F2937] p-3 flex flex-col gap-2 overflow-hidden rounded-xl shadow-lg">
               <div className="flex justify-between items-center mb-1">
                 <span className="text-[#94A3B8] text-xs uppercase tracking-widest font-semibold">Alerts</span>
                 <span className="text-[#0ea5e9] text-[10px] cursor-pointer hover:underline">View All</span>
               </div>
               <div className="flex gap-2 items-start bg-[#10B981]/10 p-1.5 rounded border border-[#10B981]/20">
                 <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981] flex-shrink-0 mt-0.5" />
                 <div>
                   <p className="text-[#E5E7EB] text-[11px] font-medium leading-tight">No critical alerts</p>
                   <p className="text-[#10B981]/80 text-[9px]">System operating normally</p>
                 </div>
               </div>
               <div className="flex gap-2 items-start bg-[#F59E0B]/5 p-1.5 rounded border border-[#F59E0B]/10 opacity-70 hover:opacity-100 transition-opacity cursor-pointer">
                 <AlertTriangle className="w-3.5 h-3.5 text-[#F59E0B] flex-shrink-0 mt-0.5" />
                 <div>
                   <p className="text-[#E5E7EB] text-[11px] font-medium leading-tight">High Memory Usage</p>
                   <p className="text-[#F59E0B]/80 text-[9px]">{metrics.memory.toFixed(1)} GB observed</p>
                 </div>
               </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Isolated Footer */}
      <div className="mt-auto pt-4 border-t border-[#1F2937] flex justify-between items-center text-xs text-[#64748B] font-medium">
        <div className="flex gap-8">
           <span className="flex items-center gap-2 uppercase">DATA STREAM STATUS <span className={`${isConnected ? 'text-[#10B981]' : 'text-[#F59E0B]'} flex items-center gap-1.5`}><span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#10B981]' : 'bg-[#F59E0B]'}`}></span>{isConnected ? 'Live' : 'Offline'}</span></span>
           <span>LAST UPDATED: <span className="text-white font-mono">{liveMetrics?.timestamp || new Date().toISOString()}</span></span>
        </div>
        <div className="flex gap-8">
           <span>DATA POINTS: <span className="text-white font-mono">{history.length}</span></span>
           <span>LATENCY: <span className="text-white font-mono">1 Hz</span></span>
           <button className="flex items-center gap-1.5 hover:text-white transition-colors bg-[#111827] px-3 py-1 rounded border border-[#1F2937]"><Download className="w-3 h-3" /> EXPORT DATA</button>
        </div>
      </div>
    </div>
  );
}
