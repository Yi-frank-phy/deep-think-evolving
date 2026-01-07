/**
 * ForceSynthesizeBar - Force Synthesize Control Bar
 * 
 * Displayed when multiple strategy nodes are selected, allowing the user to "Synthesize Report".
 * HIL (Human-in-the-Loop) Feature Implementation - T-052
 */

import React, { useState } from 'react';
import { FileText, X, CheckCircle } from 'lucide-react';

interface ForceSynthesizeBarProps {
    selectedIds: string[];
    strategyNames: Map<string, string>;
    onSynthesize: (ids: string[]) => void;
    onClearSelection: () => void;
    isLoading?: boolean;
}

export const ForceSynthesizeBar: React.FC<ForceSynthesizeBarProps> = ({
    selectedIds,
    strategyNames,
    onSynthesize,
    onClearSelection,
    isLoading = false
}) => {
    const [showConfirm, setShowConfirm] = useState(false);

    if (selectedIds.length === 0) return null;

    const handleSynthesize = async () => {
        if (showConfirm) {
            onSynthesize(selectedIds);
            setShowConfirm(false);
        } else {
            setShowConfirm(true);
        }
    };

    return (
        <>
            {/* Selection Info */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={18} color="#4CAF50" />
                <span style={{ fontWeight: 'bold' }}>
                    Selected {selectedIds.length} strategies
                </span>
            </div>

            {/* Selected Names Preview */}
            <div style={{
                maxWidth: '300px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                color: '#ccc',
                fontSize: '0.85rem'
            }}>
                {selectedIds.slice(0, 3).map(id => strategyNames.get(id) || id).join(', ')}
                {selectedIds.length > 3 && ` +${selectedIds.length - 3} more`}
            </div>

            {/* Confirm Dialog or Action Buttons */}
            {showConfirm ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: '#feca57', fontSize: '0.9rem' }}>
                        Synthesize these strategies?
                    </span>
                    <button
                        onClick={handleSynthesize}
                        disabled={isLoading}
                        className="btn-primary"
                        style={{
                            background: '#4CAF50',
                            padding: '0.4rem 0.8rem',
                            fontSize: '0.9rem'
                        }}
                    >
                        {isLoading ? 'Processing...' : 'Confirm'}
                    </button>
                    <button
                        onClick={() => setShowConfirm(false)}
                        style={{
                            background: 'transparent',
                            color: '#ccc',
                            border: '1px solid #666',
                            padding: '0.4rem 0.8rem',
                            borderRadius: '100px',
                            cursor: 'pointer',
                            fontSize: '0.9rem'
                        }}
                    >
                        Cancel
                    </button>
                </div>
            ) : (
                <>
                    <button
                        onClick={handleSynthesize}
                        disabled={isLoading}
                        className="btn-primary"
                        style={{
                            background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                            boxShadow: 'none',
                            padding: '0.5rem 1rem'
                        }}
                    >
                        <FileText size={16} />
                        Synthesize Report
                    </button>
                    <button
                        onClick={onClearSelection}
                        className="btn-icon"
                        style={{
                            color: '#ccc',
                            borderColor: 'transparent',
                            width: '32px',
                            height: '32px'
                        }}
                        title="Clear selection"
                        aria-label="Clear selection"
                    >
                        <X size={18} />
                    </button>
                </>
            )}
        </>
    );
};
