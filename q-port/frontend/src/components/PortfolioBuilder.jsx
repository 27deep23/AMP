import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Rocket, Shield, TrendingUp, DollarSign, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];

export default function PortfolioBuilder({ onOptimizeComplete }) {
  const [capital, setCapital] = useState(1000000);
  const [riskProfile, setRiskProfile] = useState('balanced');
  const [kTarget, setKTarget] = useState(5);
  const [maxWeight, setMaxWeight] = useState(0.35);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const getRiskLambda = (profile) => {
    switch (profile) {
      case 'conservative': return 3.0;
      case 'balanced': return 1.0;
      case 'growth': return 0.5;
      case 'aggressive': return 0.2;
      default: return 1.0;
    }
  };

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          capital: parseFloat(capital),
          k_target: parseInt(kTarget),
          risk_aversion: getRiskLambda(riskProfile),
          max_weight: parseFloat(maxWeight),
          max_sector_weight: 0.50,
          solver: 'qaoa',
          force_bundled: true
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Optimization failed');
      }

      const data = await res.json();
      setResult(data);
      if (onOptimizeComplete) onOptimizeComplete(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Run initial optimization on load
  useEffect(() => {
    handleOptimize();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Intro Header */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700 }}>
              Smart Portfolio Allocator
            </h2>
            <p style={{ margin: '0.4rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
              Select your investment amount and risk preference. Our hybrid Quantum engine chooses the optimal stock combination.
            </p>
          </div>
          <button className="btn-primary" onClick={handleOptimize} disabled={loading}>
            <Sparkles size={18} />
            {loading ? 'Quantum Computing in Progress...' : '⚡ Optimize My Portfolio'}
          </button>
        </div>
      </div>

      {/* Input Controls Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {/* Capital & Investment */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '0.5rem' }}>
            Investment Amount (INR ₹)
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.2rem', color: '#38bdf8', fontWeight: 700 }}>₹</span>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              step="100000"
              style={{
                width: '100%',
                padding: '0.65rem 1rem',
                borderRadius: '10px',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                background: 'rgba(10, 12, 22, 0.6)',
                color: '#f8fafc',
                fontSize: '1.1rem',
                fontWeight: 600
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem' }}>
            {[500000, 1000000, 2500000, 5000000].map(amt => (
              <button
                key={amt}
                onClick={() => setCapital(amt)}
                style={{
                  padding: '0.3rem 0.6rem',
                  fontSize: '0.75rem',
                  borderRadius: '6px',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  background: capital === amt ? 'rgba(99, 102, 241, 0.3)' : 'transparent',
                  color: '#cbd5e1',
                  cursor: 'pointer'
                }}
              >
                ₹{(amt/100000).toFixed(1)}L
              </button>
            ))}
          </div>
        </div>

        {/* Risk Appetite */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '0.5rem' }}>
            Risk Preference
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            {[
              { id: 'conservative', label: 'Conservative', icon: Shield, desc: 'Low Volatility' },
              { id: 'balanced', label: 'Balanced', icon: TrendingUp, desc: 'Optimal Sharpe' },
              { id: 'growth', label: 'Growth', icon: Rocket, desc: 'Higher Returns' },
              { id: 'aggressive', label: 'Aggressive', icon: Sparkles, desc: 'Max Return' }
            ].map(p => {
              const Icon = p.icon;
              const isSel = riskProfile === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setRiskProfile(p.id)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    padding: '0.65rem 0.8rem',
                    borderRadius: '10px',
                    border: isSel ? '1px solid #38bdf8' : '1px solid rgba(99, 102, 241, 0.15)',
                    background: isSel ? 'rgba(56, 189, 248, 0.15)' : 'rgba(10, 12, 22, 0.4)',
                    color: isSel ? '#f8fafc' : '#94a3b8',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.85rem' }}>
                    <Icon size={14} color={isSel ? '#38bdf8' : '#94a3b8'} />
                    {p.label}
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>{p.desc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Target Asset Count */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '0.5rem' }}>
            Target Stock Count (K = {kTarget} Stocks)
          </label>
          <input
            type="range"
            min="2"
            max="15"
            value={kTarget}
            onChange={(e) => setKTarget(parseInt(e.target.value))}
            style={{ width: '100%', accentColor: '#6366f1', cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.6rem' }}>
            {[
              { count: 3, label: '3 (High Conviction)' },
              { count: 5, label: '5 (Balanced)' },
              { count: 10, label: '10 (Diversified)' },
              { count: 15, label: '15 (Full Universe)' }
            ].map(item => (
              <button
                key={item.count}
                onClick={() => setKTarget(item.count)}
                style={{
                  flex: 1,
                  padding: '0.35rem 0.2rem',
                  fontSize: '0.72rem',
                  borderRadius: '6px',
                  border: parseInt(kTarget) === item.count ? '1px solid #38bdf8' : '1px solid rgba(99, 102, 241, 0.2)',
                  background: parseInt(kTarget) === item.count ? 'rgba(56, 189, 248, 0.2)' : 'rgba(10, 12, 22, 0.4)',
                  color: parseInt(kTarget) === item.count ? '#f8fafc' : '#94a3b8',
                  cursor: 'pointer',
                  fontWeight: parseInt(kTarget) === item.count ? 600 : 400
                }}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div style={{ marginTop: '1rem' }}>
            <label style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>
              Max Single Stock Cap: <strong>{(maxWeight * 100).toFixed(0)}%</strong>
            </label>
            <input
              type="range"
              min="0.15"
              max="0.50"
              step="0.05"
              value={maxWeight}
              onChange={(e) => setMaxWeight(e.target.value)}
              style={{ width: '100%', accentColor: '#06b6d4', cursor: 'pointer', marginTop: '0.3rem' }}
            />
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Results Workspace */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Key Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.2rem' }}>
            <div className="glass-card" style={{ padding: '1.2rem 1.5rem' }}>
              <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Expected Annual Return</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34d399', marginTop: '0.3rem' }}>
                +{result.metrics.expected_return_pct}%
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Annualized Portfolio Yield</span>
            </div>

            <div className="glass-card" style={{ padding: '1.2rem 1.5rem' }}>
              <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Expected Annual Risk</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f59e0b', marginTop: '0.3rem' }}>
                {result.metrics.volatility_pct}%
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Standard Volatility</span>
            </div>

            <div className="glass-card" style={{ padding: '1.2rem 1.5rem' }}>
              <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Portfolio Efficiency (Sharpe)</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8', marginTop: '0.3rem' }}>
                {result.metrics.sharpe_ratio}
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Return per Unit Risk</span>
            </div>

            <div className="glass-card" style={{ padding: '1.2rem 1.5rem' }}>
              <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Quantum Compute Time</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a5b4fc', marginTop: '0.3rem' }}>
                {result.runtime_sec}s
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>QAOA Simulator Speed</span>
            </div>
          </div>

          {/* Plain-English Executive Summary */}
          <div className="glass-card" style={{ padding: '1.5rem 1.8rem', borderLeft: '4px solid #38bdf8' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
              <CheckCircle2 size={20} color="#38bdf8" />
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Executive Portfolio Strategy Summary</h3>
            </div>
            <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6' }}>
              {result.executive_narrative}
            </p>
          </div>

          {/* Charts & Allocations */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
            {/* Allocation Donut Chart */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Weight Distribution (% Share)</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={result.allocations}
                      dataKey="weight_pct"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={95}
                      paddingAngle={4}
                    >
                      {result.allocations.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: '#121628', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px' }}
                      formatter={(val) => [`${val}%`, 'Weight']}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Capital Allocation Bar Chart */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Capital Invested Per Stock (₹ INR)</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={result.allocations}>
                    <XAxis dataKey="ticker" stroke="#94a3b8" />
                    <YAxis
                      stroke="#94a3b8"
                      tickFormatter={(val) => {
                        if (!val || val === 0) return '₹0';
                        if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
                        if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
                        if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
                        return `₹${val}`;
                      }}
                    />
                    <Tooltip
                      contentStyle={{ background: '#121628', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px' }}
                      formatter={(val) => [`₹${val.toLocaleString()}`, 'Investment']}
                    />
                    <Bar dataKey="allocation_inr" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Allocation Table */}
          <div className="glass-card" style={{ padding: '1.5rem', overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Optimized Stock Holdings Table</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.2)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Ticker</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Company Name</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Sector</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Portfolio Share (%)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Invested Amount (INR)</th>
                </tr>
              </thead>
              <tbody>
                {result.allocations.map((item, idx) => (
                  <tr key={item.ticker} style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.08)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#38bdf8' }}>{item.ticker}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#f8fafc' }}>{item.name}</td>
                    <td style={{ padding: '0.75rem 1rem' }}><span className="metric-pill">{item.sector}</span></td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{item.weight_pct}%</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#34d399' }}>
                      {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(item.allocation_inr)}
                    </td>
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
