
import React, { useState, useMemo, useCallback } from 'react';
import { Mic, Square, Settings, Play, TriangleAlert } from 'lucide-react';
import { ChatPanel } from './ChatPanel';
import { KnowledgePanel } from './KnowledgePanel';
import { TaskGraph } from './TaskGraph';
import { KPIDashboard } from './KPIDashboard';
import { NodeDetailModal } from './NodeDetailModal';
import { ActivityPanel } from './ActivityPanel';
import { InterventionPanel } from './InterventionPanel';
import { ForceSynthesizeBar } from './ForceSynthesizeBar';
import { ThinkingPanel } from './ThinkingPanel';
import { useSimulation } from '../hooks/useSimulation';
import { useModels } from '../hooks/useModels';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { StrategyNode } from '../types';

export const ControlTower: React.FC = () => {
    const { isConnected, state, activityLog, currentAgent, simulationStatus, hilRequest, startSimulation, stopSimulation, respondToHil } = useSimulation();
    const { models } = useModels();
    const { isRecording, audioBlob, startRecording, stopRecording, getBase64, clearAudio } = useAudioRecorder();
    const [problemInput, setProblemInput] = useState("");
    const [config, setConfig] = useState({
        model_name: 'gemini-2.5-flash-lite-preview-06-17',  // Default to affordable model
        t_max: 2.0,
        c_explore: 1.0,
        thinking_level: 'HIGH',  // Thinking depth: MINIMAL, LOW, MEDIUM, HIGH
        max_iterations: 10,
        entropy_threshold: 0.1,
        total_child_budget: 6,
        // NOTE: LLM temperature is always 1.0 (Logic Manifold Integrity)
        // System temperature τ controls resource allocation only
    });
    const [showConfig, setShowConfig] = useState(false);
    const [selectedNode, setSelectedNode] = useState<StrategyNode | null>(null);

    // T-052: Multi-select state for force synthesize
    const [selectedForSynthesize, setSelectedForSynthesize] = useState<Set<string>>(new Set());
    const [isSynthesizing, setIsSynthesizing] = useState(false);

    // Strategy name map for display
    const strategyNames = useMemo(() => {
        const map = new Map<string, string>();
        state?.strategies?.forEach(s => map.set(s.id, s.name));
        return map;
    }, [state?.strategies]);

    // Handle Ctrl+Click for multi-select
    const handleNodeClick = useCallback((node: StrategyNode, ctrlKey: boolean) => {
        if (ctrlKey) {
            // Multi-select mode
            setSelectedForSynthesize(prev => {
                const newSet = new Set(prev);
                if (newSet.has(node.id)) {
                    newSet.delete(node.id);
                } else {
                    newSet.add(node.id);
                }
                return newSet;
            });
        } else {
            // Single click - open detail modal
            setSelectedNode(node);
        }
    }, []);

    // Force synthesize handler
    const handleForceSynthesize = async (ids: string[]) => {
        setIsSynthesizing(true);
        try {
            const response = await fetch('http://localhost:8000/api/hil/force_synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy_ids: ids })
            });
            const data = await response.json();
            if (data.status === 'ok') {
                setSelectedForSynthesize(new Set()); // Clear selection
            }
        } catch (error) {
            console.error('Force synthesize failed:', error);
        } finally {
            setIsSynthesizing(false);
        }
    };

    // Get current model's supported thinking levels
    const currentModel = useMemo(() => {
        return models.find(m => m.id === config.model_name) || {
            id: config.model_name,
            name: 'Unknown',
            thinking_levels: ['LOW', 'HIGH']
        };
    }, [models, config.model_name]);

    // When model changes, ensure thinking_level is valid for new model
    const handleModelChange = (modelId: string) => {
        const model = models.find(m => m.id === modelId);
        if (model) {
            // If current level not supported by new model, default to HIGH
            const validLevel = model.thinking_levels?.includes(config.thinking_level)
                ? config.thinking_level
                : 'HIGH';
            setConfig({
                ...config,
                model_name: modelId,
                thinking_level: validLevel
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
                                color: isConnected ? 'var(--success-color)' : 'var(--error-color)',
                                padding: '0.25rem 0.5rem',
                                border: '1px solid currentColor',
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.8rem',
                                fontWeight: 500
                            }}>
                            {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
                        </span>
                    </div>
                </div>

                <div className="simulation-controls">
                    <div style={{ display: 'flex', flex: 1, gap: '0.5rem', alignItems: 'center' }}>
                        <input
                            type="text"
                            id="problem-input"
                            aria-label="Problem statement"
                            className="control-input"
                            value={problemInput}
                            onChange={(e) => setProblemInput(e.target.value)}
                            placeholder={audioBlob ? "Audio recorded - add text..." : "Enter problem statement..."}
                        />
                        <button
                            type="button"
                            onClick={toggleRecording}
                            title={isRecording ? "Stop recording" : "Record voice problem"}
                            aria-label={isRecording ? "Stop recording" : "Record voice problem"}
                            className={`control-btn ${isRecording ? 'danger' : ''}`}
                            style={{ minWidth: '42px', padding: '0', justifyContent: 'center' }}
                        >
                            {isRecording ? <Square size={18} /> : <Mic size={18} />}
                        </button>
                    </div>
                    <button
                        className={`control-btn ${showConfig ? 'active' : ''}`}
                        onClick={() => setShowConfig(!showConfig)}
                        aria-expanded={showConfig}
                        aria-controls="config-panel"
                    >
                        <Settings size={16} />
                        Config
                    </button>
                    <button onClick={handleStart} className="control-btn primary">
                        <Play size={16} />
                        Start Mission
                    </button>
                    <button onClick={stopSimulation} className="control-btn danger">
                        <TriangleAlert size={16} />
                        Abort
                    </button>
                </div>

                {showConfig && (
                    <div id="config-panel" className="config-panel">
                        {/* 1. Model Selection */}
                        <div className="config-section">
                            <h4>Model & Compute</h4>
                            <div className="config-item">
                                <label htmlFor="config-model">Core Model</label>
                                <select
                                    id="config-model"
                                    className="control-input"
                                    value={config.model_name}
                                    onChange={e => handleModelChange(e.target.value)}
                                >
                                    {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                                </select>
                            </div>
                            <div className="config-item">
                                <label htmlFor="config-thinking-level">Thinking Level</label>
                                <select
                                    id="config-thinking-level"
                                    className="control-input"
                                    value={config.thinking_level}
                                    onChange={e => setConfig({ ...config, thinking_level: e.target.value })}
                                >
                                    {(currentModel.thinking_levels || ['LOW', 'HIGH']).map((level: string) => (
                                        <option key={level} value={level}>
                                            {level === 'MINIMAL' ? '⚡ Minimal (Fastest)' :
                                                level === 'LOW' ? '🟢 Low' :
                                                    level === 'MEDIUM' ? '🟡 Medium' :
                                                        '🔴 High (Deep Reasoning)'}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* 2. Evolution Engine */}
                        <div className="config-section">
                            <h4>Evolution Engine</h4>
                            <div className="config-item">
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <label htmlFor="config-iterations">Max Iterations</label>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-color)' }}>{config.max_iterations}</span>
                                </div>
                                <input
                                    id="config-iterations"
                                    type="range"
                                    min="1"
                                    max="50"
                                    value={config.max_iterations}
                                    onChange={e => setConfig({ ...config, max_iterations: parseInt(e.target.value) })}
                                    style={{ width: '100%', accentColor: 'var(--primary-color)' }} />
                            </div>
                            <div className="config-item">
                                <label htmlFor="config-entropy">Entropy Threshold</label>
                                <input
                                    id="config-entropy"
                                    type="number"
                                    step="0.01"
                                    className="control-input"
                                    value={config.entropy_threshold}
                                    onChange={e => setConfig({ ...config, entropy_threshold: parseFloat(e.target.value) })}
                                />
                            </div>
                            <div className="config-item">
                                <label htmlFor="config-child-budget">Child Budget</label>
                                <input
                                    id="config-child-budget"
                                    type="number"
                                    min="2"
                                    max="20"
                                    className="control-input"
                                    value={config.total_child_budget}
                                    onChange={e => setConfig({ ...config, total_child_budget: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>

                        {/* 3. Physics & Temperature */}
                        <div className="config-section">
                            <h4>Physics & Temp</h4>
                            <div className="config-item">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <label htmlFor="config-temp" style={{ borderBottom: '1px dotted var(--text-muted)', cursor: 'help' }}>Max Temp (T_max)</label>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-color)' }}>{config.t_max.toFixed(1)}</span>
                                </div>
                                <input
                                    id="config-temp"
                                    type="range"
                                    min="0.0"
                                    max="2.0"
                                    step="0.1"
                                    value={config.t_max}
                                    onChange={e => setConfig({ ...config, t_max: parseFloat(e.target.value) })}
                                    style={{ width: '100%', marginTop: '0.5rem', accentColor: 'var(--primary-color)' }}
                                />
                            </div>
                            <div className="config-item">
                                <label htmlFor="config-explore">Exploration (C)</label>
                                <input
                                    id="config-explore"
                                    type="number"
                                    step="0.1"
                                    className="control-input"
                                    value={config.c_explore}
                                    onChange={e => setConfig({ ...config, c_explore: parseFloat(e.target.value) })}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </header>

            <main className="dashboard-main">
                {/* Left: Thinking Panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
                    <ThinkingPanel
                        state={state}
                        activityLog={activityLog}
                        currentAgent={currentAgent}
                        simulationStatus={simulationStatus}
                    />
                </div>

                {/* Center: TaskGraph */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
                    <TaskGraph
                        state={state}
                        onNodeClick={handleNodeClick}
                        selectedNodeIds={selectedForSynthesize}
                    />
                    <KPIDashboard
                        state={state}
                        currentAgent={currentAgent}
                        simulationStatus={simulationStatus}
                    />
                </div>

                {/* Right: Knowledge & Chat */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
                    <KnowledgePanel />
                    <ChatPanel />
                </div>
            </main>

            <NodeDetailModal
                node={selectedNode}
                isOpen={!!selectedNode}
                onClose={() => setSelectedNode(null)}
            />

            <ForceSynthesizeBar
                selectedIds={Array.from(selectedForSynthesize)}
                strategyNames={strategyNames}
                onSynthesize={handleForceSynthesize}
                onClearSelection={() => setSelectedForSynthesize(new Set())}
                isLoading={isSynthesizing}
            />

            <InterventionPanel
                isOpen={hilRequest !== null}
                request={hilRequest}
                onSubmit={(response) => {
                    if (hilRequest) {
                        respondToHil(hilRequest.request_id, response);
                    }
                }}
                onSkip={() => {
                    if (hilRequest) {
                        respondToHil(hilRequest.request_id, "[Skipped by user - continue autonomously]");
                    }
                }}
            />
        </div >
    );
};
