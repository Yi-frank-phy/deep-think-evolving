import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { StrategyNode as StrategyNodeType } from '../types';

interface CustomStrategyNodeData {
    strategy: StrategyNodeType;
}

const StrategyNodeComponent: React.FC<NodeProps<CustomStrategyNodeData>> = ({ data }) => {
    const { strategy: strat } = data;

    const score = strat.score?.toFixed(2) ?? '?';
    const ucb = strat.ucb_score?.toFixed(2) ?? '-';
    const quota = strat.child_quota ?? 0;

    // 状态图标
    let statusIcon = '⚪';
    if (strat.status === 'active') statusIcon = '🟢';
    else if (strat.status === 'pruned' || strat.status === 'pruned_synthesized') statusIcon = '🔴';
    else if (strat.status === 'expanded') statusIcon = '🔵';
    else if (strat.status === 'completed') statusIcon = '🟣';

    // 截断但显示更多
    const rationalePreview = strat.rationale
        ? (strat.rationale.length > 80 ? strat.rationale.substring(0, 80) + '...' : strat.rationale)
        : '';

    return (
        <div style={{ lineHeight: 1.4, position: 'relative' }}>
            <Handle type="target" position={Position.Top} style={{ visibility: 'hidden' }} />

            <div style={{
                fontWeight: 600,
                fontSize: '13px',
                marginBottom: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
            }}>
                <span>{statusIcon}</span>
                <span style={{ flex: 1 }}>{strat.name}</span>
            </div>

            <div style={{
                display: 'flex',
                gap: '8px',
                fontSize: '10px',
                color: '#888',
                marginBottom: '6px'
            }}>
                <span>Score: <b style={{ color: '#4CAF50' }}>{score}</b></span>
                <span>UCB: <b style={{ color: '#FF9800' }}>{ucb}</b></span>
                {quota > 0 && <span>Quota: <b style={{ color: '#2196F3' }}>{quota}</b></span>}
            </div>

            {rationalePreview && (
                <div style={{
                    fontSize: '11px',
                    color: '#aaa',
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    paddingTop: '6px',
                    marginTop: '4px'
                }}>
                    {rationalePreview}
                </div>
            )}

            <Handle type="source" position={Position.Bottom} style={{ visibility: 'hidden' }} />
        </div>
    );
};

export const StrategyNode = memo(StrategyNodeComponent, (prev, next) => {
    // Custom comparison to optimize re-renders
    const s1 = prev.data.strategy;
    const s2 = next.data.strategy;

    // If it's the same object reference, no change
    if (s1 === s2) return true;

    // Compare critical fields that affect rendering
    return (
        s1.id === s2.id &&
        s1.name === s2.name &&
        s1.status === s2.status &&
        s1.score === s2.score &&
        s1.ucb_score === s2.ucb_score &&
        s1.child_quota === s2.child_quota &&
        s1.rationale === s2.rationale
    );
});
