import React from 'react';
import { Cpu, LayoutDashboard, BarChart3, History, Lightbulb, Binary, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, isQuantMode, setIsQuantMode }) {
  const navItems = [
    { id: 'builder', label: 'Portfolio Builder', icon: LayoutDashboard },
    { id: 'benchmark', label: 'Quantum vs Classical', icon: BarChart3 },
    { id: 'backtest', label: 'Historical Growth', icon: History },
    { id: 'explainer', label: 'Why This Portfolio?', icon: Lightbulb },
    ...(isQuantMode ? [{ id: 'quant', label: 'Quant Deep-Dive', icon: Binary }] : [])
  ];

  return (
    <header style={{
      background: 'rgba(10, 12, 22, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(99, 102, 241, 0.15)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0.8rem 2rem'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            padding: '0.6rem',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
          }}>
            <Cpu size={24} color="#ffffff" />
          </div>
          <div>
            <h1 className="gradient-text" style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, letterSpacing: '1px' }}>
              Q-PORT
            </h1>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Smart Quantum Portfolio Intelligence
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(18, 22, 40, 0.6)', padding: '0.3rem', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.1)' }}>
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.55rem 1rem',
                  borderRadius: '8px',
                  border: 'none',
                  background: isActive ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%)' : 'transparent',
                  color: isActive ? '#f8fafc' : '#94a3b8',
                  fontWeight: isActive ? 600 : 400,
                  fontSize: '0.88rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} color={isActive ? '#38bdf8' : '#94a3b8'} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Quant Mode Toggle & Engine Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '0.35rem 0.75rem', borderRadius: '20px' }}>
            <ShieldCheck size={14} color="#10b981" />
            <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
              Python Quantum Core Active
            </span>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: '#cbd5e1', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={isQuantMode}
              onChange={(e) => setIsQuantMode(e.target.checked)}
              style={{ accentColor: '#6366f1', cursor: 'pointer' }}
            />
            Quant / Research Mode
          </label>
        </div>
      </div>
    </header>
  );
}
