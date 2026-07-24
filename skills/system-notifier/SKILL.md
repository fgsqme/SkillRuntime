---
name: system-notifier
description: >-
  向用户发送桌面通知，支持自定义标题、消息和紧急程度。
  当需要提醒用户事件、提醒任务或提供状态更新时使用。
  支持不同的通知类型（信息、警告、错误、成功）和可选超时。
  关键词：notify, notification, alert, popup, toast, message, reminder, 系统通知
whenToUse: >-
  任务完成时通知用户、发生错误或警告时提醒、
  定时提醒、状态更新、需要用户确认的事件。
---

# 系统通知发送器

发送桌面通知以提醒用户重要事件、任务完成或状态更新。

## 使用时机

- 任务完成通知
- 错误或警告警报
- 提醒通知
- 状态更新
- 需要用户确认

## 安全规则

**关键**：只发送真正有用的通知！

### 准则：
1. **不要垃圾邮件**：只为重要事件发送通知
2. **清晰的消息**：使通知简洁明了
3. **适当的紧急程度**：将紧急程度与重要性匹配
4. **用户同意**：确保用户期望收到通知
5. **无敏感数据**：不要在通知中包含密码或私人信息

## 通知工作流程

### 步骤 1：选择通知类型

选择合适的紧急程度：
- `low`：信息性消息（默认）
- `normal`：常规通知
- `critical`：需要注意的重要警报

### 步骤 2：发送通知

```bash
python scripts/send_notification.py --title "标题" --message "消息" --urgency normal
```

参数：
- `--title`：通知标题（必需）
- `--message`：通知消息正文（必需）
- `--urgency`：紧急程度：low/normal/critical（默认：normal）
- `--timeout`：显示持续时间（秒）（0 = 等待点击，默认：5）
- `--icon`：图标名称（可选，使用系统默认）

### 步骤 3：确认送达

检查退出码：
- `0`：通知发送成功
- `1`：发送失败（检查 stderr 获取详细信息）

## 通知示例

### 基本信息通知

```bash
python scripts/send_notification.py \
  --title "任务完成" \
  --message "文件处理成功完成" \
  --urgency low
```

### 警告通知

```bash
python scripts/send_notification.py \
  --title "警告" \
  --message "磁盘空间不足（已使用 85%）" \
  --urgency critical \
  --timeout 10
```

### 成功通知

```bash
python scripts/send_notification.py \
  --title "构建成功" \
  --message "应用程序编译无错误" \
  --urgency normal
```

### 错误通知

```bash
python scripts/send_notification.py \
  --title "发生错误" \
  --message "数据库连接失败。请检查网络。" \
  --urgency critical \
  --timeout 0
```

### 自定义超时

```bash
# 显示通知 3 秒
python scripts/send_notification.py \
  --title "提醒" \
  --message "会议将在 15 分钟后开始" \
  --urgency normal \
  --timeout 3
```

## 平台支持

### Linux（主要）
使用 `notify-send`（libnotify）- 在 Ubuntu/Debian 上最常见

**安装**（如果不可用）：
```bash
sudo apt-get install libnotify-bin
```

### macOS
使用 `osascript`（AppleScript）- 内置

### Windows
使用 PowerShell toast 通知 - 内置

脚本自动检测平台并使用适当的方法。

## 最佳实践

1. **保持标题简短**：最多 50 个字符
2. **具体明确**：在消息中包含相关细节
3. **使用适当的紧急程度**：不要将所有内容都标记为关键
4. **考虑时机**：不要在不当时间发送通知
5. **先测试**：验证通知在目标系统上是否有效
6. **处理失败**：检查退出码并提供后备方案

## 集成示例

### 长时间运行任务后

```python
import subprocess

# 你的长时间任务在这里...
result = perform_task()

# 发送通知
subprocess.run([
    'python', 'scripts/send_notification.py',
    '--title', '任务完成',
    '--message', f'处理了 {result.count} 个项目',
    '--urgency', 'normal'
])
```

### 错误警报

```python
try:
    risky_operation()
except Exception as e:
    subprocess.run([
        'python', 'scripts/send_notification.py',
        '--title', '操作失败',
        '--message', str(e),
        '--urgency', 'critical',
        '--timeout', '0'
    ])
```

### 定时提醒

```bash
# 使用 cron 或任务计划程序
0 9 * * * python /path/to/scripts/send_notification.py \
  --title "每日站会" \
  --message "团队会议将在 30 分钟后开始" \
  --urgency normal
```

## 故障排除

### 通知未出现

1. **检查 notify-send 是否已安装**：
   ```bash
   which notify-send
   ```

2. **手动测试**：
   ```bash
   notify-send "测试" "这是一个测试"
   ```

3. **检查桌面环境**：某些最小化设置不支持通知

4. **验证权限**：确保脚本具有执行权限

### 错误的紧急程度

- 调整 `--urgency` 参数
- 测试不同级别以查看视觉差异

### 超时问题

- `--timeout 0`：通知保持显示直到点击
- `--timeout 5`：5 秒后自动关闭
- 如果未指定，默认为 5 秒

## 高级功能

### 自定义图标（Linux）

```bash
python scripts/send_notification.py \
  --title "下载完成" \
  --message "file.zip 已下载" \
  --icon "download"
```

常见图标名称：`info`、`warning`、`error`、`success`、`download`、`upload`

### 操作按钮（平台相关）

某些平台支持操作按钮。查看平台特定文档。

### 丰富格式

消息支持基本格式：
- 换行：使用 `\n`
- Unicode 表情符号：✅ ❌ ⚠️ ℹ️

示例：
```bash
python scripts/send_notification.py \
  --title "状态更新" \
  --message "✅ 构建通过\n⏱️ 持续时间：2分30秒"
```

## 参考文档

有关平台特定的详细信息：
- 参见 [references/linux-notifications.md](references/linux-notifications.md)
- 参见 [references/platform-comparison.md](references/platform-comparison.md)

---

**实现说明**：
- 内置跨平台支持
- 自动平台检测
- 在不支持的系统上优雅降级
- 最小依赖（使用系统工具）
- 异步交付（非阻塞）
