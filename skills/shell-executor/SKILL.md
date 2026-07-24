---
name: shell-executor
description: >-
  安全执行 Shell 命令，支持验证、超时控制和输出捕获。
  当用户需要运行系统命令、检查文件状态、列出目录、
  执行脚本或进行系统操作时使用。支持命令验证、
  沙箱执行和结果格式化。
whenToUse: >-
  用户要求运行系统命令（ls、pwd、grep 等）、检查文件/目录状态、
  执行脚本或程序、获取系统信息（磁盘空间、进程等）、
  请求文件操作（复制、移动、删除）时使用。
---

# Shell 命令执行器

安全执行 Shell 命令，支持验证、超时控制和输出捕获。

## 使用时机

- 用户要求运行系统命令（ls、pwd、grep 等）
- 用户需要检查文件/目录状态
- 用户想要执行脚本或程序
- 用户需要系统信息（磁盘空间、进程等）
- 用户请求文件操作（复制、移动、删除需确认）

## 安全规则

**关键**：执行前务必验证命令！

### 禁止的命令（绝不执行）：
- `rm -rf /` 或任何递归根目录删除
- `dd if=/dev/zero` 或磁盘擦除命令
- `mkfs` 或文件系统格式化
- 带有 `sudo` 的命令，除非明确授权
- 网络攻击工具：`nmap`、`hping`、渗透工具
- Fork 炸弹：`:(){ :|:& };:`
- 任何未经用户明确确认就修改系统文件的命令

### 必需的验证步骤：
1. **使用 `scripts/validate_command.py` 检查危险模式**
2. **对破坏性操作与用户确认**（删除、覆盖）
3. **设置超时**（默认：30 秒）防止挂起
4. **捕获 stdout 和 stderr**
5. **返回退出码和格式化的输出**

## 执行工作流程

### 步骤 1：验证命令

```bash
python scripts/validate_command.py "<命令>"
```

检查内容：
- 危险模式
- 命令注入尝试
- 路径遍历攻击
- 资源耗尽风险

**如果验证失败**：拒绝该命令并说明原因。

### 步骤 2：执行命令

```bash
python scripts/execute_command.py "<命令>" [--timeout <秒数>]
```

参数：
- `<命令>`：要执行的 shell 命令（直接传递到 shell）
- `--timeout`：超时时间（秒），可选。如果不设置，命令会一直运行直到完成

**返回数据格式**：

脚本通过标准输出（stdout）和标准错误（stderr）返回以下格式的数据：

```
Exit Code: <退出码>
Execution Time: <执行时间>s

STDOUT:
<标准输出内容>

STDERR:
<标准错误内容>
```

**字段说明**：
- `Exit Code`：命令的退出状态码，0 表示成功，非 0 表示失败
- `Execution Time`：命令执行耗时（秒），保留 3 位小数
- `STDOUT`：命令的标准输出内容（如果有）
- `STDERR`：命令的标准错误内容（如果有）
- 如果命令超时，`Exit Code` 为 `-1`，`STDERR` 显示超时信息
- 如果发生异常，错误信息会输出到 stderr，退出码为 `-1`

**解析示例**：
```python
# 从输出中提取信息
output = subprocess.check_output(cmd, text=True)
lines = output.strip().split('\n')
exit_code = int(lines[0].split(': ')[1])
execution_time = float(lines[1].split(': ')[1].rstrip('s'))
stdout_content = ''
stderr_content = ''
# 解析 STDOUT 和 STDERR 部分...
```

### 步骤 3：格式化结果

按以下格式呈现结果：

```markdown
**命令**：`<命令>`
**退出码**：`<代码>`
**工作目录**：`<目录>`

**输出**：
```
<stdout 内容/>
```

**错误**（如果有）：
```
<stderr 内容/>
```

**执行时间**：`<秒>s`
**状态**：✅ 成功 / ❌ 失败
```

## 命令示例

### 安全命令（直接执行）

```bash
# 文件列表
ls -la /home/user
find . -name "*.py" -type f

# 系统信息
pwd
whoami
date
uname -a

# 文本处理
grep "pattern" file.txt
wc -l file.txt
head -n 10 file.txt

# 进程监控
ps aux | grep python
top -bn1 | head -20
```

### 需要确认的命令

```bash
# 文件删除
rm file.txt          # 询问："删除文件 file.txt？(yes/no)"
rm -r directory/     # 询问："递归删除目录 directory/？(yes/no)"

# 文件修改
mv old.txt new.txt   # 询问："将 old.txt 重命名为 new.txt？(yes/no)"
cp source dest       # 询问："复制 source 到 dest？(yes/no)"

# 包管理
pip install package  # 询问："安装 package？(yes/no)"
apt-get update       # 询问："更新软件包列表？(yes/no)"
```

### 禁止的命令（始终拒绝）

