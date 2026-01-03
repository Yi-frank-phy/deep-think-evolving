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
    // Optimization: Calculate all metrics in a single pass to avoid multiple array traversals
    const { activeCount, totalCount, bestScore } = React.useMemo(() => {
        if (!state?.strategies) return { activeCount: 0, totalCount: 0, bestScore: 0 };

        let active = 0;
        let max = 0;
        const total = state.strategies.length;

        for (const s of state.strategies) {
            if (s.status === 'active') active++;
            const score = s.score || 0;
            if (score > max) max = score;
        }

        return {
            activeCount: active,
            totalCount: total,
            bestScore: max
        };
    }, [state?.strategies]);

    const agentInfo = currentAgent ? AGENT_DISPLAY[currentAgent] : null;

    return (
        <section
            className="kpi-dashboard"
            aria-label="Key Performance Indicators"
            role="region"
        >
            {/* Current Agent Status - Compact inline badge */}
            {simulationStatus === 'running' && agentInfo && (
                <div
                    className="kpi-item"
                    style={{ borderRight: '1px solid var(--border-color)', paddingRight: '1rem' }}
                    role="status"
                    aria-label={`Current Agent: ${agentInfo.name}`}
                >
                    <span style={{ fontSize: '1rem' }} aria-hidden="true">{agentInfo.icon}</span>
                    <span className="kpi-value" style={{ color: agentInfo.color, fontWeight: 600 }} aria-hidden="true">
                        {agentInfo.name}
                    </span>
                </div>
            )}

            <KPIItem
                label="Iter"
                value={state?.iteration_count || 0}
                description="Current Iteration Count"
            />
            <KPIItem
                label="Active"
                value={`${activeCount}/${totalCount}`}
                description="Active Strategies vs Total"
            />
            <KPIItem
                label="Entropy"
                value={(state?.spatial_entropy || 0).toFixed(3)}
                description="Spatial Entropy (Diversity Metric)"
            />
            <KPIItem
                label="T_eff"
                value={(state?.effective_temperature || 0).toFixed(2)}
                description="Effective Temperature (Exploration Rate)"
            />
            <KPIItem
                label="Best UCB"
                value={bestScore.toFixed(3)}
                description="Best Upper Confidence Bound Score"
            />
        </section>
    );
});

interface KPIItemProps {
    label: string;
    value: string | number;
    description: string;
}

const KPIItem: React.FC<KPIItemProps> = ({ label, value, description }) => (
    <div
        className="kpi-item"
        title={description}
        role="group"
        aria-label={`${description}: ${value}`}
    >
        <span className="kpi-label" aria-hidden="true">{label}</span>
        <span className="kpi-value" aria-hidden="true">{value}</span>
    </div>
);
