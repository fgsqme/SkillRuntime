#!/usr/bin/env python3
"""
test_subtask.py - 子任务拆分功能测试

测试内容：
1. TaskStep 子任务字段
2. parse_sub_task_plan 解析
3. needs_decompose 标记解析
4. 子任务执行流程（模拟）
5. 验证机制（模拟）
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_planner import TaskPlanner, TaskStep, ExecutionPlan


def test_task_step_subtask_fields():
    """测试 1: TaskStep 子任务相关字段"""
    print("=" * 60)
    print("测试 1: TaskStep 子任务字段")
    print("=" * 60)
    
    step = TaskStep(
        step_id=1,
        description="创建项目文件夹",
        skill_name="shell-executor",
        script="execute_command.py",
        args_template="mkdir -p project/src"
    )
    
    # 验证默认值
    assert step.has_subtasks == False, "has_subtasks 默认值应为 False"
    assert step.sub_task_plan is None, "sub_task_plan 默认值应为 None"
    assert step.parent_step_id is None, "parent_step_id 默认值应为 None"
    assert step.needs_decompose == False, "needs_decompose 默认值应为 False"
    assert step.verification_result is None, "verification_result 默认值应为 None"
    
    # 设置子任务标记
    step.needs_decompose = True
    step.has_subtasks = True
    
    # 验证 to_dict 包含新字段
    step_dict = step.to_dict()
    assert 'has_subtasks' in step_dict, "to_dict 应包含 has_subtasks"
    assert 'parent_step_id' in step_dict, "to_dict 应包含 parent_step_id"
    assert 'needs_decompose' in step_dict, "to_dict 应包含 needs_decompose"
    assert step_dict['has_subtasks'] == True
    assert step_dict['needs_decompose'] == True
    
    print("✅ TaskStep 子任务字段测试通过")
    print(f"   has_subtasks: {step.has_subtasks}")
    print(f"   needs_decompose: {step.needs_decompose}")
    print(f"   parent_step_id: {step.parent_step_id}")
    print()


def test_parse_task_plan_with_needs_decompose():
    """测试 2: 解析包含 needs_decompose 的任务计划"""
    print("=" * 60)
    print("测试 2: 解析包含 needs_decompose 的任务计划")
    print("=" * 60)
    
    planner = TaskPlanner(verbose=False)
    
    ai_response = '''
{
  "task_plan": {
    "description": "创建一个新的 Python 项目",
    "steps": [
      {
        "step_id": 1,
        "description": "创建项目文件夹结构",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p myproject/src myproject/tests",
        "depends_on": [],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null,
        "needs_decompose": true
      },
      {
        "step_id": 2,
        "description": "创建代码文件",
        "skill_name": "text-file-ops",
        "script": "write_file.py",
        "args": "myproject/src/main.py 'print(hello)'",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null,
        "needs_decompose": true
      },
      {
        "step_id": 3,
        "description": "验证项目结构",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "find myproject -type f",
        "depends_on": [2],
        "extraction": "smart",
        "save_to_context": null,
        "context_prompt": null,
        "needs_decompose": false
      }
    ]
  }
}
'''
    
    plan = planner.parse_task_plan(ai_response)
    
    assert plan is not None, "解析不应返回 None"
    assert len(plan.steps) == 3, f"应有 3 个步骤，实际 {len(plan.steps)}"
    
    # 验证 needs_decompose 标记
    assert plan.steps[0].needs_decompose == True, "步骤 1 应标记 needs_decompose"
    assert plan.steps[1].needs_decompose == True, "步骤 2 应标记 needs_decompose"
    assert plan.steps[2].needs_decompose == False, "步骤 3 不应标记 needs_decompose"
    
    print("✅ 解析包含 needs_decompose 的任务计划测试通过")
    print(f"   任务: {plan.task_description}")
    for step in plan.steps:
        print(f"   步骤 {step.step_id}: {step.description} (needs_decompose={step.needs_decompose})")
    print()


def test_parse_sub_task_plan():
    """测试 3: 解析子任务计划"""
    print("=" * 60)
    print("测试 3: 解析子任务计划")
    print("=" * 60)
    
    planner = TaskPlanner(verbose=False)
    
    # AI 返回的子任务计划
    ai_response = '''
{
  "sub_task_plan": {
    "description": "创建项目文件夹结构的子任务",
    "parent_step_id": 1,
    "steps": [
      {
        "step_id": 1,
        "description": "创建项目根目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p myproject",
        "depends_on": [],
        "extraction": null,
        "save_to_context": "project_dir",
        "context_prompt": "项目根目录路径"
      },
      {
        "step_id": 2,
        "description": "创建 src 子目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p {project_dir}/src",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null
      },
      {
        "step_id": 3,
        "description": "创建 tests 子目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p {project_dir}/tests",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null
      },
      {
        "step_id": 4,
        "description": "验证目录创建结果",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "ls -la {project_dir}",
        "depends_on": [2, 3],
        "extraction": "smart",
        "save_to_context": null,
        "context_prompt": null
      }
    ]
  }
}
'''
    
    sub_plan = planner.parse_sub_task_plan(ai_response)
    
    assert sub_plan is not None, "子任务计划解析不应返回 None"
    assert len(sub_plan.steps) == 4, f"应有 4 个子步骤，实际 {len(sub_plan.steps)}"
    
    # 验证 parent_step_id
    for step in sub_plan.steps:
        assert step.parent_step_id == 1, f"子步骤 {step.step_id} 的 parent_step_id 应为 1"
    
    print("✅ 解析子任务计划测试通过")
    print(f"   子任务: {sub_plan.task_description}")
    print(f"   父步骤 ID: {sub_plan.steps[0].parent_step_id}")
    for step in sub_plan.steps:
        print(f"   子步骤 {step.step_id}: {step.description}")
    print()


def test_parse_sub_task_plan_no_decompose():
    """测试 4: AI 判断不需要拆分（单步骤）"""
    print("=" * 60)
    print("测试 4: AI 判断不需要拆分")
    print("=" * 60)
    
    planner = TaskPlanner(verbose=False)
    
    # AI 返回单步骤（表示不需要拆分）
    ai_response = '''
{
  "sub_task_plan": {
    "description": "无需拆分",
    "parent_step_id": 1,
    "steps": [
      {
        "step_id": 1,
        "description": "创建目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p myproject",
        "depends_on": [],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null
      }
    ]
  }
}
'''
    
    sub_plan = planner.parse_sub_task_plan(ai_response)
    
    assert sub_plan is None, "单步骤子任务应返回 None（不需要拆分）"
    
    print("✅ AI 判断不需要拆分测试通过")
    print("   单步骤子任务正确返回 None")
    print()


def test_parse_sub_task_plan_no_field():
    """测试 5: AI 返回不包含 sub_task_plan 字段"""
    print("=" * 60)
    print("测试 5: AI 返回不包含 sub_task_plan 字段")
    print("=" * 60)
    
    planner = TaskPlanner(verbose=False)
    
    # 没有 sub_task_plan 字段
    ai_response = '''
{
  "message": "这个步骤已经是原子操作，不需要拆分"
}
'''
    
    sub_plan = planner.parse_sub_task_plan(ai_response)
    
    assert sub_plan is None, "缺少 sub_task_plan 字段应返回 None"
    
    print("✅ 缺少 sub_task_plan 字段测试通过")
    print("   正确返回 None")
    print()


def test_execution_plan_with_subtasks():
    """测试 6: ExecutionPlan 包含子任务的完整流程"""
    print("=" * 60)
    print("测试 6: ExecutionPlan 包含子任务的完整流程")
    print("=" * 60)
    
    planner = TaskPlanner(verbose=False)
    
    # 先解析主任务计划
    main_plan_response = '''
{
  "task_plan": {
    "description": "创建 Python 项目",
    "steps": [
      {
        "step_id": 1,
        "description": "创建文件夹结构",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p project",
        "depends_on": [],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null,
        "needs_decompose": true
      },
      {
        "step_id": 2,
        "description": "验证创建结果",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "ls -la project",
        "depends_on": [1],
        "extraction": "smart",
        "save_to_context": null,
        "context_prompt": null
      }
    ]
  }
}
'''
    
    main_plan = planner.parse_task_plan(main_plan_response)
    assert main_plan is not None
    
    # 模拟：为步骤 1 设置子任务计划
    sub_plan_response = '''
{
  "sub_task_plan": {
    "description": "创建文件夹结构子任务",
    "parent_step_id": 1,
    "steps": [
      {
        "step_id": 1,
        "description": "创建根目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p project",
        "depends_on": [],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null
      },
      {
        "step_id": 2,
        "description": "创建 src 目录",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p project/src",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null,
        "context_prompt": null
      },
      {
        "step_id": 3,
        "description": "验证目录创建",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "find project -type d",
        "depends_on": [2],
        "extraction": "smart",
        "save_to_context": null,
        "context_prompt": null
      }
    ]
  }
}
'''
    
    sub_plan = planner.parse_sub_task_plan(sub_plan_response)
    assert sub_plan is not None
    
    # 将子任务计划关联到父步骤
    main_plan.steps[0].has_subtasks = True
    main_plan.steps[0].sub_task_plan = sub_plan
    
    # 验证完整结构
    assert main_plan.steps[0].has_subtasks == True
    assert main_plan.steps[0].sub_task_plan is not None
    assert len(main_plan.steps[0].sub_task_plan.steps) == 3
    
    # 验证 to_dict 包含子任务信息
    plan_dict = main_plan.to_dict()
    step1_dict = plan_dict['steps'][0]
    assert step1_dict['has_subtasks'] == True
    assert step1_dict['sub_task_plan'] is not None
    assert len(step1_dict['sub_task_plan']['steps']) == 3
    
    print("✅ ExecutionPlan 包含子任务的完整流程测试通过")
    print(f"   主任务: {main_plan.task_description}")
    print(f"   步骤 1: {main_plan.steps[0].description} (has_subtasks=True)")
    print(f"     子任务数: {len(main_plan.steps[0].sub_task_plan.steps)}")
    for sub_step in main_plan.steps[0].sub_task_plan.steps:
        print(f"       子步骤 {sub_step.step_id}: {sub_step.description}")
    print(f"   步骤 2: {main_plan.steps[1].description} (has_subtasks=False)")
    print()


def test_subtask_prompt_template():
    """测试 7: 子任务提示词模板加载"""
    print("=" * 60)
    print("测试 7: 子任务提示词模板加载")
    print("=" * 60)
    
    from pathlib import Path
    
    prompt_path = Path(__file__).parent / "prompts" / "subtask_prompt.txt"
    assert prompt_path.exists(), f"提示词模板文件不存在: {prompt_path}"
    
    template = prompt_path.read_text(encoding='utf-8')
    
    # 验证模板包含必要的占位符
    assert '{step_id}' in template, "模板应包含 {step_id}"
    assert '{step_description}' in template, "模板应包含 {step_description}"
    assert '{skill_name}' in template, "模板应包含 {skill_name}"
    assert '{script}' in template, "模板应包含 {script}"
    assert '{args}' in template, "模板应包含 {args}"
    assert '{parent_task_description}' in template, "模板应包含 {parent_task_description}"
    assert '{completed_results}' in template, "模板应包含 {completed_results}"
    assert 'sub_task_plan' in template, "模板应包含 sub_task_plan"
    
    # 测试模板填充
    filled = template.format(
        step_id=1,
        step_description="创建项目文件夹",
        skill_name="shell-executor",
        script="execute_command.py",
        args="mkdir -p project",
        parent_task_description="创建 Python 项目",
        parent_context="无额外上下文",
        completed_results="无已完成步骤"
    )
    
    assert '创建项目文件夹' in filled
    assert 'shell-executor' in filled
    assert '创建 Python 项目' in filled
    
    print("✅ 子任务提示词模板加载测试通过")
    print(f"   模板长度: {len(template)} 字符")
    print(f"   填充后长度: {len(filled)} 字符")
    print()


def test_verification_result_structure():
    """测试 8: 验证结果数据结构"""
    print("=" * 60)
    print("测试 8: 验证结果数据结构")
    print("=" * 60)
    
    plan = ExecutionPlan("测试任务")
    
    # 添加步骤
    step1 = TaskStep(1, "步骤1", "shell-executor", "execute_command.py", "echo hello")
    step1.status = 'success'
    step1.result = "hello"
    plan.add_step(step1)
    
    # 模拟验证结果
    verification_result = {
        'passed': True,
        'confidence': 0.95,
        'reason': '所有步骤执行成功，输出符合预期',
        'issues': []
    }
    
    plan.verification_result = verification_result
    
    assert plan.verification_result is not None
    assert plan.verification_result['passed'] == True
    assert plan.verification_result['confidence'] == 0.95
    
    print("✅ 验证结果数据结构测试通过")
    print(f"   passed: {plan.verification_result['passed']}")
    print(f"   confidence: {plan.verification_result['confidence']}")
    print(f"   reason: {plan.verification_result['reason']}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 子任务拆分功能测试")
    print("=" * 60 + "\n")
    
    tests = [
        test_task_step_subtask_fields,
        test_parse_task_plan_with_needs_decompose,
        test_parse_sub_task_plan,
        test_parse_sub_task_plan_no_decompose,
        test_parse_sub_task_plan_no_field,
        test_execution_plan_with_subtasks,
        test_subtask_prompt_template,
        test_verification_result_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__} 失败: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 异常: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
