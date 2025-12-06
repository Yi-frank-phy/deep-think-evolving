
import React, { useState } from 'react';
import { ChatPanel } from './ChatPanel';
import { KnowledgePanel } from './KnowledgePanel';
import { TaskGraph } from './TaskGraph';
import { KPIDashboard } from './KPIDashboard';
import { NodeDetailModal } from './NodeDetailModal';
import { useSimulation } from '../hooks/useSimulation';
import { StrategyNode } from '../types';

export const ControlTower: React.FC = () => {
    const { isConnected, state, startSimulation, stopSimulation } = useSimulation();
    const [problemInput, setProblemInput] = useState("How to build a dyson sphere?");
    const [config, setConfig] = useState({
        t_max: 2.0,
        c_explore: 1.0,
        beam_width: 3,
        thinking_budget: 1024
    });
    const [showConfig, setShowConfig] = useState(false);
    const [selectedNode, setSelectedNode] = useState<StrategyNode | null>(null);

    const handleStart = () => {
        startSimulation(problemInput, config);
    };

    return (
        <div id="dashboard" className="control-tower">
            <header className="dashboard-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <h1>Project Prometheus: Control Tower</h1>
                        <span className={`status-badge ${isConnected ? 'online' : 'offline'}`}
                            style={{
                                background: isConnected ? 'var(--success-color)' : 'var(--error-color)',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.8rem'
                            }}>
                            {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
                        </span>
                    </div>
                </div>

                <div className="simulation-controls" style={{
                    display: 'flex', flexWrap: 'wrap', gap: '0.5rem',
                    background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px'
                }}>
                    <input
                        type="text"
                        value={problemInput}
                        onChange={(e) => setProblemInput(e.target.value)}
                        placeholder="Enter problem statement..."
                        style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #333', background: '#222', color: '#fff' }}
                    />
                    <button onClick={() => setShowConfig(!showConfig)} style={{ background: '#444' }}>
                        {showConfig ? 'Hide Config' : 'Config'}
                    </button>
                    <button onClick={handleStart} className="primary">Start Mission</button>
                    <button onClick={stopSimulation} className="danger">Abort</button>
                </div>

                {showConfig && (
                    <div className="config-panel" style={{
                        marginTop: '1rem', padding: '1rem', background: '#2a2a2a',
                        borderRadius: '8px', border: '1px solid #444',
                        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem'
                    }}>
                        <div className="config-item">
                            <label>Max Temperature (T_max)</label>
                            <input type="number" step="0.1" value={config.t_max}
                                onChange={e => setConfig({ ...config, t_max: parseFloat(e.target.value) })}
                                style={{ width: '100%', padding: '0.25rem', background: '#333', border: '1px solid #555', color: '#fff' }} />
                        </div>
                        <div className="config-item">
                            <label>Exploration Constant (C)</label>
                            <input type="number" step="0.1" value={config.c_explore}
                                onChange={e => setConfig({ ...config, c_explore: parseFloat(e.target.value) })}
                                style={{ width: '100%', padding: '0.25rem', background: '#333', border: '1px solid #555', color: '#fff' }} />
                        </div>
                        <div className="config-item">
                            <label>Beam Width (k)</label>
                            <input type="number" step="1" value={config.beam_width}
                                onChange={e => setConfig({ ...config, beam_width: parseInt(e.target.value) })}
                                style={{ width: '100%', padding: '0.25rem', background: '#333', border: '1px solid #555', color: '#fff' }} />
                        </div>
                        <div className="config-item">
                            <label>Thinking Budget</label>
                            <input type="number" step="128" value={config.thinking_budget}
                                onChange={e => setConfig({ ...config, thinking_budget: parseInt(e.target.value) })}
                                style={{ width: '100%', padding: '0.25rem', background: '#333', border: '1px solid #555', color: '#fff' }} />
                        </div>
                    </div>
                )}
            </header>

            <main className="dashboard-main">
                <div className="left-panel">
                    <KPIDashboard state={state} />
                    <TaskGraph state={state} onNodeClick={setSelectedNode} />
                    <ChatPanel />
                </div>

                <KnowledgePanel />
            </main>

            <NodeDetailModal
                node={selectedNode}
                isOpen={!!selectedNode}
                onClose={() => setSelectedNode(null)}
            />
        </div>
    );
};
