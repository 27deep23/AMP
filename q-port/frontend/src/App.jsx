import React, { useState } from 'react';
import Navbar from './components/Navbar';
import PortfolioBuilder from './components/PortfolioBuilder';
import BenchmarkView from './components/BenchmarkView';
import BacktestView from './components/BacktestView';
import PortfolioExplainer from './components/PortfolioExplainer';
import QuantDeepDive from './components/QuantDeepDive';

export default function App() {
  const [activeTab, setActiveTab] = useState('builder');
  const [isQuantMode, setIsQuantMode] = useState(false);
  const [lastOptimizationResult, setLastOptimizationResult] = useState(null);

  const handleOptimizeComplete = (data) => {
    setLastOptimizationResult(data);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isQuantMode={isQuantMode}
        setIsQuantMode={setIsQuantMode}
      />

      {/* Main Page Workspace */}
      <main style={{ flex: 1, maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '2rem' }}>
        {activeTab === 'builder' && <PortfolioBuilder onOptimizeComplete={handleOptimizeComplete} />}
        {activeTab === 'benchmark' && <BenchmarkView />}
        {activeTab === 'backtest' && <BacktestView />}
        {activeTab === 'explainer' && <PortfolioExplainer lastOptimizationResult={lastOptimizationResult} />}
        {activeTab === 'quant' && isQuantMode && <QuantDeepDive lastOptimizationResult={lastOptimizationResult} />}
      </main>

      {/* Footer */}
      <footer style={{
        background: 'rgba(10, 12, 22, 0.9)',
        borderTop: '1px solid rgba(99, 102, 241, 0.15)',
        padding: '1.5rem 2rem',
        marginTop: '3rem',
        fontSize: '0.82rem',
        color: '#64748b'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong style={{ color: '#cbd5e1' }}>Q-PORT — Quantum Portfolio Intelligence Platform</strong> · UC-018 Asset Manager Portfolio Optimisation
          </div>
          <div>
            ⚠️ <em>All quantum computation executed via Qiskit Aer simulation on local CPU infrastructure. No physical quantum hardware used.</em>
          </div>
        </div>
      </footer>
    </div>
  );
}
