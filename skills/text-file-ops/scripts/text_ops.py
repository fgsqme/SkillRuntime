#!/usr/bin/env python3
"""
text_ops.py - 文本文件操作工具

功能：读取、写入、搜索、替换文本文件内容
支持：整文件读取、指定行读取、行列定位、写入/追加、批量替换、内容搜索
"""

import argparse
import json
import os
import re
import sys


def read_file(args):
    """读取文件内容"""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    encoding = args.encoding or 'utf-8'

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        print(f"错误: 编码失败 ({encoding}): {e}", file=sys.stderr)
        print("提示: 尝试使用 --encoding gbk 或 --encoding latin-1", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取失败: {e}", file=sys.stderr)
        sys.exit(1)

    total_lines = len(lines)

    # 指定行范围
    if args.start_line is not None or args.end_line is not None:
        start = (args.start_line or 1) - 1  # 转为0索引
        end = args.end_line or total_lines
        start = max(0, start)
        end = min(end, total_lines)
        selected = lines[start:end]
        content = ''.join(selected)
        result = {
            "action": "read",
            "file": filepath,
            "total_lines": total_lines,
            "line_range": f"{start+1}-{end}",
            "lines_returned": len(selected),
            "content": content
        }
    # 指定行列定位
    elif args.row is not None and args.col is not None:
        row = args.row - 1
        if row < 0 or row >= total_lines:
            print(f"错误: 行号 {args.row} 超出范围 (1-{total_lines})", file=sys.stderr)
            sys.exit(1)
        line = lines[row]
        col_start = args.col - 1
        col_end = args.col_end or args.col
        col_start = max(0, col_start)
        col_end = min(col_end, len(line.rstrip('\n')))
        text = line[col_start:col_end]
        result = {
            "action": "read",
            "file": filepath,
            "total_lines": total_lines,
            "position": f"行{args.row}, 列{args.col}-{col_end}",
            "content": text
        }
    # 指定单行
    elif args.line is not None:
        line_num = args.line - 1
        if line_num < 0 or line_num >= total_lines:
            print(f"错误: 行号 {args.line} 超出范围 (1-{total_lines})", file=sys.stderr)
            sys.exit(1)
        content = lines[line_num]
        result = {
            "action": "read",
            "file": filepath,
            "total_lines": total_lines,
            "line_number": args.line,
            "content": content
        }
    # 读取全部
    else:
        content = ''.join(lines)
        result = {
            "action": "read",
            "file": filepath,
            "total_lines": total_lines,
            "content": content
        }

    # 截断大内容
    if args.max_output and len(result.get("content", "")) > args.max_output:
        result["content"] = result["content"][:args.max_output]
        result["truncated"] = True
        result["truncated_at"] = args.max_output

    print(json.dumps(result, ensure_ascii=False, indent=2))


def write_file(args):
    """写入文件"""
    filepath = args.file
    encoding = args.encoding or 'utf-8'
    mode = args.mode or 'overwrite'

    # 检查目录是否存在
    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        if args.mkdir:
            os.makedirs(dirpath, exist_ok=True)
        else:
            print(f"错误: 目录不存在: {dirpath}", file=sys.stderr)
            print("提示: 使用 --mkdir 自动创建目录", file=sys.stderr)
            sys.exit(1)

    # 获取写入内容
    content = args.content
    if args.content_file:
        if not os.path.exists(args.content_file):
            print(f"错误: 内容文件不存在: {args.content_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.content_file, 'r', encoding=encoding) as f:
            content = f.read()

    if content is None:
        # 从stdin读取
        content = sys.stdin.read()

    # 追加换行符
    if args.newline:
        if not content.endswith('\n'):
            content += '\n'

    try:
        write_mode = 'a' if mode == 'append' else 'w'
        with open(filepath, write_mode, encoding=encoding) as f:
            f.write(content)

        # 返回结果
        file_size = os.path.getsize(filepath)
        with open(filepath, 'r', encoding=encoding) as f:
            total_lines = sum(1 for _ in f)

        result = {
            "action": "write",
            "file": filepath,
            "mode": mode,
            "bytes_written": len(content.encode(encoding)),
            "file_size": file_size,
            "total_lines": total_lines,
            "success": True
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"错误: 写入失败: {e}", file=sys.stderr)
        sys.exit(1)


def search_text(args):
    """搜索文本内容"""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    encoding = args.encoding or 'utf-8'
    pattern = args.pattern
    use_regex = args.regex

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            lines = f.readlines()
    except Exception as e:
        print(f"错误: 读取失败: {e}", file=sys.stderr)
        sys.exit(1)

    matches = []
    for i, line in enumerate(lines, 1):
        if use_regex:
            if re.search(pattern, line):
                matches.append({"line": i, "content": line.rstrip('\n')})
        else:
            if pattern in line:
                matches.append({"line": i, "content": line.rstrip('\n')})

    # 限制结果数量
    if args.max_results and len(matches) > args.max_results:
        matches = matches[:args.max_results]

    result = {
        "action": "search",
        "file": filepath,
        "pattern": pattern,
        "regex": use_regex,
        "total_matches": len(matches),
        "matches": matches
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def replace_text(args):
    """批量替换文本"""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    encoding = args.encoding or 'utf-8'

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
    except Exception as e:
        print(f"错误: 读取失败: {e}", file=sys.stderr)
        sys.exit(1)

    original_content = content
    replace_count = 0

    # 从参数构建替换规则
    replacements = []
    if args.old and args.new is not None:
        replacements.append((args.old, args.new))
    elif args.replacements_json:
        try:
            replacements = json.loads(args.replacements_json)
        except json.JSONDecodeError as e:
            print(f"错误: JSON解析失败: {e}", file=sys.stderr)
            sys.exit(1)

    if not replacements:
        print("错误: 未提供替换规则。使用 --old/--new 或 --replacements", file=sys.stderr)
        sys.exit(1)

    # 执行替换
    for old_text, new_text in replacements:
        if args.regex:
            new_content, count = re.subn(old_text, new_text, content)
        else:
            new_content = content.replace(old_text, new_text)
            count = content.count(old_text)
        replace_count += count
        content = new_content

    # 写回文件
    if args.dry_run:
        result = {
            "action": "replace",
            "file": filepath,
            "dry_run": True,
            "replacements_made": replace_count,
            "preview": content[:500] if len(content) > 500 else content
        }
    else:
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
            result = {
                "action": "replace",
                "file": filepath,
                "replacements_made": replace_count,
                "success": True
            }
        except Exception as e:
            print(f"错误: 写入失败: {e}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def file_info(args):
    """获取文件信息"""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    encoding = args.encoding or 'utf-8'

    try:
        stat = os.stat(filepath)
        with open(filepath, 'r', encoding=encoding) as f:
            lines = f.readlines()

        total_lines = len(lines)
        total_chars = sum(len(line) for line in lines)
        max_line_length = max((len(line.rstrip('\n')) for line in lines), default=0)

        result = {
            "action": "info",
            "file": filepath,
            "size_bytes": stat.st_size,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "max_line_length": max_line_length,
            "last_modified": stat.st_mtime
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='文本文件操作工具 - 读取、写入、搜索、替换',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('action', choices=['read', 'write', 'search', 'replace', 'info'],
                        help='操作类型: read(读取), write(写入), search(搜索), replace(替换), info(信息)')
    parser.add_argument('--file', '-f', required=True, help='目标文件路径')
    parser.add_argument('--encoding', '-e', help='文件编码 (默认: utf-8)')

    # 读取相关参数
    parser.add_argument('--line', '-l', type=int, help='读取指定行号')
    parser.add_argument('--start-line', type=int, help='读取起始行号')
    parser.add_argument('--end-line', type=int, help='读取结束行号')
    parser.add_argument('--row', type=int, help='指定行号 (与 --col 配合)')
    parser.add_argument('--col', type=int, help='指定列号 (与 --row 配合)')
    parser.add_argument('--col-end', type=int, help='指定结束列号')
    parser.add_argument('--max-output', type=int, default=100000, help='最大输出字符数 (默认: 100000)')

    # 写入相关参数
    parser.add_argument('--content', '-c', help='写入内容')
    parser.add_argument('--content-file', help='从文件读取写入内容')
    parser.add_argument('--mode', '-m', choices=['overwrite', 'append'], default='overwrite',
                        help='写入模式: overwrite(覆盖), append(追加)')
    parser.add_argument('--mkdir', action='store_true', help='自动创建不存在的目录')
    parser.add_argument('--newline', action='store_true', help='末尾自动添加换行符')

    # 搜索相关参数
    parser.add_argument('--pattern', '-p', help='搜索模式/文本')
    parser.add_argument('--regex', '-r', action='store_true', help='使用正则表达式')
    parser.add_argument('--max-results', type=int, default=100, help='最大结果数 (默认: 100)')

    # 替换相关参数
    parser.add_argument('--old', help='被替换的文本')
    parser.add_argument('--new', help='替换后的文本')
    parser.add_argument('--replacements', dest='replacements_json', help='批量替换规则 (JSON格式)')
    parser.add_argument('--dry-run', action='store_true', help='预览替换结果，不实际写入')

    args = parser.parse_args()

    # 路由到对应操作
    actions = {
        'read': read_file,
        'write': write_file,
        'search': search_text,
        'replace': replace_text,
        'info': file_info,
    }

    actions[args.action](args)


if __name__ == "__main__":
    main()
