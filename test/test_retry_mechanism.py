#!/usr/bin/env python3
"""
test_retry_mechanism.py - 测试任务重试机制

功能：
- 测试任务执行失败后的自动重试
- 测试错误分析和自动修复
- 测试最大重试次数限制
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from task_planner import TaskPlanner, ExecutionPlan, TaskStep
from tool_executor import ToolExecutor


def test_error_analysis():
    """测试错误分析功能"""
    print("=" * 80)
    print("🧪 测试 1: 错误分析功能")
    print("=" * 80)
    
    planner = TaskPlanner(verbose=True)
    
    # 创建测试步骤
    step = TaskStep(
        step_id=1,
        description="测试步骤",
        skill_name="shell-executor",
        script="execute_command.py",
        args_template="python test_script.py"
    )
    
    # 测试各种错误类型
    test_cases = [
        ("ModuleNotFoundError: No module named 'requests'", "missing_module"),
        ("bash: command: command not found", "command_not_found"),
        ("Permission denied: /root/test.txt", "permission_denied"),
        ("Command timed out after 60 seconds", "timeout"),
        ("FileNotFoundError: [Errno 2] No such file or directory", "file_not_found"),
        ("SyntaxError: invalid syntax", "syntax_error"),
        ("Connection refused", "network_error"),
        ("Unknown error occurred", "unknown")
    ]
    
    for error_msg, expected_type in test_cases:
        analysis = planner.analyze_error_and_suggest_fix(step, error_msg)
        print(f"\n错误消息: {error_msg[:50]}...")
        print(f"识别类型: {analysis['error_type']}")
        print(f"建议操作: {analysis['suggested_action']}")
        print(f"可自动修复: {analysis['can_auto_fix']}")
        
        # 验证类型是否正确
        if analysis['error_type'] == expected_type or (expected_type == 'unknown' and analysis['error_type'] == 'unknown_error'):
            print("✅ 类型识别正确")
        else:
            print(f"❌ 类型识别错误（期望: {expected_type}）")


def test_tool_error_identification():
    """测试工具执行器的错误识别功能"""
    print("\n" + "=" * 80)
    print("🧪 测试 2: 工具执行器错误识别")
    print("=" * 80)
    
    executor = ToolExecutor(verbose=False)
    
    # 测试各种错误结果
    test_results = [
        ({'success': True, 'output': 'ok', 'error': ''}, 'none'),
        ({'success': False, 'output': '', 'error': "ModuleNotFoundError: No module named 'numpy'"}, 'missing_module'),
        ({'success': False, 'output': '', 'error': 'bash: xyz: command not found'}, 'command_not_found'),
        ({'success': False, 'output': '', 'error': 'Permission denied'}, 'permission_denied'),
        ({'success': False, 'output': '', 'error': 'Timed out'}, 'timeout'),
    ]
    
    for result, expected_type in test_results:
        identified_type = executor.identify_error_type(result)
        status = "✅" if identified_type == expected_type else "❌"
        print(f"{status} 错误: {result['error'][:40]:40} -> 识别为: {identified_type:20} (期望: {expected_type})")


def test_plan_validation():
    """测试计划验证功能"""
    print("\n" + "=" * 80)
    print("🧪 测试 3: 计划验证和重试检查")
    print("=" * 80)
    
    plan = ExecutionPlan("测试任务")
    
    # 添加测试步骤
    step1 = TaskStep(1, "步骤1", "skill1", "script1.py", "args1")
    step2 = TaskStep(2, "步骤2", "skill2", "script2.py", "args2")
    step3 = TaskStep(3, "步骤3", "skill3", "script3.py", "args3")
    
    plan.add_step(step1)
    plan.add_step(step2)
    plan.add_step(step3)
    
    # 测试1: 所有步骤都成功
    step1.status = 'success'
    step2.status = 'success'
    step3.status = 'success'
    
    is_complete = plan.validate_completion()
    print(f"\n场景1: 所有步骤成功")
    print(f"  完成状态: {is_complete} ✅" if is_complete else f"  完成状态: {is_complete} ❌")
    print(f"  可重试: {plan.can_retry()}")
    
    # 测试2: 部分步骤失败
    step2.status = 'failed'
    step2.error_message = "Test error"
    step2.retry_count = 0
    
    is_complete = plan.validate_completion()
    can_retry = plan.can_retry(max_retries=3)
    failed_steps = plan.get_failed_steps()
    
    print(f"\n场景2: 一个步骤失败（重试次数 0/3）")
    print(f"  完成状态: {is_complete} {'✅' if not is_complete else '❌'}")
    print(f"  可重试: {can_retry} ✅" if can_retry else f"  可重试: {can_retry} ❌")
    print(f"  失败步骤数: {len(failed_steps)}")
    
    # 测试3: 达到最大重试次数
    step2.retry_count = 3
    
    can_retry = plan.can_retry(max_retries=3)
    print(f"\n场景3: 失败步骤达到最大重试次数（3/3）")
    print(f"  可重试: {can_retry} {'✅' if not can_retry else '❌'}")
    
    # 测试4: 多个步骤失败，部分可重试
    step3.status = 'failed'
    step3.retry_count = 1
    step3.error_message = "Another error"
    
    can_retry = plan.can_retry(max_retries=3)
    failed_steps = plan.get_failed_steps()
    
    print(f"\n场景4: 两个步骤失败，一个可重试")
    print(f"  可重试: {can_retry} ✅" if can_retry else f"  可重试: {can_retry} ❌")
    print(f"  失败步骤数: {len(failed_steps)}")


def test_retry_workflow():
    """模拟完整的重试工作流程"""
    print("\n" + "=" * 80)
    print("🧪 测试 4: 完整重试流程模拟")
    print("=" * 80)
    
    from skill_runtime import SkillRuntime
    
    # 创建运行时（不初始化）
    runtime = SkillRuntime(skill_dirs=["./skills"], verbose=True)
    runtime.max_retries = 3
    
    # 创建测试计划
    plan = ExecutionPlan("测试多步骤任务")
    
    step1 = TaskStep(
        step_id=1,
        description="获取当前时间",
        skill_name="shell-executor",
        script="execute_command.py",
        args_template="date '+%Y-%m-%d %H:%M:%S'",
        extraction="first_line",
        save_to_context="current_time"
    )
    
    step2 = TaskStep(
        step_id=2,
        description="发送通知",
        skill_name="system-notifier",
        script="send_notification.py",
        args_template="--title '时间' --message '{current_time}'",
        depends_on=[1]
    )
    
    plan.add_step(step1)
    plan.add_step(step2)
    
    print(f"\n📋 创建测试计划:")
    print(f"   任务描述: {plan.task_description}")
    print(f"   步骤数量: {len(plan.steps)}")
    print(f"   最大重试次数: {runtime.max_retries}\n")
    
    # 模拟执行（这里只展示逻辑，不实际执行）
    print("ℹ️  注: 这是一个模拟测试，展示重试机制的工作流程")
    print("   实际执行需要运行: python skill_runtime.py -v --query \"你的问题\"\n")
    
    print("重试流程:")
    print("  1. 首次执行所有步骤")
    print("  2. 如果步骤失败，分析错误类型")
    print("  3. 尝试自动修复（如安装缺失的库）")
    print("  4. 重新执行失败的步骤")
    print("  5. 重复步骤 2-4，直到所有步骤成功或达到最大重试次数")
    print("  6. 生成最终报告\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 SKILL 任务重试机制测试套件")
    print("=" * 80 + "\n")
    
    try:
        test_error_analysis()
        test_tool_error_identification()
        test_plan_validation()
        test_retry_workflow()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        print("\n💡 提示: 要测试实际的自动重试功能，请运行:")
        print("   python skill_runtime.py -v --max-retries 3 --query \"执行一个可能失败的任务\"")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
