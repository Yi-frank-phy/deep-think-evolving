/**
 * InterventionPanel - Human-in-the-Loop 交互面板
 * 
 * 当 AI Agent 需要人类输入时，此面板会弹出显示问题并接收用户回复。
 */

import React, { useState, useEffect, useRef } from 'react';
import type { HilRequest, AgentPhase } from '../types';

// Agent 显示信息
const AGENT_INFO: Record<AgentPhase, { icon: string; name: string; color: string }> = {
    researcher: { icon: '🔍', name: 'Researcher', color: '#4ECDC4' },
    distiller: { icon: '🧪', name: 'Distiller', color: '#45B7D1' },
    architect: { icon: '🏗️', name: 'Architect', color: '#96CEB4' },
    distiller_for_judge: { icon: '📋', name: 'Context Prep', color: '#FFEAA7' },
    judge: { icon: '⚖️', name: 'Judge', color: '#DDA0DD' },
    evolution: { icon: '🧬', name: 'Evolution', color: '#98D8C8' },
    propagation: { icon: '🌱', name: 'Propagation', color: '#F7DC6F' }
};

interface InterventionPanelProps {
    isOpen: boolean;
    request: HilRequest | null;
    onSubmit: (response: string) => void;
    onSkip: () => void;
    onDismiss?: () => void;
}

export const InterventionPanel: React.FC<InterventionPanelProps> = ({
    isOpen,
    request,
    onSubmit,
    onSkip,
    onDismiss
}) => {
    const [response, setResponse] = useState('');
    const [timeRemaining, setTimeRemaining] = useState(60);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // 重置状态当新请求到来
    useEffect(() => {
        if (request) {
            setResponse('');
            setTimeRemaining(request.timeout_seconds);
        }
    }, [request?.request_id]);

    // 倒计时
    useEffect(() => {
        if (!isOpen || !request) return;

        const timer = setInterval(() => {
            setTimeRemaining(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [isOpen, request?.request_id]);

    // 自动聚焦文本框
    useEffect(() => {
        if (isOpen && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [isOpen]);

    if (!isOpen || !request) return null;

    const agentInfo = AGENT_INFO[request.agent] || { icon: '❓', name: request.agent, color: '#888' };
    const urgencyColor = timeRemaining <= 10 ? '#ff6b6b' : timeRemaining <= 30 ? '#feca57' : '#1dd1a1';

    const handleSubmit = () => {
        if (response.trim()) {
            onSubmit(response.trim());
            setResponse('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            backdropFilter: 'blur(4px)'
        }}>
            <div style={{
                background: 'var(--surface-color, #1e1e2e)',
                border: `2px solid ${agentInfo.color}`,
                borderRadius: '12px',
                padding: '1.5rem',
                maxWidth: '600px',
                width: '90%',
                boxShadow: `0 0 30px ${agentInfo.color}40`,
                animation: 'fadeIn 0.3s ease-out'
            }}>
                {/* Header */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '1rem',
                    paddingBottom: '0.75rem',
                    borderBottom: '1px solid rgba(255,255,255,0.1)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '1.5rem' }}>{agentInfo.icon}</span>
                        <div>
                            <div style={{ fontWeight: 'bold', color: agentInfo.color }}>
                                {agentInfo.name} 需要您的输入
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#888' }}>
                                Human-in-the-Loop 请求
                            </div>
                        </div>
                    </div>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.25rem 0.75rem',
                        background: `${urgencyColor}20`,
                        borderRadius: '20px',
                        color: urgencyColor,
                        fontWeight: 'bold',
                        fontSize: '0.9rem'
                    }}>
                        ⏱️ {timeRemaining}s
                    </div>
                </div>

                {/* Question */}
                <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '1rem',
                    borderRadius: '8px',
                    marginBottom: '1rem'
                }}>
                    <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '0.5rem' }}>
                        问题:
                    </div>
                    <div style={{ fontSize: '1rem', lineHeight: 1.6 }}>
                        {request.question}
                    </div>
                </div>

                {/* Context (if provided) */}
                {request.context && (
                    <details style={{
                        marginBottom: '1rem',
                        background: 'rgba(255,255,255,0.03)',
                        padding: '0.75rem',
                        borderRadius: '8px'
                    }}>
                        <summary style={{ cursor: 'pointer', color: '#888', fontSize: '0.85rem' }}>
                            📋 查看上下文
                        </summary>
                        <div style={{
                            marginTop: '0.5rem',
                            fontSize: '0.85rem',
                            color: '#aaa',
                            whiteSpace: 'pre-wrap'
                        }}>
                            {request.context}
                        </div>
                    </details>
                )}

                {/* Response Input */}
                <div style={{ marginBottom: '1rem' }}>
                    <label style={{ fontSize: '0.85rem', color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                        您的回复: (Ctrl+Enter 提交)
                    </label>
                    <textarea
                        ref={textareaRef}
                        value={response}
                        onChange={e => setResponse(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="输入您的回复..."
                        style={{
                            width: '100%',
                            minHeight: '100px',
                            padding: '0.75rem',
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px',
                            color: '#fff',
                            fontSize: '0.95rem',
                            resize: 'vertical',
                            outline: 'none'
                        }}
                    />
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                        onClick={onSkip}
                        style={{
                            padding: '0.6rem 1.2rem',
                            background: 'transparent',
                            border: '1px solid #666',
                            borderRadius: '6px',
                            color: '#888',
                            cursor: 'pointer',
                            fontSize: '0.9rem'
                        }}
                    >
                        跳过 (让 AI 自己决定)
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={!response.trim()}
                        style={{
                            padding: '0.6rem 1.5rem',
                            background: response.trim() ? agentInfo.color : '#444',
                            border: 'none',
                            borderRadius: '6px',
                            color: response.trim() ? '#000' : '#666',
                            cursor: response.trim() ? 'pointer' : 'not-allowed',
                            fontSize: '0.9rem',
                            fontWeight: 'bold'
                        }}
                    >
                        提交回复
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: scale(0.95); }
                    to { opacity: 1; transform: scale(1); }
                }
            `}</style>
        </div>
    );
};
