#!/usr/bin/env python3
"""
skill_runtime.py - SKILL 运行时主程序

功能：
- 加载和管理多个 SKILL
- 通过渐进式暴露机制为 AI 提供技能
- 处理用户查询并智能调用 SKILL
- 支持交互式对话和命令行模式
"""

import sys
from pathlib import Path
from typing import List, Optional


from skill_manager import SkillManager
from ai_integration import AIIntegration
from tool_executor import ToolExecutor
from task_planner import TaskPlanner


class SkillRuntime:
    """SKILL 运行时环境"""
    
    def __init__(self, skill_dirs: List[str] = None,
                 api_url: str = "http://localhost:8080",
                 api_key: str = "test",
                 model: str = "gpt-4",
                 verbose: bool = False):
        """
        初始化运行时
        
        Args:
            skill_dirs: SKILL 目录列表
            api_url: API 地址
            api_key: API Key
            model: 模型名称
            verbose: 是否显示详细日志
        """
        if skill_dirs is None:
            skill_dirs = ["./skills"]
        
        self.skill_manager = SkillManager(skill_dirs, verbose=verbose)
        self.ai = AIIntegration(api_url, api_key, model=model, verbose=verbose)
        self.tool_executor = ToolExecutor("./skills", verbose=verbose)
        self.task_planner = TaskPlanner(verbose=verbose, ai_integration=self.ai)  # 传入 AI 实例
        self.conversation_history = []
        self.verbose = verbose
        self.skill_nesting_depth = 0  # 嵌套调用深度（最多 3 层）
        self.MAX_NESTING_DEPTH = 3
        self.subtask_depth = 0  # 子任务递归深度
        self.MAX_SUBTASK_DEPTH = 3  # 子任务最大递归深度
        
    def start(self):
        """启动运行时"""
        print("─" * 50)
        print("🚀 SKILL Runtime System")
        print("─" * 50)
        
        # 初始化 SKILL（只解析 frontmatter 元数据）
        count = self.skill_manager.initialize()
        
        if count == 0:
            print("\n⚠️  未找到任何 SKILL")
            print("请将 SKILL 放在 ./skills 目录或使用 --dirs 指定路径")
            return
        
        # 渐进式调用：阶段 2 - 将 Skill 注册表摘要注入系统提示词
        registry_summary = self.skill_manager.get_skill_registry_summary()
        self.ai.set_skill_registry(registry_summary)
        
        # 测试 API 连接
        print("\n🔌 测试 API 连接...")
        if not self.ai.test_connection():
            print("⚠️  API 连接失败，将使用离线模式")
        
        # 进入交互模式
        self.interactive_mode()
    
    def interactive_mode(self):
        """交互式对话模式"""
        print("\n" + "─" * 50)
        print("💬 交互模式已启动")
        print("─" * 50)
        print("\n可用命令:")
        print("  /list     - 列出所有 SKILL")
        print("  /search Q - 搜索 SKILL")
        print("  /reload   - 重新加载 SKILL")
        print("  /quit     - 退出\n")
        
        while True:
            try:
                user_input = input("👤 你: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    if not self._handle_command(user_input):
                        break
                    continue
                
                # 正常对话
                self._handle_message(user_input)
            
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except EOFError:
                break
    
    def _handle_command(self, command: str) -> bool:
        """
        处理命令
        
        Returns:
            是否继续
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        
        if cmd == "/list":
            skills = self.skill_manager.list_active_skills()
            print(f"\n已加载 {len(skills)} 个 SKILL:\n")
            for i, skill in enumerate(skills, 1):
                print(f"{i}. **{skill['name']}**")
                print(f"   {skill['description'][:100]}...\n")
        
        elif cmd == "/search":
            if len(parts) < 2:
                print("用法: /search <关键词>")
            else:
                query = parts[1]
                matches = self.skill_manager.match_skills(query)
                print(f"\n搜索结果: '{query}'\n")
                if matches:
                    for info in matches:
                        print(f"• {info.name}")
                        print(f"  {info.description[:150]}\n")
                else:
                    print("未找到匹配的 SKILL\n")
        
        elif cmd == "/reload":
            print("\n重新加载 SKILL...")
            self.skill_manager.reload_all()
        
        elif cmd == "/quit" or cmd == "/exit":
            print("\n再见！")
            return False
        
        else:
            print(f"未知命令: {cmd}")
            print("可用命令: /list, /search, /reload, /quit\n")
        
        return True
    
    def _handle_message(self, user_message: str, max_tool_iterations: int = 5):
        """
        处理用户消息，支持多次工具调用迭代。
        
        渐进式披露机制（参考 Kimi Code CLI）：
        - 启动时：只注入 Skill 注册表摘要（L1 元数据）到系统提示词
        - 命中时：才加载 SKILL.md 正文到系统提示词
        - 用完后：立即清除正文缓存，不持久化到对话历史，节省 token
        
        Args:
            user_message: 用户消息
            max_tool_iterations: 最大工具调用迭代次数（默认 5 次）
        """
        if self.verbose:
            print(f"\n{'─'*50}")
            print(f"📋 请求: {user_message}")
            print(f"{'─'*50}")
        
        # 初始化对话变量
        current_response = ""
        iteration = 0
        execution_history = []  # 记录所有执行历史
        pending_skill_body = ""  # 待注入的 Skill 正文（用于下一次 AI 调用）
        
        # 多次迭代执行工具调用
        while iteration < max_tool_iterations:
            iteration += 1
            
            # 第 1 次迭代：直接调用 AI
            # 后续迭代：使用增强后的 prompt（包含之前的执行结果）
            if iteration == 1:
                ai_input = user_message
            else:
                ai_input = self._build_iterative_prompt(user_message, execution_history)
                if self.verbose:
                    print(f"\n🔄 迭代 {iteration}/{max_tool_iterations}")
            
            # 调用 AI（如果有上一轮加载的 Skill 正文，注入本次调用）
            if self.verbose:
                print(f"🌐 调用 AI (history: {len(self.conversation_history)} 条)")
            
            current_response = self.ai.chat_with_skills(
                ai_input,
                "",  # 已废弃，Skill 摘要已在系统提示词中
                self.conversation_history,
                skill_body=pending_skill_body  # 注入上一轮加载的 Skill 正文
            )
            # 用完即清：pending_skill_body 已注入本次调用，清空
            pending_skill_body = ""
            
            if self.verbose:
                print(f"📥 AI 响应 ({len(current_response)} 字符)")
            
            # 先尝试解析为任务计划
            plan = self.task_planner.parse_task_plan(current_response)
            
            if plan:
                # 检查嵌套深度
                if self.skill_nesting_depth >= self.MAX_NESTING_DEPTH:
                    print(f"⚠️  已达到最大嵌套深度 ({self.MAX_NESTING_DEPTH})，终止")
                    break
                
                # 显示任务计划
                print(f"\n📋 任务: {plan.task_description} ({len(plan.steps)} 步)")
                for s in plan.steps:
                    print(f"  {s.step_id}. {s.description} → {s.skill_name}/{s.script}")
                
                # 命中后加载 Skill 正文（仅在最终回复时注入）
                combined_plan_skill_body = self._load_skill_bodies_for_plan(plan)
                
                self.skill_nesting_depth += 1
                self._execute_task_plan(plan, max_retries=getattr(self, 'max_retries', 3), original_user_query=user_message, skill_body=combined_plan_skill_body)
                self.skill_nesting_depth -= 1
                break
            else:
                # 检测单个工具调用
                tool_calls = self.tool_executor.detect_tool_calls(current_response)
                
                if tool_calls:
                    # 执行所有工具调用
                    execution_results = []
                    raw_results = []
                    for i, tc in enumerate(tool_calls, 1):
                        # 显示工具调用
                        print(f"\n🔧 调用 {tc['skill_name']}/{tc['script']}")
                        print(f"  参数: {tc['args']}")
                        
                        result = self.tool_executor.execute_tool_call(tc)
                        raw_results.append(result)
                        formatted_result = self.tool_executor.format_execution_result(tc, result)
                        execution_results.append(formatted_result)
                        
                        # 显示执行结果
                        if result['success']:
                            output = result.get('output', '').strip()
                            print(f"  ✅ 成功 (exit_code={result.get('exit_code', 0)})")
                            if output:
                                print(f"  输出: {output[:2000]}{'...' if len(output) > 2000 else ''}")
                        else:
                            error = result.get('error', 'Unknown error')
                            print(f"  ❌ 失败: {error[:2000]}")
                    
                    # 记录执行历史
                    execution_history.append({
                        'iteration': iteration,
                        'ai_response': current_response,
                        'tool_calls': tool_calls,
                        'results': execution_results,
                        'raw_results': raw_results
                    })
                    
                    # 检查是否所有工具调用都成功
                    all_success = all(
                        raw_result.get('success', False)
                        for history in execution_history
                        for raw_result in history.get('raw_results', [])
                    )
                    
                    if all_success and iteration > 1:
                        # 所有工具成功，加载 Skill 正文生成最终回复
                        final_prompt = self._build_final_prompt(user_message, execution_history)
                        combined_skill_body = self._load_skill_bodies_for_tool_calls(
                            [tc for h in execution_history for tc in h.get('tool_calls', [])]
                        )
                        final_response = self.ai.chat_with_skills(
                            final_prompt, "", [],
                            skill_body=combined_skill_body
                        )
                        print(f"\n🤖 回复:\n{final_response}")
                        current_response = final_response
                        break
                    elif iteration >= max_tool_iterations:
                        # 达到最大迭代，加载 Skill 正文生成最终回复
                        final_prompt = self._build_final_prompt(user_message, execution_history)
                        combined_skill_body = self._load_skill_bodies_for_tool_calls(
                            [tc for h in execution_history for tc in h.get('tool_calls', [])]
                        )
                        final_response = self.ai.chat_with_skills(
                            final_prompt, "", [],
                            skill_body=combined_skill_body
                        )
                        print(f"\n⚠️  达到最大迭代 ({max_tool_iterations})")
                        print(f"\n🤖 回复:\n{final_response}")
                        current_response = final_response
                        break
                    else:
                        # 还有迭代机会：立即加载 SKILL 正文，注入下一次 AI 调用
                        # 这样 AI 能看到正确的参数格式，避免盲猜
                        pending_skill_body = self._load_skill_bodies_for_tool_calls(tool_calls)
                        continue
                else:
                    # 没有工具调用，直接返回 AI 回复
                    print(f"\n🤖 回复:\n{current_response}")
                    break
        
        # 用完即弃：清除本次消息处理中加载的所有 Skill 正文缓存
        self.skill_manager.clear_skill_body()
        
        # 保存对话历史（不包含 Skill 正文，只有用户消息和 AI 回复）
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": current_response})
        
        # 限制历史记录长度
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def _execute_task_plan(self, plan, max_retries: int = 3, original_user_query: str = "", skill_body: str = ""):
        """
        执行多步骤任务计划，支持：
        1. 子任务拆分：每个步骤可由 AI 分析后拆分为子任务
        2. 失败后 AI 重新规划
        3. 完成后验证，不成功则继续创建任务直到成功
        
        Args:
            plan: ExecutionPlan 对象
            max_retries: 最大重试次数（默认 3 次）
            original_user_query: 原始用户查询，用于 AI 重新规划
            skill_body: 命中的 Skill 正文，用于注入最终回复（用完即弃）
        """
        if self.verbose:
            print(f"\n📋 开始执行任务计划 (重试: {max_retries})")
        
        # 首次执行所有步骤（含子任务拆分）
        self._execute_plan_steps(plan, max_retries)
        
        # 检查是否有失败的步骤需要 AI 重新规划
        retry_round = 1
        while plan.get_failed_steps() and retry_round <= max_retries:
            failed_steps = plan.get_failed_steps()
            if not failed_steps:
                break
            
            print(f"\n🔄 重新规划 {retry_round}/{max_retries}: {len(failed_steps)} 个步骤失败")
            
            # 构建失败上下文
            failure_context = self._build_failure_context(plan, original_user_query)
            
            if self.verbose:
                print(f"📊 [失败上下文摘要]")
                print(f"   已完成步骤: {sum(1 for s in plan.steps if s.status == 'success')}")
                print(f"   失败步骤: {len(failed_steps)}")
                print(f"   已保存的上下文数据: {list(plan.context.keys())}\n")
            
            # 调用 AI 重新规划
            new_plan = self._ask_ai_to_replan(failure_context, plan)
            
            if new_plan:
                if self.verbose:
                    print(f"  ✅ 重新规划成功 ({len(new_plan.steps)} 步)")
                
                # 继承已成功步骤的结果和上下文
                self._merge_successful_steps(plan, new_plan)
                plan = new_plan
            else:
                print(f"  ❌ 重新规划失败")
                break
            
            # 执行新计划的步骤
            self._execute_plan_steps(plan, max_retries)
            
            retry_round += 1
        
        # 完成后验证：检查任务是否真正完成
        verification_passed = self._verify_task_completion(plan, original_user_query)
        
        # 如果验证未通过，继续创建修复任务直到成功
        verify_round = 1
        max_verify_rounds = max_retries
        while not verification_passed and verify_round <= max_verify_rounds:
            print(f"\n🔍 验证未通过 ({verify_round}/{max_verify_rounds})，正在分析问题并创建修复任务...")
            
            # 让 AI 分析验证结果并创建修复计划
            fix_plan = self._create_fix_plan_from_verification(plan, original_user_query)
            
            if fix_plan:
                if self.verbose:
                    print(f"  ✅ 生成修复计划 ({len(fix_plan.steps)} 步)")
                
                # 继承已有上下文
                self._merge_successful_steps(plan, fix_plan)
                
                # 执行修复计划
                self._execute_plan_steps(fix_plan, max_retries)
                
                # 将修复步骤合并到主计划
                for step in fix_plan.steps:
                    if step.step_id not in [s.step_id for s in plan.steps]:
                        plan.add_step(step)
                
                # 重新验证
                verification_passed = self._verify_task_completion(plan, original_user_query)
            else:
                print(f"  ❌ 无法生成修复计划")
                break
            
            verify_round += 1
        
        # 最终状态
        is_complete = plan.validate_completion() and verification_passed
        success_count = sum(1 for s in plan.steps if s.status == 'success')
        fail_count = sum(1 for s in plan.steps if s.status == 'failed')
        
        # 显示执行摘要
        if is_complete:
            print(f"\n✅ 任务完成 ({success_count}/{len(plan.steps)} 步成功)")
        else:
            print(f"\n❌ 任务未完成 ({success_count}/{len(plan.steps)} 步成功, {fail_count} 步失败)")
            for step in plan.get_failed_steps():
                print(f"  ❌ 步骤{step.step_id}: {step.description}")
                if step.error_message:
                    print(f"    {step.error_message[:200]}")
        
        if self.verbose:
            print(f"  上下文: {plan.context}")
        
        # 让 AI 基于所有步骤的结果生成最终回复
        
        final_prompt = f"任务: {plan.task_description}\n\n执行结果:\n"
        for step in plan.steps:
            status_icon = "✅" if step.status == "success" else "❌"
            final_prompt += f"\n{status_icon} 步骤 {step.step_id}: {step.description}\n"
            if step.result:
                final_prompt += f"结果: {step.result}\n"
            if step.error_message:
                final_prompt += f"错误: {step.error_message}\n"
        
        if is_complete:
            final_prompt += "\n请基于以上执行结果给用户一个完整的回答。"
        else:
            final_prompt += "\n\n注意：部分步骤执行失败，请在回答中说明哪些步骤成功了，哪些失败了，以及可能的原因。"
        
        # 命中时注入 Skill 正文 + 子 Agent 隔离（用完即弃，不进入对话历史）
        final_response = self.ai.chat_with_skills(
            final_prompt,
            "",
            [],  # 子 Agent 隔离：任务计划执行过程不污染主对话历史
            skill_body=skill_body
        )
        
        # 用完即弃：清除本次任务计划加载的 Skill 正文缓存
        if skill_body:
            self.skill_manager.clear_skill_body()
        
        print(f"\n🤖 回复:\n{final_response}")
    
    def _load_skill_bodies_for_plan(self, plan) -> str:
        """
        命中时按需加载任务计划中所有涉及 Skill 的正文。
        返回合并后的正文，用于在最终回复时注入到 AI 系统提示词。
        注入完成后由调用方清除缓存（用完即弃）。
        
        Args:
            plan: ExecutionPlan 对象
            
        Returns:
            合并后的 Skill 正文字符串
        """
        loaded_skills = set()
        bodies = []
        for step in plan.steps:
            if step.skill_name not in loaded_skills:
                body = self.skill_manager.load_skill_body(step.skill_name)
                if body:
                    loaded_skills.add(step.skill_name)
                    bodies.append(body)
                    print(f"\n{'='*60}")
                    print(f"📖 [L2] 命中加载 Skill: {step.skill_name}")
                    print(f"{'='*60}")
                    print(body)
                    print(f"{'='*60}\n")
        return "\n\n".join(bodies)
    
    def _load_skill_bodies_for_tool_calls(self, tool_calls: list) -> str:
        """
        命中时按需加载工具调用中涉及 Skill 的正文。
        返回合并后的正文，用于在最终回复时注入到 AI 系统提示词。
        注入完成后由调用方清除缓存（用完即弃）。
        
        Args:
            tool_calls: 工具调用列表，每项包含 skill_name 字段
            
        Returns:
            合并后的 Skill 正文字符串
        """
        loaded_skills = set()
        bodies = []
        for tc in tool_calls:
            skill_name = tc.get('skill_name', '')
            if skill_name and skill_name not in loaded_skills:
                body = self.skill_manager.load_skill_body(skill_name)
                if body:
                    loaded_skills.add(skill_name)
                    bodies.append(body)
                    print(f"\n{'='*60}")
                    print(f"📖 [L2] 命中加载 Skill: {skill_name}")
                    print(f"{'='*60}")
                    print(body)
                    print(f"{'='*60}\n")
        return "\n\n".join(bodies)
    
    def _execute_plan_steps(self, plan, max_retries: int = 3, only_failed: bool = False):
        """
        执行任务计划中的步骤，支持子任务拆分
        
        Args:
            plan: ExecutionPlan 对象
            max_retries: 最大重试次数
            only_failed: 是否只执行失败的步骤
        """
        step_count = len(plan.steps)
        
        for i, step in enumerate(plan.steps, 1):
            # 如果只执行失败步骤，跳过已成功的步骤
            if only_failed and step.status == 'success':
                continue
            
            # 跳过已达到最大重试次数的失败步骤
            if step.status == 'failed' and step.retry_count >= max_retries:
                if self.verbose:
                    print(f"⚠️  [步骤 {step.step_id}] 已达到最大重试次数，跳过\n")
                continue
            
            # 更新步骤状态
            step.status = 'running'
            step.retry_count += 1
            
            # 填充参数模板
            filled_args = self.task_planner.fill_args_template(step.args_template, plan.context)
            
            # 始终显示步骤执行信息
            print(f"\n  [{i}/{step_count}] {step.description}")
            print(f"  {step.skill_name}/{step.script} | 参数: {filled_args}")
            
            if self.verbose:
                print(f"  Args Template: {step.args_template}")
                print(f"  Retry: {step.retry_count}/{max_retries}")
                if step.depends_on:
                    print(f"  Depends on: {step.depends_on}")
                if plan.context:
                    print(f"  Context: {plan.context}")
            
            # 检查是否需要 AI 分析拆分为子任务
            if step.needs_decompose and not step.has_subtasks:
                sub_plan = self._analyze_step_for_subtasks(step, plan)
                if sub_plan:
                    step.has_subtasks = True
                    step.sub_task_plan = sub_plan
                    print(f"  🧩 已拆分为 {len(sub_plan.steps)} 个子任务")
            
            # 如果步骤已拆分为子任务，执行子任务
            if step.has_subtasks and step.sub_task_plan:
                self._execute_sub_task_plan(step, plan, max_retries)
                continue
            
            # 构建工具调用
            tool_call = {
                'skill_name': step.skill_name,
                'script': f"skills/{step.skill_name}/scripts/{step.script}",
                'args': filled_args,
                'type': 'task_plan_step'
            }
            
            # 执行工具调用
            result = self.tool_executor.execute_tool_call(tool_call)
            
            # 识别错误类型
            error_type = self.tool_executor.identify_error_type(result)
            
            # 始终显示执行结果
            if result['success']:
                output = result.get('output', '').strip()
                print(f"  ✅ 成功 (exit_code={result.get('exit_code', 0)})")
                if output:
                    print(f"  输出: {output[:2000]}{'...' if len(output) > 2000 else ''}")
                
                # 保存执行结果
                step.result = output
                step.status = 'success'
                step.error_message = None
                step.last_error_type = None
                
                # 提取数据并保存到上下文
                if step.save_to_context:
                    if step.context_prompt and self.ai:
                        extraction_prompt = (
                            f"请根据以下说明，从执行结果中提取关键信息：\n\n"
                            f"【说明】\n{step.context_prompt}\n\n"
                            f"【执行结果】\n{output}\n\n"
                            f"请直接返回提取出的核心内容，不要加任何解释或标记。"
                        )
                        extracted_value = self.ai.chat_with_skills(
                            extraction_prompt, "", []
                        ).strip()
                        plan.update_context(step.save_to_context, extracted_value)
                        step.extracted_data = {'value': extracted_value, 'method': 'context_prompt'}
                        if self.verbose:
                            print(f"  💾 {step.save_to_context} = {extracted_value[:200]}")
                    elif step.extraction:
                        extracted = self.task_planner.extract_data_from_result(output, step.extraction)
                        step.extracted_data = extracted
                        if 'value' in extracted:
                            plan.update_context(step.save_to_context, extracted['value'])
                            if self.verbose:
                                print(f"  💾 {step.save_to_context} = {extracted['value']}")
                    else:
                        clean_output = self.task_planner._extract_stdout_from_formatted(output)
                        plan.update_context(step.save_to_context, clean_output.strip())
                        step.extracted_data = {'value': clean_output.strip(), 'method': 'auto_clean'}
                        if self.verbose:
                            print(f"  💾 {step.save_to_context} = {clean_output.strip()[:200]}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"  ❌ 失败: {error[:2000]}")
                
                # 记录错误信息
                step.status = 'failed'
                step.error_message = error
                step.last_error_type = error_type
    
    def _attempt_auto_fix(self, step, error_analysis: dict) -> bool:
        """
        尝试自动修复错误
        
        Args:
            step: 失败的步骤
            error_analysis: 错误分析结果
            
        Returns:
            True 如果修复成功，否则 False
        """
        action = error_analysis.get('suggested_action', '')
        
        if not action:
            return False
        
        # 处理缺少模块的情况
        if action.startswith('pip install '):
            package_name = action.replace('pip install ', '')
            if self.verbose:
                print(f"\n🔧 [自动修复] 正在安装 Python 包: {package_name}")
            
            try:
                import subprocess
                result = subprocess.run(
                    ['pip', 'install', package_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    if self.verbose:
                        print(f"✅ [自动修复] 成功安装 {package_name}")
                    return True
                else:
                    if self.verbose:
                        print(f"❌ [自动修复] 安装失败: {result.stderr[:200]}")
                    return False
            except Exception as e:
                if self.verbose:
                    print(f"❌ [自动修复] 安装异常: {str(e)}")
                return False
        
        # 其他类型的修复暂不支持
        return False
    
    def _analyze_step_for_subtasks(self, step, plan) -> Optional['ExecutionPlan']:
        """
        调用 AI 分析某个步骤是否需要拆分为子任务
        
        Args:
            step: 需要分析的步骤
            plan: 当前执行计划
            
        Returns:
            子任务 ExecutionPlan 或 None（不需要拆分）
        """
        # 检查递归深度
        if self.subtask_depth >= self.MAX_SUBTASK_DEPTH:
            if self.verbose:
                print(f"⚠️  子任务递归深度已达上限 ({self.MAX_SUBTASK_DEPTH})，不再拆分")
            return None
        
        self.subtask_depth += 1
        
        if self.verbose:
            print(f"\n🧩 [子任务分析] 步骤 {step.step_id}: {step.description}")
            print(f"   当前子任务深度: {self.subtask_depth}/{self.MAX_SUBTASK_DEPTH}")
        
        # 构建已完成步骤的结果摘要
        completed_results = []
        for s in plan.steps:
            if s.status == 'success' and s.result:
                completed_results.append(f"步骤 {s.step_id} ({s.description}): {s.result[:500]}")
        completed_results_text = "\n".join(completed_results) if completed_results else "无已完成步骤"
        
        # 构建父上下文
        parent_context = ""
        if plan.context:
            ctx_lines = [f"  {k} = {str(v)[:200]}" for k, v in plan.context.items()]
            parent_context = "已保存的上下文变量:\n" + "\n".join(ctx_lines)
        
        # 从文件加载 subtask 提示词模板
        subtask_prompt_path = Path(__file__).parent / "prompts" / "subtask_prompt.txt"
        if subtask_prompt_path.exists():
            subtask_prompt_template = subtask_prompt_path.read_text(encoding='utf-8')
            subtask_prompt = subtask_prompt_template.format(
                step_id=step.step_id,
                step_description=step.description,
                skill_name=step.skill_name,
                script=step.script,
                args=step.args_template,
                parent_task_description=plan.task_description,
                parent_context=parent_context,
                completed_results=completed_results_text
            )
        else:
            # 回退：内联构建
            subtask_prompt = f"""请分析以下步骤是否需要拆分为多个子步骤：
步骤 {step.step_id}: {step.description}
技能: {step.skill_name}/{step.script}
参数: {step.args_template}

如果需要拆分，请以 JSON 格式返回 sub_task_plan。
如果不需要拆分，返回单步骤计划。"""
        
        try:
            # 调用 AI 分析（子 Agent 隔离）
            response = self.ai.chat_with_skills(
                subtask_prompt,
                "",
                []  # 子 Agent 隔离
            )
            
            if self.verbose:
                print(f"📥 [子任务分析] AI 响应长度: {len(response)} 字符")
            
            # 解析子任务计划
            sub_plan = self.task_planner.parse_sub_task_plan(response)
            
            if sub_plan:
                print(f"  ✅ 拆分为 {len(sub_plan.steps)} 个子任务:")
                for s in sub_plan.steps:
                    print(f"     {s.step_id}. {s.description} → {s.skill_name}/{s.script}")
                return sub_plan
            else:
                if self.verbose:
                    print(f"  ℹ️  AI 判断不需要拆分子任务")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️  [子任务分析] 失败: {e}")
            return None
        finally:
            self.subtask_depth -= 1
    
    def _execute_sub_task_plan(self, parent_step, parent_plan, max_retries: int = 3):
        """
        执行某个步骤的子任务计划
        
        Args:
            parent_step: 父步骤（已拆分为子任务）
            parent_plan: 父执行计划
            max_retries: 最大重试次数
        """
        sub_plan = parent_step.sub_task_plan
        if not sub_plan:
            return
        
        print(f"\n  🧩 执行子任务: {sub_plan.task_description}")
        
        # 继承父计划的上下文到子计划
        for key, value in parent_plan.context.items():
            if key not in sub_plan.context:
                sub_plan.context[key] = value
        
        # 执行子任务步骤
        self._execute_plan_steps(sub_plan, max_retries)
        
        # 检查子任务是否有失败
        sub_retry_round = 1
        while sub_plan.get_failed_steps() and sub_retry_round <= max_retries:
            failed_steps = sub_plan.get_failed_steps()
            print(f"\n  🔄 子任务重新规划 {sub_retry_round}/{max_retries}: {len(failed_steps)} 个步骤失败")
            
            # 构建失败上下文
            failure_context = self._build_failure_context(sub_plan, 
                f"父步骤 {parent_step.step_id}: {parent_step.description}")
            
            # 调用 AI 重新规划
            new_sub_plan = self._ask_ai_to_replan(failure_context, sub_plan)
            
            if new_sub_plan:
                self._merge_successful_steps(sub_plan, new_sub_plan)
                sub_plan = new_sub_plan
                parent_step.sub_task_plan = sub_plan
                self._execute_plan_steps(sub_plan, max_retries)
            else:
                print(f"  ❌ 子任务重新规划失败")
                break
            
            sub_retry_round += 1
        
        # 根据子任务结果更新父步骤状态
        sub_success = all(s.status == 'success' for s in sub_plan.steps)
        
        if sub_success:
            parent_step.status = 'success'
            # 收集子任务的输出作为父步骤的结果
            sub_outputs = []
            for s in sub_plan.steps:
                if s.result:
                    sub_outputs.append(f"[子步骤{s.step_id}] {s.result}")
            parent_step.result = "\n".join(sub_outputs)
            parent_step.error_message = None
            
            # 继承子任务的上下文到父计划
            for key, value in sub_plan.context.items():
                if key not in parent_plan.context:
                    parent_plan.context[key] = value
            
            # 处理父步骤的 save_to_context
            if parent_step.save_to_context and parent_step.result:
                parent_plan.update_context(parent_step.save_to_context, parent_step.result)
            
            print(f"  ✅ 子任务全部完成，父步骤 {parent_step.step_id} 标记为成功")
        else:
            parent_step.status = 'failed'
            failed_sub = [s for s in sub_plan.steps if s.status == 'failed']
            error_msgs = [f"子步骤{s.step_id}: {s.error_message or '未知错误'}" for s in failed_sub]
            parent_step.error_message = "子任务失败: " + "; ".join(error_msgs)
            print(f"  ❌ 子任务部分失败，父步骤 {parent_step.step_id} 标记为失败")
    
    def _verify_task_completion(self, plan, original_query: str) -> bool:
        """
        验证任务是否真正完成（通过 AI 分析执行结果）
        
        Args:
            plan: 执行计划
            original_query: 原始用户查询
            
        Returns:
            True 如果验证通过（任务已完成），False 如果验证未通过
        """
        # 如果有失败的步骤，直接返回 False
        if plan.get_failed_steps():
            if self.verbose:
                print(f"🔍 [验证] 存在 {len(plan.get_failed_steps())} 个失败步骤，验证不通过")
            return False
        
        # 构建执行结果摘要
        result_summary = []
        for step in plan.steps:
            status_icon = "✅" if step.status == "success" else "❌"
            result_summary.append(f"{status_icon} 步骤 {step.step_id}: {step.description}")
            if step.result:
                result_summary.append(f"   结果: {step.result[:500]}")
            if step.has_subtasks and step.sub_task_plan:
                for sub_s in step.sub_task_plan.steps:
                    sub_icon = "✅" if sub_s.status == "success" else "❌"
                    result_summary.append(f"   {sub_icon} 子步骤 {sub_s.step_id}: {sub_s.description}")
                    if sub_s.result:
                        result_summary.append(f"      结果: {sub_s.result[:300]}")
        
        result_text = "\n".join(result_summary)
        
        if self.verbose:
            print(f"\n🔍 [验证] 正在验证任务完成情况...")
        
        # 调用 AI 验证
        verify_prompt = f"""请根据以下信息判断任务是否已成功完成。

【原始需求】
{original_query}

【执行结果】
{result_text}

请分析：
1. 原始需求是否已经被完全满足？
2. 执行结果是否表明所有操作都成功完成？
3. 是否有遗漏或未完成的部分？

请以 JSON 格式返回验证结果：
```json
{{
  "verification": {{
    "passed": true或false,
    "confidence": 0.0到1.0的置信度,
    "reason": "判断理由",
    "issues": ["发现的问题列表，如果没有则为空数组"]
  }}
}}
```"""
        
        try:
            response = self.ai.chat_with_skills(
                verify_prompt,
                "",
                []  # 子 Agent 隔离
            )
            
            # 解析验证结果
            import json
            import re
            
            json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            verification = data.get('verification', {})
            passed = verification.get('passed', False)
            confidence = verification.get('confidence', 0)
            reason = verification.get('reason', '')
            issues = verification.get('issues', [])
            
            if passed:
                print(f"  ✅ 验证通过 (置信度: {confidence})")
                if self.verbose:
                    print(f"     理由: {reason}")
            else:
                print(f"  ❌ 验证未通过 (置信度: {confidence})")
                print(f"     理由: {reason}")
                if issues:
                    for issue in issues:
                        print(f"     - {issue}")
            
            # 保存验证结果到计划
            plan.verification_result = verification
            
            return passed
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  [验证] AI 验证失败: {e}，默认通过")
            # 验证失败时默认通过，避免无限循环
            return True
    
    def _create_fix_plan_from_verification(self, plan, original_query: str) -> Optional['ExecutionPlan']:
        """
        根据验证结果创建修复计划
        
        Args:
            plan: 当前执行计划
            original_query: 原始用户查询
            
        Returns:
            修复用的 ExecutionPlan 或 None
        """
        # 构建验证失败上下文
        verify_result = getattr(plan, 'verification_result', {})
        issues = verify_result.get('issues', []) if verify_result else []
        reason = verify_result.get('reason', '未知原因') if verify_result else '未知原因'
        
        # 构建执行结果摘要
        result_summary = []
        for step in plan.steps:
            status_icon = "✅" if step.status == "success" else "❌"
            result_summary.append(f"{status_icon} 步骤 {step.step_id}: {step.description}")
            if step.result:
                result_summary.append(f"   结果: {step.result[:500]}")
        
        fix_prompt = f"""任务执行后验证未通过，请分析问题并创建修复计划。

【原始需求】
{original_query}

【已执行的步骤和结果】
{chr(10).join(result_summary)}

【验证结果】
状态: 未通过
原因: {reason}
发现的问题:
{chr(10).join(f"- {issue}" for issue in issues)}

【已保存的上下文数据】
{chr(10).join(f"  {k} = {str(v)[:200]}" for k, v in plan.context.items()) if plan.context else "无"}

请创建修复计划来解决以上问题，确保任务最终完成。

请以 JSON 格式返回任务计划：
```json
{{
  "task_plan": {{
    "description": "修复计划描述",
    "steps": [
      {{
        "step_id": 1,
        "description": "步骤描述",
        "skill_name": "技能名称",
        "script": "脚本文件",
        "args": "参数",
        "depends_on": [],
        "extraction": "smart",
        "save_to_context": "variable_name",
        "context_prompt": "描述本步骤产出什么内容"
      }}
    ]
  }}
}}
```"""
        
        try:
            response = self.ai.chat_with_skills(
                fix_prompt,
                "",
                []  # 子 Agent 隔离
            )
            
            if self.verbose:
                print(f"📥 [修复计划] AI 响应长度: {len(response)} 字符")
            
            # 解析修复计划
            fix_plan = self.task_planner.parse_task_plan(response)
            
            if fix_plan:
                # 重新编号步骤，避免与已有步骤冲突
                max_step_id = max((s.step_id for s in plan.steps), default=0)
                for step in fix_plan.steps:
                    step.step_id = max_step_id + step.step_id
                
                return fix_plan
            else:
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️  [修复计划] 生成失败: {e}")
            return None
    
    def _build_failure_context(self, plan, original_query: str) -> str:
        """
        构建失败上下文，包含所有执行结果和错误信息
        
        Args:
            plan: 当前执行计划
            original_query: 原始用户查询
            
        Returns:
            格式化的失败上下文字符串
        """
        context_lines = []
        context_lines.append(f"# 原始任务")
        context_lines.append(f"用户请求: {original_query}")
        context_lines.append(f"任务描述: {plan.task_description}\n")
        
        context_lines.append(f"# 执行状态\n")
        
        for step in plan.steps:
            status_icon = "✅" if step.status == "success" else "❌"
            context_lines.append(f"{status_icon} 步骤 {step.step_id}: {step.description}")
            context_lines.append(f"   Skill: {step.skill_name}")
            context_lines.append(f"   Script: {step.script}")
            context_lines.append(f"   Args: {step.args_template}")
            
            if step.status == "success":
                context_lines.append(f"   结果: {step.result[:2000] if step.result else 'N/A'}")
            elif step.status == "failed":
                context_lines.append(f"   错误类型: {step.last_error_type}")
                context_lines.append(f"   错误信息: {step.error_message[:2000] if step.error_message else 'N/A'}")
                context_lines.append(f"   重试次数: {step.retry_count}")
            
            context_lines.append("")
        
        # 添加已保存的上下文数据
        if plan.context:
            context_lines.append(f"# 已保存的上下文数据\n")
            for key, value in plan.context.items():
                context_lines.append(f"   {key}: {value}")
            context_lines.append("")
        
        # 总结失败情况
        failed_steps = plan.get_failed_steps()
        context_lines.append(f"# 失败总结\n")
        context_lines.append(f"总步骤数: {len(plan.steps)}")
        context_lines.append(f"成功步骤: {sum(1 for s in plan.steps if s.status == 'success')}")
        context_lines.append(f"失败步骤: {len(failed_steps)}\n")
        
        if failed_steps:
            context_lines.append("请分析以上失败原因，并制定新的任务计划。可以考虑：")
            context_lines.append("1. 使用不同的技能或脚本")
            context_lines.append("2. 调整命令参数")
            context_lines.append("3. 改变执行顺序")
            context_lines.append("4. 采用替代方案")
            context_lines.append("5. 如果某些步骤无法完成，可以跳过或简化\n")
        
        return "\n".join(context_lines)
    
    def _ask_ai_to_replan(self, failure_context: str, old_plan) -> Optional:
        """
        调用 AI 重新制定任务计划
        
        Args:
            failure_context: 失败上下文信息
            old_plan: 旧的执行计划
            
        Returns:
            新的 ExecutionPlan 或 None
        """
        if self.verbose:
            print("🤖 [AI] 正在重新制定任务计划...")
            print(f"   失败上下文长度: {len(failure_context)} 字符\n")
        
        # 从文件加载 replan 提示词模板
        replan_prompt_path = Path(__file__).parent / "prompts" / "replan_prompt.txt"
        if replan_prompt_path.exists():
            replan_prompt_template = replan_prompt_path.read_text(encoding='utf-8')
            replan_prompt = replan_prompt_template.format(failure_context=failure_context)
        else:
            # 回退：文件不存在时内联构建
            replan_prompt = f"""你是一个智能任务规划助手。之前的任务执行失败了，请根据以下信息重新制定任务计划。

{failure_context}

请以 JSON 格式返回新的任务计划。"""
        
        try:
            # 调用 AI 重新规划（子 Agent 隔离：使用独立对话历史）
            response = self.ai.chat_with_skills(
                replan_prompt,
                "",  # 不注入 SKILL 上下文，因为已经在 failure_context 中包含了
                []  # 子 Agent 隔离：replan 使用独立对话历史
            )
            
            if self.verbose:
                print(f"📥 [AI 响应] 长度: {len(response)} 字符")
                print(f"   前 200 字符: {response[:200]}...\n")
            
            # 解析新的任务计划
            new_plan = self.task_planner.parse_task_plan(response)
            
            if new_plan:
                if self.verbose:
                    print(f"✅ [AI] 成功解析新的任务计划")
                    print(f"   步骤数: {len(new_plan.steps)}\n")
                return new_plan
            else:
                if self.verbose:
                    print(f"❌ [AI] 无法解析新的任务计划\n")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"❌ [AI] 重新规划失败: {str(e)}\n")
            return None
    
    def _merge_successful_steps(self, old_plan, new_plan):
        """
        将旧计划中已成功步骤的结果合并到新计划中
        
        Args:
            old_plan: 旧的执行计划（包含已成功的步骤）
            new_plan: 新的执行计划
        """
        if self.verbose:
            print(f"🔄 [合并] 继承已成功步骤的结果...")
        
        # 创建旧步骤的映射
        old_steps_map = {step.step_id: step for step in old_plan.steps if step.status == 'success'}
        
        # 检查新计划中是否有相同 ID 的步骤
        merged_count = 0
        for new_step in new_plan.steps:
            if new_step.step_id in old_steps_map:
                old_step = old_steps_map[new_step.step_id]
                # 继承结果
                new_step.result = old_step.result
                new_step.status = 'success'
                new_step.extracted_data = old_step.extracted_data
                merged_count += 1
                
                if self.verbose:
                    print(f"   ✅ 继承步骤 {new_step.step_id}: {new_step.description[:50]}")
        
        # 继承上下文数据
        for key, value in old_plan.context.items():
            if key not in new_plan.context:
                new_plan.context[key] = value
                if self.verbose:
                    print(f"   💾 继承上下文: {key} = {value}")
        
        if self.verbose:
            print(f"   共继承 {merged_count} 个步骤的结果\n")
    
    def _build_iterative_prompt(self, original_query: str, execution_history: list) -> str:
        """
        构建迭代 prompt，包含之前的执行历史
        
        Args:
            original_query: 原始用户查询
            execution_history: 执行历史记录
            
        Returns:
            增强后的 prompt
        """
        prompt_lines = [f"原始请求: {original_query}"]
        prompt_lines.append("\n【之前的执行历史】\n")
        
        for i, history in enumerate(execution_history, 1):
            prompt_lines.append(f"--- 第 {i} 次尝试 ---")
            prompt_lines.append(f"\nAI 的响应:\n{history['ai_response'][:500]}...\n")
            
            if history['results']:
                prompt_lines.append(f"\n工具执行结果:")
                for j, result in enumerate(history['results'], 1):
                    prompt_lines.append(f"\n  工具 {j}: {result}")
            
            prompt_lines.append("")
        
        prompt_lines.append("\n【重要提示】")
        prompt_lines.append("根据上面的执行历史，请：")
        prompt_lines.append("1. 如果之前的工具调用失败，请分析原因并修正参数")
        prompt_lines.append("2. 如果已经成功，请直接给出最终回答")
        prompt_lines.append("3. 如果需要继续执行工具，请返回新的工具调用 JSON")
        prompt_lines.append("4. 不要重复已经失败的调用方式")
        
        return "\n".join(prompt_lines)
    
    def _build_final_prompt(self, original_query: str, execution_history: list) -> str:
        """
        构建最终回复的 prompt
        
        Args:
            original_query: 原始用户查询
            execution_history: 执行历史记录
            
        Returns:
            最终 prompt
        """
        prompt_lines = [f"原始请求: {original_query}"]
        prompt_lines.append("\n【完整执行历史】\n")
        
        for i, history in enumerate(execution_history, 1):
            prompt_lines.append(f"--- 第 {i} 次尝试 ---")
            prompt_lines.append(f"\nAI 计划:\n{history['ai_response'][:500]}...\n")
            
            if history['results']:
                prompt_lines.append(f"\n执行结果:")
                for j, result in enumerate(history['results'], 1):
                    prompt_lines.append(f"\n  {result}")
            
            prompt_lines.append("")
        
        # 检查是否有成功执行
        has_success = False
        for h in execution_history:
            for r in h['results']:
                # results 可能是字符串或字典
                if isinstance(r, dict):
                    if not r.get('error', ''):
                        has_success = True
                        break
                elif isinstance(r, str):
                    # 如果是字符串，检查是否包含失败标记
                    if '❌ 失败' not in r and 'Error' not in r:
                        has_success = True
                        break
            if has_success:
                break
        
        prompt_lines.append("\n【要求】")
        if has_success:
            prompt_lines.append("基于以上成功的执行结果，给用户一个完整、清晰的回答。")
        else:
            prompt_lines.append("所有尝试都失败了，请：")
            prompt_lines.append("1. 说明尝试了哪些方法")
            prompt_lines.append("2. 解释失败的原因")
            prompt_lines.append("3. 提供可能的解决方案或建议")
        
        return "\n".join(prompt_lines)


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SKILL 运行时系统"
    )
    parser.add_argument(
        "--dirs", "-d",
        nargs="+",
        default=["./skills"],
        help="SKILL 目录列表"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="API 地址"
    )
    parser.add_argument(
        "--api-key",
        default="test",
        help="API Key"
    )
    parser.add_argument(
        "--query", "-q",
        metavar="QUESTION",
        help="单次查询（非交互模式）"
    )
    parser.add_argument(
        "--list-skills", "-l",
        action="store_true",
        help="列出所有 SKILL 并退出"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志信息"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="任务失败后的最大重试次数（默认 3）"
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-4",
        help="AI 模型名称（默认 gpt-4）"
    )
    
    args = parser.parse_args()
    
    runtime = SkillRuntime(
        skill_dirs=args.dirs,
        api_url=args.api_url,
        api_key=args.api_key,
        model=args.model,
        verbose=args.verbose
    )
    
    # 保存最大重试次数配置
    runtime.max_retries = args.max_retries
    
    if args.list_skills:
        runtime.skill_manager.initialize()
        skills = runtime.skill_manager.list_active_skills()
        print(f"\n已加载 {len(skills)} 个 SKILL:\n")
        for skill in skills:
            print(f"• {skill['name']}")
            print(f"  {skill['description'][:100]}...\n")
    
    elif args.query:
        runtime.skill_manager.initialize()
        
        # 渐进式调用：注入 Skill 注册表
        registry_summary = runtime.skill_manager.get_skill_registry_summary()
        runtime.ai.set_skill_registry(registry_summary)
        
        # 第一次调用 AI
        print("\n🌐 [Runtime] 调用 AI API...")
        response = runtime.ai.chat_with_skills(args.query, "")
        print(f"\n🤖 AI (初步回复): {response}\n")
        
        # 检测并执行工具调用或任务计划
        print("-"*80)
        print("🔧 [步骤3] 工具调用检测与执行")
        print("-"*80)
                
        # 先尝试解析为任务计划
        print("🔍 [Runtime] 尝试解析任务计划...")
        plan = runtime.task_planner.parse_task_plan(response)
                
        if plan:
            # 执行多步骤任务计划
            print(f"✅ [Planner] 检测到多步骤任务计划")
            print(f"   任务描述: {plan.task_description}")
            print(f"   步骤数量: {len(plan.steps)}\n")
            runtime._execute_task_plan(plan, max_retries=getattr(runtime, 'max_retries', 3), original_user_query=args.query)
        else:
            # 检测单个工具调用
            print("🔍 [Executor] 检测工具调用意图...")
            tool_calls = runtime.tool_executor.detect_tool_calls(response)
            
            if tool_calls:
                print(f"✅ [Executor] 检测到 {len(tool_calls)} 个工具调用")
                
                # 执行所有工具调用
                execution_results = []
                for tc in tool_calls:
                    result = runtime.tool_executor.execute_tool_call(tc)
                    formatted_result = runtime.tool_executor.format_execution_result(tc, result)
                    execution_results.append(formatted_result)
                    print(formatted_result)
                
                # 让 AI 基于真实结果再次回复
                print("\n🤖 AI 生成最终回复（基于真实执行结果）...\n")
                enhanced_prompt = args.query + "\n\n【AI 初步计划】\n" + response
                enhanced_prompt += "\n\n".join(execution_results)
                enhanced_prompt += "\n\n请基于以上真实的执行结果给用户一个完整的回答。"
                
                final_response = runtime.ai.chat_with_skills(enhanced_prompt, "")
                print(f"🤖 AI (最终回复):\n{final_response}\n")
            else:
                print(f"ℹ️  [Executor] 未检测到工具调用，直接返回 AI 回复")
    
    else:
        runtime.start()


if __name__ == "__main__":
    main()
