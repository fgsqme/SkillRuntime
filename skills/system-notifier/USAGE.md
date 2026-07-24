# System Notifier SKILL - 使用指南

## 📋 概述

System Notifier 是一个跨平台的系统通知 SKILL，可以在用户的桌面上显示弹出通知。

## 🚀 快速开始

### 基本用法

通过 AI 对话使用：

```
用户: 发送一个系统通知，标题是"任务完成"，消息是"文件处理已完成"
```

AI 会自动调用 system-notifier SKILL 并执行通知发送。

### 手动测试

```bash
cd /home/user/PycharmProjects/SKILL
python skills/system-notifier/scripts/send_notification.py \
  --title "测试通知" \
  --message "这是一个测试消息" \
  --urgency normal \
  --timeout 5
```

## 📝 参数说明

| 参数 | 简写 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--title` | `-t` | ✅ | 通知标题 | `--title "任务完成"` |
| `--message` | `-m` | ✅ | 通知消息 | `--message "处理成功"` |
| `--urgency` | `-u` | ❌ | 紧急程度 (low/normal/critical) | `--urgency normal` |
| `--timeout` | `-T` | ❌ | 显示时长（秒），0=等待点击 | `--timeout 5` |
| `--icon` | `-i` | ❌ | 图标名称 | `--icon dialog-info` |

## 💡 使用示例

### 1. 信息性通知

```bash
python skills/system-notifier/scripts/send_notification.py \
  --title "下载完成" \
  --message "文件已保存到 /Downloads" \
  --urgency low
```

### 2. 警告通知

```bash
python skills/system-notifier/scripts/send_notification.py \
  --title "磁盘空间不足" \
  --message "已使用 85% 的存储空间" \
  --urgency critical \
  --timeout 10
```

### 3. 成功通知

```bash
python skills/system-notifier/scripts/send_notification.py \
  --title "构建成功" \
  --message "应用编译完成，无错误" \
  --urgency normal
```

### 4. 持久通知（等待用户点击）

```bash
python skills/system-notifier/scripts/send_notification.py \
  --title "重要提醒" \
  --message "请保存您的工作，系统将重启" \
  --urgency critical \
  --timeout 0
```

## 🔧 AI 集成

### 在对话中使用

当您需要发送通知时，只需告诉 AI：

```
用户: 当备份完成后发送一个通知
```

AI 会返回：
```
[TOOL_CALL: system-notifier | send_notification.py | --title "备份完成" --message "数据已成功备份"]
```

运行时系统会自动执行并返回结果。

### 编程调用

```python
import subprocess

def send_notification(title, message, urgency="normal"):
    subprocess.run([
        'python', 'skills/system-notifier/scripts/send_notification.py',
        '--title', title,
        '--message', message,
        '--urgency', urgency
    ])

# 使用
send_notification("任务完成", "所有文件已处理")
```

## 🌍 平台支持

### Linux ✅
- 使用 `notify-send` (libnotify)
- 需要安装: `sudo apt-get install libnotify-bin`
- 完全支持所有功能

### macOS ✅
- 使用 `osascript` (AppleScript)
- 系统内置，无需安装
- 不支持超时和自定义图标

### Windows ✅
- 使用 PowerShell Toast 通知
- 系统内置（Windows 10+）
- 现代化通知样式

## ⚙️ 紧急程度级别

| 级别 | 用途 | 视觉效果 |
|------|------|----------|
| `low` | 信息性消息 | 淡色，不显眼 |
| `normal` | 常规通知 | 标准样式 |
| `critical` | 重要警告 | 醒目，可能带声音 |

## 🎨 图标选项（Linux）

常用系统图标：
- `dialog-information`: ℹ️ 信息
- `dialog-warning`: ⚠️ 警告
- `dialog-error`: ❌ 错误
- `dialog-question`: ❓ 问题
- `process-working`: ⏳ 加载
- `mail-unread`: 📧 邮件
- `battery-caution`: 🔋 电池

## ❗ 最佳实践

1. **保持简洁**: 标题 < 50 字符，消息 < 200 字符
2. **选择合适的紧急程度**: 不要滥用 critical
3. **提供有意义的标题**: 让用户快速了解通知内容
4. **考虑时机**: 避免在不适当的时间发送通知
5. **不要滥用**: 只发送真正重要的通知

## 🐛 故障排除

### 通知不显示

**检查 notify-send 是否安装：**
```bash
which notify-send
```

**如果没有安装：**
```bash
sudo apt-get install libnotify-bin
```

**测试基本功能：**
```bash
notify-send "Test" "This is a test"
```

### 权限问题

某些桌面环境可能需要配置通知守护进程：

```bash
# 检查通知服务是否运行
ps aux | grep notification

# 重启通知服务（GNOME）
killall gnome-shell
```

### 中文乱码

确保系统支持 UTF-8：

```bash
locale
```

如果需要，设置：
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

## 📚 相关文件

- [SKILL.md](SKILL.md) - SKILL 完整文档
- [references/linux-notifications.md](references/linux-notifications.md) - Linux 通知详解
- [references/platform-comparison.md](references/platform-comparison.md) - 跨平台对比

## 🧪 测试

运行测试用例：

```bash
# 测试 1: 基本通知
python skills/system-notifier/scripts/send_notification.py \
  --title "Test" --message "Basic notification"

# 测试 2: 不同紧急程度
for urgency in low normal critical; do
  python skills/system-notifier/scripts/send_notification.py \
    --title "Urgency: $urgency" --message "Test" --urgency $urgency
done

# 测试 3: 中文支持
python skills/system-notifier/scripts/send_notification.py \
  --title "测试通知" --message "系统工作正常 ✅"
```

## 🔗 相关资源

- [libnotify 官方文档](https://developer.gnome.org/libnotify/)
- [Desktop Notifications Specification](https://specifications.freedesktop.org/notification-spec/)
- [Ubuntu Notification Guidelines](https://wiki.ubuntu.com/NotificationDevelopmentGuidelines)

---

**创建时间**: 2026-07-13  
**版本**: 1.0.0  
**作者**: SKILL Runtime System
