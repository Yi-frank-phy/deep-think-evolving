import React from 'react';
import { DeepThinkState } from '../types';

interface KPIDashboardProps {
    state: DeepThinkState | null;
}

export const KPIDashboard: React.FC<KPIDashboardProps> = ({ state }) => {
    const activeCount = state?.strategies.filter(s => s.status === 'active').length || 0;
    const totalCount = state?.strategies.length || 0;
    const bestScore = state?.strategies.reduce((max, s) => Math.max(max, s.score || 0), 0) || 0;

    // Entropy background color (Red = High/Chaos, Blue = Low/Order)
    // T_eff Color (Red = High Temp, Blue = Low Temp)

    return (
        <div className="kpi-dashboard" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem'
        }}>
            <KPICard title="Active Strategies" value={activeCount} subValue={`/ ${totalCount} Total`} />
            <KPICard title="Spatial Entropy" value={state?.spatial_entropy.toFixed(4) || "0.0000"} />
            <KPICard title="Effective Temp (T_eff)" value={state?.effective_temperature.toFixed(2) || "0.00"}
                color={state?.effective_temperature ? `rgba(255, 100, 100, ${Math.min(1, state.effective_temperature / 5)})` : undefined} />
            <KPICard title="Best UCB Score" value={bestScore.toFixed(4)} />
        </div>
    );
};

interface KPICardProps {
    title: string;
    value: string | number;
    subValue?: string;
    color?: string;
}

const KPICard: React.FC<KPICardProps> = ({ title, value, subValue, color }) => (
    <div className="kpi-card" style={{
        background: 'var(--surface-color)',
        padding: '1rem',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden'
    }}>
        {color && (
            <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                background: color,
                opacity: 0.1,
                pointerEvents: 'none'
            }} />
        )}
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>{title}</h4>
        <span className="kpi-value" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{value}</span>
        {subValue && <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>{subValue}</span>}
    </div>
);
