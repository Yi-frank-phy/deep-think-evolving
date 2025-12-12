import React, { memo } from 'react';
import { Sender } from '../types';

export type Message = {
    sender: Sender;
    text: string;
    isStreaming?: boolean;
};

interface MessageItemProps {
    message: Message;
}

export const MessageItem = memo(({ message }: MessageItemProps) => {
    return (
        <div className={`message ${message.sender}`}>
            <p>
                {message.text}
                {message.isStreaming && <span className="streaming-cursor">▌</span>}
            </p>
        </div>
    );
});

MessageItem.displayName = 'MessageItem';
