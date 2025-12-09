export type Sender = "user" | "assistant";

export type KnowledgeEntry = {
    id: string;
    thread_id: string;
    outcome: string;
    created_at: string;
    reflection: string;
    embedding_dimensions: number;
    embedding_preview: number[];
};

export type KnowledgeMessage =
    | { type: "snapshot"; data: KnowledgeEntry[] }
    | { type: "update"; data: KnowledgeEntry }
    | { type: "delete"; data: { id: string } };

export interface StrategyNode {
    id: string;
    parent_id: string | null; // Added for tree visualization
    name: string;
    rationale: string;
    assumption: string;
    milestones: any;
    status: "active" | "pruned" | "pruned_beam" | "pruned_error" | "completed" | "expanded";
    score: number;
    density: number;
    embedding_preview: number[];
    trajectory: string[];
}

export interface DeepThinkState {
    problem_state: string;

    // Task Decomposition
    subtasks?: string[];
    information_needs?: { topic: string; type: string; priority: string }[];

    // Evolution State
    strategies: StrategyNode[];

    // Research Context
    research_context: string | null;
    research_status?: string;
    research_iteration?: number;

    // Global Metrics
    spatial_entropy: number;
    effective_temperature: number;
    normalized_temperature: number;

    // Config
    config?: any;

    // Memory
    virtual_filesystem?: { [key: string]: string };

    // Tracking
    iteration_count: number;
    history: string[];

    // Contexts
    judge_context: string | null;
    architect_decisions?: { strategy_id: string; executor_instruction: string; context_injection: string }[];
}

// Agent phase types for activity tracking
export type AgentPhase = "researcher" | "distiller" | "architect" | "distiller_for_judge" | "judge" | "evolution" | "propagation";

// Agent activity message types
export interface AgentActivity {
    id: string;
    agent: AgentPhase;
    message: string;
    detail?: string;
    timestamp: string;
    type: 'start' | 'progress' | 'complete';
    duration_ms?: number;
}

export type SimulationMessage =
    | { type: "status"; data: "started" | "completed" | "stopped" }
    | { type: "state_update"; data: DeepThinkState }
    | { type: "error"; data: string }
    // Agent activity messages for real-time visualization
    | { type: "agent_start"; data: { agent: AgentPhase; message: string } }
    | { type: "agent_progress"; data: { agent: AgentPhase; message: string; detail?: string } }
    | { type: "agent_complete"; data: { agent: AgentPhase; message: string; duration_ms?: number } }
    // Human-in-the-Loop messages
    | { type: "hil_required"; data: HilRequest };

// Human-in-the-Loop request type
export interface HilRequest {
    request_id: string;
    agent: AgentPhase;
    question: string;
    context?: string;
    timeout_seconds: number;
    created_at: string;
}

export interface ModelInfo {
    id: string;
    name: string;
    thinking_min: number;
    thinking_max: number;
    tier?: 'free' | 'standard' | 'premium' | 'experimental';
}

