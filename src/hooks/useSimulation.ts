
import { useState, useEffect, useCallback, useRef } from 'react';
import { DeepThinkState, SimulationMessage } from '../types';

const WS_URL = 'ws://localhost:8000/ws/simulation';

export const useSimulation = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [state, setState] = useState<DeepThinkState | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

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
                // Reconnect logic could go here
            };

            ws.onmessage = (event) => {
                try {
                    const msg: SimulationMessage = JSON.parse(event.data);
                    if (msg.type === 'state_update') {
                        setState(msg.data);
                    } else if (msg.type === 'status') {
                        console.log(`[Simulation] Status: ${msg.data}`);
                    } else if (msg.type === 'error') {
                        console.error(`[Simulation] Error: ${msg.data}`);
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
    }, []);

    const startSimulation = useCallback(async (problem: string, config?: any) => {
        try {
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
        }
    }, []);

    const stopSimulation = useCallback(async () => {
        try {
            await fetch('http://localhost:8000/api/simulation/stop');
        } catch (e) {
            console.error('Failed to stop simulation', e);
        }
    }, []);

    return {
        isConnected,
        state,
        startSimulation,
        stopSimulation
    };
};
