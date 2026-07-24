#!/usr/bin/env python3
"""
test_iterative_tool_calls.py - 测试多次工具调用迭代功能

这个脚本演示了当 AI 第一次返回的工具调用失败后，系统如何再次调用 AI
并执行修正后的工具调用。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def test_build_iterative_prompt():
    """测试构建迭代 prompt"""
    print("=" * 80)
    print("🧪 测试: 构建迭代 Prompt")
    print("=" * 80 + "\n")
    
    from skill_runtime import SkillRuntime
    
    # 创建运行时（不初始化）
    runtime = SkillRuntime(skill_dirs=["./skills"], verbose=True)
    
    # 模拟执行历史
    execution_history = [
        {
            'iteration': 1,
            'ai_response': '''```json
{
  "tool_call": {
    "skill_name": "pdf-generator",
    "script": "generate_pdf.py",
    "args": "content='测试文本'"
  }
}
```''',
            'tool_calls': [{
                'skill_name': 'pdf-generator',
                'script': 'generate_pdf.py',
                'args': "content='测试文本'"
            }],
            'results': [
                '\n【工具执行结果】\nSkill: pdf-generator\n命令: content=\'测试文本\'\n状态: ❌ 失败\n\n错误:\n```\nusage: generate_pdf.py [-h] --input-type {text,markdown,html} ...\n```'
            ]
        }
    ]
    
    # 构建迭代 prompt
    iterative_prompt = runtime._build_iterative_prompt(
        "生成一个测试pdf 创建一个文本 '测试文本'",
        execution_history
    )
    
    print("生成的迭代 Prompt:")
    print("-" * 80)
    print(iterative_prompt)
    print("-" * 80)
    print()
    
    # 验证 prompt 包含关键信息
    checks = [
        ("原始请求", "生成一个测试pdf" in iterative_prompt),
        ("执行历史", "第 1 次尝试" in iterative_prompt),
        ("AI 响应", "pdf-generator" in iterative_prompt),
        ("执行结果", "❌ 失败" in iterative_prompt),
        ("重要提示", "请分析原因并修正参数" in iterative_prompt),
    ]
    
    print("验证结果:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        all_passed = all_passed and passed
    
    print()
    if all_passed:
        print("✅ 所有检查通过！迭代 Prompt 构建正确。")
    else:
        print("❌ 部分检查失败。")
    
    return all_passed


def test_build_final_prompt():
    """测试构建最终回复 prompt"""
    print("\n" + "=" * 80)
    print("🧪 测试: 构建最终回复 Prompt")
    print("=" * 80 + "\n")
    
    from skill_runtime import SkillRuntime
    
    runtime = SkillRuntime(skill_dirs=["./skills"], verbose=True)
    
    # 模拟执行历史（包含成功和失败）
    execution_history = [
        {
            'iteration': 1,
            'ai_response': '第一次尝试使用错误的参数',
            'tool_calls': [],
            'results': ['失败的结果']
        },
        {
            'iteration': 2,
            'ai_response': '第二次尝试使用正确的参数',
            'tool_calls': [],
            'results': ['成功的结果']
        }
    ]
    
    # 构建最终 prompt
    final_prompt = runtime._build_final_prompt(
        "生成一个测试pdf",
        execution_history
    )
    
    print("生成的最终 Prompt:")
    print("-" * 80)
    print(final_prompt)
    print("-" * 80)
    print()
    
    # 验证
    checks = [
        ("原始请求", "生成一个测试pdf" in final_prompt),
        ("完整历史", "第 1 次尝试" in final_prompt and "第 2 次尝试" in final_prompt),
        ("要求部分", "【要求】" in final_prompt),
        ("成功提示", "基于以上成功的执行结果" in final_prompt),
    ]
    
    print("验证结果:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        all_passed = all_passed and passed
    
    print()
    if all_passed:
        print("✅ 所有检查通过！最终 Prompt 构建正确。")
    else:
        print("❌ 部分检查失败。")
    
    return all_passed


def demonstrate_iterative_workflow():
    """演示多次迭代工作流程"""
    print("\n" + "=" * 80)
    print("🎬 演示: 多次工具调用迭代流程")
    print("=" * 80 + "\n")
    
    print("场景: 用户要求'生成一个测试PDF，内容为测试文本'")
    print()
    
    print("【第 1 次迭代】")
    print("  1. AI 首次调用，生成工具调用:")
    print("     ```json")
    print("     {")
    print("       \"tool_call\": {")
    print("         \"skill_name\": \"pdf-generator\",")
    print("         \"script\": \"generate_pdf.py\",")
    print("         \"args\": \"content='测试文本'\"")
    print("       }")
    print("     }")
    print("     ```")
    print()
    print("  2. 执行工具调用:")
    print("     $ python generate_pdf.py content='测试文本'")
    print("     ❌ 失败: 缺少必需参数 --input-type 和 --output")
    print()
    print("  3. 将执行结果记录到 execution_history")
    print()
    
    print("【第 2 次迭代】")
    print("  4. 构建迭代 Prompt，包含:")
    print("     - 原始请求")
    print("     - 第 1 次迭代的 AI 响应")
    print("     - 第 1 次迭代的执行结果（失败）")
    print("     - 重要提示：请分析原因并修正参数")
    print()
    print("  5. 再次调用 AI，传入迭代 Prompt")
    print("     AI 看到之前的失败，分析原因:")
    print("     - 问题: 缺少 --input-type 和 --output 参数")
    print("     - 解决: 添加正确的参数")
    print()
    print("  6. AI 返回修正后的工具调用:")
    print("     ```json")
    print("     {")
    print("       \"tool_call\": {")
    print("         \"skill_name\": \"pdf-generator\",")
    print("         \"script\": \"generate_pdf.py\",")
    print("         \"args\": \"--input-type text --input '测试文本' --output test.pdf\"")
    print("       }")
    print("     }")
    print("     ```")
    print()
    print("  7. 执行修正后的工具调用:")
    print("     $ python generate_pdf.py --input-type text --input '测试文本' --output test.pdf")
    print("     ✅ 成功: 生成了 test.pdf 文件")
    print()
    print("  8. 检测到所有工具调用成功，进入最终回复阶段")
    print()
    
    print("【最终回复】")
    print("  9. 构建最终 Prompt，包含完整的执行历史")
    print("  10. 调用 AI 生成最终回复:")
    print("      '我已经成功生成了 PDF 文件 test.pdf，内容为\"测试文本\"。'")
    print("      '文件保存在当前目录下。'")
    print()
    
    print("=" * 80)
    print("💡 关键点:")
    print("  1. 系统支持多次迭代（默认最多 3 次）")
    print("  2. 每次迭代都会将之前的执行结果反馈给 AI")
    print("  3. AI 可以根据失败信息修正参数或改变策略")
    print("  4. 当所有工具调用成功或达到最大迭代次数时，生成最终回复")
    print("=" * 80)


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 SKILL 多次工具调用迭代功能测试")
    print("=" * 80 + "\n")
    
    try:
        result1 = test_build_iterative_prompt()
        result2 = test_build_final_prompt()
        demonstrate_iterative_workflow()
        
        print("\n" + "=" * 80)
        if result1 and result2:
            print("✅ 所有测试通过！")
        else:
            print("⚠️  部分测试未通过，请检查实现")
        print("=" * 80)
        
        print("\n💡 提示: 要测试实际的多次迭代功能，请运行:")
        print("   python skill_runtime.py -v")
        print("   然后输入: 生成一个测试pdf 创建一个文本 '测试文本'")
        print("\n预期行为:")
        print("  1. 第 1 次调用失败（参数不正确）")
        print("  2. 系统自动进行第 2 次迭代")
        print("  3. AI 修正参数后再次调用")
        print("  4. 第 2 次调用成功")
        print("  5. 生成最终回复")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
