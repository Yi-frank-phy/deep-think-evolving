/**
 * ThinkingPanel - Gemini Deep Research 风格的思维面板
 * 
 * 侧边栏实时显示 AI 推理过程，支持展开/折叠。
 * 设计参考 Google Gemini Deep Research 的 Thinking Panel。
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { ChevronDown, ChevronRight, Brain, Loader2, CheckCircle2 } from 'lucide-react';
import { DeepThinkState, AgentActivity, AgentPhase } from '../types';

interface ThinkingPanelProps {
    state: DeepThinkState | null;
    activityLog: AgentActivity[];
    currentAgent: AgentPhase | null;
    simulationStatus: 'idle' | 'running' | 'completed' | 'error' | 'awaiting_human';
}

const AGENT_LABELS: Record<AgentPhase, string> = {
    task_decomposer: '任务分解',
    researcher: '信息收集',
    strategy_generator: '策略生成',
    distiller: '上下文蒸馏',
    architect: '战略规划',
    architect_scheduler: '执行调度',
    distiller_for_judge: '评估准备',
    executor: '策略执行',
    judge: '可行性评估',
    evolution: '演化迭代',
    propagation: '知识传播'
};

export const ThinkingPanel: React.FC<ThinkingPanelProps> = ({
    state,
    activityLog,
    currentAgent,
    simulationStatus
}) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set(['understanding', 'evaluation', 'execution']));
    const [expandedIterations, setExpandedIterations] = useState<Set<number>>(new Set());
    const scrollRef = useRef<HTMLDivElement>(null);

    // 自动滚动到底部
    useEffect(() => {
        if (scrollRef.current && simulationStatus === 'running') {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [activityLog, simulationStatus]);

    const toggleIteration = (iteration: number) => {
        setExpandedIterations(prev => {
            const newSet = new Set(prev);
            if (newSet.has(iteration)) {
                newSet.delete(iteration);
            } else {
                newSet.add(iteration);
            }
            return newSet;
        });
    };

    // 按迭代分组活动 - Memoized to prevent re-grouping on every render
    const iterationGroups = useMemo(() => {
        const groups: Map<number, AgentActivity[]> = new Map();
        let currentIteration = 0;

        activityLog.forEach(activity => {
            if (activity.agent === 'evolution') {
                currentIteration++;
            }
            if (!groups.has(currentIteration)) {
                groups.set(currentIteration, []);
            }
            groups.get(currentIteration)?.push(activity);
        });

        return groups;
    }, [activityLog]);

    const currentIteration = state?.iteration_count || 0;

    // 策略摘要统计 - Memoized
    const strategyStats = useMemo(() => {
        if (!state?.strategies) return null;
        return {
            activeCount: state.strategies.filter(s => s.status === 'active').length,
            prunedCount: state.strategies.filter(s => s.status === 'pruned' || s.status === 'pruned_synthesized').length,
            total: state.strategies.length
        };
    }, [state?.strategies]);

    // 高分策略计算 - Memoized
    const topStrategies = useMemo(() => {
        if (!state?.strategies) return [];
        return state.strategies
            .filter(s => s.status === 'active')
            .sort((a, b) => (b.ucb_score || b.score || 0) - (a.ucb_score || a.score || 0))
            .slice(0, 3);
    }, [state?.strategies]);

    // 渲染策略摘要
    const renderStrategySummary = () => {
        if (!strategyStats) return null;

        return (
            <div style={{
                padding: '12px',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                marginBottom: '12px'
            }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                    策略空间
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
                    <span style={{ color: '#4CAF50' }}>🟢 活跃: {strategyStats.activeCount}</span>
                    <span style={{ color: '#f44336' }}>🔴 剪枝: {strategyStats.prunedCount}</span>
                    <span style={{ color: '#888' }}>总计: {strategyStats.total}</span>
                </div>
            </div>
        );
    };

    // 渲染指标
    const renderMetrics = () => {
        if (!state) return null;

        return (
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '8px',
                padding: '12px',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                marginBottom: '12px'
            }}>
                <div>
                    <div style={{ fontSize: '11px', color: '#666' }}>迭代</div>
                    <div style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>
                        {currentIteration} / {state.config?.max_iterations || 10}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: '11px', color: '#666' }}>温度 τ</div>
                    <div style={{ fontSize: '18px', fontWeight: 600, color: getTemperatureColor(state.normalized_temperature || 0) }}>
                        {(state.normalized_temperature || 0).toFixed(3)}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: '11px', color: '#666' }}>空间熵</div>
                    <div style={{ fontSize: '14px', color: '#fff' }}>
                        {(state.spatial_entropy || 0).toFixed(2)}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: '11px', color: '#666' }}>状态</div>
                    <div style={{ fontSize: '14px', color: getStatusColor(simulationStatus) }}>
                        {getStatusLabel(simulationStatus)}
                    </div>
                </div>
            </div>
        );
    };

    // 渲染当前推理
    const renderCurrentThinking = () => {
        if (simulationStatus !== 'running' || !currentAgent) return null;

        const latestActivity = activityLog[activityLog.length - 1];

        return (
            <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(59,130,246,0.1) 100%)',
                borderRadius: '8px',
                border: '1px solid rgba(139,92,246,0.3)',
                marginBottom: '12px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                    <span style={{ fontSize: '12px', color: '#a78bfa' }}>
                        {AGENT_LABELS[currentAgent]} 正在推理...
                    </span>
                </div>
                {latestActivity?.detail && (
                    <div style={{ fontSize: '13px', color: '#e0e0e0', lineHeight: 1.5 }}>
                        {latestActivity.detail}
                    </div>
                )}
            </div>
        );
    };

    // 渲染迭代详情
    const renderIterationDetails = (iteration: number, activities: AgentActivity[]) => {
        const isExpanded = expandedIterations.has(iteration);
        const isCurrentIteration = iteration === Math.max(...Array.from(iterationGroups.keys()));

        return (
            <div key={iteration} style={{ marginBottom: '8px' }}>
                <div
                    onClick={() => toggleIteration(iteration)}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 12px',
                        background: isCurrentIteration ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.02)',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                    }}
                >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span style={{ fontSize: '13px', fontWeight: 500 }}>
                        迭代 {iteration}
                    </span>
                    <span style={{ fontSize: '11px', color: '#666', marginLeft: 'auto' }}>
                        {activities.length} 步骤
                    </span>
                </div>

                {isExpanded && (
                    <div style={{ paddingLeft: '24px', paddingTop: '8px' }}>
                        {activities.map((activity, idx) => (
                            <div key={activity.id || idx} style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '8px',
                                padding: '6px 0',
                                borderLeft: '2px solid rgba(255,255,255,0.1)',
                                paddingLeft: '12px',
                                marginLeft: '6px'
                            }}>
                                <span style={{ fontSize: '12px', color: '#888', minWidth: '80px' }}>
                                    {AGENT_LABELS[activity.agent]}
                                </span>
                                <span style={{ fontSize: '12px', color: '#e0e0e0', flex: 1 }}>
                                    {activity.detail || activity.message}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // 渲染高分策略
    const renderTopStrategies = () => {
        if (topStrategies.length === 0) return null;

        return (
            <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                    🏆 当前领先策略
                </div>
                {topStrategies.map((s, idx) => (
                    <div key={s.id} style={{
                        padding: '10px 12px',
                        background: idx === 0 ? 'rgba(76,175,80,0.1)' : 'rgba(255,255,255,0.02)',
                        borderRadius: '6px',
                        marginBottom: '6px',
                        borderLeft: idx === 0 ? '3px solid #4CAF50' : '3px solid #333'
                    }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, color: '#fff', marginBottom: '4px' }}>
                            {s.name}
                        </div>
                        <div style={{ fontSize: '11px', color: '#888' }}>
                            UCB: {(s.ucb_score || 0).toFixed(2)} | Score: {(s.score || 0).toFixed(2)}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div style={{
            background: '#0d0d0d',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{
                padding: '16px',
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
            }}>
                <Brain size={18} style={{ color: '#a78bfa' }} />
                <span style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>
                    Thinking
                </span>
                {simulationStatus === 'running' && (
                    <Loader2 size={14} style={{ marginLeft: 'auto', animation: 'spin 1s linear infinite', color: '#a78bfa' }} />
                )}
                {simulationStatus === 'completed' && (
                    <CheckCircle2 size={14} style={{ marginLeft: 'auto', color: '#4CAF50' }} />
                )}
            </div>

            {/* Content */}
            <div ref={scrollRef} style={{
                flex: 1,
                overflow: 'auto',
                padding: '16px'
            }}>
                {simulationStatus === 'idle' && (
                    <div style={{ color: '#666', fontSize: '13px', textAlign: 'center', padding: '40px 20px' }}>
                        输入问题并启动模拟以开始推理...
                    </div>
                )}

                {simulationStatus !== 'idle' && (
                    <>
                        {renderMetrics()}
                        {renderCurrentThinking()}
                        {renderStrategySummary()}
                        {renderTopStrategies()}

                        {/* 迭代历史 */}
                        <div style={{ marginTop: '16px' }}>
                            <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                                📜 推理历史
                            </div>
                            {Array.from(iterationGroups.entries())
                                .reverse()
                                .map(([iteration, activities]) =>
                                    renderIterationDetails(iteration, activities)
                                )}
                        </div>
                    </>
                )}
            </div>

            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

// 辅助函数
function getTemperatureColor(t: number): string {
    if (t < 0.3) return '#4CAF50';
    if (t < 0.7) return '#FF9800';
    return '#f44336';
}

function getStatusColor(status: string): string {
    switch (status) {
        case 'running': return '#a78bfa';
        case 'completed': return '#4CAF50';
        case 'error': return '#f44336';
        case 'awaiting_human': return '#FF9800';
        default: return '#666';
    }
}

function getStatusLabel(status: string): string {
    switch (status) {
        case 'idle': return '待命';
        case 'running': return '推理中';
        case 'completed': return '已完成';
        case 'error': return '错误';
        case 'awaiting_human': return '等待输入';
        default: return status;
    }
}

export default ThinkingPanel;
