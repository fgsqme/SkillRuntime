---
name: text-file-ops
description: >-
  快速文本/代码文件操作工具，支持读取、写入、搜索、批量替换。
  当需要读取文件内容、写入文本、搜索关键字、批量替换文本、
  从指定行列读取内容时使用。适用于文本文件、代码文件（.txt、.py、.js、.java、.json、.yaml、.md等）、
  配置文件、日志文件等所有纯文本文件。
whenToUse: >-
  用户需要读取文件内容、写入或追加文本到文件、
  在文件中搜索特定文本、批量替换文件中的内容、
  从指定行号或行列位置读取文本、查看文件信息、
  读取或修改代码文件、配置文件。
---

# 文本/代码文件操作工具

快速读取、写入、搜索、替换文本和代码文件内容。支持 .txt、.py、.js、.java、.json、.yaml、.md 等所有纯文本文件。

## 使用时机

- 读取文件全部内容或指定行
- 写入或追加文本到文件
- 在文件中搜索特定文本
- 批量替换文件中的内容
- 从指定行列位置精确读取
- 查看文件基本信息
- 读取或修改代码文件（.py、.js、.java 等）
- 修改配置文件（.json、.yaml、.ini、.conf 等）

## 操作工作流程

### 1. 读取文件 (read)

```bash
# 读取整个文件
python scripts/text_ops.py read --file /path/to/file.txt

# 读取指定行
python scripts/text_ops.py read --file /path/to/file.txt --line 10

# 读取行范围
python scripts/text_ops.py read --file /path/to/file.txt --start-line 5 --end-line 15

# 从指定行列位置读取
python scripts/text_ops.py read --file /path/to/file.txt --row 3 --col 10 --col-end 50

# 限制输出大小
python scripts/text_ops.py read --file /path/to/file.txt --max-output 5000
```

**参数说明**：
- `--file, -f`：目标文件路径（必需）
- `--line, -l`：读取指定行号
- `--start-line`：起始行号（包含）
- `--end-line`：结束行号（包含）
- `--row`：行号（与 `--col` 配合使用）
- `--col`：起始列号（与 `--row` 配合使用）
- `--col-end`：结束列号
- `--max-output`：最大输出字符数（默认：100000）
- `--encoding, -e`：文件编码（默认：utf-8）

**返回数据格式**：
```json
{
  "action": "read",
  "file": "/path/to/file.txt",
  "total_lines": 100,
  "content": "文件内容..."
}
```

### 2. 写入文件 (write)

```bash
# 覆盖写入
python scripts/text_ops.py write --file /path/to/file.txt --content "Hello World"

# 追加写入
python scripts/text_ops.py write --file /path/to/file.txt --content "New line" --mode append

# 从文件读取内容写入
python scripts/text_ops.py write --file /path/to/file.txt --content-file /path/to/source.txt

# 自动创建目录
python scripts/text_ops.py write --file /path/to/newdir/file.txt --content "data" --mkdir

# 自动添加换行符
python scripts/text_ops.py write --file /path/to/file.txt --content "line" --newline
```

**参数说明**：
- `--content, -c`：写入内容
- `--content-file`：从文件读取写入内容
- `--mode, -m`：写入模式 `overwrite`（覆盖）或 `append`（追加），默认 `overwrite`
- `--mkdir`：自动创建不存在的目录
- `--newline`：末尾自动添加换行符

**返回数据格式**：
```json
{
  "action": "write",
  "file": "/path/to/file.txt",
  "mode": "overwrite",
  "bytes_written": 11,
  "file_size": 11,
  "total_lines": 1,
  "success": true
}
```

### 3. 搜索文本 (search)

```bash
# 简单文本搜索
python scripts/text_ops.py search --file /path/to/file.txt --pattern "关键字"

# 正则表达式搜索
python scripts/text_ops.py search --file /path/to/file.txt --pattern "\d{4}-\d{2}-\d{2}" --regex

# 限制结果数量
python scripts/text_ops.py search --file /path/to/file.txt --pattern "error" --max-results 20
```

**参数说明**：
- `--pattern, -p`：搜索模式或文本
- `--regex, -r`：使用正则表达式
- `--max-results`：最大结果数（默认：100）

**返回数据格式**：
```json
{
  "action": "search",
  "file": "/path/to/file.txt",
  "pattern": "关键字",
  "regex": false,
  "total_matches": 5,
  "matches": [
    {"line": 10, "content": "包含关键字的行内容"},
    {"line": 25, "content": "另一行包含关键字的内容"}
  ]
}
```

