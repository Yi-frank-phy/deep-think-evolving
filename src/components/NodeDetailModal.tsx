
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
                width: 'min(800px, 90%)',
                maxHeight: '85vh',
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
                        <span className={`status-badge status-${node.status}`} style={{
                            fontSize: '0.8rem', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '1px'
                        }}>{node.status}</span>
                    </div>
                    <button onClick={onClose} style={{
                        background: 'transparent', border: 'none', color: 'var(--header-color)', fontSize: '1.5rem', cursor: 'pointer'
                    }}>×</button>
                </header>

                <div className="modal-body" style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
                    <section style={{ marginBottom: '2rem' }}>
                        <h3 style={{ color: 'var(--primary-color)', marginBottom: '0.5rem' }}>Rationale</h3>
                        <p style={{ lineHeight: 1.6 }}>{node.rationale}</p>
                    </section>

                    <section style={{ marginBottom: '2rem' }}>
                        <h3 style={{ color: 'var(--primary-color)', marginBottom: '0.5rem' }}>Core Assumption</h3>
                        <p style={{ lineHeight: 1.6, fontStyle: 'italic', opacity: 0.9 }}>{node.assumption}</p>
                    </section>

                    <section style={{
                        background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border-color)'
                    }}>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
                            <div style={{ flex: 1 }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--header-color)' }}>Select Expansion Model</label>
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
                                {isLoading ? 'Generating Analysis...' : 'Expand Strategy'}
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
