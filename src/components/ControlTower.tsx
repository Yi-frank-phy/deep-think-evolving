
import React, { useState, useMemo } from 'react';
import { ChatPanel } from './ChatPanel';
import { KnowledgePanel } from './KnowledgePanel';
import { TaskGraph } from './TaskGraph';
import { KPIDashboard } from './KPIDashboard';
import { NodeDetailModal } from './NodeDetailModal';
import { useSimulation } from '../hooks/useSimulation';
import { useModels } from '../hooks/useModels';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { StrategyNode } from '../types';

export const ControlTower: React.FC = () => {
    const { isConnected, state, startSimulation, stopSimulation } = useSimulation();
    const { models } = useModels();
    const { isRecording, audioBlob, startRecording, stopRecording, getBase64, clearAudio } = useAudioRecorder();
    const [problemInput, setProblemInput] = useState("How to build a dyson sphere?");
    const [config, setConfig] = useState({
        model_name: 'gemini-2.5-flash',
        t_max: 2.0,
        c_explore: 1.0,
        beam_width: 3,
        thinking_budget: 1024
    });
    const [showConfig, setShowConfig] = useState(false);
    const [selectedNode, setSelectedNode] = useState<StrategyNode | null>(null);

    // Get current model's thinking budget constraints
    const currentModel = useMemo(() => {
        return models.find(m => m.id === config.model_name) || {
            id: config.model_name,
            name: 'Unknown',
            thinking_min: 0,
            thinking_max: 24576
        };
    }, [models, config.model_name]);

    // When model changes, clamp thinking_budget to valid range
    const handleModelChange = (modelId: string) => {
        const model = models.find(m => m.id === modelId);
        if (model) {
            const clampedBudget = Math.max(
                model.thinking_min,
                Math.min(model.thinking_max, config.thinking_budget)
            );
            setConfig({
                ...config,
                model_name: modelId,
                thinking_budget: clampedBudget
            });
        } else {
            setConfig({ ...config, model_name: modelId });
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const handleStart = async () => {
        // If we have audio, we could transcribe it first or send as part of the problem
        // For now, start the simulation with the text input
        if (audioBlob) {
            clearAudio(); // Clear after use
        }
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
                    <div style={{ display: 'flex', flex: 1, gap: '0.5rem', alignItems: 'center' }}>
                        <input
                            type="text"
                            value={problemInput}
                            onChange={(e) => setProblemInput(e.target.value)}
                            placeholder={audioBlob ? "Audio recorded - add text..." : "Enter problem statement..."}
                            style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #333', background: '#222', color: '#fff' }}
                        />
                        <button
                            type="button"
                            onClick={toggleRecording}
                            title={isRecording ? "Stop recording" : "Record voice problem"}
                            className={`voice-btn ${isRecording ? 'recording' : ''}`}
                            style={{
                                background: isRecording ? '#e53935' : '#444',
                                minWidth: '42px',
                                height: '36px',
                                padding: '0 0.5rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            {isRecording ? '⏹' : '🎤'}
                        </button>
                        {audioBlob && (
                            <span style={{
                                background: '#2e7d32',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.8rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.25rem'
                            }}>
                                🎙️ Ready
                                <button
                                    type="button"
                                    onClick={clearAudio}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        color: '#fff',
                                        cursor: 'pointer',
                                        padding: '0 0.25rem'
                                    }}
                                >✕</button>
                            </span>
                        )}
                    </div>
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
                        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem'
                    }}>
                        <div className="config-item" style={{ gridColumn: 'span 2' }}>
                            <label>Model</label>
                            <select
                                value={config.model_name}
                                onChange={e => handleModelChange(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.5rem', background: '#333',
                                    border: '1px solid #555', color: '#fff', borderRadius: '4px'
                                }}
                            >
                                {models.map(m => (
                                    <option key={m.id} value={m.id}>{m.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="config-item" style={{ gridColumn: 'span 2' }}>
                            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Thinking Budget</span>
                                <span style={{ color: '#888', fontSize: '0.85rem' }}>
                                    {config.thinking_budget} tokens ({currentModel.thinking_min} - {currentModel.thinking_max})
                                </span>
                            </label>
                            <input
                                type="range"
                                min={currentModel.thinking_min}
                                max={currentModel.thinking_max}
                                step={128}
                                value={config.thinking_budget}
                                onChange={e => setConfig({ ...config, thinking_budget: parseInt(e.target.value) })}
                                style={{ width: '100%', marginTop: '0.5rem' }}
                            />
                        </div>
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
