import React from 'react';
import { ChatPanel } from './ChatPanel';
import { KnowledgePanel } from './KnowledgePanel';
import { TaskGraph } from './TaskGraph';
import { KPIDashboard } from './KPIDashboard';

export const ControlTower: React.FC = () => {
    return (
        <div id="dashboard" className="control-tower">
            <header className="dashboard-header">
                <h1>Project Prometheus: Control Tower</h1>
            </header>

            <main className="dashboard-main">
                <div className="left-panel">
                    <KPIDashboard />
                    <TaskGraph />
                    <ChatPanel />
                </div>

                <KnowledgePanel />
            </main>
        </div>
    );
};
