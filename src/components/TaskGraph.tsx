
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
    onNodeClick?: (node: StrategyNode) => void;
}

export const TaskGraph: React.FC<TaskGraphProps> = ({ state, onNodeClick }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        if (!state || !state.strategies) return;

        // Transform Strategies to Nodes
        // Layout Logic: Grid based on index/status
        // Active on top row, Pruned below.

        const newNodes: Node[] = state.strategies.map((strat, index) => {
            const isActive = strat.status === 'active';
            const row = isActive ? 0 : 1;
            const col = index % 5; // 5 per row for naive grid
            const x = col * 250;
            const y = row * 150 + (isActive ? 0 : Math.floor(index / 5) * 150 + 200);

            return {
                id: strat.id || `strat-${index}`,
                position: { x, y },
                data: {
                    label: strat.name + `\n(${strat.score?.toFixed(2)})`
                },
                style: {
                    background: isActive ? '#1a1a1a' : '#2a1a1a',
                    color: '#fff',
                    border: isActive ? '1px solid #4CAF50' : '1px solid #f44336',
                    width: 200,
                    borderRadius: '8px',
                    fontSize: '12px',
                    padding: '10px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                    transition: 'transform 0.2s',
                    zIndex: 10
                },
                type: 'default',
                // ReactFlow passes the specific node object to event handlers, 
                // but we need the StrategyNode data. We can pass it via data or handle generic lookup.
                // Simpler: Use the StrategyNode directly if possible, or mapping.
                // We'll attach the handler to the node properties in a way ReactFlow supports 
                // but ReactFlow 'onNodeClick' is a prop on the Flow component, not individual nodes.
            };
        });

        // Edges: Since we don't have parent_id yet, we can't draw real edges.
        // We can draw implicit edges if 'trajectory' implies it, or just leave disconnected for now.
        // Let's connect index i to i+1 just for visual structure if we assume sequential generation? 
        // No, that's misleading. 
        // Better: Connect "Architect" (Virtual Root) to all Gen 0.
        // For now, no edges, just cards.

        setNodes(newNodes);
        setEdges([]);

    }, [state, setNodes, setEdges]);

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
                onNodeClick={(_, node) => {
                    // Find the original StrategyNode based on ID or index
                    if (!state?.strategies) return;
                    // Our IDs are strat-${index} or strat.id
                    const strategy = state.strategies.find((s, i) =>
                        (s.id && s.id === node.id) || `strat-${i}` === node.id
                    );
                    if (strategy && onNodeClick) {
                        onNodeClick(strategy);
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
