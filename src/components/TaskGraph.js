"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TaskGraph = void 0;
var react_1 = require("react");
var reactflow_1 = require("reactflow");
require("reactflow/dist/style.css");
var TaskGraph = function (_a) {
    var state = _a.state, onNodeClick = _a.onNodeClick;
    var _b = (0, reactflow_1.useNodesState)([]), nodes = _b[0], setNodes = _b[1], onNodesChange = _b[2];
    var _c = (0, reactflow_1.useEdgesState)([]), edges = _c[0], setEdges = _c[1], onEdgesChange = _c[2];
    (0, react_1.useEffect)(function () {
        if (!state || !state.strategies)
            return;
        // --- Tree Layout Logic ---
        // 1. Build Adjacency List & Find Roots
        var stratMap = new Map();
        var childrenMap = new Map();
        var roots = [];
        state.strategies.forEach(function (s) {
            var _a;
            stratMap.set(s.id, s);
            var pid = s.parent_id;
            if (pid) {
                if (!childrenMap.has(pid))
                    childrenMap.set(pid, []);
                (_a = childrenMap.get(pid)) === null || _a === void 0 ? void 0 : _a.push(s.id);
            }
            else {
                roots.push(s.id);
            }
        });
        // 2. BFS for Level Assignment
        var levels = new Map();
        var queue = roots.map(function (r) { return ({ id: r, level: 0 }); });
        var maxLevelWidth = []; // Count nodes per level to assign X
        var _loop_1 = function () {
            var _a = queue.shift(), id = _a.id, level = _a.level;
            levels.set(id, level);
            // Track width
            maxLevelWidth[level] = (maxLevelWidth[level] || 0) + 1;
            var children = childrenMap.get(id) || [];
            children.forEach(function (childId) { return queue.push({ id: childId, level: level + 1 }); });
        };
        while (queue.length > 0) {
            _loop_1();
        }
        // 3. Assign Positions
        var levelCurrentX = []; // Track current X index for each level
        var newNodes = state.strategies.map(function (strat) {
            var _a, _b;
            var level = levels.get(strat.id) || 0;
            var levelIdx = levelCurrentX[level] || 0;
            levelCurrentX[level] = levelIdx + 1;
            var width = maxLevelWidth[level] || 1;
            // Center buttons: total width ~ width * 250
            // x = (levelIdx - width/2) * 220
            var x = (levelIdx - width / 2) * 240;
            var y = level * 180;
            var isActive = strat.status === 'active';
            var isPruned = strat.status === 'pruned' || strat.status === 'pruned_beam';
            var isExpanded = strat.status === 'expanded';
            var borderColor = '#666';
            if (isActive)
                borderColor = '#4CAF50';
            else if (isPruned)
                borderColor = '#f44336';
            else if (isExpanded)
                borderColor = '#2196F3';
            return {
                id: strat.id,
                position: { x: x, y: y },
                data: {
                    label: "".concat(strat.name, "\n(S:").concat((_b = (_a = strat.score) === null || _a === void 0 ? void 0 : _a.toFixed(2)) !== null && _b !== void 0 ? _b : '?', ")")
                },
                style: {
                    background: '#1a1a1a',
                    color: '#fff',
                    border: "1px solid ".concat(borderColor),
                    borderLeft: "4px solid ".concat(borderColor),
                    width: 200,
                    borderRadius: '8px',
                    fontSize: '11px',
                    padding: '8px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                    opacity: isPruned ? 0.6 : 1,
                    textAlign: 'left',
                    whiteSpace: 'pre-wrap'
                },
            };
        });
        // 4. Create Edges
        var newEdges = [];
        state.strategies.forEach(function (s) {
            if (s.parent_id) {
                newEdges.push({
                    id: "e-".concat(s.parent_id, "-").concat(s.id),
                    source: s.parent_id,
                    target: s.id,
                    type: 'smoothstep',
                    animated: s.status === 'active',
                    style: { stroke: '#555' }
                });
            }
        });
        setNodes(newNodes);
        setEdges(newEdges);
        // ⚡ Bolt: Optimize re-renders by only updating layout when strategies change,
        // ignoring other state updates like logs, iteration counts, or metrics.
    }, [state === null || state === void 0 ? void 0 : state.strategies, setNodes, setEdges]);
    return (<div className="task-graph-container" style={{
            flex: 1,
            background: '#111',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            minHeight: '400px',
            position: 'relative' // Needed for ReactFlow
        }}>
            <reactflow_1.default nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={function (_, node) {
            // Find the original StrategyNode based on ID or index
            if (!(state === null || state === void 0 ? void 0 : state.strategies))
                return;
            // Our IDs are strat-${index} or strat.id
            var strategy = state.strategies.find(function (s, i) {
                return (s.id && s.id === node.id) || "strat-".concat(i) === node.id;
            });
            if (strategy && onNodeClick) {
                onNodeClick(strategy);
            }
        }} fitView>
                <reactflow_1.Background color="#333" gap={16}/>
                <reactflow_1.Controls />
            </reactflow_1.default>

            {!state && (<div style={{
                position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                color: '#666', pointerEvents: 'none'
            }}>
                    Waiting for Simulation Data...
                </div>)}
        </div>);
};
exports.TaskGraph = TaskGraph;
