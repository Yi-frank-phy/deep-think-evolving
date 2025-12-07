import React, { useRef, useEffect } from 'react';
import { AgentActivity, AgentPhase } from '../types';

interface ActivityPanelProps {
    activityLog: AgentActivity[];
    currentAgent: AgentPhase | null;
    simulationStatus: 'idle' | 'running' | 'completed' | 'error';
}

const AGENT_COLORS: Record<AgentPhase, string> = {
    researcher: '#8B5CF6',      // Purple
    distiller: '#06B6D4',       // Cyan
    architect: '#F59E0B',       // Amber
    distiller_for_judge: '#6366F1', // Indigo
    judge: '#EF4444',           // Red
    evolution: '#10B981',       // Emerald
    propagation: '#3B82F6',     // Blue
};

const AGENT_ICONS: Record<AgentPhase, string> = {
    researcher: '🔍',
    distiller: '📝',
    architect: '🏗️',
    distiller_for_judge: '📋',
    judge: '⚖️',
    evolution: '🧬',
    propagation: '🌱',
};

export const ActivityPanel: React.FC<ActivityPanelProps> = ({
    activityLog,
    currentAgent,
    simulationStatus
}) => {
    const logRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new entries
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [activityLog]);

    const formatTime = (timestamp: string) => {
        return new Date(timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    return (
        <section className="activity-panel" style={{
            background: 'var(--surface-color)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '200px',
            maxHeight: '300px'
        }}>
            {/* Header */}
            <div style={{
                padding: '0.75rem 1rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(255, 255, 255, 0.02)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.1rem' }}>📊</span>
                    <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>
                        AI 工作进度
                    </h3>
                </div>

                {/* Status indicator */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.8rem'
                }}>
                    {simulationStatus === 'running' && currentAgent && (
                        <>
                            <span className="pulse-dot" style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: AGENT_COLORS[currentAgent],
                                animation: 'pulse 1.5s ease-in-out infinite'
                            }} />
                            <span style={{ color: AGENT_COLORS[currentAgent] }}>
                                {AGENT_ICONS[currentAgent]} 工作中
                            </span>
                        </>
                    )}
                    {simulationStatus === 'completed' && (
                        <span style={{ color: 'var(--success-color)' }}>✅ 完成</span>
                    )}
                    {simulationStatus === 'error' && (
                        <span style={{ color: 'var(--error-color)' }}>❌ 错误</span>
                    )}
                    {simulationStatus === 'idle' && (
                        <span style={{ color: 'var(--text-muted)' }}>⏸️ 待命</span>
                    )}
                </div>
            </div>

            {/* Activity Log */}
            <div
                ref={logRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '0.5rem',
                    fontSize: '0.8rem'
                }}
            >
                {activityLog.length === 0 ? (
                    <div style={{
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-muted)',
                        fontStyle: 'italic'
                    }}>
                        点击 "Start Mission" 开始模拟
                    </div>
                ) : (
                    <div>
                        {activityLog.map((activity, index) => {
                            const agentColor = AGENT_COLORS[activity.agent] || '#888';
                            const agentIcon = AGENT_ICONS[activity.agent] || '❓';
                            return (
                                <div key={index} style={{
                                    padding: '0.5rem 0.75rem',
                                    marginBottom: '0.25rem',
                                    borderRadius: '4px',
                                    background: activity.type === 'start' ? `${agentColor}20` : 'rgba(255,255,255,0.02)',
                                    borderLeft: `3px solid ${agentColor}`
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                        <span style={{ opacity: 0.5, fontSize: '0.75rem' }}>
                                            {formatTime(activity.timestamp)}
                                        </span>
                                        <span>{agentIcon}</span>
                                        <span style={{ color: activity.type === 'complete' ? '#888' : '#fff' }}>
                                            {activity.message}
                                        </span>
                                        {activity.duration_ms && (
                                            <span style={{
                                                marginLeft: 'auto',
                                                fontSize: '0.7rem',
                                                color: '#888',
                                                background: 'rgba(255,255,255,0.1)',
                                                padding: '0.1rem 0.4rem',
                                                borderRadius: '3px'
                                            }}>
                                                {(activity.duration_ms / 1000).toFixed(1)}s
                                            </span>
                                        )}
                                    </div>
                                    {activity.detail && (
                                        <div style={{
                                            marginTop: '0.25rem',
                                            paddingLeft: '2rem',
                                            fontSize: '0.75rem',
                                            color: '#888',
                                            lineHeight: 1.4
                                        }}>
                                            {activity.detail}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <style>{`
                @keyframes pulse {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.5; transform: scale(1.2); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateX(-10px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>
        </section>
    );
};
