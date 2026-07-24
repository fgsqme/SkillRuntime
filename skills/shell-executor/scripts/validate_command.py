#!/usr/bin/env python3
"""
validate_command.py - Shell 命令安全验证器

功能：
- 检测危险命令模式
- 防止命令注入攻击
- 检查路径遍历
- 验证资源使用风险
"""

import re
import sys
from typing import Tuple, List


# 危险命令模式（正则表达式）
DANGEROUS_PATTERNS = [
    # 递归删除根目录
    (r'rm\s+(-rf?|--recursive)\s+/', 'Recursive deletion of root or system directories'),
    (r'rm\s+-rf\s+\*', 'Wildcard deletion with recursive flag'),
    
    # 磁盘操作
    (r'dd\s+if=/dev/(zero|null|random)', 'Disk wiping or corruption'),
    (r'mkfs\.', 'Filesystem formatting'),
    (r'fdisk\s+', 'Disk partitioning'),
    
    # Fork bomb
    (r':\(\)\s*\{.*:.*\|.*&.*\}', 'Fork bomb detected'),
    (r'\.\(\)\s*\{', 'Fork bomb variant'),
    
    # 权限提升
    (r'sudo\s+rm\s+', 'Root deletion command'),
    (r'sudo\s+chmod\s+777', 'Dangerous permission change'),
    
    # 网络攻击工具
    (r'nmap\s+', 'Network scanning tool'),
    (r'hping3?\s+', 'Network flooding tool'),
    (r'metasploit', 'Penetration testing framework'),
    
    # 系统破坏
    (r'>\s*/etc/(passwd|shadow|fstab)', 'System file overwrite'),
    (r'echo.*>\s*/dev/sd', 'Device file corruption'),
    
    # 环境变量注入
    (r'\$\{.*\}', 'Potential variable injection'),
    (r'`.*`', 'Command substitution (use $() instead)'),
]

# 需要用户确认的命令
REQUIRES_CONFIRMATION = [
    r'rm\s+',           # File deletion
    r'mv\s+',           # File move/rename
    r'cp\s+',           # File copy (overwrite risk)
    r'dd\s+',           # Disk operations
    r'chmod\s+',        # Permission changes
    r'chown\s+',        # Ownership changes
    r'pip\s+install',   # Package installation
    r'apt-get\s+',      # System package management
    r'yum\s+',          # System package management
]


def validate_command(command: str) -> Tuple[bool, str, List[str]]:
    """
    验证命令是否安全
    
    Args:
        command: 要执行的 shell 命令
    
    Returns:
        Tuple[bool, str, List[str]]: 
            - is_safe: 是否安全
            - message: 验证消息
            - warnings: 警告列表
    """
    warnings = []
    
    # 1. 检查空命令
    if not command or not command.strip():
        return False, "Empty command", []
    
    # 2. 检查命令长度
    if len(command) > 10000:
        return False, "Command too long (max 10000 chars)", []
    
    # 3. 检查危险模式
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous pattern detected: {reason}", []
    
    # 4. 检查是否需要确认
    for pattern in REQUIRES_CONFIRMATION:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(f"⚠️ Command requires user confirmation: {pattern}")
    
    # 5. 检查命令注入尝试
    if ';' in command and '|' not in command:
        # 分号可能是命令分隔符，但不一定是注入
        warnings.append("⚠️ Command contains semicolon (;) - verify it's intentional")
    
    # 6. 检查管道使用
    if '|' in command:
        # 管道是允许的，但需要验证每个部分
        parts = command.split('|')
        for part in parts:
            part = part.strip()
            if part:
                is_part_safe, part_reason, _ = validate_single_command(part)
                if not is_part_safe:
                    return False, f"Pipeline component unsafe: {part_reason}", []
    
    # 7. 检查重定向
    if '>' in command or '>>' in command:
        warnings.append("⚠️ Command contains output redirection - verify target path")
    
    return True, "Command validation passed", warnings


def validate_single_command(command: str) -> Tuple[bool, str]:
    """验证单个命令（不含管道）"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, "OK"


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="验证 shell 命令的安全性"
    )
    parser.add_argument(
        "command",
        help="要验证的 shell 命令"
    )
    parser.add_argument(
        "--strict", "-s",
        action="store_true",
        help="严格模式：将警告视为错误"
    )
    
    args = parser.parse_args()
    
    is_safe, message, warnings = validate_command(args.command)
    
    # 输出结果
    if is_safe:
        print(f"✅ Validation passed: {message}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  {w}")
            
            if args.strict and warnings:
                print("\n⚠️ Strict mode: Treating warnings as errors")
                sys.exit(1)
        sys.exit(0)
    else:
        print(f"❌ Validation failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
