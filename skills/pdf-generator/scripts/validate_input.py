#!/usr/bin/env python3
"""
validate_input.py - PDF生成输入验证器

功能：
- 验证输入内容类型和格式
- 检查HTML安全性（无脚本标签）
- 验证文件大小限制
- 检查输出路径安全性
"""

import os
import sys
import re


def validate_file_path(file_path: str, must_exist: bool = False) -> dict:
    """
    验证文件路径的安全性
    
    Args:
        file_path: 文件路径
        must_exist: 文件是否必须存在
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'file_path': file_path,
        'error': None,
        'warnings': [],
    }
    
    # 检查路径是否为空
    if not file_path:
        result['valid'] = False
        result['error'] = "文件路径不能为空"
        return result
    
    # 检查危险路径
    dangerous_paths = ['/etc/', '/boot/', '/proc/', '/sys/', '/root/']
    for dangerous in dangerous_paths:
        if file_path.startswith(dangerous):
            result['valid'] = False
            result['error'] = f"禁止访问系统路径: {dangerous}"
            return result
    
    # 检查路径遍历攻击
    if '..' in file_path:
        result['valid'] = False
        result['error'] = "路径中包含非法字符: .."
        return result
    
    # 如果文件必须存在，检查是否存在
    if must_exist and not os.path.exists(file_path):
        result['valid'] = False
        result['error'] = f"文件不存在: {file_path}"
        return result
    
    # 检查输出目录是否可写
    output_dir = os.path.dirname(file_path) or '.'
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            result['valid'] = False
            result['error'] = f"无法创建目录: {str(e)}"
            return result
    elif not os.access(output_dir, os.W_OK):
        result['valid'] = False
        result['error'] = f"目录不可写: {output_dir}"
        return result
    
    return result


def validate_html_content(content: str) -> dict:
    """
    验证HTML内容的安全性
    
    Args:
        content: HTML内容
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'content_length': len(content),
        'error': None,
        'warnings': [],
    }
    
    # 检查内容大小（限制为1MB）
    max_size = 1 * 1024 * 1024  # 1MB
    if len(content.encode('utf-8')) > max_size:
        result['valid'] = False
        result['error'] = f"HTML内容过大（最大{max_size // 1024}KB）"
        return result
    
    # 检查危险的HTML标签
    dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<applet', '<form']
    content_lower = content.lower()
    
    for tag in dangerous_tags:
        if tag in content_lower:
            result['valid'] = False
            result['error'] = f"检测到不安全的HTML标签: {tag}"
            return result
    
    # 检查外部资源引用（警告）
    external_patterns = [
        r'src\s*=\s*["\']https?://',
        r'href\s*=\s*["\']https?://',
        r'url\s*\(\s*["\']?https?://',
    ]
    
    for pattern in external_patterns:
        if re.search(pattern, content_lower):
            result['warnings'].append(
                "检测到外部资源引用，可能在离线环境中无法加载"
            )
            break
    
    # 检查内联JavaScript事件
    js_events = ['onclick', 'onload', 'onerror', 'onmouseover', 'onsubmit']
    for event in js_events:
        if event in content_lower:
            result['warnings'].append(
                f"检测到内联JavaScript事件: {event}（将被忽略）"
            )
    
    return result


def validate_markdown_content(content: str) -> dict:
    """
    验证Markdown内容
    
    Args:
        content: Markdown内容
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'content_length': len(content),
        'error': None,
        'warnings': [],
    }
    
    # 检查内容大小（限制为500KB）
    max_size = 500 * 1024  # 500KB
    if len(content.encode('utf-8')) > max_size:
        result['valid'] = False
        result['error'] = f"Markdown内容过大（最大{max_size // 1024}KB）"
        return result
    
    # 检查是否有内容
    if not content.strip():
        result['warnings'].append("内容为空或仅包含空白字符")
    
    return result


def validate_text_content(content: str) -> dict:
    """
    验证纯文本内容
    
    Args:
        content: 文本内容
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'content_length': len(content),
        'error': None,
        'warnings': [],
    }
    
    # 检查内容大小（限制为500KB）
    max_size = 500 * 1024  # 500KB
    if len(content.encode('utf-8')) > max_size:
        result['valid'] = False
        result['error'] = f"文本内容过大（最大{max_size // 1024}KB）"
        return result
    
    # 检查是否有内容
    if not content.strip():
        result['warnings'].append("内容为空或仅包含空白字符")
    
    return result


