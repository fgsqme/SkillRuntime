#!/usr/bin/env python3
"""
test_ai_replan.py - 测试 AI 重新规划功能

这个脚本演示了当任务执行失败时，系统如何调用 AI 重新制定任务计划。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from task_planner import TaskPlanner, ExecutionPlan, TaskStep


def test_build_failure_context():
    """测试构建失败上下文"""
    print("=" * 80)
    print("🧪 测试: 构建失败上下文")
    print("=" * 80 + "\n")
    
    from skill_runtime import SkillRuntime
    
    # 创建运行时（不初始化）
    runtime = SkillRuntime(skill_dirs=["./skills"], verbose=True)
    
    # 创建一个模拟的执行计划
    plan = ExecutionPlan("获取时间并发送通知")
    
    step1 = TaskStep(
        step_id=1,
        description="获取当前时间",
        skill_name="shell-executor",
        script="execute_command.py",
        args_template="date '+%Y-%m-%d %H:%M:%S'",
        extraction="first_line",
        save_to_context="current_time"
    )
    step1.status = 'success'
    step1.result = "2024-01-15 10:30:00"
    
    step2 = TaskStep(
        step_id=2,
        description="发送桌面通知",
        skill_name="system-notifier",
        script="send_notification.py",
        args_template="--title '时间' --message '{current_time}'",
        depends_on=[1]
    )
    step2.status = 'failed'
    step2.error_message = "ModuleNotFoundError: No module named 'notify2'"
    step2.last_error_type = 'missing_module'
    step2.retry_count = 1
    
    step3 = TaskStep(
        step_id=3,
        description="记录日志",
        skill_name="text-file-ops",
        script="write_file.py",
        args_template="--file '/tmp/time.log' --content '{current_time}'",
        depends_on=[1]
    )
    step3.status = 'pending'
    
    plan.add_step(step1)
    plan.add_step(step2)
    plan.add_step(step3)
    
    # 添加一些上下文数据
    plan.update_context("current_time", "2024-01-15 10:30:00")
    
    # 构建失败上下文
    failure_context = runtime._build_failure_context(plan, "获取当前时间并发送通知")
    
    print("生成的失败上下文:")
    print("-" * 80)
    print(failure_context)
    print("-" * 80)
    print()
    
    # 验证上下文包含关键信息
    checks = [
        ("原始任务", "用户请求" in failure_context),
        ("成功步骤", "✅ 步骤 1" in failure_context),
        ("失败步骤", "❌ 步骤 2" in failure_context),
        ("错误信息", "ModuleNotFoundError" in failure_context),
        ("上下文数据", "current_time" in failure_context),
        ("失败总结", "失败总结" in failure_context),
    ]
    
    print("验证结果:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        all_passed = all_passed and passed
    
    print()
    if all_passed:
        print("✅ 所有检查通过！失败上下文构建正确。")
    else:
        print("❌ 部分检查失败。")
    
    return all_passed


def test_merge_successful_steps():
    """测试合并已成功步骤"""
    print("\n" + "=" * 80)
    print("🧪 测试: 合并已成功步骤")
    print("=" * 80 + "\n")
    
    from skill_runtime import SkillRuntime
    
    runtime = SkillRuntime(skill_dirs=["./skills"], verbose=True)
    
    # 创建旧计划（包含已成功的步骤）
    old_plan = ExecutionPlan("旧任务")
    
    old_step1 = TaskStep(1, "步骤1", "skill1", "script1.py", "args1")
    old_step1.status = 'success'
    old_step1.result = "Result 1"
    old_step1.extracted_data = {'value': 'data1'}
    
    old_step2 = TaskStep(2, "步骤2", "skill2", "script2.py", "args2")
    old_step2.status = 'failed'
    old_step2.error_message = "Error"
    
    old_plan.add_step(old_step1)
    old_plan.add_step(old_step2)
    old_plan.update_context("var1", "value1")
    old_plan.update_context("var2", "value2")
    
    # 创建新计划
    new_plan = ExecutionPlan("新任务")
    
    new_step1 = TaskStep(1, "步骤1（保留）", "skill1", "script1.py", "args1")
    new_step1.status = 'pending'
    
    new_step2 = TaskStep(2, "步骤2（改进）", "skill2", "new_script.py", "new_args")
    new_step2.status = 'pending'
    
    new_step3 = TaskStep(3, "步骤3（新增）", "skill3", "script3.py", "args3")
    new_step3.status = 'pending'
    
    new_plan.add_step(new_step1)
    new_plan.add_step(new_step2)
    new_plan.add_step(new_step3)
    
    print("合并前:")
    print(f"  旧计划: 成功步骤={sum(1 for s in old_plan.steps if s.status == 'success')}, "
          f"失败步骤={sum(1 for s in old_plan.steps if s.status == 'failed')}")
    print(f"  新计划: 所有步骤都是 pending 状态")
    print(f"  旧计划上下文: {old_plan.context}")
    print(f"  新计划上下文: {new_plan.context}")
    print()
    
    # 执行合并
    runtime._merge_successful_steps(old_plan, new_plan)
    
    print("合并后:")
    print(f"  新计划步骤 1 状态: {new_step1.status} (期望: success)")
    print(f"  新计划步骤 1 结果: {new_step1.result} (期望: Result 1)")
    print(f"  新计划步骤 2 状态: {new_step2.status} (期望: pending)")
    print(f"  新计划步骤 3 状态: {new_step3.status} (期望: pending)")
    print(f"  新计划上下文: {new_plan.context}")
    print()
    
    # 验证
    checks = [
        ("步骤1继承成功", new_step1.status == 'success' and new_step1.result == "Result 1"),
        ("步骤2保持pending", new_step2.status == 'pending'),
        ("步骤3保持pending", new_step3.status == 'pending'),
        ("上下文继承", 'var1' in new_plan.context and 'var2' in new_plan.context),
    ]
    
    print("验证结果:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        all_passed = all_passed and passed
    
    print()
    if all_passed:
        print("✅ 所有检查通过！步骤合并功能正常。")
    else:
        print("❌ 部分检查失败。")
    
    return all_passed


def demonstrate_replan_workflow():
    """演示完整的重新规划流程"""
    print("\n" + "=" * 80)
    print("🎬 演示: 完整的 AI 重新规划流程")
    print("=" * 80 + "\n")
    
    print("场景: 用户要求'获取当前时间并发送桌面通知'")
    print()
    
    print("【第1轮执行】")
    print("  1. AI 生成初始任务计划:")
    print("     - 步骤1: 使用 shell-executor 获取时间 ✅")
    print("     - 步骤2: 使用 system-notifier 发送通知 ❌ (缺少 notify2 库)")
    print()
    
    print("  2. 检测到步骤2失败")
    print("     错误: ModuleNotFoundError: No module named 'notify2'")
    print()
    
    print("【AI 重新规划轮次 1/3】")
    print("  3. 构建失败上下文，包含:")
    print("     - 原始用户请求")
    print("     - 步骤1的成功结果: current_time = '2024-01-15 10:30:00'")
    print("     - 步骤2的失败信息和错误类型")
    print("     - 已保存的上下文数据")
    print()
    
    print("  4. 调用 AI 重新规划，传入失败上下文")
    print("     AI 分析:")
    print("     - 问题: system-notifier 需要 notify2 库，但系统中未安装")
    print("     - 方案1: 先安装 notify2，再重试（需要额外步骤）")
    print("     - 方案2: 改用其他方式发送通知（如 write_file 写入日志）")
    print("     - 方案3: 简化任务，只返回时间不发送通知")
    print()
    
    print("  5. AI 生成新的任务计划:")
    print("     - 步骤1: [继承] 使用已获取的时间 (跳过执行)")
    print("     - 步骤2: [新] 使用 text-file-ops 将时间写入文件")
    print("     - 步骤3: [新] 使用 shell-executor 显示文件内容")
    print()
    
    print("【第2轮执行】")
    print("  6. 执行新计划:")
    print("     - 步骤1: 直接继承之前的结果 ✅")
    print("     - 步骤2: 写入文件 /tmp/time.log ✅")
    print("     - 步骤3: 读取并显示文件内容 ✅")
    print()
    
    print("  7. 所有步骤成功！任务完成 ✅")
    print()
    
    print("【最终结果】")
    print("  AI 基于执行结果生成回复:")
    print("  '我已经获取了当前时间 (2024-01-15 10:30:00)，并将其保存到")
    print("   /tmp/time.log 文件中。由于系统缺少桌面通知库，我采用了替代方案，")
    print("   将时间写入文件并显示了内容。'")
    print()
    
    print("=" * 80)
    print("💡 关键点:")
    print("  1. 不是简单重试失败的步骤")
    print("  2. 而是让 AI 分析失败原因，制定全新的计划")
    print("  3. 保留已成功步骤的结果，避免重复执行")
    print("  4. AI 可以提出完全不同的解决方案")
    print("=" * 80)


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 SKILL AI 重新规划功能测试")
    print("=" * 80 + "\n")
    
    try:
        result1 = test_build_failure_context()
        result2 = test_merge_successful_steps()
        demonstrate_replan_workflow()
        
        print("\n" + "=" * 80)
        if result1 and result2:
            print("✅ 所有测试通过！")
        else:
            print("⚠️  部分测试未通过，请检查实现")
        print("=" * 80)
        
        print("\n💡 提示: 要测试实际的 AI 重新规划功能，请运行:")
        print("   python skill_runtime.py -v --max-retries 3 --query \"获取时间并发送通知\"")
        print("\n注意: 实际测试需要:")
        print("  1. API 连接正常")
        print("  2. 某些技能依赖缺失（触发失败）")
        print("  3. AI 能够生成合理的替代方案")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
