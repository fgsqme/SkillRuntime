#!/usr/bin/env python3
"""
task_planner.py - 任务规划器

功能：
- 分析复杂任务并拆解为多个步骤
- 生成执行计划
- 管理步骤间的数据流转
"""

import json
from typing import Dict, List, Optional


class TaskStep:
    """任务步骤"""
    
    def __init__(self, step_id: int, description: str, skill_name: str, 
                 script: str, args_template: str, depends_on: List[int] = None,
                 extraction: str = None, save_to_context: str = None,
                 context_prompt: str = None):
        self.step_id = step_id
        self.description = description
        self.skill_name = skill_name
        self.script = script
        self.args_template = args_template  # 支持 {variable} 占位符
        self.depends_on = depends_on or []  # 依赖的步骤 ID
        self.extraction = extraction  # 数据提取规则
        self.save_to_context = save_to_context  # 保存到上下文的键名
        self.context_prompt = context_prompt  # 上下文提示词模板，注入依赖步骤的结果
        self.result = None  # 执行结果
        self.extracted_data = {}  # 提取的数据
        self.status = 'pending'  # 执行状态: pending, running, success, failed
        self.retry_count = 0  # 重试次数
        self.error_message = None  # 错误信息
        self.last_error_type = None  # 最后一次错误类型
        self.has_subtasks = False  # 是否已拆分为子任务
        self.sub_task_plan = None  # 子任务执行计划（ExecutionPlan 对象）
        self.parent_step_id = None  # 父步骤 ID（当自身是子任务时）
        self.needs_decompose = False  # 是否需要 AI 分析是否拆分为子任务
        self.verification_result = None  # 验证结果（用于判断步骤是否真正完成）
        
    def to_dict(self) -> dict:
        return {
            'step_id': self.step_id,
            'description': self.description,
            'skill_name': self.skill_name,
            'script': self.script,
            'args_template': self.args_template,
            'depends_on': self.depends_on,
            'result': self.result,
            'extracted_data': self.extracted_data,
            'status': self.status,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'has_subtasks': self.has_subtasks,
            'parent_step_id': self.parent_step_id,
            'needs_decompose': self.needs_decompose,
            'sub_task_plan': self.sub_task_plan.to_dict() if self.sub_task_plan else None
        }


class ExecutionPlan:
    """执行计划"""
    
    def __init__(self, task_description: str):
        self.task_description = task_description
        self.steps: List[TaskStep] = []
        self.context = {}  # 上下文数据存储
        self.current_step = 0
        self.is_complete = False
        
    def add_step(self, step: TaskStep):
        self.steps.append(step)
        
    def get_next_step(self) -> Optional[TaskStep]:
        """获取下一个可执行的步骤"""
        for step in self.steps[self.current_step:]:
            # 检查依赖是否已满足
            if all(dep in [s.step_id for s in self.steps if s.result is not None] 
                   for dep in step.depends_on):
                return step
        return None
    
    def update_context(self, key: str, value):
        """更新上下文数据"""
        self.context[key] = value
        
    def get_context_value(self, key: str, default=None):
        """获取上下文数据"""
        return self.context.get(key, default)
    
    def to_dict(self) -> dict:
        return {
            'task_description': self.task_description,
            'steps': [step.to_dict() for step in self.steps],
            'context': self.context,
            'current_step': self.current_step,
            'is_complete': self.is_complete
        }
    
    def validate_completion(self) -> bool:
        """
        验证任务是否全部成功完成
        
        Returns:
            True 如果所有步骤都成功，否则 False
        """
        if not self.steps:
            return False
        
        # 检查所有步骤是否都成功
        all_success = all(step.status == 'success' for step in self.steps)
        
        # 更新完成状态
        self.is_complete = all_success
        
        return all_success
    
    def get_failed_steps(self) -> List[TaskStep]:
        """
        获取失败的步骤列表
        
        Returns:
            失败的步骤列表
        """
        return [step for step in self.steps if step.status == 'failed']
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """
        检查是否有步骤可以重试
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            True 如果有步骤可以重试
        """
        failed_steps = self.get_failed_steps()
        return any(step.retry_count < max_retries for step in failed_steps)


