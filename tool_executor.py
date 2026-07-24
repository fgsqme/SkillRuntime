#!/usr/bin/env python3
"""
tool_executor.py - 工具执行器

功能：
- 解析 AI 回复中的工具调用意图
- 实际执行 SKILL 脚本
- 将执行结果返回给 AI 进行二次回复
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self, skills_base_path: str = "./skills", verbose: bool = True):
        self.skills_base = Path(skills_base_path)
        self.verbose = verbose
        
    def detect_tool_calls(self, ai_response: str) -> List[Dict]:
        """
        检测 AI 回复中的工具调用意图
            
        Args:
            ai_response: AI 的回复文本
                
        Returns:
            工具调用列表，每个包含 skill_name, script, args
        """
        import json
        
        tool_calls = []
        
        # 模式1: JSON 代码块（推荐）
        # ```json
        # {
        #   "tool_call": {
        #     "skill_name": "shell-executor",
        #     "script": "execute_command.py",
        #     "args": "ls -l /tmp"
        #   }
        # }
        # ```
        json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        matches = re.findall(json_pattern, ai_response, re.DOTALL)
        
        for json_str in matches:
            try:
                data = json.loads(json_str.strip())
                if 'tool_call' in data:
                    tc = data['tool_call']
                    skill_name = tc.get('skill_name', '')
                    script = tc.get('script', '')
                    args = tc.get('args', '')
                    
                    if skill_name and script:
                        tool_calls.append({
                            'skill_name': skill_name,
                            'script': f"skills/{skill_name}/scripts/{script}",
                            'args': args,
                            'type': 'json_block'
                        })
            except (json.JSONDecodeError, KeyError, AttributeError):
                continue
        
        # 模式2: 纯 JSON 对象（无代码块）
        if not tool_calls:
            try:
                # 尝试直接解析整个响应为 JSON
                data = json.loads(ai_response.strip())
                if 'tool_call' in data:
                    tc = data['tool_call']
                    skill_name = tc.get('skill_name', '')
                    script = tc.get('script', '')
                    args = tc.get('args', '')
                    
                    if skill_name and script:
                        tool_calls.append({
                            'skill_name': skill_name,
                            'script': f"skills/{skill_name}/scripts/{script}",
                            'args': args,
                            'type': 'pure_json'
                        })
            except (json.JSONDecodeError, KeyError, AttributeError):
                pass
        
        # 模式3: TOOL_CALL 标记（向后兼容）
        # [TOOL_CALL: shell-executor | execute_command.py | ls -l /tmp]
        if not tool_calls:
            tool_call_pattern = r'\[TOOL_CALL:\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^\]]+)\]'
            matches = re.findall(tool_call_pattern, ai_response)
            for skill_name, script, args in matches:
                # 清理参数，去除首尾空白和引号
                args_clean = args.strip()
                tool_calls.append({
                    'skill_name': skill_name.strip(),
                    'script': f"skills/{skill_name.strip()}/scripts/{script.strip()}",
                    'args': args_clean,
                    'type': 'tool_call_marker'
                })
        
        # 模式4: 明确的代码块调用（向后兼容）
        # ```bash
        # python scripts/execute_command.py "ls -la"
        # ```
        if not tool_calls:
            bash_pattern = r'```(?:bash|shell)?\s*\npython\s+(skills/[^/]+/scripts/\S+\.py)\s+(.*?)\n```'
            matches = re.findall(bash_pattern, ai_response, re.DOTALL)
            for script, args in matches:
                skill_name = self._extract_skill_from_path(script)
                tool_calls.append({
                    'skill_name': skill_name,
                    'script': script,
                    'args': args.strip().strip('"').strip("'"),
                    'type': 'code_block'
                })
            
        return tool_calls
    
    def execute_tool_call(self, tool_call: Dict) -> Dict:
        """
        执行单个工具调用
        
        Args:
            tool_call: 工具调用信息
            
        Returns:
            执行结果
        """
        if self.verbose:
            print(f"\n🔧 [Executor] 检测到工具调用:")
            print(f"   Skill: {tool_call['skill_name']}")
            print(f"   Script: {tool_call['script']}")
            print(f"   Args: {tool_call['args']}")
            print(f"   Type: {tool_call.get('type', 'unknown')}")
        
        # 构建脚本路径
        script_path = self.skills_base.parent / tool_call['script']
        
        if not script_path.exists():
            if self.verbose:
                print(f"❌ [Executor] 脚本不存在: {script_path}")
            return {
                'success': False,
                'error': f"Script not found: {script_path}",
                'output': ''
            }
        
        # 执行脚本
        try:
            if self.verbose:
                print(f"✅ [Executor] 执行脚本: python {script_path} {tool_call['args']}")
            
            # 构建命令
            # 对于 execute_command.py，整个 args 应该作为单个 command 参数传递
            if 'execute_command.py' in str(script_path):
                # 直接将整个 args 字符串作为 command 参数
                cmd = ['python', str(script_path), tool_call['args']]
            else:
                # 其他脚本使用 shlex.split() 解析参数
                import shlex
                try:
                    args_list = shlex.split(tool_call['args'])
                except ValueError:
                    # 如果解析失败，直接使用原始字符串
                    args_list = [tool_call['args']]
                cmd = ['python', str(script_path)] + args_list
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.skills_base.parent)
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            
            if self.verbose:
                print(f"📊 [Executor] 执行完成 (exit code: {result.returncode})")
                if output:
                    print(f"📝 [Executor] 输出 ({len(output)} 字符)")
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': output,
                'error': result.stderr if result.returncode != 0 else ''
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out after 60 seconds"
            if self.verbose:
                print(f"⏱️  [Executor] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'output': ''
            }
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            if self.verbose:
                print(f"❌ [Executor] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'output': ''
            }
    
    def _extract_skill_from_path(self, script_path: str) -> str:
        """从脚本路径提取 skill 名称"""
        # scripts/shell-executor/scripts/execute_command.py -> shell-executor
        parts = Path(script_path).parts
        if 'skills' in parts:
            idx = parts.index('skills')
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return 'unknown'
    
    def _find_script_for_command(self, skill_name: str, command: str) -> Optional[Path]:
        """根据命令查找对应的脚本"""
        skill_path = self.skills_base / skill_name
        
        if not skill_path.exists():
            return None
        
        scripts_dir = skill_path / "scripts"
        if not scripts_dir.exists():
            return None
        
        # 根据命令关键词匹配脚本
        command_lower = command.lower()
        
        for script in scripts_dir.glob("*.py"):
            script_name = script.stem.lower()
            
            # execute_command -> 匹配 "执行", "命令", "run", "execute"
            if 'execute' in script_name or 'command' in script_name:
                if any(kw in command_lower for kw in ['执行', '命令', 'run', 'execute', 'ls', 'pwd', 'cat']):
                    return script.relative_to(self.skills_base.parent)
            
            # validate_command -> 匹配 "验证", "validate"
            if 'validate' in script_name:
                if any(kw in command_lower for kw in ['验证', '检查', 'validate', 'check']):
                    return script.relative_to(self.skills_base.parent)
        
        # 默认返回第一个脚本
        scripts = list(scripts_dir.glob("*.py"))
        if scripts:
            return scripts[0].relative_to(self.skills_base.parent)
        
        return None
    
    def format_execution_result(self, tool_call: Dict, result: Dict) -> str:
        """
        格式化执行结果为 AI 可读的格式
        
        Args:
            tool_call: 工具调用信息
            result: 执行结果
            
        Returns:
            格式化的结果文本
        """
        lines = []
        lines.append(f"\n【工具执行结果】")
        lines.append(f"Skill: {tool_call['skill_name']}")
        lines.append(f"命令: {tool_call['args']}")
        lines.append(f"状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        if result['output']:
            lines.append(f"\n输出:\n```\n{result['output']}\n```")
        
        if result['error']:
            lines.append(f"\n错误:\n```\n{result['error']}\n```")
        
        lines.append(f"\n请基于以上真实执行结果回答用户，不要编造数据。")
        
        return "\n".join(lines)
    
    def identify_error_type(self, result: Dict) -> str:
        """
        识别错误类型
        
        Args:
            result: 执行结果
            
        Returns:
            错误类型字符串
        """
        if result.get('success', False):
            return 'none'
        
        error_msg = result.get('error', '').lower()
        output = result.get('output', '').lower()
        combined = f"{error_msg} {output}"
        
        # 缺少模块
        if any(kw in combined for kw in ['module not found', 'no module named', 'importerror']):
            return 'missing_module'
        
        # 命令不存在
        if any(kw in combined for kw in ['command not found', 'not recognized']):
            return 'command_not_found'
        
        # 权限错误
        if any(kw in combined for kw in ['permission denied', 'access denied']):
            return 'permission_denied'
        
        # 超时
        if any(kw in combined for kw in ['timeout', 'timed out']):
            return 'timeout'
        
        # 文件不存在
        if any(kw in combined for kw in ['file not found', 'no such file']):
            return 'file_not_found'
        
        # 语法错误
        if any(kw in combined for kw in ['syntaxerror', 'invalid syntax']):
            return 'syntax_error'
        
        # 网络错误
        if any(kw in combined for kw in ['connection', 'network']):
            return 'network_error'
        
        return 'unknown'


def main():
    """测试工具执行器"""
    import sys
    
    executor = ToolExecutor("./skills")
    
    if len(sys.argv) > 1:
        # 从参数读取 AI 回复
        ai_response = sys.argv[1]
    else:
        # 测试用例
        ai_response = """我将使用 shell-executor 技能执行 `ls -l /tmp` 命令：

```bash
python skills/shell-executor/scripts/execute_command.py "ls -l /tmp"
```
"""
    
    print("检测工具调用...")
    tool_calls = executor.detect_tool_calls(ai_response)
    
    if tool_calls:
        print(f"检测到 {len(tool_calls)} 个工具调用:\n")
        for tc in tool_calls:
            print(f"- {tc}")
            
            # 执行
            result = executor.execute_tool_call(tc)
            
            # 格式化结果
            formatted = executor.format_execution_result(tc, result)
            print(formatted)
    else:
        print("未检测到工具调用")


if __name__ == "__main__":
    main()