```bash
rm -rf /             # ❌ 绝不：递归根目录删除
sudo rm -rf /*       # ❌ 绝不：使用 sudo 的根目录删除
dd if=/dev/zero of=/dev/sda  # ❌ 绝不：磁盘擦除
:(){ :|:& };:        # ❌ 绝不：Fork 炸弹
```

## 输出处理

### 大输出（>10KB）

如果输出超过 `--max-output`：
1. 截断到指定限制
2. 添加警告：`⚠️ 输出已截断（显示前 100KB）`
3. 建议："使用 `| head -n 50` 或重定向到文件"

### 二进制输出

如果命令产生二进制数据：
1. 使用 `file` 命令检测
2. 显示：`⚠️ 检测到二进制输出（<大小> 字节）`
3. 建议："重定向到文件：command > output.bin"

### 错误处理

如果命令失败（退出码 != 0）：
1. 显示退出码
2. 突出显示 stderr
3. 如果可能，提供修复建议
4. 标记状态为 ❌ 失败

## 高级功能

### 智能数据提取（AI Analyze）

在任务计划中，可以使用 `"extraction": "ai_analyze"` 让 AI 智能分析脚本输出并提取关键数据，而不是使用固定的提取规则。

**适用场景**：
- 输出格式不固定或复杂
- 需要从多个信息点中提取最关键的内容
- 需要理解输出的语义而非简单匹配
- 结构化数据（JSON、表格）的核心字段提取

**示例任务计划**：
```json
{
  "task_plan": {
    "description": "获取系统信息并总结",
    "steps": [
      {
        "step_id": 1,
        "description": "获取系统详细信息",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "uname -a && df -h && free -m",
        "depends_on": [],
        "extraction": "ai_analyze",
        "save_to_context": "system_info"
      },
      {
        "step_id": 2,
        "description": "发送系统状态通知",
        "skill_name": "system-notifier",
        "script": "send_notification.py",
        "args": "--title \"系统状态\" --message \"{system_info}\"",
        "depends_on": [1],
        "extraction": null,
        "save_to_context": null
      }
    ]
  }
}
```

在这个例子中，AI 会分析 `uname -a && df -h && free -m` 的输出，自动提取最关键的信息（如操作系统版本、磁盘使用率、内存使用情况），而不是简单地取第一行或使用正则表达式。

### 管道命令

支持命令管道：
```bash
ls -la | grep ".py" | wc -l
cat file.txt | sort | uniq
```

验证适用于整个管道。

### 后台执行

对于长时间运行的命令，在命令后添加 `&`：
```bash
python scripts/execute_command.py "long_task.sh &"
```

## 参考文档

有关详细的安全指南和高级用法：
- 参见 [references/security-guide.md](references/security-guide.md)
- 参见 [references/command-reference.md](references/command-reference.md)

## 最佳实践

1. **始终先验证**：绝不跳过验证步骤
2. **最小权限**：以最低权限运行命令
3. **捕获错误**：始终检查 stderr
4. **用户确认**：在执行破坏性操作前询问
5. **记录执行**：跟踪命令以进行审计

## 示例会话

### 示例 1：列出 Python 文件

**用户**："显示当前目录中的所有 Python 文件"

**助手**：
```bash
python scripts/validate_command.py "find . -name '*.py' -type f"
# ✅ 验证通过

python scripts/execute_command.py "find . -name '*.py' -type f" --timeout 30
```

**输出**：
```markdown
**命令**：`find . -name '*.py' -type f`
**退出码**：`0`
**工作目录**：`/home/user/project`

**输出**：
```
./main.py
./scripts/init_skill.py
./scripts/validate.py
```

**执行时间**：`0.5s`
**状态**：✅ 成功
```

### 示例 2：删除文件（需要确认）

**用户**："删除 test.txt"

**助手**：
```
⚠️ 这将永久删除 test.txt。继续？(yes/no)
```

**用户**："yes"

**助手**：
```bash
python scripts/validate_command.py "rm test.txt"
# ✅ 验证通过（简单文件删除）

python scripts/execute_command.py "rm test.txt" --timeout 10
```

### 示例 3：危险命令（被拒绝）

**用户**："运行 rm -rf /"

**助手**：
```bash
python scripts/validate_command.py "rm -rf /"
# ❌ 验证失败：检测到危险模式
```

**响应**：
```
❌ 出于安全原因拒绝命令：

**原因**：禁止递归删除根目录
**风险**：将删除所有系统文件
**建议**：如果需要清理文件，请指定确切路径

安全替代示例：
- `rm -rf /tmp/old_files/`（特定目录）
```

---

**实现说明**：
- 所有命令都通过 `scripts/execute_command.py` 执行以保持一致性
- 验证是强制性的，不能绕过
- 输出捕获实现正确的错误处理
- 简单中转模式：直接传递命令到 shell，不添加额外参数
