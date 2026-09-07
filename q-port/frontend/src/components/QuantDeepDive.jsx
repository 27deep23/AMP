import React, { useState } from 'react';
import { Binary, Cpu, Sliders, ShieldCheck } from 'lucide-react';

export default function QuantDeepDive({ lastOptimizationResult }) {
  const [nQubits, setNQubits] = useState(6);
  const [pLayers, setPLayers] = useState(1);
  const [shots, setShots] = useState(1024);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '0.8rem', borderRadius: '12px' }}>
            <Binary size={32} color="#a5b4fc" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700 }}>
              Quant & Research Deep-Dive
            </h2>
            <p style={{ margin: '0.4rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
              Inspect low-level QUBO matrix coefficients, QAOA circuit parameters, Qiskit Aer simulator settings, and Ising spin transformations.
            </p>
          </div>
        </div>
      </div>

      {/* Grid of Quant Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
        {/* QAOA Parameters */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} color="#6366f1" /> QAOA Circuit Configuration
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>QAOA Layers (p): <strong>{pLayers}</strong></label>
              <input type="range" min="1" max="4" value={pLayers} onChange={(e) => setPLayers(e.target.value)} style={{ width: '100%', accentColor: '#6366f1' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>Measurement Shots: <strong>{shots}</strong></label>
              <input type="range" min="256" max="4096" step="256" value={shots} onChange={(e) => setShots(e.target.value)} style={{ width: '100%', accentColor: '#06b6d4' }} />
            </div>

            <div style={{ padding: '0.8rem', background: 'rgba(10, 12, 22, 0.6)', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.2)', fontSize: '0.8rem', color: '#94a3b8' }}>
              <div>• Hardware Target: <strong>Qiskit Aer (AerSimulator)</strong></div>
              <div>• Classical Optimizer: <strong>COBYLA</strong></div>
              <div>• Max Qubit Limit: <strong>24 Qubits (Local CPU)</strong></div>
            </div>
          </div>
        </div>

        {/* Mathematical Formulation */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={18} color="#38bdf8" /> QUBO & Ising Formulation
          </h3>

          <div style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            <p><strong>QUBO Cost Function</strong>:</p>
            <code style={{ background: '#0a0c16', padding: '0.4rem 0.6rem', borderRadius: '6px', color: '#34d399', display: 'block', marginBottom: '0.8rem' }}>
              C(x) = -(μ^T x / K - λ x^T Σ x / K^2) + A (Σ x_i - K)^2 + B Σ (Σ x_i - K_s)^2
            </code>

            <p><strong>Ising Transformation</strong>:</p>
            <code style={{ background: '#0a0c16', padding: '0.4rem 0.6rem', borderRadius: '6px', color: '#38bdf8', display: 'block' }}>
              x_i = (1 - Z_i) / 2  ⇒  H_C = Σ h_i Z_i + Σ J_ij Z_i Z_j + offset
            </code>
          </div>
        </div>
      </div>

      {/* Raw Optimization Dump */}
      {lastOptimizationResult && (
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Raw API Execution Response Dump</h3>
          <pre style={{ background: '#0a0c16', padding: '1rem', borderRadius: '10px', overflowX: 'auto', color: '#a5b4fc', fontSize: '0.8rem' }}>
            {JSON.stringify(lastOptimizationResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