def validate_output_path(output_path: str) -> dict:
    """
    验证输出PDF路径
    
    Args:
        output_path: 输出文件路径
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'output_path': output_path,
        'error': None,
        'warnings': [],
    }
    
    # 检查扩展名
    if not output_path.endswith('.pdf'):
        result['valid'] = False
        result['error'] = "输出文件必须以.pdf结尾"
        return result
    
    # 验证路径安全性
    path_result = validate_file_path(output_path, must_exist=False)
    if not path_result['valid']:
        result['valid'] = False
        result['error'] = path_result['error']
        return result
    
    # 检查文件大小限制（50MB）
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            result['warnings'].append(
                f"现有文件较大 ({format_file_size(file_size)})，将被覆盖"
            )
    
    return result


def validate_input(input_type: str, input_source: str, 
                   content: str = None, output_path: str = None) -> dict:
    """
    综合验证输入
    
    Args:
        input_type: 输入类型（text/markdown/html）
        input_source: 输入来源（inline/filename）
        content: 内容字符串（如果是inline）
        output_path: 输出路径
    
    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        'valid': True,
        'input_type': input_type,
        'errors': [],
        'warnings': [],
    }
    
    # 验证输入类型
    if input_type not in ['text', 'markdown', 'html']:
        result['valid'] = False
        result['errors'].append(f"不支持的输入类型: {input_type}")
        return result
    
    # 根据类型验证内容
    if content is not None:
        if input_type == 'html':
            validation = validate_html_content(content)
        elif input_type == 'markdown':
            validation = validate_markdown_content(content)
        else:  # text
            validation = validate_text_content(content)
        
        if not validation['valid']:
            result['valid'] = False
            result['errors'].append(validation['error'])
        
        result['warnings'].extend(validation.get('warnings', []))
    
    # 验证输出路径
    if output_path:
        output_validation = validate_output_path(output_path)
        if not output_validation['valid']:
            result['valid'] = False
            result['errors'].append(output_validation['error'])
        
        result['warnings'].extend(output_validation.get('warnings', []))
    
    return result


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="验证PDF生成输入的安全性"
    )
    parser.add_argument(
        "input_type",
        choices=['text', 'markdown', 'html'],
        help="输入内容类型"
    )
    parser.add_argument(
        "input_source",
        help="输入来源（inline或文件名）"
    )
    parser.add_argument(
        "--content-file",
        help="从文件读取内容进行验证"
    )
    parser.add_argument(
        "--output-path",
        help="输出PDF路径"
    )
    
    args = parser.parse_args()
    
    # 读取内容
    content = None
    if args.content_file:
        try:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading content file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    elif args.input_source != 'inline':
        # 假设是文件路径
        try:
            with open(args.input_source, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading input file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    # 执行验证
    result = validate_input(
        args.input_type,
        args.input_source,
        content=content,
        output_path=args.output_path
    )
    
    # 输出结果
    if result['valid']:
        print("✅ Validation Passed")
        if result['warnings']:
            print("\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        print(f"\nInput Type: {args.input_type}")
        if content:
            print(f"Content Length: {len(content)} characters")
        if args.output_path:
            print(f"Output Path: {args.output_path}")
        print(f"\nStatus: ✅ Valid")
        sys.exit(0)
    else:
        print("❌ Validation Failed")
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
