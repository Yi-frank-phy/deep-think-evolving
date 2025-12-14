
import React, { useState } from 'react';
import { StrategyNode } from '../types';

interface NodeDetailModalProps {
    node: StrategyNode | null;
    isOpen: boolean;
    onClose: () => void;
}

const AVAILABLE_MODELS = [
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Fast)' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Reasoning)' },
    { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (Experimental)' }
];

// Collapsible section component
const CollapsibleSection: React.FC<{
    title: string;
    icon: string;
    defaultOpen?: boolean;
    children: React.ReactNode;
}> = ({ title, icon, defaultOpen = false, children }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    return (
        <section style={{ marginBottom: '1rem' }}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.05)',
                    border: '1px solid var(--border-color)', borderRadius: '8px',
                    color: 'var(--header-color)', cursor: 'pointer', fontSize: '1rem',
                    justifyContent: 'space-between'
                }}
            >
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>{icon}</span>
                    <span>{title}</span>
                </span>
                <span style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>▼</span>
            </button>
            {isOpen && (
                <div style={{
                    padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0 0 8px 8px',
                    border: '1px solid var(--border-color)', borderTop: 'none',
                    whiteSpace: 'pre-wrap', lineHeight: 1.7, maxHeight: '400px', overflowY: 'auto'
                }}>
                    {children}
                </div>
            )}
        </section>
    );
};

export const NodeDetailModal: React.FC<NodeDetailModalProps> = ({ node, isOpen, onClose }) => {
    const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0].value);
    const [expandedContent, setExpandedContent] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen || !node) return null;

    const handleExpand = async () => {
        setIsLoading(true);
        setExpandedContent(null);
        try {
            const response = await fetch('http://localhost:8000/api/expand_node', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rationale: node.rationale,
                    context: `Node Name: ${node.name}\nInitial Assumption: ${node.assumption}`,
                    model_name: selectedModel
                })
            });
            const data = await response.json();
            setExpandedContent(data.expanded_content);
        } catch (error) {
            setExpandedContent("Error expanding content. Please check backend connection.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose} style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
            <div className="modal-content" onClick={e => e.stopPropagation()} style={{
                background: 'var(--panel-background)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                width: 'min(900px, 95%)',
                maxHeight: '90vh',
                display: 'flex', flexDirection: 'column',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                color: 'var(--text-color)'
            }}>
                <header style={{
                    padding: '1.5rem', borderBottom: '1px solid var(--border-color)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                }}>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#fff' }}>{node.name}</h2>
                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.85rem' }}>
                            <span className={`status-badge status-${node.status}`} style={{
                                textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.8
                            }}>{node.status}</span>
                            {node.ucb_score !== undefined && (
                                <span style={{ color: 'var(--primary-color)' }}>UCB: {node.ucb_score.toFixed(4)}</span>
                            )}
                            {node.child_quota !== undefined && (
                                <span style={{ color: '#10B981' }}>Quota: {node.child_quota}</span>
                            )}
                        </div>
                    </div>
                    <button onClick={onClose} style={{
                        background: 'transparent', border: 'none', color: 'var(--header-color)', fontSize: '1.5rem', cursor: 'pointer'
                    }}>×</button>
                </header>

                <div className="modal-body" style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
                    {/* Basic Info */}
                    <section style={{ marginBottom: '1.5rem' }}>
                        <h3 style={{ color: 'var(--primary-color)', marginBottom: '0.5rem' }}>📋 Rationale</h3>
                        <p style={{ lineHeight: 1.6, margin: 0 }}>{node.rationale}</p>
                    </section>

                    <section style={{ marginBottom: '1.5rem' }}>
                        <h3 style={{ color: 'var(--primary-color)', marginBottom: '0.5rem' }}>💡 Core Assumption</h3>
                        <p style={{ lineHeight: 1.6, fontStyle: 'italic', opacity: 0.9, margin: 0 }}>{node.assumption}</p>
                    </section>

                    {/* Thinking Summary - Collapsible (T-050) */}
                    {node.thinking_summary && (
                        <CollapsibleSection title="Gemini 思维链摘要" icon="🧠" defaultOpen={true}>
                            {node.thinking_summary}
                        </CollapsibleSection>
                    )}

                    {/* Full Response - Collapsible (T-050) */}
                    {node.full_response && (
                        <CollapsibleSection title="完整 AI 回答" icon="💬" defaultOpen={false}>
                            {node.full_response}
                        </CollapsibleSection>
                    )}

                    {/* Execution Trajectory - Collapsible */}
                    {node.trajectory && node.trajectory.length > 0 && (
                        <CollapsibleSection title={`执行轨迹 (${node.trajectory.length} 步)`} icon="📜" defaultOpen={false}>
                            {node.trajectory.map((step, i) => (
                                <div key={i} style={{
                                    padding: '0.5rem', marginBottom: '0.5rem',
                                    background: 'rgba(255,255,255,0.03)', borderRadius: '4px',
                                    borderLeft: '3px solid var(--primary-color)'
                                }}>
                                    <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>#{i + 1}</span>
                                    {step}
                                </div>
                            ))}
                        </CollapsibleSection>
                    )}

                    {/* Expand Strategy Section */}
                    <section style={{
                        background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '8px',
                        border: '1px solid var(--border-color)', marginTop: '1rem'
                    }}>
                        <h3 style={{ color: 'var(--primary-color)', marginBottom: '1rem' }}>🔍 深度展开策略</h3>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
                            <div style={{ flex: 1 }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--header-color)' }}>选择模型</label>
                                <select
                                    value={selectedModel}
                                    onChange={(e) => setSelectedModel(e.target.value)}
                                    style={{
                                        width: '100%', padding: '0.6rem', background: '#1a1a2e', color: '#fff',
                                        border: '1px solid var(--border-color)', borderRadius: '6px'
                                    }}
                                >
                                    {AVAILABLE_MODELS.map(m => (
                                        <option key={m.value} value={m.value}>{m.label}</option>
                                    ))}
                                </select>
                            </div>
                            <button
                                onClick={handleExpand}
                                disabled={isLoading}
                                className="primary-glow"
                            >
                                {isLoading ? '生成中...' : '展开策略'}
                            </button>
                        </div>

                        {expandedContent && (
                            <div className="expansion-result markdown-body" style={{
                                marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)',
                                whiteSpace: 'pre-wrap', lineHeight: 1.7
                            }}>
                                {expandedContent}
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    );
};
