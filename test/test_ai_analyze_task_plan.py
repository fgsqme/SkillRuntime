#!/usr/bin/env python3
"""
test_ai_analyze_task_plan.py - 测试在任务计划中使用 AI 智能数据提取

演示一个完整的任务流程，其中使用 ai_analyze 来智能提取脚本输出
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from skill_runtime import SkillRuntime


def test_task_with_ai_analyze():
    """测试包含 ai_analyze 的任务计划"""
    
    print("=" * 80)
    print("🚀 测试任务计划中的 AI 智能数据提取")
    print("=" * 80)
    
    # 初始化运行时
    runtime = SkillRuntime(
        skill_dirs=["./skills"],
        api_url="http://localhost:8080",
        api_key="test",
        verbose=True
    )
    
    # 模拟一个需要 AI 分析输出的任务计划
    task_plan_json = '''
{
  "task_plan": {
    "description": "获取系统关键信息并生成报告",
    "steps": [
      {
        "step_id": 1,
        "description": "获取系统基本信息",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "uname -a && hostname && whoami",
        "depends_on": [],
        "extraction": "ai_analyze",
        "save_to_context": "system_basic_info"
      },
      {
        "step_id": 2,
        "description": "获取资源使用情况",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "df -h / && free -m",
        "depends_on": [],
        "extraction": "ai_analyze",
        "save_to_context": "resource_usage"
      },
      {
        "step_id": 3,
        "description": "生成综合报告",
        "skill_name": "text-file-ops",
        "script": "write_file.py",
        "args": "--file '/tmp/system_report.txt' --content '系统基本信息: {system_basic_info}\\n\\n资源使用情况: {resource_usage}'",
        "depends_on": [1, 2],
        "extraction": null,
        "save_to_context": null
      }
    ]
  }
}
'''
    
    print("\n📋 任务计划:")
    print(task_plan_json)
    
    # 解析任务计划
    plan = task_planner.parse_task_plan(task_plan_json)
    
    if not plan:
        print("❌ 任务计划解析失败")
        return
    
    print(f"\n✅ 任务计划解析成功!")
    print(f"   任务描述: {plan.task_description}")
    print(f"   步骤数量: {len(plan.steps)}\n")
    
    for step in plan.steps:
        print(f"   步骤 {step.step_id}: {step.description}")
        print(f"      Skill: {step.skill_name}")
        print(f"      Script: {step.script}")
        print(f"      Extraction: {step.extraction}")
        print(f"      Save to Context: {step.save_to_context}\n")
    
    print("\n" + "=" * 80)
    print("💡 说明")
    print("=" * 80)
    print("""
在这个任务计划中：

1. 步骤 1 和 2 使用 "extraction": "ai_analyze"
   - AI 会智能分析命令输出，提取最关键的信息
   - 例如从 uname -a 的输出中提取操作系统版本
   - 例如从 df -h 和 free -m 中提取磁盘和内存使用率

2. 步骤 3 使用提取的上下文数据生成报告
   - {system_basic_info} 来自步骤 1 的 AI 提取结果
   - {resource_usage} 来自步骤 2 的 AI 提取结果

与传统方式对比：
- first_line: 只能取第一行，可能不是最有价值的信息
- regex: 需要预先知道格式，不够灵活
- ai_analyze: AI 理解语义，自动提取最关键信息
    """)
    
    print("\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_task_with_ai_analyze()
