import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { History, TrendingUp, ShieldAlert, Check } from 'lucide-react';

export default function BacktestView() {
  const [loading, setLoading] = useState(false);
  const [backtestData, setBacktestData] = useState(null);

  const runBacktest = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          train_window_days: 252,
          test_window_days: 63,
          k_target: 5,
          force_bundled: true
        })
      });
      const data = await res.json();
      setBacktestData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runBacktest();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-card" style={{ padding: '1.8rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 700 }}>
              Historical Out-of-Sample Backtesting Growth
            </h2>
            <p style={{ margin: '0.4rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
              Test how the strategy would have performed historically over unseen out-of-sample periods without look-ahead bias.
            </p>
          </div>
          <button className="btn-primary" onClick={runBacktest} disabled={loading}>
            <History size={18} />
            {loading ? 'Running Walk-Forward Simulation...' : '🚀 Execute Historical Backtest'}
          </button>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div style={{ padding: '0.9rem 1.2rem', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '10px', color: '#f59e0b', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <ShieldAlert size={18} />
        <span><strong>Past Performance Notice</strong>: Historical simulation results do not guarantee future performance under real trading dynamics.</span>
      </div>

      {backtestData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Equity Curve Chart */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Growth of ₹1.00 Out-of-Sample Portfolio Value</h3>
            <div style={{ width: '100%', height: 380 }}>
              <ResponsiveContainer>
                <LineChart data={backtestData.equity_curves}>
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" domain={['auto', 'auto']} tickFormatter={(v) => `₹${v.toFixed(2)}`} />
                  <Tooltip contentStyle={{ background: '#121628', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px' }} />
                  <Legend />
                  <Line type="monotone" dataKey="Q-PORT (Hybrid QAOA)" stroke="#38bdf8" strokeWidth={3} dot={false} />
                  <Line type="monotone" dataKey="Equal Weight (1/N)" stroke="#94a3b8" strokeWidth={2} strokeDasharray="3 3" dot={false} />
                  <Line type="monotone" dataKey="Continuous Mean-Variance" stroke="#34d399" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Performance Summary Metrics Table */}
          <div className="glass-card" style={{ padding: '1.5rem', overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>Out-of-Sample Risk & Return Summary</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.2)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Strategy Name</th>
                  <th style={{ padding: '0.75rem 1rem' }}>CAGR (%)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Annualized Return (%)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Annual Volatility (%)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Sharpe Ratio</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Max Drawdown (%)</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Win Rate (%)</th>
                </tr>
              </thead>
              <tbody>
                {backtestData.metrics.map((m) => (
                  <tr key={m.Strategy} style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.08)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: m.Strategy.includes('Q-PORT') ? '#38bdf8' : '#f8fafc' }}>{m.Strategy}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#34d399', fontWeight: 600 }}>{m['CAGR (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{m['Annualized Return (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#f59e0b' }}>{m['Annualized Volatility (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700 }}>{m['Sharpe Ratio'].toFixed(2)}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ec4899' }}>{m['Max Drawdown (%)'].toFixed(2)}%</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{m['Win Rate (%)'].toFixed(1)}%</td>
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
