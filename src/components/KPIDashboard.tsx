import React from 'react';

export const KPIDashboard: React.FC = () => {
    return (
        <div className="kpi-dashboard" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem'
        }}>
            <div className="kpi-card" style={kpiCardStyle}>
                <h4>Active Tasks</h4>
                <span className="kpi-value">3</span>
            </div>
            <div className="kpi-card" style={kpiCardStyle}>
                <h4>Total Cost</h4>
                <span className="kpi-value">$0.42</span>
            </div>
            <div className="kpi-card" style={kpiCardStyle}>
                <h4>Explored Paths</h4>
                <span className="kpi-value">128</span>
            </div>
            <div className="kpi-card" style={kpiCardStyle}>
                <h4>Best Score</h4>
                <span className="kpi-value">0.89</span>
            </div>
        </div>
    );
};

const kpiCardStyle: React.CSSProperties = {
    background: 'var(--surface-color)',
    padding: '1rem',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
};
