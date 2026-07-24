# Linux 系统通知指南

## notify-send 命令

### 基本用法

```bash
notify-send "标题" "消息内容"
```

### 完整参数

```bash
notify-send [选项] <标题> <消息>
```

### 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-i, --icon=ICON` | 图标名称或路径 | `-i dialog-warning` |
| `-u, --urgency=LEVEL` | 紧急程度 | `-u critical` |
| `-t, --expire-time=TIME` | 超时时间（毫秒） | `-t 5000` |
| `-a, --app-name=APP_NAME` | 应用名称 | `-a "My App"` |

### 紧急程度级别

- **low**: 低优先级，信息性通知
- **normal**: 普通优先级，常规通知
- **critical**: 高优先级，重要警告

### 图标名称

系统内置图标：
- `dialog-information`: 信息图标 ℹ️
- `dialog-warning`: 警告图标 ⚠️
- `dialog-error`: 错误图标 ❌
- `dialog-question`: 问题图标 ❓
- `process-working`: 加载图标 ⏳
- `mail-unread`: 邮件图标 📧
- `battery-caution`: 电池警告 🔋

### 示例

```bash
# 简单通知
notify-send "Hello" "World"

# 带图标的警告
notify-send -i dialog-warning -u critical "警告" "磁盘空间不足"

# 自定义超时
notify-send -t 10000 "提醒" "会议将在10分钟后开始"

# 指定应用名称
notify-send -a "Build System" "编译完成" "成功构建项目"
```

## 安装

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install libnotify-bin
```

### Fedora

```bash
sudo dnf install libnotify
```

### Arch Linux

```bash
sudo pacman -S libnotify
```

## 桌面环境支持

### GNOME
✅ 完全支持，内置通知中心

### KDE Plasma
✅ 完全支持，有通知历史

### XFCE
⚠️ 需要安装通知守护进程
```bash
sudo apt-get install xfce4-notifyd
```

### MATE
⚠️ 需要安装通知守护进程
```bash
sudo apt-get install mate-notification-daemon
```

### i3 / dwm (窗口管理器)
❌ 需要手动安装通知服务器
```bash
sudo apt-get install dunst
```

## 故障排除

### 通知不显示

1. **检查是否安装**
   ```bash
   which notify-send
   ```

2. **测试基本功能**
   ```bash
   notify-send "Test" "This is a test"
   ```

3. **检查通知守护进程**
   ```bash
   ps aux | grep notification
   ```

4. **查看日志**
   ```bash
   journalctl -f | grep notification
   ```

### 权限问题

某些桌面环境可能需要配置 D-Bus 权限：

```bash
# 编辑 D-Bus 配置
sudo nano /etc/dbus-1/system.d/notification.conf

# 添加权限
<policy user="your_username">
    <allow send_destination="org.freedesktop.Notifications"/>
</policy>
```

## Python 集成示例

```python
import subprocess

def send_notification(title, message, urgency="normal"):
    subprocess.run([
        'notify-send',
        '-u', urgency,
        title,
        message
    ])

# 使用
send_notification("任务完成", "文件处理完毕", "normal")
```

## 高级功能

### 动作按钮（需要额外工具）

使用 `notification-action` 可以添加交互按钮：

```bash
# 安装
pip install pydbus

# Python 示例
from pydbus import SessionBus

bus = SessionBus()
notifications = bus.get('org.freedesktop.Notifications')

# 发送带按钮的通知
notifications.Notify(
    'app_name',
    0,
    'dialog-info',
    'Title',
    'Message',
    ['action_id', 'Action Label'],
    {},
    5000
)
```

### 通知替换

使用相同的 `replaces_id` 可以更新现有通知：

```python
import subprocess

# 第一次发送
result = subprocess.run(
    ['notify-send', '-p', 'Title', 'Message'],
    capture_output=True,
    text=True
)
notification_id = result.stdout.strip()

# 更新通知
subprocess.run([
    'notify-send',
    '-r', notification_id,
    'Title',
    'Updated Message'
])
```

## 最佳实践

1. **保持简洁**: 标题不超过 50 字符，消息不超过 200 字符
2. **选择合适的紧急程度**: 不要滥用 critical
3. **提供有意义的图标**: 帮助用户快速识别通知类型
4. **考虑用户上下文**: 不要在用户忙碌时发送过多通知
5. **测试不同环境**: 确保在各种桌面环境下正常工作

## 相关资源

- [libnotify 官方文档](https://developer.gnome.org/libnotify/)
- [Desktop Notifications Specification](https://specifications.freedesktop.org/notification-spec/)
- [Ubuntu Notification Guidelines](https://wiki.ubuntu.com/NotificationDevelopmentGuidelines)