### 4. 批量替换 (replace)

```bash
# 单个替换
python scripts/text_ops.py replace --file /path/to/file.txt --old "旧文本" --new "新文本"

# 批量替换（JSON格式）
python scripts/text_ops.py replace --file /path/to/file.txt \
  --replacements '[["旧1","新1"],["旧2","新2"],["旧3","新3"]]'

# 正则替换
python scripts/text_ops.py replace --file /path/to/file.txt \
  --old "\d+" --new "NUM" --regex

# 预览模式（不实际写入）
python scripts/text_ops.py replace --file /path/to/file.txt \
  --old "旧文本" --new "新文本" --dry-run
```

**参数说明**：
- `--old`：被替换的文本
- `--new`：替换后的文本
- `--replacements`：批量替换规则（JSON数组格式）
- `--regex`：使用正则表达式
- `--dry-run`：预览模式，不实际写入文件

**返回数据格式**：
```json
{
  "action": "replace",
  "file": "/path/to/file.txt",
  "replacements_made": 10,
  "success": true
}
```

### 5. 文件信息 (info)

```bash
python scripts/text_ops.py info --file /path/to/file.txt
```

**返回数据格式**：
```json
{
  "action": "info",
  "file": "/path/to/file.txt",
  "size_bytes": 1024,
  "total_lines": 50,
  "total_chars": 1000,
  "max_line_length": 80,
  "last_modified": 1640000000.0
}
```

## 使用示例

### 示例 1：读取配置文件特定部分

```bash
# 读取第10-20行
python scripts/text_ops.py read --file config.txt --start-line 10 --end-line 20
```

### 示例 2：快速写入日志

```bash
# 追加日志
python scripts/text_ops.py write --file app.log --content "2024-01-01 操作完成" --mode append --newline
```

### 示例 3：批量替换配置值

```bash
# 替换多个配置项
python scripts/text_ops.py replace --file config.ini \
  --replacements '[["host=localhost","host=192.168.1.100"],["port=3306","port=3307"]]'
```

### 示例 4：搜索错误日志

```bash
# 搜索所有ERROR行
python scripts/text_ops.py search --file app.log --pattern "ERROR" --max-results 50
```

### 示例 5：从CSV读取特定单元格

```bash
# 读取第5行第3列开始到第10列的内容
python scripts/text_ops.py read --file data.csv --row 5 --col 3 --col-end 10
```

### 示例 6：读取代码文件指定行

```bash
# 读取 Python 文件第20-30行
python scripts/text_ops.py read --file main.py --start-line 20 --end-line 30
```

### 示例 7：批量修改代码中的变量名

```bash
# 批量替换代码中的变量名
python scripts/text_ops.py replace --file app.js \
  --replacements '[["oldVar","newVar"],["oldFunc()","newFunc()"]]'
```

## 任务计划集成示例

```json
{
  "task_plan": {
    "description": "读取配置文件并修改",
    "steps": [
      {
        "step_id": 1,
        "description": "读取当前配置",
        "skill_name": "text-file-ops",
        "script": "text_ops.py",
        "args": "read --file /path/to/config.txt",
        "extraction": "ai_analyze",
        "save_to_context": "current_config"
      },
      {
        "step_id": 2,
        "description": "替换配置值",
        "skill_name": "text-file-ops",
        "script": "text_ops.py",
        "args": "replace --file /path/to/config.txt --old \"old_value\" --new \"new_value\"",
        "depends_on": [1]
      }
    ]
  }
}
```

## 最佳实践

1. **大文件处理**：使用 `--start-line` 和 `--end-line` 分段读取
2. **编码问题**：遇到编码错误时使用 `--encoding gbk` 或 `--encoding latin-1`
3. **批量操作**：使用 `--replacements` JSON格式一次性替换多个值
4. **安全替换**：先用 `--dry-run` 预览，确认无误再执行
5. **输出控制**：使用 `--max-output` 限制大文件输出
6. **自动建目录**：写入新文件时使用 `--mkdir` 自动创建目录

## 返回格式说明

所有操作返回 JSON 格式，包含：
- `action`：操作类型
- `file`：文件路径
- 操作特定的结果字段
- `success`：操作是否成功（写入/替换操作）

错误信息输出到 stderr，退出码非 0。