class TaskPlanner:
    """任务规划器"""
    
    def __init__(self, verbose: bool = True, ai_integration=None):
        self.verbose = verbose
        self.ai_integration = ai_integration  # AI 集成实例，用于智能数据提取
    
    def _fix_json_string(self, json_str: str) -> str:
        """
        修复常见的 JSON 格式问题
        
        Args:
            json_str: 原始 JSON 字符串
            
        Returns:
            修复后的 JSON 字符串
        """
        import re
        
        if self.verbose:
            print(f"🔧 [Planner] 修复前 JSON 长度: {len(json_str)}")
        
        # 首先尝试提取 args 的值并修复
        def fix_args_field(match):
            prefix = match.group(1)  # "args": 
            value_start = match.group(2)  # 开始引号
            value_content = match.group(3)  # 值内容
            value_end = match.group(4)  # 结束引号和后续字符
            
            # 将值内部的双引号替换为单引号
            fixed_value = value_content.replace('"', "'")
            if fixed_value != value_content:
                if self.verbose:
                    print(f"🔧 [Planner] 修复 args 字段: {value_content[:50]}... -> {fixed_value[:50]}...")
            return f'{prefix}{value_start}{fixed_value}{value_end}'
        
        # 使用正则匹配 args 字段并修复
        pattern = r'("args":\s*)(")([^"]*?)("[,\s}\]])'
        json_str = re.sub(pattern, fix_args_field, json_str)
        
        if self.verbose:
            print(f"🔧 [Planner] 修复后 JSON 长度: {len(json_str)}")
        
        return json_str
    
    def parse_task_plan(self, ai_response: str) -> Optional[ExecutionPlan]:
        """
        解析 AI 返回的任务计划
        
        Args:
            ai_response: AI 的回复
            
        Returns:
            ExecutionPlan 或 None
        """
        import re
        
        if self.verbose:
            print(f"🔍 [Planner] parse_task_plan 被调用，响应长度: {len(ai_response)}")
        
        try:
            # 先尝试提取 JSON 代码块
            json_match = re.search(r'```(?:json)?\s*(.*?)```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                if self.verbose:
                    print(f"🔍 [Planner] 提取到 JSON 代码块，长度: {len(json_str)}")
            else:
                json_str = ai_response.strip()
                if self.verbose:
                    print(f"🔍 [Planner] 未找到代码块，直接使用原始响应，长度: {len(json_str)}")
            
            # 尝试修复常见的 JSON 问题
            json_str_fixed = self._fix_json_string(json_str)
            if json_str != json_str_fixed and self.verbose:
                print(f"🔧 [Planner] 已修复 JSON 格式")
            
            # 调试：打印前500个字符
            if self.verbose:
                print(f"🔍 [Planner] JSON 前500字符:\n{json_str_fixed}\n")
            
            # 调试：打印所有 args 字段
            if self.verbose:
                import re as regex_module
                args_matches = regex_module.findall(r'"args":\s*"([^"]+)"', json_str_fixed)
                if args_matches:
                    print(f"🔍 [Planner] 找到 {len(args_matches)} 个 args 字段:")
                    for i, arg in enumerate(args_matches):
                        print(f"   {i+1}. {arg[:80]}...")
                else:
                    print(f"🔍 [Planner] 未找到有效的 args 字段")
            
            # 尝试解析 JSON
            data = json.loads(json_str_fixed, strict=False)  # strict=False 允许控制字符
            
            if 'task_plan' not in data:
                if self.verbose:
                    print(f"⚠️  [Planner] JSON 中不包含 task_plan 字段")
                return None
            
            plan_data = data['task_plan']
            plan = ExecutionPlan(plan_data.get('description', ''))
            
            for step_data in plan_data.get('steps', []):
                step = TaskStep(
                    step_id=step_data['step_id'],
                    description=step_data['description'],
                    skill_name=step_data['skill_name'],
                    script=step_data['script'],
                    args_template=step_data['args'],
                    depends_on=step_data.get('depends_on', []),
                    extraction=step_data.get('extraction'),
                    save_to_context=step_data.get('save_to_context'),
                    context_prompt=step_data.get('context_prompt')
                )
                # 检查是否需要 AI 分析拆分为子任务
                if step_data.get('needs_decompose', False):
                    step.needs_decompose = True
                plan.add_step(step)
            
            return plan
            
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            if self.verbose:
                print(f"⚠️  [Planner] 解析任务计划失败: {e}")
            return None
    
    def parse_sub_task_plan(self, ai_response: str) -> Optional['ExecutionPlan']:
        """
        解析 AI 返回的子任务计划
        
        Args:
            ai_response: AI 的回复
            
        Returns:
            ExecutionPlan 或 None（如果 AI 判断不需要拆分）
        """
        import re
        
        if self.verbose:
            print(f"🔍 [Planner] parse_sub_task_plan 被调用，响应长度: {len(ai_response)}")
        
        try:
            # 提取 JSON 代码块
            json_match = re.search(r'```(?:json)?\s*(.*?)```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = ai_response.strip()
            
            # 修复 JSON
            json_str_fixed = self._fix_json_string(json_str)
            
            # 解析 JSON
            data = json.loads(json_str_fixed, strict=False)
            
            if 'sub_task_plan' not in data:
                if self.verbose:
                    print(f"⚠️  [Planner] sub_task_plan 字段不存在，AI 判断不需要拆分")
                return None
            
            sub_data = data['sub_task_plan']
            steps = sub_data.get('steps', [])
            
            # 如果只有一个步骤且和原步骤相同，说明不需要拆分
            if len(steps) <= 1:
                if self.verbose:
                    print(f"ℹ️  [Planner] AI 返回单步骤子任务，判断为不需要拆分")
                return None
            
            # 构建子任务执行计划
            parent_step_id = sub_data.get('parent_step_id', 0)
            plan = ExecutionPlan(sub_data.get('description', f'步骤 {parent_step_id} 的子任务'))
            
            for step_data in steps:
                step = TaskStep(
                    step_id=step_data['step_id'],
                    description=step_data['description'],
                    skill_name=step_data['skill_name'],
                    script=step_data['script'],
                    args_template=step_data['args'],
                    depends_on=step_data.get('depends_on', []),
                    extraction=step_data.get('extraction'),
                    save_to_context=step_data.get('save_to_context'),
                    context_prompt=step_data.get('context_prompt')
                )
                step.parent_step_id = parent_step_id
                plan.add_step(step)
            
            if self.verbose:
                print(f"✅ [Planner] 子任务计划解析成功: {len(plan.steps)} 个子步骤")
            
            return plan
            
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            if self.verbose:
                print(f"⚠️  [Planner] 解析子任务计划失败: {e}")
            return None
    
    def extract_data_from_result(self, result_text: str, extraction_rule: str) -> dict:
        """
        从执行结果中提取数据
        
        Args:
            result_text: 执行结果文本
            extraction_rule: 提取规则（如 "first_line", "json", "regex:pattern", "output_only", "ai_analyze", "smart"）
            
        Returns:
            提取的数据字典
        """
        extracted = {}
        
        if extraction_rule == "smart":
            # 智能提取：先尝试解析结构化输出格式，再用 AI 提取关键信息
            clean_output = self._extract_stdout_from_formatted(result_text)
            if self.ai_integration:
                ai_result = self._extract_with_ai(clean_output)
                if ai_result and 'value' in ai_result:
                    return ai_result
            # AI 不可用时，直接使用清理后的输出
            extracted['value'] = clean_output.strip()
            
        elif extraction_rule == "first_line":
            # 先尝试从格式化输出中提取 STDOUT 内容
            clean_output = self._extract_stdout_from_formatted(result_text)
            lines = clean_output.strip().split('\n')
            
            # 查找 **Output**: 后面的内容
            output_start = -1
            for i, line in enumerate(lines):
                if '**Output**:' in line or '```' in line:
                    output_start = i + 1
                    break
            
            if output_start > 0 and output_start < len(lines):
                # 提取 Output 块中的第一行非空行
                for i in range(output_start, len(lines)):
                    line = lines[i].strip()
                    if line and line != '```':  # 跳过代码块标记
                        extracted['value'] = line
                        return extracted
            
            # 回退：使用清理后输出的第一行
            if lines:
                extracted['value'] = lines[0].strip()
                
        elif extraction_rule == "full_output":
            # 使用清理后的完整输出
            extracted['value'] = self._extract_stdout_from_formatted(result_text).strip()
            
        elif extraction_rule == "output_only":
            # 只提取 **Output**: 块中的内容
            import re
            match = re.search(r'\*\*Output\*\*:\s*```\s*(.*?)\s*```', result_text, re.DOTALL)
            if match:
                extracted['value'] = match.group(1).strip()
            else:
                extracted['value'] = self._extract_stdout_from_formatted(result_text).strip()
            
        elif extraction_rule.startswith("regex:"):
            import re
            pattern = extraction_rule[6:]
            match = re.search(pattern, result_text)
            if match:
                extracted['value'] = match.group(1) if match.lastindex else match.group(0)
        
        elif extraction_rule == "ai_analyze":
            # 使用 AI 智能分析并提取数据
            if hasattr(self, 'ai_integration') and self.ai_integration:
                extracted = self._extract_with_ai(result_text)
            else:
                print(f"⚠️  [Planner] ai_analyze 需要配置 AI 实例，回退到 smart")
                clean_output = self._extract_stdout_from_formatted(result_text)
                extracted['value'] = clean_output.strip()
        
        return extracted
    
    def _extract_stdout_from_formatted(self, result_text: str) -> str:
        """
        从格式化的脚本输出中提取实际数据（STDOUT 部分）
        
        处理 execute_command.py 等脚本的输出格式：
        Exit Code: 0
        Execution Time: 0.001s
        
        STDOUT:
        2026-07-23 15:48:30
        
        Args:
            result_text: 原始输出文本
            
        Returns:
            提取的实际数据（STDOUT 内容），如果没有格式化标记则返回原文
        """
        import re
        
        # 尝试提取 STDOUT: 后面的内容
        stdout_match = re.search(r'STDOUT:\s*\n(.*?)(?:\nSTDERR:|\nErrors:|\Z)', result_text, re.DOTALL)
        if stdout_match:
            return stdout_match.group(1).strip()
        
        # 尝试提取 **Output**: 代码块中的内容
        output_match = re.search(r'\*\*Output\*\*:\s*```\s*(.*?)\s*```', result_text, re.DOTALL)
        if output_match:
            return output_match.group(1).strip()
        
        # 没有格式化标记，返回原文
        return result_text
    
    def _extract_with_ai(self, result_text: str) -> dict:
        """
        使用 AI 智能分析执行结果并提取数据
        
        Args:
            result_text: 执行结果文本
            
        Returns:
            提取的数据字典
        """
        if not self.ai_integration:
            return {'value': result_text.strip()}
        
        try:
            if self.verbose:
                print(f"🤖 [AI 数据提取] 正在分析执行结果...")
                print(f"   结果长度: {len(result_text)} 字符")
            
            # 构建 prompt
            extraction_prompt = f"""你是一个智能数据分析助手。请分析以下脚本执行结果，提取出最有价值的关键信息。

【执行结果】
{result_text}

【要求】
1. 分析这段输出的内容和结构
2. 识别并提取最关键的信息（如：时间、文件名、数值、状态等）
3. 如果输出包含多个信息点，提取最重要的那个
4. 如果是结构化数据（JSON、表格等），提取核心字段
5. 去除无关的日志、错误堆栈、格式化标记等

请以 JSON 格式返回提取结果：
```json
{{
  "extracted_value": "提取的关键信息",
  "explanation": "简要说明为什么提取这个值"
}}
```

如果无法提取有价值的信息，请返回完整但清理过的输出。
"""
            
            # 调用 AI
            response = self.ai_integration.chat_with_skills(
                extraction_prompt,
                "",  # 不注入 SKILL 上下文
                []  # 不使用对话历史
            )
            
            if self.verbose:
                print(f"📥 [AI 响应] 长度: {len(response)} 字符")
            
            # 解析 AI 返回的 JSON
            import re
            import json
            
            # 尝试提取 JSON 代码块
            json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()
            
            # 解析 JSON
            data = json.loads(json_str)
            
            extracted_value = data.get('extracted_value', result_text.strip())
            explanation = data.get('explanation', '')
            
            if self.verbose:
                print(f"✅ [AI 数据提取成功]")
                print(f"   提取值: {extracted_value[:200]}{'...' if len(extracted_value) > 200 else ''}")
                if explanation:
                    print(f"   说明: {explanation}")
            
            return {
                'value': extracted_value,
                'explanation': explanation,
                'method': 'ai_analyze'
            }
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  [AI 数据提取失败]: {e}，回退到 full_output")
            return {'value': result_text.strip(), 'method': 'fallback'}
    
    def fill_args_template(self, template: str, context: dict) -> str:
        """
        填充参数模板中的变量
        
        只替换 {variable_name} 中变量名存在于 context 的占位符，
        其他 { 字符保持原样，避免 str.format() 因非法占位符报错。
        
        Args:
            template: 参数模板，如 "date '{time}'"
            context: 上下文数据
            
        Returns:
            填充后的参数字符串
        """
        import re
        
        if not context:
            return template
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                return str(context[var_name])
            # 变量不在上下文中，保持原样
            return match.group(0)
        
        # 只替换 {variable_name} 格式的占位符
        result = re.sub(r'\{(\w+)\}', replace_var, template)
        return result
    
    def build_context_prompt(self, step, plan) -> str:
        """
        构建上下文提示词，将依赖步骤的结果注入到当前步骤的提示词中
        
        Args:
            step: 当前步骤
            plan: 执行计划
            
        Returns:
            格式化的上下文提示词，如果没有依赖则返回空字符串
        """
        if not step.depends_on:
            return ""
        
        context_lines = []
        context_lines.append("【前序步骤执行结果】")
        context_lines.append("以下是你依赖的步骤的执行结果，请根据需要从中提取和使用数据：")
        context_lines.append("")
        
        for dep_id in step.depends_on:
            dep_step = next((s for s in plan.steps if s.step_id == dep_id), None)
            if dep_step and dep_step.result:
                context_lines.append(f"--- 步骤 {dep_id}: {dep_step.description} ---")
                # 清理输出，去掉格式化标记
                clean_result = self._extract_stdout_from_formatted(dep_step.result)
                context_lines.append(f"结果: {clean_result.strip()}")
                if dep_step.extracted_data:
                    context_lines.append(f"已提取数据: {dep_step.extracted_data}")
                context_lines.append("")
        
        # 添加已保存的上下文变量
        if plan.context:
            context_lines.append("【已保存的上下文变量】")
            for key, value in plan.context.items():
                context_lines.append(f"  {key} = {value}")
            context_lines.append("")
        
        # 如果有 context_prompt 模板，用它来指导数据使用
        if step.context_prompt:
            context_lines.append("【数据使用指引】")
            context_lines.append(step.context_prompt)
        
        return "\n".join(context_lines)
    
    def save_large_data_to_file(self, data: str, step_id: int, max_inline_length: int = 500) -> str:
        """
        如果数据过大，保存到临时文件并返回文件路径
        
        Args:
            data: 要保存的数据
            step_id: 步骤 ID（用于文件名）
            max_inline_length: 最大内联长度，超过此长度则存文件
            
        Returns:
            如果数据小返回 None，否则返回文件路径
        """
        if len(data) <= max_inline_length:
            return None
        
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f'skill_step_{step_id}_output.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        
        if self.verbose:
            print(f"💾 [Planner] 大数据已存文件: {file_path} ({len(data)} 字符)")
        
        return file_path
    
    def analyze_error_and_suggest_fix(self, step: TaskStep, error_message: str, error_type: str = None) -> Dict:
        """
        分析错误并生成修复建议
        
        Args:
            step: 失败的步骤
            error_message: 错误信息
            error_type: 错误类型
            
        Returns:
            包含错误分析和修复建议的字典
        """
        analysis = {
            'step_id': step.step_id,
            'error_type': error_type or 'unknown',
            'error_message': error_message,
            'suggested_action': None,
            'can_auto_fix': False,
            'fix_description': ''
        }
        
        # 分析常见错误类型
        error_lower = error_message.lower()
        
        # 1. 缺少库/模块
        if any(kw in error_lower for kw in ['module not found', 'no module named', 'importerror', '没有这个模块']):
            analysis['error_type'] = 'missing_module'
            # 提取模块名
            import re
            # 尝试多种模式匹配模块名
            patterns = [
                r"No module named ['\"]?([\w-]+)['\"]?",
                r"module ['\"]?([\w-]+)['\"]? not found",
                r"name ['\"]?([\w-]+)['\"]? is not defined"
            ]
            module_name = 'unknown'
            for pattern in patterns:
                match = re.search(pattern, error_message)
                if match:
                    module_name = match.group(1)
                    break
            
            analysis['suggested_action'] = f'pip install {module_name}'
            analysis['can_auto_fix'] = True
            analysis['fix_description'] = f'检测到缺少 Python 模块 "{module_name}"，建议执行 pip install {module_name} 安装'
        
        # 2. 命令不存在
        elif any(kw in error_lower for kw in ['command not found', 'not recognized', '没有那个文件或目录']):
            analysis['error_type'] = 'command_not_found'
            analysis['suggested_action'] = 'install_system_package'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = f'检测到系统命令不存在，可能需要安装相应的软件包'
        
        # 3. 权限错误
        elif any(kw in error_lower for kw in ['permission denied', '权限被拒绝', 'access denied']):
            analysis['error_type'] = 'permission_denied'
            analysis['suggested_action'] = 'check_permissions'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = '检测到权限错误，请检查文件/目录权限或使用 sudo'
        
        # 4. 超时
        elif any(kw in error_lower for kw in ['timeout', 'timed out', '超时']):
            analysis['error_type'] = 'timeout'
            analysis['suggested_action'] = 'increase_timeout_or_optimize'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = '操作超时，可能需要增加超时时间或优化操作'
        
        # 5. 文件不存在
        elif any(kw in error_lower for kw in ['file not found', 'no such file', '没有那个文件']):
            analysis['error_type'] = 'file_not_found'
            analysis['suggested_action'] = 'create_file_or_check_path'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = '文件不存在，请检查路径或创建所需文件'
        
        # 6. 脚本执行错误
        elif any(kw in error_lower for kw in ['syntaxerror', '语法错误', 'invalid syntax']):
            analysis['error_type'] = 'syntax_error'
            analysis['suggested_action'] = 'fix_script_syntax'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = '脚本存在语法错误，需要修复代码'
        
        # 7. 网络连接错误
        elif any(kw in error_lower for kw in ['connection', 'network', '网络', 'timeout']):
            analysis['error_type'] = 'network_error'
            analysis['suggested_action'] = 'check_network_connection'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = '网络连接失败，请检查网络连接'
        
        else:
            analysis['error_type'] = error_type or 'unknown_error'
            analysis['suggested_action'] = 'manual_intervention'
            analysis['can_auto_fix'] = False
            analysis['fix_description'] = f'未知错误: {error_message[:200]}'
        
        return analysis


def main():
    """测试任务规划器"""
    planner = TaskPlanner()
    
    # 示例：AI 返回的任务计划
    ai_response = '''
{
  "task_plan": {
    "description": "获取当前时间并发送通知",
    "steps": [
      {
        "step_id": 1,
        "description": "获取当前系统时间",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "date +'%Y-%m-%d %H:%M:%S'",
        "depends_on": [],
        "extraction": "first_line",
        "save_to_context": "current_time"
      },
      {
        "step_id": 2,
        "description": "发送时间通知",
        "skill_name": "system-notifier",
        "script": "send_notification.py",
        "args": "--title \"当前时间\" --message \"{current_time}\"",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null
      }
    ]
  }
}
'''
    
    plan = planner.parse_task_plan(ai_response)
    
    if plan:
        print(f"✅ 解析成功!")
        print(f"任务: {plan.task_description}")
        print(f"步骤数: {len(plan.steps)}")
        
        for step in plan.steps:
            print(f"\n步骤 {step.step_id}:")
            print(f"  描述: {step.description}")
            print(f"  Skill: {step.skill_name}")
            print(f"  Script: {step.script}")
            print(f"  Args: {step.args_template}")
            print(f"  依赖: {step.depends_on}")
    else:
        print("❌ 解析失败")


if __name__ == "__main__":
    main()
