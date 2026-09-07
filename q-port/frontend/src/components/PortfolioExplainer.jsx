import React from 'react';
import { Lightbulb, TrendingUp, ShieldAlert, Award, Layers } from 'lucide-react';

export default function PortfolioExplainer({ lastOptimizationResult }) {
  if (!lastOptimizationResult) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
        <Lightbulb size={48} color="#6366f1" style={{ marginBottom: '1rem' }} />
        <h3>No Portfolio Data Available Yet</h3>
        <p>Please run the <strong>Portfolio Builder</strong> first to generate executive portfolio insights.</p>
      </div>
    );
  }

  const { metrics, allocations, attribution, executive_narrative, sector_exposures } = lastOptimizationResult;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(56, 189, 248, 0.15)', padding: '0.8rem', borderRadius: '12px' }}>
            <Lightbulb size={32} color="#38bdf8" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700 }}>
              Why Was This Portfolio Selected?
            </h2>
            <p style={{ margin: '0.4rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
              Plain-English explanation of asset selection, risk mitigation, and sector balance choices made by the quantum engine.
            </p>
          </div>
        </div>
      </div>

      {/* Executive Narrative Box */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem', borderLeft: '4px solid #34d399' }}>
        <h3 style={{ margin: '0 0 0.8rem 0', fontSize: '1.2rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Award size={20} /> Executive Summary
        </h3>
        <p style={{ margin: 0, color: '#f8fafc', fontSize: '1.05rem', lineHeight: '1.7' }}>
          {executive_narrative}
        </p>
      </div>

      {/* Asset Attribution Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {attribution && attribution.map((item) => (
          <div key={item.Ticker} className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>{item.Ticker}</h4>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{item.Name}</span>
              </div>
              <span className="metric-pill">{item.Sector}</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem', paddingTop: '0.6rem', borderTop: '1px solid rgba(99, 102, 241, 0.1)' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Weight Share</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>{item['Weight (%)'].toFixed(2)}%</div>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Expected Return</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>+{item['Expected Return (%)'].toFixed(2)}%</div>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Share of Risk</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>{item['Variance Contribution (%)'].toFixed(1)}%</div>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Portfolio Correlation</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#a5b4fc' }}>{item['Portfolio Correlation'].toFixed(2)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sector Exposure Breakdown */}
      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Layers size={18} color="#6366f1" /> Sector Allocation Cap & Breakdown
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          {sector_exposures && Object.entries(sector_exposures).map(([sector, pct]) => (
            <div key={sector} style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '0.8rem 1.2rem', borderRadius: '10px', minWidth: '160px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{sector}</span>
              <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.2rem' }}>{pct}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
