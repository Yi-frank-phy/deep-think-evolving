/**
 * TaskGraph - 增强版策略演化图
 * 
 * 参考 Gemini Deep Research 设计，显示完整策略信息和演化过程
 */

import React, { useMemo, useEffect, useCallback } from 'react';
import ReactFlow, {
    Background,
    Controls,
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    MarkerType,
    MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DeepThinkState, StrategyNode } from '../types';

interface TaskGraphProps {
    state: DeepThinkState | null;
    onNodeClick?: (node: StrategyNode, ctrlKey: boolean) => void;
    selectedNodeIds?: Set<string>;
}

// 自定义节点样式
const getNodeStyle = (strat: StrategyNode, isSelected: boolean) => {
    const isActive = strat.status === 'active';
    const isPruned = strat.status === 'pruned' || strat.status === 'pruned_synthesized';
    const isExpanded = strat.status === 'expanded';
    const isCompleted = strat.status === 'completed';
    const isProcessing = isActive && (strat.child_quota ?? 0) > 0; // 正在处理中

    let borderColor = '#555';
    let bgGradient = 'linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)';

    if (isActive) {
        borderColor = '#4CAF50';
        bgGradient = 'linear-gradient(135deg, #1a2e1a 0%, #0d1a0d 100%)';
    } else if (isPruned) {
        borderColor = '#f44336';
        bgGradient = 'linear-gradient(135deg, #2e1a1a 0%, #1a0d0d 100%)';
    } else if (isExpanded) {
        borderColor = '#2196F3';
        bgGradient = 'linear-gradient(135deg, #1a1a2e 0%, #0d0d1a 100%)';
    } else if (isCompleted) {
        borderColor = '#9C27B0';
        bgGradient = 'linear-gradient(135deg, #2e1a2e 0%, #1a0d1a 100%)';
    }

    return {
        background: bgGradient,
        color: '#e0e0e0',
        border: isSelected ? `2px solid #a78bfa` : `1px solid ${borderColor}`,
        borderLeft: `4px solid ${borderColor}`,
        width: 260,
        minHeight: 80,
        borderRadius: '12px',
        fontSize: '12px',
        padding: '12px',
        cursor: 'pointer',
        boxShadow: isProcessing
            ? '0 0 15px rgba(76, 175, 80, 0.5), 0 0 30px rgba(76, 175, 80, 0.3)' // 处理中脉冲
            : isSelected
                ? '0 0 20px rgba(167, 139, 250, 0.4)'
                : '0 4px 12px rgba(0,0,0,0.4)',
        opacity: isPruned ? 0.5 : 1,
        textAlign: 'left' as const,
        transition: 'all 0.3s ease',
        animation: isProcessing ? 'pulse 2s ease-in-out infinite' : 'none'
    };
};

// 构建节点标签 - 显示完整信息
const buildNodeLabel = (strat: StrategyNode) => {
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
        <div style={{ lineHeight: 1.4 }}>
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
                {quota > 0 && <span>配额: <b style={{ color: '#2196F3' }}>{quota}</b></span>}
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
        </div>
    );
};

