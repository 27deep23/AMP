import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Trophy, Zap, Target, BarChart2 } from 'lucide-react';

export default function BenchmarkView() {
  const [nAssets, setNAssets] = useState(15);
  const [kTarget, setKTarget] = useState(5);
  const [loading, setLoading] = useState(false);
  const [benchData, setBenchData] = useState(null);

  const runBenchmark = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          n_assets: parseInt(nAssets),
          k_target: parseInt(kTarget),
          risk_aversion: 1.0,
          max_weight: 0.35,
          max_sector_weight: 0.50,
          run_qaoa: true,
          run_exact: true,
          force_bundled: true
        })
      });
      const data = await res.json();
      setBenchData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runBenchmark();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700 }}>
              Quantum vs Classical Optimization Benchmark
            </h2>
            <p style={{ margin: '0.4rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
              Compare how the QAOA Quantum Simulator performs against classical heuristics (Greedy, SA) and exact global math search.
            </p>
          </div>
          <button className="btn-primary" onClick={runBenchmark} disabled={loading}>
            <Trophy size={18} />
            {loading ? 'Running Solvers...' : '🚀 Run Benchmark Test'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1.2rem', paddingTop: '1.2rem', borderTop: '1px solid rgba(99, 102, 241, 0.15)' }}>
          <div>
            <label style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Universe Size (N): </label>
            <select
              value={nAssets}
              onChange={(e) => setNAssets(e.target.value)}
              style={{ background: '#121628', color: '#fff', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '6px', padding: '0.3rem 0.6rem', marginLeft: '0.4rem' }}
            >
              <option value="10">10 Assets</option>
              <option value="15">15 Assets</option>
              <option value="20">20 Assets</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Target Portfolio Size (K): </label>
            <select
              value={kTarget}
              onChange={(e) => setKTarget(e.target.value)}
              style={{ background: '#121628', color: '#fff', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '6px', padding: '0.3rem 0.6rem', marginLeft: '0.4rem' }}
            >
              <option value="3">3 Stocks</option>
              <option value="5">5 Stocks</option>
              <option value="7">7 Stocks</option>
            </select>
          </div>
        </div>
      </div>

      {benchData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Baseline Reference Pill */}
          <div style={{ padding: '0.8rem 1.2rem', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '10px', color: '#38bdf8', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Target size={18} />
            <span>Benchmark Reference Baseline: <strong>{benchData.info.reference_baseline_name}</strong></span>
          </div>

          {/* Charts Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
            {/* Sharpe Ratio Comparison */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Portfolio Efficiency (Sharpe Ratio)</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={benchData.results}>
                    <XAxis dataKey="Method" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: '#121628', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px' }} />
                    <Bar dataKey="Sharpe Ratio" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Precision Match / Optimality Gap */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Optimality Difference vs Global Best (%)</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={benchData.results}>
                    <XAxis dataKey="Method" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: '#121628', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px' }} />
                    <Bar dataKey="Optimality Gap (%)" fill="#ec4899" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Results Comparison Table */}
          <div className="glass-card" style={{ padding: '1.5rem', overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Comprehensive Solver Comparison</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.2)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem' }}>Algorithm Method</th>
                  <th style={{ padding: '0.75rem' }}>Expected Return (%)</th>
                  <th style={{ padding: '0.75rem' }}>Annual Volatility (%)</th>
                  <th style={{ padding: '0.75rem' }}>Sharpe Ratio</th>
                  <th style={{ padding: '0.75rem' }}>Difference vs Best (%)</th>
                  <th style={{ padding: '0.75rem' }}>Compute Time</th>
                </tr>
              </thead>
              <tbody>
                {benchData.results.map((row) => (
                  <tr key={row.Method} style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.08)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: row.Method.includes('QAOA') ? '#38bdf8' : '#f8fafc' }}>{row.Method}</td>
                    <td style={{ padding: '0.75rem', color: '#34d399', fontWeight: 600 }}>{row['Expected Return (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem', color: '#f59e0b' }}>{row['Annual Volatility (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700 }}>{row['Sharpe Ratio'].toFixed(2)}</td>
                    <td style={{ padding: '0.75rem' }}>{row['Optimality Gap (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem', color: '#a5b4fc' }}>{row['Runtime (s)'].toFixed(4)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
