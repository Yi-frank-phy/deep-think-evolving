import React, { useState, useRef, useEffect } from 'react';
import { Sender } from '../types';

type Message = {
    sender: Sender;
    text: string;
};

export const ChatPanel: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        { sender: 'assistant', text: 'System standby. Awaiting your instructions.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const chatLogRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (chatLogRef.current) {
            chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const text = inputValue.trim();
        if (!text) return;

        setMessages(prev => [...prev, { sender: 'user', text }]);
        setInputValue('');

        // Mock response
        setTimeout(() => {
            setMessages(prev => [...prev, {
                sender: 'assistant',
                text: `Instruction received: "${text}". Acknowledged. Standby for execution.`
            }]);
        }, 500);
    };

    return (
        <section id="chat-container">
            <div id="chat-log" ref={chatLogRef}>
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.sender}`}>
                        <p>{msg.text}</p>
                    </div>
                ))}
            </div>
            <form id="chat-form" onSubmit={handleSubmit}>
                <input
                    type="text"
                    id="user-input"
                    placeholder="Enter your instructions here..."
                    autoComplete="off"
                    required
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                />
                <button type="submit">Send</button>
            </form>
        </section>
    );
};
