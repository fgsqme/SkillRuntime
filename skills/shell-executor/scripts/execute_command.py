#!/usr/bin/env python3
"""
execute_command.py - Shell 命令执行器（简单中转）

功能：直接传递命令到 shell 执行，捕获输出和错误
"""

import subprocess
import sys
import time


def main():
    """命令行接口 - 简单中转模式"""
    if len(sys.argv) < 2:
        print("用法: python execute_command.py <command> [--timeout <seconds>]", file=sys.stderr)
        sys.exit(1)
    
    # 解析参数
    command_parts = []
    timeout = None
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--timeout' and i + 1 < len(sys.argv):
            try:
                timeout = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print("错误: timeout 必须是整数", file=sys.stderr)
                sys.exit(1)
        else:
            command_parts.append(sys.argv[i])
            i += 1
    
    if not command_parts:
        print("用法: python execute_command.py <command> [--timeout <seconds>]", file=sys.stderr)
        sys.exit(1)
    
    # 获取要执行的命令（支持多个参数拼接）
    command = ' '.join(command_parts)
    
    try:
        start_time = time.time()
        
        # 直接执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            errors='replace',
            timeout=timeout
        )
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 3)
        
        # 输出结果
        print(f"Exit Code: {result.returncode}")
        print(f"Execution Time: {execution_time}s")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        
        # 返回退出码
        sys.exit(result.returncode)
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        execution_time = round(end_time - start_time, 3)
        print(f"Exit Code: -1")
        print(f"Execution Time: {execution_time}s")
        print(f"\nSTDERR:\nCommand timed out after {timeout} seconds", file=sys.stderr)
        sys.exit(-1)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(-1)


if __name__ == "__main__":
    main()
