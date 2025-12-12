"""
SpecKit Compliance Checker - 规范合规性检查脚本

增强版检查功能：
1. 验证 tasks.md 格式
2. 验证 spec.md 中提及的模块是否存在
3. 验证所有代理文件是否与规范一致
4. 验证 API 端点是否与 server.py 匹配
5. 生成一致性报告
"""

import re
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Set


class SpecKitChecker:
    """SpecKit 合规性检查器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.docs_dir = base_dir / "docs" / "spec-kit"
        self.src_dir = base_dir / "src"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
    
    def check_all(self) -> bool:
        """运行所有检查"""
        print("=" * 60)
        print("SpecKit Compliance Checker v2.0")
        print("=" * 60)
        
        checks = [
            ("Tasks.md Format", self.check_tasks_md),
            ("Spec.md Existence", self.check_spec_exists),
            ("Agent Modules", self.check_agent_modules),
            ("Core Modules", self.check_core_modules),
            ("Math Engine Modules", self.check_math_engine_modules),
            ("Server Endpoints", self.check_server_endpoints),
            ("Knowledge Base Tools", self.check_knowledge_base_tools),
        ]
        
        for name, check_fn in checks:
            print(f"\n[Checking] {name}...")
            try:
                check_fn()
            except Exception as e:
                self.errors.append(f"{name}: 检查过程出错 - {e}")
        
        self._print_summary()
        return len(self.errors) == 0
    
    def check_tasks_md(self):
        """检查 tasks.md 格式"""
        tasks_path = self.docs_dir / "tasks.md"
        
        if not tasks_path.exists():
            self.errors.append(f"tasks.md 文件不存在: {tasks_path}")
            return
        
        content = tasks_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        # 匹配任务行: | T-XXX | Description | Owner | Status | Docs |
        task_pattern = re.compile(r"^\|\s*(T-\d+)\s*\|.*\|.*\|.*\|\s*([^|]+)\s*\|$")
        task_count = 0
        missing_docs = 0
        
        for i, line in enumerate(lines, 1):
            match = task_pattern.match(line)
            if match:
                task_id = match.group(1)
                docs_col = match.group(2).strip()
                task_count += 1
                
                if not docs_col or docs_col.lower() == "todo":
                    self.warnings.append(f"任务 {task_id} (行 {i}) 缺少文档链接")
                    missing_docs += 1
        
        if task_count > 0:
            self.passed.append(f"tasks.md: 找到 {task_count} 个任务条目")
            if missing_docs > 0:
                self.warnings.append(f"tasks.md: {missing_docs} 个任务缺少文档链接")
        else:
            self.warnings.append("tasks.md: 未找到符合格式的任务条目")
    
    def check_spec_exists(self):
        """检查 spec.md 是否存在且非空"""
        spec_path = self.docs_dir / "spec.md"
        
        if not spec_path.exists():
            self.errors.append(f"spec.md 文件不存在: {spec_path}")
            return
        
        content = spec_path.read_text(encoding="utf-8")
        if len(content) < 1000:
            self.warnings.append(f"spec.md 内容过短 ({len(content)} 字符)，可能不完整")
        else:
            self.passed.append(f"spec.md: 存在且内容充足 ({len(content)} 字符)")
        
        # 检查关键章节
        required_sections = [
            "背景与目标",
            "系统架构",
            "核心代理规范",
            "状态管理",
            "API 端点规范",
        ]
        
        for section in required_sections:
            if section not in content:
                self.warnings.append(f"spec.md: 缺少 '{section}' 章节")
            else:
                self.passed.append(f"spec.md: 包含 '{section}' 章节")
    
    def check_agent_modules(self):
        """检查所有代理模块是否存在"""
        agents_dir = self.src_dir / "agents"
        
        required_agents = [
            ("task_decomposer.py", "TaskDecomposer"),
            ("researcher.py", "Researcher"),
            ("strategy_generator.py", "StrategyGenerator"),
            ("judge.py", "Judge"),
            ("evolution.py", "Evolution"),
            ("architect.py", "ArchitectScheduler"),
            ("executor.py", "Executor"),
            ("distiller.py", "Distiller"),
        ]
        
        for filename, agent_name in required_agents:
            agent_path = agents_dir / filename
            if agent_path.exists():
                self.passed.append(f"Agent: {agent_name} ({filename}) 存在")
            else:
                self.errors.append(f"Agent: {agent_name} ({filename}) 不存在于 {agents_dir}")
    
    def check_core_modules(self):
        """检查核心模块是否存在"""
        core_dir = self.src_dir / "core"
        
        required_modules = [
            ("graph_builder.py", "Graph Builder"),
            ("state.py", "State Definitions"),
        ]
        
        for filename, module_name in required_modules:
            module_path = core_dir / filename
            if module_path.exists():
                self.passed.append(f"Core: {module_name} ({filename}) 存在")
            else:
                self.errors.append(f"Core: {module_name} ({filename}) 不存在于 {core_dir}")
    
    def check_math_engine_modules(self):
        """检查数学引擎模块是否存在"""
        math_dir = self.src_dir / "math_engine"
        
        required_modules = [
            ("kde.py", "KDE Density Estimation"),
            ("temperature.py", "Temperature Model"),
            ("ucb.py", "UCB Calculation"),
        ]
        
        for filename, module_name in required_modules:
            module_path = math_dir / filename
            if module_path.exists():
                self.passed.append(f"MathEngine: {module_name} ({filename}) 存在")
            else:
                self.errors.append(f"MathEngine: {module_name} ({filename}) 不存在于 {math_dir}")
    
    def check_server_endpoints(self):
        """检查 server.py 中的端点是否符合规范"""
        server_path = self.base_dir / "server.py"
        
        if not server_path.exists():
            self.errors.append("server.py 不存在")
            return
        
        content = server_path.read_text(encoding="utf-8")
        
        # 规范中定义的端点
        required_endpoints = [
            ("/health", "健康检查"),
            ("/api/models", "模型列表"),
            ("/api/simulation/start", "启动模拟"),
            ("/api/simulation/stop", "停止模拟"),
            ("/api/expand_node", "节点展开"),
            ("/api/chat/stream", "流式聊天"),
            ("/api/hil/response", "HIL响应"),
            ("/ws/knowledge_base", "知识库WebSocket"),
            ("/ws/simulation", "模拟WebSocket"),
        ]
        
        for endpoint, description in required_endpoints:
            # 检查端点是否存在于代码中
            if endpoint in content or endpoint.replace("/", r"\/") in content:
                self.passed.append(f"Endpoint: {endpoint} ({description}) 存在")
            else:
                self.warnings.append(f"Endpoint: {endpoint} ({description}) 未在 server.py 中找到")
    
    def check_knowledge_base_tools(self):
        """检查知识库工具是否存在"""
        tools_dir = self.src_dir / "tools"
        
        required_tools = [
            ("knowledge_base.py", "Knowledge Base Tools"),
            ("ask_human.py", "HIL Tools"),
        ]
        
        for filename, tool_name in required_tools:
            tool_path = tools_dir / filename
            if tool_path.exists():
                self.passed.append(f"Tool: {tool_name} ({filename}) 存在")
            else:
                self.errors.append(f"Tool: {tool_name} ({filename}) 不存在于 {tools_dir}")
    
    def _print_summary(self):
        """打印检查摘要"""
        print("\n" + "=" * 60)
        print("检查摘要")
        print("=" * 60)
        
        print(f"\n✅ 通过: {len(self.passed)}")
        for item in self.passed[:10]:  # 只显示前10个
            print(f"   • {item}")
        if len(self.passed) > 10:
            print(f"   ... 及其他 {len(self.passed) - 10} 项")
        
        if self.warnings:
            print(f"\n⚠️ 警告: {len(self.warnings)}")
            for item in self.warnings:
                print(f"   • {item}")
        
        if self.errors:
            print(f"\n❌ 错误: {len(self.errors)}")
            for item in self.errors:
                print(f"   • {item}")
        
        print("\n" + "-" * 60)
        if self.errors:
            print("[Spec-FAIL] 规范检查失败")
        elif self.warnings:
            print("[Spec-OK] 规范检查通过 (有警告)")
        else:
            print("[Spec-OK] 规范检查全部通过")


def main():
    base_dir = Path(__file__).resolve().parent.parent
    
    checker = SpecKitChecker(base_dir)
    success = checker.check_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
