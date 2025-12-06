import { useState, useEffect } from 'react';

export interface ModelInfo {
    id: string;
    name: string;
    thinking_min: number;
    thinking_max: number;
}

const API_URL = 'http://localhost:8000';

export const useModels = () => {
    const [models, setModels] = useState<ModelInfo[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchModels = async () => {
            try {
                const response = await fetch(`${API_URL}/api/models`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch models: ${response.status}`);
                }
                const data = await response.json();
                setModels(data.models);
                setError(null);
            } catch (e) {
                console.error('[useModels] Error fetching models:', e);
                setError(e instanceof Error ? e.message : 'Unknown error');
                // Fallback to default models if API fails
                setModels([
                    { id: 'gemini-2.5-pro-preview-06-05', name: 'Gemini 2.5 Pro', thinking_min: 128, thinking_max: 32768 },
                    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', thinking_min: 0, thinking_max: 24576 },
                    { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite', thinking_min: 512, thinking_max: 24576 }
                ]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchModels();
    }, []);

    return { models, isLoading, error };
};
