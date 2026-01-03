/**
 * ForceSynthesizeBar - 强制收束控制栏
 * 
 * 当用户选择多个策略节点时显示，提供"收束为报告"操作。
 * HIL (Human-in-the-Loop) 功能实现 - T-052
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
        <div style={{
            position: 'fixed',
            bottom: '2rem',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            border: '1px solid #4CAF50',
            borderRadius: '12px',
            padding: '1rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: '0 8px 32px rgba(76, 175, 80, 0.3)',
            zIndex: 999,
            animation: 'slideUp 0.3s ease-out'
        }}>
            {/* Selection Info */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={18} color="#4CAF50" />
                <span style={{ color: '#fff', fontWeight: 'bold' }}>
                    已选择 {selectedIds.length} 个策略
                </span>
            </div>

            {/* Selected Names Preview */}
            <div style={{
                maxWidth: '300px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                color: '#888',
                fontSize: '0.85rem'
            }}>
                {selectedIds.slice(0, 3).map(id => strategyNames.get(id) || id).join(', ')}
                {selectedIds.length > 3 && ` +${selectedIds.length - 3} 更多`}
            </div>

            {/* Confirm Dialog or Action Buttons */}
            {showConfirm ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: '#feca57', fontSize: '0.9rem' }}>
                        确定收束这些策略?
                    </span>
                    <button
                        onClick={handleSynthesize}
                        disabled={isLoading}
                        style={{
                            background: '#4CAF50',
                            color: '#fff',
                            border: 'none',
                            padding: '0.5rem 1rem',
                            borderRadius: '6px',
                            cursor: isLoading ? 'wait' : 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        {isLoading ? '处理中...' : '确认'}
                    </button>
                    <button
                        onClick={() => setShowConfirm(false)}
                        style={{
                            background: 'transparent',
                            color: '#888',
                            border: '1px solid #444',
                            padding: '0.5rem 1rem',
                            borderRadius: '6px',
                            cursor: 'pointer'
                        }}
                    >
                        取消
                    </button>
                </div>
            ) : (
                <>
                    <button
                        onClick={handleSynthesize}
                        disabled={isLoading}
                        style={{
                            background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                            color: '#fff',
                            border: 'none',
                            padding: '0.6rem 1.2rem',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontWeight: 'bold',
                            boxShadow: '0 4px 12px rgba(76, 175, 80, 0.4)'
                        }}
                    >
                        <FileText size={16} />
                        收束为报告
                    </button>
                    <button
                        onClick={onClearSelection}
                        style={{
                            background: 'transparent',
                            color: '#888',
                            border: 'none',
                            padding: '0.5rem',
                            borderRadius: '50%',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center'
                        }}
                        title="清除选择"
                        aria-label="清除选择"
                    >
                        <X size={18} />
                    </button>
                </>
            )}

            <style>{`
                @keyframes slideUp {
                    from { transform: translateX(-50%) translateY(20px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
};