export const TaskGraph: React.FC<TaskGraphProps> = ({ state, onNodeClick, selectedNodeIds = new Set() }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        if (!state || !state.strategies) return;

        // --- Tree Layout Logic ---
        const stratMap = new Map<string, StrategyNode>();
        const childrenMap = new Map<string, string[]>();
        const roots: string[] = [];

        state.strategies.forEach(s => {
            stratMap.set(s.id, s);
            const pid = s.parent_id;
            if (pid) {
                if (!childrenMap.has(pid)) childrenMap.set(pid, []);
                childrenMap.get(pid)?.push(s.id);
            } else {
                roots.push(s.id);
            }
        });

        // BFS for Level Assignment
        const levels = new Map<string, number>();
        const queue: { id: string, level: number }[] = roots.map(r => ({ id: r, level: 0 }));
        const maxLevelWidth: number[] = [];

        while (queue.length > 0) {
            const { id, level } = queue.shift()!;
            levels.set(id, level);
            maxLevelWidth[level] = (maxLevelWidth[level] || 0) + 1;
            const children = childrenMap.get(id) || [];
            children.forEach(childId => queue.push({ id: childId, level: level + 1 }));
        }

        // Assign Positions
        const levelCurrentX: number[] = [];
        const newNodes: Node[] = state.strategies.map((strat) => {
            const level = levels.get(strat.id) || 0;
            const levelIdx = levelCurrentX[level] || 0;
            levelCurrentX[level] = levelIdx + 1;

            const width = maxLevelWidth[level] || 1;
            const x = (levelIdx - width / 2) * 300;  // 更宽的间距
            const y = level * 160;

            const isSelected = selectedNodeIds.has(strat.id);

            return {
                id: strat.id,
                position: { x, y },
                data: {
                    label: buildNodeLabel(strat)
                },
                style: getNodeStyle(strat, isSelected),
            };
        });

        // Create Edges with UCB labels
        const newEdges: Edge[] = [];
        state.strategies.forEach(s => {
            if (s.parent_id) {
                const isActive = s.status === 'active';
                const ucbLabel = s.ucb_score ? `UCB: ${s.ucb_score.toFixed(1)}` : '';

                newEdges.push({
                    id: `e-${s.parent_id}-${s.id}`,
                    source: s.parent_id,
                    target: s.id,
                    type: 'smoothstep',
                    animated: isActive,
                    label: ucbLabel,
                    labelStyle: {
                        fill: '#FF9800',
                        fontSize: 10,
                        fontWeight: 500
                    },
                    labelBgStyle: {
                        fill: 'rgba(0,0,0,0.7)',
                        fillOpacity: 0.8
                    },
                    labelBgPadding: [4, 2] as [number, number],
                    style: {
                        stroke: isActive ? '#4CAF50' : '#444',
                        strokeWidth: isActive ? 2 : 1
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: isActive ? '#4CAF50' : '#444'
                    }
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);
    }, [state?.strategies, selectedNodeIds, setNodes, setEdges]);

    const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        if (!state?.strategies) return;
        const strategy = state.strategies.find(s => s.id === node.id);
        if (strategy && onNodeClick) {
            const isMultiSelect = event.ctrlKey || event.metaKey;
            onNodeClick(strategy, isMultiSelect);
        }
    }, [state?.strategies, onNodeClick]);

    return (
        <div className="task-graph-container" style={{
            flex: 1,
            background: 'linear-gradient(180deg, #0a0a0a 0%, #111 100%)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '12px',
            minHeight: '500px',
            position: 'relative'
        }}>
            {/* Header */}
            <div style={{
                position: 'absolute',
                top: '12px',
                left: '16px',
                zIndex: 10,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                color: '#888'
            }}>
                <span>🌳</span>
                <span>Strategy Evolution Graph</span>
                {state?.strategies && (
                    <span style={{
                        background: 'rgba(255,255,255,0.1)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px'
                    }}>
                        {state.strategies.length} nodes
                    </span>
                )}
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={handleNodeClick}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.3}
                maxZoom={1.5}
            >
                <Background color="#222" gap={20} />
                <Controls style={{ background: '#1a1a1a', borderRadius: '8px' }} />
                <MiniMap
                    nodeColor={(node) => {
                        const borderLeft = String(node.style?.borderLeft ?? '');
                        if (borderLeft.includes('#4CAF50')) return '#4CAF50';
                        if (borderLeft.includes('#f44336')) return '#f44336';
                        if (borderLeft.includes('#2196F3')) return '#2196F3';
                        return '#666';
                    }}
                    style={{
                        background: '#0a0a0a',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px'
                    }}
                />
            </ReactFlow>

            {!state && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: '#555',
                    textAlign: 'center'
                }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🌌</div>
                    <div>Waiting for Simulation...</div>
                </div>
            )}
        </div>
    );
};
