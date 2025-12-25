/**
 * ThinkingPanel - Gemini Deep Research Style Thinking Panel
 * 
 * Sidebar displaying real-time AI reasoning process, supporting expansion/collapse.
 * Design inspired by Google Gemini Deep Research Thinking Panel.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { ChevronDown, ChevronRight, Brain, Loader2, CheckCircle2 } from 'lucide-react';
import { DeepThinkState, AgentActivity, AgentPhase } from '../types';

interface ThinkingPanelProps {
    state: DeepThinkState | null;
    activityLog: AgentActivity[];
    currentAgent: AgentPhase | null;
    simulationStatus: 'idle' | 'running' | 'completed' | 'error' | 'awaiting_human';
}

const AGENT_LABELS: Record<AgentPhase, string> = {
    task_decomposer: 'Task Decomposition',
    researcher: 'Information Gathering',
    strategy_generator: 'Strategy Generation',
    distiller: 'Context Distillation',
    architect: 'Strategic Planning',
    architect_scheduler: 'Execution Scheduling',
    distiller_for_judge: 'Evaluation Prep',
    executor: 'Strategy Execution',
    judge: 'Feasibility Assessment',
    evolution: 'Evolutionary Iteration',
    propagation: 'Knowledge Propagation'
};

export const ThinkingPanel: React.FC<ThinkingPanelProps> = React.memo(({
    state,
    activityLog,
    currentAgent,
    simulationStatus
}) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set(['understanding', 'evaluation', 'execution']));
    const [expandedIterations, setExpandedIterations] = useState<Set<number>>(new Set());
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current && simulationStatus === 'running') {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [activityLog, simulationStatus]);

    const toggleIteration = (iteration: number) => {
        setExpandedIterations(prev => {
            const newSet = new Set(prev);
            if (newSet.has(iteration)) {
                newSet.delete(iteration);
            } else {
                newSet.add(iteration);
            }
            return newSet;
        });
    };

    // Group activities by iteration - Memoized
    const iterationGroups = useMemo(() => {
        const groups: Map<number, AgentActivity[]> = new Map();
        let currentIteration = 0;

        activityLog.forEach(activity => {
            if (activity.agent === 'evolution') {
                currentIteration++;
            }
            if (!groups.has(currentIteration)) {
                groups.set(currentIteration, []);
            }
            groups.get(currentIteration)?.push(activity);
        });

        return groups;
    }, [activityLog]);

    const currentIteration = state?.iteration_count || 0;

    // Strategy stats - Memoized
    const strategyStats = useMemo(() => {
        if (!state?.strategies) return null;
        return {
            activeCount: state.strategies.filter(s => s.status === 'active').length,
            prunedCount: state.strategies.filter(s => s.status === 'pruned' || s.status === 'pruned_synthesized').length,
            total: state.strategies.length
        };
    }, [state?.strategies]);

    // Top strategies - Memoized
    const topStrategies = useMemo(() => {
        if (!state?.strategies) return [];
        return state.strategies
            .filter(s => s.status === 'active')
            .sort((a, b) => (b.ucb_score || b.score || 0) - (a.ucb_score || a.score || 0))
            .slice(0, 3);
    }, [state?.strategies]);

    // Render Strategy Summary
    const renderStrategySummary = () => {
        if (!strategyStats) return null;

        return (
            <div className="strategy-summary">
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Strategy Space
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--success-color)' }}>🟢 Active: {strategyStats.activeCount}</span>
                    <span style={{ color: 'var(--failure-color)' }}>🔴 Pruned: {strategyStats.prunedCount}</span>
                    <span style={{ color: 'var(--text-muted)' }}>Total: {strategyStats.total}</span>
                </div>
            </div>
        );
    };

    // Render Metrics
    const renderMetrics = () => {
        if (!state) return null;

        return (
            <div className="metric-grid">
                <div className="metric-card">
                    <div className="metric-label">Iteration</div>
                    <div className="metric-value">
                        {currentIteration} / {state.config?.max_iterations || 10}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">Temperature τ</div>
                    <div className="metric-value" style={{ color: getTemperatureColor(state.normalized_temperature || 0) }}>
                        {(state.normalized_temperature || 0).toFixed(3)}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">Entropy</div>
                    <div className="metric-value">
                        {(state.spatial_entropy || 0).toFixed(2)}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">Status</div>
                    <div className="metric-value" style={{ color: getStatusColor(simulationStatus), fontSize: '0.9rem' }}>
                        {getStatusLabel(simulationStatus)}
                    </div>
                </div>
            </div>
        );
    };

    // Render Current Thinking
    const renderCurrentThinking = () => {
        if (simulationStatus !== 'running' || !currentAgent) return null;

        const latestActivity = activityLog[activityLog.length - 1];

        return (
            <div className="thinking-active-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Loader2 size={14} style={{ animation: 'spin 1s linear infinite', color: 'var(--primary-color)' }} />
                    <span style={{ fontSize: '12px', color: 'var(--primary-color)', fontWeight: 500 }}>
                        {AGENT_LABELS[currentAgent]}...
                    </span>
                </div>
                {latestActivity?.detail && (
                    <div style={{ fontSize: '13px', color: 'var(--text-color)', lineHeight: 1.5 }}>
                        {latestActivity.detail}
                    </div>
                )}
            </div>
        );
    };

    // Render Iteration Details
    const renderIterationDetails = (iteration: number, activities: AgentActivity[]) => {
        const isExpanded = expandedIterations.has(iteration);
        const isCurrentIteration = iteration === Math.max(...Array.from(iterationGroups.keys()));

        return (
            <div key={iteration} style={{ marginBottom: '8px' }}>
                <button
                    type="button"
                    onClick={() => toggleIteration(iteration)}
                    aria-expanded={isExpanded}
                    aria-controls={`iteration-content-${iteration}`}
                    className="iteration-header"
                    style={{
                        background: isCurrentIteration ? 'rgba(168, 199, 250, 0.1)' : 'transparent',
                    }}
                >

                    {isExpanded ? <ChevronDown size={14} color="var(--text-muted)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
                    <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-color)' }}>
                        Iteration {iteration}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                        {activities.length} Steps
                    </span>
                </button>

                {isExpanded && (
                    <div id={`iteration-content-${iteration}`} style={{ paddingLeft: '24px', paddingTop: '8px' }}>
                        {activities.map((activity, idx) => (
                            <div key={activity.id || idx} style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '8px',
                                padding: '6px 0',
                                borderLeft: '1px solid var(--border-color)',
                                paddingLeft: '12px',
                                marginLeft: '6px'
                            }}>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '80px' }}>
                                    {AGENT_LABELS[activity.agent]}
                                </span>
                                <span style={{ fontSize: '12px', color: 'var(--text-color)', flex: 1 }}>
                                    {activity.detail || activity.message}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // Render Top Strategies
    const renderTopStrategies = () => {
        if (topStrategies.length === 0) return null;

        return (
            <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    🏆 Top Strategies
                </div>
                {topStrategies.map((s, idx) => (
                    <div key={s.id} style={{
                        padding: '10px 12px',
                        background: idx === 0 ? 'rgba(129, 201, 149, 0.1)' : 'var(--surface-color)',
                        borderRadius: 'var(--radius-sm)',
                        marginBottom: '6px',
                        borderLeft: idx === 0 ? '3px solid var(--success-color)' : '3px solid var(--border-color)'
                    }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-color)', marginBottom: '4px' }}>
                            {s.name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            UCB: {(s.ucb_score || 0).toFixed(2)} | Score: {(s.score || 0).toFixed(2)}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="thinking-container">
            {/* Header */}
            <div className="thinking-header">
                <Brain size={18} style={{ color: 'var(--primary-color)' }} />
                <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-color)' }}>
                    Thinking Process
                </span>
                {simulationStatus === 'running' && (
                    <Loader2 size={14} style={{ marginLeft: 'auto', animation: 'spin 1s linear infinite', color: 'var(--primary-color)' }} />
                )}
                {simulationStatus === 'completed' && (
                    <CheckCircle2 size={14} style={{ marginLeft: 'auto', color: 'var(--success-color)' }} />
                )}
            </div>

            {/* Content */}
            <div ref={scrollRef} className="thinking-content">
                {simulationStatus === 'idle' && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '40px 20px' }}>
                        Enter a problem and start simulation to begin reasoning...
                    </div>
                )}

                {simulationStatus !== 'idle' && (
                    <>
                        {renderMetrics()}
                        {renderCurrentThinking()}
                        {renderStrategySummary()}
                        {renderTopStrategies()}

                        {/* Iteration History */}
                        <div style={{ marginTop: '16px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                📜 Reasoning History
                            </div>
                            {Array.from(iterationGroups.entries())
                                .reverse()
                                .map(([iteration, activities]) =>
                                    renderIterationDetails(iteration, activities)
                                )}
                        </div>
                    </>
                )}
            </div>

            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
});

// Helper Functions
function getTemperatureColor(t: number): string {
    if (t < 0.3) return 'var(--success-color)';
    if (t < 0.7) return 'var(--warning-color)';
    return 'var(--failure-color)';
}

function getStatusColor(status: string): string {
    switch (status) {
        case 'running': return 'var(--primary-color)';
        case 'completed': return 'var(--success-color)';
        case 'error': return 'var(--failure-color)';
        case 'awaiting_human': return 'var(--warning-color)';
        default: return 'var(--text-muted)';
    }
}

function getStatusLabel(status: string): string {
    switch (status) {
        case 'idle': return 'Idle';
        case 'running': return 'Reasoning';
        case 'completed': return 'Completed';
        case 'error': return 'Error';
        case 'awaiting_human': return 'Awaiting Input';
        default: return status;
    }
}

export default ThinkingPanel;
