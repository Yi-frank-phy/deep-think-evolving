import React from 'react';

export const TaskGraph: React.FC = () => {
    return (
        <div className="task-graph-container" style={{
            flex: 1,
            background: 'rgba(0,0,0,0.2)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '300px'
        }}>
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <h3>Task Graph Visualization</h3>
                <p>Graph rendering engine initializing...</p>
                {/* Placeholder for actual graph */}
                <svg width="200" height="100" viewBox="0 0 200 100">
                    <circle cx="50" cy="50" r="20" fill="var(--primary-color)" opacity="0.5" />
                    <line x1="70" y1="50" x2="130" y2="50" stroke="var(--border-color)" strokeWidth="2" />
                    <circle cx="150" cy="50" r="20" fill="var(--secondary-color)" opacity="0.5" />
                </svg>
            </div>
        </div>
    );
};
