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
