import React, { useState, useRef, useEffect } from 'react';
import { Sender } from '../types';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { MessageItem, Message } from './MessageItem';
import { Send, Mic, Square, X, Loader2 } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export const ChatPanel: React.FC = React.memo(() => {
    const [messages, setMessages] = useState<Message[]>([
        { sender: 'assistant', text: 'System standby. Awaiting your instructions.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatLogRef = useRef<HTMLDivElement>(null);
    const { isRecording, audioBlob, startRecording, stopRecording, getBase64, clearAudio } = useAudioRecorder();

    useEffect(() => {
        if (chatLogRef.current) {
            chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const text = inputValue.trim();
        if (!text && !audioBlob) return;

        // Add user message
        const userMessage: Message = {
            sender: 'user',
            text: audioBlob ? `🎤 ${text || '[Voice message]'}` : text
        };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // Add placeholder for assistant response
        const assistantIdx = messages.length + 1;
        setMessages(prev => [...prev, { sender: 'assistant', text: '', isStreaming: true }]);

        try {
            // Prepare request body
            const body: any = {
                message: text || 'Please transcribe and respond to the audio message.',
                model_name: 'gemini-2.5-flash'
            };

            // Add audio if recorded
            if (audioBlob) {
                const audioBase64 = await getBase64();
                if (audioBase64) {
                    body.audio_base64 = audioBase64;
                }
                clearAudio();
            }

            // Stream response
            const response = await fetch(`${API_URL}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.text) {
                                    fullText += data.text;
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        updated[assistantIdx] = {
                                            sender: 'assistant',
                                            text: fullText,
                                            isStreaming: true
                                        };
                                        return updated;
                                    });
                                } else if (data.done) {
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        updated[assistantIdx] = {
                                            sender: 'assistant',
                                            text: fullText,
                                            isStreaming: false
                                        };
                                        return updated;
                                    });
                                } else if (data.error) {
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        updated[assistantIdx] = {
                                            sender: 'assistant',
                                            text: `Error: ${data.error}`,
                                            isStreaming: false
                                        };
                                        return updated;
                                    });
                                }
                            } catch (parseErr) {
                                // Skip malformed JSON
                            }
                        }
                    }
                }
            }
        } catch (err) {
            console.error('Chat error:', err);
            setMessages(prev => {
                const updated = [...prev];
                updated[assistantIdx] = {
                    sender: 'assistant',
                    text: `Connection error: ${err instanceof Error ? err.message : 'Unknown error'}`,
                    isStreaming: false
                };
                return updated;
            });
        } finally {
            setIsLoading(false);
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    return (
        <section id="chat-container">
            <div id="chat-log" ref={chatLogRef}>
                {messages.map((msg, idx) => (
                    <MessageItem key={idx} message={msg} />
                ))}
            </div>
            <form id="chat-form" onSubmit={handleSubmit}>
                <div style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
                    <label htmlFor="user-input" className="sr-only" style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap', border: 0 }}>
                        User Input
                    </label>
                    <input
                        type="text"
                        id="user-input"
                        placeholder={audioBlob ? "Add text to accompany voice..." : "Enter your instructions here..."}
                        autoComplete="off"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        disabled={isLoading}
                        style={{ flex: 1 }}
                    />
                    <button
                        type="button"
                        onClick={toggleRecording}
                        disabled={isLoading}
                        title={isRecording ? "Stop recording" : "Start voice recording"}
                        aria-label={isRecording ? "Stop recording" : "Start voice recording"}
                        style={{
                            background: isRecording ? '#e53935' : '#444',
                            minWidth: '40px',
                            padding: '0.5rem',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            transition: 'background 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        {isRecording ? <Square size={18} /> : <Mic size={18} />}
                    </button>
                </div>
                {audioBlob && (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        padding: '0.25rem 0.5rem', background: '#333', borderRadius: '4px',
                        fontSize: '0.85rem', color: '#4CAF50'
                    }}>
                        <span>🎙️ Voice recorded</span>
                        <button
                            type="button"
                            onClick={clearAudio}
                            aria-label="Clear recorded audio"
                            style={{
                                background: 'transparent', border: 'none',
                                color: '#888', cursor: 'pointer', fontSize: '0.9rem',
                                display: 'flex', alignItems: 'center'
                            }}
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}
                <button
                    type="submit"
                    disabled={isLoading || (!inputValue.trim() && !audioBlob)}
                    aria-label={isLoading ? "Sending message" : "Send message"}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        minWidth: '80px'
                    }}
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="animate-spin" size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            <span>Sending...</span>
                        </>
                    ) : (
                        <>
                            <span>Send</span>
                            <Send size={16} />
                        </>
                    )}
                </button>
                <style>{`
                    @keyframes spin {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                `}</style>
            </form>
        </section>
    );
});
