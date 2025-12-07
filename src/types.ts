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
    strategies: StrategyNode[];
    research_context: string | null;
    judge_context: string | null; // Added for context awareness
    spatial_entropy: number;
    effective_temperature: number;
    normalized_temperature: number;
    iteration_count: number; // Added for dashboard
    history: string[];
}

export type SimulationMessage =
    | { type: "status"; data: "started" | "completed" | "stopped" }
    | { type: "state_update"; data: DeepThinkState }
    | { type: "error"; data: string };

export interface ModelInfo {
    id: string;
    name: string;
    thinking_min: number;
    thinking_max: number;
}
