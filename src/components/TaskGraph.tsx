
import React, { useMemo, useEffect } from 'react';
import ReactFlow, {
    Background,
    Controls,
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DeepThinkState, StrategyNode } from '../types';

interface TaskGraphProps {
    state: DeepThinkState | null;
    onNodeClick?: (node: StrategyNode, ctrlKey: boolean) => void;
    selectedNodeIds?: Set<string>;  // For multi-select highlighting
}

export const TaskGraph: React.FC<TaskGraphProps> = ({ state, onNodeClick, selectedNodeIds = new Set() }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        if (!state || !state.strategies) return;

        // --- Tree Layout Logic ---
        // 1. Build Adjacency List & Find Roots
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

        // 2. BFS for Level Assignment
        const levels = new Map<string, number>();
        const queue: { id: string, level: number }[] = roots.map(r => ({ id: r, level: 0 }));
        const maxLevelWidth: number[] = []; // Count nodes per level to assign X

        while (queue.length > 0) {
            const { id, level } = queue.shift()!;
            levels.set(id, level);

            // Track width
            maxLevelWidth[level] = (maxLevelWidth[level] || 0) + 1;

            const children = childrenMap.get(id) || [];
            children.forEach(childId => queue.push({ id: childId, level: level + 1 }));
        }

        // 3. Assign Positions
        const levelCurrentX: number[] = []; // Track current X index for each level
        const newNodes: Node[] = state.strategies.map((strat) => {
            const level = levels.get(strat.id) || 0;
            const levelIdx = levelCurrentX[level] || 0;
            levelCurrentX[level] = levelIdx + 1;

            const width = maxLevelWidth[level] || 1;
            // Center buttons: total width ~ width * 250
            // x = (levelIdx - width/2) * 220
            const x = (levelIdx - width / 2) * 240;
            const y = level * 180;

            const isActive = strat.status === 'active';
            const isPruned = strat.status === 'pruned' || strat.status === 'pruned_synthesized';
            const isExpanded = strat.status === 'expanded';
            const isCompleted = strat.status === 'completed';

            let borderColor = '#666';
            if (isActive) borderColor = '#4CAF50';
            else if (isPruned) borderColor = '#f44336';
            else if (isExpanded) borderColor = '#2196F3';
            else if (isCompleted) borderColor = '#9C27B0';

            return {
                id: strat.id,
                position: { x, y },
                data: {
                    label: `${strat.name}\n(S:${strat.score?.toFixed(2) ?? '?'})`
                },
                style: {
                    background: '#1a1a1a',
                    color: '#fff',
                    border: `1px solid ${borderColor}`,
                    borderLeft: `4px solid ${borderColor}`,
                    width: 200,
                    borderRadius: '8px',
                    fontSize: '11px',
                    padding: '8px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                    opacity: isPruned ? 0.6 : 1,
                    textAlign: 'left',
                    whiteSpace: 'pre-wrap'
                },
            };
        });

        // 4. Create Edges
        const newEdges: Edge[] = [];
        state.strategies.forEach(s => {
            if (s.parent_id) {
                newEdges.push({
                    id: `e-${s.parent_id}-${s.id}`,
                    source: s.parent_id,
                    target: s.id,
                    type: 'smoothstep',
                    animated: s.status === 'active',
                    style: { stroke: '#555' }
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);

        // ⚡ Bolt: Optimize re-renders by only updating layout when strategies change,
        // ignoring other state updates like logs, iteration counts, or metrics.
    }, [state?.strategies, setNodes, setEdges]);

    return (
        <div className="task-graph-container" style={{
            flex: 1,
            background: '#111',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            minHeight: '400px',
            position: 'relative' // Needed for ReactFlow
        }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(event, node) => {
                    // Find the original StrategyNode based on ID or index
                    if (!state?.strategies) return;
                    // Our IDs are strat-${index} or strat.id
                    const strategy = state.strategies.find((s, i) =>
                        (s.id && s.id === node.id) || `strat-${i}` === node.id
                    );
                    if (strategy && onNodeClick) {
                        // Pass ctrlKey/metaKey for multi-select
                        const isMultiSelect = event.ctrlKey || event.metaKey;
                        onNodeClick(strategy, isMultiSelect);
                    }
                }}
                fitView
            >
                <Background color="#333" gap={16} />
                <Controls />
            </ReactFlow>

            {!state && (
                <div style={{
                    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                    color: '#666', pointerEvents: 'none'
                }}>
                    Waiting for Simulation Data...
                </div>
            )}
        </div>
    );
};
