import React from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { AgentActivity, AgentPhase } from '../types';

interface IterationItemProps {
    iteration: number;
    activities: AgentActivity[];
    isExpanded: boolean;
    isCurrentIteration: boolean;
    onToggle: (iteration: number) => void;
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

export const IterationItem = React.memo(({
    iteration,
    activities,
    isExpanded,
    isCurrentIteration,
    onToggle
}: IterationItemProps) => {
    return (
        <div style={{ marginBottom: '8px' }}>
            <button
                type="button"
                onClick={() => onToggle(iteration)}
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
                                {AGENT_LABELS[activity.agent] || activity.agent}
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
}, (prev, next) => {
    // Custom comparison for performance
    if (prev.iteration !== next.iteration) return false;
    if (prev.isExpanded !== next.isExpanded) return false;
    if (prev.isCurrentIteration !== next.isCurrentIteration) return false;

    // Optimization: Check if activities array changed significantly
    // Since arrays are rebuilt on every parent render, strict equality (===) always fails.
    // We assume append-only or update-last behavior for activities.

    // 1. Length check
    if (prev.activities.length !== next.activities.length) return false;

    // 2. If length is same, check the last item (most likely to change in streaming)
    if (prev.activities.length > 0) {
        const lastPrev = prev.activities[prev.activities.length - 1];
        const lastNext = next.activities[next.activities.length - 1];

        // Check if the last activity object is the same reference or has same content
        if (lastPrev !== lastNext) {
            // If references differ, check content (id or simple props)
            if (lastPrev.id !== lastNext.id) return false;
            if (lastPrev.detail !== lastNext.detail) return false;
        }
    }

    return true;
});
