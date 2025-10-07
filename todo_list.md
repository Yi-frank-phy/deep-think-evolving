# Project Prometheus: Improvement Todo List

This document outlines the key areas for improvement for the Project Prometheus framework, translating the initial critique into a list of actionable development tasks. The focus is on enhancing Human-Computer Interaction (HCI), system observability, cost management, and leveraging advanced AI model features.

---

- [ ] **测试基线**：在每个迭代结束时运行 `pytest`（或 `npm run test`）验证后端流水线。

### **Area 1: UI/UX & System Observability (The "Control Tower")**

**Critique:** The current design places a high cognitive load on the "Architect" and operates as a "black box," lacking transparency into the system's internal processes.

- [ ] **Task 1.1: Implement Real-Time Task Graph Visualization**
    - [ ] Render the "Emergent Task Graph" dynamically in the frontend.
    - [ ] Use visual cues for node status (e.g., size for credibility score, color for state: active, paused, pruned).
    - [ ] Implement an interactive feature where clicking a node reveals its detailed "Evidence Board," associated Agent conversations, and resource allocation.

- [ ] **Task 1.2: Develop a Key Performance Indicator (KPI) Dashboard**
    - [ ] Display critical real-time metrics: cumulative API cost, number of active tasks, total explored paths, and the current best solution's score.
    - [ ] Ensure the dashboard is the central view for the "Architect" to monitor the system's health and progress at a glance.

- [ ] **Task 1.3: Create a Guided Setup Wizard**
    - [ ] Replace the abstract initial configuration with an interactive, step-by-step wizard.
    - [ ] The wizard should suggest default "evolution modes," "success metrics," and model configurations based on user-selected problem archetypes (e.g., "Open-ended Research," "Code Optimization").

---

### **Area 2: Human-in-the-Loop Interaction**

**Critique:** The human intervention mechanism is vaguely defined, limiting the potential for effective human-AI collaboration.

- [ ] **Task 2.1: Implement Visual Conditional Breakpoints**
    - [ ] Allow users to set intervention points directly on the visualized task graph.
    - [ ] Define rules for these breakpoints, such as: "Pause if a node's credibility score remains below 0.2 for three consecutive cycles" or "Require confirmation before escalating a task to the 'Expert' model."

- [ ] **Task 2.2: Design a Context-Aware Intervention UI**
    - [ ] When a breakpoint is hit, the UI should automatically focus on the relevant node.
    - [ ] Present a clear, concise summary of the situation, including pro/con evidence and Agent reasoning.
    - [ ] Provide explicit action buttons for the user, such as `[Force Continue]`, `[Prune Branch]`, `[Provide Corrective Feedback]`, or `[Manually Edit Task]`.

---

### **Area 3: Advanced AI Model Integration (Gemini API)**

**Critique:** The framework's model usage is too rigid and does not fully exploit the capabilities of modern multimodal models like Gemini.

- [ ] **Task 3.1: Implement Dynamic Model Configuration**
    - [ ] The "Capability Gradient Scheduling" should not just switch models. Before escalating (e.g., from `gemini-2.5-flash`), the system should first attempt to dynamically adjust the current model's parameters (e.g., increase `thinkingConfig.thinkingBudget`) to achieve better results more cost-effectively.

- [ ] **Task 3.2: Enforce Structured Outputs with `responseSchema`**
    - [ ] Mandate the use of Gemini's `responseSchema` for any Agent that produces structured data (especially the "Scorer Agent").
    - [ ] This will ensure data consistency, eliminate fragile text-parsing logic, and improve overall system robustness.

- [ ] **Task 3.3: Integrate Google Search for Grounding**
    - [ ] For research-oriented tasks, explicitly add the `googleSearch` tool to the available tools for Agents.
    - [ ] Ensure that any information retrieved from the web is properly cited, and display the source URLs in the UI to enhance the final report's credibility.

---

### **Area 4: Cost & Performance Management**

**Critique:** The core principle of "Cost-Effectiveness First" is not supported by any concrete mechanisms, posing a significant financial risk.

- [ ] **Task 4.1: Implement Budget Controls and Alerting**
    - [ ] The system setup must require the user to define a hard budget limit for API calls.
    - [ ] Implement a monitoring service that tracks spending and automatically pauses the system when the budget threshold (e.g., 90%) is reached, pending user approval to continue.

- [ ] **Task 4.2: Track and Display Granular Performance Metrics**
    - [ ] Beyond cost, the dashboard should track operational metrics: average task resolution time, ratio of model usage (`Explorer` vs. `Analyst` vs. `Expert`), and the average lifecycle of pruned nodes.
    - [ ] This data will provide the "Architect" with deeper insights to refine future configurations.
