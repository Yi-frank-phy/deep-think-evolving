import React, { memo, useState } from 'react';
import { Sender } from '../types';
import { Copy, Check } from 'lucide-react';

export type Message = {
    sender: Sender;
    text: string;
    isStreaming?: boolean;
};

interface MessageItemProps {
    message: Message;
}

export const MessageItem = memo(({ message }: MessageItemProps) => {
    const [isCopied, setIsCopied] = useState(false);

    const handleCopy = async () => {
        if (!message.text) return;
        try {
            await navigator.clipboard.writeText(message.text);
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text:', err);
        }
    };

    const hasCopyButton = !message.isStreaming && !!message.text;

    return (
        <div
            className={`message ${message.sender}`}
            style={{
                position: 'relative',
                paddingRight: hasCopyButton ? '2.5rem' : undefined
            }}
        >
            <p>
                {message.text}
                {message.isStreaming && <span className="streaming-cursor">▌</span>}
            </p>

            {hasCopyButton && (
                <button
                    onClick={handleCopy}
                    className={`message-copy-btn ${isCopied ? 'copied' : ''}`}
                    aria-label={isCopied ? "Copied" : "Copy message text"}
                    title={isCopied ? "Copied" : "Copy to clipboard"}
                >
                    {isCopied ? <Check size={14} /> : <Copy size={14} />}
                </button>
            )}
        </div>
    );
});

MessageItem.displayName = 'MessageItem';
