import React from 'react';
import { DeepThinkState, AgentPhase } from '../types';

interface KPIDashboardProps {
    state: DeepThinkState | null;
    currentAgent?: AgentPhase | null;
    simulationStatus?: 'idle' | 'running' | 'completed' | 'error';
}

const AGENT_DISPLAY: Record<AgentPhase, { icon: string; name: string; color: string }> = {
    researcher: { icon: '🔍', name: 'Researcher', color: '#8B5CF6' },
    distiller: { icon: '📝', name: 'Distiller', color: '#06B6D4' },
    architect: { icon: '🏗️', name: 'Architect', color: '#F59E0B' },
    distiller_for_judge: { icon: '📋', name: 'Context Prep', color: '#6366F1' },
    judge: { icon: '⚖️', name: 'Judge', color: '#EF4444' },
    evolution: { icon: '🧬', name: 'Evolution', color: '#10B981' },
    propagation: { icon: '🌱', name: 'Propagation', color: '#3B82F6' },
};

export const KPIDashboard: React.FC<KPIDashboardProps> = ({
    state,
    currentAgent,
    simulationStatus = 'idle'
}) => {
    const activeCount = state?.strategies.filter(s => s.status === 'active').length || 0;
    const totalCount = state?.strategies.length || 0;
    const bestScore = state?.strategies.reduce((max, s) => Math.max(max, s.score || 0), 0) || 0;

    const agentInfo = currentAgent ? AGENT_DISPLAY[currentAgent] : null;

    return (
        <div className="kpi-dashboard" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem'
        }}>
            {/* Current Agent Status - Only show when running */}
            {simulationStatus === 'running' && agentInfo && (
                <div className="kpi-card agent-status" style={{
                    background: `linear-gradient(135deg, ${agentInfo.color}20 0%, ${agentInfo.color}05 100%)`,
                    padding: '1rem',
                    borderRadius: 'var(--radius-sm)',
                    border: `1px solid ${agentInfo.color}40`,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                    animation: 'pulse-border 2s ease-in-out infinite'
                }}>
                    <div style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        background: `radial-gradient(circle at center, ${agentInfo.color}10 0%, transparent 70%)`,
                        animation: 'pulse-glow 2s ease-in-out infinite',
                        pointerEvents: 'none'
                    }} />
                    <span style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{agentInfo.icon}</span>
                    <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                        当前工作
                    </h4>
                    <span style={{ fontSize: '1rem', fontWeight: 'bold', color: agentInfo.color }}>
                        {agentInfo.name}
                    </span>
                </div>
            )}

            <KPICard title="Iteration" value={state?.iteration_count || 0} />
            <KPICard title="Active Strategies" value={activeCount} subValue={`/ ${totalCount} Total`} />
            <KPICard title="Spatial Entropy" value={state?.spatial_entropy.toFixed(4) || "0.0000"} />
            <KPICard title="Effective Temp (T_eff)" value={state?.effective_temperature.toFixed(2) || "0.00"}
                color={state?.effective_temperature ? `rgba(255, 100, 100, ${Math.min(1, state.effective_temperature / 5)})` : undefined} />
            <KPICard title="Best UCB Score" value={bestScore.toFixed(4)} />

            <style>{`
                @keyframes pulse-border {
                    0%, 100% { box-shadow: 0 0 0 0 currentColor; }
                    50% { box-shadow: 0 0 15px -5px currentColor; }
                }
                @keyframes pulse-glow {
                    0%, 100% { opacity: 0.3; }
                    50% { opacity: 0.6; }
                }
            `}</style>
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

