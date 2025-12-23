import React from 'react';
import { DeepThinkState, AgentPhase } from '../types';

interface KPIDashboardProps {
    state: DeepThinkState | null;
    currentAgent?: AgentPhase | null;
    simulationStatus?: 'idle' | 'running' | 'completed' | 'error' | 'awaiting_human';
}

const AGENT_DISPLAY: Record<AgentPhase, { icon: string; name: string; color: string }> = {
    task_decomposer: { icon: '🧩', name: 'Decomposer', color: '#9C27B0' },
    researcher: { icon: '🔍', name: 'Researcher', color: '#8B5CF6' },
    strategy_generator: { icon: '💡', name: 'Generator', color: '#E91E63' },
    distiller: { icon: '📝', name: 'Distiller', color: '#06B6D4' },
    architect: { icon: '🏗️', name: 'Architect', color: '#F59E0B' },
    architect_scheduler: { icon: '📅', name: 'Scheduler', color: '#FF9800' },
    distiller_for_judge: { icon: '📋', name: 'Context Prep', color: '#6366F1' },
    executor: { icon: '🤖', name: 'Executor', color: '#795548' },
    judge: { icon: '⚖️', name: 'Judge', color: '#EF4444' },
    evolution: { icon: '🧬', name: 'Evolution', color: '#10B981' },
    propagation: { icon: '🌱', name: 'Propagation', color: '#3B82F6' },
};

export const KPIDashboard: React.FC<KPIDashboardProps> = React.memo(({
    state,
    currentAgent,
    simulationStatus = 'idle'
}) => {
    const activeCount = state?.strategies.filter(s => s.status === 'active').length || 0;
    const totalCount = state?.strategies.length || 0;
    const bestScore = state?.strategies.reduce((max, s) => Math.max(max, s.score || 0), 0) || 0;

    const agentInfo = currentAgent ? AGENT_DISPLAY[currentAgent] : null;

    return (
        <>
            {/* Current Agent Status - Compact inline badge */}
            {simulationStatus === 'running' && agentInfo && (
                <div className="kpi-item" style={{ borderRight: '1px solid var(--border-color)', paddingRight: '1rem' }}>
                    <span style={{ fontSize: '1rem' }} aria-hidden="true">{agentInfo.icon}</span>
                    <span className="kpi-value" style={{ color: agentInfo.color, fontWeight: 600 }}>
                        {agentInfo.name}
                    </span>
                </div>
            )}

            <KPIItem
                label="Iter"
                value={state?.iteration_count || 0}
                tooltip="Current Iteration Count"
                ariaLabel="Current iteration count"
            />
            <KPIItem
                label="Active"
                value={`${activeCount}/${totalCount}`}
                tooltip="Active / Total Strategies"
                ariaLabel={`Active strategies: ${activeCount} of ${totalCount}`}
            />
            <KPIItem
                label="Entropy"
                value={(state?.spatial_entropy || 0).toFixed(3)}
                tooltip="Spatial Entropy (Diversity of thought)"
                ariaLabel={`Spatial Entropy: ${(state?.spatial_entropy || 0).toFixed(3)}`}
            />
            <KPIItem
                label="T_eff"
                value={(state?.effective_temperature || 0).toFixed(2)}
                tooltip="Effective Temperature (Exploration rate)"
                ariaLabel={`Effective Temperature: ${(state?.effective_temperature || 0).toFixed(2)}`}
            />
            <KPIItem
                label="Best UCB"
                value={bestScore.toFixed(3)}
                tooltip="Best Upper Confidence Bound score"
                ariaLabel={`Best Upper Confidence Bound score: ${bestScore.toFixed(3)}`}
            />
        </>
    );
});

interface KPIItemProps {
    label: string;
    value: string | number;
    tooltip?: string;
    ariaLabel?: string;
}

const KPIItem: React.FC<KPIItemProps> = ({ label, value, tooltip, ariaLabel }) => (
    <div
        className="kpi-item"
        title={tooltip}
        role="group"
        aria-label={ariaLabel || `${label}: ${value}`}
        tabIndex={0}
    >
        <span className="kpi-label" aria-hidden="true">{label}</span>
        <span className="kpi-value" aria-hidden="true">{value}</span>
    </div>
);
