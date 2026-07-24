# Skill 运行环境

一个 Python 实现的 SKILL 运行环境，使用 OpenAI 接口，如果要用其他AI API ，建议使用 [one-api]([https://markdown.com.cn](https://github.com/songquanpeng/one-api)) 这个项目可以将多种AI接口转为OpenAI接口。
此项目基于**渐进式调用（Progressive Disclosure）** 机制，让 AI 在有限的上下文窗口中高效调用外部工具，自动拆解复杂任务、递归执行子任务、验证结果并自我修复，直到任务完成。
- 备注: 此项目也是用AI写的，主要是为了学习SKILL调用流程，如果你有更好的想法，请随时提 issue 或 fork 项目并改进。

---

## 核心功能

### 1. 渐进式技能发现

采用三级加载机制，避免一次性将所有技能信息塞入上下文：

| 层级 | 内容 | 加载时机 |
|------|------|----------|
| **L1** 元数据 | name、description、whenToUse | 启动时，始终在上下文中 |
| **L2** 正文 | SKILL.md 完整使用指引 | 命中后按需加载，用完即弃 |
| **L3** 资源 | scripts/、references/、assets/ | 执行时按需调用 |

### 2. 三种任务执行模式

**模式一：单步工具调用** — 一步即可完成的任务
```json
{
  "tool_call": {
    "skill_name": "shell-executor",
    "script": "execute_command.py",
    "args": "ls -la"
  }
}
```

**模式二：多步任务计划** — 多步骤、有数据依赖的复杂任务
```json
{
  "task_plan": {
    "description": "获取系统时间并发送通知",
    "steps": [
      {
        "step_id": 1,
        "description": "获取系统时间",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "date '+%Y-%m-%d %H:%M:%S'",
        "depends_on": [],
        "extraction": "smart",
        "save_to_context": "current_time",
        "context_prompt": "本步骤输出当前系统时间"
      },
      {
        "step_id": 2,
        "description": "发送通知",
        "skill_name": "system-notifier",
        "script": "send_notification.py",
        "args": "--title '当前时间' --message '{current_time}'",
        "depends_on": [1]
      }
    ]
  }
}
```

**模式三：子任务拆分** — 复杂任务，步骤可递归拆分并自动验证
```json
{
  "task_plan": {
    "description": "创建 Python 项目",
    "steps": [
      {
        "step_id": 1,
        "description": "创建文件夹结构",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "mkdir -p project/src project/tests",
        "needs_decompose": true
      },
      {
        "step_id": 2,
        "description": "创建代码文件",
        "skill_name": "text-file-ops",
        "script": "write_file.py",
        "args": "project/src/main.py 'print(\"hello\")'",
        "depends_on": [1],
        "needs_decompose": true
      },
      {
        "step_id": 3,
        "description": "验证项目结构",
        "skill_name": "shell-executor",
        "script": "execute_command.py",
        "args": "find project -type f",
        "depends_on": [2]
      }
    ]
  }
}
```

### 3. 子任务递归拆分

设置 `"needs_decompose": true` 的步骤，执行时由 AI 自动拆分为更细粒度的子步骤：

```
步骤: "创建项目文件夹结构" (needs_decompose: true)
    ↓ AI 分析拆分
    ├── 子步骤 1: 创建根目录
    ├── 子步骤 2: 创建 src 子目录
    ├── 子步骤 3: 创建 tests 子目录
    └── 子步骤 4: 验证目录创建结果
```

- 最大递归深度 3 层，防止无限拆分
- 子步骤之间支持依赖关系和数据流转
- 子任务结果自动回传父步骤

### 4. 完成后验证 + 自动修复

任务执行完成后，AI 自动验证是否真正达成目标：

```
执行所有步骤 → AI 验证结果
    ├── 通过 → 任务完成
    └── 未通过 → 分析原因 → 创建修复计划 → 重新执行 → 再次验证
                  (循环直到成功或达到最大重试次数)
```

### 5. 失败重试与 AI 重新规划

- 每个步骤支持自动重试（默认 3 次）
- 全部失败后，AI 分析错误原因并重新制定计划
- 已成功步骤的结果被继承，不重复执行

### 6. 多轮迭代工具调用

- 支持最多 5 次迭代（可配置）
- 每次基于前次执行结果修正参数或换工具
- 所有工具成功后，AI 基于真实结果生成最终回复

### 7. 上下文数据流转

前序步骤的结果可通过变量传递给后续步骤：

- `save_to_context` — 将结果保存为变量
- `{变量名}` — 在后续步骤的 args 中引用
- `context_prompt` — 用自然语言指导 AI 智能提取关键信息

### 8. 子 Agent 隔离

Skill 执行的中间过程使用独立对话历史，不污染主 Agent 上下文。只有最终结果回流到主对话。

---

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    用户输入                           │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────┐
│  skill_runtime.py        运行时主程序                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │SkillManager │  │AIIntegration │  │ToolExecutor │ │
│  │(技能管理)    │  │(AI 对话接口)  │  │(工具执行)    │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────────┘ │
│         │                │                            │
│  ┌──────┴──────┐  ┌──────┴───────┐                   │
│  │SkillLoader  │  │TaskPlanner   │                   │
│  │(技能发现)    │  │(任务规划/     │                   │
│  │             │  │ 子任务拆分)   │                   │
│  └─────────────┘  └──────────────┘                   │
│                                                       │
│  ┌─────────────────────────┐                          │
│  │ProgressiveExposureEngine│                          │
│  │(渐进式暴露 L1/L2/L3)    │                          │
│  └─────────────────────────┘                          │
└──────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- Python 3.8+
- OpenAI 兼容 API（用于 AI 推理）

### 安装

```bash
# 克隆项目
cd SKILL

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

依赖项：
- `requests` — API 调用
- `pyyaml` — SKILL.md frontmatter 解析
- `chardet` — 文件编码检测

### 启动

```bash
# 交互模式（默认）
python skill_runtime.py

# 指定 API 地址和模型
python skill_runtime.py --api-url http://localhost:8080 --api-key your-key --model gpt-4

# 单次查询（非交互）
python skill_runtime.py -q "列出当前目录的文件"

# 显示详细日志
python skill_runtime.py -v

# 列出已加载的 Skill
python skill_runtime.py --list-skills

# 设置最大重试次数
python skill_runtime.py --max-retries 5
```

### 交互命令

| 命令 | 说明 |
|------|------|
| `/list` | 列出所有已加载的 SKILL |
| `/search <关键词>` | 搜索 SKILL |
| `/reload` | 重新加载所有 SKILL |
| `/quit` | 退出 |

---

## 项目结构

```
SKILL/
├── skill_runtime.py            # 运行时主程序（入口）
├── skill_manager.py            # Skill 管理器（注册表、正文加载）
├── skill_loader.py             # Skill 加载器（目录扫描、frontmatter 解析）
├── ai_integration.py           # AI 对话接口（系统提示词、API 调用）
├── tool_executor.py            # 工具执行器（脚本调用、结果格式化）
├── task_planner.py             # 任务规划器（多步骤拆解、子任务拆分、数据流转）
├── progressive_exposure.py     # 渐进式暴露引擎（L1/L2/L3 三级加载）
├── demo_image_feature.py       # 图片功能演示
├── test_subtask.py             # 子任务功能测试
├── prompts/
│   ├── system_prompt.txt       # 系统提示词模板
│   ├── replan_prompt.txt       # 失败重规划提示词
│   └── subtask_prompt.txt      # 子任务拆分提示词
├── test/                       # 测试目录
│   ├── test_ai_analyze.py      # AI 数据提取测试
│   ├── test_ai_analyze_task_plan.py  # AI 任务规划分析测试
│   ├── test_ai_replan.py       # AI 重规划测试
│   ├── test_image_feature.py   # 图片功能测试
│   ├── test_iterative_tool_calls.py  # 迭代工具调用测试
│   └── test_retry_mechanism.py # 重试机制测试
├── skills/                     # Skill 目录
│   ├── shell-executor/         # Shell 命令执行
│   ├── system-notifier/        # 系统桌面通知
│   ├── text-file-ops/          # 文本文件操作
│   ├── pdf-generator/          # PDF 生成
│   ├── ppt-generator/          # PPT 生成
│   └── ui-design-system/       # UI 设计规范
└── requirements.txt            # Python 依赖
```

---

## 内置 Skill

| Skill | 说明 | 主要脚本 |
|-------|------|----------|
| **shell-executor** | 安全执行 Shell 命令，支持超时控制 | `execute_command.py`, `validate_command.py` |
| **system-notifier** | 发送桌面通知，支持多种通知类型 | `send_notification.py` |
| **text-file-ops** | 文本文件读写、搜索、替换、统计 | `text_ops.py` |
| **pdf-generator** | PDF 生成，支持图片、HTML 输入 | `generate_pdf.py` |
| **ppt-generator** | 智能 PPT 生成，多行业多风格 | `generate_ppt.py` 等 |
| **ui-design-system** | UI 设计规范：配色、组件、布局 | 参考文档 |

---

## 创建自定义 Skill

每个 Skill 是一个独立目录：

```
my-skill/
├── SKILL.md              # 必须：技能定义文件
├── scripts/              # 可选：可执行脚本
│   └── run.py
├── references/           # 可选：参考文档
│   └── guide.md
└── assets/               # 可选：静态资源
```

### SKILL.md 格式

```yaml
---
name: my-skill
description: >-
  技能的简短描述，出现在系统提示词中供 AI 匹配。
whenToUse: >-
  描述何时应该使用这个技能，帮助 AI 精准判断。
---

# 技能标题

## 使用时机
- 使用场景 1
- 使用场景 2

## 工作流程
### 步骤 1：验证输入
...

### 步骤 2：执行操作
...
```

### Frontmatter 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | Skill 唯一标识 |
| `description` | 是 | 简短描述，注入系统提示词 |
| `whenToUse` | 推荐 | 使用时机，帮助 AI 精准匹配 |

### 占位符

L2 正文支持占位符，加载时自动展开：

| 占位符 | 说明 |
|--------|------|
| `${KIMI_SKILL_DIR}` | Skill 目录的绝对路径 |
| `$ARGUMENTS` | 用户传入的参数 |
| `$<name>` / `${name}` | 自定义变量 |

---

## 命令行参数

```
python skill_runtime.py [选项]

选项：
  --dirs, -d DIRS       Skill 目录列表（默认 ./skills）
  --api-url URL         API 地址（默认 http://localhost:8080）
  --api-key KEY         API Key（默认 test）
  --model, -m MODEL     AI 模型名称（默认 gpt-4）
  --query, -q QUESTION  单次查询（非交互模式）
  --list-skills, -l     列出所有 Skill 并退出
  --max-retries N       任务失败后最大重试次数（默认 3）
  --verbose, -v         显示详细日志
```

---

## 任务执行流程

```
用户请求
    ↓
AI 分析 → 选择执行模式
    ├── 单步 → tool_call → 执行 → AI 回复
    ├── 多步 → task_plan → 逐步执行 → AI 回复
    └── 复杂 → task_plan + needs_decompose
                    ↓
              逐步执行，遇到 needs_decompose 的步骤
                    ↓
              AI 拆分子任务 → 执行子步骤 → 结果回传
                    ↓
              全部完成后 → AI 验证
                    ├── 通过 → 完成
                    └── 未通过 → AI 创建修复计划 → 重新执行
                                  (循环直到成功)
```

---

## 设计优势

| 策略 | 效果 |
|------|------|
| **元数据预加载** | 系统提示词精简，模型注意力不被无关 Skill 分散 |
| **正文按需加载** | 只有命中的 Skill 才进入上下文，节省 token |
| **用完即弃** | Skill 正文不持久化到对话历史，持续节省 token |
| **子任务递归** | 复杂任务自动拆解，逐步执行直到完成 |
| **验证+自修复** | 执行后验证结果，不通过则自动修复，形成闭环 |
| **嵌套深度限制** | 3 层上限防止无限递归，保障稳定性 |
| **子 Agent 隔离** | 中间执行过程不污染主上下文 |
