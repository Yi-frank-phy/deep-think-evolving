
import { useState, useEffect, useCallback, useRef } from 'react';
import { DeepThinkState, SimulationMessage, AgentActivity, AgentPhase } from '../types';

const WS_URL = 'ws://localhost:8000/ws/simulation';

export const useSimulation = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [state, setState] = useState<DeepThinkState | null>(null);
    const [activityLog, setActivityLog] = useState<AgentActivity[]>([]);
    const [currentAgent, setCurrentAgent] = useState<AgentPhase | null>(null);
    const [simulationStatus, setSimulationStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
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
                            setState(msg.data);
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

    return {
        isConnected,
        state,
        activityLog,
        currentAgent,
        simulationStatus,
        startSimulation,
        stopSimulation
    };
};
