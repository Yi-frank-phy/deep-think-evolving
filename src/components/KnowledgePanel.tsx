import React, { useEffect, useState, useRef } from 'react';
import { KnowledgeEntry, KnowledgeMessage } from '../types';

export const KnowledgePanel: React.FC = () => {
    const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
    const [status, setStatus] = useState<"connecting" | "connected" | "error" | "closed">("closed");
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimerRef = useRef<number | undefined>(undefined);

    const connect = (attempt = 0) => {
        if (socketRef.current) {
            socketRef.current.close();
        }
        if (reconnectTimerRef.current) {
            window.clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = undefined;
        }

        setStatus("connecting");

        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const { VITE_KNOWLEDGE_SOCKET_URL, VITE_KNOWLEDGE_SOCKET_PORT } = import.meta.env;
        const socketUrl =
            VITE_KNOWLEDGE_SOCKET_URL ||
            `${protocol}://${window.location.hostname}:${VITE_KNOWLEDGE_SOCKET_PORT || "8000"
            }/ws/knowledge_base`;

        const socket = new WebSocket(socketUrl);
        socketRef.current = socket;

        socket.addEventListener("open", () => {
            if (socketRef.current !== socket) return;
            setStatus("connected");
        });

        socket.addEventListener("message", (event) => {
            if (socketRef.current !== socket) return;
            try {
                const payload = JSON.parse(event.data) as KnowledgeMessage;
                handleMessage(payload);
            } catch (error) {
                console.warn("Failed to parse knowledge base message", error);
            }
        });

        socket.addEventListener("close", () => {
            if (socketRef.current !== socket) return;
            socketRef.current = null;
            setStatus("closed");
            scheduleReconnect(attempt + 1);
        });

        socket.addEventListener("error", () => {
            if (socketRef.current !== socket) return;
            setStatus("error");
            socket.close();
        });
    };

    const scheduleReconnect = (attempt: number) => {
        if (reconnectTimerRef.current) {
            window.clearTimeout(reconnectTimerRef.current);
        }
        const cappedAttempt = Math.min(attempt, 6);
        const delay = Math.min(10000, (cappedAttempt + 1) * 1000);
        reconnectTimerRef.current = window.setTimeout(() => connect(attempt + 1), delay);
    };

    const handleMessage = (payload: KnowledgeMessage) => {
        switch (payload.type) {
            case "snapshot":
                if (Array.isArray(payload.data)) {
                    // Sort by created_at desc
                    const sorted = [...payload.data].sort((a, b) =>
                        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                    );
                    setEntries(sorted);
                }
                break;
            case "update":
                if (payload.data?.id) {
                    setEntries(prev => {
                        const newEntries = prev.filter(e => e.id !== payload.data.id);
                        newEntries.push(payload.data);
                        return newEntries.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                    });
                }
                break;
            case "delete":
                if (payload.data?.id) {
                    setEntries(prev => prev.filter(e => e.id !== payload.data.id));
                }
                break;
        }
    };

    useEffect(() => {
        connect();
        return () => {
            if (socketRef.current) socketRef.current.close();
            if (reconnectTimerRef.current) window.clearTimeout(reconnectTimerRef.current);
        };
    }, []);

    const formatEmbeddingPreview = (values: number[]) => {
        if (!values || values.length === 0) return "n/a";
        const formatted = values.map((value) =>
            Number.isFinite(value) ? value.toFixed(4) : String(value)
        );
        return `[${formatted.join(", ")}]`;
    };

    return (
        <aside id="knowledge-panel">
            <div className="knowledge-header">
                <h2>Reflection Knowledge Base</h2>
                <span id="knowledge-status" className={`status status--${status}`}>
                    {status === "connecting" ? "Connecting..." :
                        status === "connected" ? "Connected" :
                            status === "error" ? "Error" : "Disconnected"}
                </span>
            </div>
            <div id="knowledge-feed" className={`knowledge-feed ${entries.length === 0 ? 'empty' : ''}`}>
                {entries.length === 0 ? (
                    <p className="placeholder">Waiting for reflections...</p>
                ) : (
                    entries.map(entry => (
                        <article key={entry.id} className="knowledge-entry">
                            <div className="knowledge-entry__header">
                                <h3>{entry.thread_id}</h3>
                                <span className={`tag tag--${entry.outcome}`}>{entry.outcome.toUpperCase()}</span>
                                <time dateTime={entry.created_at}>
                                    {new Date(entry.created_at).toLocaleString()}
                                </time>
                            </div>
                            <div className="knowledge-entry__body">
                                <p>{entry.reflection || "(empty reflection)"}</p>
                                <dl className="knowledge-entry__meta">
                                    <dt>Embedding dims</dt>
                                    <dd>{entry.embedding_dimensions}</dd>
                                    <dt>Preview</dt>
                                    <dd>{formatEmbeddingPreview(entry.embedding_preview)}</dd>
                                </dl>
                            </div>
                        </article>
                    ))
                )}
            </div>
        </aside>
    );
};
