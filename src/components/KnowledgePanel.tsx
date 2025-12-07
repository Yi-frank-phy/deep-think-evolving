import React, { useEffect, useState, useRef } from 'react';
import { KnowledgeEntry, KnowledgeMessage } from '../types';

export const KnowledgePanel: React.FC = () => {
    const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
    const [status, setStatus] = useState<"connecting" | "connected" | "error" | "closed">("closed");
    const [filter, setFilter] = useState<'all' | 'lesson_learned' | 'success_pattern' | 'insight'>('all');

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

    const filteredEntries = entries.filter(e => {
        if (filter === 'all') return true;
        if (filter === 'insight') return e.outcome === 'insight';
        if (filter === 'lesson_learned') return e.outcome === 'lesson_learned' || e.outcome === 'failure_pattern';
        if (filter === 'success_pattern') return e.outcome === 'success_pattern';
        return true;
    });

    return (
        <aside id="knowledge-panel">
            <div className="knowledge-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2>Knowledge Base</h2>
                    <span id="knowledge-status" className={`status status--${status}`}>
                        {status === "connected" ? "● Online" : "○ Offline"}
                    </span>
                </div>

                <div className="knowledge-filters" style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', borderBottom: '1px solid #333' }}>
                    <button
                        className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                        style={{ background: 'none', border: 'none', color: filter === 'all' ? '#fff' : '#666', borderBottom: filter === 'all' ? '2px solid #2196F3' : '2px solid transparent', padding: '0.5rem', cursor: 'pointer' }}
                    >
                        All
                    </button>
                    <button
                        className={`filter-tab ${filter === 'lesson_learned' ? 'active' : ''}`}
                        onClick={() => setFilter('lesson_learned')}
                        style={{ background: 'none', border: 'none', color: filter === 'lesson_learned' ? '#fff' : '#666', borderBottom: filter === 'lesson_learned' ? '2px solid #e53935' : '2px solid transparent', padding: '0.5rem', cursor: 'pointer' }}
                    >
                        Lessons
                    </button>
                    <button
                        className={`filter-tab ${filter === 'success_pattern' ? 'active' : ''}`}
                        onClick={() => setFilter('success_pattern')}
                        style={{ background: 'none', border: 'none', color: filter === 'success_pattern' ? '#fff' : '#666', borderBottom: filter === 'success_pattern' ? '2px solid #4CAF50' : '2px solid transparent', padding: '0.5rem', cursor: 'pointer' }}
                    >
                        Patterns
                    </button>
                    <button
                        className={`filter-tab ${filter === 'insight' ? 'active' : ''}`}
                        onClick={() => setFilter('insight')}
                        style={{ background: 'none', border: 'none', color: filter === 'insight' ? '#fff' : '#666', borderBottom: filter === 'insight' ? '2px solid #FFC107' : '2px solid transparent', padding: '0.5rem', cursor: 'pointer' }}
                    >
                        Insights
                    </button>
                </div>
            </div>

            <div id="knowledge-feed" className={`knowledge-feed ${filteredEntries.length === 0 ? 'empty' : ''}`} style={{ marginTop: '1rem' }}>
                {filteredEntries.length === 0 ? (
                    <p className="placeholder">No entries found for this filter.</p>
                ) : (
                    filteredEntries.map(entry => (
                        <article key={entry.id} className="knowledge-entry" style={{
                            borderLeft: `4px solid ${entry.outcome === 'success_pattern' ? '#4CAF50' :
                                    entry.outcome === 'lesson_learned' || entry.outcome === 'failure_pattern' ? '#e53935' :
                                        entry.outcome === 'insight' ? '#FFC107' : '#666'
                                }`
                        }}>
                            <div className="knowledge-entry__header">
                                <span className="tag" style={{ fontSize: '0.75rem', opacity: 0.8 }}>{entry.outcome.toUpperCase().replace('_', ' ')}</span>
                                <time dateTime={entry.created_at} style={{ fontSize: '0.75rem', color: '#888' }}>
                                    {new Date(entry.created_at).toLocaleTimeString()}
                                </time>
                            </div>
                            <h4 style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#eee' }}>{entry.thread_id}</h4>
                            <p style={{ fontSize: '0.85rem', color: '#ccc', lineHeight: '1.4' }}>{entry.reflection}</p>
                            <dl className="knowledge-entry__meta">
                                <dt>Preview</dt>
                                <dd>{formatEmbeddingPreview(entry.embedding_preview)}</dd>
                            </dl>
                        </article>
                    ))
                )}
            </div>
        </aside>
    );
};
