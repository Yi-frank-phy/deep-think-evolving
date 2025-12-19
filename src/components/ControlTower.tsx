import React, { useState, useMemo, useCallback } from 'react';
import { Mic, Square, Settings, Play, TriangleAlert, StopCircle } from 'lucide-react';
import { ChatPanel } from './ChatPanel';
import { KnowledgePanel } from './KnowledgePanel';
import { TaskGraph } from './TaskGraph';
import { KPIDashboard } from './KPIDashboard';
import { NodeDetailModal } from './NodeDetailModal';
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
        model_name: 'gemini-2.5-flash-lite-preview-06-17',
        t_max: 2.0,
        c_explore: 1.0,
        thinking_level: 'HIGH',
        max_iterations: 10,
        entropy_threshold: 0.1,
        total_child_budget: 6,
    });
    const [showConfig, setShowConfig] = useState(false);
    const [selectedNode, setSelectedNode] = useState<StrategyNode | null>(null);
    const [selectedForSynthesize, setSelectedForSynthesize] = useState<Set<string>>(new Set());
    const [isSynthesizing, setIsSynthesizing] = useState(false);

    // Strategy name map
    const strategyNames = useMemo(() => {
        const map = new Map<string, string>();
        state?.strategies?.forEach(s => map.set(s.id, s.name));
        return map;
    }, [state?.strategies]);

    // Handle Node Click
    const handleNodeClick = useCallback((node: StrategyNode, ctrlKey: boolean) => {
        if (ctrlKey) {
            setSelectedForSynthesize(prev => {
                const newSet = new Set(prev);
                if (newSet.has(node.id)) newSet.delete(node.id);
                else newSet.add(node.id);
                return newSet;
            });
        } else {
            setSelectedNode(node);
        }
    }, []);

    // Force synthesize
    const handleForceSynthesize = async (ids: string[]) => {
        setIsSynthesizing(true);
        try {
            const response = await fetch('http://localhost:8000/api/hil/force_synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy_ids: ids })
            });
            const data = await response.json();
            if (data.status === 'ok') setSelectedForSynthesize(new Set());
        } catch (error) {
            console.error('Force synthesize failed:', error);
        } finally {
            setIsSynthesizing(false);
        }
    };

    const toggleRecording = () => isRecording ? stopRecording() : startRecording();

    const handleStart = async () => {
        if (audioBlob) clearAudio();
        startSimulation(problemInput, config);
    };

    // Helper to get thinking options based on model
    const currentModel = useMemo(() => models.find(m => m.id === config.model_name) || { id: config.model_name, thinking_levels: ['LOW', 'HIGH'] }, [models, config.model_name]);

    return (
        <div className="gemini-layout">
            {/* --- LEFT SIDEBAR: Controls & Context --- */}
            <aside className="gemini-sidebar">
                {/* Header */}
                <div className="sidebar-header">
                    <div className="brand-title">
                        <span>✨ Deep Research</span>
                    </div>
                    <div className={`status-indicator ${isConnected ? '' : 'offline'}`}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'currentColor' }} />
                        {isConnected ? 'System Online' : 'Disconnected'}
                    </div>
                </div>

                {/* Input Area */}
                <div className="input-area">
                    <textarea
                        className="gemini-input"
                        placeholder="Describe your research goal..."
                        value={problemInput}
                        onChange={(e) => setProblemInput(e.target.value)}
                        aria-label="Research Goal"
                    />
                    <div className="action-row">
                        <button
                            className={`btn-icon ${isRecording ? 'danger' : ''}`}
                            onClick={toggleRecording}
                            title="Voice Input"
                        >
                            {isRecording ? <Square size={16} /> : <Mic size={18} />}
                        </button>
                        <button
                            className={`btn-icon ${showConfig ? 'active' : ''}`}
                            onClick={() => setShowConfig(!showConfig)}
                            title="Configuration"
                            aria-expanded={showConfig}
                            aria-controls="config-card"
                        >
                            <Settings size={18} />
                        </button>
                        {simulationStatus === 'running' ? (
                            <button className="btn-primary" onClick={stopSimulation} style={{ background: '#d93025' }}>
                                <StopCircle size={18} /> Stop
                            </button>
                        ) : (
                            <button className="btn-primary" onClick={handleStart}>
                                <Play size={18} /> Start
                            </button>
                        )}
                    </div>
                </div>

                {/* Config Panel (Conditional) */}
                {showConfig && (
                    <div id="config-card" className="config-card">
                        <div className="config-group">
                            <label className="config-label">Model</label>
                            <select
                                className="config-select"
                                value={config.model_name}
                                onChange={e => setConfig({ ...config, model_name: e.target.value })}
                            >
                                {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                            </select>
                        </div>
                        <div className="config-group">
                            <label className="config-label">Thinking Depth</label>
                            <select
                                className="config-select"
                                value={config.thinking_level}
                                onChange={e => setConfig({ ...config, thinking_level: e.target.value })}
                            >
                                {currentModel.thinking_levels?.map((l: string) => (
                                    <option key={l} value={l}>{l}</option>
                                ))}
                            </select>
                        </div>
                        <div className="config-group">
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <label className="config-label">Iterations</label>
                                <span style={{ fontSize: '0.8rem' }}>{config.max_iterations}</span>
                            </div>
                            <input
                                type="range"
                                min="1" max="50"
                                style={{ width: '100%' }}
                                value={config.max_iterations}
                                onChange={e => setConfig({ ...config, max_iterations: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>
                )}

                {/* Chat / Session Log */}
                <div className="chat-container">
                    <div className="chat-header">Session Log</div>
                    <div className="chat-messages">
                        <ChatPanel />
                    </div>
                </div>

                {/* Thinking Panel (Compact) */}
                 <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                    <ThinkingPanel
                        state={state}
                        activityLog={activityLog}
                        currentAgent={currentAgent}
                        simulationStatus={simulationStatus}
                    />
                </div>
            </aside>

            {/* --- RIGHT MAIN: Research Space --- */}
            <main className="gemini-main">
                {/* KPI Overlay */}
                <div className="kpi-overlay">
                    <KPIDashboard
                        state={state}
                        currentAgent={currentAgent}
                        simulationStatus={simulationStatus}
                    />
                </div>

                {/* Visualization */}
                <div className="viz-container">
                    <TaskGraph
                        state={state}
                        onNodeClick={handleNodeClick}
                        selectedNodeIds={selectedForSynthesize}
                    />
                </div>

                {/* Force Synthesize Floating Bar */}
                {selectedForSynthesize.size > 0 && (
                    <div className="synth-bar">
                        <ForceSynthesizeBar
                            selectedIds={Array.from(selectedForSynthesize)}
                            strategyNames={strategyNames}
                            onSynthesize={handleForceSynthesize}
                            onClearSelection={() => setSelectedForSynthesize(new Set())}
                            isLoading={isSynthesizing}
                        />
                    </div>
                )}

                {/* Knowledge Drawer (Bottom) */}
                <div className="knowledge-drawer">
                    <div className="drawer-header">
                        <span>Knowledge Base</span>
                        {/* Could add expand/collapse toggle here */}
                    </div>
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                        <KnowledgePanel />
                    </div>
                </div>

                {/* Modals */}
                <NodeDetailModal
                    node={selectedNode}
                    isOpen={!!selectedNode}
                    onClose={() => setSelectedNode(null)}
                />
                <InterventionPanel
                    isOpen={hilRequest !== null}
                    request={hilRequest}
                    onSubmit={(response) => hilRequest && respondToHil(hilRequest.request_id, response)}
                    onSkip={() => hilRequest && respondToHil(hilRequest.request_id, "[Skipped]")}
                />
            </main>
        </div>
    );
};
