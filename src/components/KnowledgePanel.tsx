import React, { useEffect, useState, useRef } from 'react';
import { KnowledgeEntry, KnowledgeMessage } from '../types';
import { BookOpen, Search, Wifi, WifiOff, Database } from 'lucide-react';

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
        <aside id="knowledge-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div className="drawer-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <BookOpen size={16} className="text-secondary" />
                    <h2 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Knowledge Base</h2>
                </div>
                <div
                    className={`status-indicator icon-only ${status === 'connected' ? '' : 'offline'}`}
                    title={status === "connected" ? "Connected" : "Disconnected"}
                >
                    {status === "connected" ? (
                        <Wifi size={14} color="#137333" aria-label="Connected" />
                    ) : (
                        <WifiOff size={14} color="#c5221f" aria-label="Disconnected" />
                    )}
                </div>
            </div>

            <div style={{ padding: '0 1rem' }}>
                <div className="knowledge-filters">
                    <button className={`filter-tab all ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All</button>
                    <button className={`filter-tab lesson ${filter === 'lesson_learned' ? 'active' : ''}`} onClick={() => setFilter('lesson_learned')}>Lessons</button>
                    <button className={`filter-tab pattern ${filter === 'success_pattern' ? 'active' : ''}`} onClick={() => setFilter('success_pattern')}>Patterns</button>
                    <button className={`filter-tab insight ${filter === 'insight' ? 'active' : ''}`} onClick={() => setFilter('insight')}>Insights</button>
                </div>
            </div>

            <div id="knowledge-feed" className={`knowledge-feed`} style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
                {entries.length === 0 ? (
                    <div className="knowledge-feed empty">
                        <div className="empty-icon-wrapper">
                            <Database size={24} style={{ opacity: 0.4 }} />
                        </div>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>Knowledge Base Empty</h4>
                        <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5 }}>
                            Completed simulations will archive their insights here for future reference.
                        </p>
                    </div>
                ) : filteredEntries.length === 0 ? (
                    <div className="knowledge-feed empty">
                        <Search size={24} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
                        <p style={{ margin: 0 }}>No matches found. Try selecting a different filter.</p>
                    </div>
                ) : (
                    filteredEntries.map(entry => (
                        <article key={entry.id} className="knowledge-entry" style={{
                            borderLeft: `4px solid ${entry.outcome === 'success_pattern' ? '#4CAF50' :
                                    entry.outcome === 'lesson_learned' || entry.outcome === 'failure_pattern' ? '#e53935' :
                                        entry.outcome === 'insight' ? '#FFC107' : '#666'
                                }`
                        }}>
                            <div className="knowledge-entry__header">
                                <span className="tag">
                                    {entry.outcome.toUpperCase().replace('_', ' ')}
                                </span>
                                <time dateTime={entry.created_at} style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    {new Date(entry.created_at).toLocaleTimeString()}
                                </time>
                            </div>
                            <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--text-primary)' }}>{entry.thread_id}</h4>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5', margin: '0 0 0.75rem 0' }}>{entry.reflection}</p>
                            <dl className="knowledge-entry__meta" style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                <dt style={{ display: 'inline', fontWeight: 500 }}>Vector Preview: </dt>
                                <dd style={{ display: 'inline', margin: 0, fontFamily: 'monospace' }}>{formatEmbeddingPreview(entry.embedding_preview)}</dd>
                            </dl>
                        </article>
                    ))
                )}
            </div>
        </aside>
    );
};
