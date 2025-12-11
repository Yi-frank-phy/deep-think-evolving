
import { useState, useEffect, useCallback, useRef } from 'react';
import { DeepThinkState, SimulationMessage, AgentActivity, AgentPhase, HilRequest } from '../types';

const WS_URL = 'ws://localhost:8000/ws/simulation';

export const useSimulation = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [state, setState] = useState<DeepThinkState | null>(null);
    const [activityLog, setActivityLog] = useState<AgentActivity[]>([]);
    const [currentAgent, setCurrentAgent] = useState<AgentPhase | null>(null);
    const [simulationStatus, setSimulationStatus] = useState<'idle' | 'running' | 'completed' | 'error' | 'awaiting_human'>('idle');
    const [hilRequest, setHilRequest] = useState<HilRequest | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const addActivity = useCallback((activity: Omit<AgentActivity, 'id' | 'timestamp'>) => {
        const newActivity: AgentActivity = {
            ...activity,
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
        };
        setActivityLog(prev => [...prev.slice(-99), newActivity]); // Keep last 100 entries
    }, []);

    useEffect(() => {
        const connect = () => {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[Simulation] Connected');
                setIsConnected(true);
            };

            ws.onclose = () => {
                console.log('[Simulation] Disconnected');
                setIsConnected(false);
                setCurrentAgent(null);
            };

            ws.onmessage = (event) => {
                try {
                    const msg: SimulationMessage = JSON.parse(event.data);

                    switch (msg.type) {
                        case 'state_update':
                            setState(prev => {
                                if (!prev) return msg.data as DeepThinkState;
                                const update = msg.data as Partial<DeepThinkState>;

                                // Debug logging for key metrics
                                if (update.iteration_count !== undefined) {
                                    console.log(`[State] iteration_count: ${prev.iteration_count} -> ${update.iteration_count}`);
                                }
                                if (update.spatial_entropy !== undefined) {
                                    console.log(`[State] spatial_entropy: ${prev.spatial_entropy} -> ${update.spatial_entropy}`);
                                }
                                if (update.strategies) {
                                    console.log(`[State] strategies: ${prev.strategies.length} -> ${update.strategies.length}`);
                                }

                                // Merge strategies intelligently: prefer the update if provided
                                const mergedStrategies = update.strategies || prev.strategies;

                                // Merge numeric fields: only update if new value is defined
                                const mergedIterationCount = update.iteration_count ?? prev.iteration_count;
                                const mergedSpatialEntropy = update.spatial_entropy ?? prev.spatial_entropy;
                                const mergedEffectiveTemp = update.effective_temperature ?? prev.effective_temperature;
                                const mergedNormalizedTemp = update.normalized_temperature ?? prev.normalized_temperature;

                                return {
                                    ...prev,
                                    ...update,
                                    // Explicit handling of key fields
                                    strategies: mergedStrategies,
                                    iteration_count: mergedIterationCount,
                                    spatial_entropy: mergedSpatialEntropy,
                                    effective_temperature: mergedEffectiveTemp,
                                    normalized_temperature: mergedNormalizedTemp,
                                    // Append history instead of replacing, as backend sends deltas
                                    history: update.history
                                        ? [...(prev.history || []), ...update.history]
                                        : prev.history
                                };
                            });
                            break;

                        case 'status':
                            console.log(`[Simulation] Status: ${msg.data}`);
                            if (msg.data === 'started') {
                                setSimulationStatus('running');
                                setActivityLog([]); // Clear previous run
                            } else if (msg.data === 'completed') {
                                setSimulationStatus('completed');
                                setCurrentAgent(null);
                            } else if (msg.data === 'stopped') {
                                setSimulationStatus('idle');
                                setCurrentAgent(null);
                            }
                            break;

                        case 'error':
                            console.error(`[Simulation] Error: ${msg.data}`);
                            setSimulationStatus('error');
                            addActivity({
                                agent: 'researcher' as AgentPhase,
                                message: `Error: ${msg.data}`,
                                type: 'complete'
                            });
                            break;

                        case 'agent_start':
                            setCurrentAgent(msg.data.agent);
                            addActivity({
                                agent: msg.data.agent,
                                message: msg.data.message,
                                type: 'start'
                            });
                            break;

                        case 'agent_progress':
                            addActivity({
                                agent: msg.data.agent,
                                message: msg.data.message,
                                detail: msg.data.detail,
                                type: 'progress'
                            });
                            break;

                        case 'agent_complete':
                            addActivity({
                                agent: msg.data.agent,
                                message: msg.data.message,
                                duration_ms: msg.data.duration_ms,
                                type: 'complete'
                            });
                            break;

                        case 'hil_required':
                            console.log('[Simulation] HIL request received:', msg.data);
                            setHilRequest(msg.data);
                            setSimulationStatus('awaiting_human');
                            addActivity({
                                agent: msg.data.agent,
                                message: `⚠️ ${msg.data.agent} 需要人类输入`,
                                detail: msg.data.question,
                                type: 'progress'
                            });
                            break;
                    }
                } catch (e) {
                    console.error('[Simulation] Failed to parse message', e);
                }
            };
        };

        connect();

        return () => {
            wsRef.current?.close();
        };
    }, [addActivity]);

    const startSimulation = useCallback(async (problem: string, config?: any) => {
        try {
            setSimulationStatus('running');
            setActivityLog([]);
            setState(null);
            await fetch('http://localhost:8000/api/simulation/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    problem,
                    config: config || { t_max: 2.0, c_explore: 1.0, beam_width: 3 }
                })
            });
        } catch (e) {
            console.error('Failed to start simulation', e);
            setSimulationStatus('error');
        }
    }, []);

    const stopSimulation = useCallback(async () => {
        try {
            await fetch('http://localhost:8000/api/simulation/stop');
            setSimulationStatus('idle');
            setCurrentAgent(null);
        } catch (e) {
            console.error('Failed to stop simulation', e);
        }
    }, []);

    const respondToHil = useCallback(async (requestId: string, response: string) => {
        try {
            console.log('[Simulation] Submitting HIL response:', requestId, response);
            await fetch('http://localhost:8000/api/hil/response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: requestId, response })
            });
            setHilRequest(null);
            setSimulationStatus('running');
            addActivity({
                agent: hilRequest?.agent || 'researcher',
                message: '✅ 人类输入已提交',
                type: 'progress'
            });
        } catch (e) {
            console.error('Failed to submit HIL response', e);
        }
    }, [hilRequest, addActivity]);

    return {
        isConnected,
        state,
        activityLog,
        currentAgent,
        simulationStatus,
        hilRequest,
        startSimulation,
        stopSimulation,
        respondToHil
    };
};
